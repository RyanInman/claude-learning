#!/usr/bin/env python3
"""Step 6 (mechanical half): validate category tags and collect the Misc entries.

Reports any category outside Added/Fixed/Changed/Removed/Misc, and lists every
Misc-tagged entry so Claude can judge whether it belongs elsewhere. Judging the
re-home target is NOT done here.

Exit code 0 when all tags are in the allowed list, 1 when any tag is unknown.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from changelog_lib import (  # noqa: E402
    ALLOWED_CATEGORIES,
    add_dir_arg,
    add_json_arg,
    load_dir,
)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    add_dir_arg(p)
    add_json_arg(p)
    args = p.parse_args(argv)

    logs = load_dir(args.changelog_dir)
    unknown = []
    misc = []
    for c in logs:
        for e in c.entries:
            rec = {
                "file": c.name,
                "line": e.line_no,
                "category": e.category,
                "entry": e.text,
            }
            if e.category not in ALLOWED_CATEGORIES:
                unknown.append(rec)
            elif e.category == "Misc":
                misc.append(rec)

    if args.json:
        print(
            json.dumps(
                {
                    "allowed": ALLOWED_CATEGORIES,
                    "unknown_categories": unknown,
                    "misc_entries": misc,
                },
                indent=2,
            )
        )
    else:
        for r in unknown:
            print(f"FAIL {r['file']}:{r['line']} unknown category {r['category']!r}: {r['entry']}")
        for r in misc:
            print(f"MISC {r['file']}:{r['line']} {r['entry']}")
        print(f"{len(unknown)} unknown tag(s), {len(misc)} Misc entry(ies) needing judgment")
    return 1 if unknown else 0


if __name__ == "__main__":
    raise SystemExit(main())
