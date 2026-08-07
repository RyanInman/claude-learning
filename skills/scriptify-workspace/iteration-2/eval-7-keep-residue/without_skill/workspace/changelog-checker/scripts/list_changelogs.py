#!/usr/bin/env python3
"""Step 1: list changelog files sorted by version and report the count.

Usage: python3 scripts/list_changelogs.py CHANGELOG_DIR [--json]
Exit 0 when at least one changelog is found, 1 when the folder holds none,
2 on a usage error.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import changelog_lib as lib  # noqa: E402


def main(argv):
    directory = lib.require_dir(argv)
    files = lib.list_files(directory)
    result = {
        "dir": os.path.abspath(directory),
        "count": len(files),
        "versions": [lib.filename_version(p) for p in files],
        "files": [os.path.basename(p) for p in files],
    }

    if lib.wants_json(argv):
        print(json.dumps(result, indent=2))
    else:
        print("count: %d" % result["count"])
        for name, version in zip(result["files"], result["versions"]):
            print("%s\t%s" % (version, name))

    return 0 if files else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
