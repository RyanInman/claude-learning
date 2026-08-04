#!/usr/bin/env python3
"""Compute the skill-vs-baseline delta trend across eval iterations.

Reads every <workspace>/iteration-*/benchmark.json (as produced by
scripts/aggregate_benchmark.py; schema in references/schemas.md), extracts the
per-configuration run_summary (pass_rate / time_seconds / tokens means), and
computes the with_skill minus baseline pass-rate delta per iteration. The
baseline is whichever non-"with_skill" configuration the summary holds
(without_skill or old_skill).

Flags "tie": true when the latest iteration's pass-rate delta is <= 0 —
SKILL.md's retire-the-skill signal. Deciding retire vs continue stays with the
agent and user; this tool only computes.

USAGE
    python3 scripts/benchmark_trend.py <workspace> [--json] [--out FILE]

    --json      emit full JSON to stdout (default: human-readable summary)
    --out FILE  write full JSON to FILE, print summary to stdout

EXIT CODES
    0  skill beats baseline in the latest iteration
    1  tie or regression in the latest iteration (delta <= 0)
    2  usage error / no iteration-*/benchmark.json found / unreadable JSON
"""

import argparse
import json
import re
import sys
from pathlib import Path


def summary_of(benchmark, path):
    rs = benchmark.get("run_summary")
    if not isinstance(rs, dict) or "with_skill" not in rs:
        raise ValueError(f"{path}: run_summary.with_skill missing")
    baseline_name = next((k for k in rs if k not in ("with_skill", "delta", "notes")), None)
    if baseline_name is None:
        raise ValueError(f"{path}: no baseline configuration in run_summary")

    def stats(cfg):
        c = rs[cfg]
        return {m: c.get(m, {}).get("mean") for m in ("pass_rate", "time_seconds", "tokens")}

    with_skill, baseline = stats("with_skill"), stats(baseline_name)
    if with_skill["pass_rate"] is None or baseline["pass_rate"] is None:
        raise ValueError(f"{path}: pass_rate.mean missing")
    return {
        "with_skill": with_skill,
        "baseline_configuration": baseline_name,
        "baseline": baseline,
        "pass_rate_delta": round(with_skill["pass_rate"] - baseline["pass_rate"], 4),
    }


def main():
    ap = argparse.ArgumentParser(description="Skill-vs-baseline delta per iteration; tie flag on the latest.")
    ap.add_argument("workspace", help="eval workspace containing iteration-*/benchmark.json")
    ap.add_argument("--json", action="store_true", help="emit full JSON to stdout")
    ap.add_argument("--out", help="write full JSON to FILE, summary to stdout")
    args = ap.parse_args()

    workspace = Path(args.workspace)
    if not workspace.is_dir():
        print(f"error: not a directory: {workspace}", file=sys.stderr)
        return 2
    bench_files = sorted(
        workspace.glob("iteration-*/benchmark.json"),
        key=lambda p: int(re.search(r"\d+", p.parent.name).group()),
    )
    if not bench_files:
        print(f"error: no iteration-*/benchmark.json under {workspace}", file=sys.stderr)
        return 2

    iterations = []
    for path in bench_files:
        try:
            data = json.loads(path.read_text())
            entry = summary_of(data, path)
        except (ValueError, json.JSONDecodeError, OSError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        entry["iteration"] = path.parent.name
        iterations.append(entry)

    latest = iterations[-1]
    result = {
        "workspace": str(workspace),
        "iterations": iterations,
        "latest_delta": latest["pass_rate_delta"],
        "tie": latest["pass_rate_delta"] <= 0,
    }
    payload = json.dumps(result, indent=2)
    if args.out:
        Path(args.out).write_text(payload + "\n")
        print(f"{len(iterations)} iteration(s), latest delta {latest['pass_rate_delta']:+} -> {args.out}")
    elif args.json:
        print(payload)
    else:
        for it in iterations:
            print(f"{it['iteration']}: with_skill {it['with_skill']['pass_rate']} vs "
                  f"{it['baseline_configuration']} {it['baseline']['pass_rate']} (delta {it['pass_rate_delta']:+})")
        if result["tie"]:
            print("TIE: latest iteration does not beat baseline — retirement candidate")
    return 1 if result["tie"] else 0


if __name__ == "__main__":
    sys.exit(main())
