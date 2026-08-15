---
name: debug-loop
description: >-
  Turns a bug report into an executable Debug Brief, then runs a verification-gated debug loop:
  reproduce deterministically, commit a failing test first, rank 2-4 hypotheses, instrument to read
  real runtime values, change one variable at a time, and prove the fix with actual command output
  instead of asserting it works. Use whenever someone says something is broken — "the build is
  failing", "this throws", "tests are red", "why does this return undefined", "it worked yesterday",
  "track down this regression" — or pastes a stack trace, error log, or failing CI output and asks
  for a fix, even when the request looks like a one-line change. Also use when a previous fix attempt
  already failed and the session needs a clean restart with a sharper prompt. Do NOT use for building
  new features, for open-ended code review, or for a refactor with no failing behavior, because those
  have no pass/fail check for the loop to close on.
---

# Debug Loop

Two moves make agentic debugging work, and both are missing by default. First, **give the loop a
check it can run**: without a command that returns pass or fail, "looks fixed" is the only signal
available and the user becomes the verification loop. Second, **spend the context on signal, not on
failed attempts**: a debug session that accumulates dead ends biases the model toward re-trying
ruled-out fixes.

So this skill does two things in order. It rewrites the user's raw report into a **Debug Brief** —
symptom, repro, check, ranked hypotheses — and shows it. Then it runs the loop against that brief.

Scope check: a failing behavior with a check to close on. New features, style-only refactors, and
open-ended review belong elsewhere.

## Workflow

### Step 0: Before starting

Get these four facts before reading any implementation code, because a brief built on a guessed
symptom debugs the wrong problem:

1. **The exact symptom** — the verbatim error text and stack trace, or observed-versus-expected
   behavior. Never a paraphrase.
2. **A repro** — the command, request, or input that fails every time. Variability here means each
   iteration debugs a different bug.
3. **A check** — the command that returns pass or fail (`pytest path/to/test.py`, `npm run build`,
   a curl plus expected status). This is the gate the whole loop closes on.
4. **A scope hint** — the files, module, or recent commit range to search first.

Mine the conversation and the repo for these first: a pasted traceback supplies fact 1, the test
runner in `package.json` or `Makefile` supplies fact 3, `git log` supplies fact 4. Ask the user only
for what is genuinely missing, and pass silently when all four are known.

If no check exists yet, say so and make creating one the first step of the loop.

### Step 1: Emit the Debug Brief

Use this exact template — the brief is the contract for the rest of the run, and a fixed shape lets
the user correct a wrong hypothesis before any code changes:

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
**Reset trigger:** after 2 failed corrections on the same issue, stop and hand off (Step 6).
```

Rank hypotheses **before** editing. Enumerating causes first is what prevents the jump-to-a-fix
reflex that produces a plausible patch for the wrong fault. Three is the usual count; two is fine
for an obvious bug, four for an unfamiliar subsystem. For a multi-file or unfamiliar bug, think hard
while drafting them.

Once the cause is confirmed, the final write-up can open with a one-line root cause above the brief.
The reader wants the answer first; the brief below it shows the work. This changes the order of the
report, never the order of the work — the brief is still drafted before any edit.

### Step 1a: Take the fast path when the bug is small

The full loop costs real time and tokens, and spending them on a typo is waste. Take the fast path
when **all three** hold:

- The error text names a specific file and line.
- Reading that line explains the failure outright, with no guessing about runtime values.
- The fix is confined to that one place.

On the fast path, emit a three-line brief, fix, run the check, and paste the output:

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

Run the repro and paste its real output. Then write the smallest test that fails for this bug and
**commit it before writing any fix**. The committed test is what exposes the failure mode where a
model edits the test instead of the code — the diff makes that visible.

State explicitly that no implementation code changes in this step. If the test passes on the first
run, the repro is wrong; go back to Step 0 rather than proceeding.

When the bug resists a test (flaky, environment-dependent, UI-only), write a repro script that
exits non-zero instead, and say why a test was not possible.

### Step 3: Instrument before guessing

Add logging or prints that show the actual runtime values along the path to the failure, run the
repro, and read the output. Runtime state is the bridge between a symptom and its root cause;
without it, fixes tend to mask the symptom.

For wide investigation — reading many files, grepping error patterns across the repo, scanning
commit history — delegate to a subagent and keep only its conclusion. That work is discarded once
it answers the question, so it should not sit in the main context for the rest of the session.

### Step 4: One change, then run the check

Change one variable. Run the check. Read the actual output.

Report the result as command plus output, never as a claim:

```
$ pytest tests/test_auth.py::test_refresh_expired -q
1 passed in 0.31s
```

If the check passes, commit. If it fails, the top hypothesis is dead — say so, move to the next one,
and do not stack a second change on top of an unverified first.

Keep the diff proportional to the bug. A one-cause fix that touches fourteen files has stopped being
a fix; note the adjacent problems for the user instead of solving them here.

### Step 5: Verify the fix is real

Before declaring done:

- Run the full check, not just the new test, and paste the output.
- Confirm the fix addresses the cause named in the brief. If the passing test came from something
  else, say what actually changed.
- For anything non-trivial, have a fresh subagent review the diff against the brief and flag only
  correctness or requirement gaps. A reviewer sharing the context that produced the code is biased
  toward approving it; a reviewer told to find problems in general will invent them.

### Step 6: Reset when the loop stalls

Stop and hand off when any of these hits:

- The same issue has been corrected twice without progress.
- Proposed fixes are variants of a hypothesis already ruled out.
- Output quality has visibly dropped mid-session.

Do not push through. Write a handoff block, then tell the user to run `/clear` and paste it back as
the first message of a fresh session:

```markdown
## Debug Handoff

**Symptom / repro / check:** <carry over from the brief>
**Ruled out:** <hypothesis> — killed by <evidence>
**Current best hypothesis:** <...>
**Next step:** <the single concrete action to take first>
**Touched so far:** <files, and which commits are safe to keep>
```

Externalizing before the reset is what makes the reset cheap — a clean session with a sharper prompt
beats a long one carrying failed attempts.

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
**Reset trigger:** after 2 failed corrections on the same issue, stop and hand off.
```

Then: add the failing test for hypothesis 1, commit it, instrument `refreshSession`, run the repro.

## Gotchas

- **A green check after a change does not mean the change caused it.** Revert the fix once and
  confirm the check goes red again, because a coincidental pass hides the live bug.
- **Never edit the test to make it pass.** If the test looks wrong, say so and ask; changing it
  silently converts a bug report into a false all-clear.
- **Verify package and API names against the registry or the installed version before use.**
  Invented package names and methods are a common failure, and a type checker or linter catches
  them faster than a runtime error does.
- **Do not over-read a single run.** A test can pass three times and fail the fourth from batching
  or caching effects. Freeze the input and run a flaky check several times before calling it fixed.
- **`/rewind` checkpoints only track edits made through file-editing tools**, not changes made by
  shell commands. Use git commits as the real safety net.

## Deeper tactics

Read `references/tactics.md` when the bug is a regression with unknown origin, when the check itself
needs building, or when the session should be gated automatically. It covers `git bisect`, hooks
that run tests after every edit, subagent delegation cost, and overfitting checks.
