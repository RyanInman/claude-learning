#!/usr/bin/env python3
"""
_changelog.py - Shared parsing helpers for the changelog-checker scripts.

Not a step script: it has no CLI. scan_changelogs.py, check_headings.py,
check_tags.py and render_summary.py all import it so one parser defines the
changelog grammar.

GRAMMAR
    Version header : `## vX.Y.Z — YYYY-MM-DD` (em dash U+2014) on the first
                     non-empty line of the file.
    Category tag   : `### <Tag>`
    Entry          : a line starting with `- ` under the current tag.

EXIT CODES
    None. Callers own their exit codes.
"""

import re
import sys
from pathlib import Path

COUNTED_CATEGORIES = ("Added", "Fixed", "Changed", "Removed")
ALLOWED_TAGS = ("Added", "Fixed", "Changed", "Removed", "Misc")

VERSION_HEADER = re.compile(
    r"^##\s+v(?P<version>\d+\.\d+\.\d+)\s+—\s+(?P<date>\d{4}-\d{2}-\d{2})\s*$"
)
CATEGORY_HEADING = re.compile(r"^###\s+(?P<tag>\S.*?)\s*$")
ENTRY = re.compile(r"^\s*-\s+(?P<text>\S.*?)\s*$")
FILENAME_VERSION = re.compile(r"^v?(?P<version>\d+\.\d+\.\d+)$")

# Files with no parseable version sort after every real version.
UNVERSIONED_SORT_KEY = (10**6, 10**6, 10**6)


def version_key(version):
    """Sort key for a dotted version string; unparseable sorts last."""
    if not version:
        return UNVERSIONED_SORT_KEY
    try:
        return tuple(int(p) for p in version.split("."))
    except ValueError:
        return UNVERSIONED_SORT_KEY


def find_files(directory):
    """Return the .md files in `directory`, sorted by version ascending.

    Raises NotADirectoryError / FileNotFoundError for the caller to map to
    exit 2.
    """
    d = Path(directory)
    if not d.is_dir():
        raise NotADirectoryError(f"not a directory: {directory}")
    files = sorted(d.glob("*.md"))
    return sorted(files, key=lambda p: (version_key(_stem_version(p)), p.name))


def _stem_version(path):
    m = FILENAME_VERSION.match(path.stem)
    return m.group("version") if m else None


def parse_file(path):
    """Parse one changelog file into a dict.

    Keys: file, path, version, date, header_line, header_ok, counts (the four
    counted categories), tags (every tag seen, with its entry count), entries
    (every entry with its category).
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    header_line = ""
    for line in lines:
        if line.strip():
            header_line = line.strip()
            break

    m = VERSION_HEADER.match(header_line)
    version = m.group("version") if m else _stem_version(path)
    date = m.group("date") if m else None

    counts = {c: 0 for c in COUNTED_CATEGORIES}
    tags = {}
    entries = []
    current = None
    for line in lines:
        heading = CATEGORY_HEADING.match(line)
        if heading:
            current = heading.group("tag")
            tags.setdefault(current, 0)
            continue
        entry = ENTRY.match(line)
        if entry and current:
            tags[current] = tags.get(current, 0) + 1
            if current in counts:
                counts[current] += 1
            entries.append({"category": current, "text": entry.group("text")})

    return {
        "file": path.name,
        "path": path.as_posix(),
        "version": version,
        "date": date,
        "header_line": header_line,
        "header_ok": bool(m),
        "counts": counts,
        "tags": tags,
        "entries": entries,
    }


def load_dir(directory):
    """Parse every changelog in `directory`, version ascending."""
    return [parse_file(p) for p in find_files(directory)]


def die_unreadable(exc):
    """Print a predictable-failure message and return exit code 2."""
    print(f"error: {exc}", file=sys.stderr)
    return 2
