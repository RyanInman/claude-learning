# Deeper Debug Tactics

Read this when the full loop in `SKILL.md` is not enough. Four cases qualify. The bug is a
regression with an unknown origin. No check exists to close on. The session needs an automatic gate.
A fix passes the check but looks suspicious.

## Contents

- [Locating a regression with git bisect](#locating-a-regression-with-git-bisect)
- [Building a check when none exists](#building-a-check-when-none-exists)
- [Automating the gate with hooks](#automating-the-gate-with-hooks)
- [Delegating investigation to subagents](#delegating-investigation-to-subagents)
- [Catching a fix that overfits the test](#catching-a-fix-that-overfits-the-test)
- [Context hygiene during a long session](#context-hygiene-during-a-long-session)

## Locating a regression with git bisect

Use bisect when the code worked at an earlier commit. Nobody knows which commit broke it.
Binary search finds the culprit in about 10 steps across 1,000 commits, which beats reading diffs.

1. Turn the repro into a script that exits 0 on pass and non-zero on fail.
2. Find a commit where the check passes. Run `git log`. Check three or four commits by hand.
3. Run it:

```bash
git bisect start <bad-sha> <good-sha>
git bisect run ./repro.sh
git bisect reset
```

Bisect prints the first bad commit. Read that diff, not the whole history.

Bisect only works on a tidy commit history. A repo with 400-file "wip" commits gives a first-bad
commit too large to read. In that case, instrument the failure path instead.

## Building a check when none exists

Some projects have no test for the failing area. Build the check before debugging, because a loop
without a pass or fail signal cannot close.

In order of preference:

1. **A unit test** in the project's existing framework, asserting the specific wrong value.
2. **A repro script** that exercises the path and exits non-zero on the failure. Use it when the bug
   needs a server, a browser, or real I/O.
3. **A command whose exit code already encodes the bug** — a build, a type check, a lint run.
4. **A threshold check** for a performance regression — a timed repro that exits non-zero above a
   bound (`pytest-benchmark`, `hyperfine`, or a script wrapping `time` with an explicit limit). Pin
   the bound from a real baseline. Take the first source that exists: a figure the user states, a
   timing from the last known-good commit, or an explicit target the change must hit. Say which
   source you used, because an unsourced bound is a guess. Run the check
   five times before you trust it, because a single timing is noise.

Commit the check before the fix. The committed diff proves later that the fix moved the code, not
the test.

## Automating the gate with hooks

Prose instructions are advisory. A hook is deterministic. When the same check must run all session:

- A `PostToolUse` hook runs the test command after every Edit or Write. The feedback arrives while
  the context is still fresh, so the model corrects its own mistake immediately.
- A `Stop` hook can block the turn from ending until the check passes. Claude Code overrides it after
  8 consecutive blocks, so treat it as pressure, not as an absolute gate.

Suggest a hook when the user is about to debug three or more bugs in one area. Do not install one
mid-loop without asking — an unexpected hook changes the behavior of every later turn in the session.

## Delegating investigation to subagents

**Run the work in a subagent when its output is disposable.** Discard that output once it answers
the question. A subagent can read 20 files to find where the code sets a config value. Nobody needs that output after the answer
arrives. That output must not occupy the main context for the rest of the session.

Good subagent tasks:

- "Find every place that writes to the `sessions` table and report the file and line."
- "Read the last 30 commits touching `src/auth/` and summarize what changed about token expiry."
- "Review this diff against this brief and flag only correctness gaps."

Bad subagent tasks: single-file lookups and one-line greps. A subagent run costs about three times
the tokens of the same work inline, so spend it on noisy investigation only.

## Catching a fix that overfits the test

A fix can pass the test and still be semantically wrong — special-casing the exact input, or
returning a hardcoded value that satisfies the assertion.

Two checks:

1. Add one more case that exercises the same cause with different data. An overfitted fix fails it.
2. Give an independent subagent the test and the diff, but not the debugging history. Ask whether
   the implementation generalizes beyond the test cases.

The committed-test-first discipline supports both checks. If the fix commit also modified the test,
the fix overfits the test.

## Context hygiene during a long session

- Compact at about 60% context use, ahead of the automatic threshold, because auto-compaction
  fires exactly when reliability is already lowest. Steer it: `/compact keep the auth repro and the
  ruled-out hypotheses, drop the file reads`.
- Run `/clear` between unrelated bugs. The previous bug's dead ends supply misleading examples to
  pattern-match against.
- Write the handoff block before any reset. Code changes and committed tests survive a `/clear`. The
  reasoning that produced them does not.
- Keep CLAUDE.md lean. For each line, ask one question: does removing it cause a mistake? Claude
  ignores a bloated file wholesale.
