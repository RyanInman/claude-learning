#!/usr/bin/env python3
"""Inventory the markdown under a docs tree and flag structural problems.

Covers three deterministic checks that the docs-linter workflow used to do by
hand: listing the files, verifying the level-1 heading opener, and counting
fenced code blocks.

This is a separate file from scripts/check_headings.py, which despite its name
checks image alt text and is called by the release pipeline at that exact path.

Usage:
    python3 scripts/lint_docs_structure.py <docs-dir> [--json]

Output:
    Human-readable report by default, or a JSON object with --json.

Exit codes:
    0  every file opens with a level-1 heading followed by a blank line
    1  at least one file does not
    2  usage error
"""

import json
import sys
from pathlib import Path

FENCE_CHARS = ("```", "~~~")


def check_opening(lines):
    """Return None if the file opens correctly, else the reason it does not."""
    if not lines:
        return "file is empty"
    first = lines[0].rstrip("\n")
    if not first.startswith("# ") or first.startswith("##"):
        return "first line is not a level-1 heading: %r" % first[:60]
    if len(lines) < 2:
        return "level-1 heading is not followed by a blank line"
    if lines[1].strip():
        return "level-1 heading is not followed by a blank line"
    return None


def count_fences(lines):
    """Count fenced code blocks. A block is an opening fence plus its closer."""
    open_fence = None
    blocks = 0
    for line in lines:
        stripped = line.strip()
        if open_fence is None:
            for char in FENCE_CHARS:
                if stripped.startswith(char):
                    open_fence = char
                    break
        elif stripped.startswith(open_fence):
            blocks += 1
            open_fence = None
    if open_fence is not None:
        blocks += 1  # unterminated fence still counts as one block
    return blocks


def scan(root):
    files = []
    for path in sorted(root.rglob("*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        files.append(
            {
                "path": str(path.relative_to(root)),
                "opening_problem": check_opening(lines),
                "code_blocks": count_fences(lines),
            }
        )
    return {
        "docs_dir": str(root),
        "file_count": len(files),
        "files": files,
        "flagged": [f["path"] for f in files if f["opening_problem"]],
        "total_code_blocks": sum(f["code_blocks"] for f in files),
    }


def render(result):
    out = ["%d markdown file(s) under %s" % (result["file_count"], result["docs_dir"]), ""]
    for entry in result["files"]:
        status = entry["opening_problem"] or "ok"
        out.append(
            "  %-28s  %-2d code block(s)  %s"
            % (entry["path"], entry["code_blocks"], status)
        )
    out.append("")
    out.append("total code blocks: %d" % result["total_code_blocks"])
    out.append(
        "flagged for heading structure: %s"
        % (", ".join(result["flagged"]) if result["flagged"] else "none")
    )
    return "\n".join(out)


def main(argv):
    args = [a for a in argv[1:] if a != "--json"]
    as_json = "--json" in argv[1:]
    if len(args) != 1:
        sys.stderr.write(__doc__)
        return 2
    root = Path(args[0])
    if not root.is_dir():
        sys.stderr.write("not a directory: %s\n" % root)
        return 2
    result = scan(root)
    print(json.dumps(result, indent=2) if as_json else render(result))
    return 1 if result["flagged"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
