#!/usr/bin/env python3
"""
scan_notes.py - Inventory the PR notes in a directory, validate their header
line, and tally them by type.

Covers three release-notes steps: list the .md files sorted by filename with a
total, check every file opens with `PR #<number>:`, and group the entries by
their `type:` field with per-group counts.

Finding codes (one per condition actually tested):
    bad_header    the first line does not match `PR #<number>: <title>`
    missing_type  no `type: <value>` line anywhere in the file

USAGE
    python3 scripts/scan_notes.py <notes-dir> [--json] [--out FILE]

    --json   print the full JSON report to stdout (default)
    --out F  write the JSON report to F and print a one-line summary instead

EXIT CODES
    0  Every file has a valid header and a type; no findings.
    1  Findings present; each one is listed under "findings".
    2  Usage error, missing directory, or an unreadable file.
"""

import argparse
import json
import re
import sys
from pathlib import Path

HEADER_RE = re.compile(r"^PR #(\d+):\s*(.+?)\s*$")
TYPE_RE = re.compile(r"^type:\s*(\S+)\s*$")


def scan(notes_dir):
    """Return (report_dict, error_message). error_message is None on success."""
    files = sorted(p for p in notes_dir.glob("*.md") if p.is_file())
    entries = []
    findings = []
    counts = {}

    for path in files:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as e:
            return None, f"cannot read {path}: {e}"

        first = lines[0] if lines else ""
        header = HEADER_RE.match(first)
        if not header:
            findings.append({"file": path.name, "code": "bad_header",
                             "detail": f"first line is {first!r}"})

        entry_type = None
        for line in lines[1:]:
            m = TYPE_RE.match(line)
            if m:
                entry_type = m.group(1)
                break
        if entry_type is None:
            findings.append({"file": path.name, "code": "missing_type",
                             "detail": "no `type:` line"})
        else:
            counts[entry_type] = counts.get(entry_type, 0) + 1

        entries.append({
            "file": path.name,
            "pr": int(header.group(1)) if header else None,
            "title": header.group(2) if header else None,
            "type": entry_type,
        })

    report = {
        "dir": notes_dir.as_posix(),
        "total": len(files),
        "files": [p.name for p in files],
        "entries": entries,
        "counts": dict(sorted(counts.items())),
        "findings": findings,
    }
    return report, None


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="List, validate, and tally the PR notes in a directory.")
    ap.add_argument("notes_dir", help="Directory holding the pr-*.md notes")
    ap.add_argument("--json", action="store_true",
                    help="Print the full JSON report to stdout (default)")
    ap.add_argument("--out", help="Write the JSON report here; print a summary")
    args = ap.parse_args(argv)

    notes_dir = Path(args.notes_dir)
    if not notes_dir.is_dir():
        print(f"not a directory: {notes_dir}", file=sys.stderr)
        return 2

    report, err = scan(notes_dir)
    if err:
        print(err, file=sys.stderr)
        return 2

    text = json.dumps(report, indent=2)
    if args.out:
        try:
            Path(args.out).write_text(text + "\n", encoding="utf-8")
        except OSError as e:
            print(f"cannot write {args.out}: {e}", file=sys.stderr)
            return 2
        print(f"{report['total']} notes, {len(report['findings'])} findings "
              f"-> {args.out}")
    else:
        print(text)

    return 1 if report["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())
