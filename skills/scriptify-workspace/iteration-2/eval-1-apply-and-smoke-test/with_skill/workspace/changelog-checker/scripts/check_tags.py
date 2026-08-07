#!/usr/bin/env python3
"""
check_tags.py - Check every category tag against the allowed list
(Added, Fixed, Changed, Removed, Misc) and list every Misc entry for re-triage.

The membership check is mechanical and lives here. Whether a Misc entry really
belongs under another category is contextual, so the script only enumerates
those entries; the caller judges them.

USAGE
    python3 scripts/check_tags.py <changelogs-dir> [--json] [--out FILE]

    --json   full JSON on stdout (default is a one-line summary)
    --out F  write the full JSON to F, keep the summary on stdout

STDOUT (--json)
    {"dir", "allowed", "invalid": [{"file", "tag", "entries"}],
     "misc": [{"file", "text"}]}

EXIT CODES
    0  Every tag is in the allowed list (misc may still be non-empty).
    1  At least one tag is outside the allowed list.
    2  Usage error, or the directory is missing or unreadable.
"""

import argparse
import json
import sys

import _changelog

MISC_TAG = "Misc"


def check(directory):
    parsed = _changelog.load_dir(directory)
    invalid = []
    misc = []
    for p in parsed:
        for tag, count in p["tags"].items():
            if tag not in _changelog.ALLOWED_TAGS:
                invalid.append({"file": p["file"], "tag": tag, "entries": count})
        for entry in p["entries"]:
            if entry["category"] == MISC_TAG:
                misc.append({"file": p["file"], "text": entry["text"]})
    return {
        "dir": directory,
        "allowed": list(_changelog.ALLOWED_TAGS),
        "invalid": invalid,
        "misc": misc,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Check changelog category tags and list Misc entries.")
    parser.add_argument("directory", help="Folder holding the .md changelogs")
    parser.add_argument("--json", action="store_true",
                        help="Print the full JSON instead of a summary line")
    parser.add_argument("--out", help="Write the full JSON to this file")
    args = parser.parse_args(argv)

    try:
        result = check(args.directory)
    except (OSError, ValueError) as e:
        return _changelog.die_unreadable(e)

    blob = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(blob + "\n")
        except OSError as e:
            return _changelog.die_unreadable(e)

    if args.json:
        print(blob)
    else:
        print(f"{len(result['invalid'])} invalid tag(s), "
              f"{len(result['misc'])} Misc entry(ies) to re-triage")

    return 1 if result["invalid"] else 0


if __name__ == "__main__":
    sys.exit(main())
