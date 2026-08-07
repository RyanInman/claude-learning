#!/usr/bin/env python3
"""Step 3: count entries per category per file, plus totals across files."""

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
    per_file = []
    totals = {c: 0 for c in ALLOWED_CATEGORIES}
    for c in logs:
        counts = c.counts()
        for k, v in counts.items():
            totals[k] = totals.get(k, 0) + v
        per_file.append(
            {
                "file": c.name,
                "version": c.version,
                "date": c.date,
                "counts": counts,
                "total": len(c.entries),
            }
        )

    if args.json:
        print(
            json.dumps(
                {
                    "per_file": per_file,
                    "totals": totals,
                    "grand_total": sum(totals.values()),
                },
                indent=2,
            )
        )
    else:
        for row in per_file:
            detail = " ".join(f"{k}={v}" for k, v in row["counts"].items() if v)
            print(f"{row['version'] or '(unknown)':10} {row['file']:14} {detail}")
        print("totals: " + " ".join(f"{k}={v}" for k, v in totals.items()))
        print(f"grand total: {sum(totals.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
