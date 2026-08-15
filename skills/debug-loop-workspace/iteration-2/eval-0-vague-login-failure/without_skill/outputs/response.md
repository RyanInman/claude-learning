# Fixed: stale session row wins on same-second refresh

## Root cause

`sessions.py` stores sessions append-only, so a refresh writes a **new row** with `version = previous + 1`. `get_session` picked the newest row like this:

```python
return max(rows, key=lambda r: r["created_at"])
```

`created_at` is stored at **one-second resolution**. When a refresh lands in the same second as the row it replaces, both rows carry an identical `created_at`. Python's `max` returns the *first* maximal element, so the tie resolves to whichever row was appended first — the **old, already-expiring row**. `refresh` then reads that row's `expires_at`, sees it in the past, and returns `401`, bouncing the user to login even though a valid session exists.

That explains both things you noticed:

- **Not everyone.** It only hits users whose refresh happens to complete inside the same clock second as the previous write. That's a timing race, so it looks random.
- **Can't get back in.** The stale row keeps winning the tie on every subsequent read, so the user stays wedged rather than recovering on retry.

## The fix

`version` is strictly increasing per `session_id`, so it — not the truncated timestamp — is the authoritative ordering:

```python
# created_at has one-second resolution, so two rows for the same session can
# tie. version is strictly increasing per session_id, so it is the
# authoritative ordering; created_at only backstops rows sharing a version.
return max(rows, key=lambda r: (r["version"], r["created_at"]))
```

One line changed in `sessions.py`. No behavior change for the non-tied case: when timestamps differ, versions already order the same way.

## Tests

Added two regression tests in `tests/test_sessions.py`:

- `test_refresh_within_same_second_uses_new_row` — two rows, same `created_at`, old one appended first. This **failed with `401` before the fix** and passes now. It's the direct reproduction of the reported bug.
- `test_same_second_tie_is_order_independent` — same tie with insertion order reversed, so the fix can't be faked by row ordering.

Full suite: **6 passed**, including all four original tests.

## Assumptions I made

You weren't around to ask, so I'm flagging these:

1. **`version` is genuinely monotonic per `session_id`.** The module docstring states it (`version = previous version + 1`), and I've relied on it. If some path can write a duplicate or out-of-order version, `created_at` still acts as the secondary key, but the ordering guarantee would be worth confirming.
2. **The one-second timestamp resolution is fixed upstream** (a DB column type, most likely). Widening it to millisecond precision would shrink the race window but not close it — two writes can still land in the same millisecond. The version tie-break is the correct fix regardless, so I did that rather than touch the schema.
3. **The `<=` in `expires_at <= now` is intentional** — a session expiring exactly at `now` counts as expired. I left it alone; it wasn't implicated in your report.

## Worth checking next

If any other code path reads sessions with its own "latest row" query — an analytics job, a login handler, a SQL `ORDER BY created_at LIMIT 1` — it has the identical tie-break bug. `get_session` was the only such spot in this module, but I couldn't see beyond it. Grepping for `created_at` ordering elsewhere in the codebase would be a cheap way to rule that out.
