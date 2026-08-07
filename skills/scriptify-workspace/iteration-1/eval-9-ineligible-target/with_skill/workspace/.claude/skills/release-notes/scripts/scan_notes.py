#!/usr/bin/env python3
"""
scan_notes.py - Inventory the release notes in a notes/ directory: list the
files, validate the `PR #<number>:` header of each, and group the entries by
their `type:` field.

Covers workflow steps 1-3 of the release-notes skill: the listing and count,
the header check, and the per-type grouping and tally.

STDOUT (JSON)
{
  "dir": "notes",
  "total": 3,                       # every .md file found, sorted by filename
  "files": ["pr-101.md", ...],
  "invalid": [{"file": "pr-104.md", "reason": "missing_pr_header"}],
  "unknown_type": [{"file": "x.md", "type": "docs"}],
  "counts": {"feat": 1, "fix": 1, "chore": 1},
  "groups": {"feat": [{"pr": 101, "title": "...", "file": "pr-101.md"}], ...}
}

USAGE
    python3 scripts/scan_notes.py <notes-dir> [--json] [--out FILE]

EXIT CODES
    0  Every file carries a valid header and a known type.
    1  Findings: `invalid` or `unknown_type` is non-empty.
    2  Usage error, or the directory is missing or unreadable.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# The header form the skill's step 2 requires, on the file's first line.
PR_HEADER_RE = re.compile(r"^PR #(\d+):\s*(.+?)\s*$")
TYPE_RE = re.compile(r"^type:\s*(\S+)\s*$")
# The three categories the skill's step 3 names.
KNOWN_TYPES = ("feat", "fix", "chore")


def scan(notes_dir):
    """Return the scan result dict for a notes directory."""
    d = Path(notes_dir)
    files = sorted(p.name for p in d.glob("*.md") if p.is_file())
    result = {
        "dir": str(d).replace("\\", "/"),
        "total": len(files),
        "files": files,
        "invalid": [],
        "unknown_type": [],
        "counts": {t: 0 for t in KNOWN_TYPES},
        "groups": {t: [] for t in KNOWN_TYPES},
    }
    for name in files:
        lines = (d / name).read_text(encoding="utf-8").splitlines()
        first = lines[0].strip() if lines else ""
        m = PR_HEADER_RE.match(first)
        if not m:
            result["invalid"].append({"file": name, "reason": "missing_pr_header"})
            continue
        entry_type = None
        for line in lines[1:]:
            t = TYPE_RE.match(line.strip())
            if t:
                entry_type = t.group(1)
                break
        if entry_type is None:
            result["invalid"].append({"file": name, "reason": "missing_type"})
            continue
        if entry_type not in KNOWN_TYPES:
            result["unknown_type"].append({"file": name, "type": entry_type})
            continue
        result["groups"][entry_type].append(
            {"pr": int(m.group(1)), "title": m.group(2), "file": name})
        result["counts"][entry_type] += 1
    for t in KNOWN_TYPES:
        result["groups"][t].sort(key=lambda e: e["pr"])
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="List, header-check, and group the release notes in a directory.")
    ap.add_argument("notes_dir", help="directory holding the per-PR .md notes")
    ap.add_argument("--json", action="store_true",
                    help="accepted for explicitness; stdout is JSON either way")
    ap.add_argument("--out", help="write the JSON here; print a summary to stdout")
    args = ap.parse_args(argv)

    d = Path(args.notes_dir)
    if not d.is_dir():
        print(f"scan_notes: not a directory: {args.notes_dir}", file=sys.stderr)
        return 2
    try:
        result = scan(d)
    except OSError as e:
        print(f"scan_notes: cannot read notes: {e}", file=sys.stderr)
        return 2

    payload = json.dumps(result, indent=2)
    if args.out:
        try:
            Path(args.out).write_text(payload + "\n", encoding="utf-8")
        except OSError as e:
            print(f"scan_notes: cannot write --out: {e}", file=sys.stderr)
            return 2
        print(f"scan_notes: {result['total']} files, "
              f"{len(result['invalid'])} invalid -> {args.out}")
    else:
        print(payload)
    return 1 if (result["invalid"] or result["unknown_type"]) else 0


if __name__ == "__main__":
    sys.exit(main())
