#!/usr/bin/env python3
"""
render_summary.py - Render the release summary table from a scan JSON.

Reads the JSON that `scan_changelogs.py --out` writes and prints one markdown
table: one row per changelog file sorted by version descending, then a totals
row. Rendering lives here so the table is never hand-typed, because a
hand-typed table drifts from the counts it claims to report.

USAGE
    python3 scripts/render_summary.py <scan.json>

STDOUT
    A markdown table: Version | Date | Added | Fixed | Changed | Removed |
    Misc | Total. A file with no valid version header shows its date as
    "unknown".

EXIT CODES
    0  Table rendered.
    2  Usage error, or the scan file is missing, unparseable, or lacks the
       `files` and `totals` keys this renderer needs.
"""

import argparse
import json
import re
import sys
from pathlib import Path

CATEGORIES = ["Added", "Fixed", "Changed", "Removed", "Misc"]
VERSION_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")


def version_key(version):
    """Sortable tuple for a dotted version string; unparseable sorts last."""
    m = VERSION_RE.search(version or "")
    if not m:
        return (-1, 0, 0)
    return tuple(int(g) for g in m.groups())


def render(scan):
    rows = sorted(scan["files"], key=lambda r: version_key(r.get("version")), reverse=True)
    out = ["| Version | Date | " + " | ".join(CATEGORIES) + " | Total |",
           "|---|---|" + "---|" * (len(CATEGORIES) + 1)]
    for r in rows:
        counts = r.get("counts", {})
        cells = [str(counts.get(c, 0)) for c in CATEGORIES]
        version = f'v{r.get("version")}' if r.get("version") else r.get("file", "?")
        out.append(f'| {version} | {r.get("date") or "unknown"} | '
                   + " | ".join(cells)
                   + f' | {r.get("entries", sum(int(c) for c in cells))} |')
    totals = scan["totals"]
    total_cells = [str(totals.get(c, 0)) for c in CATEGORIES]
    out.append("| **Total** | unknown | " + " | ".join(total_cells)
               + f' | {scan.get("total_entries", sum(int(c) for c in total_cells))} |')
    return "\n".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Render the release summary table from a scan JSON.")
    parser.add_argument("scan", help="scan JSON written by scan_changelogs.py --out")
    args = parser.parse_args(argv)

    try:
        scan = json.loads(Path(args.scan).read_text(encoding="utf-8"))
    except OSError as e:
        print(f"cannot read {args.scan}: {e}", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"{args.scan} is not valid JSON: {e}", file=sys.stderr)
        return 2
    for key in ("files", "totals"):
        if key not in scan:
            print(f"{args.scan} has no \"{key}\" key; is it a scan_changelogs.py --out file?",
                  file=sys.stderr)
            return 2

    print(render(scan))
    return 0


if __name__ == "__main__":
    sys.exit(main())
