# Subagent prompt templates

One subagent handles a whole effort tier (all its findings), dispatched on the
model that tier chose. Pass the *minimum* context the tier needs — a haiku agent
handed unrelated findings or the full file set will waste tokens and may wander.
The agent runs the per-finding loop itself (apply → subset test → commit/revert);
the orchestrator owns the baseline and the final full-suite certification.

## Shared contract (every tier)

Put this in every dispatch:

> For each finding I give you, in order: apply exactly that one change and nothing
> else. Preserve behavior — this is a refactor, not a feature change. Edit only the
> lines the finding points at; do not reformat, rename, or "improve" adjacent code.
> **Never edit a test file.** The tests are the net that proves you preserved
> behavior; a test you changed to make it pass proves nothing, so a fix that only
> goes green by touching a test is a failed fix — revert it. After each change, run
> the changed file's tests and compare against the baseline with `diff_tests.py`.
> If it prints PASS, `git commit` naming the finding; if it prints REGRESSED,
> `git checkout -- <files>` to revert and move on (do not fix the fix). Report one
> status line per finding: `applied` / `reverted: <test>` /
> `could-not-apply: <reason>`.

## Low effort → haiku

Minimal context: the single finding plus the test command. The fix_example makes
this near-mechanical.

```
Finding f3 in src/calc.py (line 1):
  Issue: add() uses a mutable list default argument.
  Rule: "No mutable default arguments."
  Current:
    def add(x, acc=[]):
  Apply this fix:
    def add(x, acc=None):  # then `acc = acc or []` at top of body
Test command: python3 -m unittest discover -v
[shared contract]
```

## Medium effort → sonnet

Same finding block, but invite the agent to read the file for context since the
fix isn't fully spelled out:

```
Finding f5 in src/api/users.ts (line 12):
  Issue: SQL built by string interpolation of req params.
  Rule: "Never interpolate user input into SQL; use parameterized queries."
  Current snippet: <code_snippet>
  Suggested fix: switch to a parameterized query.
Read src/api/users.ts for the surrounding query setup before editing.
Test command: <cmd>
[shared contract]
```

## High effort → opus (only after the user approves the cost)

These ripple across files. Give the agent the finding plus permission to read
related files, and ask it to keep the change surgical despite the wider surface.

```
Finding f8 spanning src/api/*.ts:
  Issue: no shared input validator; every handler validates ad hoc or not at all.
  Rule: "Validate every handler's input against a shared schema."
  Suggested fix: introduce one shared validator and route handlers through it.
Read the handlers under src/api/ to map call sites first. Make the smallest
change that satisfies the rule without altering response behavior.
Test command: <cmd>
[shared contract]
```

## Why one tier per agent, but one commit+test per finding

Isolation is what makes the zero-regression guarantee cheap — but it lives in the
**per-finding commit + test**, not in spawning a separate process per finding. One
agent can walk a tier's queue and still commit and test each change individually,
so the git history pins exactly which change caused a regression. Batching by tier
keeps that blame trail while paying one cold start per tier instead of one per
finding, and reads a shared target file once instead of repeatedly. What you must
*not* drop is the per-finding granularity of the commit and the test — collapse
those and you lose the bisectable trail that the guarantee rests on.
