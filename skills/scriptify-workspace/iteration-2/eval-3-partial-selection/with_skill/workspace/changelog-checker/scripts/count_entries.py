#!/usr/bin/env python3
"""
count_entries.py - Count changelog entries per category, per file, and in total.

An entry is a `- ` bullet under a `### <Category>` heading. The four standard
categories (Added, Fixed, Changed, Removed) always appear in the counts, at
zero when absent; any other category found is reported after them, sorted by
name, so a stray tag stays visible instead of vanishing into the totals.

USAGE
    python3 scripts/count_entries.py <changelogs-dir> [--json] [--out FILE]

OUTPUT (stdout, JSON)
    {"dir": "...",
     "per_file": [{"path", "name", "version", "date", "counts": {...}}],
     "totals": {"Added": N, "Fixed": N, "Changed": N, "Removed": N, ...}}
    per_file is version-sorted ascending; unversioned files sort last.

EXIT CODES
    0  At least one entry counted.
    1  No entries found (every total zero, or no .md files).
    2  Usage error / directory missing or unreadable.
"""

import argparse
import json
import re
import sys
from pathlib import Path

STANDARD = ["Added", "Fixed", "Changed", "Removed"]
FILE_VERSION_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
HEADING_RE = re.compile(r"^##\s+v(\d+\.\d+\.\d+)\s*[—-]\s*(\d{4}-\d{2}-\d{2})")
CATEGORY_RE = re.compile(r"^###\s+(.+?)\s*$")
BULLET_RE = re.compile(r"^\s*-\s+\S")


def parse_file(path):
    version = None
    date = None
    m = FILE_VERSION_RE.match(path.stem)
    if m:
        version = ".".join(m.groups())
    counts = {}
    category = None
    for line in path.read_text(encoding="utf-8").splitlines():
        h = HEADING_RE.match(line)
        if h:
            version = version or h.group(1)
            date = date or h.group(2)
            continue
        c = CATEGORY_RE.match(line)
        if c:
            category = c.group(1)
            counts.setdefault(category, 0)
            continue
        if category and BULLET_RE.match(line):
            counts[category] += 1
    return {"path": path.as_posix(), "name": path.name,
            "version": version, "date": date, "counts": counts}


def ordered(counts):
    out = {k: counts.get(k, 0) for k in STANDARD}
    for k in sorted(counts):
        if k not in out:
            out[k] = counts[k]
    return out


def sort_key(rec):
    if rec["version"] is None:
        return (1, (), rec["name"])
    return (0, tuple(int(p) for p in rec["version"].split(".")), rec["name"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("changelogs_dir", help="folder holding the changelog .md files")
    ap.add_argument("--json", action="store_true",
                    help="accepted for interface stability; output is always JSON")
    ap.add_argument("--out", help="write the JSON to FILE; print a summary to stdout")
    args = ap.parse_args(argv)

    root = Path(args.changelogs_dir)
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    per_file = []
    totals = {}
    for p in sorted(root.glob("*.md")):
        try:
            rec = parse_file(p)
        except OSError as e:
            print(f"cannot read {p}: {e}", file=sys.stderr)
            return 2
        for k, v in rec["counts"].items():
            totals[k] = totals.get(k, 0) + v
        rec["counts"] = ordered(rec["counts"])
        per_file.append(rec)
    per_file.sort(key=sort_key)

    data = {"dir": root.as_posix(), "per_file": per_file, "totals": ordered(totals)}
    payload = json.dumps(data)

    if args.out:
        try:
            Path(args.out).write_text(payload + "\n", encoding="utf-8")
        except OSError as e:
            print(f"cannot write {args.out}: {e}", file=sys.stderr)
            return 2
        print(f"{len(per_file)} files, {sum(data['totals'].values())} entries -> {args.out}")
    else:
        print(payload)

    if sum(data["totals"].values()) == 0:
        print(f"no changelog entries found in {root}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
