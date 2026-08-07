#!/usr/bin/env python3
"""Inventory a docs tree: the markdown files, and the code blocks in each.

Covers two mechanical steps at once, off one traversal: list every *.md sorted
by path with a total count, and count fenced code blocks per file plus the
total across files. A fence is a line whose first non-space characters are ```
or ~~~; fences toggle, so an unclosed final fence still counts as one block.

Usage:
    python3 scripts/docs_stats.py <docs-dir> [--out FILE]

Exit codes:
    0  stats emitted (a tree with no markdown is a valid result, not an error)
    2  usage error, or <docs-dir> is not a readable directory
"""

import argparse
import json
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^\s*(```|~~~)")


def count_code_blocks(text):
    """Count fenced blocks by toggling; an unclosed final fence counts as one."""
    blocks = 0
    inside = False
    for line in text.splitlines():
        if FENCE.match(line):
            if not inside:
                blocks += 1
            inside = not inside
    return blocks


def collect(root):
    files = []
    per_file = {}
    total = 0
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root).as_posix()
        files.append(rel)
        n = count_code_blocks(path.read_text(encoding="utf-8", errors="replace"))
        per_file[rel] = n
        total += n
    return {"docs_dir": root.as_posix(), "files": files, "file_count": len(files),
            "code_blocks": per_file, "total_code_blocks": total}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="List the markdown files under a docs tree and count the "
                    "fenced code blocks in each.")
    parser.add_argument("docs_dir", help="Directory to scan recursively for *.md")
    parser.add_argument("--out", help="Write the stats JSON here; print a "
                                      "one-line summary to stdout instead")
    args = parser.parse_args(argv)

    root = Path(args.docs_dir)
    if not root.is_dir():
        sys.stderr.write("not a directory: %s\n" % root)
        return 2

    try:
        result = collect(root)
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
        print("%d markdown file(s), %d code block(s) -> %s"
              % (result["file_count"], result["total_code_blocks"], args.out))
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
