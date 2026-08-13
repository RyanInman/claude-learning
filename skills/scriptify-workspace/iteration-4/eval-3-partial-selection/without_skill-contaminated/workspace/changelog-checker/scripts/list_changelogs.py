#!/usr/bin/env python3
"""List changelog .md files sorted by version, with the total count."""

import argparse
import re
import sys
from pathlib import Path

VERSION_RE = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")


def sort_key(path):
    """Sort by numeric semver from the filename; unparseable names sort last by name."""
    m = VERSION_RE.search(path.stem)
    if m:
        return (0, tuple(int(g) for g in m.groups()), path.name)
    return (1, (0, 0, 0), path.name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("changelog_dir", help="directory holding the changelog .md files")
    parser.add_argument("--descending", action="store_true", help="sort newest version first")
    args = parser.parse_args()

    directory = Path(args.changelog_dir)
    if not directory.is_dir():
        print(f"error: not a directory: {directory}", file=sys.stderr)
        return 2

    files = sorted(directory.glob("*.md"), key=sort_key, reverse=args.descending)
    if not files:
        print(f"error: no .md files in {directory}", file=sys.stderr)
        return 1

    for path in files:
        print(path.name)
    print(f"total: {len(files)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
