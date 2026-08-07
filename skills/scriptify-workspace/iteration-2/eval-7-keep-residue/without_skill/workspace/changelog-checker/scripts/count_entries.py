#!/usr/bin/env python3
"""Step 3: count entries per category per file, plus totals across files.

Usage: python3 scripts/count_entries.py CHANGELOG_DIR [--json]
Exit 0 when at least one entry is counted, 1 when the folder yields none,
2 on a usage error.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import changelog_lib as lib  # noqa: E402


def main(argv):
    directory = lib.require_dir(argv)
    per_file = []
    totals = {}
    total_entries = 0

    for parsed in lib.parse_dir(directory):
        counts = {}
        for section in parsed["sections"]:
            n = len(section["entries"])
            counts[section["category"]] = counts.get(section["category"], 0) + n
            totals[section["category"]] = totals.get(section["category"], 0) + n
            total_entries += n
        per_file.append({
            "file": parsed["name"],
            "version": parsed["header_version"] or parsed["file_version"],
            "date": parsed["date"],
            "counts": counts,
            "total": sum(counts.values()),
        })

    ordered = {}
    for category in lib.ALLOWED_TAGS:
        ordered[category] = totals.get(category, 0)
    for category in sorted(totals):
        if category not in ordered:
            ordered[category] = totals[category]

    result = {
        "dir": os.path.abspath(directory),
        "per_file": per_file,
        "totals": ordered,
        "total_entries": total_entries,
    }

    if lib.wants_json(argv):
        print(json.dumps(result, indent=2))
    else:
        for row in per_file:
            print("%s\t%s\t%d" % (row["file"], row["counts"], row["total"]))
        print("totals: %s" % ordered)
        print("total_entries: %d" % total_entries)

    return 0 if total_entries else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
