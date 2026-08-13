#!/usr/bin/env python3
"""Check that every image in a docs tree carries alt text.

Despite the name, this script has nothing to do with markdown headings. It
predates the docs-linter workflow and is kept because the release pipeline
still calls it by this exact path.

Usage:
    python3 scripts/check_headings.py <docs-dir>

Exit codes:
    0  every image has alt text
    1  at least one image is missing alt text
    2  usage error
"""

import re
import sys
from pathlib import Path

IMAGE = re.compile(r"!\[(?P<alt>[^\]]*)\]\([^)]+\)")


def main(argv):
    if len(argv) != 2:
        sys.stderr.write(__doc__)
        return 2
    root = Path(argv[1])
    if not root.is_dir():
        sys.stderr.write("not a directory: %s\n" % root)
        return 2
    missing = []
    for path in sorted(root.rglob("*.md")):
        for match in IMAGE.finditer(path.read_text(encoding="utf-8")):
            if not match.group("alt").strip():
                missing.append(str(path))
    for path in missing:
        print("missing alt text: %s" % path)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
