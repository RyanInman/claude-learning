#!/usr/bin/env python3
"""
check_categories.py - Check every changelog entry's category tag against the
allowed list and isolate the Misc entries that need a human re-triage.

Covers changelog-checker step 6. The allowed-list test is decided here; the
Misc entries are returned verbatim so the caller can judge whether each one
really belongs under Added, Fixed, Changed, or Removed.

FINDING CODES
    unknown_category   the "### <Category>" tag is outside the allowed list
    misc_needs_triage  the entry sits under "### Misc" and needs a judgment call

USAGE
    python3 scripts/check_categories.py <changelogs-dir> [--json] [--out FILE]

    Default stdout is a compact text listing. --json emits
    {"invalid": [...], "misc": [...], "counts": {...}}, each record carrying
    file, category, entry, and code.

EXIT CODES
    0  Every tag is allowed and no Misc entry needs triage.
    1  Findings; every one carries a code above.
    2  Usage error, missing directory, or unreadable file.
"""

import argparse
import json
import sys
from pathlib import Path
import re

ALLOWED = ["Added", "Fixed", "Changed", "Removed", "Misc"]
TRIAGE_CATEGORY = "Misc"
SECTION_HEADING = re.compile(r"^###\s+(.+?)\s*$")
ENTRY = re.compile(r"^[-*]\s+(\S.*)$")


def scan_file(path):
    """Return (invalid, misc) records for one changelog file."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as e:
        raise SystemExit(f"cannot read {path}: {e}")

    invalid, misc, section = [], [], None
    for ln in lines:
        head = SECTION_HEADING.match(ln)
        if head:
            section = head.group(1)
            continue
        entry = ENTRY.match(ln)
        if not (section and entry):
            continue
        record = {"file": path.name, "category": section,
                  "entry": entry.group(1)}
        if section not in ALLOWED:
            invalid.append(dict(record, code="unknown_category"))
        elif section == TRIAGE_CATEGORY:
            misc.append(dict(record, code="misc_needs_triage"))
    return invalid, misc


def scan(directory):
    invalid, misc, counts = [], [], {}
    for path in sorted(directory.glob("*.md")):
        i, m = scan_file(path)
        invalid.extend(i)
        misc.extend(m)
    for rec in invalid + misc:
        counts[rec["category"]] = counts.get(rec["category"], 0) + 1
    return {"dir": str(directory).replace("\\", "/"), "allowed": ALLOWED,
            "invalid": invalid, "misc": misc, "counts": counts}


def render(result):
    out = [f"allowed categories: {', '.join(ALLOWED)}"]
    if result["invalid"]:
        out.append(f"{len(result['invalid'])} entry(s) under a category "
                   "outside the allowed list:")
        for r in result["invalid"]:
            out.append(f"  unknown_category  {r['file']}  [{r['category']}] "
                       f"{r['entry']}")
    if result["misc"]:
        out.append(f"{len(result['misc'])} Misc entry(s) to re-triage:")
        for r in result["misc"]:
            out.append(f"  misc_needs_triage  {r['file']}  {r['entry']}")
    if not result["invalid"] and not result["misc"]:
        out.append("no findings")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Check changelog category tags against the allowed list "
                    "and list the Misc entries needing re-triage.")
    ap.add_argument("directory", help="folder holding the changelog .md files")
    ap.add_argument("--json", action="store_true",
                    help="emit structured JSON instead of the text listing")
    ap.add_argument("--out", help="write the output to FILE instead of stdout")
    args = ap.parse_args(argv)

    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"not a directory: {args.directory}", file=sys.stderr)
        return 2

    result = scan(directory)
    findings = len(result["invalid"]) + len(result["misc"])
    body = json.dumps(result, indent=2) if args.json else render(result)

    if args.out:
        try:
            Path(args.out).write_text(body + "\n", encoding="utf-8")
        except OSError as e:
            print(f"cannot write {args.out}: {e}", file=sys.stderr)
            return 2
        print(f"{findings} finding(s) -> {args.out}")
    else:
        print(body)

    return 1 if findings else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit as e:
        if isinstance(e.code, str):
            print(e.code, file=sys.stderr)
            sys.exit(2)
        raise
