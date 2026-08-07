#!/usr/bin/env python3
"""Smoke-test every script in this skill against the manifest beside this file.

Usage: python3 scripts/tests/run_smoke.py [MANIFEST]
Default manifest: scripts/tests/manifest.json. Exit 0 when every case passes,
1 when any case fails.

Manifest schema (per script entry):
  path                 script path, relative to target_skill
  invocations[]        argv + expect_exit / expect_stdout_json / expect_stdout_contains
  bad_data_invocation  argv that must exit non-zero on malformed input
  bad_invocation       argv that must exit non-zero on a usage error
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MANIFEST = os.path.join(HERE, "manifest.json")


def check_case(cwd, case, label, failures):
    argv = case["argv"]
    proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
    out = proc.stdout

    if "expect_exit" in case and proc.returncode != case["expect_exit"]:
        failures.append("%s: exit %d, expected %d" % (label, proc.returncode, case["expect_exit"]))
    if case.get("expect_exit_nonzero") and proc.returncode == 0:
        failures.append("%s: exit 0, expected non-zero" % label)
    if case.get("expect_stdout_json"):
        try:
            json.loads(out)
        except ValueError as exc:
            failures.append("%s: stdout is not JSON (%s)" % (label, exc))
    needle = case.get("expect_stdout_contains")
    if needle and needle not in out:
        failures.append("%s: stdout missing %r" % (label, needle))


def main(argv):
    manifest_path = argv[1] if len(argv) > 1 else DEFAULT_MANIFEST
    with open(manifest_path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)

    cwd = manifest["target_skill"]
    failures = []
    cases = 0

    for entry in manifest["scripts"]:
        script = entry["path"]
        if not os.path.isfile(os.path.join(cwd, script)):
            failures.append("%s: script not found" % script)
            continue
        for i, case in enumerate(entry.get("invocations", [])):
            check_case(cwd, case, "%s invocation[%d]" % (script, i), failures)
            cases += 1
        for key in ("bad_data_invocation", "bad_invocation"):
            if key in entry:
                check_case(cwd, entry[key], "%s %s" % (script, key), failures)
                cases += 1

    for fixture in sorted(set(
        arg
        for entry in manifest["scripts"]
        for case in list(entry.get("invocations", [])) + [entry.get(k) for k in ("bad_data_invocation", "bad_invocation") if k in entry]
        for arg in case["argv"]
        if arg.startswith("/")
    )):
        if not os.path.exists(fixture):
            failures.append("fixture missing: %s" % fixture)

    print("ran %d cases from %s" % (cases, manifest_path))
    for f in failures:
        print("FAIL %s" % f)
    if failures:
        return 1
    print("all green")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
