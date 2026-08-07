#!/usr/bin/env python3
"""Scan a changelogs folder and emit one JSON report.

Covers the mechanical parts of the changelog-checker workflow:
  - enumerate + version-sort every .md file, with a total count
  - validate each file's `## vX.Y.Z - YYYY-MM-DD` heading (em dash)
  - count entries per category, per file and in total
  - flag category tags outside the allowed list
  - collect the `Misc` entries (and their text) for judgement elsewhere

Usage:
    scan_changelogs.py [CHANGELOGS_DIR] [-o OUT.json]

CHANGELOGS_DIR defaults to ./changelogs. JSON goes to stdout unless -o is given.
Exit codes: 0 = scan completed, 2 = directory missing or contains no .md files.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ALLOWED_CATEGORIES = ["Added", "Fixed", "Changed", "Removed", "Misc"]
COUNTED_CATEGORIES = ["Added", "Fixed", "Changed", "Removed"]

HEADING_RE = re.compile(r"^##\s+v(\d+)\.(\d+)\.(\d+)\s+—\s+(\d{4}-\d{2}-\d{2})\s*$")
LOOSE_HEADING_RE = re.compile(r"^##\s+(?P<rest>\S.*)$")
CATEGORY_RE = re.compile(r"^###\s+(?P<name>.+?)\s*$")
ENTRY_RE = re.compile(r"^[-*]\s+(?P<text>.*\S)\s*$")
FILENAME_VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")

UNSORTABLE = (10**9, 10**9, 10**9)


def parse_file(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()

    heading_line = None
    for line in lines:
        if line.strip():
            heading_line = line.rstrip()
            break

    version = None
    date = None
    heading_ok = False
    heading_problem = None

    if heading_line is None:
        heading_problem = "file is empty"
    else:
        match = HEADING_RE.match(heading_line)
        if match:
            heading_ok = True
            version = f"{match.group(1)}.{match.group(2)}.{match.group(3)}"
            date = match.group(4)
        elif LOOSE_HEADING_RE.match(heading_line):
            heading_problem = (
                f"first heading {heading_line!r} does not match "
                "'## vX.Y.Z — YYYY-MM-DD'"
            )
        else:
            heading_problem = (
                f"first content line {heading_line!r} is not a '## ' version heading"
            )

    version_source = "heading" if version else None
    if version is None:
        fname_match = FILENAME_VERSION_RE.match(path.stem)
        if fname_match:
            version = ".".join(fname_match.groups())
            version_source = "filename"

    entries: dict[str, list[str]] = {}
    category_order: list[str] = []
    untagged: list[str] = []
    current = None
    # Scan every line: a `## ` version heading can never match CATEGORY_RE, so a
    # file whose first content line is `### Added` still keeps that section.
    for line in lines:
        cat_match = CATEGORY_RE.match(line)
        if cat_match:
            current = cat_match.group("name")
            if current not in entries:
                entries[current] = []
                category_order.append(current)
            continue
        entry_match = ENTRY_RE.match(line)
        if entry_match:
            if current is None:
                untagged.append(entry_match.group("text"))
            else:
                entries[current].append(entry_match.group("text"))

    counts = {name: len(items) for name, items in entries.items()}
    unknown = [name for name in category_order if name not in ALLOWED_CATEGORIES]
    misc = [{"category": "Misc", "text": text} for text in entries.get("Misc", [])]

    return {
        "filename": path.name,
        "path": str(path),
        "version": version,
        "version_source": version_source,
        "date": date,
        "heading_ok": heading_ok,
        "heading_line": heading_line,
        "heading_problem": heading_problem,
        "categories": counts,
        "counted_entry_total": sum(
            counts.get(name, 0) for name in COUNTED_CATEGORIES
        ),
        "entry_total": sum(counts.values()),
        "unknown_categories": unknown,
        "misc_entries": misc,
        "untagged_entries": untagged,
        "entries": entries,
    }


def version_key(record: dict) -> tuple:
    if not record["version"]:
        return UNSORTABLE
    return tuple(int(part) for part in record["version"].split("."))


def scan(directory: Path) -> dict:
    files = sorted(p for p in directory.glob("*.md") if p.is_file())
    records = [parse_file(p) for p in files]
    records.sort(key=lambda r: (version_key(r), r["filename"]))

    totals = {name: 0 for name in ALLOWED_CATEGORIES}
    for record in records:
        for name, count in record["categories"].items():
            totals[name] = totals.get(name, 0) + count

    return {
        "changelogs_dir": str(directory),
        "file_count": len(records),
        "allowed_categories": ALLOWED_CATEGORIES,
        "files": records,
        "totals": totals,
        "counted_entry_total": sum(totals.get(n, 0) for n in COUNTED_CATEGORIES),
        "entry_total": sum(totals.values()),
        "problems": {
            "bad_heading": [
                {"filename": r["filename"], "problem": r["heading_problem"]}
                for r in records
                if not r["heading_ok"]
            ],
            "unknown_categories": [
                {"filename": r["filename"], "categories": r["unknown_categories"]}
                for r in records
                if r["unknown_categories"]
            ],
            "misc_entries": [
                {"filename": r["filename"], "text": m["text"]}
                for r in records
                for m in r["misc_entries"]
            ],
            "untagged_entries": [
                {"filename": r["filename"], "text": t}
                for r in records
                for t in r["untagged_entries"]
            ],
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("directory", nargs="?", default="changelogs")
    parser.add_argument("-o", "--out", help="write JSON here instead of stdout")
    args = parser.parse_args(argv)

    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"error: no such directory: {directory}", file=sys.stderr)
        return 2

    report = scan(directory)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)

    if report["file_count"] == 0:
        print(f"error: no .md files in {directory}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
