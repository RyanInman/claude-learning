#!/usr/bin/env python3
"""Scan a changelogs folder and report structure, counts, and a summary table as JSON.

Usage: check_changelogs.py <changelogs-dir>

Prints one JSON object to stdout. Exit 0 on a successful scan (even when the scan
finds problems), 2 when the directory is missing or empty, because a findings-based
exit code would be indistinguishable from a crashed run.
"""

import json
import re
import sys
from pathlib import Path

HEADING_RE = re.compile(r"^## v(\d+)\.(\d+)\.(\d+) — (\d{4}-\d{2}-\d{2})\s*$")
CATEGORY_RE = re.compile(r"^###\s+(.+?)\s*$")
ENTRY_RE = re.compile(r"^[-*]\s+(.+?)\s*$")
FILENAME_VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)\.md$")

KNOWN = ["Added", "Fixed", "Changed", "Removed"]
ALLOWED = KNOWN + ["Misc"]


def parse_file(path):
    lines = path.read_text(encoding="utf-8").splitlines()

    first = next((line for line in lines if line.strip()), "")
    heading = HEADING_RE.match(first)
    version = None
    date = None
    heading_problem = None
    if heading:
        version = "v{}.{}.{}".format(*heading.groups()[:3])
        date = heading.group(4)
    else:
        heading_problem = (
            "first line is {!r}, expected a heading of the form "
            "'## vX.Y.Z — YYYY-MM-DD'".format(first)
        )
        name_match = FILENAME_VERSION_RE.match(path.name)
        if name_match:
            version = "v{}.{}.{}".format(*name_match.groups())

    counts = {}
    misc_entries = []
    unknown_categories = []
    current = None
    for line in lines:
        category = CATEGORY_RE.match(line)
        if category:
            current = category.group(1)
            counts.setdefault(current, 0)
            if current not in ALLOWED and current not in unknown_categories:
                unknown_categories.append(current)
            continue
        entry = ENTRY_RE.match(line)
        if entry and current is not None:
            counts[current] += 1
            if current == "Misc":
                misc_entries.append(entry.group(1))

    return {
        "file": path.name,
        "version": version,
        "date": date,
        "heading_ok": heading is not None,
        "heading_problem": heading_problem,
        "counts": counts,
        "unknown_categories": unknown_categories,
        "misc_entries": misc_entries,
    }


def sort_key(record):
    version = record["version"]
    if not version:
        return (0, 0, 0, 0, record["file"])
    parts = [int(p) for p in version.lstrip("v").split(".")]
    return (1, parts[0], parts[1], parts[2], record["file"])


def render_table(records):
    # The Other column appears only when some file uses a category outside the
    # allowed list, so the row cells always add up to the Total column.
    has_other = any(r["unknown_categories"] for r in records)
    columns = ALLOWED + ["Other"] if has_other else ALLOWED
    header = "| Version | Date | " + " | ".join(columns) + " | Total |"
    divider = "|---" * (len(columns) + 3) + "|"
    rows = [header, divider]
    for record in records:
        cells = [str(record["counts"].get(c, 0)) for c in ALLOWED]
        if has_other:
            other = sum(
                n for c, n in record["counts"].items() if c not in ALLOWED
            )
            cells.append(str(other))
        total = sum(record["counts"].values())
        rows.append(
            "| {} | {} | {} | {} |".format(
                record["version"] or "(unknown)",
                record["date"] or "(missing)",
                " | ".join(cells),
                total,
            )
        )
    return "\n".join(rows)


def main(argv):
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    directory = Path(argv[1])
    if not directory.is_dir():
        print("not a directory: {}".format(directory), file=sys.stderr)
        return 2

    paths = sorted(directory.glob("*.md"))
    if not paths:
        print("no .md files in {}".format(directory), file=sys.stderr)
        return 2

    records = [parse_file(p) for p in paths]
    records.sort(key=sort_key, reverse=True)

    totals = {}
    for record in records:
        for category, count in record["counts"].items():
            totals[category] = totals.get(category, 0) + count

    result = {
        "file_count": len(records),
        "files": records,
        "totals": totals,
        "total_entries": sum(totals.values()),
        "heading_problems": [
            {"file": r["file"], "problem": r["heading_problem"]}
            for r in records
            if not r["heading_ok"]
        ],
        "unknown_category_uses": [
            {"file": r["file"], "category": c}
            for r in records
            for c in r["unknown_categories"]
        ],
        "misc_entries": [
            {"file": r["file"], "entry": e} for r in records for e in r["misc_entries"]
        ],
        "table": render_table(records),
    }
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
