#!/usr/bin/env python3
"""Inventory a docs tree: file list, missing level-1 headings, fenced code block counts.

Covers steps 1-3 of the docs-linter workflow in one pass. Step 4 (which files to
fix first) is a judgment call and stays with the model.

Usage:
    python3 scripts/lint_docs.py [docs-dir]     # docs-dir defaults to "docs"

Output:
    JSON on stdout. Keys:
      docs_dir          the directory scanned
      file_count        number of .md files found
      files             every .md file, path-relative and sorted
      missing_h1        files whose first line is not a level-1 heading followed
                        by a blank line, each with the reason
      code_blocks       fenced code block count per file, same order as files
      total_code_blocks sum of code_blocks

Exit codes:
    0  scan completed (findings live in the JSON, not the exit code)
    2  usage error or missing directory
"""

import json
import sys
from pathlib import Path


def check_h1(lines):
    """Return None if the file opens with an H1 plus blank line, else the reason."""
    if not lines:
        return "file is empty"
    if not lines[0].startswith("# "):
        return "first line is not a level-1 heading"
    if len(lines) > 1 and lines[1].strip():
        return "no blank line after the level-1 heading"
    return None


def count_code_blocks(lines):
    """Count opening fences. Toggles on ``` or ~~~ so fences inside a block do not double-count."""
    count = 0
    open_fence = None
    for line in lines:
        stripped = line.strip()
        marker = stripped[:3]
        if marker not in ("```", "~~~"):
            continue
        if open_fence is None:
            open_fence = marker
            count += 1
        elif marker == open_fence:
            open_fence = None
    return count


def main(argv):
    if len(argv) > 2:
        sys.stderr.write(__doc__)
        return 2
    root = Path(argv[1]) if len(argv) == 2 else Path("docs")
    if not root.is_dir():
        sys.stderr.write("not a directory: %s\n" % root)
        return 2

    paths = sorted(root.rglob("*.md"))
    files, missing, blocks = [], [], {}
    for path in paths:
        rel = path.as_posix()
        files.append(rel)
        lines = path.read_text(encoding="utf-8").splitlines()
        reason = check_h1(lines)
        if reason:
            missing.append({"file": rel, "reason": reason})
        blocks[rel] = count_code_blocks(lines)

    json.dump({
        "docs_dir": root.as_posix(),
        "file_count": len(files),
        "files": files,
        "missing_h1": missing,
        "code_blocks": blocks,
        "total_code_blocks": sum(blocks.values()),
    }, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
