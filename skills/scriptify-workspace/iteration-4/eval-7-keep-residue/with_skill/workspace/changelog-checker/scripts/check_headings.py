#!/usr/bin/env python3
"""
check_headings.py - Verify every changelog file opens with `## vX.Y.Z - YYYY-MM-DD`.

Three conditions get three finding codes, because a caller that reads the code
should not have to guess which one it hit:
    no_h2_first_line          the first non-empty line is not an H2 at all
    h2_not_version_dated      an H2 is there but it is not `vX.Y.Z - YYYY-MM-DD`
    version_filename_mismatch the heading version disagrees with the filename

The em dash and the en dash both count as the separator, because editors
substitute them silently.

USAGE
    python3 scripts/check_headings.py <changelogs-dir> [--json]

EXIT CODES
    0  Every file has a well-formed, matching heading.
    1  Findings; the JSON on stdout names each one.
    2  Usage error, or the folder is missing or unreadable.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_changelogs import parse_file, sorted_files  # noqa: E402


def check(directory):
    findings = []
    files = sorted_files(directory)
    for path in files:
        info = parse_file(path)
        if not info["heading_ok"]:
            code = "h2_not_version_dated" if info["first_line_is_h2"] else "no_h2_first_line"
            findings.append({
                "code": code,
                "file": info["file"],
                "detail": f'first line is {info["first_line"]!r}; expected "## v{info["file_version"] or "X.Y.Z"} - YYYY-MM-DD"',
            })
        elif info["file_version"] and info["version"] != info["file_version"]:
            findings.append({
                "code": "version_filename_mismatch",
                "file": info["file"],
                "detail": f'heading says v{info["version"]}, filename says v{info["file_version"]}',
            })
    return {"dir": Path(directory).as_posix(), "checked": len(files), "findings": findings}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Verify every changelog file opens with a dated version heading.")
    ap.add_argument("directory", help="Folder holding the changelog .md files")
    ap.add_argument("--json", action="store_true", help="Print JSON (the default and only format; accepted for symmetry)")
    args = ap.parse_args(argv)

    d = Path(args.directory)
    if not d.is_dir():
        print(f"check_headings: not a directory: {args.directory}", file=sys.stderr)
        return 2
    try:
        result = check(d)
    except OSError as e:
        print(f"check_headings: cannot read {args.directory}: {e}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2))
    return 1 if result["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())
