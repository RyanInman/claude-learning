#!/usr/bin/env python3
"""Compare two run_tests.py result files and print only the regression verdict.

Keeps the per-finding gate off the context stream: instead of reading a full
results JSON into the conversation every finding, the gate runs this and gets one
short line. A regression is any test id failing in `after` that passed in
`baseline`; when per-test ids aren't reliable (generic runners) it falls back to
exit code / failed count.

Usage: diff_tests.py <baseline.json> <after.json>
Exit:  0 no regression (prints "PASS") · 2 regression (prints the new failures).
"""

import json
import sys


def regressions(baseline, after):
    if baseline.get("ids_reliable") and after.get("ids_reliable"):
        return sorted(set(after.get("failed_ids", [])) - set(baseline.get("failed_ids", [])))
    worse = (after.get("exit_code", 0) != 0 and baseline.get("exit_code", 0) == 0) or \
            ((after.get("failed") or 0) > (baseline.get("failed") or 0))
    return ["<count/exit-code regression — per-test ids unavailable>"] if worse else []


def main():
    if len(sys.argv) != 3:
        print("usage: diff_tests.py <baseline.json> <after.json>", file=sys.stderr)
        sys.exit(1)
    base = json.load(open(sys.argv[1], encoding="utf-8"))
    after = json.load(open(sys.argv[2], encoding="utf-8"))
    regs = regressions(base, after)
    if regs:
        print("REGRESSED: " + ", ".join(regs))
        sys.exit(2)
    print("PASS")


if __name__ == "__main__":
    main()
