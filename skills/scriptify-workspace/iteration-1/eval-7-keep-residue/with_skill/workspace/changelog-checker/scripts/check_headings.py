#!/usr/bin/env python3
"""
check_headings.py - Check that every changelog file starts with a version
heading of the exact form `## vX.Y.Z — YYYY-MM-DD` (em dash, ISO date).

USAGE
    python3 scripts/check_headings.py changelogs/ [--json] [--out FILE]

STDOUT
    --json: {"checked": N, "findings": [{file, issue, line, found}]}.
    issue is "missing_version_header" (no version heading anywhere in the
    file) or "malformed_version_header" (a heading that is close but does not
    match the exact form).

EXIT CODES
    0  Every file carries a well-formed version heading.
    1  One or more findings.
    2  Usage error, or the directory is missing or unreadable.
"""

import argparse
import sys

import changelog_lib as cl


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Check every changelog file's version heading.")
    parser.add_argument("directory", help="Folder holding the changelog .md files")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--out", help="Write JSON to FILE, summary to stdout")
    args = parser.parse_args(argv)

    try:
        files = cl.find_files(args.directory)
    except cl.ChangelogError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    findings = []
    for path in files:
        try:
            parsed = cl.parse_file(path)
            lines = path.read_text(encoding="utf-8").splitlines()
        except (cl.ChangelogError, OSError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        first = lines[0] if lines else ""
        if cl.STRICT_HEADING.match(first):
            continue
        if parsed["version"]:
            findings.append({"file": parsed["file"],
                             "issue": "malformed_version_header",
                             "line": parsed["heading_line"],
                             "found": lines[parsed["heading_line"] - 1]})
        else:
            findings.append({"file": parsed["file"],
                             "issue": "missing_version_header",
                             "line": 1, "found": first})

    payload = {"checked": len(files), "findings": findings}
    summary = f"{len(findings)} findings in {len(files)} files"

    if args.json or args.out:
        rc = cl.emit(payload, args.out, summary)
        if rc is not None:
            return rc
    else:
        for f in findings:
            print(f"{f['file']}:{f['line']}  {f['issue']}  {f['found']!r}")
        print(summary)

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
