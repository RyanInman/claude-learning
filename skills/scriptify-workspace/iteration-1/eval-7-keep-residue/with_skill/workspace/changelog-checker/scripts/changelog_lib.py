#!/usr/bin/env python3
"""
changelog_lib.py - Shared parsing helpers for the changelog-checker scripts.

Not a CLI. Imported by list_changelogs.py, check_headings.py,
count_entries.py, render_table.py, check_tags.py and list_entries.py, which
sit in the same folder, so a plain `import changelog_lib` resolves.

CHANGELOG FILE SHAPE
    ## v1.2.0 — 2026-03-02      version heading (strict form uses an em dash)
    ### Added                   category heading
    - CSV export                entry
"""

import re
import sys
from pathlib import Path

# The categories a changelog entry may be filed under.
ALLOWED_CATEGORIES = ["Added", "Fixed", "Changed", "Removed", "Misc"]

# The heading exactly as the workflow specifies it: em dash, ISO date.
STRICT_HEADING = re.compile(r"^## v(\d+\.\d+\.\d+) — (\d{4}-\d{2}-\d{2})$")
# Lenient form, so the reporting scripts still parse a sloppy heading that
# check_headings.py flags separately (any dash, loose spacing).
LOOSE_HEADING = re.compile(
    r"^##\s+v(\d+\.\d+\.\d+)\s*[—–-]\s*(\d{4}-\d{2}-\d{2})\s*$")
CATEGORY_HEADING = re.compile(r"^###\s+(\S.*?)\s*$")
ENTRY = re.compile(r"^[-*]\s+(\S.*?)\s*$")

# Sort key for a file whose version heading is missing or unparseable: it
# sorts below every real version instead of crashing the sort.
UNKNOWN_VERSION_KEY = (-1, -1, -1)


class ChangelogError(Exception):
    """A caller-facing failure: exit 2 and print the message to stderr."""


def find_files(directory):
    """Return every .md file in directory, sorted by version then name."""
    d = Path(directory)
    if not d.is_dir():
        raise ChangelogError(f"not a directory: {directory}")
    try:
        files = [p for p in d.iterdir() if p.is_file() and p.suffix == ".md"]
    except OSError as e:
        raise ChangelogError(f"cannot read directory {directory}: {e}")
    return sorted(files, key=lambda p: (version_key(read_version(p)), p.name))


def version_key(version):
    """Numeric sort key, so 1.10.0 sorts above 1.9.0."""
    if not version:
        return UNKNOWN_VERSION_KEY
    return tuple(int(part) for part in version.split("."))


def read_version(path):
    """Version from the file's heading, or None when there is no heading."""
    return parse_file(path)["version"]


def parse_file(path):
    """Parse one changelog file into {file, path, version, date, entries}.

    entries: [{category, line, text}] - category is the last `###` heading
    seen above the entry, or None for an entry filed under no category.
    """
    p = Path(path)
    try:
        lines = p.read_text(encoding="utf-8").splitlines()
    except OSError as e:
        raise ChangelogError(f"cannot read file {path}: {e}")

    version = date = None
    heading_line = None
    category = None
    entries = []
    for i, line in enumerate(lines, start=1):
        m = LOOSE_HEADING.match(line)
        if m and version is None:
            version, date = m.group(1), m.group(2)
            heading_line = i
            continue
        m = CATEGORY_HEADING.match(line)
        if m:
            category = m.group(1)
            continue
        m = ENTRY.match(line)
        if m:
            entries.append({"category": category, "line": i, "text": m.group(1)})
    return {"file": p.name, "path": p.as_posix(), "version": version,
            "date": date, "heading_line": heading_line,
            "first_line": lines[0] if lines else "", "entries": entries}


def parse_dir(directory):
    """Parse every changelog file in directory, version-sorted ascending."""
    return [parse_file(p) for p in find_files(directory)]


def counts_for(parsed):
    """Per-category entry counts for one parsed file, allowed categories only."""
    counts = {c: 0 for c in ALLOWED_CATEGORIES}
    for entry in parsed["entries"]:
        if entry["category"] in counts:
            counts[entry["category"]] += 1
    return counts


def emit(payload, out_path, summary):
    """Write JSON to stdout, or to --out with a one-line summary on stdout."""
    import json
    text = json.dumps(payload, indent=2)
    if out_path:
        try:
            Path(out_path).write_text(text + "\n", encoding="utf-8")
        except OSError as e:
            print(f"error: cannot write {out_path}: {e}", file=sys.stderr)
            return 2
        print(f"{summary} -> {out_path}")
        return None
    print(text)
    return None
