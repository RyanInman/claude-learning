#!/usr/bin/env python3
"""
check_headings.py - Check that every changelog file starts with a version
header of the form `## vX.Y.Z — YYYY-MM-DD` (em dash U+2014).

USAGE
    python3 scripts/check_headings.py <changelogs-dir> [--json] [--out FILE]

    --json   full JSON on stdout (default is a one-line summary)
    --out F  write the full JSON to F, keep the summary on stdout

STDOUT (--json)
    {"dir", "checked", "findings": [{"file", "issue", "found"}]}
    issue is always "missing_version_header"; found holds the offending first
    line so the fix is obvious without reopening the file.

EXIT CODES
    0  Every file carries a well-formed version header.
    1  At least one file does not (findings on stdout).
    2  Usage error, or the directory is missing or unreadable.
"""

import argparse
import json
import sys

import _changelog

ISSUE = "missing_version_header"


def check(directory):
    parsed = _changelog.load_dir(directory)
    findings = [
        {"file": p["file"], "issue": ISSUE, "found": p["header_line"]}
        for p in parsed if not p["header_ok"]
    ]
    return {"dir": directory, "checked": len(parsed), "findings": findings}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Check every changelog starts with `## vX.Y.Z — YYYY-MM-DD`.")
    parser.add_argument("directory", help="Folder holding the .md changelogs")
    parser.add_argument("--json", action="store_true",
                        help="Print the full JSON instead of a summary line")
    parser.add_argument("--out", help="Write the full JSON to this file")
    args = parser.parse_args(argv)

    try:
        result = check(args.directory)
    except (OSError, ValueError) as e:
        return _changelog.die_unreadable(e)

    blob = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(blob + "\n")
        except OSError as e:
            return _changelog.die_unreadable(e)

    if args.json:
        print(blob)
    else:
        print(f"checked {result['checked']} file(s): "
              f"{len(result['findings'])} missing a version header")

    return 1 if result["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())
