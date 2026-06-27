#!/usr/bin/env python3
"""Run the test command and normalize results to JSON for before/after diffs.

The whole zero-regression guarantee reduces to a set comparison: capture the set
of failing test ids before any change (baseline), then after each applied change,
and flag any id that is newly failing. This script produces that normalized set
so the comparison is deterministic instead of eyeballing log text.

Per-framework parsers extract individual failing test ids where the output makes
it possible (pytest, go, cargo). When ids can't be recovered (generic make /
gradle / mvn), it falls back to (exit_code, failed_count) — a regression is then
"exit code went non-zero" or "failed count rose".

Output JSON:
  {"command", "framework", "exit_code", "ok": bool, "passed", "failed",
   "skipped", "failed_ids": [...], "ids_reliable": bool}

Exit always 0 (the JSON carries the verdict); use --quiet to suppress raw output.
"""

import argparse
import json
import re
import subprocess
import sys


def _count(text, word):
    m = re.search(rf"(\d+) {word}", text)
    return int(m.group(1)) if m else 0


def parse_pytest(text):
    # `-v` prints one `path::test PASSED|FAILED|SKIPPED` line per test; the final
    # `=== N failed, M passed ===` line gives the totals.
    ids = sorted(set(re.findall(r"^(\S+::\S+)\s+FAILED", text, re.MULTILINE)
                     + re.findall(r"^FAILED\s+(\S+)", text, re.MULTILINE)))
    failed = _count(text, "failed")
    passed = _count(text, "passed")
    skipped = _count(text, "skipped")
    return ids, failed, passed, skipped, True


def parse_go(text):
    ids = sorted(set(re.findall(r"^--- FAIL:\s+(\S+)", text, re.MULTILINE)))
    return ids, len(ids), None, None, True


def parse_cargo(text):
    ids = sorted(set(re.findall(r"^test (\S+) \.\.\. FAILED", text, re.MULTILINE)))
    return ids, len(ids), None, None, True


def parse_unittest(text):
    # `-v` prints `name (dotted.path) ... ok|FAIL|ERROR|skipped`; footer has
    # `Ran N tests` and `FAILED (failures=X, errors=Y)`.
    ids = []
    for m in re.finditer(r"^(\S+) \((\S+?)\)(?:\s+\S.*?)? \.\.\. (FAIL|ERROR)", text, re.MULTILINE):
        ids.append(m.group(2) if "." in m.group(2) else f"{m.group(2)}.{m.group(1)}")
    ran = _count(text, "tests" if "tests" in text else "test")
    failures = int((re.search(r"failures=(\d+)", text) or [0, 0])[1])
    errors = int((re.search(r"errors=(\d+)", text) or [0, 0])[1])
    skipped = int((re.search(r"skipped=(\d+)", text) or [0, 0])[1])
    failed = failures + errors
    passed = max(ran - failed - skipped, 0) if ran else None
    return sorted(set(ids)), failed, passed, skipped, True


def parse_jest(text):
    m = re.search(r"Tests:\s+(?:(\d+) failed,?\s*)?(?:(\d+) skipped,?\s*)?(?:(\d+) passed,?\s*)?", text)
    failed = int(m.group(1)) if m and m.group(1) else 0
    skipped = int(m.group(2)) if m and m.group(2) else 0
    passed = int(m.group(3)) if m and m.group(3) else 0
    ids = sorted(set(re.findall(r"✕\s+(.+)", text)))
    return ids, failed, passed, skipped, bool(ids)


PARSERS = {"pytest": parse_pytest, "unittest": parse_unittest, "go": parse_go,
           "cargo": parse_cargo, "jest": parse_jest}


def main():
    ap = argparse.ArgumentParser(description="Run tests and emit normalized JSON results.")
    ap.add_argument("--command", required=True, help="test command to run (e.g. 'pytest -v')")
    ap.add_argument("--framework", default="generic", help="pytest|go|cargo|jest|generic")
    ap.add_argument("--cwd", default=None, help="working directory")
    ap.add_argument("--quiet", action="store_true", help="don't echo raw test output")
    args = ap.parse_args()

    proc = subprocess.run(args.command, shell=True, cwd=args.cwd,
                          capture_output=True, text=True)
    text = proc.stdout + "\n" + proc.stderr
    if not args.quiet:
        sys.stderr.write(text)

    parser = PARSERS.get(args.framework)
    if parser:
        ids, failed, passed, skipped, reliable = parser(text)
    else:
        ids, failed, passed, skipped, reliable = [], None, None, None, False

    failed_n = failed if failed is not None else (len(ids) if reliable else None)
    # exit!=0 with nothing run means the command itself broke (missing module,
    # collection error) — not a clean baseline. The skill must not treat this as
    # green; it's the "no working harness" branch.
    ran_total = (passed or 0) + (failed_n or 0) + (skipped or 0)
    error = proc.returncode != 0 and ran_total == 0
    out = {
        "command": args.command,
        "framework": args.framework,
        "exit_code": proc.returncode,
        "ok": proc.returncode == 0 and not error,
        "error": error,
        "passed": passed,
        "failed": failed_n,
        "skipped": skipped,
        "failed_ids": ids,
        "ids_reliable": reliable,
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
