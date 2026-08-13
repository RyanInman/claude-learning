#!/usr/bin/env python3
"""lint_docs.py - Structural lint over a docs tree.

One pass over `<docs-dir>/**/*.md` backs three workflow steps: the sorted file
list and its count, the "starts with a level-1 heading followed by a blank
line" rule, and the fenced-code-block tally.

Named `lint_docs.py` rather than `check_headings.py` because this folder
already ships an unrelated `check_headings.py` that checks image alt text and
is called by the release pipeline at that exact path.

USAGE
    python3 scripts/lint_docs.py <docs-dir> [--json] [--out FILE]

    --json   pretty-print the report to stdout (default; kept explicit so the
             SKILL.md invocation reads unambiguously)
    --out F  write the report to F and print a one-line summary to stdout,
             for trees large enough that the full report would flood context

FINDING CODES
    empty_file              the file has no content at all
    no_h1                   the file has no level-1 heading anywhere
    h1_not_first            the file has a level-1 heading, but not on line 1
    missing_blank_after_h1  line 1 is a level-1 heading and line 2 is not blank

EXIT CODES
    0  every file passes the heading rule
    1  at least one finding
    2  usage error, or <docs-dir> is not a directory
"""

import argparse
import json
import sys
from pathlib import Path

# A level-1 ATX heading: one "#", then whitespace, then text. "## API" must not
# match, so the second character is checked explicitly.
FENCE = "```"


def is_h1(line):
    stripped = line.strip()
    return stripped.startswith("# ") and len(stripped) > 2


def has_h1_anywhere(lines):
    return any(is_h1(line) for line in lines)


def count_fences(lines):
    """Count fenced code blocks: every second fence line closes a block."""
    fences = sum(1 for line in lines if line.lstrip().startswith(FENCE))
    return fences // 2


def check_file(lines):
    """Return a finding code for one file's lines, or None when it passes."""
    if not [line for line in lines if line.strip()]:
        return "empty_file"
    if not is_h1(lines[0]):
        return "h1_not_first" if has_h1_anywhere(lines) else "no_h1"
    if len(lines) > 1 and lines[1].strip():
        return "missing_blank_after_h1"
    return None


def build_report(root):
    paths = sorted(root.rglob("*.md"), key=lambda p: p.as_posix())
    files, findings, fenced = [], [], {}
    for path in paths:
        rel = path.relative_to(root).as_posix()
        files.append(rel)
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError) as exc:
            findings.append({"path": rel, "code": "unreadable", "detail": str(exc)})
            fenced[rel] = 0
            continue
        code = check_file(lines)
        if code:
            findings.append({"path": rel, "code": code})
        fenced[rel] = count_fences(lines)
    return {
        "root": root.as_posix(),
        "file_count": len(files),
        "files": files,
        "findings": findings,
        "fenced_blocks": fenced,
        "fenced_blocks_total": sum(fenced.values()),
    }


def main(argv):
    parser = argparse.ArgumentParser(
        description="Lint a docs tree: file inventory, H1 rule, fence counts."
    )
    parser.add_argument("docs_dir", help="directory to scan for .md files")
    parser.add_argument("--json", action="store_true", help="report to stdout (default)")
    parser.add_argument("--out", help="write the report here; summarize on stdout")
    args = parser.parse_args(argv)

    root = Path(args.docs_dir)
    if not root.is_dir():
        sys.stderr.write("not a directory: %s\n" % root.as_posix())
        return 2

    report = build_report(root)
    text = json.dumps(report, indent=2)
    if args.out:
        try:
            Path(args.out).write_text(text + "\n", encoding="utf-8")
        except OSError as exc:
            sys.stderr.write("cannot write %s: %s\n" % (args.out, exc))
            return 2
        print(
            "%d files, %d fenced blocks, %d findings -> %s"
            % (
                report["file_count"],
                report["fenced_blocks_total"],
                len(report["findings"]),
                args.out,
            )
        )
    else:
        print(text)
    return 1 if report["findings"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
