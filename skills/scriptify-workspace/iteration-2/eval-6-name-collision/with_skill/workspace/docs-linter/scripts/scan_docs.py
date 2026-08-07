#!/usr/bin/env python3
"""
scan_docs.py - Inventory a docs tree: every .md file sorted by path, the file
count, the fenced code blocks per file, and the total across files.

A fenced code block is one pair of ``` fence lines; an unclosed trailing fence
still counts as one block.

USAGE
    python3 scripts/scan_docs.py <docs-dir> [--json] [--out FILE]

EXIT CODES
    0  scan completed (this script reports, it does not judge)
    2  usage error / unreadable directory
"""

import argparse
import json
import sys
from pathlib import Path

FENCE = "```"


def count_code_blocks(text):
    fences = sum(1 for line in text.splitlines() if line.strip().startswith(FENCE))
    return (fences + 1) // 2  # an unclosed trailing fence still opens a block


def scan(root):
    files = []
    code_blocks = {}
    total = 0
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root).as_posix()
        files.append(rel)
        n = count_code_blocks(path.read_text(encoding="utf-8"))
        code_blocks[rel] = n
        total += n
    return {"root": root.as_posix(), "files": files, "file_count": len(files),
            "code_blocks": code_blocks, "total_code_blocks": total}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="List the .md files under a docs tree and count fenced code blocks.")
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
        print("%d file(s), %d code block(s) -> %s"
              % (result["file_count"], result["total_code_blocks"], args.out))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
