#!/usr/bin/env python3
"""
list_changelogs.py - List every changelog .md file in a folder, version-sorted
ascending, with the total count.

Version comes from the filename (vX.Y.Z.md) when it matches, otherwise from the
first `## vX.Y.Z` heading in the file. Files with no version sort last, after
the versioned ones, by filename.

USAGE
    python3 scripts/list_changelogs.py <changelogs-dir> [--json] [--out FILE]

OUTPUT (stdout, JSON)
    {"dir": "...", "count": N,
     "versions": ["1.0.0", ...],
     "files": [{"path": "...", "name": "...", "version": "1.0.0"|null}]}

EXIT CODES
    0  At least one .md file found.
    1  No .md files found (count 0).
    2  Usage error / directory missing or unreadable.
"""

import argparse
import json
import re
import sys
from pathlib import Path

VERSION_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
HEADING_RE = re.compile(r"^##\s+v(\d+\.\d+\.\d+)", re.MULTILINE)
# Sorts unversioned files after every versioned one.
NO_VERSION_KEY = (1, (), "")


def version_of(path):
    m = VERSION_RE.match(path.stem)
    if m:
        return ".".join(m.groups())
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    m = HEADING_RE.search(text)
    return m.group(1) if m else None


def sort_key(entry):
    if entry["version"] is None:
        return (NO_VERSION_KEY[0], NO_VERSION_KEY[1], entry["name"])
    parts = tuple(int(p) for p in entry["version"].split("."))
    return (0, parts, entry["name"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("changelogs_dir", help="folder holding the changelog .md files")
    ap.add_argument("--json", action="store_true",
                    help="accepted for interface stability; output is always JSON")
    ap.add_argument("--out", help="write the JSON to FILE; print a summary to stdout")
    args = ap.parse_args(argv)

    root = Path(args.changelogs_dir)
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    entries = []
    for p in root.glob("*.md"):
        entries.append({"path": p.as_posix(), "name": p.name, "version": version_of(p)})
    entries.sort(key=sort_key)

    data = {
        "dir": root.as_posix(),
        "count": len(entries),
        "versions": [e["version"] for e in entries if e["version"]],
        "files": entries,
    }
    payload = json.dumps(data)

    if args.out:
        try:
            Path(args.out).write_text(payload + "\n", encoding="utf-8")
        except OSError as e:
            print(f"cannot write {args.out}: {e}", file=sys.stderr)
            return 2
        print(f"{data['count']} changelog files -> {args.out}")
    else:
        print(payload)

    if not entries:
        print(f"no .md files in {root}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
