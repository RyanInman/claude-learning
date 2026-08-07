#!/usr/bin/env python3
"""Step 2: check every changelog starts with '## vX.Y.Z — YYYY-MM-DD'.

Exit code 0 when every file is well formed, 1 when any file fails.
"""

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
    bad = [c for c in logs if not c.header_ok]

    if args.json:
        print(
            json.dumps(
                {
                    "checked": len(logs),
                    "violations": [
                        {"file": c.name, "problem": c.header_problem} for c in bad
                    ],
                },
                indent=2,
            )
        )
    else:
        for c in bad:
            print(f"FAIL {c.name}: {c.header_problem}")
        print(f"checked {len(logs)} file(s), {len(bad)} bad header(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
