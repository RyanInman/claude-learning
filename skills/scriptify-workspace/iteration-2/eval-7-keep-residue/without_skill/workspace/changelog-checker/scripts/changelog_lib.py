"""Shared parsing helpers for the changelog-checker scripts."""

import os
import re
import sys

HEADER_RE = re.compile(r"^##\s+v(\d+\.\d+\.\d+)\s+[-—]\s+(\d{4}-\d{2}-\d{2})\s*$")
SECTION_RE = re.compile(r"^###\s+(\S+)\s*$")
ENTRY_RE = re.compile(r"^[-*]\s+(.*\S)\s*$")
FILENAME_VERSION_RE = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")

KNOWN_CATEGORIES = ["Added", "Fixed", "Changed", "Removed"]
ALLOWED_TAGS = ["Added", "Fixed", "Changed", "Removed", "Misc"]


def die(msg):
    sys.stderr.write("error: %s\n" % msg)
    raise SystemExit(2)


def require_dir(argv):
    """Pull the changelog directory off argv, or exit 2 if it is missing/bad."""
    positional = [a for a in argv[1:] if not a.startswith("--")]
    if len(positional) != 1:
        die("usage: %s CHANGELOG_DIR [--json]" % os.path.basename(argv[0]))
    path = positional[0]
    if not os.path.isdir(path):
        die("not a directory: %s" % path)
    return path


def version_key(version):
    m = FILENAME_VERSION_RE.search(version or "")
    if not m:
        return (0, 0, 0)
    return tuple(int(p) for p in m.groups())


def list_files(directory):
    """Changelog .md files, sorted by the version in the filename (ascending)."""
    names = [n for n in os.listdir(directory) if n.endswith(".md")]
    names.sort(key=lambda n: (version_key(n), n))
    return [os.path.join(directory, n) for n in names]


def filename_version(path):
    m = FILENAME_VERSION_RE.search(os.path.basename(path))
    return ".".join(m.groups()) if m else None


def parse_file(path):
    """Parse one changelog file into {path, name, header_version, date, sections}."""
    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.read().splitlines()

    header_version = None
    date = None
    sections = []
    current = None

    for line in lines:
        header = HEADER_RE.match(line)
        if header and header_version is None:
            header_version, date = header.group(1), header.group(2)
            continue
        section = SECTION_RE.match(line)
        if section:
            current = {"category": section.group(1), "entries": []}
            sections.append(current)
            continue
        entry = ENTRY_RE.match(line)
        if entry and current is not None:
            current["entries"].append(entry.group(1))

    return {
        "path": path,
        "name": os.path.basename(path),
        "file_version": filename_version(path),
        "header_version": header_version,
        "date": date,
        "sections": sections,
    }


def parse_dir(directory):
    return [parse_file(p) for p in list_files(directory)]


def wants_json(argv):
    return "--json" in argv[1:]
