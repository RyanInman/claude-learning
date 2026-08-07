#!/usr/bin/env python3
"""Count changelog entries per category, per file, plus grand totals.

Usage:
    python3 scripts/count_entries.py [CHANGELOG_DIR] [--json]

Categories counted: Added, Fixed, Changed, Removed. Any other `###` section is
counted under "other" so nothing is silently dropped. An entry is a top-level
list item ("- " or "* ") under a category heading.
"""

import argparse
import json
import re
import sys
from pathlib import Path

CATEGORIES = ["Added", "Fixed", "Changed", "Removed"]
HEADING_RE = re.compile(r"^###\s+(.+?)\s*$")
ITEM_RE = re.compile(r"^[-*]\s+\S")
VERSION_RE = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")


def version_key(path: Path):
    m = VERSION_RE.search(path.stem)
    if not m:
        return (1, (0, 0, 0), path.name)
    return (0, tuple(int(g) for g in m.groups()), path.name)


def count_file(path: Path):
    counts = {c: 0 for c in CATEGORIES}
    counts["other"] = 0
    other_sections = {}
    current = None
    for line in path.read_text(encoding="utf-8").splitlines():
        h = HEADING_RE.match(line)
        if h:
            current = h.group(1)
            if current not in CATEGORIES:
                other_sections.setdefault(current, 0)
            continue
        if current and ITEM_RE.match(line.strip()) and line.startswith(("-", "*")):
            if current in CATEGORIES:
                counts[current] += 1
            else:
                counts["other"] += 1
                other_sections[current] = other_sections.get(current, 0) + 1
    return counts, other_sections


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="changelogs")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"error: not a directory: {directory}", file=sys.stderr)
        return 1

    per_file = []
    totals = {c: 0 for c in CATEGORIES}
    totals["other"] = 0
    for path in sorted(directory.glob("*.md"), key=version_key):
        counts, other_sections = count_file(path)
        for k, v in counts.items():
            totals[k] += v
        per_file.append(
            {
                "file": path.name,
                "counts": counts,
                "other_sections": other_sections,
            }
        )

    result = {"per_file": per_file, "totals": totals}

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        header = ["file"] + CATEGORIES + ["other"]
        print(" | ".join(header))
        for row in per_file:
            print(
                " | ".join(
                    [row["file"]]
                    + [str(row["counts"][c]) for c in CATEGORIES]
                    + [str(row["counts"]["other"])]
                )
            )
        print(
            " | ".join(
                ["TOTAL"] + [str(totals[c]) for c in CATEGORIES] + [str(totals["other"])]
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
