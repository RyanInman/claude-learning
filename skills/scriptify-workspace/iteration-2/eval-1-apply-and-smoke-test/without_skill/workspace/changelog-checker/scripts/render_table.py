#!/usr/bin/env python3
"""Step 5: render the markdown summary table (version, date, per-category counts).

Rows are sorted by version descending.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from changelog_lib import CORE_CATEGORIES, add_dir_arg, load_dir  # noqa: E402


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    add_dir_arg(p)
    p.add_argument(
        "--include-misc",
        action="store_true",
        help="Add a Misc column alongside the four core categories.",
    )
    args = p.parse_args(argv)

    cats = list(CORE_CATEGORIES) + (["Misc"] if args.include_misc else [])
    logs = sorted(load_dir(args.changelog_dir), key=lambda c: c.version_key, reverse=True)

    header = ["Version", "Date"] + cats + ["Total"]
    print("| " + " | ".join(header) + " |")
    print("| " + " | ".join(["---"] * len(header)) + " |")
    for c in logs:
        counts = c.counts()
        row = [c.version or "(unknown)", c.date or "(missing)"]
        row += [str(counts.get(k, 0)) for k in cats]
        row.append(str(len(c.entries)))
        print("| " + " | ".join(row) + " |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
