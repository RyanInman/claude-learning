---
name: refactoring-from-audit
description: >-
  Apply an audit report's recommended fixes to code without changing behavior,
  verifying every change against the test suite so zero regressions slip through.
  Use this whenever the user wants to act on an audit/review report — "apply the
  audit", "fix the rule-audit findings", "refactor per this report", "clean up the
  violations the audit flagged", "apply the suggested fixes but don't break
  anything". Do NOT use this to produce an audit (that's the rule-audit skill) or
  for open-ended "just refactor this" with no report — it needs a report and will
  ask for one.
---

# Refactoring from an audit

Take a list of audit findings and apply their fixes so the code is cleaner but
behaves identically. The guarantee that earns this skill its keep: **not one test
that passed before may fail after.** Everything below exists to make that cheap
and certain — deterministic scripts for the mechanical parts, the cheapest model
that can do each fix, and a test run after every single change so a regression is
caught and reverted the moment it appears, not at the end.

That guarantee is a property of the **test net, not the model.** So the order is
inverted from how it feels natural: lock behavior first, then change structure.
A green, trustworthy suite is the precondition for every fix below — and if one
doesn't exist, the right first move is to build one (Phase 1), not to refactor
blind. The net's completeness is also the ceiling: a fix can only be proven safe
for behavior the tests actually cover.

Scripts live in `scripts/`; run them, don't reimplement them. They keep raw
findings and test logs out of context and make the before/after comparison a
deterministic set diff instead of log-reading.

## The loop at a glance

```
0. load findings      → load_findings.py        → .refactor/findings.json
1. confirm harness     → detect_harness.py + run_tests.py (baseline)
2. negotiate scope     → pick a small first slice
3. estimate effort     → estimate_effort.py      → effort + model per finding
4+5. one agent per tier (sequential): per finding → apply → subset tests →
                   diff_tests.py → green keep+commit · regressed revert
6. final report        → run_tests.py (full suite, gate of record)
                       → render_refactor_report.py → reports/refactor-summary.md
```

## Phase 0 — Load the findings

```bash
python3 <skill>/scripts/load_findings.py <report> --out .refactor/findings.json
```

`<report>` is a rule-audit working dir (`.rule-review/`), a findings JSON, or a
markdown report. See `references/findings-schema.md` for the canonical shape and
input details.

**No report, no work.** If the user hasn't pointed you at one, or the script exits
3 (zero findings after the confidence filter), stop and ask what they want
refactored. Do not guess fixes from a vague request — a fix with no finding behind
it has nothing to verify it against and defeats the skill.

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

When the baseline isn't green, you can't prove zero regression yet — but
"proceed unverified" is the weakest of three answers, not the default. Surface it
plainly and ask **once** with `AskUserQuestion`:

- **Build a net first (recommended when behavior is characterizable).** Write
  characterization tests that lock current behavior, get them green, then refactor
  under a real net. This is the inversion that makes the guarantee real instead of
  aspirational. See `references/characterization-net.md` for the fast path
  (approval/golden-master), what to scrub, and framework tooling. After the net is
  green, recapture the baseline and proceed with the full guarantee in force.
- **Proceed with caution.** Every change this run is tagged `unverified` in the
  final report and you say so — honesty about what was and wasn't verified is the
  point. Don't silently push on.
- **Stop.**

Hard stop regardless of the answer: if behavior can't be characterized, or the
code touches auth, crypto, payments, or sensitive data, don't make direct edits —
use the model for analysis only and say why. `references/characterization-net.md`
explains the line.

## Phase 2 — Negotiate a small scope

Audits often return many findings. Applying all of them blind is how you spend a
pile of tokens and still hand back a regression. Propose a small first slice and
confirm it: highest `impact`+`risk` first, or one file, or one rule. Bound the
work, show value, expand if the user wants more. State the slice you're taking and
why before you touch code.

## Phase 3 — Estimate effort

```bash
python3 <skill>/scripts/estimate_effort.py .refactor/findings.json
```

This tags each finding `low`/`medium`/`high` with the signals behind the call and
the model to use (haiku/sonnet/opus). The criteria are in
`references/effort-rubric.md` — read it if a tier looks surprising. The point is to
spend the cheapest model that can plausibly do each fix, because most audit fixes
are mechanical and a wide fan-out of haiku agents is far cheaper than reaching for
Opus by reflex.

## Phase 4 — Dispatch each fix by tier

Set up a checkpoint branch first so each kept change is its own commit (bisectable
history, easy revert; never refactor straight on `main`):

```bash
git checkout -b refactor/from-audit
```

Then dispatch **one subagent per effort tier, not one per finding**. Each agent
walks its tier's queue and runs the full per-finding loop itself (Phase 5): apply
one change, test, commit if green / revert if regressed, next. Per-finding commits
already give bisectable blame, so batching a tier into one agent keeps the same
isolation while paying one cold start instead of N and reading a shared file once
instead of N times. Templates and the contract are in
`references/subagent-prompts.md`.

- **low → haiku.** The whole low queue + each fix_example + the test command. Mechanical.
- **medium → sonnet.** The medium queue, plus permission to read the target files.
- **high → opus, but ask first.** High-effort fixes touch public surfaces or
  ripple across files, and Opus costs more. Before dispatching the high queue, use
  `AskUserQuestion` to let the user approve the spend, skip, or defer. Don't reach
  for the expensive model on their behalf.

Run the tiers **sequentially** — they share one working tree, so concurrent agents
would clash. Each agent edits only its findings' lines (no drive-by edits) and
returns a per-finding status summary for the report.

## Phase 5 — Verify and checkpoint, per finding

This is the engine each tier agent runs for every finding in its queue. After
applying one change, gate it — but run only the **changed file's tests** for fast
feedback, not the whole suite:

```bash
python3 <skill>/scripts/run_tests.py --command "<cmd narrowed to the file's tests>" --framework <fw> > .refactor/after.json
python3 <skill>/scripts/diff_tests.py .refactor/baseline.json .refactor/after.json
```

`diff_tests.py` prints `PASS` (exit 0) or the new failing ids (exit 2), so the
gate costs one line instead of a JSON blob in context. Then:

- **PASS** → keep it. `git add -A && git commit` with a message naming the finding.
  Record `status: applied` (or `unverified` if the baseline wasn't green). Next
  finding, against this committed state.
- **REGRESSED** → the fix broke something. Revert it (`git checkout -- <files>`,
  since prior findings are already committed) and record `status: reverted` with
  the failing test. Don't "fix the fix" inline — that's how scope creep and second
  regressions start. Leave it for the user.

The subset run is the fast inner loop, not the guarantee. The **Phase 6
full-suite run is the gate of record**: a change can break a test far from the file
it touched, and that surfaces there. Because every kept finding is its own commit,
a regression caught only at the end still bisects to the finding that caused it —
so you keep both the speed and the blame trail.

## Phase 6 — Final report and the verdict

Write the results you recorded to `.refactor/results.json`
(schema in `render_refactor_report.py`'s header: `branch`, `baseline`, `final`,
and a `results` list), capture one last full run as `final`, then:

```bash
python3 <skill>/scripts/run_tests.py --command "<cmd>" --framework <fw> > .refactor/final.json
python3 <skill>/scripts/render_refactor_report.py .refactor/results.json --out reports/refactor-summary.md
```

The script computes the zero-regression verdict by diffing `final` against
`baseline` and exits 2 if any regression survived. Report the verdict to the user
plainly: how many findings applied, reverted, skipped, or left unverified, and the
PASS/FAIL line — backed by the actual final test output, not an assertion that it
"should" pass. If anything regressed, say so first.

## Gotchas

- **A green baseline is non-negotiable for the guarantee.** `error: true` from
  `run_tests.py` means the command itself broke (e.g. test runner not installed),
  not that there are zero failures. Treat it as no-harness, not as green. No net?
  Build one (Phase 1, `references/characterization-net.md`) before refactoring,
  don't proceed blind.
- **The guarantee only covers what tests exercise.** A fix can silently change
  behavior on an uncovered path and every test still passes. The net's
  completeness is the real ceiling — say so when coverage is thin, and for a
  high-stakes module consider mutation testing once before refactoring to confirm
  the net actually catches faults (coverage % alone lies). Details in
  `references/characterization-net.md`.
- **Per-test ids aren't always recoverable.** For generic runners (make, gradle,
  mvn) `ids_reliable` is false and regression detection falls back to exit code /
  failed count. It still works, but you can't name the broken test — mention that
  limitation if you hit it.
- **Don't batch findings into one subagent.** You lose the ability to say which
  change regressed, which is the entire reason for the per-finding loop.
- **Markdown reports are lossy.** They carry no code_snippet or fix_example, so
  those findings route to a stronger (pricier) model. Feed rule-audit JSON when you
  have it.
- **Clean up `.refactor/` when done** (safe to gitignore). Keep `reports/`.
