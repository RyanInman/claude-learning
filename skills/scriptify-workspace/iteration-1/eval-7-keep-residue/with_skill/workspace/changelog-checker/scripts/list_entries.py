#!/usr/bin/env python3
"""
list_entries.py - List every changelog entry with neutral length facts, so a
reader can judge which entries are confusing.

Facts only. The script reports word_count and char_count and never scores
clarity, because "a reader would find this confusing" is a judgment that
varies with the audience, and a script that guessed it would look
authoritative while being arbitrary.

USAGE
    python3 scripts/list_entries.py changelogs/ [--json] [--out FILE]

STDOUT
    --json: {"count": N, "entries": [{file, version, category, line, text,
    word_count, char_count}]}, version ascending, file order preserved.

EXIT CODES
    0  One or more entries listed.
    1  No entries found in any file.
    2  Usage error, or the directory is missing or unreadable.
"""

import argparse
import sys

import changelog_lib as cl


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="List every changelog entry with neutral length facts.")
    parser.add_argument("directory", help="Folder holding the changelog .md files")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--out", help="Write JSON to FILE, summary to stdout")
    args = parser.parse_args(argv)

    try:
        parsed = cl.parse_dir(args.directory)
    except cl.ChangelogError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    entries = []
    for p in parsed:
        for entry in p["entries"]:
            text = entry["text"]
            entries.append({"file": p["file"], "version": p["version"],
                            "category": entry["category"], "line": entry["line"],
                            "text": text, "word_count": len(text.split()),
                            "char_count": len(text)})

    payload = {"count": len(entries), "entries": entries}
    summary = f"{len(entries)} entries across {len(parsed)} files"

    if args.json or args.out:
        rc = cl.emit(payload, args.out, summary)
        if rc is not None:
            return rc
    else:
        for e in entries:
            print(f"{e['file']}:{e['line']}  [{e['category']}]  "
                  f"{e['word_count']}w  {e['text']}")
        print(summary)

    if not entries:
        print(f"warning: no entries found in {args.directory}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
