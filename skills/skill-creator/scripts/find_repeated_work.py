#!/usr/bin/env python3
"""Find files repeated across test-case runs in an eval iteration directory.

Enumerates every file under each run directory (<eval>/<configuration>/) of an
iteration and reports basenames that appear in two or more runs. A helper
script independently rewritten by several runs (e.g. create_docx.py) is a
strong signal the skill should bundle it once in scripts/. This tool only
enumerates; judging whether a repeat is bundle-worthy stays with the agent.

Standard per-run harness files (timing.json, grading.json, eval_metadata.json,
feedback.json) appear in every run by design and are excluded.

USAGE
    python3 scripts/find_repeated_work.py <workspace>/iteration-N [--json] [--out FILE]

    --json      emit full JSON to stdout (default: human-readable summary)
    --out FILE  write full JSON to FILE, print summary to stdout

EXIT CODES
    0  no repeated files across runs
    1  repeats found (listed on stdout)
    2  usage error / iteration dir missing or contains no run directories
"""

import argparse
import json
import sys
from pathlib import Path

# Present in every run by design; never a repeat worth reporting.
HARNESS_FILES = {"timing.json", "grading.json", "eval_metadata.json", "feedback.json"}


def find_runs(iteration_dir):
    """A run is a <eval>/<configuration>/ directory two levels below the iteration."""
    runs = []
    for eval_dir in sorted(p for p in iteration_dir.iterdir() if p.is_dir()):
        for config_dir in sorted(p for p in eval_dir.iterdir() if p.is_dir()):
            runs.append(config_dir)
    return runs


def collect_repeats(iteration_dir):
    runs = find_runs(iteration_dir)
    by_basename = {}
    for run in runs:
        run_id = f"{run.parent.name}/{run.name}"
        for f in sorted(run.rglob("*")):
            if not f.is_file() or f.name in HARNESS_FILES:
                continue
            entry = by_basename.setdefault(f.name, {})
            entry.setdefault(run_id, []).append(str(f))
    repeats = [
        {"basename": name, "runs": sorted(paths_by_run), "paths": sorted(p for ps in paths_by_run.values() for p in ps)}
        for name, paths_by_run in sorted(by_basename.items())
        if len(paths_by_run) >= 2
    ]
    return runs, repeats


def main():
    ap = argparse.ArgumentParser(description="Report basenames appearing in 2+ runs of an eval iteration.")
    ap.add_argument("iteration_dir", help="path to <workspace>/iteration-N")
    ap.add_argument("--json", action="store_true", help="emit full JSON to stdout")
    ap.add_argument("--out", help="write full JSON to FILE, summary to stdout")
    args = ap.parse_args()

    iteration_dir = Path(args.iteration_dir)
    if not iteration_dir.is_dir():
        print(f"error: not a directory: {iteration_dir}", file=sys.stderr)
        return 2
    runs, repeats = collect_repeats(iteration_dir)
    if not runs:
        print(f"error: no run directories (<eval>/<configuration>/) under {iteration_dir}", file=sys.stderr)
        return 2

    result = {"iteration": str(iteration_dir), "runs_scanned": len(runs), "repeats": repeats}
    payload = json.dumps(result, indent=2)
    if args.out:
        Path(args.out).write_text(payload + "\n")
        print(f"{len(repeats)} repeated basename(s) across {len(runs)} runs -> {args.out}")
    elif args.json:
        print(payload)
    else:
        print(f"{len(repeats)} repeated basename(s) across {len(runs)} runs")
        for r in repeats:
            print(f"  {r['basename']}: {', '.join(r['runs'])}")
    return 1 if repeats else 0


if __name__ == "__main__":
    sys.exit(main())
