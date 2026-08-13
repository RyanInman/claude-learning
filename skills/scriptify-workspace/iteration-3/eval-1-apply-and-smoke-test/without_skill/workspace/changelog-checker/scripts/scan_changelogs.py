#!/usr/bin/env python3
"""Scan a changelogs folder and report structure facts as JSON or a markdown table.

Facts collected per file: version, date, heading validity, per-category entry
counts, unknown category tags, and the text of every `Misc` entry.
"""

import argparse
import json
import pathlib
import re
import sys

KNOWN = ["Added", "Fixed", "Changed", "Removed"]
ALLOWED = KNOWN + ["Misc"]
HEADING = re.compile(r"^## v(\d+)\.(\d+)\.(\d+) — (\d{4}-\d{2}-\d{2})\s*$")
SECTION = re.compile(r"^### (.+?)\s*$")
ENTRY = re.compile(r"^[-*] +(.*\S)\s*$")


def version_key(name):
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", name)
    return tuple(int(g) for g in m.groups()) if m else (0, 0, 0)


def scan_file(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    rec = {
        "file": path.name,
        "version": None,
        "date": None,
        "heading_ok": False,
        "heading_problem": None,
        "counts": {c: 0 for c in ALLOWED},
        "unknown_tags": [],
        "misc_entries": [],
    }

    first = next((ln for ln in lines if ln.strip()), "")
    m = HEADING.match(first)
    if m:
        rec["heading_ok"] = True
        rec["version"] = "v%s.%s.%s" % m.group(1, 2, 3)
        rec["date"] = m.group(4)
    else:
        rec["heading_problem"] = (
            "first non-empty line is %r; expected '## vX.Y.Z — YYYY-MM-DD'"
            % first
        )
        rec["version"] = "v%d.%d.%d" % version_key(path.name)

    section = None
    for ln in lines:
        s = SECTION.match(ln)
        if s:
            section = s.group(1)
            if section not in ALLOWED and section not in rec["unknown_tags"]:
                rec["unknown_tags"].append(section)
            continue
        e = ENTRY.match(ln)
        if e and section:
            if section in ALLOWED:
                rec["counts"][section] += 1
            if section == "Misc":
                rec["misc_entries"].append(e.group(1))
    return rec


def scan(folder):
    paths = sorted(pathlib.Path(folder).glob("*.md"), key=lambda p: version_key(p.name))
    files = [scan_file(p) for p in paths]
    totals = {c: sum(f["counts"][c] for f in files) for c in ALLOWED}
    return {
        "folder": str(folder),
        "file_count": len(files),
        "files": files,
        "totals": totals,
        "total_entries": sum(totals.values()),
        "bad_headings": [f["file"] for f in files if not f["heading_ok"]],
        "misc_entries": [
            {"file": f["file"], "entry": e} for f in files for e in f["misc_entries"]
        ],
        "unknown_tags": [
            {"file": f["file"], "tag": t} for f in files for t in f["unknown_tags"]
        ],
    }


def render_table(data):
    cols = ["Version", "Date"] + KNOWN + ["Misc", "Total"]
    rows = [
        "| " + " | ".join(cols) + " |",
        "|" + "|".join(["---"] * len(cols)) + "|",
    ]
    for f in sorted(data["files"], key=lambda f: version_key(f["version"]), reverse=True):
        counts = [str(f["counts"][c]) for c in ALLOWED]
        total = str(sum(f["counts"].values()))
        rows.append(
            "| "
            + " | ".join(
                [f["version"], f["date"] or "(missing)"] + counts + [total]
            )
            + " |"
        )
    t = data["totals"]
    rows.append(
        "| **Total** | — | "
        + " | ".join(str(t[c]) for c in ALLOWED)
        + " | **%d** |" % data["total_entries"]
    )
    return "\n".join(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("folder", nargs="?", default="changelogs")
    ap.add_argument("--format", choices=["json", "table"], default="json")
    args = ap.parse_args()

    folder = pathlib.Path(args.folder)
    if not folder.is_dir():
        print("error: not a directory: %s" % folder, file=sys.stderr)
        return 2

    data = scan(folder)
    if args.format == "table":
        print(render_table(data))
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
