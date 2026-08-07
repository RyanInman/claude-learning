#!/usr/bin/env python3
"""Run the checks listed in tests/manifest.json against the bundled fixtures.

Usage (from the skill folder):
    python3 tests/run_smoke_tests.py
    python3 tests/run_smoke_tests.py --only scan-clean render-clean
    python3 tests/run_smoke_tests.py -v

Exit codes: 0 = every check passed, 1 = at least one failed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = SKILL_ROOT / "tests" / "manifest.json"


def dig(data, dotted: str):
    """Look up a dotted path; integer segments index into lists."""
    current = data
    for part in dotted.split("."):
        if isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                raise KeyError(dotted) from None
        elif isinstance(current, dict):
            if part not in current:
                raise KeyError(dotted)
            current = current[part]
        else:
            raise KeyError(dotted)
    return current


def run_check(check: dict, python: str, stdout_cache: dict[str, str]) -> list[str]:
    failures: list[str] = []
    cmd = [python, str(SKILL_ROOT / check["script"]), *check.get("args", [])]

    stdin_text = check.get("stdin")
    if "stdin_from" in check:
        source = check["stdin_from"]
        if source not in stdout_cache:
            return [f"stdin_from refers to check {source!r}, which has not run"]
        stdin_text = stdout_cache[source]

    proc = subprocess.run(
        cmd,
        cwd=SKILL_ROOT,
        input=stdin_text,
        capture_output=True,
        text=True,
    )
    stdout_cache[check["id"]] = proc.stdout

    expected_exit = check.get("expect_exit")
    if expected_exit is not None and proc.returncode != expected_exit:
        failures.append(
            f"exit code {proc.returncode}, expected {expected_exit}"
            + (f" (stderr: {proc.stderr.strip()[:200]})" if proc.stderr.strip() else "")
        )

    for needle in check.get("expect_stdout_contains", []):
        if needle not in proc.stdout:
            failures.append(f"stdout missing {needle!r}")

    for needle in check.get("expect_stderr_contains", []):
        if needle not in proc.stderr:
            failures.append(f"stderr missing {needle!r}")

    order = check.get("expect_stdout_order", [])
    positions = []
    for needle in order:
        index = proc.stdout.find(needle)
        if index < 0:
            failures.append(f"stdout missing ordered marker {needle!r}")
        positions.append(index)
    if len(positions) > 1 and all(p >= 0 for p in positions):
        if positions != sorted(positions):
            failures.append(f"stdout order wrong for {order}")

    expect_json = check.get("expect_json")
    if expect_json:
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            failures.append(f"stdout is not JSON: {exc}")
        else:
            for path, expected in expect_json.items():
                try:
                    actual = dig(payload, path)
                except KeyError:
                    failures.append(f"{path}: missing from report")
                    continue
                if actual != expected:
                    failures.append(f"{path}: got {actual!r}, expected {expected!r}")

    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", nargs="+", metavar="ID", help="run just these checks")
    parser.add_argument("-v", "--verbose", action="store_true", help="print each check's reason")
    args = parser.parse_args(argv)

    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read {MANIFEST}: {exc}", file=sys.stderr)
        return 1

    python = manifest.get("python", sys.executable or "python3")
    checks = manifest.get("checks", [])
    selected = {c.lower() for c in args.only} if args.only else None

    stdout_cache: dict[str, str] = {}
    passed = failed = skipped = 0

    for check in checks:
        if selected is not None and check["id"].lower() not in selected:
            # still run upstream producers needed by a selected check
            if not any(
                other.get("stdin_from") == check["id"]
                and other["id"].lower() in selected
                for other in checks
            ):
                skipped += 1
                continue
        failures = run_check(check, python, stdout_cache)
        if selected is not None and check["id"].lower() not in selected:
            continue
        if failures:
            failed += 1
            print(f"FAIL  {check['id']}")
            for line in failures:
                print(f"        {line}")
        else:
            passed += 1
            print(f"PASS  {check['id']}")
        if args.verbose and check.get("why"):
            print(f"        why: {check['why']}")

    print(f"\n{passed} passed, {failed} failed" + (f", {skipped} skipped" if skipped else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
