#!/usr/bin/env python3
"""Render final release notes markdown from collect_notes.py JSON + a summary.

Covers step 5 of the release-notes workflow: group by type, sort by PR number
ascending, emit markdown. The summary paragraph is authored by Claude (step 4)
and passed in; this script never invents prose.
"""

import argparse
import json
import sys
from pathlib import Path

TYPE_HEADINGS = {
    "feat": "Features",
    "fix": "Fixes",
    "chore": "Chores",
}


def read_source(value: str) -> str:
    if value == "-":
        return sys.stdin.read()
    return Path(value).read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data", required=True, help="collect_notes.py JSON file, or - for stdin"
    )
    parser.add_argument(
        "--summary", required=True, help="summary text file, or - for stdin"
    )
    parser.add_argument("--title", default="Release Notes", help="top-level heading")
    args = parser.parse_args()

    if args.data == "-" and args.summary == "-":
        print("error: only one of --data/--summary may read stdin", file=sys.stderr)
        return 2

    data = json.loads(read_source(args.data))
    summary = read_source(args.summary).strip()

    if data.get("invalid"):
        names = ", ".join(item["file"] for item in data["invalid"])
        print(
            f"error: {len(data['invalid'])} malformed note(s): {names}. "
            "Fix them or rerun collect_notes.py before rendering.",
            file=sys.stderr,
        )
        return 1

    lines = [f"# {args.title}", ""]
    if summary:
        lines += [summary, ""]

    for note_type in data["by_type"]:
        heading = TYPE_HEADINGS.get(note_type, note_type.capitalize())
        lines.append(f"## {heading}")
        lines.append("")
        group = [e for e in data["entries"] if e["type"] == note_type]
        for entry in sorted(group, key=lambda e: e["number"]):
            lines.append(f"- #{entry['number']}: {entry['title']}")
        lines.append("")

    sys.stdout.write("\n".join(lines).rstrip() + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
