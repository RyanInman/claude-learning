#!/usr/bin/env python3
"""
render_summary.py - Render the release summary table from a scan JSON.

Reads the scan written by scan_changelogs.py and prints one markdown table of
versions, dates, and per-category entry counts, sorted by version descending,
with an all-versions total row.

USAGE
    python3 scripts/render_summary.py scan.json

STDOUT
    The markdown summary table.

EXIT CODES
    0  Table rendered.
    1  invalid_scan: the JSON parses but is not a scan (no `files` list).
    2  Usage error, missing file, or unparseable JSON.
"""

import argparse
import json
import sys
from pathlib import Path

NO_DATE = "—"


def version_key(record):
    """Sort by version; files without a version sort last, by name."""
    version = record.get("version")
    if not version:
        return (1, (0, 0, 0), record.get("file", ""))
    try:
        return (0, tuple(int(p) for p in str(version).split(".")), record.get("file", ""))
    except ValueError:
        return (1, (0, 0, 0), record.get("file", ""))


def render(scan):
    categories = scan.get("categories") or ["Added", "Fixed", "Changed", "Removed", "Misc"]
    files = sorted(scan["files"], key=version_key, reverse=True)
    lines = ["| Version | Date | " + " | ".join(categories) + " | Total |",
             "|" + "---|" * (len(categories) + 3)]
    for r in files:
        counts = r.get("counts", {})
        cells = [str(counts.get(c, 0)) for c in categories]
        total = r.get("entry_count", sum(counts.get(c, 0) for c in categories))
        lines.append("| %s | %s | %s | %s |" % (r.get("version") or NO_DATE,
                                                r.get("date") or NO_DATE,
                                                " | ".join(cells), total))
    totals = scan.get("totals", {})
    total_cells = [str(totals.get(c, 0)) for c in categories]
    lines.append("| **All** | %s | %s | %s |" % (NO_DATE, " | ".join(total_cells),
                                                 scan.get("entry_total", 0)))
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render the release summary table from a scan JSON.")
    ap.add_argument("scan", help="scan.json written by scan_changelogs.py --out")
    args = ap.parse_args(argv)

    path = Path(args.scan)
    try:
        scan = json.loads(path.read_text(encoding="utf-8"))
    except OSError as e:
        sys.stderr.write("cannot read %s: %s\n" % (path, e))
        return 2
    except ValueError as e:
        sys.stderr.write("%s is not valid JSON: %s\n" % (path, e))
        return 2

    if not isinstance(scan, dict) or not isinstance(scan.get("files"), list):
        sys.stderr.write("invalid_scan: %s has no `files` list; run scan_changelogs.py --out first\n" % path)
        print("invalid_scan")
        return 1

    print("\n".join(render(scan)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
