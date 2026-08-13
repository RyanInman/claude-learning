#!/usr/bin/env python3
"""Inventory notes/*.md and render the changelog body grouped by type.

Usage: collect_notes.py [notes_dir]
Prints one JSON object to stdout. Standard library only.
"""
import json
import re
import sys
from pathlib import Path

HEADER = re.compile(r"^PR #(\d+):\s*(.*)$")
TYPE = re.compile(r"^type:\s*(\S+)\s*$", re.M)
ORDER = ["feat", "fix", "chore"]
LABELS = {"feat": "Features", "fix": "Fixes", "chore": "Chores"}


def render(entries):
    seen = [t for t in ORDER if any(e["type"] == t for e in entries)]
    extra = sorted({e["type"] for e in entries} - set(ORDER))
    lines = []
    for kind in seen + extra:
        lines.append(f"### {LABELS.get(kind, kind)}")
        for e in sorted((e for e in entries if e["type"] == kind), key=lambda e: e["pr"]):
            lines.append(f"- PR #{e['pr']}: {e['title']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n" if lines else ""


def main():
    notes_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "notes")
    if not notes_dir.is_dir():
        print(json.dumps({"error": f"no such directory: {notes_dir}"}))
        return 1
    files = sorted(notes_dir.glob("*.md"), key=lambda p: p.name)
    entries, malformed = [], []
    for path in files:
        lines = path.read_text(encoding="utf-8").splitlines()
        head = lines[0].strip() if lines else ""
        match = HEADER.match(head)
        if not match:
            malformed.append({"file": path.name,
                              "reason": "first line is not 'PR #<number>: <title>'",
                              "found": head})
            continue
        kind = TYPE.search("\n".join(lines))
        if not kind:
            malformed.append({"file": path.name, "reason": "no 'type:' field"})
            continue
        entries.append({"file": path.name, "pr": int(match.group(1)),
                        "title": match.group(2).strip(), "type": kind.group(1)})
    counts = {}
    for e in entries:
        counts[e["type"]] = counts.get(e["type"], 0) + 1
    print(json.dumps({
        "total_files": len(files),
        "parsed": len(entries),
        "counts": counts,
        "unknown_types": sorted(set(counts) - set(ORDER)),
        "malformed": malformed,
        "entries": sorted(entries, key=lambda e: e["pr"]),
        "markdown": render(entries),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
