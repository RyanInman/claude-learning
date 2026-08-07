#!/usr/bin/env python3
"""
render_summary_table.py - Render the release summary table from the JSON that
parse_changelogs.py writes.

Columns: Version, Date, Added, Fixed, Changed, Removed, Misc. Rows sorted by
version descending, with a Totals row last.

USAGE
    python3 scripts/render_summary_table.py <parsed.json> [--out FILE]

EXIT CODES
    0  Table rendered to stdout (or to --out).
    1  The parsed JSON holds no files (stdout: no_files).
    2  Usage error, or the JSON is missing/unreadable/not the expected shape.
"""

import argparse
import json
import sys
from pathlib import Path

import _changelog as cl

COLUMNS = cl.KNOWN_CATEGORIES  # Added, Fixed, Changed, Removed, Misc


def render(report):
    files = sorted(report["files"],
                   key=lambda f: cl.version_sort_key(f.get("version")),
                   reverse=True)
    header = "| Version | Date | " + " | ".join(COLUMNS) + " |"
    rule = "|---" * (2 + len(COLUMNS)) + "|"
    rows = [header, rule]
    for f in files:
        counts = f.get("counts", {})
        cells = [str(counts.get(c, 0)) for c in COLUMNS]
        rows.append("| " + (f.get("version") or "?") + " | "
                    + (f.get("date") or "?") + " | " + " | ".join(cells) + " |")
    totals = report.get("totals") or {c: 0 for c in COLUMNS}
    rows.append("| **Total** | | "
                + " | ".join(str(totals.get(c, 0)) for c in COLUMNS) + " |")
    return "\n".join(rows)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    p.add_argument("parsed_json",
                   help="JSON written by parse_changelogs.py --out")
    p.add_argument("--out", help="write the table here instead of stdout")
    args = p.parse_args(argv)

    try:
        report = json.loads(Path(args.parsed_json).read_text(encoding="utf-8"))
    except OSError as e:
        cl.fail(f"cannot read {args.parsed_json}: {e}", 2)
    except ValueError as e:
        cl.fail(f"{args.parsed_json} is not valid JSON: {e}", 2)
    if not isinstance(report, dict) or "files" not in report:
        cl.fail(f"{args.parsed_json} has no 'files' key; run "
                f"parse_changelogs.py --out to produce it", 2)

    if not report["files"]:
        print("no_files")
        print(f"{args.parsed_json} lists no changelog files", file=sys.stderr)
        return 1

    table = render(report)
    if args.out:
        try:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(table + "\n", encoding="utf-8")
        except OSError as e:
            cl.fail(f"cannot write {args.out}: {e}", 2)
        print(f"{len(report['files'])} rows -> {args.out}")
    else:
        print(table)
    return 0


if __name__ == "__main__":
    sys.exit(main())
