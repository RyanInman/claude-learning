#!/usr/bin/env python3
"""
scan_changelogs.py - Inventory a changelogs folder and tally entries per category.

Lists every .md file sorted by semantic version, records each file's version,
date, and per-category entry counts, and totals the counts across files. This
module is also the shared parser: check_headings.py, check_tags.py, and
render_summary.py import parse_file() and sorted_files() from it.

USAGE
    python3 scripts/scan_changelogs.py <changelogs-dir>
    python3 scripts/scan_changelogs.py <changelogs-dir> --out scan.json

    Without --out the full scan JSON goes to stdout. With --out the JSON goes
    to the file and stdout carries a compact one-line-per-file summary, because
    a large changelogs folder would otherwise spend the tokens the script saves.

EXIT CODES
    0  Scan completed.
    2  Usage error, or the folder is missing or unreadable.
"""

import argparse
import json
import re
import sys
from pathlib import Path

CATEGORIES = ["Added", "Fixed", "Changed", "Removed"]
HEADING_RE = re.compile(r"^##\s+v(\d+)\.(\d+)\.(\d+)\s+[-–—]\s+(\d{4}-\d{2}-\d{2})\s*$")
H2_RE = re.compile(r"^##\s+(?!#)(.*)$")
CATEGORY_RE = re.compile(r"^###\s+(.+?)\s*$")
ENTRY_RE = re.compile(r"^[-*]\s+\S")
FILENAME_VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


def version_key(path):
    """Sort key from the filename version; unparseable names sort last by name."""
    m = FILENAME_VERSION_RE.match(path.stem)
    if m:
        return (0, tuple(int(g) for g in m.groups()), path.name)
    return (1, (0, 0, 0), path.name)


def sorted_files(directory):
    """Every .md file in `directory`, ascending by semantic version."""
    return sorted(Path(directory).glob("*.md"), key=version_key)


def parse_file(path):
    """Parse one changelog file into version, date, heading state, and entries."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    first = next((ln for ln in lines if ln.strip()), "")
    heading = HEADING_RE.match(first)
    file_version = None
    m = FILENAME_VERSION_RE.match(path.stem)
    if m:
        file_version = ".".join(m.groups())
    entries = []
    category = None
    for line in lines:
        cat = CATEGORY_RE.match(line)
        if cat:
            category = cat.group(1)
            continue
        if ENTRY_RE.match(line.strip()) and line.startswith(("-", "*")):
            entries.append({"category": category, "text": line.lstrip("-* ").strip()})
    counts = {c: sum(1 for e in entries if e["category"] == c) for c in CATEGORIES}
    return {
        "file": path.name,
        "version": heading.group(1) + "." + heading.group(2) + "." + heading.group(3) if heading else file_version,
        "file_version": file_version,
        "date": heading.group(4) if heading else None,
        "first_line": first,
        "first_line_is_h2": bool(H2_RE.match(first)),
        "heading_ok": bool(heading),
        "counts": counts,
        "entry_count": len(entries),
        "entries": entries,
    }


def scan(directory):
    files = [parse_file(p) for p in sorted_files(directory)]
    totals = {c: sum(f["counts"][c] for f in files) for c in CATEGORIES}
    return {
        "dir": Path(directory).as_posix(),
        "file_count": len(files),
        "categories": CATEGORIES,
        "totals": totals,
        "total_entries": sum(f["entry_count"] for f in files),
        "files": [{k: v for k, v in f.items() if k != "entries"} for f in files],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Inventory a changelogs folder and tally entries per category.")
    ap.add_argument("directory", help="Folder holding the changelog .md files")
    ap.add_argument("--out", help="Write the full scan JSON here and keep stdout compact")
    args = ap.parse_args(argv)

    d = Path(args.directory)
    if not d.is_dir():
        print(f"scan_changelogs: not a directory: {args.directory}", file=sys.stderr)
        return 2
    try:
        data = scan(d)
    except OSError as e:
        print(f"scan_changelogs: cannot read {args.directory}: {e}", file=sys.stderr)
        return 2

    if args.out:
        try:
            Path(args.out).write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError as e:
            print(f"scan_changelogs: cannot write {args.out}: {e}", file=sys.stderr)
            return 2
        print(f'{data["file_count"]} files, {data["total_entries"]} entries -> {args.out}')
        for f in data["files"]:
            print(f'  {f["file"]:<16} v{f["version"] or "?"} {f["date"] or "no-date"} entries={f["entry_count"]}')
    else:
        print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
