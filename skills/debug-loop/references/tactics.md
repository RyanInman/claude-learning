# Deeper Debug Tactics

Read this when the plain loop in `SKILL.md` is not enough: the bug is a regression with an unknown
origin, there is no check to close on yet, the session needs an automatic gate, or a fix passed the
tests but looks suspicious.

## Contents

- [Locating a regression with git bisect](#locating-a-regression-with-git-bisect)
- [Building a check when none exists](#building-a-check-when-none-exists)
- [Automating the gate with hooks](#automating-the-gate-with-hooks)
- [Delegating investigation to subagents](#delegating-investigation-to-subagents)
- [Catching a fix that overfits the test](#catching-a-fix-that-overfits-the-test)
- [Context hygiene during a long session](#context-hygiene-during-a-long-session)

## Locating a regression with git bisect

Use bisect when the code worked at some earlier commit and nobody knows which change broke it.
Binary search finds the culprit in about 10 steps across 1,000 commits, which beats reading diffs.

1. Turn the repro into a script that exits 0 on pass and non-zero on fail.
2. Find a commit where the check passes (`git log` plus a manual check at a few points).
3. Run it:

```bash
git bisect start <bad-sha> <good-sha>
git bisect run ./repro.sh
git bisect reset
```

Bisect prints the first bad commit. Read that diff, not the whole history.

This only works on a tidy commit history. A repo with 400-file "wip" commits gives a first-bad
commit too large to read, so fall back to instrumenting the failure path.

## Building a check when none exists

Sometimes the project has no test for the failing area. Build the check before debugging, because a
loop without a pass/fail signal cannot close.

In order of preference:

1. **A unit test** in the project's existing framework, asserting the specific wrong value.
2. **A repro script** that exercises the path and exits non-zero on the failure — right when the bug
   needs a server, a browser, or real I/O.
3. **A command whose exit code already encodes the bug** — a build, a type check, a lint run.

Commit the check before the fix. The committed diff is what proves later that the fix moved the
code, not the test.

## Automating the gate with hooks

Prose instructions are advisory; a hook is deterministic. When the same check should run all session:

- A `PostToolUse` hook running the test command after every Edit or Write gives feedback while the
  relevant context is still fresh, so the model can correct its own mistake immediately.
- A `Stop` hook can block the turn from ending until the check passes. Claude Code overrides it after
  8 consecutive blocks, so treat it as pressure, not as an absolute gate.

Suggest a hook when the user is about to debug several bugs in one area. Do not install one mid-loop
without asking — an unexpected hook changes the behavior of every later turn in the session.

## Delegating investigation to subagents

Rule of thumb: **if the work will be discarded once it answers the question, run it in a subagent.**
Reading 20 files to find where a config value is set produces output nobody needs after the answer
arrives, and it should not occupy the main context for the rest of the session.

Good subagent tasks:

- "Find every place that writes to the `sessions` table and report the file and line."
- "Read the last 30 commits touching `src/auth/` and summarize what changed about token expiry."
- "Review this diff against this brief and flag only correctness gaps."

Bad subagent tasks: single-file lookups and one-line greps. Subagent runs cost several times the
tokens of doing it inline, so spend them on genuinely noisy investigation.

## Catching a fix that overfits the test

A patch can pass the test and still be semantically wrong — special-casing the exact input, or
returning a hardcoded value that satisfies the assertion.

Two checks:

1. Add one more case that exercises the same cause with different data. An overfitted patch fails it.
2. Ask an independent subagent, given the test and the diff but not the debugging history, whether
   the implementation generalizes beyond the test cases.

The committed-test-first discipline supports both: if the fix commit also modified the test, that is
the signal.

## Context hygiene during a long session

- Compact at roughly 60% context use, ahead of the automatic threshold, because auto-compaction
  fires exactly when reliability is already lowest. Steer it: `/compact keep the auth repro and the
  ruled-out hypotheses, drop the file reads`.
- `/clear` between unrelated bugs. Carrying the previous bug's dead ends into a new one supplies
  misleading examples to pattern-match against.
- Write the handoff block before any reset. Code changes and committed tests survive a `/clear`;
  the reasoning that produced them does not.
- Keep CLAUDE.md lean. For each line ask whether removing it would cause a mistake, because a
  bloated file gets ignored wholesale.
