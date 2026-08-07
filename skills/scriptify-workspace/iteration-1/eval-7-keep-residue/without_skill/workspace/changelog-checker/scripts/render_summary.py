#!/usr/bin/env python3
"""Render the changelog summary table and problem list from a scan report.

Reads the JSON produced by scan_changelogs.py and prints markdown:
  - a version/date/per-category count table, sorted by version descending
  - a totals row
  - a structural-problems section (bad headings, non-allowed category tags)

Usage:
    scan_changelogs.py changelogs | render_summary.py
    render_summary.py report.json

Exit codes: 0 = rendered, 1 = structural problems found, 2 = bad input.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

COUNTED_CATEGORIES = ["Added", "Fixed", "Changed", "Removed"]


def render_table(report: dict) -> list[str]:
    columns = list(COUNTED_CATEGORIES)
    extra = [
        name
        for name in report.get("totals", {})
        if name not in columns and report["totals"].get(name)
    ]
    columns += sorted(extra)

    header = ["Version", "Date"] + columns + ["Total"]
    lines = [
        "| " + " | ".join(header) + " |",
        "|" + "|".join(["---"] * len(header)) + "|",
    ]

    for record in reversed(report.get("files", [])):
        version = record.get("version") or "?"
        label = f"v{version}" if version != "?" else record["filename"]
        if not record.get("heading_ok"):
            label += " *"
        date = record.get("date") or "—"
        counts = record.get("categories", {})
        row = [label, date]
        row += [str(counts.get(name, 0)) for name in columns]
        row.append(str(sum(counts.get(name, 0) for name in columns)))
        lines.append("| " + " | ".join(row) + " |")

    totals = report.get("totals", {})
    total_row = ["**Total**", f"{report.get('file_count', 0)} files"]
    total_row += [f"**{totals.get(name, 0)}**" for name in columns]
    total_row.append(f"**{sum(totals.get(name, 0) for name in columns)}**")
    lines.append("| " + " | ".join(total_row) + " |")
    return lines


def render_problems(report: dict) -> tuple[list[str], int]:
    problems = report.get("problems", {})
    lines: list[str] = []
    count = 0

    bad = problems.get("bad_heading", [])
    lines.append(f"### Heading check ({len(bad)} problem(s))")
    if bad:
        count += len(bad)
        for item in bad:
            lines.append(f"- `{item['filename']}`: {item['problem']}")
    else:
        lines.append("- All files start with a valid `## vX.Y.Z — YYYY-MM-DD` heading.")
    lines.append("")

    unknown = problems.get("unknown_categories", [])
    lines.append(f"### Category tags outside the allowed list ({len(unknown)} file(s))")
    if unknown:
        count += len(unknown)
        for item in unknown:
            tags = ", ".join(f"`{t}`" for t in item["categories"])
            lines.append(f"- `{item['filename']}`: {tags}")
    else:
        allowed = ", ".join(f"`{c}`" for c in report.get("allowed_categories", []))
        lines.append(f"- Every tag is one of {allowed}.")
    lines.append("")

    untagged = problems.get("untagged_entries", [])
    if untagged:
        count += len(untagged)
        lines.append(f"### Entries outside any category ({len(untagged)})")
        for item in untagged:
            lines.append(f"- `{item['filename']}`: {item['text']}")
        lines.append("")

    misc = problems.get("misc_entries", [])
    lines.append(f"### `Misc` entries needing a judgement call ({len(misc)})")
    if misc:
        for item in misc:
            lines.append(f"- `{item['filename']}`: {item['text']}")
    else:
        lines.append("- None.")
    lines.append("")
    return lines, count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("report", nargs="?", help="scan JSON (default: stdin)")
    args = parser.parse_args(argv)

    try:
        raw = Path(args.report).read_text(encoding="utf-8") if args.report else sys.stdin.read()
        report = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: could not read scan report: {exc}", file=sys.stderr)
        return 2

    if not isinstance(report, dict) or "files" not in report:
        print("error: input is not a scan_changelogs.py report", file=sys.stderr)
        return 2

    out = [
        f"## Changelog summary ({report.get('file_count', 0)} files, "
        f"{report.get('entry_total', 0)} entries)",
        "",
    ]
    out += render_table(report)
    out.append("")
    out.append("`*` = heading does not match the required format.")
    out.append("")
    problem_lines, problem_count = render_problems(report)
    out += problem_lines

    print("\n".join(out).rstrip())
    return 1 if problem_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
