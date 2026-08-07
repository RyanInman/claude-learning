#!/usr/bin/env python3
"""
render_table.py - Render the summary table of versions, dates and
per-category entry counts, sorted by version descending.

A file with no parseable version heading still gets a row, with "unknown" in
the version and date cells, and the exit code turns to 1 so the incomplete
row is never mistaken for a complete table.

USAGE
    python3 scripts/render_table.py changelogs/ [--out FILE]

STDOUT
    A markdown table: Version | Date | Added | Fixed | Changed | Removed |
    Misc | Total, one row per file, version descending.

EXIT CODES
    0  Every row carries a version and a date.
    1  At least one row has an unknown version or date.
    2  Usage error, or the directory is missing or unreadable.
"""

import argparse
import sys
from pathlib import Path

import changelog_lib as cl

UNKNOWN = "unknown"


def build_rows(parsed):
    rows = []
    for p in parsed:
        counts = cl.counts_for(p)
        rows.append([p["version"] or UNKNOWN, p["date"] or UNKNOWN]
                    + [str(counts[c]) for c in cl.ALLOWED_CATEGORIES]
                    + [str(sum(counts.values()))])
    rows.sort(key=lambda r: cl.version_key(None if r[0] == UNKNOWN else r[0]),
              reverse=True)
    return rows


def render(rows):
    header = ["Version", "Date"] + cl.ALLOWED_CATEGORIES + ["Total"]
    lines = ["| " + " | ".join(header) + " |",
             "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Render the changelog summary table, version descending.")
    parser.add_argument("directory", help="Folder holding the changelog .md files")
    parser.add_argument("--out", help="Write the table to FILE, summary to stdout")
    args = parser.parse_args(argv)

    try:
        parsed = cl.parse_dir(args.directory)
    except cl.ChangelogError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    rows = build_rows(parsed)
    table = render(rows)

    if args.out:
        try:
            Path(args.out).write_text(table + "\n", encoding="utf-8")
        except OSError as e:
            print(f"error: cannot write {args.out}: {e}", file=sys.stderr)
            return 2
        print(f"{len(rows)} rows -> {args.out}")
    else:
        print(table)

    incomplete = [r[0] for r in rows if UNKNOWN in (r[0], r[1])]
    if incomplete:
        print(f"warning: {len(incomplete)} row(s) missing a version or date",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
