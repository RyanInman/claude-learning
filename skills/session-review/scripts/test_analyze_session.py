#!/usr/bin/env python3
"""Fixture tests for analyze_session.py.

Run:  python3 skills/session-review/scripts/test_analyze_session.py
Exit: 0 all pass, 1 any failure. Stdlib only, no pytest.

Two fixtures under fixtures/: legacy_session.jsonl (old interleaved-sidechain
format) and modern_session.jsonl (+ modern_session/subagents/) covering
turn_duration, usage.speed, cache TTL split, and attributionSkill.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import analyze_session as A

FIX = Path(__file__).parent / "fixtures"
PASSES = 0
FAILURES = []


def check(name, actual, expected):
    global PASSES
    if actual == expected:
        PASSES += 1
    else:
        FAILURES.append(f"{name}: expected {expected!r}, got {actual!r}")


def run_analysis(fixture_name):
    path = FIX / fixture_name
    records, _total, bad = A.iter_records(path)
    assert bad == 0, f"{fixture_name}: {bad} malformed fixture lines"
    return A.analyze(records)


def test_legacy():
    m = run_analysis("legacy_session.jsonl")
    check("legacy.assistant_turns", m["counts"]["assistant_turns"], 4)
    check("legacy.user_turns", m["counts"]["user_turns"], 3)
    check("legacy.sidechain_entries", m["counts"]["sidechain_entries"], 2)
    check("legacy.tool_calls", m["counts"]["tool_calls"], 1)
    check("legacy.tool_results", m["counts"]["tool_results"], 1)
    check("legacy.hit_fraction", m["cache"]["cache_hit_fraction"], 0.641)
    check("legacy.miss_turns", m["cache"]["cache_miss_turns"], 0)
    check("legacy.peak_context", m["tokens"]["peak_context_size"], 7400)
    check("legacy.peak_pct", m["tokens"]["peak_context_pct_of_window"], 3.7)
    check("legacy.low_cache_hit", m["signals"]["low_cache_hit"], False)
    check("legacy.model_switching", m["signals"]["model_switching"], False)
    check("legacy.high_peak_context", m["signals"]["high_peak_context"], False)


def test_modern():
    m = run_analysis("modern_session.jsonl")
    check("modern.sidechain_entries", m["counts"]["sidechain_entries"], 0)
    check("modern.assistant_turns", m["counts"]["assistant_turns"], 3)
    check("modern.hit_fraction", m["cache"]["cache_hit_fraction"], 0.0)
    check("modern.miss_turns", m["cache"]["cache_miss_turns"], 2)
    check("modern.low_cache_hit", m["signals"]["low_cache_hit"], True)
    check("modern.peak_context", m["tokens"]["peak_context_size"], 33000)


def main():
    test_legacy()
    test_modern()
    print(f"{PASSES} checks passed, {len(FAILURES)} failed")
    for f in FAILURES:
        print(f"  FAIL {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
