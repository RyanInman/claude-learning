#!/usr/bin/env python3
"""Step 2: check every changelog opens with `## vX.Y.Z - YYYY-MM-DD`.

Usage: python3 scripts/check_headings.py CHANGELOG_DIR [--json]
Exit 0 when every file has a valid header, 1 when any file fails,
2 on a usage error.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import changelog_lib as lib  # noqa: E402


def main(argv):
    directory = lib.require_dir(argv)
    findings = []

    for parsed in lib.parse_dir(directory):
        if parsed["header_version"] is None:
            findings.append({
                "file": parsed["name"],
                "issue": "missing_version_header",
                "detail": "no line matching '## vX.Y.Z - YYYY-MM-DD'",
            })
            continue
        if parsed["file_version"] and parsed["header_version"] != parsed["file_version"]:
            findings.append({
                "file": parsed["name"],
                "issue": "version_mismatch",
                "detail": "header says v%s, filename says v%s"
                          % (parsed["header_version"], parsed["file_version"]),
            })

    result = {"dir": os.path.abspath(directory), "findings": findings}

    if lib.wants_json(argv):
        print(json.dumps(result, indent=2))
    else:
        if not findings:
            print("all headers valid")
        for f in findings:
            print("%s\t%s\t%s" % (f["file"], f["issue"], f["detail"]))

    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
