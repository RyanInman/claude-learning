#!/usr/bin/env python3
"""Count changelog entries per category, per file and across all files.

Usage: count_categories.py [CHANGELOGS_DIR]

A category is an `### Name` heading. An entry is a top-level `- ` bullet under it.
Counts every category found, not only the four expected ones, so an unexpected
tag such as `Misc` shows up instead of being silently dropped.

Prints JSON: {"per_file": {file: {category: n}}, "totals": {category: n},
              "categories": [...], "grand_total": N}
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

CATEGORY_RE = re.compile(r"^###\s+(.+?)\s*$")
BULLET_RE = re.compile(r"^[-*]\s+\S")

VERSION_RE = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")


def sort_key(path: Path):
    m = VERSION_RE.search(path.stem)
    if m:
        return (0, tuple(int(g) for g in m.groups()), path.name)
    return (1, (0, 0, 0), path.name)


def count_file(path: Path) -> Counter:
    counts: Counter = Counter()
    current = None
    for line in path.read_text(encoding="utf-8").splitlines():
        heading = CATEGORY_RE.match(line)
        if heading:
            current = heading.group(1)
            counts.setdefault(current, 0)
            continue
        if current and BULLET_RE.match(line):
            counts[current] += 1
    return counts


def main() -> int:
    directory = Path(sys.argv[1] if len(sys.argv) > 1 else "changelogs")
    if not directory.is_dir():
        print(f"error: not a directory: {directory}", file=sys.stderr)
        return 1
    per_file = {}
    totals: Counter = Counter()
    for path in sorted(directory.glob("*.md"), key=sort_key):
        counts = count_file(path)
        per_file[path.name] = dict(counts)
        totals.update(counts)
    result = {
        "per_file": per_file,
        "totals": dict(totals),
        "categories": sorted(totals),
        "grand_total": sum(totals.values()),
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
