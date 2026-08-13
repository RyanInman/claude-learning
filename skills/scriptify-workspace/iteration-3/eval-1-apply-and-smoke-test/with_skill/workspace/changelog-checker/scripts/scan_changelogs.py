#!/usr/bin/env python3
"""
scan_changelogs.py - Inventory and validate a changelogs folder in one pass.

Covers the mechanical half of the changelog-checker workflow: it lists the
`.md` files sorted by version, validates each file's `## vX.Y.Z — YYYY-MM-DD`
header, counts entries per category, totals them across files,
and flags every category tag outside the allowed list. It never judges: the
`Misc` entries it collects are handed back for a human or Claude to re-file.

USAGE
    python3 scripts/scan_changelogs.py <changelogs-dir> [--out FILE]

    <changelogs-dir>  folder holding the changelog `.md` files (non-recursive)
    --out FILE        write the full scan JSON here; stdout keeps the summary

STDOUT
    One summary line - "scan: N files, N entries, N findings, N misc" - then
    one indented line per finding and one per Misc entry.

FINDING CODES
    header_not_first        first non-empty line is not a `## v...` heading
    header_malformed        first line is a `## v...` heading that does not
                            match `## vX.Y.Z — YYYY-MM-DD` (em dash, ISO date)
    unknown_tag             a `###` category outside the allowed list
    entry_outside_category  a bullet sits above every `###` category heading

EXIT CODES
    0  No findings. Misc entries alone do not raise the exit code, because
       re-filing a Misc entry is a judgment call, not a structural defect.
    1  At least one finding.
    2  Usage error, or the directory is missing, unreadable, or holds no .md.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ALLOWED = ["Added", "Fixed", "Changed", "Removed", "Misc"]
HEADER_RE = re.compile(r"^##\s+v(\d+)\.(\d+)\.(\d+)\s+—\s+(\d{4}-\d{2}-\d{2})\s*$")
HEADER_START_RE = re.compile(r"^##\s+v", re.IGNORECASE)
CATEGORY_RE = re.compile(r"^###\s+(.+?)\s*$")
ENTRY_RE = re.compile(r"^-\s+(\S.*?)\s*$")
FILENAME_VERSION_RE = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")


def version_key(version):
    """Sortable tuple for a dotted version string; unparseable sorts last."""
    if not version:
        return (10**6, 0, 0)
    m = FILENAME_VERSION_RE.search(version)
    if not m:
        return (10**6, 0, 0)
    return tuple(int(g) for g in m.groups())


def scan_file(path):
    """Parse one changelog file into a record plus its findings."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    findings = []

    version = None
    date = None
    first = next((ln for ln in lines if ln.strip()), "")
    m = HEADER_RE.match(first)
    if m:
        version = f"{m.group(1)}.{m.group(2)}.{m.group(3)}"
        date = m.group(4)
    elif HEADER_START_RE.match(first):
        findings.append({"code": "header_malformed", "file": path.name,
                         "detail": f'first line is "{first.strip()}", not "## vX.Y.Z — YYYY-MM-DD"'})
    else:
        findings.append({"code": "header_not_first", "file": path.name,
                         "detail": f'first non-empty line is "{first.strip()}", not a "## v" heading'})
    if version is None:
        fm = FILENAME_VERSION_RE.search(path.name)
        if fm:
            version = ".".join(fm.groups())

    counts = {c: 0 for c in ALLOWED}
    misc_entries = []
    category = None
    reported_orphan = False
    for line in lines:
        cm = CATEGORY_RE.match(line)
        if cm:
            category = cm.group(1)
            if category not in ALLOWED:
                findings.append({"code": "unknown_tag", "file": path.name,
                                 "detail": f'category "{category}" is not one of {", ".join(ALLOWED)}'})
            continue
        em = ENTRY_RE.match(line)
        if not em:
            continue
        if category is None:
            if not reported_orphan:
                findings.append({"code": "entry_outside_category", "file": path.name,
                                 "detail": f'entry "{em.group(1)}" sits above every "###" category heading'})
                reported_orphan = True
            continue
        if category in counts:
            counts[category] += 1
        if category == "Misc":
            misc_entries.append({"file": path.name, "text": em.group(1)})

    record = {"file": path.name, "version": version, "date": date,
              "entries": sum(counts.values()), "counts": counts}
    return record, findings, misc_entries


def scan_dir(directory):
    files = sorted(p for p in directory.glob("*.md") if p.is_file())
    records, findings, misc = [], [], []
    for path in files:
        record, file_findings, file_misc = scan_file(path)
        records.append(record)
        findings.extend(file_findings)
        misc.extend(file_misc)
    records.sort(key=lambda r: (version_key(r["version"]), r["file"]))
    totals = {c: sum(r["counts"][c] for r in records) for c in ALLOWED}
    return {"dir": directory.as_posix(),
            "file_count": len(records),
            "total_entries": sum(totals.values()),
            "totals": totals,
            "files": records,
            "misc_entries": misc,
            "findings": findings}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Inventory and validate a changelogs folder.")
    parser.add_argument("directory", help="folder holding the changelog .md files")
    parser.add_argument("--out", help="write the full scan JSON to this file")
    args = parser.parse_args(argv)

    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"not a directory: {directory}", file=sys.stderr)
        return 2
    try:
        scan = scan_dir(directory)
    except OSError as e:
        print(f"cannot read {directory}: {e}", file=sys.stderr)
        return 2
    if scan["file_count"] == 0:
        print(f"no .md files under {directory}", file=sys.stderr)
        return 2

    if args.out:
        try:
            Path(args.out).write_text(json.dumps(scan, indent=2) + "\n", encoding="utf-8")
        except OSError as e:
            print(f"cannot write {args.out}: {e}", file=sys.stderr)
            return 2

    print(f'scan: {scan["file_count"]} files, {scan["total_entries"]} entries, '
          f'{len(scan["findings"])} findings, {len(scan["misc_entries"])} misc '
          f'({scan["dir"]})')
    for f in scan["findings"]:
        print(f'  {f["code"]} {f["file"]}: {f["detail"]}')
    for m in scan["misc_entries"]:
        print(f'  misc {m["file"]}: {m["text"]}')
    return 1 if scan["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())
