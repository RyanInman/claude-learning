#!/usr/bin/env python3
"""
scan_changelogs.py - Inventory a changelogs folder and tally entries per category.

Covers two workflow steps of the changelog-checker skill: listing the changelog
files sorted by version with a total count, and counting the entries in each
file per category plus the totals across files.

Files sort by numeric version, so v1.9.0 precedes v1.10.0. A lexical sort gets
that pair backwards. The version comes from the `## vX.Y.Z - YYYY-MM-DD`
heading when the file has one, and from the filename otherwise, so a file
missing its heading still lands in the right place instead of dropping out.
Checking that heading belongs to a separate step; this script only extracts.

Entries are lines starting with `- ` under a `### Category` heading. Categories
outside the counted set (Added, Fixed, Changed, Removed) are tallied under
`other_categories` rather than dropped, because a silently discarded entry
makes the totals lie.

USAGE
    python3 scripts/scan_changelogs.py changelogs/ --json
    python3 scripts/scan_changelogs.py changelogs/ --out scan.json

    No flag prints a one-line summary. --json prints the full scan JSON to
    stdout. --out writes that JSON to a file and prints the summary.

EXIT CODES
    0  Scan produced.
    1  No changelog .md files found in the directory. The JSON is still printed,
       with file_count 0.
    2  Usage error, or the directory is missing or unreadable.
"""

import argparse
import json
import re
import sys
from pathlib import Path

COUNTED = ("Added", "Fixed", "Changed", "Removed")
HEADING_RE = re.compile(r"^##\s+v(\d+\.\d+\.\d+)\s*[—-]\s*(\d{4}-\d{2}-\d{2})")
FILENAME_VERSION_RE = re.compile(r"v?(\d+\.\d+\.\d+)")
CATEGORY_RE = re.compile(r"^###\s+(.+?)\s*$")
ENTRY_RE = re.compile(r"^[-*]\s+\S")
# Files with no parseable version sort after every parseable one.
UNPARSEABLE_VERSION_KEY = (float("inf"),)


def version_key(version):
    if version is None:
        return UNPARSEABLE_VERSION_KEY
    return tuple(int(part) for part in version.split("."))


def scan_file(path):
    """Return one file's version, date, and per-category entry counts."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    version, date = None, None
    for line in lines:
        m = HEADING_RE.match(line)
        if m:
            version, date = m.group(1), m.group(2)
            break
    if version is None:
        m = FILENAME_VERSION_RE.search(path.stem)
        if m:
            version = m.group(1)

    counts = {name: 0 for name in COUNTED}
    other = {}
    category = None
    for line in lines:
        m = CATEGORY_RE.match(line)
        if m:
            category = m.group(1)
            continue
        if category and ENTRY_RE.match(line):
            if category in counts:
                counts[category] += 1
            else:
                other[category] = other.get(category, 0) + 1

    return {
        "file": path.name,
        "version": version,
        "date": date,
        "counts": counts,
        "other_counts": other,
        "total": sum(counts.values()) + sum(other.values()),
    }


def scan(directory):
    files = sorted(directory.glob("*.md"))
    records = [scan_file(p) for p in files]
    records.sort(key=lambda r: (version_key(r["version"]), r["file"]))

    totals = {name: sum(r["counts"][name] for r in records) for name in COUNTED}
    other_totals = {}
    for r in records:
        for name, n in r["other_counts"].items():
            other_totals[name] = other_totals.get(name, 0) + n

    return {
        "changelog_dir": directory.as_posix(),
        "file_count": len(records),
        "files": [r["file"] for r in records],
        "versions": records,
        "totals": totals,
        "other_categories": other_totals,
        "total_entries": sum(totals.values()) + sum(other_totals.values()),
    }


def summarize(result):
    counted = ", ".join(f"{k} {v}" for k, v in result["totals"].items())
    line = (f"{result['file_count']} changelog files, "
            f"{result['total_entries']} entries ({counted})")
    if result["other_categories"]:
        other = ", ".join(f"{k} {v}" for k, v in sorted(result["other_categories"].items()))
        line += f"; outside the counted set: {other}"
    return line


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="List changelog files sorted by version and count entries per category.")
    parser.add_argument("directory", help="Folder holding the changelog .md files")
    parser.add_argument("--json", action="store_true",
                        help="Print the full scan JSON to stdout")
    parser.add_argument("--out", help="Write the scan JSON here and print the summary")
    args = parser.parse_args(argv)

    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"error: not a directory: {directory}", file=sys.stderr)
        return 2

    try:
        result = scan(directory)
    except OSError as e:
        print(f"error: cannot read {directory}: {e}", file=sys.stderr)
        return 2
    except UnicodeDecodeError as e:
        print(f"error: {directory} holds a file that is not UTF-8 text: {e}",
              file=sys.stderr)
        return 2

    payload = json.dumps(result, indent=2)
    if args.out:
        try:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(payload + "\n", encoding="utf-8")
        except OSError as e:
            print(f"error: cannot write {args.out}: {e}", file=sys.stderr)
            return 2

    if args.json and not args.out:
        print(payload)
    else:
        print(summarize(result))

    if result["file_count"] == 0:
        print(f"error: no .md files in {directory}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
