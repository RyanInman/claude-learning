#!/usr/bin/env python3
"""
check_changelogs.py - Validate changelog headings and category tags.

Checks two fixed rules: every file opens with a `## vX.Y.Z — YYYY-MM-DD`
heading, and every `###` category tag is on the allowed list. Entries tagged
`Misc` are legal, so they are reported separately under `misc` for a human
judgment call, not as violations.

FINDING CODES
    no_version_heading         no `## vX.Y.Z — YYYY-MM-DD` heading anywhere
    version_heading_not_first  a conforming heading exists, but another
                               heading comes before it
    malformed_version_heading  the first heading starts `## v` but does not
                               match the required version-and-date form
    invalid_tag                a `###` category outside the allowed list

USAGE
    python3 scripts/check_changelogs.py changelogs/ --json

    --json   print the full findings JSON (default prints a compact summary)

STDOUT
    Findings JSON with `violations`, `misc`, and `allowed`, or a compact
    summary without --json.

EXIT CODES
    0  Clean: no violations and no Misc entries to triage.
    1  Findings: violations, Misc entries, or both.
    2  Usage error, missing folder, or unreadable file.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ALLOWED = ["Added", "Fixed", "Changed", "Removed", "Misc"]
VERSION_HEADING = re.compile(r"^##\s+v\d+\.\d+\.\d+\s+—\s+\d{4}-\d{2}-\d{2}\s*$")
ANY_HEADING = re.compile(r"^#{1,6}\s+\S")
H2_VERSION_ATTEMPT = re.compile(r"^##\s+v", re.IGNORECASE)
CATEGORY_HEADING = re.compile(r"^###\s+(.+?)\s*$")
ENTRY = re.compile(r"^[-*]\s+(.+?)\s*$")


def check_headings(name, lines):
    """Return the heading violations for one file."""
    headings = [ln for ln in lines if ANY_HEADING.match(ln)]
    conforming = [ln for ln in headings if VERSION_HEADING.match(ln)]
    if not conforming:
        first = headings[0] if headings else ""
        if H2_VERSION_ATTEMPT.match(first):
            return [{"code": "malformed_version_heading", "file": name,
                     "detail": "first heading %r does not match `## vX.Y.Z — YYYY-MM-DD`" % first}]
        return [{"code": "no_version_heading", "file": name,
                 "detail": "no `## vX.Y.Z — YYYY-MM-DD` heading in the file"}]
    if headings[0] != conforming[0]:
        return [{"code": "version_heading_not_first", "file": name,
                 "detail": "%r comes before the version heading" % headings[0]}]
    return []


def check_tags(name, lines):
    """Return invalid-tag violations and Misc entries for one file."""
    violations = []
    misc = []
    category = None
    for line in lines:
        m = CATEGORY_HEADING.match(line)
        if m:
            category = m.group(1)
            if category not in ALLOWED:
                violations.append({"code": "invalid_tag", "file": name, "tag": category,
                                   "detail": "category %r is not on the allowed list" % category})
            continue
        m = ENTRY.match(line)
        if m and category == "Misc":
            misc.append({"file": name, "text": m.group(1)})
    return violations, misc


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate changelog headings and category tags.")
    ap.add_argument("folder", help="Folder holding the changelog .md files")
    ap.add_argument("--json", action="store_true", dest="as_json",
                    help="Print the full findings JSON")
    args = ap.parse_args(argv)

    folder = Path(args.folder)
    if not folder.is_dir():
        sys.stderr.write("not a folder: %s\n" % folder)
        return 2

    violations = []
    misc = []
    files = sorted(p for p in folder.glob("*.md") if p.is_file())
    for path in files:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as e:
            sys.stderr.write("cannot read %s: %s\n" % (path, e))
            return 2
        violations.extend(check_headings(path.name, lines))
        tag_violations, file_misc = check_tags(path.name, lines)
        violations.extend(tag_violations)
        misc.extend(file_misc)

    findings = {
        "dir": folder.as_posix(),
        "file_count": len(files),
        "allowed": ALLOWED,
        "violations": violations,
        "misc": misc,
    }
    if args.as_json:
        print(json.dumps(findings, indent=2, ensure_ascii=False))
    else:
        print("checked %d files: %d violations, %d Misc entries to triage"
              % (len(files), len(violations), len(misc)))
        for v in violations:
            print("  %s %s: %s" % (v["code"], v["file"], v["detail"]))
        for m in misc:
            print("  misc %s: %s" % (m["file"], m["text"]))
    return 1 if (violations or misc) else 0


if __name__ == "__main__":
    sys.exit(main())
