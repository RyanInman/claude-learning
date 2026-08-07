#!/usr/bin/env python3
"""
render_summary.py - Render the release summary table: one row per changelog
with its version, date, and per-category entry counts, sorted by version
descending, plus a totals row.

USAGE
    python3 scripts/render_summary.py <changelogs-dir> [--out FILE]

    --out F  write the table to F, keep a one-line summary on stdout

STDOUT
    A markdown table:
    | Version | Date | Added | Fixed | Changed | Removed |

EXIT CODES
    0  Table rendered.
    1  No .md files in the directory; nothing to render.
    2  Usage error, or the directory is missing or unreadable.
"""

import argparse
import sys

import _changelog

MISSING = "unknown"
COLUMNS = ("Version", "Date") + _changelog.COUNTED_CATEGORIES


def render(directory):
    parsed = _changelog.load_dir(directory)
    parsed.sort(key=lambda p: _changelog.version_key(p["version"]), reverse=True)
    if not parsed:
        return ""

    lines = [
        "| " + " | ".join(COLUMNS) + " |",
        "|" + "|".join("---" for _ in COLUMNS) + "|",
    ]
    totals = {c: 0 for c in _changelog.COUNTED_CATEGORIES}
    for p in parsed:
        version = f"v{p['version']}" if p["version"] else p["file"]
        cells = [version, p["date"] or MISSING]
        for cat in _changelog.COUNTED_CATEGORIES:
            totals[cat] += p["counts"][cat]
            cells.append(str(p["counts"][cat]))
        lines.append("| " + " | ".join(cells) + " |")

    total_cells = ["**Total**", ""] + [str(totals[c])
                                       for c in _changelog.COUNTED_CATEGORIES]
    lines.append("| " + " | ".join(total_cells) + " |")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Render the changelog summary table, version descending.")
    parser.add_argument("directory", help="Folder holding the .md changelogs")
    parser.add_argument("--out", help="Write the table to this file")
    args = parser.parse_args(argv)

    try:
        table = render(args.directory)
    except (OSError, ValueError) as e:
        return _changelog.die_unreadable(e)

    if not table:
        print(f"error: no .md changelog files in {args.directory}",
              file=sys.stderr)
        return 1

    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(table + "\n")
        except OSError as e:
            return _changelog.die_unreadable(e)
        print(f"wrote summary table to {args.out}")
    else:
        print(table)
    return 0


if __name__ == "__main__":
    sys.exit(main())
