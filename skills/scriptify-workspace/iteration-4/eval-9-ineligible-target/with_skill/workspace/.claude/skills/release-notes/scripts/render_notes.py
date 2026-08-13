#!/usr/bin/env python3
"""
render_notes.py - Render the milestone notes from scan_notes.py's JSON.

Groups the scanned entries by type in the fixed order feat, fix, chore, sorts
each group by PR number ascending, and writes the markdown list. It refuses to
render a scan that still carries findings, because a malformed note has no PR
number to sort on and publishing it would ship the defect into the changelog.

FINDING CODES
    scan_has_findings  the input scan JSON lists at least one finding

USAGE
    python3 scripts/render_notes.py <scan.json> [--out FILE]

    Without --out the markdown goes to stdout. With --out it goes to the file
    and stdout carries the per-group order, so a caller can confirm the sort
    without opening the file.

EXIT CODES
    0  Markdown rendered.
    1  The scan carries findings; nothing rendered.
    2  Usage error, or the scan JSON is missing, unreadable, or malformed.
"""

import argparse
import json
import sys
from pathlib import Path

TYPE_ORDER = ("feat", "fix", "chore")
TYPE_HEADINGS = {"feat": "Features", "fix": "Fixes", "chore": "Chores"}


def group(entries):
    """Return {type: [entry, ...]} with each group sorted by PR ascending."""
    grouped = {t: [] for t in TYPE_ORDER}
    for entry in entries:
        if entry.get("type") in grouped:
            grouped[entry["type"]].append(entry)
    for bucket in grouped.values():
        bucket.sort(key=lambda e: e["pr"])
    return grouped


def render(grouped):
    lines = ["# Release Notes", ""]
    for kind in TYPE_ORDER:
        bucket = grouped[kind]
        if not bucket:
            continue
        lines += [f"## {TYPE_HEADINGS[kind]}", ""]
        lines += [f"- #{e['pr']} {e['title']}" for e in bucket]
        lines.append("")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render milestone release notes.")
    ap.add_argument("scan_json", help="JSON written by scan_notes.py --out")
    ap.add_argument("--out", help="Write the markdown here; summarize on stdout")
    args = ap.parse_args(argv)

    try:
        scan = json.loads(Path(args.scan_json).read_text(encoding="utf-8"))
    except OSError as e:
        print(f"render_notes: cannot read {args.scan_json}: {e}",
              file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"render_notes: {args.scan_json} is not valid JSON: {e}",
              file=sys.stderr)
        return 2

    entries = scan.get("entries")
    if not isinstance(entries, list):
        print(f"render_notes: {args.scan_json} has no `entries` list; it is not "
              "scan_notes.py output", file=sys.stderr)
        return 2

    findings = scan.get("findings") or []
    if findings:
        print(f"scan_has_findings: {len(findings)}")
        for f in findings:
            print(f"  {f.get('code')}  {f.get('file')}")
        print("nothing rendered; fix the notes and re-run scan_notes.py")
        return 1

    grouped = group(entries)
    markdown = render(grouped)

    if args.out:
        out_path = Path(args.out)
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(markdown, encoding="utf-8")
        except OSError as e:
            print(f"render_notes: cannot write {out_path}: {e}",
                  file=sys.stderr)
            return 2
        order = " ".join(f"{t}{[e['pr'] for e in grouped[t]]}"
                         for t in TYPE_ORDER)
        print(f"wrote {out_path.as_posix()}")
        print(f"order: {order}")
    else:
        print(markdown)

    return 0


if __name__ == "__main__":
    sys.exit(main())
