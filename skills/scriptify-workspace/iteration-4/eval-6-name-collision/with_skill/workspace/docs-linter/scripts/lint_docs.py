#!/usr/bin/env python3
"""Lint a docs tree: file inventory, level-1 heading rule, fenced-block counts.

One pass over <docs-dir> answers the three mechanical questions the docs-linter
workflow asks: which markdown files exist, which ones break the level-1 heading
rule, and how many fenced code blocks each one holds.

This is NOT scripts/check_headings.py. That script, despite its name, checks
image alt text and is called by the release pipeline at that exact path, so it
is left alone.

FINDING CODES (a file can trip more than one)
    first_line_not_h1      line 1 is not a `# ` heading
    no_h1_anywhere         no line in the file is a `# ` heading
    h1_missing_blank_line  line 1 is a `# ` heading but line 2 is not blank

USAGE
    python3 scripts/lint_docs.py <docs-dir> [--json] [--out FILE]

    --json   print the full JSON report to stdout (the data contract)
    --out F  write the JSON report to F and keep stdout to a one-line summary

EXIT CODES
    0  no heading findings
    1  at least one heading finding
    2  usage error, or <docs-dir> is missing or unreadable
"""

import argparse
import json
import sys
from pathlib import Path

FENCE = "```"


def scan_file(text):
    """Return (finding codes, fenced-block count) for one file's text."""
    lines = text.splitlines()
    codes = []
    first = lines[0] if lines else ""
    has_h1_anywhere = any(ln.startswith("# ") for ln in lines)
    if not first.startswith("# "):
        codes.append("first_line_not_h1")
    elif len(lines) < 2 or lines[1].strip():
        # An H1 with nothing after it is also unseparated from its body.
        codes.append("h1_missing_blank_line")
    if not has_h1_anywhere:
        codes.append("no_h1_anywhere")
    fences = sum(1 for ln in lines if ln.lstrip().startswith(FENCE))
    return codes, fences // 2  # opener + closer make one block


def scan_tree(root):
    files, findings, fence_counts = [], [], {}
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as e:
            sys.stderr.write("cannot read %s: %s\n" % (rel, e))
            return None
        files.append(rel)
        codes, fences = scan_file(text)
        fence_counts[rel] = fences
        if codes:
            findings.append({"file": rel, "codes": codes})
    return {
        "root": root.as_posix(),
        "files": files,
        "file_count": len(files),
        "h1_findings": findings,
        "fence_counts": fence_counts,
        "fence_total": sum(fence_counts.values()),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Lint a docs tree for the level-1 heading rule and count "
                    "files and fenced code blocks.")
    ap.add_argument("docs_dir", help="directory to scan recursively for *.md")
    ap.add_argument("--json", action="store_true",
                    help="print the full JSON report to stdout")
    ap.add_argument("--out", help="write the JSON report here instead")
    args = ap.parse_args(argv)

    root = Path(args.docs_dir)
    if not root.is_dir():
        sys.stderr.write("not a directory: %s\n" % args.docs_dir)
        return 2

    report = scan_tree(root)
    if report is None:
        return 2

    summary = "%d files, %d heading findings, %d fenced blocks" % (
        report["file_count"], len(report["h1_findings"]), report["fence_total"])

    if args.out:
        try:
            Path(args.out).write_text(json.dumps(report, indent=2) + "\n",
                                      encoding="utf-8")
        except OSError as e:
            sys.stderr.write("cannot write %s: %s\n" % (args.out, e))
            return 2
        print("%s -> %s" % (summary, args.out))
    elif args.json:
        print(json.dumps(report, indent=2))
    else:
        print(summary)

    return 1 if report["h1_findings"] else 0


if __name__ == "__main__":
    sys.exit(main())
