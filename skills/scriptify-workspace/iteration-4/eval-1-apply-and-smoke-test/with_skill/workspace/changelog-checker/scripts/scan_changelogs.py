#!/usr/bin/env python3
"""
scan_changelogs.py - Inventory a changelogs folder, validate every file's
version heading, and tally entries per category.

Covers changelog-checker steps 1, 2, 3, and 5: list the files sorted by
version with a total count, check that each file starts with a heading of the
form "## vX.Y.Z - YYYY-MM-DD" (em dash), count entries per category, and
render the summary table sorted by version descending.

FINDING CODES
    no_changelog_files             the folder holds no .md file at all
    first_line_not_version_heading line 1 is not a well-formed version heading
    version_heading_missing        no line in the file is a version heading
    malformed_version_heading      line 1 looks like a version heading but does
                                   not match "## vX.Y.Z - YYYY-MM-DD"

USAGE
    python3 scripts/scan_changelogs.py <changelogs-dir> [--json] [--out FILE]

    Default stdout is the markdown summary table plus the finding list.
    --json emits the same data structured. --out writes the chosen format to a
    file and keeps a one-line summary on stdout.

EXIT CODES
    0  No findings.
    1  Findings; every one carries a code above.
    2  Usage error, missing directory, or unreadable file.
"""

import argparse
import json
import re
import sys
from pathlib import Path

CATEGORIES = ["Added", "Fixed", "Changed", "Removed"]
EM_DASH = "—"
VERSION_HEADING = re.compile(
    r"^##\s+v(\d+)\.(\d+)\.(\d+)\s+" + EM_DASH + r"\s+(\d{4}-\d{2}-\d{2})\s*$")
# Anything opening "## v" is a version heading attempt; if it fails the strict
# pattern it is malformed rather than absent, and the two need separate codes.
VERSION_HEADING_LOOSE = re.compile(r"^##\s+v", re.IGNORECASE)
SECTION_HEADING = re.compile(r"^###\s+(.+?)\s*$")
ENTRY = re.compile(r"^[-*]\s+\S")
FILENAME_VERSION = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")
TABLE_ROW_LIMIT = 200  # beyond this the table stops being readable; use --out


def parse_file(path):
    """Return the per-file record: version, date, category counts, findings."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as e:
        raise SystemExit(f"cannot read {path}: {e}")

    findings = []
    first = lines[0] if lines else ""
    strict = VERSION_HEADING.match(first)
    anywhere = any(VERSION_HEADING.match(ln) for ln in lines)

    if not strict:
        findings.append({"code": "first_line_not_version_heading",
                         "file": path.name,
                         "detail": f"line 1 is {first.strip()!r}"})
        if VERSION_HEADING_LOOSE.match(first):
            findings.append({"code": "malformed_version_heading",
                             "file": path.name,
                             "detail": f"line 1 is {first.strip()!r}, expected "
                                       f"'## vX.Y.Z {EM_DASH} YYYY-MM-DD'"})
        if not anywhere:
            findings.append({"code": "version_heading_missing",
                             "file": path.name,
                             "detail": "no line matches "
                                       f"'## vX.Y.Z {EM_DASH} YYYY-MM-DD'"})

    if strict:
        version = f"{strict.group(1)}.{strict.group(2)}.{strict.group(3)}"
        date = strict.group(4)
    else:
        fname = FILENAME_VERSION.search(path.stem)
        version = ".".join(fname.groups()) if fname else "0.0.0"
        date = None

    counts = {c: 0 for c in CATEGORIES}
    counts["Other"] = 0
    section = None
    for ln in lines:
        head = SECTION_HEADING.match(ln)
        if head:
            section = head.group(1)
            continue
        if section and ENTRY.match(ln):
            counts[section if section in counts else "Other"] += 1

    return {"file": path.name, "version": version, "date": date,
            "counts": counts, "total": sum(counts.values()),
            "findings": findings}


def sort_key(record):
    return tuple(int(p) for p in record["version"].split("."))


def scan(directory):
    files = sorted(directory.glob("*.md"))
    if not files:
        return {"dir": str(directory).replace("\\", "/"), "file_count": 0,
                "files": [], "totals": {c: 0 for c in CATEGORIES + ["Other"]},
                "findings": [{"code": "no_changelog_files", "file": None,
                              "detail": f"no .md file in {directory}"}]}

    records = sorted((parse_file(f) for f in files), key=sort_key, reverse=True)
    totals = {c: 0 for c in CATEGORIES + ["Other"]}
    for r in records:
        for c, n in r["counts"].items():
            totals[c] += n
    findings = [f for r in records for f in r["findings"]]
    return {"dir": str(directory).replace("\\", "/"),
            "file_count": len(records), "files": records,
            "totals": totals, "findings": findings}


def render(result):
    cols = CATEGORIES + ["Other"]
    out = [f"{result['file_count']} changelog file(s) in {result['dir']}", ""]
    if result["file_count"]:
        out.append("| Version | Date | " + " | ".join(cols) + " | Total |")
        out.append("|---|---|" + "---|" * (len(cols) + 1))
        for r in result["files"][:TABLE_ROW_LIMIT]:
            cells = " | ".join(str(r["counts"][c]) for c in cols)
            out.append(f"| v{r['version']} | {r['date'] or '(none)'} | "
                       f"{cells} | {r['total']} |")
        tcells = " | ".join(str(result["totals"][c]) for c in cols)
        out.append(f"| **all** |  | {tcells} | "
                   f"{sum(result['totals'].values())} |")
        out.append("")
    if result["findings"]:
        out.append(f"{len(result['findings'])} finding(s):")
        for f in result["findings"]:
            out.append(f"  {f['code']}  {f['file'] or result['dir']}: "
                       f"{f['detail']}")
    else:
        out.append("no findings")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Inventory changelog files, check version headings, "
                    "tally entries per category.")
    ap.add_argument("directory", help="folder holding the changelog .md files")
    ap.add_argument("--json", action="store_true",
                    help="emit structured JSON instead of the table")
    ap.add_argument("--out", help="write the output to FILE instead of stdout")
    args = ap.parse_args(argv)

    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"not a directory: {args.directory}", file=sys.stderr)
        return 2

    result = scan(directory)
    body = json.dumps(result, indent=2) if args.json else render(result)

    if args.out:
        try:
            Path(args.out).write_text(body + "\n", encoding="utf-8")
        except OSError as e:
            print(f"cannot write {args.out}: {e}", file=sys.stderr)
            return 2
        print(f"{result['file_count']} file(s), {len(result['findings'])} "
              f"finding(s) -> {args.out}")
    else:
        print(body)

    return 1 if result["findings"] else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit as e:
        if isinstance(e.code, str):
            print(e.code, file=sys.stderr)
            sys.exit(2)
        raise
