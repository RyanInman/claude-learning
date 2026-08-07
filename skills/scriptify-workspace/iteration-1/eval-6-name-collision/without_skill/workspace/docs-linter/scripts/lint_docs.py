#!/usr/bin/env python3
"""Inventory a docs tree and report heading and fenced-code-block facts.

Covers workflow steps 1-3 of the docs-linter skill in one pass:
  1. list every .md file under the docs dir, sorted by path, with a total count
  2. flag every file that does not start with a level-1 heading followed by a
     blank line
  3. count fenced code blocks per file and in total

Not to be confused with scripts/check_headings.py, which despite its name
checks image alt text and is called by path from the release pipeline.

Usage:
    python3 scripts/lint_docs.py <docs-dir> [--json]

Exit codes:
    0  every file passes the heading check
    1  at least one file fails the heading check
    2  usage error
"""

import json
import re
import sys
from pathlib import Path

H1 = re.compile(r"^# +\S")
FENCE_OPEN = re.compile(r"^ {0,3}(?P<marker>`{3,}|~{3,})(?P<info>.*)$")


def fence_count(lines):
    """Count opening fences, honouring marker char, length, and open state."""
    count = 0
    marker = None
    for line in lines:
        if marker is None:
            match = FENCE_OPEN.match(line)
            if not match:
                continue
            opener = match.group("marker")
            # A backtick fence's info string may not contain a backtick.
            if opener[0] == "`" and "`" in match.group("info"):
                continue
            marker = opener
            count += 1
            continue
        closer = re.match(r"^ {0,3}(?P<marker>%s{%d,}) *$" % (marker[0], len(marker)), line)
        if closer:
            marker = None
    return count


def heading_issue(lines):
    """Return a reason string if the level-1 heading rule fails, else None."""
    if not lines:
        return "file is empty"
    if not H1.match(lines[0]):
        return "line 1 is not a level-1 heading"
    if len(lines) > 1 and lines[1].strip():
        return "no blank line after the level-1 heading"
    return None


def scan(root):
    files = []
    for path in sorted(root.rglob("*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        files.append(
            {
                "path": str(path),
                "heading_issue": heading_issue(lines),
                "fences": fence_count(lines),
            }
        )
    return {
        "root": str(root),
        "file_count": len(files),
        "files": files,
        "heading_failures": [f["path"] for f in files if f["heading_issue"]],
        "total_fences": sum(f["fences"] for f in files),
    }


def render(result):
    out = ["docs root: %s" % result["root"], "markdown files: %d" % result["file_count"], ""]
    width = max([len("file")] + [len(f["path"]) for f in result["files"]])
    out.append("%-*s  fences  heading" % (width, "file"))
    for entry in result["files"]:
        out.append(
            "%-*s  %6d  %s"
            % (width, entry["path"], entry["fences"], entry["heading_issue"] or "ok")
        )
    out.append("")
    out.append("total fenced code blocks: %d" % result["total_fences"])
    out.append("heading failures: %d" % len(result["heading_failures"]))
    for path in result["heading_failures"]:
        out.append("  %s" % path)
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
    return 1 if result["heading_failures"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
