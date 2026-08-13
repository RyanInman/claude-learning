#!/usr/bin/env python3
"""
sample_target_data.py - Digest the data a target skill's steps operate on, so
the classifier sees the real inputs in one call instead of N reads.

A proposed interface written against unopened data invents its own fixture: it
misses the malformed file already sitting in the target, and the contract step
then derives expectations that never exercise it. Reading every data file by
hand costs one tool call each; this costs one.

WHAT IT REPORTS
Per data directory -- the target root when it holds data files beside SKILL.md,
plus any folder under it that is not scripts/, references/, assets/, evals/,
tests/, or a dot-folder:
  files        name, bytes, lines, first non-empty line
  shape        the first-line shape shared by the majority of files
  outliers     files whose first line does not match that shape -- these are
               the planted defects a step exists to catch, and the fixtures the
               generated script must fail on

Shape is computed by masking digits, so "## v1.2.0 - 2026-01-01" and
"## v1.10.0 - 2026-02-01" share a shape while "### Added" does not.

USAGE
    python3 scripts/sample_target_data.py <target-dir> [--json] [--out FILE]
             [--max-files N]   default 40 per directory
             [--max-line N]    default 120 chars of each first line

EXIT CODES
    0  Digest produced.
    1  No data directories found (the target ships no data of its own).
    2  Usage error, or target is not a directory.
"""

import argparse
import json
import re
import sys
from pathlib import Path

SKIP_DIRS = {"scripts", "references", "assets", "evals", "tests", "fixtures"}
DIGITS_RE = re.compile(r"\d+")


def _shape(line):
    """The structural prefix of a first line: first two tokens, digits masked.

    Whole-line matching fails because sibling files differ in their titles --
    "PR #101: Add widget batch endpoint" and "PR #109: Bump lockfile" are the
    same shape and must compare equal, while "Merged 104: Fix pagination" is
    the outlier a step exists to catch.
    """
    return " ".join(DIGITS_RE.sub("#", line.strip()).split()[:2])


def _first_line(path, limit):
    try:
        with path.open(encoding="utf-8", errors="replace") as fh:
            for raw in fh:
                if raw.strip():
                    return raw.strip()[:limit]
    except OSError:
        return ""
    return ""


def _count_lines(path):
    try:
        with path.open(encoding="utf-8", errors="replace") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


ROOT_NON_DATA = {"SKILL.md", "README.md", "LICENSE", ".DS_Store"}


def data_dirs(target):
    """Directories holding the target's own data, nearest the root first.

    The target root counts when it holds data files beside SKILL.md -- a small
    skill often ships one `topics.txt` at the top level rather than a folder,
    and walking only subdirectories reported such a target as shipping no data
    at all.
    """
    out = []
    if any(f.is_file() and f.name not in ROOT_NON_DATA and not f.name.startswith(".")
           for f in target.iterdir()):
        out.append(target)
    for d in sorted(target.rglob("*")):
        if not d.is_dir():
            continue
        parts = set(d.relative_to(target).parts)
        if parts & SKIP_DIRS or any(p.startswith(".") for p in parts):
            continue
        if any(f.is_file() for f in d.iterdir()):
            out.append(d)
    return out


def digest(target, max_files, max_line):
    report = {"target": str(target), "directories": []}
    for d in data_dirs(target):
        files = sorted(f for f in d.iterdir() if f.is_file()
                       and not (d == target and (f.name in ROOT_NON_DATA
                                                 or f.name.startswith("."))))
        entry = {"path": str(d.relative_to(target)) or ".", "file_count": len(files),
                 "files": [], "majority_shape": None, "outliers": []}
        shapes = {}
        for f in files[:max_files]:
            first = _first_line(f, max_line)
            rec = {"name": f.name, "bytes": f.stat().st_size,
                   "lines": _count_lines(f), "first_line": first}
            entry["files"].append(rec)
            shapes.setdefault(_shape(first), []).append(f.name)
        if shapes:
            top = max(shapes, key=lambda s: len(shapes[s]))
            # A shape only counts as "the majority" if more than one file shares
            # it; otherwise every file is its own shape and nothing is an outlier.
            if len(shapes[top]) > 1:
                entry["majority_shape"] = top
                entry["outliers"] = sorted(n for s, names in shapes.items()
                                           if s != top for n in names)
        if len(files) > max_files:
            entry["truncated"] = len(files) - max_files
        report["directories"].append(entry)
    return report


def render(report):
    lines = [f"data under {report['target']}"]
    if not report["directories"]:
        lines.append("  (none -- the target ships no data of its own)")
    for d in report["directories"]:
        lines.append(f"\n  {d['path']}/  {d['file_count']} files")
        for f in d["files"]:
            lines.append(f"    {f['name']:24} {f['lines']:>4}L  {f['first_line'][:60]}")
        if d["majority_shape"]:
            lines.append(f"    shape: {d['majority_shape'][:60]}")
        if d["outliers"]:
            lines.append(f"    OUTLIERS (a step exists to catch these): "
                         f"{', '.join(d['outliers'])}")
        if d.get("truncated"):
            lines.append(f"    ... {d['truncated']} more files not sampled")
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Digest the data a target skill's steps operate on.")
    p.add_argument("target", help="Target skill folder")
    p.add_argument("--json", action="store_true", help="Emit JSON, not a table")
    p.add_argument("--out", help="Write the JSON to FILE and keep stdout compact")
    p.add_argument("--max-files", type=int, default=40,
                   help="Files sampled per directory (default 40)")
    p.add_argument("--max-line", type=int, default=120,
                   help="Characters kept from each first line (default 120)")
    args = p.parse_args(argv)

    target = Path(args.target)
    if not target.is_dir():
        print(f"error: not a directory: {args.target}", file=sys.stderr)
        return 2

    report = digest(target, args.max_files, args.max_line)

    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=1), encoding="utf-8")
        n = sum(d["file_count"] for d in report["directories"])
        outliers = sum(len(d["outliers"]) for d in report["directories"])
        print(f"{len(report['directories'])} data dirs, {n} files, "
              f"{outliers} outliers -> {args.out}")
    else:
        print(json.dumps(report, indent=1) if args.json else render(report))

    return 0 if report["directories"] else 1


if __name__ == "__main__":
    sys.exit(main())
