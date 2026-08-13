#!/usr/bin/env python3
"""
list_changelogs.py - List the changelog files in a folder, sorted by version.

Backs step 1 of changelog-checker: every .md file in the folder, ordered by the
semantic version in its filename (vX.Y.Z.md), plus the total count. Filenames
that carry no version sort last, alphabetically, and are named under
"unversioned" so a stray file is visible instead of silently mis-sorted.

USAGE
    python3 scripts/list_changelogs.py <changelogs-dir> [--json] [--out FILE]

OUTPUT (--json)
    {"count": N,
     "files": [{"file": "v1.0.0.md", "version": "1.0.0"}, ...],
     "sorted_versions": ["1.0.0", ...],
     "unversioned": ["notes.md", ...],
     "findings": []}

EXIT CODES
    0  At least one .md file found.
    1  Finding: the folder holds no .md file ("no_markdown_files").
    2  Usage error, or the folder is missing or unreadable.
"""

import argparse
import json
import re
import sys
from pathlib import Path

VERSION_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
# Unversioned names sort after every real version, so this key beats any
# plausible major number without pinning a magic literal at the call site.
UNVERSIONED_RANK = (float("inf"), float("inf"), float("inf"))


def collect(folder):
    files, unversioned = [], []
    for path in sorted(folder.glob("*.md")):
        m = VERSION_RE.match(path.stem)
        if m:
            files.append({"file": path.name,
                          "version": ".".join(m.groups()),
                          "_key": tuple(int(g) for g in m.groups())})
        else:
            unversioned.append(path.name)
            files.append({"file": path.name, "version": None,
                          "_key": UNVERSIONED_RANK})
    files.sort(key=lambda f: (f["_key"], f["file"]))
    for f in files:
        del f["_key"]
    return files, unversioned


def main(argv=None):
    ap = argparse.ArgumentParser(description="List changelog files sorted by version.")
    ap.add_argument("folder", help="Folder holding the changelog .md files")
    ap.add_argument("--json", action="store_true", help="Emit JSON on stdout")
    ap.add_argument("--out", help="Write the JSON to FILE instead of stdout")
    args = ap.parse_args(argv)

    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"not a folder: {args.folder}", file=sys.stderr)
        return 2

    files, unversioned = collect(folder)
    findings = [] if files else ["no_markdown_files"]
    payload = {"count": len(files), "files": files,
               "sorted_versions": [f["version"] for f in files if f["version"]],
               "unversioned": unversioned, "findings": findings}

    text = json.dumps(payload, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"{payload['count']} file(s) -> {args.out}")
    elif args.json:
        print(text)
    else:
        print(f"{payload['count']} changelog file(s)")
        for f in files:
            print(f"  {f['file']}  {f['version'] or 'unversioned'}")
        if findings:
            print("  findings: " + ", ".join(findings))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
