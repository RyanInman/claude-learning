#!/usr/bin/env python3
"""
<name>.py - <one line: what it checks or transforms>

READS   <paths the script opens>
WRITES  <paths the script creates or changes, or "nothing">

USAGE
    python3 scripts/<name>.py <data-dir> [--out FILE]

EXIT CODES
    0  Clean.
    1  Findings (JSON on stdout).
    2  Usage error or unreadable input.
    3  Unexpected failure.
"""

import argparse
import json
import sys
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("data_dir", help="Folder to check")
    parser.add_argument("--out", help="Write full JSON here; print a summary to stdout")
    args = parser.parse_args(argv)

    root = Path(args.data_dir)
    if not root.is_dir():
        print(f"error: not a directory: {args.data_dir}", file=sys.stderr)
        return 2

    findings = []  # {"file": ..., "line": ..., "code": ..., "message": ...}
    result = {"findings": findings}
    payload = json.dumps(result, indent=2)
    if args.out:
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
        print(f"{len(findings)} findings -> {args.out}")
    else:
        print(payload)
    return 1 if findings else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # predictable errors already returned 2 above
        print(f"unexpected failure: {e}", file=sys.stderr)
        sys.exit(3)
