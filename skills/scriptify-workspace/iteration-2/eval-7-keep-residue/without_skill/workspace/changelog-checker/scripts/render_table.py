#!/usr/bin/env python3
"""Step 5: render the summary table, version descending.

Usage: python3 scripts/render_table.py CHANGELOG_DIR
Exit 0 when every row has a version and date, 1 when any row is `unknown`,
2 on a usage error.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import changelog_lib as lib  # noqa: E402

COLUMNS = lib.ALLOWED_TAGS


def main(argv):
    directory = lib.require_dir(argv)
    rows = []
    incomplete = False

    for parsed in lib.parse_dir(directory):
        counts = {}
        for section in parsed["sections"]:
            counts[section["category"]] = counts.get(section["category"], 0) + len(section["entries"])
        version = parsed["header_version"] or "unknown"
        date = parsed["date"] or "unknown"
        if version == "unknown" or date == "unknown":
            incomplete = True
        rows.append({
            "sort": lib.version_key(parsed["header_version"] or parsed["file_version"] or ""),
            "version": version,
            "date": date,
            "counts": counts,
            "total": sum(counts.values()),
        })

    rows.sort(key=lambda r: r["sort"], reverse=True)

    header = ["Version", "Date"] + COLUMNS + ["Total"]
    print("| " + " | ".join(header) + " |")
    print("|" + "|".join([" --- "] * len(header)) + "|")
    for row in rows:
        cells = [row["version"], row["date"]]
        cells += [str(row["counts"].get(c, 0)) for c in COLUMNS]
        cells.append(str(row["total"]))
        print("| " + " | ".join(cells) + " |")

    return 1 if incomplete else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
