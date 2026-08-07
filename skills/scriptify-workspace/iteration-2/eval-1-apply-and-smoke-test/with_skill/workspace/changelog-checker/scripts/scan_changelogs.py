#!/usr/bin/env python3
"""
scan_changelogs.py - Inventory a changelogs folder: files sorted by version,
per-file per-category entry counts, cross-file totals, and every entry's text.

One scan feeds three workflow steps: the file list and count, the per-category
tallies, and the enumerated entries Claude judges for clarity.

USAGE
    python3 scripts/scan_changelogs.py <changelogs-dir> [--json] [--out FILE]

    --json   full JSON on stdout (default is a one-line summary)
    --out F  write the full JSON to F, keep the summary on stdout

STDOUT (--json)
    {"dir", "file_count", "files": [{"file", "version", "date", "counts",
     "entries": [{"category", "text"}]}], "totals"}
    files is sorted by version ascending.

EXIT CODES
    0  Scanned at least one changelog file.
    1  No .md files in the directory (JSON still printed, file_count 0).
    2  Usage error, or the directory is missing or unreadable.
"""

import argparse
import json
import sys

import _changelog


def scan(directory):
    parsed = _changelog.load_dir(directory)
    totals = {c: 0 for c in _changelog.COUNTED_CATEGORIES}
    totals["entries"] = 0
    files = []
    for p in parsed:
        for cat in _changelog.COUNTED_CATEGORIES:
            totals[cat] += p["counts"][cat]
        totals["entries"] += len(p["entries"])
        files.append({
            "file": p["file"],
            "version": p["version"],
            "date": p["date"],
            "counts": p["counts"],
            "entries": p["entries"],
        })
    return {
        "dir": directory,
        "file_count": len(files),
        "files": files,
        "totals": totals,
    }


def summary_line(result):
    t = result["totals"]
    per_cat = " ".join(f"{c}={t[c]}" for c in _changelog.COUNTED_CATEGORIES)
    return (f"scanned {result['file_count']} file(s) in {result['dir']}: "
            f"{t['entries']} entries ({per_cat})")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Scan a changelogs folder: files, counts, totals, entries.")
    parser.add_argument("directory", help="Folder holding the .md changelogs")
    parser.add_argument("--json", action="store_true",
                        help="Print the full JSON instead of a summary line")
    parser.add_argument("--out", help="Write the full JSON to this file")
    args = parser.parse_args(argv)

    try:
        result = scan(args.directory)
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
        print(summary_line(result))

    if result["file_count"] == 0:
        print(f"error: no .md changelog files in {args.directory}",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
