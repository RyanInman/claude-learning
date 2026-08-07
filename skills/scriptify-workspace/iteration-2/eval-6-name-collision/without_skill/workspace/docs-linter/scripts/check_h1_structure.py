#!/usr/bin/env python3
"""Check that every markdown file starts with a level-1 heading followed by a blank line.

Backs workflow step 2 of the docs-linter skill.

Named check_h1_structure.py, not check_headings.py: scripts/check_headings.py
already exists in this skill and checks image alt text. The release pipeline
calls it by that exact path, so it must not be replaced.

Exit codes:
    0  every file conforms
    1  at least one file was flagged
    2  usage error
"""

import argparse
import json
import sys
from pathlib import Path


def inspect(path: Path):
    """Return a reason string if the file is non-conforming, else None."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return "file is empty"
    first = lines[0]
    if not first.startswith("# "):
        if first.lstrip().startswith("#"):
            return "first line is not a level-1 heading: %r" % first
        return "content appears before the first heading: %r" % first
    if len(lines) < 2:
        return "no blank line after the level-1 heading"
    if lines[1].strip() != "":
        return "no blank line after the level-1 heading"
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("docs_dir", help="directory to scan (e.g. docs/)")
    parser.add_argument(
        "--json", action="store_true", help="emit JSON instead of plain text"
    )
    args = parser.parse_args(argv)

    root = Path(args.docs_dir)
    if not root.is_dir():
        sys.stderr.write("not a directory: %s\n" % root)
        return 2

    flagged = []
    checked = 0
    for path in sorted(root.rglob("*.md")):
        checked += 1
        reason = inspect(path)
        if reason:
            flagged.append({"file": str(path.relative_to(root)), "reason": reason})

    if args.json:
        print(json.dumps({"checked": checked, "flagged": flagged}, indent=2))
    else:
        for item in flagged:
            print("%s: %s" % (item["file"], item["reason"]))
        print("checked: %d, flagged: %d" % (checked, len(flagged)))
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
