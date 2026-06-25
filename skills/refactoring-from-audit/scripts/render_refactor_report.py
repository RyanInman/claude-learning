#!/usr/bin/env python3
"""Render the final refactor summary and the zero-regression verdict.

The skill records what happened to each finding in a results JSON as it works.
This script turns that into a human report and, critically, computes the pass/
fail verdict by diffing the final test run against the baseline: any test id
failing now that passed before is a regression and is reported loudly.

results.json schema (written by the skill):
  {
    "branch": "refactor/from-audit",
    "baseline": <run_tests.py JSON>,
    "final": <run_tests.py JSON>,
    "results": [
      {"id", "file", "title", "impact", "risk", "effort", "model",
       "status": "applied|reverted|skipped|unverified", "note"}
    ]
  }

Output: reports/refactor-summary.md (+ verdict line to stdout).
Exit: 0 no regressions · 2 regression detected.
"""

import argparse
import json
import os
import sys

STATUS_ORDER = {"applied": 0, "unverified": 1, "reverted": 2, "skipped": 3}


def regressions(baseline, final):
    """Test ids failing now but not at baseline. Falls back to counts when ids
    aren't reliable (generic frameworks)."""
    if baseline.get("ids_reliable") and final.get("ids_reliable"):
        base = set(baseline.get("failed_ids", []))
        return sorted(set(final.get("failed_ids", [])) - base)
    # no per-test ids: regression == exit code worsened or failed count rose
    worse = (final.get("exit_code", 0) != 0 and baseline.get("exit_code", 0) == 0) or \
            ((final.get("failed") or 0) > (baseline.get("failed") or 0))
    return ["<count/exit-code regression — per-test ids unavailable>"] if worse else []


def render(data):
    res = sorted(data.get("results", []), key=lambda r: (STATUS_ORDER.get(r["status"], 9),
                                                         r.get("file", "")))
    regs = regressions(data.get("baseline", {}), data.get("final", {}))
    counts = {}
    for r in res:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    lines = ["# Refactor Summary", ""]
    lines.append(f"Branch: `{data.get('branch', '-')}` · "
                 + " · ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
                 + f" · regressions: {len(regs)}")
    lines.append("")
    verdict = "PASS — no regressions" if not regs else f"FAIL — {len(regs)} regression(s)"
    lines.append(f"**Zero-regression verdict: {verdict}**")
    if regs:
        lines.append("")
        lines.append("Newly failing tests:")
        lines += [f"- `{r}`" for r in regs]
    lines.append("")
    lines.append("## Findings")
    lines.append("| File | Title | Impact | Risk | Effort | Model | Status | Note |")
    lines.append("|------|-------|--------|------|--------|-------|--------|------|")
    for r in res:
        lines.append(f"| {r.get('file','')} | {r.get('title','')} | {r.get('impact','')} "
                     f"| {r.get('risk','')} | {r.get('effort','')} | {r.get('model','')} "
                     f"| {r['status']} | {r.get('note','')} |")
    return "\n".join(lines) + "\n", regs


def main():
    ap = argparse.ArgumentParser(description="Render refactor summary + regression verdict.")
    ap.add_argument("results", help="results.json written by the skill")
    ap.add_argument("--out", default="reports/refactor-summary.md", help="output path")
    args = ap.parse_args()

    with open(args.results, encoding="utf-8") as fh:
        data = json.load(fh)
    md, regs = render(data)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(md)

    print(f"{'PASS' if not regs else 'FAIL'} — regressions: {len(regs)} — wrote {args.out}")
    sys.exit(2 if regs else 0)


if __name__ == "__main__":
    main()
