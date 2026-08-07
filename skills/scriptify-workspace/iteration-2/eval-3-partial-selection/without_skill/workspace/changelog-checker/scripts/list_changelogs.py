#!/usr/bin/env python3
"""List changelog .md files sorted by version, with a total count.

Usage:
    python3 scripts/list_changelogs.py [CHANGELOG_DIR] [--json]

Default CHANGELOG_DIR is "changelogs" relative to the current directory.
Version order comes from the leading vX.Y.Z in the filename; files without a
parseable version sort last, alphabetically.
"""

import argparse
import json
import re
import sys
from pathlib import Path

VERSION_RE = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")


def version_key(path: Path):
    m = VERSION_RE.search(path.stem)
    if not m:
        return (1, (0, 0, 0), path.name)
    return (0, tuple(int(g) for g in m.groups()), path.name)


def collect(directory: Path):
    files = sorted(directory.glob("*.md"), key=version_key)
    return [
        {
            "file": f.name,
            "path": str(f),
            "version": (
                VERSION_RE.search(f.stem).group(0).lstrip("v")
                if VERSION_RE.search(f.stem)
                else None
            ),
        }
        for f in files
    ]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="changelogs")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"error: not a directory: {directory}", file=sys.stderr)
        return 1

    entries = collect(directory)
    result = {"directory": str(directory), "count": len(entries), "files": entries}

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for e in entries:
            print(f"{e['version'] or '?':<10} {e['file']}")
        print(f"total: {len(entries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
