#!/usr/bin/env python3
"""Step 6 (mechanical half): validate category tags and collect `Misc` entries.

Tags outside Added/Fixed/Changed/Removed/Misc land in `invalid`. Every entry
under `Misc` lands in `misc` for Claude to judge a better home for.

Usage: python3 scripts/check_tags.py CHANGELOG_DIR [--json]
Exit 0 when all tags are known and no `Misc` entry exists, 1 otherwise,
2 on a usage error.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import changelog_lib as lib  # noqa: E402


def main(argv):
    directory = lib.require_dir(argv)
    invalid = []
    misc = []

    for parsed in lib.parse_dir(directory):
        for section in parsed["sections"]:
            tag = section["category"]
            if tag not in lib.ALLOWED_TAGS:
                for entry in section["entries"] or [None]:
                    invalid.append({
                        "file": parsed["name"],
                        "tag": tag,
                        "entry": entry,
                    })
            elif tag == "Misc":
                for entry in section["entries"]:
                    misc.append({
                        "file": parsed["name"],
                        "entry": entry,
                        "candidates": lib.KNOWN_CATEGORIES,
                    })

    result = {
        "dir": os.path.abspath(directory),
        "allowed": lib.ALLOWED_TAGS,
        "invalid": invalid,
        "misc": misc,
    }

    if lib.wants_json(argv):
        print(json.dumps(result, indent=2))
    else:
        for row in invalid:
            print("invalid\t%s\t%s\t%s" % (row["file"], row["tag"], row["entry"]))
        for row in misc:
            print("misc\t%s\t%s" % (row["file"], row["entry"]))
        if not invalid and not misc:
            print("all tags valid, no Misc entries")

    return 1 if (invalid or misc) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
