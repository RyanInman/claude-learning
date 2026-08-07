#!/usr/bin/env python3
"""
parse_changelogs.py - Inventory and tally a changelogs folder.

Lists every .md file sorted by version, records each file's version and date,
counts entries per category per file, and totals them across files. With
--entries it emits instead a flat list of every entry, for judging the entries
themselves.

USAGE
    python3 scripts/parse_changelogs.py <changelogs-dir> --json [--out FILE]
    python3 scripts/parse_changelogs.py <changelogs-dir> --entries [--out FILE]

    --json      full parse: {file_count, files[], totals}
    --entries   flat list: {entry_count, entries[{file, category, text}]}
    --out FILE  write the JSON to FILE, print a one-line summary to stdout

EXIT CODES
    0  Parsed.
    1  No .md changelog files in the directory (stdout: no_changelog_files).
    2  Usage error, or the directory is missing/unreadable.
"""

import argparse
import json
import sys
from pathlib import Path

import _changelog as cl


def build_report(records):
    totals = {c: 0 for c in cl.KNOWN_CATEGORIES}
    for r in records:
        for cat, n in r["counts"].items():
            totals[cat] += n
    return {"file_count": len(records),
            "files": [{"file": r["file"], "version": r["version"],
                       "date": r["date"], "counts": r["counts"],
                       "entries": r["entries"]} for r in records],
            "totals": totals}


def build_entries(records):
    entries = [e for r in records for e in r["entries"]]
    return {"entry_count": len(entries), "entries": entries}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    p.add_argument("changelogs_dir", help="folder holding the changelog .md files")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--json", action="store_true",
                      help="full parse with per-file counts and totals (default)")
    mode.add_argument("--entries", action="store_true",
                      help="flat list of every entry instead")
    p.add_argument("--out", help="write JSON here; print a summary to stdout")
    args = p.parse_args(argv)

    try:
        records = cl.parse_dir(args.changelogs_dir)
    except NotADirectoryError as e:
        cl.fail(str(e), 2)
    except OSError as e:
        cl.fail(f"cannot read {args.changelogs_dir}: {e}", 2)

    if not records:
        print(json.dumps({"error": "no_changelog_files",
                          "changelogs_dir": args.changelogs_dir}, indent=2))
        print(f"no .md changelog files in {args.changelogs_dir}", file=sys.stderr)
        return 1

    report = build_entries(records) if args.entries else build_report(records)
    report["changelogs_dir"] = args.changelogs_dir
    text = json.dumps(report, indent=2, ensure_ascii=False)

    if args.out:
        try:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(text + "\n", encoding="utf-8")
        except OSError as e:
            cl.fail(f"cannot write {args.out}: {e}", 2)
        if args.entries:
            print(f"{report['entry_count']} entries -> {args.out}")
        else:
            print(f"{report['file_count']} files, "
                  f"{sum(report['totals'].values())} entries -> {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
