---
name: debug-loop
description: >-
  Turns a bug report into an executable Debug Brief, then runs a verification-gated debug loop:
  reproduce deterministically, commit a failing test first, rank 2-4 hypotheses, instrument to read
  runtime values, change one variable at a time, and prove the fix with real command output. Use
  whenever someone says something is broken — "the build is failing", "this throws", "tests are
  red", "why does this return undefined", "it worked yesterday", "this endpoint got slow since the
  deploy", "track down this regression" — or
  pastes a stack trace, error log, or failing CI output and asks for a fix, even when the request
  looks like a one-line change. Also use when a previous fix attempt failed and the session needs a
  clean restart. Supersedes the diagnose skill: when both match, run debug-loop only. Do NOT use for
  building new features, for open-ended code review, or for a refactor with no failing behavior,
  because those have no pass/fail check for the loop to close on.
---

# Debug Loop

Two moves make agentic debugging work, and both are missing by default. First, **give the loop a
check it can run**. Without a command that returns pass or fail, "looks fixed" is the only signal.
The user then becomes the verification loop. Second, **spend the context on signal, not on failed
attempts**. A session that accumulates dead ends biases the model toward re-trying ruled-out fixes.

This skill runs in two stages. It rewrites the user's raw report into a **Debug Brief** —
symptom, repro, check, ranked hypotheses — and shows it. Then it runs the loop against that brief.

## Workflow

### Step 0: Before starting

Get these four facts before reading any implementation code, because a brief built on a guessed
symptom debugs the wrong problem:

1. **The exact symptom** — the verbatim error text and stack trace, or observed-versus-expected
   behavior. Never a paraphrase.
2. **A repro** — the command, request, or input that fails every time. Variability here means each
   iteration debugs a different bug.
3. **A check** — the command that returns pass or fail (`pytest path/to/test.py`, `npm run build`,
   a curl plus expected status). This is the check the whole loop closes on.
4. **A scope hint** — the files, module, or recent commit range to search first.

Mine the conversation and the repo first. A pasted traceback supplies fact 1. The test runner in
`package.json` or `Makefile` supplies fact 3. `git log` supplies fact 4. Ask the user only for what
is missing. Proceed without a pause when all four are known.

If no check exists yet, say so. Make building one the first step of the loop. Read
`references/tactics.md`, "Building a check when none exists", for the preference order. For a slow
endpoint or a latency regression, the check is a threshold rather than a boolean. The same section
covers it.

### Step 1: Emit the Debug Brief

Check Step 1a first. If all three fast-path conditions hold, emit the three-line brief there. Skip
the rest of this step.

Otherwise use this exact template. The brief is the contract for the rest of the run. A fixed shape
lets the user correct a wrong hypothesis before any code changes.

```markdown
## Debug Brief

**Symptom:** <verbatim error, or observed X vs expected Y>
**Repro:** <command or steps that fail every time>
**Check:** <command returning pass/fail — this gates the fix>
**Scope:** <files, module, or commit range to search first>

**Hypotheses (ranked):**
1. <most likely cause> — test: <the observation that confirms or kills it>
2. <next cause> — test: <...>
3. <next cause> — test: <...>

**Constraint:** fix the root cause. No suppressed exceptions, no widened catch, no relaxed
assertion, no clamped value.
**Reset trigger:** after 2 failed fixes on the same issue, stop and hand off (Step 6).
```

Rank hypotheses **before** editing. Enumerate the causes first. This prevents the jump-to-a-fix
reflex, which produces a plausible fix for the wrong fault. Three is the usual count. Use two for
an obvious bug and four for an unfamiliar subsystem. For a multi-file or unfamiliar bug, think hard
while drafting them.

Once you confirm the cause, open the final write-up with a one-line root cause above the brief. The
reader wants the answer first. The brief below it shows the work. This changes the order of the
report, never the order of the work. Draft the brief before any edit.

### Step 1a: Take the fast path when the bug is small

The full loop costs real time and tokens, and spending them on a typo is a waste. Take the fast path
when **all three** hold:

- The error text names a specific file and line.
- That line explains the failure outright, with no guessing about runtime values.
- The fix touches only that one place.

On the fast path, emit a three-line brief. Apply the fix. Run the check. Paste the output.

```markdown
**Symptom:** AttributeError: 'str' object has no attribute 'stip' at slug.py:7
**Cause:** typo — `stip()` should be `strip()`
**Check:** `pytest tests -q`
```

Skip the ranked hypotheses, the instrumentation step, and the revert check. When a test already
fails for this bug, that test is the check — do not write a second one. Keep the rest: no test
edits, no suppressed errors, real command output as evidence.

Escalate to the full loop the moment the first fix does not turn the check green. A fast-path fix
that fails is proof the cause was not as obvious as it looked.

### Step 2: Reproduce, then commit a failing test

Run the repro. Paste its real output. Then write the smallest test that fails for this bug.
**Commit that test before you write any fix.** This overrides the usual "commit only when asked"
default. The committed test exposes one failure mode: a model edits the test instead of the code.
The diff makes that edit visible. Tell the user that you will commit the test. If the user declines,
quote the test's pre-fix content verbatim instead.

State that this step changes no implementation code. If the test passes on the first run, the repro
is wrong. Go back to Step 0.

Some bugs resist a test: flaky, timing-dependent, environment-dependent, or UI-only. For those,
write a repro script that exits non-zero. Say why a test was not possible.

### Step 3: Instrument before guessing

Add logging that shows the runtime values along the path to the failure. Run the repro. Read the
output. Runtime state is the bridge between a symptom and its root cause. Without it, a fix masks
the symptom.

For a latency regression, instrument with a profiler rather than prints: `cProfile`, `py-spy`,
`node --cpu-prof`, or the platform's equivalent. Read where the time concentrates, not what the
values are. A hot loop shows up as call count times cost per call, and that product is the
observation that names the cause.

For a regression with an unknown origin, read `references/tactics.md`, "Locating a regression with
git bisect", before you instrument.

Delegate wide investigation to a subagent: many file reads, repo-wide greps for error patterns,
commit-history scans. Keep only its conclusion. Discard that work once it answers the question,
because it must not sit in the main context for the rest of the session.

### Step 4: One change, then run the check

Change one variable. Run the check. Read the actual output.

Report the result as command plus output, never as a claim:

```
$ pytest tests/test_auth.py::test_refresh_expired -q
1 passed in 0.31s
```

If the check passes, commit the fix separately from the test commit. Say that you committed it. If
the check fails, the top hypothesis is dead. Say so. Move to the next hypothesis. Never stack a
second change on an unverified first.

Keep the diff proportional to the bug. A one-cause fix that touches fourteen files is no longer a
fix. Note the adjacent problems for the user instead of solving them here.

### Step 5: Verify the fix is real

Before declaring done:

- Run the full check, not just the new test. Paste the output.
- Revert the fix once. Confirm the check goes red again. Re-apply the fix. A check that already goes
  green for another reason hides the live bug. Skip the revert only when the check takes minutes.
  Skip the revert also when Step 3 already proved the link. The instrumentation showed that the
  value change flipped the outcome.
- Confirm the fix addresses the cause named in the brief. If another change turned the test green,
  name that change.
- Two cases need a review: the fix touches more than one source file, or the cause was not the
  top-ranked hypothesis. The committed test does not count as a source file. In those cases, have a
  fresh subagent review the diff against the brief. Tell it to flag only correctness or requirement
  gaps. A reviewer that shares the code's context approves it too readily. A reviewer told to find
  any problem invents problems.
- For a fix that passes but looks suspicious, read `references/tactics.md`, "Catching a fix that
  overfits the test".

### Step 6: Reset when the loop stalls

Stop and hand off when any of these hits:

- The same issue took two fixes without progress.
- You propose fixes that repeat a hypothesis already ruled out.
- Output quality drops mid-session.

Do not push through. Write a handoff block. Tell the user to run `/clear`. Tell the user to paste
the block as the first message of the fresh session:

```markdown
## Debug Handoff

**Symptom / repro / check:** <carry over from the brief>
**Ruled out:** <hypothesis> — killed by <evidence>
**Current best hypothesis:** <...>
**Next step:** <the single concrete action to take first>
**Touched so far:** <files, and which commits are safe to keep>
```

Externalize the state before the reset, because that makes the reset cheap. A clean session with a
sharper prompt beats a long one that carries failed attempts.

## Example

**Input:** "login is broken for some users, can you fix it"

**Output:**

```markdown
## Debug Brief

**Symptom:** need the verbatim error — asked user for the traceback or the failing response body.
**Repro:** `curl -X POST localhost:3000/auth/refresh -d @fixtures/expired-session.json` → 500
**Check:** `npm test -- auth` (currently green, so it does not yet cover this)
**Scope:** src/auth/, last 10 commits touching token refresh

**Hypotheses (ranked):**
1. Refresh runs against an already-expired token and the expiry check throws instead of returning
   401 — test: log the token `exp` and the branch taken in `refreshSession`.
2. Clock skew between issuer and validator pushes valid tokens past expiry — test: print
   `Date.now()` against the token `iat` on a failing request.
3. The session row is read by `created_at` instead of highest version, returning a stale token —
   test: dump the rows the query returns for one failing user.

**Constraint:** fix the root cause. No suppressed exceptions, no widened catch, no relaxed
assertion, no clamped value.
**Reset trigger:** after 2 failed fixes on the same issue, stop and hand off.
```

Then: add the failing test for hypothesis 1, commit it, instrument `refreshSession`, run the repro.

## Gotchas

- **Never edit the test to make it pass.** If the test looks wrong, say so and ask. A silent change
  converts a bug report into a false all-clear.
- **Verify package and API names against the registry or the installed version before use.**
  Invented package names and methods are a common failure. A type checker or linter catches them
  faster than a runtime error does.
- **Do not over-read a single run.** A test can pass three times and fail the fourth from batching
  or caching effects. Freeze the input. Run a flaky check five times before you call it fixed.
- **`/rewind` checkpoints only track edits made through file-editing tools**, not changes made by
  shell commands. Use git commits as the real safety net.

## Deeper tactics

Read `references/tactics.md` in four cases:

- The bug is a regression with unknown origin.
- No check exists yet, so you must build one.
- A hook must gate the session automatically.
- A fix passes the check but looks suspicious.

It covers `git bisect`, hooks that run tests after every edit, subagent delegation cost, and
overfitting checks.
