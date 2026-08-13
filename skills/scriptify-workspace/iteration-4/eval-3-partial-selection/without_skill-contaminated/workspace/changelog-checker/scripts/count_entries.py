#!/usr/bin/env python3
"""Count changelog entries per category for each file, plus totals across files."""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

CATEGORIES = ["Added", "Fixed", "Changed", "Removed"]
VERSION_RE = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")
CATEGORY_RE = re.compile(r"^###\s+(.+?)\s*$")
ENTRY_RE = re.compile(r"^\s*[-*]\s+\S")


def sort_key(path):
    """Sort by numeric semver from the filename; unparseable names sort last by name."""
    m = VERSION_RE.search(path.stem)
    if m:
        return (0, tuple(int(g) for g in m.groups()), path.name)
    return (1, (0, 0, 0), path.name)


def count_file(path):
    """Return a Counter of category -> entry count for one changelog file."""
    counts = Counter()
    current = None
    for line in path.read_text(encoding="utf-8").splitlines():
        heading = CATEGORY_RE.match(line)
        if heading:
            current = heading.group(1)
            counts.setdefault(current, 0)
            continue
        if current and ENTRY_RE.match(line):
            counts[current] += 1
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("changelog_dir", help="directory holding the changelog .md files")
    args = parser.parse_args()

    directory = Path(args.changelog_dir)
    if not directory.is_dir():
        print(f"error: not a directory: {directory}", file=sys.stderr)
        return 2

    files = sorted(directory.glob("*.md"), key=sort_key)
    if not files:
        print(f"error: no .md files in {directory}", file=sys.stderr)
        return 1

    totals = Counter()
    per_file = []
    for path in files:
        counts = count_file(path)
        totals.update(counts)
        per_file.append((path.name, counts))

    extra = [c for c in sorted(totals) if c not in CATEGORIES]
    columns = CATEGORIES + extra
    width = max([len(name) for name, _ in per_file] + [len("file")])
    header = "  ".join([f"{'file':<{width}}"] + [f"{c:>8}" for c in columns] + [f"{'total':>8}"])
    print(header)
    print("-" * len(header))
    for name, counts in per_file:
        row = [f"{name:<{width}}"] + [f"{counts.get(c, 0):>8}" for c in columns]
        row.append(f"{sum(counts.values()):>8}")
        print("  ".join(row))
    print("-" * len(header))
    grand = ["  ".join([f"{'ALL':<{width}}"] + [f"{totals.get(c, 0):>8}" for c in columns] + [f"{sum(totals.values()):>8}"])]
    print(grand[0])
    if extra:
        print(f"\nnon-standard categories seen: {', '.join(extra)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
