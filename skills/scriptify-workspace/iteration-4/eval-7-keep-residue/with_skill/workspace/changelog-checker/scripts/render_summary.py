#!/usr/bin/env python3
"""
render_summary.py - Render the markdown summary table of versions, dates, and
per-category entry counts, sorted by version descending.

A file with no well-formed version heading still gets a row: its version comes
from the filename and its date renders as `-`, because dropping the row would
hide the very file check_headings.py just flagged. The last column counts every
entry in the file, so it exceeds the four category columns when a file carries a
Misc entry.

USAGE
    python3 scripts/render_summary.py <changelogs-dir>

EXIT CODES
    0  Table rendered to stdout.
    2  Usage error, or the folder is missing or unreadable.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_changelogs import CATEGORIES, scan, version_key  # noqa: E402


def render(data):
    rows = sorted(data["files"], key=lambda f: version_key(Path(f["file"])), reverse=True)
    header = "| Version | Date | " + " | ".join(CATEGORIES) + " | All entries |"
    rule = "|" + "---|" * (len(CATEGORIES) + 3)
    lines = [header, rule]
    for f in rows:
        counts = " | ".join(str(f["counts"][c]) for c in CATEGORIES)
        lines.append(f'| v{f["version"] or "?"} | {f["date"] or "-"} | {counts} | {f["entry_count"]} |')
    totals = " | ".join(str(data["totals"][c]) for c in CATEGORIES)
    lines.append(f'| **All {data["file_count"]}** | | {totals} | {data["total_entries"]} |')
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render the version summary table, sorted by version descending.")
    ap.add_argument("directory", help="Folder holding the changelog .md files")
    args = ap.parse_args(argv)

    d = Path(args.directory)
    if not d.is_dir():
        print(f"render_summary: not a directory: {args.directory}", file=sys.stderr)
        return 2
    try:
        data = scan(d)
    except OSError as e:
        print(f"render_summary: cannot read {args.directory}: {e}", file=sys.stderr)
        return 2

    print(render(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
