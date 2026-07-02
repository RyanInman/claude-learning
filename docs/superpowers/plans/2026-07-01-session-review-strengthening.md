# Session-Review Strengthening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modernize the session-review skill: fix analyze_session.py for the current transcript format (subagent sibling dirs, turn_duration, usage.speed, cache TTL split, attributionSkill, per-model windows), refresh both references with verified mid-2026 facts, and make four small SKILL.md edits.

**Architecture:** Three unchanged layers: `scripts/analyze_session.py` does deterministic measurement, `references/*.md` interpret, `SKILL.md` routes. Script changes are TDD'd against two synthetic fixture transcripts (legacy interleaved format, modern subagent-dir format) via a stdlib test runner. Reference files are full-content rewrites with verified citations.

**Tech Stack:** Python 3 stdlib only (no pip installs, no pytest; plain-assert runner). Markdown for references. Spec: `docs/superpowers/specs/2026-07-01-session-review-strengthening-design.md`.

## Global Constraints

- Python: stdlib only; script stays a single file; exit codes unchanged (0 success, 2 bad args, 3 not found, 4 no records).
- All new parsing tolerates old transcripts: absent fields, absent subagent dirs, both sidechain formats. Never crash on missing keys.
- Cache TTL constant: 300 seconds. Danger-zone fraction stays 0.80. Context-degrade threshold stays 50,000 tokens (absolute).
- 1M-window model fragments (verified 2026-07-01): `fable-5`, `mythos`, `opus-4-8`, `opus-4-7`, `opus-4-6`, `sonnet-5`, `sonnet-4-6`. Fallback window: 200,000.
- Line budgets: SKILL.md < 200 lines; review-checklist.md ≤ 220; harness-fixes.md ≤ 160.
- Only verified facts enter references; community guidance must be labeled as such. No numbers the spec's Sources section can't back.
- Fixtures are synthetic: no real usernames, paths, or session content.
- All paths below are relative to the repo root `/Users/admin/claude-learning`.

## File Structure

- Create: `skills/session-review/scripts/fixtures/legacy_session.jsonl` — old format, interleaved `isSidechain: true` entries.
- Create: `skills/session-review/scripts/fixtures/modern_session.jsonl` — current format: `isSidechain: false` main entries, `turn_duration` system entries, `usage.speed`, `cache_creation` TTL split, `attributionSkill`.
- Create: `skills/session-review/scripts/fixtures/modern_session/subagents/agent-a1b2c3.jsonl` — subagent transcript in the sibling-dir layout.
- Create: `skills/session-review/scripts/test_analyze_session.py` — stdlib assertion runner, exit 0/1.
- Modify: `skills/session-review/scripts/analyze_session.py` — six additive changes (Tasks 2–7).
- Modify: `skills/session-review/references/review-checklist.md` — full-content refresh (Task 8).
- Modify: `skills/session-review/references/harness-fixes.md` — full-content refresh (Task 9).
- Modify: `skills/session-review/SKILL.md` — four small edits (Task 10).

---

### Task 1: Fixtures and test harness (legacy characterization test)

**Files:**
- Create: `skills/session-review/scripts/fixtures/legacy_session.jsonl`
- Create: `skills/session-review/scripts/fixtures/modern_session.jsonl`
- Create: `skills/session-review/scripts/fixtures/modern_session/subagents/agent-a1b2c3.jsonl`
- Create: `skills/session-review/scripts/test_analyze_session.py`

**Interfaces:**
- Consumes: `analyze_session.iter_records(path)`, `analyze_session.analyze(records)` (existing).
- Produces: test helpers used by every later task: `run_analysis(fixture_name) -> dict` (parses a fixture and returns the metrics dict), `check(name, actual, expected)` (records pass/fail), module alias `A` for analyze_session. Fixture files in their final form; later tasks only ADD asserts, never edit fixtures.

- [ ] **Step 1: Write the legacy fixture**

Create `skills/session-review/scripts/fixtures/legacy_session.jsonl` with exactly these 7 lines (one JSON object per line, no blank lines):

```json
{"type":"user","uuid":"u1","parentUuid":null,"timestamp":"2026-06-30T09:00:00.000Z","sessionId":"legacy-fixture","cwd":"/tmp/proj","gitBranch":"main","version":"1.0.98","message":{"role":"user","content":"refactor the parser"}}
{"type":"assistant","uuid":"a1","parentUuid":"u1","timestamp":"2026-06-30T09:00:05.000Z","sessionId":"legacy-fixture","message":{"role":"assistant","model":"claude-sonnet-4-5-20250929","usage":{"input_tokens":1000,"cache_creation_input_tokens":6000,"cache_read_input_tokens":0,"output_tokens":300},"content":[{"type":"text","text":"Reading the parser first."},{"type":"tool_use","id":"t1","name":"Read","input":{"file_path":"/tmp/proj/parser.py"}}]}}
{"type":"user","uuid":"u2","parentUuid":"a1","timestamp":"2026-06-30T09:00:10.000Z","sessionId":"legacy-fixture","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"t1","content":"def parse(x):\n    return x.split()"}]}}
{"type":"user","uuid":"s1","parentUuid":null,"isSidechain":true,"timestamp":"2026-06-30T09:00:20.000Z","sessionId":"legacy-fixture","message":{"role":"user","content":"explore the tests directory"}}
{"type":"assistant","uuid":"s2","parentUuid":"s1","isSidechain":true,"timestamp":"2026-06-30T09:00:21.000Z","sessionId":"legacy-fixture","message":{"role":"assistant","model":"claude-sonnet-4-5-20250929","usage":{"input_tokens":500,"cache_creation_input_tokens":0,"cache_read_input_tokens":0,"output_tokens":100},"content":[{"type":"text","text":"Two test files found."}]}}
{"type":"assistant","uuid":"a2","parentUuid":"u2","timestamp":"2026-06-30T09:00:40.000Z","sessionId":"legacy-fixture","message":{"role":"assistant","model":"claude-sonnet-4-5-20250929","usage":{"input_tokens":200,"cache_creation_input_tokens":0,"cache_read_input_tokens":6900,"output_tokens":250},"content":[{"type":"text","text":"Parser refactored."}]}}
{"type":"assistant","uuid":"a3","parentUuid":"a2","timestamp":"2026-06-30T09:01:10.000Z","sessionId":"legacy-fixture","message":{"role":"assistant","model":"claude-sonnet-4-5-20250929","usage":{"input_tokens":200,"cache_creation_input_tokens":0,"cache_read_input_tokens":7200,"output_tokens":200},"content":[{"type":"text","text":"Done. Tests untouched."}]}}
```

Derived expectations (used in asserts): assistant_turns=4, user_turns=3, sidechain_entries=2, tool_calls=1, tool_results=1; billed input = 7000+500+7100+7400 = 22000, cache reads = 14100, hit fraction = round(14100/22000, 3) = 0.641; peak context 7400 → 3.7% of the 200k fallback window; zero miss turns (the only cache_read=0 turns are index 0 and the 500-token sidechain turn, which is below the 1000-token floor).

- [ ] **Step 2: Write the modern fixture (main file)**

Create `skills/session-review/scripts/fixtures/modern_session.jsonl` with exactly these 8 lines:

```json
{"type":"user","uuid":"u1","parentUuid":null,"timestamp":"2026-06-30T10:00:00.000Z","sessionId":"modern-fixture","cwd":"/tmp/proj","gitBranch":"main","version":"2.1.198","isSidechain":false,"message":{"role":"user","content":"add retry logic to the client"}}
{"type":"assistant","uuid":"a1","parentUuid":"u1","timestamp":"2026-06-30T10:00:05.000Z","sessionId":"modern-fixture","isSidechain":false,"requestId":"req_1","message":{"role":"assistant","model":"claude-opus-4-8","usage":{"input_tokens":5000,"cache_creation_input_tokens":25000,"cache_read_input_tokens":0,"output_tokens":500,"cache_creation":{"ephemeral_5m_input_tokens":25000,"ephemeral_1h_input_tokens":0},"speed":"standard","service_tier":"standard"},"content":[{"type":"text","text":"Looking at the client."},{"type":"tool_use","id":"t1","name":"Bash","input":{"command":"ls src/"}}]}}
{"type":"user","uuid":"u2","parentUuid":"a1","timestamp":"2026-06-30T10:00:10.000Z","sessionId":"modern-fixture","isSidechain":false,"message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"t1","content":"client.py\nretry.py"}]}}
{"type":"system","subtype":"turn_duration","uuid":"sys1","timestamp":"2026-06-30T10:01:40.000Z","sessionId":"modern-fixture","durationMs":95000,"messageCount":12}
{"type":"assistant","uuid":"a2","parentUuid":"u2","timestamp":"2026-06-30T10:02:00.000Z","sessionId":"modern-fixture","isSidechain":false,"requestId":"req_2","attributionSkill":"session-review","message":{"role":"assistant","model":"claude-opus-4-8","usage":{"input_tokens":31000,"cache_creation_input_tokens":0,"cache_read_input_tokens":0,"output_tokens":400,"speed":"fast","service_tier":"standard"},"content":[{"type":"text","text":"Retry logic added with backoff."}]}}
{"type":"user","uuid":"u3","parentUuid":"a2","timestamp":"2026-06-30T10:20:00.000Z","sessionId":"modern-fixture","isSidechain":false,"message":{"role":"user","content":"also fix the tests"}}
{"type":"assistant","uuid":"a3","parentUuid":"u3","timestamp":"2026-06-30T10:20:05.000Z","sessionId":"modern-fixture","isSidechain":false,"requestId":"req_3","message":{"role":"assistant","model":"claude-opus-4-8","usage":{"input_tokens":2000,"cache_creation_input_tokens":31000,"cache_read_input_tokens":0,"output_tokens":300,"speed":"standard","service_tier":"standard"},"content":[{"type":"text","text":"Tests updated."}]}}
{"type":"system","subtype":"turn_duration","uuid":"sys2","timestamp":"2026-06-30T10:20:40.000Z","sessionId":"modern-fixture","durationMs":30000,"messageCount":5}
```

Derived expectations: sidechain_entries=0; assistant contexts 30000 / 31000 / 33000; hit fraction 0.0 (no reads, 94000 billed) so `low_cache_hit` fires; a2 is a WARM miss (gap a1→a2 = 115s ≤ 300), a3 is a TTL-GAP miss (gap a2→a3 = 1085s > 300); durations [95000, 30000] → mean 62500, median 62500, max 95000; fast_mode_turns=1; skill attribution {"session-review": 400}; peak 33000 on claude-opus-4-8 (1M window) → 3.3%.

- [ ] **Step 3: Write the subagent fixture**

Create `skills/session-review/scripts/fixtures/modern_session/subagents/agent-a1b2c3.jsonl` (note: directory `modern_session/subagents/` sits next to `modern_session.jsonl`) with exactly these 3 lines:

```json
{"type":"user","uuid":"sa-u1","parentUuid":null,"timestamp":"2026-06-30T10:00:30.000Z","sessionId":"modern-fixture","isSidechain":true,"agentId":"a1b2c3","message":{"role":"user","content":"Search the codebase for existing retry helpers."}}
{"type":"assistant","uuid":"sa-a1","parentUuid":"sa-u1","timestamp":"2026-06-30T10:00:40.000Z","sessionId":"modern-fixture","isSidechain":true,"agentId":"a1b2c3","attributionAgent":"Explore","message":{"role":"assistant","model":"claude-haiku-4-5-20251001","usage":{"input_tokens":3000,"cache_creation_input_tokens":0,"cache_read_input_tokens":0,"output_tokens":500},"content":[{"type":"text","text":"Found retry.py with a backoff helper."}]}}
{"type":"assistant","uuid":"sa-a2","parentUuid":"sa-a1","timestamp":"2026-06-30T10:00:50.000Z","sessionId":"modern-fixture","isSidechain":true,"agentId":"a1b2c3","attributionAgent":"Explore","message":{"role":"assistant","model":"claude-haiku-4-5-20251001","usage":{"input_tokens":200,"cache_creation_input_tokens":0,"cache_read_input_tokens":3100,"output_tokens":200},"content":[{"type":"text","text":"No other helpers exist."}]}}
```

Derived expectations: transcript_files=1; billed input = 3000 + 3300 = 6300; cache_read_total=3100; output_total=700.

- [ ] **Step 4: Write the test runner with legacy characterization asserts**

Create `skills/session-review/scripts/test_analyze_session.py`:

```python
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
```

- [ ] **Step 5: Run the tests, expect all green (characterization of current behavior)**

Run: `python3 skills/session-review/scripts/test_analyze_session.py`
Expected: `18 checks passed, 0 failed`, exit 0. (Every assert here matches CURRENT script behavior; the modern fixture's new fields are silently ignored for now. If anything fails, the fixture content is wrong: fix the fixture, not the script.)

- [ ] **Step 6: Commit**

```bash
git add skills/session-review/scripts/fixtures skills/session-review/scripts/test_analyze_session.py
git commit -m "test: fixture harness for analyze_session (legacy + modern transcripts)"
```

---

### Task 2: Subagent transcript aggregation

**Files:**
- Modify: `skills/session-review/scripts/analyze_session.py`
- Modify: `skills/session-review/scripts/test_analyze_session.py`

**Interfaces:**
- Consumes: `iter_records`, fixture layout from Task 1.
- Produces: `analyze_subagents(session_path) -> dict` with keys `transcript_files`, `billed_input_total`, `cache_read_total`, `cache_creation_total`, `output_total` (all ints). `run_analysis` now attaches it at `m["subagents"]`. Later tasks rely on `m["subagents"]` existing.

- [ ] **Step 1: Add failing asserts**

In `test_analyze_session.py`, replace the `run_analysis` function body so it wires subagents the same way `main()` will:

```python
def run_analysis(fixture_name):
    path = FIX / fixture_name
    records, _total, bad = A.iter_records(path)
    assert bad == 0, f"{fixture_name}: {bad} malformed fixture lines"
    m = A.analyze(records)
    m["subagents"] = A.analyze_subagents(path)
    return m
```

Add at the end of `test_legacy()`:

```python
    check("legacy.subagent_files", m["subagents"]["transcript_files"], 0)
```

Add at the end of `test_modern()`:

```python
    sa = m["subagents"]
    check("modern.subagent_files", sa["transcript_files"], 1)
    check("modern.subagent_billed_input", sa["billed_input_total"], 6300)
    check("modern.subagent_cache_read", sa["cache_read_total"], 3100)
    check("modern.subagent_output", sa["output_total"], 700)
```

- [ ] **Step 2: Run tests, expect failure**

Run: `python3 skills/session-review/scripts/test_analyze_session.py`
Expected: `AttributeError: module 'analyze_session' has no attribute 'analyze_subagents'` (nonzero exit).

- [ ] **Step 3: Implement analyze_subagents**

In `analyze_session.py`, insert this function directly after `block_text_len` (before `analyze`):

```python
def analyze_subagents(session_path):
    """Aggregate token usage from subagent transcripts.

    Modern Claude Code stores each subagent's transcript in a sibling
    directory: <session-id>/subagents/agent-*.jsonl next to <session-id>.jsonl.
    Older sessions interleaved subagent turns in the main file instead
    (counted separately as counts.sidechain_entries).
    """
    result = {
        "transcript_files": 0,
        "billed_input_total": 0,
        "cache_read_total": 0,
        "cache_creation_total": 0,
        "output_total": 0,
    }
    p = Path(session_path)
    sub_dir = p.parent / p.stem / "subagents"
    if not sub_dir.is_dir():
        return result
    for f in sorted(sub_dir.glob("*.jsonl")):
        records, _total, _bad = iter_records(f)
        result["transcript_files"] += 1
        for r in records:
            if r.get("type") != "assistant":
                continue
            msg = r.get("message") or {}
            usage = msg.get("usage") or {}
            it = usage.get("input_tokens", 0) or 0
            cr = usage.get("cache_read_input_tokens", 0) or 0
            cc = usage.get("cache_creation_input_tokens", 0) or 0
            result["billed_input_total"] += it + cr + cc
            result["cache_read_total"] += cr
            result["cache_creation_total"] += cc
            result["output_total"] += usage.get("output_tokens", 0) or 0
    return result
```

In `analyze()`, add `"subagents": {},` to the `m = {...}` skeleton dict (after `"output": {},`). In `main()`, after `m = analyze(records)` add:

```python
    m["subagents"] = analyze_subagents(path)
```

Also update the module docstring's output description line ("emits a structured metrics summary...") by appending one sentence: `Subagent transcripts in the sibling <session-id>/subagents/ directory are aggregated automatically.`

- [ ] **Step 4: Run tests, expect pass**

Run: `python3 skills/session-review/scripts/test_analyze_session.py`
Expected: `23 checks passed, 0 failed`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add skills/session-review/scripts/analyze_session.py skills/session-review/scripts/test_analyze_session.py
git commit -m "feat: aggregate subagent transcripts from sibling subagents/ dir"
```

---

### Task 3: Per-turn latency from turn_duration entries

**Files:**
- Modify: `skills/session-review/scripts/analyze_session.py`
- Modify: `skills/session-review/scripts/test_analyze_session.py`

**Interfaces:**
- Consumes: modern fixture's two `turn_duration` records.
- Produces: `m["latency"]` = `{turns_measured, mean_turn_ms, median_turn_ms, max_turn_ms, slowest_turns_ms}` (ints; slowest is a desc-sorted list of ≤3 ints). Informational only, no new signal.

- [ ] **Step 1: Add failing asserts**

Add at the end of `test_legacy()`:

```python
    check("legacy.latency_turns", m["latency"]["turns_measured"], 0)
```

Add at the end of `test_modern()`:

```python
    la = m["latency"]
    check("modern.latency_turns", la["turns_measured"], 2)
    check("modern.latency_mean", la["mean_turn_ms"], 62500)
    check("modern.latency_median", la["median_turn_ms"], 62500)
    check("modern.latency_max", la["max_turn_ms"], 95000)
    check("modern.latency_slowest", la["slowest_turns_ms"], [95000, 30000])
```

- [ ] **Step 2: Run tests, expect failure**

Run: `python3 skills/session-review/scripts/test_analyze_session.py`
Expected: `KeyError: 'latency'` (nonzero exit).

- [ ] **Step 3: Implement**

In `analyze()`: add `"latency": {},` to the `m` skeleton (after `"subagents": {},`). Add `turn_durations = []` next to the other accumulators (after `assistant_text_chars = []`). In the record loop, directly after the `if r.get("isCompactSummary"):` block and before `if rtype == "summary":`, insert:

```python
        if rtype == "system" and r.get("subtype") == "turn_duration":
            d = r.get("durationMs")
            if isinstance(d, (int, float)) and d >= 0:
                turn_durations.append(int(d))
            continue
```

After the `# --- compaction ---` block, insert:

```python
    # --- latency (from system turn_duration entries; absent on old sessions) ---
    m["latency"] = {
        "turns_measured": len(turn_durations),
        "mean_turn_ms": round(statistics.mean(turn_durations)) if turn_durations else 0,
        "median_turn_ms": round(statistics.median(turn_durations)) if turn_durations else 0,
        "max_turn_ms": max(turn_durations) if turn_durations else 0,
        "slowest_turns_ms": sorted(turn_durations, reverse=True)[:3],
    }
```

- [ ] **Step 4: Run tests, expect pass**

Run: `python3 skills/session-review/scripts/test_analyze_session.py`
Expected: `29 checks passed, 0 failed`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add skills/session-review/scripts/analyze_session.py skills/session-review/scripts/test_analyze_session.py
git commit -m "feat: per-turn latency metrics from turn_duration entries"
```

---

### Task 4: Cache-miss classification by TTL gap + TTL write split

**Files:**
- Modify: `skills/session-review/scripts/analyze_session.py`
- Modify: `skills/session-review/scripts/test_analyze_session.py`

**Interfaces:**
- Consumes: trajectory entries; assistant `timestamp` strings; `usage.cache_creation` dict when present.
- Produces: `parse_iso(ts) -> datetime | None`; trajectory entries gain `"gap_seconds_since_prev"` (float or None); `m["cache"]` gains `warm_cache_miss_turns`, `miss_turns_after_ttl_gap`, `assistant_gaps_over_ttl` (ints) and, only when the transcript carries the split, `cache_creation_by_ttl` = `{"ephemeral_5m": int, "ephemeral_1h": int}`. Constant `CACHE_TTL_SECONDS = 300`.

- [ ] **Step 1: Add failing asserts**

Add at the end of `test_modern()`:

```python
    ca = m["cache"]
    check("modern.warm_misses", ca["warm_cache_miss_turns"], 1)
    check("modern.ttl_gap_misses", ca["miss_turns_after_ttl_gap"], 1)
    check("modern.gaps_over_ttl", ca["assistant_gaps_over_ttl"], 1)
    check("modern.ttl_split", ca.get("cache_creation_by_ttl"),
          {"ephemeral_5m": 25000, "ephemeral_1h": 0})
```

Add at the end of `test_legacy()`:

```python
    check("legacy.warm_misses", m["cache"]["warm_cache_miss_turns"], 0)
    check("legacy.ttl_split_absent", "cache_creation_by_ttl" in m["cache"], False)
```

- [ ] **Step 2: Run tests, expect failure**

Run: `python3 skills/session-review/scripts/test_analyze_session.py`
Expected: `KeyError: 'warm_cache_miss_turns'` (nonzero exit).

- [ ] **Step 3: Implement**

In `analyze_session.py`, add after the `LOW_CACHE_HIT_FRAC` constant:

```python
# Prompt-cache default TTL is 5 minutes (refreshed free on each use). A gap
# between assistant turns longer than this guarantees an EXPECTED cache miss
# (idle expiry) as opposed to a warm miss, which indicates prefix instability.
CACHE_TTL_SECONDS = 300
```

Add after `block_text_len`:

```python
def parse_iso(ts):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError, TypeError):
        return None
```

In `analyze()`, add accumulators next to `turn_durations = []`:

```python
    prev_assistant_dt = None
    eph_5m = 0
    eph_1h = 0
    eph_seen = False
```

In the assistant branch, after the `sum_output += ot` line, insert:

```python
            cc_detail = usage.get("cache_creation")
            if isinstance(cc_detail, dict):
                eph_seen = True
                eph_5m += cc_detail.get("ephemeral_5m_input_tokens", 0) or 0
                eph_1h += cc_detail.get("ephemeral_1h_input_tokens", 0) or 0
            cur_dt = parse_iso(ts)
            gap_s = None
            if cur_dt is not None and prev_assistant_dt is not None:
                gap_s = round((cur_dt - prev_assistant_dt).total_seconds(), 1)
            if cur_dt is not None:
                prev_assistant_dt = cur_dt
```

Add `"gap_seconds_since_prev": gap_s,` as the last key of the `trajectory.append({...})` dict.

Replace the existing miss-count loop (`cache_miss_turns = 0` through the end of its `for` loop) with:

```python
    cache_miss_turns = 0
    warm_miss_turns = 0
    ttl_gap_miss_turns = 0
    gaps_over_ttl = 0
    for i, t in enumerate(trajectory):
        gap = t.get("gap_seconds_since_prev")
        if gap is not None and gap > CACHE_TTL_SECONDS:
            gaps_over_ttl += 1
        if i == 0:
            continue
        if t["cache_read_input_tokens"] == 0 and t["context_size"] > 1000:
            cache_miss_turns += 1
            if gap is not None and gap > CACHE_TTL_SECONDS:
                ttl_gap_miss_turns += 1
            else:
                warm_miss_turns += 1
```

Replace the `m["cache"] = {...}` block with:

```python
    m["cache"] = {
        "cache_hit_fraction": cache_hit_frac,
        "cache_miss_turns": cache_miss_turns,
        "warm_cache_miss_turns": warm_miss_turns,
        "miss_turns_after_ttl_gap": ttl_gap_miss_turns,
        "assistant_gaps_over_ttl": gaps_over_ttl,
        "note": "hit fraction = cache_read / all billed input. Misses after a "
                ">5min idle gap are expected TTL expiry; only warm misses "
                "indicate prefix instability.",
    }
    if eph_seen:
        m["cache"]["cache_creation_by_ttl"] = {
            "ephemeral_5m": eph_5m, "ephemeral_1h": eph_1h,
        }
```

Add `"cache_ttl_seconds": CACHE_TTL_SECONDS,` to the `m["signals"]["_thresholds"]` dict.

- [ ] **Step 4: Run tests, expect pass**

Run: `python3 skills/session-review/scripts/test_analyze_session.py`
Expected: `35 checks passed, 0 failed`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add skills/session-review/scripts/analyze_session.py skills/session-review/scripts/test_analyze_session.py
git commit -m "feat: classify cache misses by 5-min TTL gap; surface TTL write split"
```

---

### Task 5: Per-model context windows

**Files:**
- Modify: `skills/session-review/scripts/analyze_session.py`
- Modify: `skills/session-review/scripts/test_analyze_session.py`

**Interfaces:**
- Consumes: `trajectory` entries (`model`, `context_size`).
- Produces: `model_window(model) -> int`; constants `WINDOW_1M = 1_000_000`, `MODEL_WINDOWS_1M` (tuple of the 7 fragments from Global Constraints); `peak_context_pct_of_window` and `context_in_danger_zone` computed against each turn's own model window; `_thresholds` gains `window_fallback` and `window_1m_model_fragments` (and drops the old `window` key).

- [ ] **Step 1: Add failing asserts**

Add at the end of `test_modern()`:

```python
    check("modern.peak_pct_1m_window", m["tokens"]["peak_context_pct_of_window"], 3.3)
    check("modern.danger_zone", m["signals"]["context_in_danger_zone"], False)
```

(Legacy's existing `legacy.peak_pct == 3.7` assert guards the 200k fallback path; it must keep passing.)

- [ ] **Step 2: Run tests, expect failure**

Run: `python3 skills/session-review/scripts/test_analyze_session.py`
Expected: `FAIL modern.peak_pct_1m_window: expected 3.3, got 16.5` (nonzero exit).

- [ ] **Step 3: Implement**

Add after the `CACHE_TTL_SECONDS` constant:

```python
# Context windows by model (verified against docs 2026-07-01). 1M is the
# default window for these families; everything else falls back to 200k.
WINDOW_1M = 1_000_000
MODEL_WINDOWS_1M = (
    "fable-5", "mythos", "opus-4-8", "opus-4-7", "opus-4-6",
    "sonnet-5", "sonnet-4-6",
)
```

Add after `parse_iso`:

```python
def model_window(model):
    if not model:
        return DEFAULT_WINDOW
    name = model.lower()
    for frag in MODEL_WINDOWS_1M:
        if frag in name:
            return WINDOW_1M
    return DEFAULT_WINDOW
```

In `analyze()`, in the `# --- tokens ---` section, insert after the `peak_context = ...` line:

```python
    peak_util_pct = 0.0
    crossed_danger = False
    for t in trajectory:
        cs = t["context_size"]
        if not cs:
            continue
        w = model_window(t["model"])
        peak_util_pct = max(peak_util_pct, cs / w * 100)
        if cs >= w * CONTEXT_DANGER_FRAC:
            crossed_danger = True
```

Change the `"peak_context_pct_of_window"` value in `m["tokens"]` to `round(peak_util_pct, 1)` (drop the old `round(peak_context / DEFAULT_WINDOW * 100, 1) if peak_context else 0.0` expression).

In the `# --- signals ---` section, delete the line `crossed_danger = peak_context >= DEFAULT_WINDOW * CONTEXT_DANGER_FRAC` (the loop above now sets it; `crossed_degrade` is unchanged).

In `_thresholds`, replace `"window": DEFAULT_WINDOW,` with:

```python
        "window_fallback": DEFAULT_WINDOW,
        "window_1m_model_fragments": list(MODEL_WINDOWS_1M),
```

In `text_summary`, change the peak-context line to:

```python
    lines.append(f"  peak context: {t['peak_context_size']:,} "
                 f"({t['peak_context_pct_of_window']}% of model window)")
```

- [ ] **Step 4: Run tests, expect pass**

Run: `python3 skills/session-review/scripts/test_analyze_session.py`
Expected: `37 checks passed, 0 failed`, exit 0. (`legacy.peak_pct` still 3.7.)

- [ ] **Step 5: Commit**

```bash
git add skills/session-review/scripts/analyze_session.py skills/session-review/scripts/test_analyze_session.py
git commit -m "feat: per-model context windows (1M default on current models)"
```

---

### Task 6: Fast-mode and skill-attribution metrics

**Files:**
- Modify: `skills/session-review/scripts/analyze_session.py`
- Modify: `skills/session-review/scripts/test_analyze_session.py`

**Interfaces:**
- Consumes: `usage.speed` and top-level `attributionSkill` on assistant records.
- Produces: `m["models"]["fast_mode_turns"]` (int); `m["attribution"]` = `{"output_tokens_by_skill": {skill: int, ...}}` (top 5, empty dict when absent).

- [ ] **Step 1: Add failing asserts**

Add at the end of `test_modern()`:

```python
    check("modern.fast_mode_turns", m["models"]["fast_mode_turns"], 1)
    check("modern.skill_attribution",
          m["attribution"]["output_tokens_by_skill"], {"session-review": 400})
```

Add at the end of `test_legacy()`:

```python
    check("legacy.fast_mode_turns", m["models"]["fast_mode_turns"], 0)
    check("legacy.skill_attribution", m["attribution"]["output_tokens_by_skill"], {})
```

- [ ] **Step 2: Run tests, expect failure**

Run: `python3 skills/session-review/scripts/test_analyze_session.py`
Expected: `KeyError: 'fast_mode_turns'` (nonzero exit).

- [ ] **Step 3: Implement**

In `analyze()`: add `"attribution": {},` to the `m` skeleton (after `"latency": {},`). Add accumulators next to `eph_seen = False`:

```python
    fast_mode_turns = 0
    skill_output_tokens = Counter()
```

In the assistant branch, insert after the `cc_detail` block (before `cur_dt = parse_iso(ts)`):

```python
            if usage.get("speed") == "fast":
                fast_mode_turns += 1
            skill = r.get("attributionSkill")
            if skill and ot:
                skill_output_tokens[skill] += ot
```

Add `"fast_mode_turns": fast_mode_turns,` as the last key of `m["models"]`. After the `m["models"]` block, insert:

```python
    # --- attribution (which skills drove output spend; absent on old sessions) ---
    m["attribution"] = {
        "output_tokens_by_skill": dict(skill_output_tokens.most_common(5)),
    }
```

- [ ] **Step 4: Run tests, expect pass**

Run: `python3 skills/session-review/scripts/test_analyze_session.py`
Expected: `41 checks passed, 0 failed`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add skills/session-review/scripts/analyze_session.py skills/session-review/scripts/test_analyze_session.py
git commit -m "feat: fast-mode turn count and per-skill output attribution"
```

---

### Task 7: Text summary plumbing

**Files:**
- Modify: `skills/session-review/scripts/analyze_session.py`
- Modify: `skills/session-review/scripts/test_analyze_session.py`

**Interfaces:**
- Consumes: all new metric blocks from Tasks 2–6.
- Produces: `--format text` output includes the new metrics; JSON shape unchanged.

- [ ] **Step 1: Add failing asserts**

Add a new test function to `test_analyze_session.py` (and call `test_text_summary()` in `main()` after `test_modern()`):

```python
def test_text_summary():
    text = A.text_summary(run_analysis("modern_session.jsonl"))
    check("text.warm_misses", "warm: 1" in text, True)
    check("text.latency_line", "LATENCY" in text, True)
    check("text.subagents_line", "SUBAGENTS" in text, True)
    check("text.fast_mode", "fast-mode turns: 1" in text, True)
```

- [ ] **Step 2: Run tests, expect failure**

Run: `python3 skills/session-review/scripts/test_analyze_session.py`
Expected: 4 FAIL lines for the `text.*` checks (nonzero exit).

- [ ] **Step 3: Implement in text_summary**

Replace the CACHE line with:

```python
    ca = m["cache"]
    lines.append(f"\nCACHE  hit fraction: {ca['cache_hit_fraction']}  "
                 f"miss turns: {ca['cache_miss_turns']} "
                 f"(warm: {ca.get('warm_cache_miss_turns', 0)}, "
                 f"after idle gap: {ca.get('miss_turns_after_ttl_gap', 0)})")
    la = m.get("latency", {})
    if la.get("turns_measured"):
        lines.append(f"\nLATENCY  turns measured: {la['turns_measured']}  "
                     f"median: {la['median_turn_ms'] / 1000:.1f}s  "
                     f"max: {la['max_turn_ms'] / 1000:.1f}s")
    sa = m.get("subagents") or {}
    if sa.get("transcript_files"):
        lines.append(f"\nSUBAGENTS  transcripts: {sa['transcript_files']}  "
                     f"billed input: {sa['billed_input_total']:,}  "
                     f"output: {sa['output_total']:,}")
```

Replace the MODELS line with:

```python
    mo = m["models"]
    fast = mo.get("fast_mode_turns", 0)
    lines.append(f"\nMODELS  {', '.join(mo['distinct_models']) or 'none'}  "
                 f"(switches: {mo['switch_count']}"
                 + (f", fast-mode turns: {fast}" if fast else "") + ")")
```

- [ ] **Step 4: Run tests and a syntax check, expect pass**

Run: `python3 skills/session-review/scripts/test_analyze_session.py && python3 -m py_compile skills/session-review/scripts/analyze_session.py && echo OK`
Expected: `45 checks passed, 0 failed` then `OK`.

- [ ] **Step 5: Smoke-test against a real session**

Run: `python3 skills/session-review/scripts/analyze_session.py --latest --format text`
Expected: a metrics summary with no traceback. If the chosen session is modern and used subagents, a SUBAGENTS line appears; LATENCY appears when turn_duration entries exist. Then run once more with `--format json | python3 -c "import json,sys; json.load(sys.stdin); print('valid json')"` → `valid json`.

- [ ] **Step 6: Commit**

```bash
git add skills/session-review/scripts/analyze_session.py skills/session-review/scripts/test_analyze_session.py
git commit -m "feat: surface latency, subagents, warm misses, fast mode in text summary"
```

---

### Task 8: review-checklist.md refresh

**Files:**
- Modify: `skills/session-review/references/review-checklist.md` (full-content replacement)

**Interfaces:**
- Consumes: metric/signal names exactly as produced by Tasks 2–7 (`warm_cache_miss_turns`, `miss_turns_after_ttl_gap`, `latency`, `fast_mode_turns`, `subagents`, `peak_context_pct_of_window`).
- Produces: the interpretation layer the reviewing agent reads. Facts must match the spec's Sources section.

- [ ] **Step 1: Replace the entire file content with:**

```markdown
# Session Review Checklist — what each signal means and how to fix it

This is the interpretation layer for `scripts/analyze_session.py`. The script
emits metrics and boolean `signals`; this file explains what each one indicates,
why it matters, and the concrete fix to recommend. Severity tags:

- **OBVIOUS** — well known, easy to spot, often still un-acted-on.
- **SUBTLE** — silent; the session still "works," just worse/slower/pricier.
- **RARELY-CONSIDERED** — high-impact and easy to miss.

Only raise a finding when the session actually shows the signal. Don't pad the
report with items that didn't fire. Lead with the highest-impact confirmed
issues. Facts were verified against primary sources 2026-07-01; community
guidance is labeled as such.

## Table of contents
1. Context management (peak context, history bloat)
2. Prompt cache health
3. Tool use and agent loops
4. Output and latency
5. Reasoning effort
6. Reliability and multi-turn structure
7. Compaction and long-running sessions
8. Cross-cutting: the one idea

---

## 1. Context management

**Signal: `high_peak_context` / `context_in_danger_zone`** (peak_context_size,
peak_context_pct_of_window — computed against each turn's model window: 1M is
the default on Fable 5, Mythos, Opus 4.6+, Sonnet 4.6+; 200k otherwise).
SUBTLE → RARELY-CONSIDERED. "Context rot" is official Anthropic vocabulary now:
as tokens grow, recall accuracy degrades, well before the window is full, and
the decline is silent. Chroma's 18-model report found focused ~300-token
prompts significantly outperforming the same questions over full ~113k-token
contexts. Still the most common root cause of "the model got dumber."
- **Fix:** `/clear` between unrelated tasks — one session per task, not one
  session per project; push exploration into subagents so the noise is
  discarded; per block ask "would removing this change the output?" The
  40–60% peak-utilization band is community guidance (HumanLayer), not an
  official target — treat it as a heuristic.

**Lost in the middle.** SUBTLE. Mid-context content is attended worst
(U-shaped curve; Liu et al. measured mid-position multi-document QA falling
below even the no-documents baseline). Earliest instructions are followed most
reliably.
- **Fix:** put the most important instructions at the start or end; in long
  sessions, re-state the live task near the end of the turn (recitation)
  rather than relying on something said 30 turns ago.

**History bloat from accumulating tool results.** SUBTLE. Old tool outputs
degrade every later turn; large `tool_results` + high `assistant_turns` is the
tell. On newer models prior-turn *thinking* is also kept by default and bills
as input (see §5).
- **Fix:** clear/compact at checkpoints; paginate or filter tool output.
  Claude Code auto-compact clears older tool outputs first, but by the time it
  fires, quality has already been degrading — don't rely on it.

**The two-correction rule.** OBVIOUS, official, rarely followed. After two
failed corrections on the same issue, `/clear` and rewrite the original prompt
with what you learned — a clean session with a better prompt almost always
beats a long session with accumulated corrections.

## 2. Prompt cache health

**Signal: `low_cache_hit`** (cache_hit_fraction; classified evidence in
warm_cache_miss_turns vs miss_turns_after_ttl_gap). RARELY-CONSIDERED,
high-impact. Cache reads cost 0.1x base input; 5-minute-TTL writes 1.25x
(1-hour writes 2x). The prefix is hashed byte-for-byte in fixed order
(tools → system → messages); any early change invalidates everything after it.
- **Read the miss classification first.** The default TTL is 5 minutes,
  refreshed free on each use. A miss after an idle gap over 5 minutes
  (`miss_turns_after_ttl_gap`) is *expected* — the cache expired; that's idle
  cost, not a harness bug. Only `warm_cache_miss_turns` (gap ≤ 5 min) indicate
  real prefix instability.
- **Warm-miss causes to check:** a timestamp/request ID early in the system
  prompt; non-deterministic tool ordering; mutating tool definitions;
  toggling thinking *mode* mid-session (invalidates message-level cache only —
  tools and system survive); adding/removing images mid-prefix.
- **Fix:** move dynamic content after the cached prefix; serialize tools in a
  fixed sorted order; for loops with predictable idle gaps, the 1-hour TTL
  (2x write) often pays for itself on a large stable prefix
  (`cache_creation_by_ttl` shows the current split).

**Signal: `model_switching`** (models.switches). SUBTLE. Caches are
model-scoped — switching mid-loop rebuilds the cache from scratch. A
deliberate one-time switch can be fine; flag it so the user confirms intent.

**Fast mode** (models.fast_mode_turns). SUBTLE cost cliff. Fast mode (Opus
4.8: up to ~2.5x faster at 2x token price) repays the *entire conversation
context* at fast-mode uncached input price the first time it's enabled in a
conversation. Enable it from the start or not at all; unavailable on
Fable/Sonnet/Haiku.

## 3. Tool use and agent loops

**Signal: `tool_sprawl`** (distinct_tools > ~15). RARELY-CONSIDERED. Past a
threshold, more visible tools degrade selection of all of them. The 2026 fix
is deferral, not just pruning: Claude Code defers MCP tool schemas by default
(tool search — Anthropic measured ~85% token reduction with accuracy *gains*).
- **Fix:** verify tool search wasn't disabled (`ENABLE_TOOL_SEARCH=false` or
  forced-upfront loading); disable unused MCP servers via `/mcp`; prefer CLI
  tools (`gh`, `aws`, `gcloud`) over MCP servers — no per-tool listing cost;
  route specialist work to subagents with small toolsets.

**Signal: `duplicate_tool_calls`** (duplicate_call_total, duplicated_tools).
SUBTLE. The same tool called with identical input more than once is wasted
work — a re-read of a file already in context, a repeated identical search.
- **Fix:** if it's a re-read of unchanged data, the info was already in
  context — the harness should remind the model not to re-fetch. If it's
  repeated searches, prefer one targeted query; make tool errors specific and
  actionable so the model doesn't retry blindly.

**Signal: `large_tool_outputs`** (tool_outputs_over_cap,
largest_tool_output_chars). SUBTLE. Outputs near the ~25k-token truncation
cap bloat context and risk silently losing the tail.
- **Fix:** default limits, pagination, `--output` to a file; process bulk
  output in a script on disk and return a summary (Anthropic measured +11%
  accuracy with 24% fewer input tokens for code-orchestrated tool use); or a
  PostToolUse hook that condenses verbose output before it enters context.

**Poor tool descriptions / ambiguous names.** SUBTLE (inferred from
misselection, not directly measured). Overlapping descriptions cause silent
misselection.
- **Fix:** crisp, differentiated descriptions; unambiguous parameter names
  (`user_id` not `user`).

## 4. Output and latency

**Output length dominates latency.** RARELY-CONSIDERED. Decode is sequential;
latency is roughly linear in output tokens, while input prefill is
comparatively cheap. High mean/max_text_chars (narration, restated code, data
dumps) is the tell.
- **Fix:** cap volume ("report at most five items"); demand structured output
  and parse it; plan-validate-execute so reasoning lives on disk. Fable 5
  un-steered elaborates beyond the task, especially at higher effort — a short
  brevity instruction is as effective as listing every verbose pattern.

**Latency metrics** (latency block, from turn_duration entries). Long turns
are NOT inherently bad — autonomous runs legitimately take minutes. Interpret
with evidence: long turns + duplicate calls + low output = thrash; long turns
+ steady distinct tool progress = working as intended.

**The two speed levers to recommend:**
- **Effort** (`/effort`; low/medium/high/xhigh/max, default high). Lower
  effort makes the model combine tool calls, skip preamble, and answer
  tersely — it shapes *all* output, not just thinking. Skills and subagents
  can pin `effort:` in frontmatter. Effort is not recorded in the transcript —
  ask the user what it was set to.
- **Fast mode** (`/fast`) for interactive iteration on Opus — see the §2 cache
  caveat. Also: parallel tool calls, and Haiku-routed subagents for
  mechanical fan-out.

## 5. Reasoning effort

**Signal: `heavy_thinking`** (thinking_blocks, approx_thinking_chars).
RARELY-CONSIDERED. Reasoning tokens bill as output and add latency. The
control surface changed in 2026: effort levels replaced thinking budgets —
`budget_tokens` is deprecated on newer models, adaptive-thinking models ignore
`MAX_THINKING_TOKENS`, and thinking cannot be disabled on Fable 5.
`ultrathink` in a prompt is the only remaining deep-reasoning keyword ("think
hard" does nothing now).
- **Fix:** heavy thinking on mechanical turns → lower session effort, or pin
  `effort: low` on the mechanical skill/subagent. On newer models prior-turn
  thinking blocks are kept by default and bill as input on every later turn —
  in very long sessions that compounds; a fresh session (or API context
  editing) clears it.

## 6. Reliability and multi-turn structure

**Signal: `tool_errors_present`** (tools.error_count). SUBTLE → OBVIOUS.
Recovered errors are normal in small numbers; clusters mean a brittle tool
interface or the model fighting an opaque failure.
- **Fix:** errors should say what went wrong, what was expected, what to try;
  backoff with jitter for rate limits. Counterpoint: keep errors in context
  *while actively debugging* — erasing failures removes the evidence the model
  adapts from (Manus); clean them at task boundaries.

**Multi-turn drift.** RARELY-CONSIDERED, now measured: across 200k+ simulated
conversations, models averaged a 39% drop when requirements arrived over many
turns vs one consolidated prompt — driven by premature answers and
over-anchoring on their own early wrong output (arXiv 2505.06120, ICLR 2026).
- **Fix:** consolidate requirements before generation; re-state the full task
  when correcting; after two failed corrections apply the two-correction rule
  (§1).

## 7. Compaction and long-running sessions

**Signal: `compaction_occurred`** (compaction.summary_lines). Informational,
not a fault. What survives is precisely documented: project-root CLAUDE.md,
unscoped rules, and auto memory are re-injected from disk; path-scoped rules
and nested CLAUDE.md are lost until a matching file is read again; invoked
skill bodies are re-injected capped at 5,000 tokens per skill / 25,000 total,
oldest dropped first; the skill *listing* is not re-injected. Auto-compact
clears older tool outputs first, then summarizes, and gives up after a few
attempts if one giant file keeps refilling context.
- **Fix:** bridging artifacts (spec/progress file + git history) so a fresh
  session can resume — now official guidance; a "Compact Instructions" section
  in CLAUDE.md or `/compact <focus>` to steer what survives; re-invoke a large
  skill after compaction if its body was dropped.
- **When recommending rewrites of memory files or summaries,** prefer
  incremental delta edits over full rewrites: iterative summarization erodes
  detail ("brevity bias") and monolithic rewrites destroy accumulated
  knowledge ("context collapse") — ACE, arXiv 2510.04618.

## 8. Cross-cutting: the one idea

Every token carried on every turn competes for the same finite attention as
the live task. Minimizing what's resident isn't austerity — it's how you buy
back the model's intelligence. Prefer one session per task; recite the live
goal near the end of long sessions; push deterministic work into scripts and
hooks; and when the same problem recurs across sessions, fix the harness
(see `references/harness-fixes.md`), not the transcript.
```

- [ ] **Step 2: Verify budget and internal consistency**

Run: `wc -l skills/session-review/references/review-checklist.md`
Expected: ≤ 220 lines.
Run: `grep -n "warm_cache_miss_turns\|miss_turns_after_ttl_gap\|fast_mode_turns\|turn_duration" skills/session-review/references/review-checklist.md | head`
Expected: each name appears; they must match the script's key names exactly.

- [ ] **Step 3: Commit**

```bash
git add skills/session-review/references/review-checklist.md
git commit -m "docs: refresh review checklist for mid-2026 (effort, TTL misses, fast mode, compaction facts)"
```

---

### Task 9: harness-fixes.md refresh

**Files:**
- Modify: `skills/session-review/references/harness-fixes.md` (full-content replacement)

**Interfaces:**
- Consumes: nothing from the script; pairs with checklist findings.
- Produces: the where-does-the-fix-live layer.

- [ ] **Step 1: Replace the entire file content with:**

```markdown
# Harness Fixes — turning session findings into instructional changes

When the session review surfaces a recurring problem, the durable fix usually
isn't "tell the model harder next time" — it's a change to the *harness*: the
always-loaded memory, the skills, the tool definitions, or a deterministic
hook. This file maps common findings to where the fix belongs.

## Table of contents
1. The decision rule — where a fix belongs
2. CLAUDE.md / memory fixes
3. Skill fixes
4. Hook fixes (guarantees)
5. Tool-definition and MCP fixes
6. The token-tier mental model

---

## 1. The decision rule — where a fix belongs

Ask, in order:

1. **Must it hold every time, no exceptions?** → a **hook**, not prose. "Never
   push to main," "run the formatter after every edit." A rule in a memory
   file is a polite request re-issued every turn; a PreToolUse hook is
   enforced once and free thereafter.
2. **Is it a multi-step procedure, or does it need scripts/templates/reference
   files?** → a **skill**. Loads on demand, keeps tokens out of every session.
3. **Is it a convention that's always true across the whole project?** →
   **project-root CLAUDE.md** (committed).
4. **Is it a personal preference across all your projects?** → **global
   `~/.claude/CLAUDE.md`**.
5. **Does it only matter in one part of the tree?** → a **path-scoped rule**
   (`.claude/rules/*.md` with a `paths:` glob) or a subdirectory CLAUDE.md.

Shorthand: **conventions go in memory; procedures go in skills; guarantees go
in hooks.**

## 2. CLAUDE.md / memory fixes

Recommend these when the session shows the model ignoring known rules,
re-learning the same facts, or carrying a bloated always-loaded layer.

- **Keep it under ~200 lines** — now the official guidance ("Aim to keep
  CLAUDE.md under 200 lines"). It's loaded in full on every turn. The
  official per-line litmus test: *"Would removing this cause Claude to make
  mistakes? If not, cut it."* Bloated memory files actively cause the model
  to ignore the rules that matter.
- **Move conditional knowledge into skills.** Official cost guidance: skills
  load on demand, so anything that only applies to certain tasks (deploy
  steps, schema docs, style guides for one subsystem) belongs in a skill, not
  in CLAUDE.md.
- **Capture repeated mistakes.** The same error twice, or a correction the
  user typed more than once, is a one-line CLAUDE.md Gotcha, not a chat fix.
- **Front-load critical rules** (primacy bias) and reserve "IMPORTANT" for the
  one or two rules that truly can't slip — if everything shouts, nothing is
  heard.
- **State the why** for non-obvious rules so the model generalizes instead of
  dropping a bare command when context shifts.
- **Cut the anti-patterns:** the Kitchen Sink (documenting everything), the
  Fossil (stale time-sensitive lines), the Contradiction (two rules pulling
  opposite ways), the Menu ("use X or Y or Z" — one default + escape hatch),
  and the Obvious ("write clean code").
- **Prefer pointers to imports.** `@imports` are inlined at launch and cost
  full tokens; a "read `references/schema.md` when relevant" pointer costs
  nothing until needed.
- **Auto memory is capped:** only the first 200 lines / 25KB of MEMORY.md load
  at session start — keep it an index (one line per memory), not a document.

## 3. Skill fixes

Recommend a skill when the session shows the same multi-step procedure worked
out from scratch, or the same helper script written repeatedly.

- **Make it a skill the third time** the user pastes the same playbook or the
  model reinvents the same helper.
- **The description is the router.** It alone decides whether the skill fires;
  the common failure is *under*-triggering. Third person, pushy, concrete
  trigger phrases, and negative triggers ("do NOT use for X").
- **Mind the listing budget.** All skill descriptions share a budget of ~1% of
  the context window, with the combined description + `when_to_use` capped at
  1,536 chars per skill. Overflow drops the least-invoked skills'
  descriptions — the symptom is a skill silently not triggering. `/doctor`
  reports shortened/dropped entries. Knobs: `skillListingMaxDescChars`,
  `skillListingBudgetFraction`, `skillOverrides` (name-only), and
  `disable-model-invocation: true` to keep a user-only skill out of the
  listing entirely.
- **Progressive disclosure:** keep SKILL.md lean (<500 lines), push mechanical
  work into `scripts/` (run, not loaded), docs into `references/` (read on
  demand), templates into `assets/`.
- **Pin `model:` and `effort:` in frontmatter** for mechanical skills and
  subagents (`model: haiku`, `effort: low`) — the routing lever that makes
  cheap steps cheap without touching the main loop.
- **If the session shows tool sprawl or duplicated work,** a skill bundling
  the right script and a tight workflow often beats more prose.

## 4. Hook fixes (guarantees)

If the review found a rule that *must* hold but didn't (a write to a protected
path, a missing lint step, a push to a protected branch), the fix is a hook.
PreToolUse blocks an action before it happens; PostToolUse lints/formats
after. Prose is advisory and degrades as context grows; hooks are enforced.

- **Hooks run as code, not context** — only a hook's `additionalContext`
  output enters the window; the hook itself costs zero resident tokens.
- **Hooks are also a token fix:** a PostToolUse hook that condenses verbose
  tool output (test logs, build spew) before it enters context turns tens of
  thousands of tokens into hundreds, every time, deterministically.

## 5. Tool-definition and MCP fixes

When the session shows misselection, repeated wrong-tool calls, or unbounded
outputs:

- **Differentiate descriptions and names** so two tools aren't confusable.
- **Bound outputs** with default limits, pagination, and `--output`-to-file.
- **Make errors actionable** (what went wrong, what was expected, what to try)
  so the model self-corrects in one turn.
- **Stabilize tool ordering** (fixed/sorted) to protect the prompt cache.
- **Keep MCP schemas deferred.** Tool search is on by default — verify nobody
  set `ENABLE_TOOL_SEARCH=false` or forced upfront loading; disable unused
  servers via `/mcp`.
- **Prefer CLI tools over MCP servers** where both exist (`gh`, `aws`,
  `gcloud`, `sentry-cli`): a CLI adds zero per-tool listing cost and its
  output can be piped through filters before it reaches context.

## 6. The token-tier mental model

Map every piece of knowledge to a tier by how *hot* it is, and keep hot data
tiny:

| Tier | Holds | Loads | Keep it |
|---|---|---|---|
| L1 — always | CLAUDE.md: build commands, architecture-at-a-glance, a few gotchas | every turn | tiny (<200 lines) |
| L2 — locality | path-scoped rules (`paths:` globs) | when a matching file is touched | <100 lines |
| L3 — task | skill bodies | when the task matches the description | <500 lines |
| Deferred | MCP tool schemas (tool search) | when the model searches for/uses the tool | names only until used |
| Disk — on demand | references, scripts, assets | read/run only when needed | unbounded |

A finance query should never load the sales schema; a payments-deploy skill
should never wake while editing inventory. Organize references by domain so
only the needed file loads.
```

- [ ] **Step 2: Verify budget**

Run: `wc -l skills/session-review/references/harness-fixes.md`
Expected: ≤ 160 lines.

- [ ] **Step 3: Commit**

```bash
git add skills/session-review/references/harness-fixes.md
git commit -m "docs: refresh harness fixes (listing budget, effort/model routing, MCP deferral, hook token fixes)"
```

---

### Task 10: SKILL.md edits

**Files:**
- Modify: `skills/session-review/SKILL.md`

**Interfaces:**
- Consumes: script behavior from Tasks 2–7.
- Produces: updated routing/gotchas; frontmatter description untouched.

- [ ] **Step 1: Add the subagent-directory note to the Inputs section**

Find:

```markdown
**A saved JSONL transcript.** Claude Code writes each session to
`~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`. If the user names a file, use it.
If they say "my latest session" or "the run I just did," run the script with `--latest`
to grab the newest one (or `--project-dir` to point at a specific project folder).
```

Replace with:

```markdown
**A saved JSONL transcript.** Claude Code writes each session to
`~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`. If the user names a file, use it.
If they say "my latest session" or "the run I just did," run the script with `--latest`
to grab the newest one (or `--project-dir` to point at a specific project folder).
Modern sessions store subagent transcripts in a sibling `<session-id>/subagents/`
directory; the script finds and aggregates them automatically.
```

- [ ] **Step 2: Add /usage to the telemetry list**

Find:

```markdown
- `/context` — what's eating the always-loaded budget before any work begins.
```

Replace with:

```markdown
- `/context` — what's eating the always-loaded budget before any work begins
  (its Skills row reflects the post-budget listing size).
- `/usage` — session cost estimate plus per-skill, per-subagent, per-plugin, and
  per-MCP-server usage breakdown (`/cost` is an alias).
```

- [ ] **Step 3: Update the sidechain gotcha and add three new ones**

Find:

```markdown
- **Sidechain entries are subagent turns.** The script counts them separately
  (`sidechain_entries`); high subagent activity is usually good context hygiene, not a problem.
```

Replace with:

```markdown
- **Subagent activity is usually good context hygiene, not a problem.** Modern
  sessions store it in `<session-id>/subagents/` (aggregated in the `subagents`
  block); legacy sessions interleave it (`sidechain_entries`).
- **Idle-gap cache misses are expected.** The prompt cache's default TTL is 5
  minutes, so `miss_turns_after_ttl_gap` is idle cost, not a defect — only
  `warm_cache_miss_turns` indicate prefix instability.
- **Effort level is not in the transcript.** Ask the user what `/effort` was
  set to before recommending reasoning-budget changes.
- **Long turns are not inherently bad.** Autonomous runs legitimately take
  minutes; read the `latency` block together with duplicate-call and output
  evidence before flagging.
```

- [ ] **Step 4: Verify budgets**

Run: `wc -l skills/session-review/SKILL.md`
Expected: < 200 lines (≈180).
Run: `python3 -c "
import re
text = open('skills/session-review/SKILL.md').read()
fm = text.split('---')[1]
m = re.search(r'description:\s*(.*?)(?=\n\w+:|\Z)', fm, re.S)
print('description chars:', len(' '.join(m.group(1).split())))
"`
Expected: `description chars: 985` (unchanged, under the 1,536 cap).

- [ ] **Step 5: Commit**

```bash
git add skills/session-review/SKILL.md
git commit -m "docs: SKILL.md subagent dir, /usage telemetry, new gotchas"
```

---

### Task 11: Final verification sweep

**Files:**
- No new changes expected; fix-forward anything this task surfaces.

- [ ] **Step 1: Full test run and syntax check**

Run: `python3 skills/session-review/scripts/test_analyze_session.py && python3 -m py_compile skills/session-review/scripts/analyze_session.py && echo ALL-OK`
Expected: `45 checks passed, 0 failed` then `ALL-OK`.

- [ ] **Step 2: Real-session runs (2–3 sessions)**

Run: `python3 skills/session-review/scripts/analyze_session.py --latest --format text`
Then pick two other transcripts: `ls -t ~/.claude/projects/*/*.jsonl | sed -n '2p;3p'` and run the script on each (both `--format text` and default JSON piped through `python3 -m json.tool > /dev/null`).
Expected: no tracebacks; JSON valid; on any session with a `<id>/subagents/` dir, `subagents.transcript_files > 0`.

- [ ] **Step 3: Line budgets**

Run: `wc -l skills/session-review/SKILL.md skills/session-review/references/*.md skills/session-review/scripts/analyze_session.py`
Expected: SKILL.md < 200; review-checklist.md ≤ 220; harness-fixes.md ≤ 160.

- [ ] **Step 4: Citation gate spot-check**

Confirm none of these unverified items appear anywhere in the three markdown files: an official context-utilization percentage target (the 40–60% band must be labeled community guidance), the word "microcompaction", minimum-cacheable-token counts, or "compact at 60%" as fact.
Run: `grep -rin "microcompaction\|compact at 60\|minimum cacheable" skills/session-review/ || echo CLEAN`
Expected: `CLEAN`.

- [ ] **Step 5: Confirm working tree is clean**

Run: `git status --short skills/session-review docs/superpowers`
Expected: no unstaged changes to session-review files (a pre-existing modification to `skills/audit-refactor/scripts/load_findings.py` and an untracked `skills/skill-reviewer/scripts/__pycache__/` may appear; leave both alone).
```
