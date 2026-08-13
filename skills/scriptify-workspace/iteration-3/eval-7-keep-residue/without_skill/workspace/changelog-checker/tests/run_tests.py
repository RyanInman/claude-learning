#!/usr/bin/env python3
"""Run every case in manifest.json against scripts/check_changelogs.py.

Usage: python3 tests/run_tests.py
Exit 0 when every case matches its expected JSON, 1 otherwise.
"""

import json
import subprocess
import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent
SKILL = TESTS.parent


def main():
    manifest = json.loads((TESTS / "manifest.json").read_text(encoding="utf-8"))
    script = SKILL / manifest["script"]
    failures = 0

    for case in manifest["cases"]:
        fixture = SKILL / case["fixture"]
        expected_path = SKILL / case["expected"]
        run = subprocess.run(
            [sys.executable, str(script), str(fixture)],
            capture_output=True,
            text=True,
        )
        if run.returncode != case["exit_code"]:
            print(
                "FAIL {}: exit {}, expected {}\n{}".format(
                    case["name"], run.returncode, case["exit_code"], run.stderr
                )
            )
            failures += 1
            continue
        actual = json.loads(run.stdout)
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        if actual != expected:
            print("FAIL {}: output differs from {}".format(case["name"], case["expected"]))
            failures += 1
            continue
        print("PASS {}".format(case["name"]))

    print("{} case(s), {} failure(s)".format(len(manifest["cases"]), failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
