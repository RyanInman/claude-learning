#!/usr/bin/env python3
"""check.py - Lint release-note structure: every note needs a title heading.

USAGE
    python3 scripts/check.py <notes-dir> [--json]

EXIT CODES
    0  Clean.
    1  Findings reported.
    2  Usage error / directory missing.
"""
import argparse
import json
import sys
from pathlib import Path


def main(argv=None):
    p = argparse.ArgumentParser(description="Lint release-note structure.")
    p.add_argument("notes_dir")
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    d = Path(a.notes_dir)
    if not d.is_dir():
        print(f"error: not a directory: {d}", file=sys.stderr)
        return 2
    findings = [{"file": f.name, "problem": "missing title heading"}
                for f in sorted(d.glob("*.md"))
                if not f.read_text(encoding="utf-8").startswith("# ")]
    if a.json:
        print(json.dumps(findings))
    else:
        print("\n".join(f"{x['file']}: {x['problem']}" for x in findings) or "clean")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
