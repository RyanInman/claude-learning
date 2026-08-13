#!/usr/bin/env python3
"""Scan a release-notes `notes/` directory and render the grouped notes.

Prints a FACTS block (file count, malformed files, per-type counts) followed by
the rendered markdown list, grouped by type and sorted by PR number ascending.
Malformed files are excluded from the rendered list and reported by name.
"""
import re
import sys
from pathlib import Path

HEADER = re.compile(r"^PR #(\d+):\s*(.+?)\s*$")
TYPE = re.compile(r"^type:\s*(\S+)\s*$")
LABELS = {"feat": "Features", "fix": "Fixes", "chore": "Chores"}
ORDER = ["feat", "fix", "chore"]


def parse(path):
    """Return (pr_number, title, type) or None when the file is malformed."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return None
    head = HEADER.match(lines[0])
    if not head:
        return None
    entry_type = None
    for line in lines[1:]:
        found = TYPE.match(line)
        if found:
            entry_type = found.group(1)
            break
    if entry_type is None:
        return None
    return int(head.group(1)), head.group(2), entry_type


def main():
    default = Path(__file__).resolve().parent.parent / "notes"
    notes_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else default
    if not notes_dir.is_dir():
        print(f"error: notes directory not found: {notes_dir}", file=sys.stderr)
        return 1

    files = sorted(notes_dir.glob("*.md"), key=lambda p: p.name)
    entries, malformed = [], []
    for path in files:
        parsed = parse(path)
        if parsed is None:
            malformed.append(path.name)
        else:
            entries.append(parsed)

    groups = {}
    for number, title, entry_type in entries:
        groups.setdefault(entry_type, []).append((number, title))
    types = [t for t in ORDER if t in groups] + sorted(t for t in groups if t not in ORDER)

    print(f"FILES: {len(files)}")
    print(f"VALID: {len(entries)}")
    print("MALFORMED: " + (", ".join(malformed) if malformed else "none"))
    print("COUNTS: " + (" ".join(f"{t}={len(groups[t])}" for t in types) if types else "none"))
    print()
    print("--- NOTES ---")
    for entry_type in types:
        print(f"### {LABELS.get(entry_type, entry_type)}")
        for number, title in sorted(groups[entry_type]):
            print(f"- #{number} {title}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
