#!/usr/bin/env python3
"""Report the benchmark as a capability delta per property, not one pass rate.

A single percentage hides where the signal is: in iteration-3, 36 of 51 assertions passed in both
arms, and every assertion that separated the arms tested one property. This reports:

  - a guardrail block, pass/fail, never averaged into a rate
  - a signal delta per property group, so the result says which capability moved
  - a stale list: assertions whose graded text no longer matches evals.json, which need re-grading
    before their numbers mean anything

Assertions are matched by text, not index, because the suite gains and loses assertions between
iterations and index matching would silently compare different checks.

Usage: python3 report_by_property.py [iteration_dir] [--evals PATH]
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

DEFAULT_EVALS = Path(__file__).resolve().parents[2] / "scriptify/evals/evals.json"
CONFIGS = ("with_skill", "without_skill")


def load_suite(evals_path: Path) -> dict:
    """Map eval_id -> {assertion text: {tier, property}}."""
    data = json.loads(evals_path.read_text())
    return {
        e["id"]: {
            a["text"]: {"tier": a.get("tier", "signal"),
                        "property": a.get("property", "unclassified")}
            for a in e["assertions"]
        }
        for e in data["evals"]
    }


def collect(iteration: Path, suite: dict):
    guard = defaultdict(lambda: defaultdict(list))   # property -> config -> [bool]
    signal = defaultdict(lambda: defaultdict(list))
    stale = []
    for eval_dir in sorted(iteration.glob("eval-*")):
        eval_id = int(eval_dir.name.split("-")[1])
        spec = suite.get(eval_id, {})
        for cfg in CONFIGS:
            g = eval_dir / cfg / "grading.json"
            if not g.exists():
                continue
            for exp in json.loads(g.read_text()).get("expectations", []):
                text = exp.get("text", "")
                meta = spec.get(text)
                if meta is None:
                    stale.append((eval_id, cfg, text))
                    continue
                bucket = guard if meta["tier"] == "guardrail" else signal
                bucket[meta["property"]][cfg].append(bool(exp.get("passed")))
    return guard, signal, stale


def rate(vals):
    return sum(vals) / len(vals) if vals else 0.0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("iteration_dir", nargs="?", default=str(Path(__file__).parent))
    ap.add_argument("--evals", default=str(DEFAULT_EVALS))
    args = ap.parse_args()

    iteration = Path(args.iteration_dir).resolve()
    suite = load_suite(Path(args.evals))
    guard, signal, stale = collect(iteration, suite)

    print(f"# Benchmark by property — {iteration.name}\n")

    print("## Guardrails (binary; a failure invalidates its own eval, not the pass)\n")
    if not guard:
        print("  none graded\n")
    for prop in sorted(guard):
        row = guard[prop]
        w, b = row.get("with_skill", []), row.get("without_skill", [])
        status = "OK" if all(w) and all(b) else "FAIL"
        print(f"  {status:4}  {prop:20}  with {sum(w)}/{len(w)}   base {sum(b)}/{len(b)}")

    print("\n## Signal, by property\n")
    print(f"  {'property':24} {'with':>8} {'base':>8} {'delta':>8}   n")
    tw = tb = tn = 0
    for prop in sorted(signal):
        w, b = signal[prop].get("with_skill", []), signal[prop].get("without_skill", [])
        tw += sum(w); tb += sum(b); tn += len(w)
        print(f"  {prop:24} {rate(w):>8.3f} {rate(b):>8.3f} {rate(w)-rate(b):>+8.3f}   {len(w)}")
    if tn:
        print(f"\n  {'CAPABILITY DELTA':24} {tw/tn:>8.3f} {tb/tn:>8.3f} {(tw-tb)/tn:>+8.3f}   {tn}")

    if stale:
        print(f"\n## Stale — {len(stale)} graded assertions no longer match evals.json\n")
        print("  These were graded against superseded text. Their numbers above are omitted;")
        print("  re-grade before reading any delta as final.\n")
        for eval_id, cfg, text in stale:
            print(f"  eval {eval_id} [{cfg}]: {text[:88]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
