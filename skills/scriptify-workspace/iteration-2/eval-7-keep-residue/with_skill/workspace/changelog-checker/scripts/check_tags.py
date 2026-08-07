#!/usr/bin/env python3
"""
check_tags.py - Check changelog category tags against the allowed list and
collect the Misc entries for re-triage.

Allowed tags: Added, Fixed, Changed, Removed, Misc. Anything else lands under
"invalid". Every Misc entry lands under "misc" with its text, because whether
a Misc entry really belongs under another category is a judgment call this
script does not make.

USAGE
    python3 scripts/check_tags.py <changelogs-dir> --json [--out FILE]

EXIT CODES
    0  No invalid tags and no Misc entries.
    1  Findings (JSON on stdout under "invalid" and "misc").
    2  Usage error, or the directory is missing/unreadable.
"""

import argparse
import json
import sys
from pathlib import Path

import _changelog as cl


def check(dirpath):
    invalid, misc = [], []
    for record in cl.parse_dir(dirpath):
        for entry in record["entries"]:
            cat = entry["category"]
            if cat not in cl.KNOWN_CATEGORIES:
                invalid.append({"file": entry["file"], "tag": cat,
                                "text": entry["text"]})
            elif cat == "Misc":
                misc.append({"file": entry["file"], "text": entry["text"]})
    return invalid, misc


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    p.add_argument("changelogs_dir", help="folder holding the changelog .md files")
    p.add_argument("--json", action="store_true",
                   help="emit findings as JSON (default, kept for explicitness)")
    p.add_argument("--out", help="write JSON here; print a summary to stdout")
    args = p.parse_args(argv)

    try:
        invalid, misc = check(args.changelogs_dir)
    except NotADirectoryError as e:
        cl.fail(str(e), 2)
    except OSError as e:
        cl.fail(f"cannot read {args.changelogs_dir}: {e}", 2)

    report = {"changelogs_dir": args.changelogs_dir,
              "allowed": cl.KNOWN_CATEGORIES,
              "invalid": invalid, "misc": misc}
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        try:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(text + "\n", encoding="utf-8")
        except OSError as e:
            cl.fail(f"cannot write {args.out}: {e}", 2)
        print(f"{len(invalid)} invalid tags, {len(misc)} Misc entries -> {args.out}")
    else:
        print(text)

    if invalid or misc:
        print(f"{len(invalid)} invalid tag(s), {len(misc)} Misc entry(ies)",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
