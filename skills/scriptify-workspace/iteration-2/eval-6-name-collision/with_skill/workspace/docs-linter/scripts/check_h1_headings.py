#!/usr/bin/env python3
"""
check_h1_headings.py - Flag markdown files that do not start with a level-1
heading followed by a blank line.

A file passes when its first non-empty line is a level-1 ATX heading ("# Title")
and the line right after it is blank (or the file ends there).

NOTE ON THE NAME: scripts/check_headings.py in this same folder is unrelated --
it checks image alt text and the release pipeline calls it by that exact path.
This script therefore uses a distinct name and does not touch it.

USAGE
    python3 scripts/check_h1_headings.py <docs-dir> [--json] [--out FILE]

EXIT CODES
    0  every file starts with an H1 followed by a blank line
    1  at least one file was flagged (findings on stdout)
    2  usage error / unreadable directory
"""

import argparse
import json
import sys
from pathlib import Path

MISSING_H1 = "missing_h1"
MISSING_BLANK = "missing_blank_after_h1"


def check_file(path):
    """Return an issue string for one file, or None when it passes."""
    lines = path.read_text(encoding="utf-8").splitlines()
    first = 0
    while first < len(lines) and not lines[first].strip():
        first += 1
    if first >= len(lines):
        return MISSING_H1
    line = lines[first]
    if not (line.startswith("# ") and line[2:].strip()):
        return MISSING_H1
    if first + 1 < len(lines) and lines[first + 1].strip():
        return MISSING_BLANK
    return None


def scan(root):
    findings = []
    checked = 0
    for path in sorted(root.rglob("*.md")):
        checked += 1
        issue = check_file(path)
        if issue:
            findings.append({"path": path.as_posix(), "issue": issue})
    return {"root": root.as_posix(), "checked": checked, "findings": findings}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Flag markdown files missing an H1 + blank line at the top.")
    parser.add_argument("docs_dir", help="directory to scan recursively for .md files")
    parser.add_argument("--json", action="store_true",
                        help="print the full result as JSON (default)")
    parser.add_argument("--out", metavar="FILE",
                        help="write JSON to FILE and print only a summary line")
    args = parser.parse_args(argv)

    root = Path(args.docs_dir)
    if not root.is_dir():
        sys.stderr.write("not a directory: %s\n" % root)
        return 2
    try:
        result = scan(root)
    except OSError as exc:
        sys.stderr.write("cannot read %s: %s\n" % (root, exc))
        return 2

    text = json.dumps(result, indent=2)
    if args.out:
        try:
            Path(args.out).write_text(text + "\n", encoding="utf-8")
        except OSError as exc:
            sys.stderr.write("cannot write %s: %s\n" % (args.out, exc))
            return 2
        print("checked %d file(s), %d finding(s) -> %s"
              % (result["checked"], len(result["findings"]), args.out))
    else:
        print(text)
    return 1 if result["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())
