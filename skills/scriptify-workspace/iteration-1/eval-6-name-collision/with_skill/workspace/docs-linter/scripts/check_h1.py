#!/usr/bin/env python3
"""Check that every markdown file starts with a level-1 heading + blank line.

Named check_h1.py, not check_headings.py: scripts/check_headings.py already
exists in this skill and checks image alt text.

A file passes when line 1 is `# Some Title` and line 2 is blank. A heading that
ends the file passes too, because there is no following content to separate.

Usage:
    python3 scripts/check_h1.py <docs-dir> [--out FILE]

Exit codes:
    0  every file starts with a level-1 heading followed by a blank line
    1  at least one file does not (findings JSON on stdout)
    2  usage error, or <docs-dir> is not a readable directory
"""

import argparse
import json
import re
import sys
from pathlib import Path

H1 = re.compile(r"^#\s+\S")
ANY_HEADING = re.compile(r"^(#+)\s")


def check_file(text):
    """Return a reason string, or "" when the file is fine."""
    lines = text.splitlines()
    if not lines:
        return "file is empty"
    first = lines[0]
    if not H1.match(first):
        m = ANY_HEADING.match(first)
        if m:
            return "first line is a level-%d heading, not level 1" % len(m.group(1))
        return "first line is not a level-1 heading"
    if len(lines) > 1 and lines[1].strip():
        return "no blank line after the level-1 heading"
    return ""


def scan(root):
    findings = []
    checked = 0
    for path in sorted(root.rglob("*.md")):
        checked += 1
        reason = check_file(path.read_text(encoding="utf-8", errors="replace"))
        if reason:
            findings.append({"path": path.relative_to(root).as_posix(),
                             "reason": reason})
    return {"docs_dir": root.as_posix(), "checked": checked,
            "missing_h1": findings}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Flag markdown files that do not start with a level-1 "
                    "heading followed by a blank line.")
    parser.add_argument("docs_dir", help="Directory to scan recursively for *.md")
    parser.add_argument("--out", help="Write the findings JSON here; print a "
                                      "one-line summary to stdout instead")
    args = parser.parse_args(argv)

    root = Path(args.docs_dir)
    if not root.is_dir():
        sys.stderr.write("not a directory: %s\n" % root)
        return 2

    try:
        result = scan(root)
    except OSError as e:
        sys.stderr.write("cannot read docs tree: %s\n" % e)
        return 2

    payload = json.dumps(result, indent=2)
    if args.out:
        try:
            Path(args.out).write_text(payload + "\n", encoding="utf-8")
        except OSError as e:
            sys.stderr.write("cannot write %s: %s\n" % (args.out, e))
            return 2
        print("checked %d file(s), %d missing a level-1 heading -> %s"
              % (result["checked"], len(result["missing_h1"]), args.out))
    else:
        print(payload)
    return 1 if result["missing_h1"] else 0


if __name__ == "__main__":
    sys.exit(main())
