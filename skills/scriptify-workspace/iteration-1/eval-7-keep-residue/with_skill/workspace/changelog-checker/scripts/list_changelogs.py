#!/usr/bin/env python3
"""
list_changelogs.py - List every .md file in a changelogs folder, sorted by
version ascending, with the total count.

Version-aware sort: 1.10.0 sorts above 1.9.0, which a plain name sort gets
wrong. A file with no parseable version heading sorts first, with a null
version.

USAGE
    python3 scripts/list_changelogs.py changelogs/ [--json] [--out FILE]

STDOUT
    --json: {"count": N, "versions": [...], "files": [{path, file, version,
    date}]}. Default: one "version  file" line per file plus the count.

EXIT CODES
    0  One or more changelog files found.
    1  No .md files in the directory.
    2  Usage error, or the directory is missing or unreadable.
"""

import argparse
import sys

import changelog_lib as cl


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="List changelog files sorted by version, with a count.")
    parser.add_argument("directory", help="Folder holding the changelog .md files")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--out", help="Write JSON to FILE, summary to stdout")
    args = parser.parse_args(argv)

    try:
        parsed = cl.parse_dir(args.directory)
    except cl.ChangelogError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    files = [{"path": p["path"], "file": p["file"], "version": p["version"],
              "date": p["date"]} for p in parsed]
    payload = {"count": len(files),
               "versions": [f["version"] for f in files],
               "files": files}

    if args.json or args.out:
        rc = cl.emit(payload, args.out, f"{len(files)} changelog files")
        if rc is not None:
            return rc
    else:
        for f in files:
            print(f"{f['version'] or 'unknown':<10} {f['file']}")
        print(f"{len(files)} changelog files")

    if not files:
        print(f"warning: no .md files in {args.directory}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
