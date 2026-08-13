#!/usr/bin/env python3
"""Scan a changelogs folder and report structure facts as JSON.

Covers the deterministic parts of the changelog-checker workflow: file
inventory and version sort, heading-format check, per-category entry counts,
the rendered summary table, and category-tag validation. Judgment calls
(release narrative, Misc re-categorization, clarity of wording) stay with the
model and are only *fed* by this output.

Usage: python3 scripts/check_changelogs.py <changelogs_dir>
Exit codes: 0 = scan completed, 2 = bad usage or unreadable directory.
"""
import json
import re
import sys
from pathlib import Path

CATEGORIES = ["Added", "Fixed", "Changed", "Removed", "Misc"]
HEADING_RE = re.compile(r"^##\s+v(\d+)\.(\d+)\.(\d+)\s+—\s+(\d{4}-\d{2}-\d{2})\s*$")
SECTION_RE = re.compile(r"^###\s+(.+?)\s*$")
ENTRY_RE = re.compile(r"^[-*]\s+(.*\S)\s*$")


def version_key(name):
    m = re.match(r"^v?(\d+)\.(\d+)\.(\d+)$", Path(name).stem)
    return (0, tuple(int(g) for g in m.groups())) if m else (1, (0, 0, 0))


def scan_file(path):
    rec = {
        "file": path.name,
        "version": Path(path.name).stem.lstrip("v"),
        "date": None,
        "heading_ok": False,
        "heading_line": "",
        "counts": {c: 0 for c in CATEGORIES},
        "unknown_tags": [],
        "misc_entries": [],
    }
    lines = path.read_text(encoding="utf-8").splitlines()
    first = next((ln for ln in lines if ln.strip()), "")
    rec["heading_line"] = first
    m = HEADING_RE.match(first)
    if m:
        rec["heading_ok"] = True
        rec["version"] = ".".join(m.groups()[:3])
        rec["date"] = m.group(4)
    section = None
    for ln in lines:
        s = SECTION_RE.match(ln)
        if s:
            section = s.group(1)
            if section not in CATEGORIES and section not in rec["unknown_tags"]:
                rec["unknown_tags"].append(section)
            continue
        e = ENTRY_RE.match(ln)
        if e and section:
            if section in rec["counts"]:
                rec["counts"][section] += 1
            if section == "Misc":
                rec["misc_entries"].append(e.group(1))
    return rec


def render_table(records):
    head = "| Version | Date | " + " | ".join(CATEGORIES) + " | Total |"
    rule = "|" + "---|" * (len(CATEGORIES) + 3)
    rows = [head, rule]
    for r in sorted(records, key=lambda r: version_key(r["file"]), reverse=True):
        counts = [str(r["counts"][c]) for c in CATEGORIES]
        total = sum(r["counts"].values())
        rows.append(
            "| v%s | %s | %s | %d |"
            % (r["version"], r["date"] or "missing", " | ".join(counts), total)
        )
    return "\n".join(rows)


def main(argv):
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    folder = Path(argv[1])
    if not folder.is_dir():
        print("not a directory: %s" % folder, file=sys.stderr)
        return 2
    files = sorted(folder.glob("*.md"), key=lambda p: version_key(p.name))
    records = [scan_file(p) for p in files]
    totals = {c: sum(r["counts"][c] for r in records) for c in CATEGORIES}
    report = {
        "changelogs_dir": str(folder.resolve()),
        "file_count": len(records),
        "files_sorted": [r["file"] for r in records],
        "files": records,
        "heading_violations": [
            {"file": r["file"], "first_line": r["heading_line"]}
            for r in records
            if not r["heading_ok"]
        ],
        "totals": totals,
        "grand_total": sum(totals.values()),
        "unknown_tags": sorted({t for r in records for t in r["unknown_tags"]}),
        "misc_entries": [
            {"file": r["file"], "entry": e} for r in records for e in r["misc_entries"]
        ],
        "table_markdown": render_table(records),
    }
    json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
