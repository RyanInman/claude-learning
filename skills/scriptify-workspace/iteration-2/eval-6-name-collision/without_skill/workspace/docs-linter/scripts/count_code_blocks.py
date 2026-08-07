#!/usr/bin/env python3
"""Count fenced code blocks per markdown file and total them across the tree.

Backs workflow step 3 of the docs-linter skill. A block is one opening fence
(``` or ~~~) plus its matching closing fence; an unclosed opening fence still
counts as one block.
"""

import argparse
import json
import sys
from pathlib import Path


def count_blocks(text: str) -> int:
    blocks = 0
    fence = None
    for line in text.splitlines():
        stripped = line.strip()
        if fence is None:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                fence = stripped[:3]
                blocks += 1
        elif stripped.startswith(fence):
            fence = None
    return blocks


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

    per_file = []
    total = 0
    for path in sorted(root.rglob("*.md")):
        n = count_blocks(path.read_text(encoding="utf-8"))
        per_file.append({"file": str(path.relative_to(root)), "code_blocks": n})
        total += n

    if args.json:
        print(json.dumps({"files": per_file, "total": total}, indent=2))
    else:
        for item in per_file:
            print("%s: %d" % (item["file"], item["code_blocks"]))
        print("total: %d" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
