#!/usr/bin/env python3
"""Scan a changelogs folder and print the deterministic half of the changelog report.

Covers: file inventory, heading-format validation, per-category entry counts,
the version-sorted summary table, and category-tag validation. Judgment calls
(the release narrative, whether a Misc entry belongs elsewhere, entry clarity)
are left to the caller; this script surfaces the raw material for them.
"""

import argparse
import re
import sys
from pathlib import Path

CATEGORIES = ["Added", "Fixed", "Changed", "Removed", "Misc"]
KNOWN = set(CATEGORIES)
HEADING_RE = re.compile(r"^## v(\d+)\.(\d+)\.(\d+) [-–—] (\d{4}-\d{2}-\d{2})\s*$")
SECTION_RE = re.compile(r"^###\s+(.+?)\s*$")
ENTRY_RE = re.compile(r"^[-*]\s+(.*\S)\s*$")
FILENAME_VERSION_RE = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")


def parse_file(path):
    """Return a dict describing one changelog file."""
    lines = path.read_text(encoding="utf-8").splitlines()
    record = {
        "file": path.name,
        "version": None,
        "date": None,
        "heading_ok": False,
        "heading_line": lines[0].strip() if lines else "",
        "sort_key": (0, 0, 0),
        "counts": {c: 0 for c in CATEGORIES},
        "unknown_sections": [],
        "misc_entries": [],
        "entries": [],
    }

    first = next((ln for ln in lines if ln.strip()), "")
    match = HEADING_RE.match(first.strip())
    if match:
        record["heading_ok"] = True
        record["version"] = "v%s.%s.%s" % match.group(1, 2, 3)
        record["date"] = match.group(4)
        record["sort_key"] = tuple(int(match.group(i)) for i in (1, 2, 3))

    if record["version"] is None:
        stem = FILENAME_VERSION_RE.search(path.stem)
        if stem:
            record["version"] = "v%s.%s.%s" % stem.group(1, 2, 3)
            record["sort_key"] = tuple(int(stem.group(i)) for i in (1, 2, 3))
        else:
            record["version"] = path.stem

    section = None
    for line in lines:
        sec = SECTION_RE.match(line)
        if sec:
            section = sec.group(1)
            if section not in KNOWN and section not in record["unknown_sections"]:
                record["unknown_sections"].append(section)
            continue
        entry = ENTRY_RE.match(line)
        if entry and section:
            text = entry.group(1)
            record["entries"].append((section, text))
            if section in record["counts"]:
                record["counts"][section] += 1
            if section == "Misc":
                record["misc_entries"].append(text)
    return record


def render(records, folder):
    out = []
    out.append("## Changelog scan: %s" % folder)
    out.append("")
    out.append("Files found: %d (%s)" % (len(records), ", ".join(r["file"] for r in records)))
    out.append("")

    out.append("### Heading format")
    bad = [r for r in records if not r["heading_ok"]]
    if bad:
        for r in bad:
            out.append("- %s: expected `## vX.Y.Z - YYYY-MM-DD`, found `%s`"
                       % (r["file"], r["heading_line"] or "<empty first line>"))
    else:
        out.append("- All files start with a valid `## vX.Y.Z - YYYY-MM-DD` heading.")
    out.append("")

    out.append("### Summary table")
    out.append("| Version | Date | " + " | ".join(CATEGORIES) + " | Total |")
    out.append("|---|---|" + "---|" * (len(CATEGORIES) + 1))
    totals = {c: 0 for c in CATEGORIES}
    for r in sorted(records, key=lambda r: r["sort_key"], reverse=True):
        row_total = sum(r["counts"].values())
        for c in CATEGORIES:
            totals[c] += r["counts"][c]
        out.append("| %s | %s | %s | %d |" % (
            r["version"], r["date"] or "missing",
            " | ".join(str(r["counts"][c]) for c in CATEGORIES), row_total))
    out.append("| **Total** | | %s | %d |" % (
        " | ".join(str(totals[c]) for c in CATEGORIES), sum(totals.values())))
    out.append("")

    out.append("### Category tags")
    unknown = [(r["file"], s) for r in records for s in r["unknown_sections"]]
    if unknown:
        for fname, sec in unknown:
            out.append("- %s: `%s` is not in the allowed list (%s)."
                       % (fname, sec, ", ".join(CATEGORIES)))
    else:
        out.append("- Every section tag is in the allowed list.")
    misc = [(r["file"], e) for r in records for e in r["misc_entries"]]
    if misc:
        out.append("")
        out.append("Misc entries needing a judgment call:")
        for fname, entry in misc:
            out.append("- %s: %s" % (fname, entry))
    out.append("")

    out.append("### All entries")
    for r in sorted(records, key=lambda r: r["sort_key"], reverse=True):
        out.append("- %s (%s)" % (r["version"], r["file"]))
        for section, text in r["entries"]:
            out.append("  - [%s] %s" % (section, text))
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("folder", nargs="?", default="changelogs",
                    help="path to the changelogs folder (default: changelogs)")
    args = ap.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        sys.exit("error: %s is not a directory" % folder)
    files = sorted(folder.glob("*.md"))
    if not files:
        sys.exit("error: no .md files in %s" % folder)

    print(render([parse_file(f) for f in files], folder))


if __name__ == "__main__":
    main()
