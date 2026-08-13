#!/usr/bin/env python3
"""
scan_changelogs.py - Parse a changelogs folder into one structured scan.

Lists every `.md` file sorted by version, reads each file's version heading,
tallies entries per category, totals them across files, and carries every entry
text so a reader never has to open the files. render_summary.py consumes this
scan; the clarity review reads its `entries`.

USAGE
    python3 scripts/scan_changelogs.py changelogs/ --out scan.json
    python3 scripts/scan_changelogs.py changelogs/ --json

    --out FILE   write the full scan JSON to FILE, print a compact summary
    --json       print the full scan JSON to stdout instead

STDOUT
    Compact summary (default): file count, entry total, one line per file.
    Full scan JSON with --json.

EXIT CODES
    0  Scan produced.
    1  No `.md` files in the folder (nothing to check).
    2  Usage error, missing folder, or unreadable file.
"""

import argparse
import json
import re
import sys
from pathlib import Path

CATEGORIES = ["Added", "Fixed", "Changed", "Removed", "Misc"]
VERSION_HEADING = re.compile(r"^##\s+v(\d+)\.(\d+)\.(\d+)\s+—\s+(\d{4}-\d{2}-\d{2})\s*$")
FILENAME_VERSION = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")
CATEGORY_HEADING = re.compile(r"^###\s+(.+?)\s*$")
ENTRY = re.compile(r"^[-*]\s+(.+?)\s*$")


def parse_file(path):
    """Return one file record: version, date, per-category counts, entries."""
    text = path.read_text(encoding="utf-8")
    version = date = None
    for line in text.splitlines():
        m = VERSION_HEADING.match(line)
        if m:
            version = "%s.%s.%s" % (m.group(1), m.group(2), m.group(3))
            date = m.group(4)
            break
    if version is None:
        m = FILENAME_VERSION.match(path.stem)
        if m:
            version = "%s.%s.%s" % (m.group(1), m.group(2), m.group(3))

    counts = {c: 0 for c in CATEGORIES}
    entries = []
    category = None
    for line in text.splitlines():
        m = CATEGORY_HEADING.match(line)
        if m:
            category = m.group(1)
            continue
        m = ENTRY.match(line)
        if m and category is not None:
            entries.append({"category": category, "text": m.group(1)})
            if category in counts:
                counts[category] += 1
    return {
        "file": path.name,
        "version": version,
        "date": date,
        "counts": counts,
        "entry_count": len(entries),
        "entries": entries,
    }


def version_key(record):
    """Sort ascending by version; files without a version sort last, by name."""
    if record["version"] is None:
        return (1, (0, 0, 0), record["file"])
    return (0, tuple(int(p) for p in record["version"].split(".")), record["file"])


def scan(folder):
    files = sorted(p for p in folder.glob("*.md") if p.is_file())
    records = [parse_file(p) for p in files]
    records.sort(key=version_key)
    totals = {c: sum(r["counts"][c] for r in records) for c in CATEGORIES}
    return {
        "dir": folder.as_posix(),
        "file_count": len(records),
        "categories": CATEGORIES,
        "files": records,
        "totals": totals,
        "entry_total": sum(r["entry_count"] for r in records),
    }


def summary_lines(data):
    lines = ["scan: %d files, %d entries" % (data["file_count"], data["entry_total"])]
    for r in data["files"]:
        counts = " ".join("%s=%d" % (c, r["counts"][c]) for c in CATEGORIES)
        lines.append("  %-14s %-10s %s" % (r["file"], r["date"] or "no-date", counts))
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description="Parse a changelogs folder into one structured scan.")
    ap.add_argument("folder", help="Folder holding the changelog .md files")
    ap.add_argument("--out", help="Write the full scan JSON here")
    ap.add_argument("--json", action="store_true", dest="as_json",
                    help="Print the full scan JSON to stdout")
    args = ap.parse_args(argv)

    folder = Path(args.folder)
    if not folder.is_dir():
        sys.stderr.write("not a folder: %s\n" % folder)
        return 2
    try:
        data = scan(folder)
    except OSError as e:
        sys.stderr.write("cannot read a changelog file: %s\n" % e)
        return 2

    if data["file_count"] == 0:
        sys.stderr.write("no_changelog_files: no .md files in %s\n" % folder)
        print(json.dumps({"code": "no_changelog_files", "dir": folder.as_posix()}, indent=2))
        return 1

    payload = json.dumps(data, indent=2, ensure_ascii=False)
    if args.out:
        try:
            Path(args.out).write_text(payload + "\n", encoding="utf-8")
        except OSError as e:
            sys.stderr.write("cannot write %s: %s\n" % (args.out, e))
            return 2
        print("\n".join(summary_lines(data)))
        print("scan written to %s" % args.out)
    elif args.as_json:
        print(payload)
    else:
        print("\n".join(summary_lines(data)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
