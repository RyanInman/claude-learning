#!/usr/bin/env python3
"""Step 1: list every changelog .md file sorted by version, with a total count."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from changelog_lib import add_dir_arg, add_json_arg, load_dir  # noqa: E402


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    add_dir_arg(p)
    add_json_arg(p)
    args = p.parse_args(argv)

    logs = load_dir(args.changelog_dir)
    if args.json:
        print(
            json.dumps(
                {
                    "count": len(logs),
                    "files": [
                        {
                            "file": c.name,
                            "version": c.version,
                            "date": c.date,
                            "header_ok": c.header_ok,
                        }
                        for c in logs
                    ],
                },
                indent=2,
            )
        )
    else:
        for c in logs:
            print(f"{c.version or '(unknown)':10} {c.name}")
        print(f"total: {len(logs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
