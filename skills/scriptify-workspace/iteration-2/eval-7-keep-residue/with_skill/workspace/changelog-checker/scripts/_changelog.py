#!/usr/bin/env python3
"""
_changelog.py - Shared parsing helpers for the changelog-checker scripts.

Not an entry point: import-only, no CLI. The four scripts in this folder
(parse_changelogs.py, check_headings.py, check_tags.py,
render_summary_table.py) all read the same file shape, so the discovery,
heading, and entry rules live here once.

CHANGELOG FILE SHAPE
    ## v1.2.0 — 2026-05-01      version heading (em dash between the two)
    ### Added                    category heading
    - Dark mode                  entry
"""

import re
import sys
from pathlib import Path

# The four counted categories plus the catch-all the workflow tolerates.
KNOWN_CATEGORIES = ["Added", "Fixed", "Changed", "Removed", "Misc"]
COUNTED_CATEGORIES = ["Added", "Fixed", "Changed", "Removed"]

# `## vX.Y.Z — YYYY-MM-DD`, em dash separator, as the workflow specifies.
VERSION_HEADING_RE = re.compile(
    r"^##\s+v(?P<version>\d+\.\d+\.\d+)\s+—\s+(?P<date>\d{4}-\d{2}-\d{2})\s*$"
)
# Any `## v...` line, used to tell "malformed heading" from "no heading at all".
LOOSE_VERSION_HEADING_RE = re.compile(r"^##\s+v?\d", re.IGNORECASE)
CATEGORY_HEADING_RE = re.compile(r"^###\s+(?P<category>.+?)\s*$")
ENTRY_RE = re.compile(r"^[-*]\s+(?P<text>.+?)\s*$")

# Files without a parseable version sort last; no real version reaches 10^6.
UNVERSIONED_SORT_KEY = (10**6, 10**6, 10**6)


def discover(dirpath):
    """Return the changelog .md files in dirpath, sorted by filename.

    Raises NotADirectoryError when dirpath is not a readable directory.
    """
    d = Path(dirpath)
    if not d.is_dir():
        raise NotADirectoryError(f"not a directory: {dirpath}")
    return sorted(d.glob("*.md"), key=lambda p: p.name)


def version_sort_key(version):
    if not version:
        return UNVERSIONED_SORT_KEY
    return tuple(int(part) for part in version.split("."))


def parse_file(path):
    """Parse one changelog file into a record.

    Returns {file, version, date, heading_status, counts, entries} where
    heading_status is "ok", "malformed_version_header", or
    "missing_version_header".
    """
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()

    version = date = None
    heading_status = "missing_version_header"
    for line in lines:
        if not line.strip():
            continue
        m = VERSION_HEADING_RE.match(line)
        if m:
            version, date = m.group("version"), m.group("date")
            heading_status = "ok"
        elif LOOSE_VERSION_HEADING_RE.match(line):
            heading_status = "malformed_version_header"
        break  # only the FIRST non-blank line counts as the file's heading

    if version is None:
        stem = Path(path).stem.lstrip("vV")
        if re.fullmatch(r"\d+\.\d+\.\d+", stem):
            version = stem

    entries = []
    counts = {c: 0 for c in KNOWN_CATEGORIES}
    current = None
    for line in lines:
        mh = CATEGORY_HEADING_RE.match(line)
        if mh:
            current = mh.group("category")
            continue
        me = ENTRY_RE.match(line)
        if me and current:
            entries.append({"file": Path(path).name,
                            "category": current,
                            "text": me.group("text")})
            if current in counts:
                counts[current] += 1
    return {"file": Path(path).name,
            "version": version,
            "date": date,
            "heading_status": heading_status,
            "counts": counts,
            "entries": entries}


def parse_dir(dirpath):
    """Parse every changelog in dirpath, sorted by version ascending."""
    records = [parse_file(p) for p in discover(dirpath)]
    records.sort(key=lambda r: (version_sort_key(r["version"]), r["file"]))
    return records


def fail(message, code=2):
    """Print a diagnostic to stderr and exit."""
    print(message, file=sys.stderr)
    sys.exit(code)
