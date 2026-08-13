#!/usr/bin/env python3
"""Re-run the kept smoke tests for scripts/check_changelogs.py.

Reads manifest.json next to this file, confirms every recorded fixture path
still resolves, runs the checker on each fixture directory, and compares the
JSON report against the expected values in the manifest.

Usage: python3 scripts/tests/run_tests.py
Exit codes: 0 = all cases pass, 1 = a case failed or a fixture is missing.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "manifest.json"


def check(case, report, failures):
    exp = case["expected"]
    name = case["name"]

    def cmp(label, got, want):
        if got != want:
            failures.append("%s: %s\n    expected %r\n    got      %r" % (name, label, want, got))

    cmp("file_count", report["file_count"], exp["file_count"])
    cmp("files_sorted", report["files_sorted"], exp["files_sorted"])
    cmp("heading_violations", [v["file"] for v in report["heading_violations"]], exp["heading_violations"])
    cmp("totals", report["totals"], exp["totals"])
    cmp("grand_total", report["grand_total"], exp["grand_total"])
    cmp("unknown_tags", report["unknown_tags"], exp["unknown_tags"])
    cmp("misc_entries", report["misc_entries"], exp["misc_entries"])
    rows = report["table_markdown"].splitlines()
    first_row_version = rows[2].split("|")[1].strip() if len(rows) > 2 else ""
    cmp("table sorted descending (first data row)", first_row_version, exp["table_first_row_version"])


def main():
    if not MANIFEST.is_file():
        print("FAIL missing manifest: %s" % MANIFEST)
        return 1
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    script = Path(manifest["script"])
    failures = []

    if not script.is_file():
        failures.append("checker script missing: %s" % script)

    for case in manifest["cases"]:
        for p in [case["fixture_dir"]] + case["fixture_files"]:
            if not Path(p).exists():
                failures.append("%s: fixture path does not resolve: %s" % (case["name"], p))
        if failures:
            continue
        proc = subprocess.run(
            [sys.executable, str(script), case["fixture_dir"]],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            failures.append("%s: checker exited %d\n%s" % (case["name"], proc.returncode, proc.stderr.strip()))
            continue
        check(case, json.loads(proc.stdout), failures)
        print("ran case %s on %s" % (case["name"], case["fixture_dir"]))

    if failures:
        print("\nFAIL (%d)" % len(failures))
        for f in failures:
            print("  - %s" % f)
        return 1
    print("PASS %d cases" % len(manifest["cases"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
