#!/usr/bin/env python3
"""
count_entries.py - Count changelog entries per category, per file and in
total across files.

Categories counted: Added, Fixed, Changed, Removed, Misc. An entry filed
under any other heading lands in "uncategorized" and is reported separately,
so the totals stay honest. check_tags.py is what names the offending tags.

USAGE
    python3 scripts/count_entries.py changelogs/ [--json] [--out FILE]

STDOUT
    --json: {"per_file": [{file, version, date, counts, total}],
    "totals": {category: n}, "total_entries": N, "uncategorized": N}

EXIT CODES
    0  One or more entries counted.
    1  No entries found in any file.
    2  Usage error, or the directory is missing or unreadable.
"""

import argparse
import sys

import changelog_lib as cl


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Count changelog entries per category and in total.")
    parser.add_argument("directory", help="Folder holding the changelog .md files")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--out", help="Write JSON to FILE, summary to stdout")
    args = parser.parse_args(argv)

    try:
        parsed = cl.parse_dir(args.directory)
    except cl.ChangelogError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    totals = {c: 0 for c in cl.ALLOWED_CATEGORIES}
    per_file = []
    uncategorized = 0
    for p in parsed:
        counts = cl.counts_for(p)
        for category, n in counts.items():
            totals[category] += n
        uncategorized += sum(1 for e in p["entries"]
                             if e["category"] not in totals)
        per_file.append({"file": p["file"], "version": p["version"],
                         "date": p["date"], "counts": counts,
                         "total": sum(counts.values())})

    total_entries = sum(totals.values())
    payload = {"per_file": per_file, "totals": totals,
               "total_entries": total_entries, "uncategorized": uncategorized}
    summary = f"{total_entries} entries across {len(parsed)} files"

    if args.json or args.out:
        rc = cl.emit(payload, args.out, summary)
        if rc is not None:
            return rc
    else:
        for f in per_file:
            print(f"{f['version'] or 'unknown':<10} {f['file']:<14} {f['counts']}")
        print(f"totals {totals}")
        print(summary)

    if total_entries == 0:
        print(f"warning: no entries found in {args.directory}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
