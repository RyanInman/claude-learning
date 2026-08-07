#!/usr/bin/env python3
"""
check_tags.py - Check every entry's category tag against the allowed list,
and collect the Misc entries for re-triage.

Two separable outputs. "invalid" is mechanical: the tag is not one of Added,
Fixed, Changed, Removed, Misc. "misc" is the residue a human or Claude judges
- whether a Misc entry actually belongs under another category is a reading
of the entry, so this script only lists the candidates and never guesses.

USAGE
    python3 scripts/check_tags.py changelogs/ [--json] [--out FILE]

STDOUT
    --json: {"checked": N, "allowed": [...], "invalid": [{file, tag, line,
    text}], "misc": [{file, version, line, text}]}

EXIT CODES
    0  No invalid tags and no Misc entries.
    1  Invalid tags or Misc entries present.
    2  Usage error, or the directory is missing or unreadable.
"""

import argparse
import sys

import changelog_lib as cl


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Check entry category tags; list Misc entries for re-triage.")
    parser.add_argument("directory", help="Folder holding the changelog .md files")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--out", help="Write JSON to FILE, summary to stdout")
    args = parser.parse_args(argv)

    try:
        parsed = cl.parse_dir(args.directory)
    except cl.ChangelogError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    invalid, misc = [], []
    for p in parsed:
        for entry in p["entries"]:
            tag = entry["category"]
            if tag not in cl.ALLOWED_CATEGORIES:
                invalid.append({"file": p["file"], "tag": tag,
                                "line": entry["line"], "text": entry["text"]})
            elif tag == "Misc":
                misc.append({"file": p["file"], "version": p["version"],
                             "line": entry["line"], "text": entry["text"]})

    payload = {"checked": len(parsed), "allowed": cl.ALLOWED_CATEGORIES,
               "invalid": invalid, "misc": misc}
    summary = f"{len(invalid)} invalid tags, {len(misc)} Misc entries"

    if args.json or args.out:
        rc = cl.emit(payload, args.out, summary)
        if rc is not None:
            return rc
    else:
        for f in invalid:
            print(f"invalid  {f['file']}:{f['line']}  tag={f['tag']!r}  {f['text']}")
        for f in misc:
            print(f"misc     {f['file']}:{f['line']}  {f['text']}")
        print(summary)

    return 1 if (invalid or misc) else 0


if __name__ == "__main__":
    sys.exit(main())
