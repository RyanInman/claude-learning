---
name: refactoring-from-audit
description: >-
  Apply an audit or rule-review report's recommended fixes to a scope of files WITHOUT changing
  behavior, re-running tests after every change so zero regressions slip through. Two independent
  inputs: a report (the findings) and a scope (the files); user may bring either, both, or neither.
  Use whenever someone wants to act on review findings safely: 'refactor this file', 'clean up
  src/api/foo.ts against our rules', 'apply our rules to these files', 'fix the rule-audit findings
  in this dir', 'refactor per this report', 'apply the suggested fixes but don't break anything', or
  pastes findings and says 'make these changes safely'. Routes each fix to the cheapest capable
  model, reverting anything that reddens the suite. Scope but no report: offers to generate one via
  rule-audit. Neither: hands off to rule-audit for a full audit, then continues. Do NOT use to
  produce an audit (that's rule-audit), or for open-ended 'just refactor this' with no report and no
  scope (also rule-audit).
---

# Refactoring from an audit

Apply an audit report's findings to a scope (file or list of files): code gets cleaner, behavior
stays identical. Two **independent** inputs — a **report** (findings to act on) and a **scope**
(files to act on). User arrives with either, both, or neither; Phase 0 routes a 2x2 and always
lands on a terminal action. No cell stops empty or invents findings.

**The guarantee: not one test that passed before may fail after.** Zero regression. Everything
below makes that cheap and certain — deterministic scripts for mechanical parts, cheapest capable
model per fix, a test run after *every* change so a regression is caught and reverted the moment it
appears, not at the end of a queue.

A green suite only guards behavior it covers. Two consequences run through the workflow:

- Before touching a finding, decide how its fix is verified and **build any missing safeguard
  first** (Phase 4). A finding in untested code can be "fixed" wrong with every test green.
- **Green tests prove no regression — not that a finding resolved.** A fix can be reverted,
  half-applied, or cosmetic-only with the suite green, so re-confirm every finding against the
  report after all fixes (Phase 7).

Scripts live in `scripts/`. **Run them; don't reimplement them.** They keep raw findings and test
logs out of context and turn before/after into a deterministic set diff instead of log-reading.
Inventory at bottom.

## The loop at a glance

```
0. resolve inputs    report? (user path · reports/rule-adherence-*.md · .rule-review/)
                     scope?  (named file/dir) ── route the 2x2
                     neither → confirm → rule-audit (full) → re-enter as Case 2
1. get findings      load_findings.py --files <scope>            → scoped findings.json
                     (no report) generate via rule-audit first, then load
                     map scope → .claude/rules/ via rule-audit map_rules.py   (rules ctx)
2. confirm harness    detect_harness.py + run_tests.py            → baseline.json
   negotiate scope    if scoped set is large → AskUserQuestion a smaller first slice
3. estimate effort    estimate_effort.py                         → tier + model per finding
4. plan verification  per-finding verify method + adversarial red-team, build safeguards first
5+6. dispatch + gate  one agent per shape-group, per-finding gate (apply→verify→commit/revert)
7. confirm + report   full suite (gate of record) + 3 report files
```

## Phase 0 — Resolve inputs and route

Detect each input independently, then route:

| | **scope given** | **no scope** |
|---|---|---|
| **report present** | **Case 1 (ideal)** — load report scoped to scope; proceed. Negotiate down only if the scoped set is large. | **Case 2** — negotiation asks for a scope, *suggesting candidate slices derived from the loaded report*; then load `--files <chosen scope>`. |
| **no report** | **Case 3** — notify there's no report; offer `rule-audit` on the scoped files first; then load scoped. | **Case 4** — the only "nothing to do" path. Confirm, run `rule-audit` on the full audit universe, re-enter as **Case 2**. |

**Scope?** User named file(s) or a dir? Resolve to concrete repo-relative paths — the form
`load_findings.py --files` and `map_rules.py` expect. A dir expands to its files. Endpoint/route
scopes unsupported (no endpoint→file map); take the file(s) behind the endpoint instead. Clean
extension point, not built.

**Report?** A user-supplied path, or a known location: `reports/rule-adherence-high-medium.md`,
`reports/rule-adherence-with-low.md`, or a `.rule-review/` working dir (`batch-*.json`). Exactly
what `rule-audit` produces and `load_findings.py` consumes.

## Phase 1 — Get findings for the scope, plus rules context

Two inputs feed the fixes: the **findings** for the scope (what to change) and the **rules that
apply** (the standard each change is held to). Findings come per the routed case; rules context is
gathered the same way every time.

**Cases 1 & 2 — report present.** Load the report, narrowed to the scope:

```bash
python3 <skill>/scripts/load_findings.py <report> --files <scope...> --out .refactor/findings.json
```

`<report>` may be a rule-audit working dir (`.rule-review/`), findings JSON, markdown report, or
user-supplied path. `--files` narrows to scope deterministically, keeping raw findings out of
context. Findings shape and input details: `references/findings-schema.md`.

**Case 2** has no scope yet: load the *full* report first (no `--files`) so negotiation can derive
candidate scopes, then re-load `--files <chosen scope>` once picked.

**Case 3 — scope, no report.** Notify plainly there's no report, then offer to generate one with
`rule-audit` scoped to the files:

- `--mode audit --path <narrowest common-ancestor>` (non-mutating), or
- stage the files and run `--mode staged` for a tidy file list with a clean index.

If the common ancestor is the repo root (scope spans top-level dirs), prefer staged or one run per
subtree — don't audit the whole repo to refactor a few files. Then load the produced report scoped
with the same `load_findings.py` command.

**Rules context (all cases).** Map scope files to their governing rules so fix agents hold each
change to the standard the audit used. Reuse rule-audit's mapper:

```bash
python3 <rule-audit>/scripts/map_rules.py --mode audit --path <common-ancestor> --out .refactor/rule-map.json
```

Read `assignments` for the scope files, collect the union of applicable rule files, hand them to
the Phase 5 fix agents alongside each finding's `rule_text`/`fix_example`. **Soft dependency:**
rule-audit ships with this skill in this repo. If not installed, fall back in-context — glob
`.claude/rules/*.md` and match each rule's `paths:` frontmatter against the scope files.

**No finding behind a fix = nothing to verify.** If a chosen path yields zero findings
(`load_findings.py` exits 3, or the scoped set is empty) and the user declines to provide or
generate a report, **STOP**. A fix with no finding has nothing to verify against and defeats the
skill. Never stop silently on an empty scope, never invent findings — route to the offer above;
only an explicit user decline ends the run.

## Phase 2 — Confirm the test harness, capture the baseline

The guarantee rests on a trustworthy baseline; establish one before touching code.

```bash
python3 <skill>/scripts/detect_harness.py <root>                 # finds the command
python3 <skill>/scripts/run_tests.py --command "<cmd>" --framework <fw> > .refactor/baseline.json
```

Read `baseline.json`:

- **`ok: true`** → green baseline. Full guarantee in force; proceed.
- **`error: true`** (command broke — missing dep, collection error) or **`ok: false`** (real
  failures present) → baseline not trustworthy. You cannot prove zero regression against a red or
  broken suite.

When not green, surface it plainly and ask **once** via `AskUserQuestion`: proceed with caution, or
stop. If proceeding, every change this run is tagged `unverified` in the report and you say so.
Don't silently push on.

**Pin the exact working invocation, propagate it verbatim.** `detect_harness.py` gives a nominal
command (`yarn test`); the one that goes green is often different — a runtime switch (`nvm use
22`), a flag to dodge a broken file-watcher (`--watchman=false`), an env var. Getting there costs
false starts. The moment baseline is green, record the **full** command (env prefix +
version-manager line + flags) and hand that exact string to every subagent and later gate.
Re-deriving per agent wastes the same minutes N times; an agent on the default runtime reddens the
tree for unrelated reasons.

## Negotiate the scope

**Conditional on size.** A small scoped set is one slice — proceed, no prompt. Only when the set is
**large** (judge against the batch-size table below, not a magic number) present an
`AskUserQuestion` menu of candidate smaller slices. Which menu depends on the case:

- **No scope yet (Case 2, or post-Case-4)** → present candidate slices *derived from the loaded
  findings*: most-violated file, highest `impact`+`risk`, largest mechanical shape-group — each
  labeled with finding count + tier. The pick becomes the scope; re-load `load_findings.py --files
  <pick>`. This *is* the "ask for a scope" step.
- **Scope given but large (Cases 1 & 3)** → present candidate *sub-slices* the same way; the pick
  narrows the working set.
- **Scope given, already a tight slice** → proceed, no prompt.

State the chosen slice and why before touching code, so a human can review each slice and a
regression has nowhere to hide.

**Scale batch size inversely with fix complexity** — a harder fix carries more regression risk and
needs closer per-finding review, so take fewer at once. This table is the yardstick for "large" and
how to slice:

| tier / model | character | batch size |
|---|---|---|
| **low / haiku** | mechanical, `fix_example` present | large — a whole shape-group of 20-30 import swaps is one slice |
| **medium / sonnet** | reads scope files, some judgment | ~5-10 per slice, grouped by shape |
| **high / opus** | public surface, cross-file ripple | one or two at a time, each reviewed before the next; never bulk a high queue |

Unsure of a finding's tier → treat it as the higher one, take fewer.

## Phase 3 — Estimate effort

```bash
python3 <skill>/scripts/estimate_effort.py .refactor/findings.json
```

Tags each finding `low`/`medium`/`high` with the signals behind the call and the model
(haiku/sonnet/opus). Criteria in `references/effort-rubric.md` — read it if a tier surprises you.
Spend the cheapest model that can plausibly do each fix: most audit fixes are mechanical; a wide
haiku fan-out beats reaching for Opus by reflex.

**`blast_radius` is raw file size and over-tiers.** A one-line, well-specified fix (swap an import,
replace `error.message`, extract a static style) in a 300-line file gets pushed to `high`/opus on
size alone. Don't take tiering at face value — re-tier by signals that track *real* effort:
`snippet_lines`, `cross_file`, `exported`, and whether a `fix_example` is present. A mechanical
one-liner with a `fix_example` is haiku work however big its file. Skip this and a run sends 80% of
findings to Opus, paying many times over.

## Phase 4 — Plan verification per finding, build the safeguards first

The baseline only covers behavior the suite exercises. A finding in untested code can be "fixed"
wrong with every test green; a pure-style finding has no behavior to test at all. Before applying
anything, decide per finding *how you'll know it's resolved* and build the missing checks first —
**the safety net must exist when the fix lands, not after.**

Classify each finding by verification method:

| finding type | safeguard | record |
|---|---|---|
| Behavior change, already covered | existing suite — Phase 6's per-finding run catches a regression | `verify: existing-tests` |
| Behavior change, not covered | characterization test pinning *current* behavior; confirm it passes against unchanged code, commit it | `verify: new-test:<id>` |
| Pure style / naming / formatting / dead-code | deterministic check — lint rule, type-check, or `grep` that must return zero hits (old name gone, banned pattern absent) | `verify: check:<cmd>` |
| Style with no automatable check | flag for a human eyeball in the final pass; write down exactly what to inspect | `verify: manual:<what to look at>` |

**A check is only a safeguard if it currently fails.** A `grep` that must return zero hits proves
nothing if it already matched zero *before* the fix; a lint or type-check that already passes can't
witness the fix either. Confirm every `check:` is **red against unchanged code first** — the mirror
of a characterization test (which must pass against unchanged code). Red-then-green for checks too.
If a check can't be made to fail pre-fix, it isn't verifying the finding; pick a stronger one.

**Red-team the plan before building anything.** Dispatch an adversarial subagent (sonnet; template
in `references/subagent-prompts.md`) with the slice's findings and proposed `verify` methods. Have
it attack each:

- an `existing-tests` whose finding touches a path the suite never exercises (green proves
  nothing);
- a `new-test` pinning a side effect instead of the finding's behavior, or still passing if the fix
  is reverted;
- a `check:<grep>` already returning zero *before* the fix (green proves nothing), matching too
  loosely (old name gone from one file, still live in another), or too tightly (misses a variant);
- a `manual` flag hiding a scriptable check.

It returns, per finding, *accepted* or a concrete weakness plus a stronger method. Apply its
upgrades to the `verify` fields **first** — the cheapest point to catch a verification gap, since
once a safeguard is built and committed a false sense of coverage rides along. You own the final
call; an adversary flagging nothing on a non-trivial slice is itself suspect.

Then build and commit every new test and check script **before** dispatching the slice's fixes.
Re-run the full suite and overwrite `baseline.json` — the new characterization tests are now part
of the green baseline, so a later regression in them is caught like any other. Record the `verify`
method per finding in `findings.json` so tier agents know how to self-check and the final pass knows
what to re-confirm.

## Phase 5 — Dispatch each fix by tier

Set up a checkpoint branch first, so each kept change is its own commit (bisectable history, easy
revert) and you never refactor straight on `main`:

```bash
git checkout -b refactor/from-audit
```

Then dispatch **one subagent per group, not one per finding.** Each agent walks its group's queue
running the full per-finding loop (Phase 6): apply one change, verify by the finding's method,
commit if green / revert if regressed, then the next. Per-finding commits already give bisectable
blame, so batching a group into one agent keeps the isolation while paying one cold start instead of
N and reading the shared file once. Templates and the agent contract: `references/subagent-prompts.md`.

**Group by fix-shape, not just effort tier.** Findings cluster into a few mechanical shapes —
relative-import→alias, `error.message`→`getErrorMessage`, `new Date()`→`DateTime`,
inline-style→`StyleSheet`. A shape-group shares one fix recipe, one `verify` method, one model, so
the agent applies the same edit N times without context-switching. **Effort tier picks the model;
shape picks the queue.**

- **low → haiku.** Whole low queue + each `fix_example` + the test command. Mechanical.
- **medium → sonnet.** Medium queue, plus permission to read the scope files.
- **high → opus, but ask first.** High-effort fixes touch public surfaces or ripple across files,
  and Opus costs more. Before dispatching the high queue, use `AskUserQuestion` to approve the
  spend, skip, or defer. Don't reach for the expensive model on the user's behalf.

Across all tiers, hand each agent the applicable `.claude/rules/` files from Phase 1 alongside each
finding's `rule_text`/`fix_example` — so a fix is held to the rule that flagged it, not just the
snippet.

**Run shape-group agents sequentially, one at a time, against the shared working tree. Never run fix
agents concurrently.** Agents in one tree clash even on disjoint files: they share one `.git/index`
(parallel commits collide on `index.lock`) and one set of working files (one agent's `git add -A`
sweeps another's half-written file into its commit; one agent's type-check or lint sees another's
mid-edit state and fails for unrelated reasons). Serial dispatch sidesteps it all — dispatch a
group, let it finish and commit, then the next. Per-finding commits keep history bisectable
regardless of order, so serializing loses nothing. Keep each group's batched gate (Phase 6) cheap so
serial wall-clock stays low.

Each agent edits only its findings' lines — no drive-by edits — and returns a per-finding status
summary for the report.

## Phase 6 — Verify and checkpoint, per finding

The engine each tier agent runs for every finding in its queue. **Gate each applied change by the
finding's `verify` method, not by reflex:**

- `existing-tests` / `new-test` → run only the **changed file's tests** for fast feedback, not the
  whole suite (command below).
- `check:<cmd>` → run it; zero hits / clean exit is the gate.
- `manual:<…>` → no automated gate. Apply, commit, leave it flagged for Phase 7 inspection; don't
  block the queue on a human check.

**When the gate is a slow whole-project check, batch it.** A type-check or lint over a large project
runs tens of seconds and re-checks the *whole* project after a one-line edit — running it per
finding across a long mechanical queue dominates the clock. For such gates on mechanical shapes:
commit each finding (blame stays per-finding) but run the heavy check **once at the end of the
shape-group**; on failure, the per-finding commits let you bisect to the culprit, revert just that
one, re-run. If a pre-commit hook re-runs that check on every commit, use `git commit --no-verify` —
the hook is redundant with the gate you own, so paying it N times is waste. Behavior-risk shapes
(untested code, error paths) stay **per-finding** — batching is only for cheap, uniform,
type-checkable edits.

For test-gated findings:

```bash
python3 <skill>/scripts/run_tests.py --command "<cmd narrowed to the file's tests>" --framework <fw> > .refactor/after.json
python3 <skill>/scripts/diff_tests.py .refactor/baseline.json .refactor/after.json
```

`diff_tests.py` prints `PASS` (exit 0) or the new failing ids (exit 2), so the gate costs one line,
not a JSON blob in context. Then:

- **PASS** → keep it. `git add -A && git commit` with a message naming the finding. Record `status:
  applied` (or `unverified` if baseline wasn't green). Next finding, against this committed state.
- **REGRESSED** → revert (`git checkout -- <files>`, since prior findings are committed) and record
  `status: reverted` with the failing test. Don't "fix the fix" inline — that starts scope creep and
  second regressions. Leave it for the user.

The subset run is the fast inner loop, not the guarantee. The **Phase 7 full-suite run is the gate
of record**: a change can break a test far from the file it touched, and that surfaces there. Since
every kept finding is its own commit, a regression caught only at the end still bisects to its cause.

## Phase 7 — Final report and the verdict

**Confirmation pass first.** Walk the original report finding by finding and confirm each one marked
applied actually holds — run the `check:` commands, do the `manual:` inspections now, spot-check that
each `new-test` still asserts its finding's behavior. The suite can't do this: green tests prove
nothing regressed, but a fix can be reverted, half-applied, or cosmetic-only with the suite green.
Any applied finding that doesn't hold gets flagged, not counted done.

Then record results to `.refactor/results.json` (schema in `render_refactor_report.py`'s header:
`branch`, `baseline`, `final`, `results` list), capture one last full run as `final`, and render:

```bash
python3 <skill>/scripts/run_tests.py --command "<cmd>" --framework <fw> > .refactor/final.json
python3 <skill>/scripts/render_refactor_report.py .refactor/results.json --out reports/refactor-summary.md
```

The script computes the zero-regression verdict by diffing `final` against `baseline`, exiting 2 if
any regression survived. Report plainly: how many findings applied / reverted / skipped /
unverified, and the PASS/FAIL line — backed by the actual final test output, not an assertion it
"should" pass. If anything regressed, say so first.

**Always write three report files under `reports/`, even on a clean run** — each serves a different
reader so the next session picks up without re-deriving state. Write all three every time; if a
section is empty, say so rather than omit the file:

1. `reports/refactor-summary.md` — **issues addressed** (`render_refactor_report.py` output): every
   finding `applied` and confirmed, with file, shape, model, verify method, PASS/FAIL.
2. `reports/refactor-followup.md` — **follow-up work remaining**: `reverted`, `skipped`/`deferred`,
   applied-but-not-holding, and slices never attempted — each with a one-line next step.
3. `reports/<original-report-name>.remaining.md` — **the audit minus what's fixed**: the input a
   future `refactoring-from-audit` run loads to continue where this one stopped.

Exact per-file contents, what stays vs gets pruned, and the **prune-by-`(file, title)`-not-row-number**
rule (finding-ids `f1..fN` do NOT match the report's summary-table `#` column, so pruning by row
number deletes the wrong findings): read `references/reporting.md` before writing the files.

## Gotchas

- **Entry needs a report *or* a scope, not both.** With neither, the skill hands off to `rule-audit`
  (Case 4) and continues — never stops empty or invents findings. No findings for a scope likewise
  never means "stop silently" or "make up findings": route to the Phase 1 offer (take a user-provided
  report, or run rule-audit scoped). Only an explicit user decline stops the run.
- **rule-audit is a soft dependency.** Phase 1's rule mapping and the generate-when-missing option
  call the sibling rule-audit skill (`map_rules.py`, `--mode audit`). Both ship together in this
  repo. If not installed, fall back in-context: glob `.claude/rules/*.md`, match `paths:` frontmatter
  against the scope files; for findings, ask the user for a report.
- **A green baseline is non-negotiable.** `error: true` from `run_tests.py` means the command broke
  (e.g. test runner not installed), not zero failures. Treat it as no-harness, not green.
- **Green tests ≠ finding resolved.** The suite only guards behavior it covers, and a fix can be
  reverted or half-applied with tests passing. Untested findings get a characterization test first
  (Phase 4); every finding is re-confirmed by its own verify method in Phase 7.
- **Per-test ids aren't always recoverable.** For generic runners (make, gradle, mvn) `ids_reliable`
  is false and regression detection falls back to exit code / failed count. Works, but you can't name
  the broken test — mention that limit if you hit it.
- **Don't batch findings into one subagent.** You lose which change regressed — the whole reason for
  the per-finding loop. (One agent per shape-*group* is fine; it still runs the loop internally.)
- **Markdown reports are lossy.** No `code_snippet` or `fix_example`, so those findings route to a
  pricier model. Feed rule-audit JSON when you have it.
- **The markdown loader can under-extract.** Even when a markdown report carries per-finding bodies
  (snippet, suggested fix, file:line under each heading), `load_findings.py` may flatten them to
  title-only. Before Phase 3, eyeball one finding in `findings.json` against the report; if rich
  bodies exist in the report but not the JSON, re-parse the markdown to recover
  `code_snippet`/`fix_example`/`line` first — those fields drop findings to cheaper models and hand
  each agent the exact diff.
- **The report's suggested fix is a hint, not ground truth.** Audit `fix_example`s can name a path
  alias or symbol absent from this repo. The per-finding gate (type-check) catches it — treat
  `fix_example` as a starting point, let the gate, not the report, have final say.
- **Bulk literal edits: use Python `str.replace`, not `perl`/`sed`.** Audit fixes routinely touch
  text with `@` (aliases like `@band`) and `$` (template literals like `${error}`). In `perl -pe
  "s/.../$new/"` and double-quoted shells, `@word`/`$word` interpolate as array/scalar — eating the
  alias sigil so `@app_types/Foo` becomes `/Foo`. Default to a Python helper doing literal
  `s.replace(old, new)` with a uniqueness assert; reach for `perl`/`sed` only on payloads with no
  `@`/`$`.
- **Clean up `.refactor/` when done** (safe to gitignore). Keep `reports/`.

## Scripts (run, don't reimplement)

| script | does | key signals |
|---|---|---|
| `scripts/load_findings.py` | load report scoped to `--files` → `findings.json` | exits **3** when zero findings |
| `scripts/detect_harness.py` | find the test command | — |
| `scripts/run_tests.py` | run tests → JSON | `ok` / `error` / `ids_reliable` |
| `scripts/diff_tests.py` | diff baseline vs after | `PASS` (exit 0) / new failing ids (exit 2) |
| `scripts/estimate_effort.py` | tag findings low/med/high + model | re-tier per Phase 3 |
| `scripts/render_refactor_report.py` | `results.json` → `refactor-summary.md` | computes verdict, exit 2 on regression; header documents `results.json` schema |

`map_rules.py` lives in the sibling **rule-audit** skill — it maps scope → rules (Phase 1).

## References (read on demand)

- `references/findings-schema.md` — canonical findings shape + input details (Phase 1).
- `references/effort-rubric.md` — effort-tier criteria (Phase 3).
- `references/subagent-prompts.md` — fix-agent templates + contract, adversary template (Phases 4 & 5).
- `references/reporting.md` — exact contents of the three Phase 7 report files + the pruning rule (Phase 7).
