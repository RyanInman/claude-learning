#!/usr/bin/env python3
"""Scan notes/, validate headers, extract PR entries, and emit JSON.

Covers steps 1-3 of the release-notes workflow: enumerate, validate, group.
Reads nothing but the notes directory; writes JSON to stdout.
"""

import argparse
import json
import re
import sys
from pathlib import Path

HEADER_RE = re.compile(r"^PR #(\d+):\s*(.+?)\s*$")
TYPE_RE = re.compile(r"^type:\s*(\S+)\s*$")

TYPE_ORDER = ["feat", "fix", "chore"]


def parse_note(path: Path) -> tuple[dict | None, dict | None]:
    """Return (entry, problem). Exactly one is non-None."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return None, {"file": path.name, "reason": f"unreadable: {exc}"}

    if not lines:
        return None, {"file": path.name, "reason": "file is empty"}

    header = HEADER_RE.match(lines[0])
    if not header:
        return None, {
            "file": path.name,
            "reason": "first line is not 'PR #<number>: <title>'",
            "first_line": lines[0],
        }

    note_type = None
    for line in lines[1:]:
        match = TYPE_RE.match(line)
        if match:
            note_type = match.group(1)
            break

    if note_type is None:
        return None, {"file": path.name, "reason": "no 'type:' line found"}

    return {
        "file": path.name,
        "number": int(header.group(1)),
        "title": header.group(2),
        "type": note_type,
    }, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "notes_dir",
        nargs="?",
        default=str(Path(__file__).resolve().parent.parent / "notes"),
        help="directory of note markdown files (default: ../notes)",
    )
    args = parser.parse_args()

    notes_dir = Path(args.notes_dir)
    if not notes_dir.is_dir():
        print(f"error: not a directory: {notes_dir}", file=sys.stderr)
        return 2

    files = sorted(notes_dir.glob("*.md"), key=lambda p: p.name)

    entries: list[dict] = []
    invalid: list[dict] = []
    for path in files:
        entry, problem = parse_note(path)
        if entry is not None:
            entries.append(entry)
        else:
            invalid.append(problem)

    by_type: dict[str, int] = {}
    for entry in entries:
        by_type[entry["type"]] = by_type.get(entry["type"], 0) + 1

    ordered_types = [t for t in TYPE_ORDER if t in by_type]
    ordered_types += sorted(t for t in by_type if t not in TYPE_ORDER)

    payload = {
        "notes_dir": str(notes_dir),
        "file_count": len(files),
        "files": [p.name for p in files],
        "entries": sorted(entries, key=lambda e: e["number"]),
        "invalid": invalid,
        "by_type": {t: by_type[t] for t in ordered_types},
        "unknown_types": sorted(t for t in by_type if t not in TYPE_ORDER),
    }
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
