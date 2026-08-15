Found and fixed it. The bug is in `get_session`, and it explains every part of what you described: only some users, no obvious pattern, and they can't get back in.

## Root cause

`sessions` is append-only — a refresh writes a *new* row for the same `session_id` with `version + 1`. `get_session` picked the current row like this:

```python
return max(rows, key=lambda r: r["created_at"])
```

`created_at` is stored with **one-second resolution**. When a user refreshes within the same second that their previous row was written, both rows carry an identical `created_at`. Python's `max` returns the **first** maximal element on a tie, which is the *older* row — the one already at or near its expiry.

So `refresh` reads the stale row, sees `expires_at <= now`, and returns `401`. The user is bounced to login. Their newly issued, still-valid session exists in the table but is never selected, so logging in again just writes another row that the same tie can hide — that's the "can't get back in" part.

Reproduced directly against the original code:

```
append_session('s1', version=1, token='t1', expires_at=120, created_at=100)
append_session('s1', version=2, token='t2', expires_at=400, created_at=100)
refresh('s1', now=150)  ->  {'status': 401}    # expected 200 / 't2'
```

This is why it looks random. It only fires when a refresh lands in the same clock second as the row before it, which depends on request timing — so it hits a fraction of users and never reproduces on demand.

## The fix

Order by `version`, not by `created_at`:

```python
def get_session(session_id):
    rows = [r for r in ROWS if r["session_id"] == session_id]
    if not rows:
        return None
    # created_at has one-second resolution, so two rows can share a timestamp and
    # ordering by it can pick a stale row. version is the authoritative append
    # order (previous + 1), so order by that.
    return max(rows, key=lambda r: r["version"])
```

`version` is the authoritative sequence for a session (each refresh is `previous + 1`), so it is exact where `created_at` is lossy. I chose it over a `(created_at, version)` tiebreak because ordering by `version` alone is also immune to a backwards clock adjustment, which would reintroduce the same class of bug — a newer row with an earlier `created_at`.

## Tests

Added three regression tests to `tests/test_sessions.py`:

- `test_refresh_within_same_second_uses_new_row` — the exact production scenario; fails on the old code with `401 != 200`.
- `test_same_second_tie_independent_of_insertion_order` — same tie, rows appended in the other order, so the test can't pass by accident of list ordering.
- `test_backwards_clock_still_uses_newest_version` — newer row has an *earlier* `created_at`.

Full suite: **7 passed**, including all 4 original tests.

## Assumptions I made

You weren't around to ask, so I want to be explicit about two things I assumed:

1. **`version` is strictly increasing per `session_id` and never reset or reused.** The module docstring states refresh appends `version = previous version + 1`, and I took that as a guarantee. If any code path writes a row without incrementing, or re-numbers versions, this fix would need `(created_at, version)` or a real sequence column instead. Worth a quick grep on your side for other writers of the `sessions` table.
2. **The stored data is fine and only the read was wrong.** I did not change `append_session` or the schema. Existing rows are all still correct — the newest version was always there, just not being selected.

## One thing I did not change

`refresh` treats `expires_at <= now` as expired, so a session expires exactly *at* its expiry second rather than one tick later. That's a defensible choice and it's unrelated to your bug, so I left it alone. Flagging it only so you know I saw it.

## Worth checking

If you have logging on 401s, the affected users should stop appearing right after deploy. If any *keep* getting bounced, that points at a second cause rather than this one, and I'd want to see those logs.
