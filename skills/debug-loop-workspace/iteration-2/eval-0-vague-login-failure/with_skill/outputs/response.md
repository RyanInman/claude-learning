**Root cause:** `get_session` picked the newest session row with `max(rows, key=created_at)`, but `created_at` has one-second resolution — when a refresh lands in the same second as the previous row, the two rows tie and Python's `max` returns the **first** one, i.e. the older, already-expired version. Those users get a 401 and bounce to login. Fixed by selecting on `version`, which the append-only table already increments monotonically.

## Debug Brief

**Symptom:** users intermittently get bounced to login and cannot get back in. No traceback available (assumption: the bounce is the client reacting to a `401` from session refresh — `refresh()` is the only path that returns 401).
**Repro:** append two rows for one `session_id` with the same `created_at` (v1 expired, v2 live), then `refresh(session_id, now)` → `{"status": 401}` instead of `200`.
**Check:** `python3 -m pytest tests -q`
**Scope:** `sessions.py` (`get_session`, `refresh`), `tests/test_sessions.py`

**Hypotheses (ranked):**
1. `get_session` picks the wrong row when `created_at` ties. The module docstring says `created_at` is one-second resolution and the table is append-only, so a refresh inside the same second produces duplicate `created_at` values; `max` breaks ties toward the first (older, expired) row — test: append two same-second rows and print which `version` `get_session` returns.
2. The expiry comparison is off by one (`<=` vs `<`), rejecting a session exactly at its expiry instant — test: call `refresh` with `now == expires_at`.
3. Rows leak across sessions or the store returns a different user's row — test: dump the rows the filter returns for one failing session_id.

**Constraint:** fix the root cause. No suppressed exceptions, no widened catch, no relaxed assertion, no clamped value.
**Reset trigger:** after 2 failed corrections on the same issue, stop and hand off.

Note the existing test `test_refreshed_session_uses_new_row` uses `created_at=100` then `130` — distinct seconds — which is exactly why the suite was green while real users bounced. The intermittency the report describes ("not everyone, can't tell what makes it happen") matches this: it only bites when the refresh happens to land in the same wall-clock second as the previous row.

## Step 1: baseline

```
$ python3 -m pytest tests -q
....                                                                     [100%]
4 passed in 0.01s
```

## Step 2: failing test, committed before any fix

Added `test_refresh_within_same_second_uses_newest_version` to `tests/test_sessions.py`. No implementation code changed in this step.

```
$ python3 -m pytest tests -q
...F.                                                                    [100%]
=================================== FAILURES ===================================
_____________ test_refresh_within_same_second_uses_newest_version ______________

    def test_refresh_within_same_second_uses_newest_version():
        # created_at has one-second resolution, so a refresh that lands in the same
        # second as the previous row produces two rows with identical created_at.
        sessions.append_session("s1", version=1, token="t1", expires_at=120, created_at=100)
        sessions.append_session("s1", version=2, token="t2", expires_at=400, created_at=100)
        result = sessions.refresh("s1", now=150)
>       assert result["status"] == 200
E       assert 401 == 200

tests/test_sessions.py:32: AssertionError
=========================== short test summary info ============================
FAILED tests/test_sessions.py::test_refresh_within_same_second_uses_newest_version
1 failed, 4 passed in 0.01s
```

Committed as `test: failing repro - same-second refresh returns stale expired row`.

## Step 3: instrumentation — actual runtime values

```
$ python3 -c "..."   # print the rows and the row get_session selects
created_at values: [100, 100]
get_session picked version: 1 expires_at: 120
refresh(now=150): {'status': 401}
```

Hypothesis 1 confirmed: with tied `created_at`, `get_session` returns version 1 (`expires_at=120`), already past `now=150`, so `refresh` returns 401 even though version 2 is live until 400. Hypotheses 2 and 3 were not needed.

## Step 4: the fix — one line

```diff
 def get_session(session_id):
     rows = [r for r in ROWS if r["session_id"] == session_id]
     if not rows:
         return None
-    return max(rows, key=lambda r: r["created_at"])
+    return max(rows, key=lambda r: r["version"])
```

`version` is the field the append-only design already guarantees increases per refresh, so it is the correct ordering key; `created_at` was never precise enough to order rows.

```
$ python3 -m pytest tests -q
.....                                                                    [100%]
5 passed in 0.00s
```

## Step 5: verification

Reverted the fix once to confirm it is what turned the check green:

```
$ git stash && python3 -m pytest tests -q
1 failed, 4 passed in 0.01s
$ git stash pop && python3 -m pytest tests -q
.....                                                                    [100%]
5 passed in 0.00s
```

Full suite green, including all four pre-existing tests. No test was edited or relaxed — only added. Diff is 2 files, +11/-1.

A fresh reviewer with no stake in the fix checked the diff against the brief. It confirmed the root cause and that the fix is sufficient for the reported symptom, and flagged one residual gap: `append_session` accepts any caller-supplied `version` with no uniqueness check, so a duplicate `version` for one `session_id` would re-open the same first-wins tie-break bug through a different door. Not fixed here (it is not the reported failure and no code path in this module produces it); captured as a follow-up below.

```
$ git log --oneline
9ebb9b4 fix: select newest session row by version, not created_at
596917e test: failing repro - same-second refresh returns stale expired row
0071a89 baseline
```

## Assumptions and follow-ups

- **Assumption:** the login bounce is the client reacting to a 401 from session refresh. `refresh()` returning 401 on a live session is the only defect in this module, and it reproduces the reported intermittency exactly. If your bounce has a different trigger (e.g. a 404 path or something outside `sessions.py`), say so and I will re-run the loop against that symptom.
- **Not changed, worth a look:** `refresh` uses `expires_at <= now`, so a session is rejected at the exact instant of expiry. That is defensible, but combined with one-second `created_at`/`expires_at` resolution it costs a user up to a full second of validity. Left alone because it is not the reported bug.
- **Not changed:** `get_session` assumes `version` is unique and monotonic per `session_id`, which the module docstring states. If a writer can ever emit a duplicate version, that ordering breaks too — worth a uniqueness constraint on `(session_id, version)` at the storage layer, or a guard in `append_session`. Say the word and I will add it.
