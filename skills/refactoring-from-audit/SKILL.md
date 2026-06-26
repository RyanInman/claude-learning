---
name: refactoring-from-audit
description: >-
  Apply an audit report's recommended fixes to code without changing behavior,
  verifying every change against the test suite so zero regressions slip through.
  Use whenever the user wants to act on an audit/review report — "apply the audit",
  "fix the rule-audit findings", "refactor per this report", "clean up the violations
  the audit flagged", "apply the suggested fixes but don't break anything", or pastes
  audit findings and says "make these changes safely". Loads findings, confirms a test
  harness, dispatches each fix to the cheapest capable model, re-runs tests after every
  change reverting regressions. An audit report is MANDATORY — without one this skill
  does not run; it stops and asks for a report. Do NOT use to produce an audit (that's
  the rule-audit skill) or for open-ended "just refactor this" with no report.
---

# Refactoring from an audit

Apply audit findings' fixes so code is cleaner but behaves identically. The
guarantee that earns this skill its keep: **not one test that passed before may fail
after.** Everything below makes that cheap and certain — deterministic scripts for
mechanical parts, the cheapest model per fix, a test run after every change so a
regression is caught and reverted the moment it appears, not at the end. But a green
suite only guards behavior it covers: before touching a finding, decide how it'll be
verified and build any missing safeguard first (Phase 4); after all fixes, re-confirm
every finding against the report (Phase 7). Green tests prove no regression, not that
a finding was resolved.

Scripts live in `scripts/`; run them, don't reimplement them. They keep raw findings
and test logs out of context and make before/after a deterministic set diff, not
log-reading.

## The loop at a glance

```
0. load findings      → load_findings.py        → .refactor/findings.json
1. confirm harness     → detect_harness.py + run_tests.py (baseline)
2. negotiate scope     → pick a small first slice
3. estimate effort     → estimate_effort.py      → effort + model per finding
4. plan verification   → per finding pick: existing test · new characterization
                         test · scripted check · manual style check; adversarial
                         subagent red-teams the plan → build + commit the missing
                         safeguards first, then re-baseline
5+6. one agent per shape-group, run sequentially (shared working tree): per finding →
                         apply → verify by the finding's method → diff_tests.py → green
                         keep+commit · regressed revert
7. confirm + report   → run_tests.py (full suite, gate of record) → walk the report,
                         confirm every finding actually resolved (run manual/scripted
                         checks) → write THREE report files (always):
                         reports/refactor-summary.md   (issues addressed)
                         reports/refactor-followup.md  (follow-up work remaining)
                         reports/<original>.remaining.md (audit minus fixed findings)
```

## Phase 0 — Load the findings

```bash
python3 <skill>/scripts/load_findings.py <report> --out .refactor/findings.json
```

`<report>` is a rule-audit working dir (`.rule-review/`), a findings JSON, or a
markdown report. See `references/findings-schema.md` for the canonical shape and
input details.

**No report, no work — hard requirement.** An audit report is the entry condition,
not a nicety. If the user hasn't named one, the path doesn't resolve, or the script
exits 3 (zero findings after the confidence filter), STOP. Don't proceed, improvise
findings, or "just start refactoring." Ask for an audit report (`.rule-review/`,
findings JSON, or markdown) and wait. A fix with no finding behind it has nothing to
verify against and defeats the skill.

## Phase 1 — Confirm the test harness, capture the baseline

The whole guarantee rests on a trustworthy baseline, so establish one first.

```bash
python3 <skill>/scripts/detect_harness.py <root>          # finds the command
python3 <skill>/scripts/run_tests.py --command "<cmd>" --framework <fw> > .refactor/baseline.json
```

Read `baseline.json`:

- **`ok: true`** → green baseline. Full guarantee is in force; proceed.
- **`error: true`** (command broke — missing dep, collection error) or **`ok:
  false`** (real failures already present) → the baseline is not trustworthy. You
  cannot prove zero regression against a red or broken suite.

When the baseline isn't green, surface it plainly and ask **once** with
`AskUserQuestion`: proceed with caution, or stop. If the user proceeds, every change
this run is tagged `unverified` in the final report and you say so — honesty about
what was and wasn't verified is the point. Don't silently push on.

**Pin the exact working invocation, then propagate it verbatim.** `detect_harness.py`
gives a nominal command (`yarn test`); the one that actually goes green is often
different — a runtime switch (`nvm use 22`), a flag to dodge a broken file-watcher
(`--watchman=false`), an env var. Getting there can cost several false starts. The
moment the baseline is green, record the *full* command (env prefix + version-manager
line + flags) and hand that exact string to every subagent and later gate. Re-deriving
it per agent wastes the same minutes N times, and an agent that falls back to the
default runtime reddens the tree for reasons unrelated to any fix.

## Phase 2 — Negotiate a small scope

Audits often return many findings. Applying all blind spends a pile of tokens and
still hands back a regression. **Always negotiate scope down** — default to the
smallest slice that shows value, not the largest you can defend. Goal: keep per-slice
review effort low so a human can check the result and a regression has nowhere to
hide. Propose a small first slice: highest `impact`+`risk`, or one file, or one rule.
Bound the work, show value, expand only if the user asks. State the slice and why
before touching code.

**If the user gives no scope direction, don't pick silently — surface the top 3
common-sense slices with `AskUserQuestion`.** Derive them from the loaded findings,
each kept small per the complexity rule below. Defaults to draw from:

- **Highest `impact`+`risk`** — the N findings that matter most, any file.
- **One file / one rule** — every finding in the most-violated file, or all findings
  for one rule. Tight blast radius, easy review.
- **One mechanical shape-group** — the largest low-tier shape (e.g. all
  relative-import→alias swaps). Big visible win, lowest regression risk.

Label each option with its finding count and tier so the user can weigh effort. After
they pick, state the slice and why before touching code.

**Scale batch size inversely with fix complexity.** Harder fix → fewer at once:
complex changes carry more regression risk and need closer per-finding review, so a
small batch keeps review tractable.

- **low / haiku (mechanical, fix_example present):** large batches fine — a whole
  shape-group of 20-30 import swaps is one slice.
- **medium / sonnet (reads target files, some judgment):** ~5-10 per slice, grouped
  by shape.
- **high / opus (public surface, cross-file ripple):** one or two at a time, each
  reviewed before the next. Never bulk a high-complexity queue.

Unsure of a finding's tier → treat as the higher one and take fewer.

## Phase 3 — Estimate effort

```bash
python3 <skill>/scripts/estimate_effort.py .refactor/findings.json
```

This tags each finding `low`/`medium`/`high` with the signals behind the call and the
model (haiku/sonnet/opus). Criteria in `references/effort-rubric.md` — read it if a
tier surprises. Spend the cheapest model that can plausibly do each fix: most audit
fixes are mechanical, and a wide fan-out of haiku agents beats reaching for Opus by
reflex.

**`blast_radius` is raw file size and over-tiers.** A one-line, well-specified fix
(swap an import, replace `error.message`, extract a static style) in a 300-line file
gets pushed to `high`/opus on file size alone. Don't take the tiering at face value:
re-tier by signals that track *real* effort — `snippet_lines`, `cross_file`,
`exported`, and whether a `fix_example` is present. A mechanical one-liner with a
fix_example is haiku work however big its file. Skip this and a run sends 80% of
findings to Opus, paying many times over.

## Phase 4 — Plan verification per finding, build the safeguards first

The baseline guarantee only covers behavior the suite exercises. A finding in
untested code can be "fixed" wrong with every test still green; a pure style finding
has no behavior to test at all. So before applying anything, decide per finding *how
you'll know it's resolved* and build the missing checks first — the safety net must
exist when the fix lands, not after.

Classify each finding by its verification method:

- **Behavior change, already covered** → the existing suite is the safeguard.
  Nothing to build; the per-finding run in Phase 6 catches a regression. Record
  `verify: existing-tests`.
- **Behavior change, not covered** → a green run proves nothing here. Write a
  characterization test that pins *current* behavior, confirm it passes against
  unchanged code, and commit it. Now the fix has a guard. Record
  `verify: new-test:<id>`.
- **Pure style / naming / formatting / dead-code** → no behavior to assert. Prefer a
  deterministic check: a lint rule, a type-check, or a `grep` that must return zero
  hits (old name gone, banned pattern absent). That check is scriptable and runs in
  the gate. Record `verify: check:<cmd>`.
- **Style with no automatable check** → mark it for a human eyeball in the final pass
  and write down exactly what to inspect. Record `verify: manual:<what to look at>`.

Before building anything, **dispatch an adversarial subagent to red-team the
verification plan** (sonnet; template in `references/subagent-prompts.md`). Hand it
the slice's findings with their proposed `verify` methods; have it attack each: a
`verify: existing-tests` whose finding touches a path the suite never exercises (green
run proves nothing); a `new-test` that pins a side effect instead of the finding's
behavior, or still passes if the fix is reverted; a `check:<grep>` matching too
loosely (old name gone from one file, live in another) or too tightly (misses a
variant); a `manual` flag hiding a scriptable check. It returns, per finding,
*accepted* or a concrete weakness plus a stronger method. Apply its upgrades to the
`verify` fields first — cheapest point to catch a verification gap, since once a
safeguard is built and committed a false sense of coverage rides along. You own the
final call; an adversary that flags nothing on a non-trivial slice is itself suspect.

Build and commit every new test and check script *before* dispatching the slice's
fixes. Then re-run the full suite and overwrite `baseline.json` — the new
characterization tests are now part of the green baseline, so a later regression in
them is caught like the rest.

Record this in `findings.json` (a `verify` field per finding) so tier agents know how
to self-check and the final pass knows what to re-confirm.

## Phase 5 — Dispatch each fix by tier

Set up a checkpoint branch first so each kept change is its own commit (bisectable
history, easy revert; never refactor straight on `main`):

```bash
git checkout -b refactor/from-audit
```

Then dispatch **one subagent per group, not one per finding**. Each agent walks its
group's queue and runs the full per-finding loop (Phase 6): apply one change, verify
by the finding's method, commit if green / revert if regressed, next. Per-finding
commits already give bisectable blame, so batching a group into one agent keeps the
isolation while paying one cold start instead of N and reading the shared file once.
Templates and contract in `references/subagent-prompts.md`.

**Group by fix-shape, not just effort tier.** Findings cluster into a few mechanical
shapes — relative-import→alias, `error.message`→`getErrorMessage`,
`new Date()`→`DateTime`, inline-style→`StyleSheet`. A shape-group shares one fix
recipe, one `verify` method, one model, so the agent applies the same edit N times
without context-switching, and you pick the cheapest model the shape needs (30 import
swaps is haiku, not opus). Effort tier picks the model; shape picks the queue.

- **low → haiku.** The whole low queue + each fix_example + the test command. Mechanical.
- **medium → sonnet.** The medium queue, plus permission to read the target files.
- **high → opus, but ask first.** High-effort fixes touch public surfaces or ripple
  across files, and Opus costs more. Before dispatching the high queue, use
  `AskUserQuestion` to let the user approve the spend, skip, or defer. Don't reach for
  the expensive model on their behalf.

**Run shape-group agents sequentially, one at a time, against the shared working
tree.** Never run fix agents concurrently. Agents in one tree clash even on disjoint
files: they share one `.git/index` (parallel commits collide on `index.lock`) and one
set of working files (one agent's `git add -A` sweeps another's half-written file into
its commit; one agent's type-check or lint sees another's mid-edit state and fails for
unrelated reasons). Serial dispatch sidesteps it — dispatch a group, let it finish and
commit, then the next. Per-finding commits keep history bisectable regardless of
order, so serializing loses nothing. Keep each group's batched gate (Phase 6) cheap so
serial wall-clock stays low.

Each agent edits only its findings' lines (no drive-by edits) and returns a
per-finding status summary for the report.

## Phase 6 — Verify and checkpoint, per finding

This is the engine each tier agent runs for every finding in its queue. Gate each
applied change by the finding's `verify` method, not by reflex:

- `existing-tests` or `new-test` → run only the **changed file's tests** for fast
  feedback, not the whole suite (command below).
- `check:<cmd>` → run that command; zero hits / clean exit is the gate.
- `manual:<…>` → no automated gate here. Apply, commit, and leave it flagged for the
  Phase 7 inspection; don't block the queue on a human check.

**When the gate is a slow whole-project check, batch it.** A type-check or lint over a
large project runs tens of seconds and re-checks the *whole* project after a one-line
edit — running it per finding across a long mechanical queue dominates the clock. For
such gates on mechanical shapes: commit each finding (blame stays per-finding) but run
the heavy check **once at the end of the shape-group**; on failure, the per-finding
commits let you bisect to the culprit, revert just that one, re-run. Zero-regression
guarantee and blame trail kept at a fraction of the cost. (If a pre-commit hook re-runs
that same check every commit, use `git commit --no-verify` — the hook is redundant with
the gate you own; paying it N times is waste.) Behavior-risk shapes (untested code,
error paths) stay per-finding — batching is only for cheap, uniform, type-checkable
edits.

For the test-gated findings:

```bash
python3 <skill>/scripts/run_tests.py --command "<cmd narrowed to the file's tests>" --framework <fw> > .refactor/after.json
python3 <skill>/scripts/diff_tests.py .refactor/baseline.json .refactor/after.json
```

`diff_tests.py` prints `PASS` (exit 0) or the new failing ids (exit 2), so the
gate costs one line instead of a JSON blob in context. Then:

- **PASS** → keep it. `git add -A && git commit` with a message naming the finding.
  Record `status: applied` (or `unverified` if the baseline wasn't green). Next
  finding, against this committed state.
- **REGRESSED** → the fix broke something. Revert it (`git checkout -- <files>`, since
  prior findings are committed) and record `status: reverted` with the failing test.
  Don't "fix the fix" inline — that starts scope creep and second regressions. Leave
  it for the user.

The subset run is the fast inner loop, not the guarantee. The **Phase 7 full-suite run
is the gate of record**: a change can break a test far from the file it touched, and
that surfaces there. Since every kept finding is its own commit, a regression caught
only at the end still bisects to its cause — speed and blame trail both kept.

## Phase 7 — Final report and the verdict

First, the confirmation pass. Walk the original report finding by finding and confirm
each marked applied actually holds — run the `check:` commands, do the `manual:`
inspections now, spot-check that each `new-test` still asserts its finding's behavior.
This the suite can't do for you: green tests prove nothing regressed, but a fix can be
reverted, half-applied, or cosmetic-only with the suite green. Any applied finding that
doesn't hold gets flagged, not counted done.

Then write the recorded results to `.refactor/results.json` (schema in
`render_refactor_report.py`'s header: `branch`, `baseline`, `final`, and a `results`
list), capture one last full run as `final`, then:

```bash
python3 <skill>/scripts/run_tests.py --command "<cmd>" --framework <fw> > .refactor/final.json
python3 <skill>/scripts/render_refactor_report.py .refactor/results.json --out reports/refactor-summary.md
```

The script computes the zero-regression verdict by diffing `final` against `baseline`,
exiting 2 if any regression survived. Report it plainly: how many findings applied,
reverted, skipped, or unverified, and the PASS/FAIL line — backed by the actual final
test output, not an assertion it "should" pass. If anything regressed, say so first.

**Always write three report files under `reports/`, even on a clean run.** Each serves
a different reader, so the next session can pick up without re-deriving state. Write all
three every time; if a section is empty, say so rather than omit the file.

1. **`reports/refactor-summary.md` — issues addressed.** The `render_refactor_report.py`
   output above. Every finding marked `applied` (and confirmed above), with its file,
   shape, model, verify method, and PASS/FAIL verdict. The record of what *this* session
   changed.

2. **`reports/refactor-followup.md` — follow-up work remaining.** Everything still owed,
   so nobody reconstructs it: findings `reverted` (with the failing test and why),
   `skipped`/`deferred` (with reason — e.g. high-tier opus queue the user declined,
   untested behavior needing a characterization test first), any finding the
   confirmation pass flagged as applied-but-not-holding, and report slices never
   attempted this run. Give each a one-line next step (the model, the safeguard to
   build, or the decision needed) so it's directly actionable.

3. **`reports/<original-report-name>.remaining.md` — the audit minus what's fixed.**
   Copy the original report and remove every finding now `applied` and confirmed,
   preserving its structure (summary table rows *and* detail blocks both pruned). Update
   counts/headers to match. This is the input a future `refactoring-from-audit` run loads
   to continue where this stopped — re-running must not re-surface a fixed finding. Leave
   `reverted`/`skipped` findings *in* (still open work).

   **Prune by `(file, title)`, never by row number.** `load_findings.py` finding-ids
   (`f1..fN`) do NOT match the report's summary-table `#` column — the id is assigned in
   load order, the `#` is the audit's ranking, and they diverge (e.g. `f39` can be table
   row 41). Match rows to remove by their `(file, issue)` cells — the same key used to
   prune detail blocks — so both stay consistent. Dropping rows by
   `int(#) == int(id[1:])` deletes the wrong rows and leaves fixed findings in; verify
   zero fixed titles remain after pruning.

## Gotchas

- **A green baseline is non-negotiable for the guarantee.** `error: true` from
  `run_tests.py` means the command broke (e.g. test runner not installed), not zero
  failures. Treat it as no-harness, not green.
- **Green tests ≠ finding resolved.** The suite only guards behavior it covers, and a
  fix can be reverted or half-applied with tests passing. Untested findings get a
  characterization test first (Phase 4); every finding is re-confirmed by its own
  verify method in Phase 7, not by the suite alone.
- **Per-test ids aren't always recoverable.** For generic runners (make, gradle, mvn)
  `ids_reliable` is false and regression detection falls back to exit code / failed
  count. Works, but you can't name the broken test — mention that limit if you hit it.
- **Don't batch findings into one subagent.** You lose which change regressed — the
  entire reason for the per-finding loop.
- **Markdown reports are lossy.** No code_snippet or fix_example, so those findings
  route to a pricier model. Feed rule-audit JSON when you have it.
- **The markdown loader can under-extract.** Even when a markdown report carries
  per-finding bodies (current snippet, suggested fix, file:line under each heading),
  `load_findings.py` may flatten them to title-only. Before Phase 3, eyeball one finding
  in `findings.json` against the report; if rich bodies exist in the report but not the
  JSON, re-parse the markdown to recover `code_snippet`/`fix_example`/`line` first. Those
  fields drop findings to cheaper models and hand each agent the exact diff — skip it and
  the run pays in model cost and agent guesswork.
- **The report's suggested fix is a hint, not ground truth.** Audit fix_examples can name
  a path alias or symbol that doesn't exist in this repo. The per-finding gate (a
  type-check) catches it — each agent treats fix_example as a start and lets the gate, not
  the report, have the final say.
- **Bulk literal edits: use Python `str.replace`, not `perl`/`sed`.** Audit fixes
  routinely touch text with `@` (aliases like `@band`) and `$` (template literals like
  `${error}`). In `perl -pe "s/.../$new/"` and double-quoted shells, `@word`/`$word`
  interpolate as array/scalar — eating the alias sigil so `@app_types/Foo` becomes
  `/Foo`. The type-check gate catches the wreckage, but only after an apply/revert/redo
  cycle. Default to a Python helper doing a literal `s.replace(old, new)` with a
  uniqueness assert; reach for `perl`/`sed` only on payloads with no `@`/`$`.
- **Clean up `.refactor/` when done** (safe to gitignore). Keep `reports/`.
