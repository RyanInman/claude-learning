#!/usr/bin/env python3
"""List every markdown file under a docs tree, sorted by path, with a total count.

Backs workflow step 1 of the docs-linter skill.
"""

import argparse
import json
import sys
from pathlib import Path


def collect(root: Path):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*.md"))


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

    files = collect(root)
    if args.json:
        print(json.dumps({"root": str(root), "files": files, "count": len(files)}, indent=2))
    else:
        for name in files:
            print(name)
        print("total: %d" % len(files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
