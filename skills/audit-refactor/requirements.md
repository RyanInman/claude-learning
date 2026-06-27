# refactoring-from-audit — Requirements & Workflow

Extracted invariant spec. Every item below must survive any rewrite of `SKILL.md`. Grouped by topic; each bullet is one discrete requirement.

## R0. Identity & purpose

- **R0.1** Name: `refactoring-from-audit`.
- **R0.2** Purpose: apply an audit/review report's recommended fixes to a scope of files **without changing behavior**, verifying every change against the test suite so zero regressions slip through.
- **R0.3** Two **independent** inputs: a **report** (the findings) and a **scope** (the files/area). User can arrive with report, scope, both, or neither.
- **R0.4** Phase 0 routes a 2x2 over which inputs are present.
- **R0.5** Skill behavior summary: loads findings scoped to the scope + the rules that apply to it, confirms a test harness, dispatches each fix to the cheapest capable model, re-runs tests after every change, reverting regressions.
- **R0.6** Scope but no report → offer to generate one by running `rule-audit` scoped to those files.
- **R0.7** Neither input → hand off to `rule-audit` for a full audit, then continue.
- **R0.8** Do NOT use to *produce* an audit (that is the `rule-audit` skill).
- **R0.9** Do NOT use for open-ended "just refactor this" with no report and no scope — that routes to `rule-audit`.

## R0b. Trigger phrases (description must keep these)

- **R0b.1** "refactor this file"; "clean up src/api/foo.ts against our rules"; "apply our rules to these files"; "fix the rule-audit findings in this dir"; "refactor per this report"; "apply the suggested fixes but don't break anything"; user pastes audit findings + "make these changes safely".

## R1. Core guarantee & principles

- **R1.1** The guarantee: **not one test that passed before may fail after** (zero regression).
- **R1.2** Made cheap/certain by: deterministic scripts for mechanical parts; cheapest model per fix; a test run after every change so a regression is caught and reverted the moment it appears, not at the end.
- **R1.3** A green suite only guards behavior it covers. Before touching a finding, decide how it will be verified and build any missing safeguard first (Phase 4).
- **R1.4** After all fixes, re-confirm every finding against the report (Phase 7).
- **R1.5** Green tests prove no regression — NOT that a finding was resolved.
- **R1.6** Scripts live in `scripts/`; **run them, don't reimplement them**. They keep raw findings and test logs out of context and make before/after a deterministic set diff, not log-reading.

## R-LOOP. The loop at a glance (must be present)

- **R-LOOP.1** Phase 0 resolve inputs: report? (user path or `reports/rule-adherence-*.md`, `.rule-review/`); scope? (named file/dir) → route the 2x2; neither → confirm → rule-audit (full) → Case 2.
- **R-LOOP.2** Phase 1 get findings: `load_findings.py --files <scope>` → scoped `findings.json`; (no report) generate via rule-audit first then load; map scope→`.claude/rules/` via rule-audit `map_rules.py` (rules ctx).
- **R-LOOP.3** Phase 2 confirm harness: `detect_harness.py` + `run_tests.py` (baseline). Negotiate scope: if scoped set large, `AskUserQuestion` a smaller first slice (top impact+risk / one file / one shape-group); else proceed.
- **R-LOOP.4** Phase 3 estimate effort: `estimate_effort.py`.
- **R-LOOP.5** Phase 4 plan verification: per-finding verify method + adversary.
- **R-LOOP.6** Phase 5+6 dispatch + gate: one agent per shape-group, per-finding gate.
- **R-LOOP.7** Phase 7 confirm + report: full suite + 3 report files.

## R-Phase0. Resolve inputs and route

- **R-P0.1** Two independent inputs: report (findings to act on) + scope (file(s)/area). Detect each, then route the 2x2.
- **R-P0.2 Scope detection:** did the user name file(s) or a dir? Resolve to a concrete set of repo-relative paths (the form `load_findings.py --files` and `map_rules.py` expect). A directory expands to the files under it.
- **R-P0.3** Endpoint/route scopes are NOT supported yet (no endpoint→file map here). Take the file(s) behind the endpoint instead. (Documented as a clean extension point, not built.)
- **R-P0.4 Report detection:** a user-supplied path, or a known location: `reports/rule-adherence-high-medium.md`, `reports/rule-adherence-with-low.md`, `.rule-review/` (`batch-*.json`). These are exactly what `rule-audit` produces and what `load_findings.py` consumes.
- **R-P0.5** Route to a terminal action — no cell stops empty or invents findings.
- **R-P0.6 Case 1 (report + scope):** Phase 1 loads the report scoped to the scope; proceed. Negotiation narrows only if the scoped set is large.
- **R-P0.7 Case 2 (report, no scope):** negotiation asks for a scope, suggesting candidate slices derived from the loaded report; then Phase 1 loads `--files <chosen scope>`.
- **R-P0.8 Case 3 (scope, no report):** Phase 1 notifies there is no report and offers to run `rule-audit` scoped to the files first, then loads the produced report scoped.
- **R-P0.9 Case 4 (neither):** the only "nothing to do" path. Confirm with the user, then invoke `rule-audit` on the full audit universe; on completion re-enter as Case 2 (ask for a scope, suggesting slices from the fresh report).

## R-Phase1. Get findings for the scope, plus rules context

- **R-P1.1** Two inputs feed the fixes: findings for the scope (what to change) + the rules that apply to it (the standard each change is held to).
- **R-P1.2 Cases 1 & 2** (report present): load the report scoped:
  `python3 <skill>/scripts/load_findings.py <report> --files <scope...> --out .refactor/findings.json`
- **R-P1.3** `<report>` = a rule-audit working dir (`.rule-review/`), a findings JSON, a markdown report, or a user-supplied path.
- **R-P1.4** `--files` narrows the report to the scope deterministically (raw findings stay out of context).
- **R-P1.5** Canonical findings shape + input details: `references/findings-schema.md`.
- **R-P1.6** Case 2 loads the **full** report first (no `--files`) so negotiation can derive candidate scopes, then re-loads `--files <chosen scope>` once the scope is picked.
- **R-P1.7 Case 3** (scope, no report): notify the developer plainly that there is no report, then offer to generate one with `rule-audit` scoped to the files: `--mode audit --path <narrowest common-ancestor>` (non-mutating), OR stage the files and run `--mode staged` for a tidy file list with a clean index. Then load the produced report scoped (same `load_findings.py` command).
- **R-P1.8** If the common ancestor is the repo root (scope spans top-level dirs), prefer staged or one run per subtree — don't audit the whole repo to refactor a few files.
- **R-P1.9 Rules context (all cases):** map the scope files to the rules that govern them so fix agents hold each change to the same standard the audit used. Reuse rule-audit's mapper:
  `python3 <rule-audit>/scripts/map_rules.py --mode audit --path <common-ancestor> --out .refactor/rule-map.json`
- **R-P1.10** Read the `assignments` for the scope files, collect the union of applicable rule files; hand those to the fix agents in Phase 5 alongside each finding's `rule_text`/`fix_example`.
- **R-P1.11 Soft dependency:** rule-audit ships alongside this skill in this repo. If it isn't installed, fall back in-context: glob `.claude/rules/*.md` and match each rule's `paths:` frontmatter against the scope files.
- **R-P1.12 No finding behind a fix = nothing to verify.** If a chosen path yields zero findings (`load_findings.py` exits 3, or the scoped set is empty) and the user declines to provide or generate a report, STOP. A fix with no finding behind it has nothing to verify against and defeats the skill.

## R-Phase2. Confirm the test harness, capture the baseline

- **R-P2.1** The whole guarantee rests on a trustworthy baseline; establish one first.
- **R-P2.2** `python3 <skill>/scripts/detect_harness.py <root>` — finds the command.
- **R-P2.3** `python3 <skill>/scripts/run_tests.py --command "<cmd>" --framework <fw> > .refactor/baseline.json`
- **R-P2.4** Read `baseline.json`: `ok: true` → green baseline, full guarantee in force, proceed.
- **R-P2.5** `error: true` (command broke — missing dep, collection error) OR `ok: false` (real failures already present) → baseline not trustworthy; cannot prove zero regression against a red or broken suite.
- **R-P2.6** When the baseline isn't green: surface it plainly and ask **once** with `AskUserQuestion`: proceed with caution, or stop.
- **R-P2.7** If the user proceeds, every change this run is tagged `unverified` in the final report and you say so. Don't silently push on.
- **R-P2.8 Pin the exact working invocation, propagate it verbatim.** `detect_harness.py` gives a nominal command (`yarn test`); the one that actually goes green is often different — a runtime switch (`nvm use 22`), a flag to dodge a broken file-watcher (`--watchman=false`), an env var. Getting there can cost false starts.
- **R-P2.9** The moment the baseline is green, record the **full** command (env prefix + version-manager line + flags) and hand that exact string to every subagent and later gate. Re-deriving it per agent wastes the same minutes N times; an agent that falls back to the default runtime reddens the tree for unrelated reasons.

## R-Negotiate. Negotiate the scope

- **R-N.1** Negotiation is **conditional on size**. Small scoped set → treat as one slice, proceed, no prompt.
- **R-N.2** Only when the set is **large** (judgment against the batch-size table, not a magic number) → present an `AskUserQuestion` menu of candidate smaller slices.
- **R-N.3 No scope yet (Case 2, or post-Case-4):** present candidate slices *derived from the loaded findings* — most-violated file, highest `impact`+`risk`, largest mechanical shape-group — each labeled with finding count + tier. The pick becomes the scope; re-load `load_findings.py --files <pick>`. This is the "ask the user for a scope" step.
- **R-N.4 Scope given but large (Cases 1 & 3):** present candidate *sub-slices* of the scope the same way; the pick narrows the working set.
- **R-N.5 Scope given and already a tight slice:** proceed, no prompt.
- **R-N.6** State the chosen slice and why before touching code, so a human can review each slice and a regression has nowhere to hide.
- **R-N.7 Scale batch size inversely with fix complexity.** Harder fix → fewer at once: complex changes carry more regression risk and need closer per-finding review; a small batch keeps review tractable. The table is the yardstick for what "large" means and how to slice.
- **R-N.8** low / haiku (mechanical, `fix_example` present): large batches fine — a whole shape-group of 20-30 import swaps is one slice.
- **R-N.9** medium / sonnet (reads scope files, some judgment): ~5-10 per slice, grouped by shape.
- **R-N.10** high / opus (public surface, cross-file ripple): one or two at a time, each reviewed before the next. Never bulk a high-complexity queue.
- **R-N.11** Unsure of a finding's tier → treat as the higher one and take fewer.

## R-Phase3. Estimate effort

- **R-P3.1** `python3 <skill>/scripts/estimate_effort.py .refactor/findings.json`
- **R-P3.2** Tags each finding `low`/`medium`/`high` with the signals behind the call and the model (haiku/sonnet/opus). Criteria in `references/effort-rubric.md` — read it if a tier surprises.
- **R-P3.3** Spend the cheapest model that can plausibly do each fix; most audit fixes are mechanical; a wide fan-out of haiku agents beats reaching for Opus by reflex.
- **R-P3.4 `blast_radius` is raw file size and over-tiers.** A one-line, well-specified fix (swap an import, replace `error.message`, extract a static style) in a 300-line file gets pushed to `high`/opus on file size alone.
- **R-P3.5** Don't take the tiering at face value: re-tier by signals that track *real* effort — `snippet_lines`, `cross_file`, `exported`, and whether a `fix_example` is present. A mechanical one-liner with a `fix_example` is haiku work however big its file. Skip this and a run sends 80% of findings to Opus, paying many times over.

## R-Phase4. Plan verification per finding, build safeguards first

- **R-P4.1** The baseline guarantee only covers behavior the suite exercises. A finding in untested code can be "fixed" wrong with every test still green; a pure style finding has no behavior to test. Before applying anything, decide per finding *how you'll know it's resolved* and build the missing checks first — the safety net must exist when the fix lands, not after.
- **R-P4.2 Classify each finding by verification method (4 classes):**
- **R-P4.3** Behavior change, already covered → existing suite is the safeguard; nothing to build; the per-finding run in Phase 6 catches a regression. Record `verify: existing-tests`.
- **R-P4.4** Behavior change, not covered → a green run proves nothing. Write a characterization test that pins *current* behavior, confirm it passes against unchanged code, and commit it. Record `verify: new-test:<id>`.
- **R-P4.5** Pure style / naming / formatting / dead-code → no behavior to assert. Prefer a deterministic check: a lint rule, a type-check, or a `grep` that must return zero hits (old name gone, banned pattern absent). Scriptable, runs in the gate. Record `verify: check:<cmd>`.
- **R-P4.6** Style with no automatable check → mark for a human eyeball in the final pass and write down exactly what to inspect. Record `verify: manual:<what to look at>`.
- **R-P4.7 Adversarial red-team of the verification plan, before building anything.** Dispatch an adversarial subagent (sonnet; template in `references/subagent-prompts.md`). Hand it the slice's findings with proposed `verify` methods; have it attack each.
- **R-P4.8** Attack patterns it must probe: `existing-tests` whose finding touches a path the suite never exercises (green run proves nothing); a `new-test` that pins a side effect instead of the finding's behavior, or still passes if the fix is reverted; a `check:<grep>` matching too loosely (old name gone from one file, live in another) or too tightly (misses a variant); a `manual` flag hiding a scriptable check.
- **R-P4.9** It returns, per finding, *accepted* or a concrete weakness + a stronger method.
- **R-P4.10** Apply its upgrades to the `verify` fields **first** — cheapest point to catch a verification gap, since once a safeguard is built and committed a false sense of coverage rides along.
- **R-P4.11** You own the final call; an adversary that flags nothing on a non-trivial slice is itself suspect.
- **R-P4.12** Build and commit every new test and check script **before** dispatching the slice's fixes.
- **R-P4.13** Then re-run the full suite and overwrite `baseline.json` — the new characterization tests are now part of the green baseline, so a later regression in them is caught like the rest.
- **R-P4.14** Record the verify method in `findings.json` (a `verify` field per finding) so tier agents know how to self-check and the final pass knows what to re-confirm.

## R-Phase5. Dispatch each fix by tier

- **R-P5.1** Set up a checkpoint branch first so each kept change is its own commit (bisectable history, easy revert; never refactor straight on `main`): `git checkout -b refactor/from-audit`.
- **R-P5.2** Dispatch **one subagent per group, NOT one per finding**. Each agent walks its group's queue and runs the full per-finding loop (Phase 6): apply one change, verify by the finding's method, commit if green / revert if regressed, next.
- **R-P5.3** Rationale: per-finding commits already give bisectable blame; batching a group into one agent keeps the isolation while paying one cold start instead of N and reading the shared file once. Templates + contract in `references/subagent-prompts.md`.
- **R-P5.4 Group by fix-shape, not just effort tier.** Findings cluster into a few mechanical shapes — relative-import→alias, `error.message`→`getErrorMessage`, `new Date()`→`DateTime`, inline-style→`StyleSheet`. A shape-group shares one fix recipe, one `verify` method, one model. Effort tier picks the model; shape picks the queue.
- **R-P5.5** low → haiku. The whole low queue + each `fix_example` + the test command. Mechanical.
- **R-P5.6** medium → sonnet. The medium queue, plus permission to read the scope files.
- **R-P5.7** high → opus, **but ask first**. High-effort fixes touch public surfaces or ripple across files, and Opus costs more. Before dispatching the high queue, use `AskUserQuestion` to let the user approve the spend, skip, or defer. Don't reach for the expensive model on their behalf.
- **R-P5.8** Across all tiers, hand each agent the applicable `.claude/rules/` files gathered in Phase 1, alongside each finding's `rule_text`/`fix_example` — so a fix is held to the rule that flagged it, not just the snippet.
- **R-P5.9 Run shape-group agents sequentially, one at a time, against the shared working tree. NEVER run fix agents concurrently.**
- **R-P5.10** Why: agents in one tree clash even on disjoint files — they share one `.git/index` (parallel commits collide on `index.lock`) and one set of working files (one agent's `git add -A` sweeps another's half-written file into its commit; one agent's type-check or lint sees another's mid-edit state and fails for unrelated reasons).
- **R-P5.11** Serial dispatch sidesteps it: dispatch a group, let it finish and commit, then the next. Per-finding commits keep history bisectable regardless of order, so serializing loses nothing. Keep each group's batched gate (Phase 6) cheap so serial wall-clock stays low.
- **R-P5.12** Each agent edits only its findings' lines (no drive-by edits) and returns a per-finding status summary for the report.

## R-Phase6. Verify and checkpoint, per finding

- **R-P6.1** This is the engine each tier agent runs for every finding in its queue. Gate each applied change by the finding's `verify` method, not by reflex.
- **R-P6.2** `existing-tests` or `new-test` → run only the **changed file's tests** for fast feedback, not the whole suite.
- **R-P6.3** `check:<cmd>` → run that command; zero hits / clean exit is the gate.
- **R-P6.4** `manual:<…>` → no automated gate here. Apply, commit, leave it flagged for the Phase 7 inspection; don't block the queue on a human check.
- **R-P6.5 When the gate is a slow whole-project check, batch it.** A type-check or lint over a large project runs tens of seconds and re-checks the *whole* project after a one-line edit — running it per finding across a long mechanical queue dominates the clock.
- **R-P6.6** For such gates on mechanical shapes: commit each finding (blame stays per-finding) but run the heavy check **once at the end of the shape-group**; on failure, the per-finding commits let you bisect to the culprit, revert just that one, re-run.
- **R-P6.7** If a pre-commit hook re-runs that same check every commit, use `git commit --no-verify` — the hook is redundant with the gate you own; paying it N times is waste.
- **R-P6.8** Behavior-risk shapes (untested code, error paths) stay per-finding — batching is only for cheap, uniform, type-checkable edits.
- **R-P6.9** Test-gated findings commands:
  `python3 <skill>/scripts/run_tests.py --command "<cmd narrowed to the file's tests>" --framework <fw> > .refactor/after.json`
  `python3 <skill>/scripts/diff_tests.py .refactor/baseline.json .refactor/after.json`
- **R-P6.10** `diff_tests.py` prints `PASS` (exit 0) or the new failing ids (exit 2), so the gate costs one line instead of a JSON blob in context.
- **R-P6.11 PASS** → keep it. `git add -A && git commit` with a message naming the finding. Record `status: applied` (or `unverified` if the baseline wasn't green). Next finding, against this committed state.
- **R-P6.12 REGRESSED** → revert it (`git checkout -- <files>`, since prior findings are committed) and record `status: reverted` with the failing test. Don't "fix the fix" inline — that starts scope creep and second regressions. Leave it for the user.
- **R-P6.13** The subset run is the fast inner loop, not the guarantee. The **Phase 7 full-suite run is the gate of record**: a change can break a test far from the file it touched, and that surfaces there. Since every kept finding is its own commit, a regression caught only at the end still bisects to its cause.

## R-Phase7. Final report and the verdict

- **R-P7.1 Confirmation pass first.** Walk the original report finding by finding and confirm each marked applied actually holds — run the `check:` commands, do the `manual:` inspections now, spot-check that each `new-test` still asserts its finding's behavior.
- **R-P7.2** Why the suite can't do this: green tests prove nothing regressed, but a fix can be reverted, half-applied, or cosmetic-only with the suite green. Any applied finding that doesn't hold gets flagged, not counted done.
- **R-P7.3** Write recorded results to `.refactor/results.json` (schema in `render_refactor_report.py`'s header: `branch`, `baseline`, `final`, and a `results` list).
- **R-P7.4** Capture one last full run as `final`:
  `python3 <skill>/scripts/run_tests.py --command "<cmd>" --framework <fw> > .refactor/final.json`
- **R-P7.5** Render: `python3 <skill>/scripts/render_refactor_report.py .refactor/results.json --out reports/refactor-summary.md`
- **R-P7.6** The script computes the zero-regression verdict by diffing `final` against `baseline`, exiting 2 if any regression survived.
- **R-P7.7** Report plainly: how many findings applied / reverted / skipped / unverified, and the PASS/FAIL line — backed by the actual final test output, not an assertion it "should" pass. If anything regressed, say so first.
- **R-P7.8 Always write three report files under `reports/`, even on a clean run.** Each serves a different reader. Write all three every time; if a section is empty, say so rather than omit the file.
- **R-P7.9 File 1 — `reports/refactor-summary.md` (issues addressed).** The `render_refactor_report.py` output. Every finding marked `applied` (and confirmed), with its file, shape, model, verify method, and PASS/FAIL verdict. The record of what *this* session changed.
- **R-P7.10 File 2 — `reports/refactor-followup.md` (follow-up work remaining).** Everything still owed: findings `reverted` (with the failing test and why), `skipped`/`deferred` (with reason — e.g. high-tier opus queue the user declined, untested behavior needing a characterization test first), any finding the confirmation pass flagged as applied-but-not-holding, and report slices never attempted this run. Give each a one-line next step (the model, the safeguard to build, or the decision needed) so it's directly actionable.
- **R-P7.11 File 3 — `reports/<original-report-name>.remaining.md` (the audit minus what's fixed).** Copy the original report and remove every finding now `applied` and confirmed, preserving its structure (summary table rows AND detail blocks both pruned). Update counts/headers to match. This is the input a future `refactoring-from-audit` run loads to continue. Leave `reverted`/`skipped` findings IN (still open work).
- **R-P7.12 Prune by `(file, title)`, never by row number.** `load_findings.py` finding-ids (`f1..fN`) do NOT match the report's summary-table `#` column — the id is assigned in load order, the `#` is the audit's ranking, and they diverge (e.g. `f39` can be table row 41). Match rows to remove by their `(file, issue)` cells — the same key used to prune detail blocks. Dropping rows by `int(#) == int(id[1:])` deletes the wrong rows and leaves fixed findings in; verify zero fixed titles remain after pruning.

## R-Gotchas

- **R-G.1** The entry needs a report *or* a scope, not necessarily both. With neither, hand off to `rule-audit` (Case 4) and continue — do not stop empty or invent findings. No findings for a scope never means "stop silently" or "make up findings": route to the Phase 1 offer. A fix with no finding behind it has nothing to verify against; only an explicit user decline stops the run.
- **R-G.2** `rule-audit` is a soft dependency. Phase 1's rule mapping and the generate-when-missing option call the sibling `rule-audit` skill (`map_rules.py`, `--mode audit`). Both ship together in this repo. If not installed, fall back: glob `.claude/rules/*.md` and match `paths:` frontmatter against scope files; for findings, ask the user for a report.
- **R-G.3** A green baseline is non-negotiable for the guarantee. `error: true` from `run_tests.py` means the command broke (e.g. test runner not installed), not zero failures. Treat as no-harness, not green.
- **R-G.4** Green tests ≠ finding resolved. The suite only guards behavior it covers; a fix can be reverted or half-applied with tests passing. Untested findings get a characterization test first (Phase 4); every finding is re-confirmed by its own verify method in Phase 7.
- **R-G.5** Per-test ids aren't always recoverable. For generic runners (make, gradle, mvn) `ids_reliable` is false and regression detection falls back to exit code / failed count. Works, but you can't name the broken test — mention that limit if you hit it.
- **R-G.6** Don't batch findings into one subagent. You lose which change regressed — the entire reason for the per-finding loop.
- **R-G.7** Markdown reports are lossy. No `code_snippet` or `fix_example`, so those findings route to a pricier model. Feed rule-audit JSON when you have it.
- **R-G.8** The markdown loader can under-extract. Even when a markdown report carries per-finding bodies (current snippet, suggested fix, file:line under each heading), `load_findings.py` may flatten them to title-only. Before Phase 3, eyeball one finding in `findings.json` against the report; if rich bodies exist in the report but not the JSON, re-parse the markdown to recover `code_snippet`/`fix_example`/`line` first.
- **R-G.9** The report's suggested fix is a hint, not ground truth. Audit `fix_example`s can name a path alias or symbol that doesn't exist in this repo. The per-finding gate (a type-check) catches it — each agent treats `fix_example` as a start and lets the gate, not the report, have the final say.
- **R-G.10** Bulk literal edits: use Python `str.replace`, not `perl`/`sed`. Audit fixes routinely touch text with `@` (aliases like `@band`) and `$` (template literals like `${error}`). In `perl -pe "s/.../$new/"` and double-quoted shells, `@word`/`$word` interpolate as array/scalar — eating the alias sigil so `@app_types/Foo` becomes `/Foo`. Default to a Python helper doing a literal `s.replace(old, new)` with a uniqueness assert; reach for `perl`/`sed` only on payloads with no `@`/`$`.
- **R-G.11** Clean up `.refactor/` when done (safe to gitignore). Keep `reports/`.

## R-Scripts. Script inventory (run, don't reimplement)

- **R-S.1** `scripts/load_findings.py` — load report scoped to `--files` → `findings.json`; exits 3 when zero findings.
- **R-S.2** `scripts/detect_harness.py` — finds the test command.
- **R-S.3** `scripts/run_tests.py` — runs tests → JSON (`ok`/`error`/`ids_reliable`).
- **R-S.4** `scripts/diff_tests.py` — diffs baseline vs after → `PASS` (exit 0) / new failing ids (exit 2).
- **R-S.5** `scripts/estimate_effort.py` — tags findings low/med/high + model.
- **R-S.6** `scripts/render_refactor_report.py` — `results.json` → `refactor-summary.md`; computes verdict (exit 2 if regression). Header documents `results.json` schema.
- **R-S.7** `map_rules.py` lives in the sibling **rule-audit** skill — maps scope → rules.

## R-Refs. Reference inventory (one level deep)

- **R-R.1** `references/findings-schema.md` — canonical findings shape + input details (cited from Phase 1).
- **R-R.2** `references/effort-rubric.md` — effort tier criteria (cited from Phase 3).
- **R-R.3** `references/subagent-prompts.md` — fix-agent templates + contract, adversary template (cited from Phases 4 & 5).
- **R-R.4** `references/characterization-net.md` — exists in folder; currently NOT cited from SKILL.md (orphan; flag, don't silently rewire).
