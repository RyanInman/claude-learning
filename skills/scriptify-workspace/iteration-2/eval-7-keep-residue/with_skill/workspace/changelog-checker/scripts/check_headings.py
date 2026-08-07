#!/usr/bin/env python3
"""
check_headings.py - Flag changelog files that do not open with a version heading.

Every file must start with `## vX.Y.Z — YYYY-MM-DD` (em dash). A file whose
first non-blank line is not that heading is reported as
missing_version_header, or as malformed_version_header when the line looks
like a version heading but does not match the form.

USAGE
    python3 scripts/check_headings.py <changelogs-dir> --json [--out FILE]

EXIT CODES
    0  Every file opens with a well-formed version heading.
    1  Findings (JSON on stdout under "findings").
    2  Usage error, or the directory is missing/unreadable.
"""

import argparse
import json
import sys
from pathlib import Path

import _changelog as cl


def check(dirpath):
    findings = []
    for record in cl.parse_dir(dirpath):
        if record["heading_status"] != "ok":
            findings.append({"file": record["file"],
                             "reason": record["heading_status"]})
    return findings


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    p.add_argument("changelogs_dir", help="folder holding the changelog .md files")
    p.add_argument("--json", action="store_true",
                   help="emit findings as JSON (default, kept for explicitness)")
    p.add_argument("--out", help="write JSON here; print a summary to stdout")
    args = p.parse_args(argv)

    try:
        findings = check(args.changelogs_dir)
    except NotADirectoryError as e:
        cl.fail(str(e), 2)
    except OSError as e:
        cl.fail(f"cannot read {args.changelogs_dir}: {e}", 2)

    report = {"changelogs_dir": args.changelogs_dir, "findings": findings}
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        try:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(text + "\n", encoding="utf-8")
        except OSError as e:
            cl.fail(f"cannot write {args.out}: {e}", 2)
        print(f"{len(findings)} heading findings -> {args.out}")
    else:
        print(text)

    if findings:
        print(f"{len(findings)} file(s) without a valid version heading",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
