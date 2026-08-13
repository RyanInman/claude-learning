#!/usr/bin/env python3
"""List changelog files sorted by version and report the total count.

Usage: list_changelogs.py [CHANGELOGS_DIR]

Prints JSON: {"files": [{"file": ..., "version": [maj, min, patch]}], "count": N}
Files whose names carry no vX.Y.Z version sort last, alphabetically.
"""
import json
import re
import sys
from pathlib import Path

VERSION_RE = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")


def sort_key(path: Path):
    m = VERSION_RE.search(path.stem)
    if m:
        return (0, tuple(int(g) for g in m.groups()), path.name)
    return (1, (0, 0, 0), path.name)


def main() -> int:
    directory = Path(sys.argv[1] if len(sys.argv) > 1 else "changelogs")
    if not directory.is_dir():
        print(f"error: not a directory: {directory}", file=sys.stderr)
        return 1
    files = sorted(directory.glob("*.md"), key=sort_key)
    result = {
        "files": [
            {
                "file": p.name,
                "version": (
                    [int(g) for g in VERSION_RE.search(p.stem).groups()]
                    if VERSION_RE.search(p.stem)
                    else None
                ),
            }
            for p in files
        ],
        "count": len(files),
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
