#!/usr/bin/env python3
"""
check_tags.py - Check every entry's category tag against the allowed list and
collect the Misc entries for re-triage.

Two finding kinds, kept in two stdout fields because they route differently:
    invalid[]  code unknown_category   - a tag outside the allowed list; a fixed rule decides it
    misc[]     code misc_needs_triage  - a Misc entry; only judgment decides where it belongs

USAGE
    python3 scripts/check_tags.py <changelogs-dir> [--json]

EXIT CODES
    0  Every tag is allowed and no entry is tagged Misc.
    1  Findings; the JSON on stdout carries invalid[] and misc[].
    2  Usage error, or the folder is missing or unreadable.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_changelogs import parse_file, sorted_files  # noqa: E402

ALLOWED = ["Added", "Fixed", "Changed", "Removed", "Misc"]
TRIAGE_TARGETS = ["Added", "Fixed", "Changed", "Removed"]


def check(directory):
    invalid, misc = [], []
    files = sorted_files(directory)
    for path in files:
        info = parse_file(path)
        for entry in info["entries"]:
            tag = entry["category"]
            if tag not in ALLOWED:
                invalid.append({"code": "unknown_category", "file": info["file"],
                                "tag": tag, "entry": entry["text"]})
            elif tag == "Misc":
                misc.append({"code": "misc_needs_triage", "file": info["file"],
                             "entry": entry["text"], "candidates": TRIAGE_TARGETS})
    return {"dir": Path(directory).as_posix(), "allowed": ALLOWED,
            "checked": len(files), "invalid": invalid, "misc": misc}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check entry category tags and collect Misc entries for re-triage.")
    ap.add_argument("directory", help="Folder holding the changelog .md files")
    ap.add_argument("--json", action="store_true", help="Print JSON (the default and only format; accepted for symmetry)")
    args = ap.parse_args(argv)

    d = Path(args.directory)
    if not d.is_dir():
        print(f"check_tags: not a directory: {args.directory}", file=sys.stderr)
        return 2
    try:
        result = check(d)
    except OSError as e:
        print(f"check_tags: cannot read {args.directory}: {e}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2))
    return 1 if (result["invalid"] or result["misc"]) else 0


if __name__ == "__main__":
    sys.exit(main())
