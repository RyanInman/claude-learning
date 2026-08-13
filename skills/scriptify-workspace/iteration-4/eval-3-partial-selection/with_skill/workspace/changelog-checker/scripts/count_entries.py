#!/usr/bin/env python3
"""
count_entries.py - Count changelog entries per category, per file and in total.

Backs step 3 of changelog-checker: for every .md file in the folder, count the
bullet entries under each `### Category` heading, then total them across files.
Every category found is reported, including tags outside the expected set, so
step 6 can triage them instead of this script hiding them.

USAGE
    python3 scripts/count_entries.py <changelogs-dir> [--json] [--out FILE]

OUTPUT (--json)
    {"per_file": {"v1.0.0.md": {"Added": 2, "Fixed": 1}},
     "totals": {"Added": 2, "Fixed": 1},
     "entry_count": 3,
     "findings": []}

EXIT CODES
    0  At least one entry counted.
    1  Finding: no entry found in any file ("no_entries_found").
    2  Usage error, or the folder is missing or unreadable.
"""

import argparse
import json
import re
import sys
from pathlib import Path

CATEGORY_RE = re.compile(r"^###\s+(.+?)\s*$")
ENTRY_RE = re.compile(r"^\s*[-*]\s+\S")


def count_file(text):
    counts = {}
    category = None
    for line in text.splitlines():
        m = CATEGORY_RE.match(line)
        if m:
            category = m.group(1)
            counts.setdefault(category, 0)
        elif category and ENTRY_RE.match(line):
            counts[category] += 1
    return counts


def main(argv=None):
    ap = argparse.ArgumentParser(description="Count changelog entries per category.")
    ap.add_argument("folder", help="Folder holding the changelog .md files")
    ap.add_argument("--json", action="store_true", help="Emit JSON on stdout")
    ap.add_argument("--out", help="Write the JSON to FILE instead of stdout")
    args = ap.parse_args(argv)

    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"not a folder: {args.folder}", file=sys.stderr)
        return 2

    per_file, totals = {}, {}
    for path in sorted(folder.glob("*.md")):
        try:
            counts = count_file(path.read_text(encoding="utf-8"))
        except OSError as e:
            print(f"cannot read {path}: {e}", file=sys.stderr)
            return 2
        per_file[path.name] = counts
        for cat, n in counts.items():
            totals[cat] = totals.get(cat, 0) + n

    entry_count = sum(totals.values())
    findings = [] if entry_count else ["no_entries_found"]
    payload = {"per_file": per_file, "totals": totals,
               "entry_count": entry_count, "findings": findings}

    text = json.dumps(payload, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"{entry_count} entr(ies) -> {args.out}")
    elif args.json:
        print(text)
    else:
        for name, counts in per_file.items():
            print(f"{name}: " + (", ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "no entries"))
        print("totals: " + (", ".join(f"{k}={v}" for k, v in sorted(totals.items())) or "none"))
        if findings:
            print("findings: " + ", ".join(findings))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
