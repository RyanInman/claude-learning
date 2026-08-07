# Debate Review Transcript

**Artifact:** /Users/admin/claude-learning/skills/debate-review-workspace/iteration-2/eval-3-pytest-inline-proposal/with_skill/work/proposal.md
**Date:** 2026-08-06

Append-only. Each phase's content lands under its own heading, transcribed verbatim by the
Defender. No role's text is ever edited after it is written.

---

## Phase 1 — Defender: Opening Statement

The goal: replace unittest with pytest as the test framework for our Python monorepo,
covering roughly 6,000 existing tests.

Three decisions drive the proposal:

**Fixtures over setUp inheritance.** Our current suites share state through TestCase base
classes. Shared setup lives in parent classes, and a test's dependencies are invisible at
the test site — you trace the inheritance chain to learn what a test assumes. pytest
fixtures invert this: each test declares exactly the fixtures it uses as parameters, and
fixtures compose without inheritance. Scoped fixtures (function, class, module, session)
also give us cheap control over expensive setup like database connections, which today we
hand-roll with class-level caching.

**parametrize over copy-pasted variants.** We have real duplication: families of
near-identical test methods that differ only in inputs and expected outputs. unittest's
answer is `subTest`, which reports less clearly and still keeps the loop inside one test
body. `@pytest.mark.parametrize` turns each variant into its own reported test case with
its own pass/fail status, and deleting the copy-paste reduces maintenance surface.

**Plugin ecosystem, especially xdist.** We run tests serially today. pytest-xdist gives
multi-core parallelism with a command-line flag. Other plugins we would likely adopt:
pytest-cov, pytest-timeout, better failure output with plain `assert` instead of
`self.assertEqual` memorization.

Key facts making the switch cheaper than it sounds: pytest runs unittest-style TestCase
suites natively, so the 6,000 tests do not need a big-bang rewrite — we can switch the
runner first and migrate test style incrementally, per-package, as files are touched.

Honest uncertainties, flagged up front:

- The 6,000-test estate means a long tail of partial migration; mixed-style codebases have
  their own confusion cost.
- CI churn is real: runner invocation, coverage wiring, result reporting, flake detection
  all change.
- Team familiarity is uneven. unittest knowledge is universal; pytest's fixture resolution
  and conftest.py scoping have a genuine learning curve, and misused fixtures can create
  action-at-a-distance of their own.
- pytest is a third-party dependency, unlike stdlib unittest; that adds a (small) supply
  chain and upgrade-treadmill consideration.

I hold that the ergonomics and parallelism gains outweigh these costs, particularly
because the compatibility path lets us pay the migration cost gradually rather than up
front. The user has final say; this debate exists to pressure-test that position.

## Phase 2 — Clarifying Questions

### Adversary's questions

1. Has pytest-xdist been trialed on any real package in the monorepo? Specifically: what fraction of the 6,000 tests touch shared mutable state (a shared database, module-level globals, fixture files on disk, fixed ports), and do any suites currently depend on test execution order?

2. Does any part of the estate use unittest features that pytest's compatibility layer does not fully support — `load_tests` hooks, custom `TestRunner`/`TestResult` classes, `subTest` (which xdist and some reporting tools handle poorly), or heavy `setUpClass`/`setUpModule` state that tests mutate?

3. What is the concrete plan for the incremental migration: who owns conftest.py conventions and fixture-scoping standards, is there a target date or trigger for declaring the migration done, and what happens to packages nobody touches — do they stay unittest-style indefinitely?

### Advocate's questions

1. What concrete numbers do we have on the pain the proposal targets — e.g., how many test classes inherit from a shared TestCase base, how many copy-pasted variant families exist, and what the serial test suite's current wall-clock time is in CI? Measured baselines let the gains (parallelism, deleted duplication) be argued as quantities rather than adjectives.

2. Which unittest features do the 6,000 tests actually rely on that pytest's compatibility mode handles imperfectly or not at all — for example `subTest`, `load_tests`, custom TestResult/TestRunner hooks, or class-level `setUpClass` interactions? Knowing the true edge-case surface tells us how solid the "switch the runner first, migrate incrementally" path really is.

3. Does any part of the codebase or team already use pytest today — a package, a service, internal tooling, or prior-job experience — and if so, what was the observed learning-curve and fixture-misuse experience there? Existing in-house precedent is the strongest available evidence for or against the familiarity concern.

## Phase 3 — Defender's Answers

**Adversary Q1 (xdist trial, shared state, ordering).** No trial has been run. The
proposal's parallelism claim rests on pytest-xdist's general behavior, not on measurement
against our suite. The fraction of tests touching shared mutable state has not been
audited. I do not have evidence that suites depend on execution order, but I also cannot
rule it out; unittest runs tests in alphabetical order within a class, and 6,000 tests
written against a deterministic serial runner may have latent order or shared-state
dependencies that xdist's process-level distribution would expose. This is an unverified
assumption in the proposal, not an established fact.

**Adversary Q2 / Advocate Q2 (unsupported unittest features).** No audit exists. Known
limits of pytest's compatibility layer, from pytest's own documentation: `load_tests`
protocol is not respected; custom `TestRunner`/`TestResult` classes are bypassed because
pytest does the running; `subTest` support has historically been partial (it works via a
plugin-grade shim and reporting differs); and pytest fixtures cannot be injected into
TestCase methods, so unmigrated tests get none of the fixture benefits. `setUpClass` /
`setUpModule` do run under pytest. Whether our estate uses `load_tests` or custom runners
is unknown until we grep. A one-day audit would convert this unknown into a list.

**Adversary Q3 (migration governance).** The proposal as written has no governance plan:
no named owner for conftest.py conventions, no fixture-scoping standard, no done-date, no
policy for untouched packages. The implicit position is "runner first, style migration
opportunistically as files are touched," which does mean untouched packages stay
unittest-style indefinitely. That is a gap in the proposal, not a deliberate accepted
trade-off.

**Advocate Q1 (measured baselines).** No measured numbers exist. The copy-paste variant
claim and the setUp-inheritance claim come from the team's lived experience of the
codebase, not from a count. Current CI wall-clock time was not stated in the proposal. The
absence of baselines cuts both ways: the gains are unquantified, and so is the pain.

**Advocate Q3 (in-house pytest precedent).** Not stated in the proposal. Some developers
know unittest well — that is documented as a downside — but the proposal is silent on
whether anyone has production pytest experience. pytest is the dominant framework in the
open-source Python ecosystem, so hiring and onboarding new developers likely skews toward
pytest familiarity, but I have no in-house precedent to cite.

## Phase 4 — Cases

### Adversary's case

#### Objection 1 — The headline parallelism benefit is unverified against this suite, and it is the claim most likely to fail

**Problem.** The proposal sells pytest-xdist as parallelism "for free." xdist distributes tests across worker processes and assumes test isolation. 6,000 tests written over years against a deterministic serial runner are exactly the population where shared databases, module-level globals, fixture files on disk, fixed ports, and alphabetical-order dependencies hide. If a meaningful fraction of the suite is not isolation-safe, the "free" benefit becomes a test-isolation remediation project of unknown size — plausibly the largest cost in the whole migration, and it appears nowhere in the proposal.

**Evidence.** The Defender's answer to my Q1: no xdist trial has been run, the shared-state fraction has not been audited, and order dependence "cannot be ruled out." The Defender's own words: "an unverified assumption in the proposal, not an established fact." The proposal's strongest quantitative selling point rests on zero measurements from this codebase.

**Better way.** Gate the decision on a time-boxed pilot. Pick two or three representative packages (one DB-heavy, one pure-unit, one integration-flavored), run them under `pytest -n auto`, and record two numbers: speedup and count of tests that fail only under parallelism. If failures are rare, the claim is proven and the proposal gets its first hard number. If they are common, the proposal must add an isolation-remediation workstream with its own cost estimate. Either outcome improves the proposal; a week of pilot beats a quarter of surprises.

#### Objection 2 — "No big-bang rewrite" rests on an unaudited compatibility layer

**Problem.** The entire risk-mitigation story is "pytest runs unittest suites natively, so switch the runner first." But the compatibility layer has documented holes: `load_tests` is not respected, custom `TestRunner`/`TestResult` classes are bypassed, `subTest` reporting differs, and fixtures cannot be injected into TestCase methods. If the estate uses `load_tests` or a custom runner (common in older monorepos for test discovery, result aggregation, or CI reporting), the "cheap runner swap" silently drops tests or breaks reporting — the worst failure mode, because dropped tests fail green.

**Evidence.** The Defender's answer to my Q2: "No audit exists... Whether our estate uses `load_tests` or custom runners is unknown until we grep." The Defender also conceded the fix is cheap: "A one-day audit would convert this unknown into a list."

**Better way.** Run that one-day audit before the decision, not after. Grep the estate for `load_tests`, `TestRunner`, `TestResult`, `subTest`, and `setUpModule`; attach the hit list to the proposal with a per-item disposition (works under pytest / needs rewrite / blocks package X). Then verify the swap drops nothing: compare collected-test counts between `unittest discover` and `pytest --collect-only` per package, and treat any mismatch as a release blocker. This converts the proposal's central premise from assertion to checked fact for one day of work.

#### Objection 3 — No migration governance means a permanent two-framework estate, and the benefits never arrive for unmigrated tests

**Problem.** The implicit plan — "runner first, style migration opportunistically" — has no owner, no conventions, no done-condition, and no policy for untouched packages. Two consequences. First, cold packages stay unittest-style forever, so the codebase permanently carries both idioms, and the Defender already conceded mixed-style codebases have their own confusion cost. Second, and worse for the cost-benefit math: TestCase tests cannot receive pytest fixtures, so benefits 1 and 2 of the proposal (fixtures, parametrize) apply only to migrated tests. Without governance, the migrated fraction is whatever entropy delivers, and the proposal's main benefits may reach 20% of the estate while 100% pays the mixed-codebase tax.

**Evidence.** The Defender's answer to my Q3: "no named owner... no done-date, no policy for untouched packages... That is a gap in the proposal, not a deliberate accepted trade-off." The fixture limitation for TestCase methods is from the Defender's own Q2 answer.

**Better way.** Add one governance page to the proposal: a named owner for conftest.py and fixture-scoping conventions; a lint/CI rule that new test files must be pytest-style (stops the hole getting deeper); a per-package migration tracker; and an explicit choice between (a) a funded finish line with a date or (b) a permanently mixed estate accepted in writing. Option (b) is legitimate — but the author should choose it, not inherit it.

#### Objection 4 — Every quantified-sounding benefit is an adjective; the author is being asked to decide without a single number

**Problem.** "Deep setUp hierarchies," "copy-pasted variants we maintain by hand," and serial-run pain are all asserted from lived experience. No count of TestCase inheritance chains, no count of variant families, not even the current CI wall-clock time — the one number that decides whether xdist parallelism is worth anything at all (a 4-minute suite gains nothing worth 6,000 tests of churn; a 40-minute suite is a different conversation). The author has final say and is being asked to weigh unmeasured gains against a measured 6,000-test blast radius.

**Evidence.** The Defender's answer to Advocate Q1: "No measured numbers exist... Current CI wall-clock time was not stated." The Defender's own framing: "the gains are unquantified, and so is the pain."

**Better way.** Half a day of scripting before the decision: record CI wall-clock from the last 20 runs; grep-count TestCase subclasses with inheritance depth over 1; sample three packages and count near-duplicate test-method families. Put the three numbers in the proposal. If they are big, the case strengthens materially; if they are small, the author just avoided a 6,000-test migration justified by vibes.

#### Objection 5 — CI churn is named as a risk but has no mitigation, when a cheap standard one exists

**Problem.** The proposal lists CI churn (runner invocation, coverage wiring, result reporting, flake detection) as a downside and stops there. A cutover that flips the runner in place risks a window where coverage numbers shift, flake-detection history resets, and reporting breaks — all at once, across every team in the monorepo, with rollback pressure landing on whoever flipped the switch.

**Evidence.** Phase 1: "CI churn is real: runner invocation, coverage wiring, result reporting, flake detection all change" — acknowledged, unmitigated. No answer in Phase 3 adds a plan.

**Better way.** Run pytest as a parallel shadow CI job (non-blocking) for two to four weeks before cutover: same tests, both runners, compare collected counts, pass/fail parity, and coverage deltas per package. Flip a package to pytest-as-source-of-truth only when its shadow job shows parity. This also doubles as the collection-count check from Objection 2 and the stability evidence from Objection 1 — one mechanism retires three risks.

---

**Summary for the Judge.** None of these objections argues pytest is the wrong destination — the ecosystem argument is real and the Defender's incremental path is directionally right. All five argue the same underlying defect: the proposal asks for a decision before running any of four cheap verifications (xdist pilot, compatibility grep, baseline measurement, shadow CI), each costing between half a day and a few weeks, each capable of converting the proposal's largest unknowns into numbers. The best version of this artifact is the same proposal with a "gates before commitment" section: pilot results, audit list, baselines, and a governance page. If those come back clean, I expect to concede the destination entirely.

### Advocate's case

The proposal is right, and its strongest feature is one the arguments-for section undersells: the shape of the migration, not just the destination.

**1. The compatibility path makes this a low-irreversibility decision, which changes the risk calculus entirely.** pytest runs unittest-style TestCase suites natively. The proposal therefore decomposes into two separately priced steps: switch the runner (small, mostly CI config, revertible in a day), then migrate test style per-package as files are touched (gradual, abortable at any point). Critics will price this as "rewrite 6,000 tests"; the actual first commitment is closer to a CI configuration change. A mixed-style estate has a confusion cost, and the Defender flagged it honestly, but mixed-style is a tolerable steady state, not a failure mode: unmigrated tests keep passing, and every migrated file is strictly readable on its own. The proposal buys optionality cheaply, and plans that let you stop halfway with positive value are rare.

**2. Fixtures fix a structural defect, not a taste preference.** The setUp-inheritance pattern hides a test's dependencies in a parent-class chain; the reader traces inheritance to learn what a test assumes. Fixture injection puts the dependency list in the test's signature. That is the same argument the industry accepted for dependency injection over inherited globals in production code, applied to tests. There is a second-order payoff the proposal does not state: tests with explicit, injected dependencies are exactly the tests that can be safely parallelized and relocated, so argument 1 (fixtures) is not independent of argument 3 (xdist) — it is the enabling work for it. Scoped fixtures also replace the hand-rolled class-level caching of expensive resources (database connections) with a supported, documented mechanism, deleting bespoke infrastructure.

**3. parametrize dominates subTest on every axis that matters operationally.** Each variant becomes an individually reported, individually selectable test: `-k` can rerun one failing case, CI dashboards show which input broke, and flake tracking attributes failures to a case rather than to a loop body. subTest keeps the loop inside one test and reports through a shim. For a 6,000-test estate where triage time is the recurring cost, per-case reporting is a compounding win, not a cosmetic one.

**4. pytest is the ecosystem default, and defaults compound.** This is the strongest argument the proposal never makes. unittest is stdlib-frozen: it evolves on the Python release cadence with minimal investment. pytest is where the Python testing ecosystem actually lives — plugins, documentation, Stack Overflow answers, and, increasingly, code-generation tooling all assume it. New hires skew pytest-fluent; the Defender conceded the in-house precedent is undocumented but correctly noted the hiring pool tilts this way. Choosing the ecosystem default means every future testing problem (coverage, timeouts, flake retry, snapshot testing) has an off-the-shelf answer, whereas staying on unittest means hand-building or going without. The learning-curve downside is real but asymmetric: pytest knowledge transfers to nearly every other Python codebase a developer will touch; deep unittest knowledge increasingly does not.

**5. xdist is the only credible path to parallelism that does not mean building a test runner.** Yes, Phase 3 established that no trial has been run and shared-state exposure is unaudited. The steelman is this: today's serial suite is the ceiling, permanently, and unittest offers no supported way through it. If xdist exposes order dependence or shared mutable state, those are latent defects in the tests that a deterministic alphabetical runner has been masking — surfacing them is a benefit wearing the costume of a cost. And xdist's failure mode is graceful: run it per-package, keep the incompatible packages serial, and still collect the speedup on the rest.

**6. The gaps Phase 3 exposed are cheap to close and none of them gates the first step.** The missing audit (`load_tests`, custom runners, `subTest` usage) is a one-day grep. The missing xdist evidence is a one-package trial. The missing governance (conftest.py ownership, scoping standards, done-criteria for untouched packages) is a page of policy the author, who has final say, can write. These are prerequisites for declaring victory, not for starting: the runner-first design means the proposal can absorb all three answers without changing its position. A proposal whose unknowns are all convertible to knowns for roughly two days of work, before any irreversible step, is about as de-risked as a framework decision gets.

**The honest constraint to keep in view:** the proposal's quantitative claims (duplication volume, CI wall-clock gain) are lived-experience claims, not measurements, and the Defender said so plainly. That candor is a strength of the artifact, and the fix is to measure before the style migration, not to reject the direction. The direction — ecosystem-default framework, explicit dependencies, per-case reporting, purchasable parallelism, all reachable through a stop-anytime incremental path — is correct as written.

## Phase 5 — Rebuttals

### Adversary's rebuttal

#### Part 1 — Rebutting the steelman point by point

**Steelman 1 (low irreversibility).** The reversibility claim assumes you can detect that the swap broke something. The documented failure mode of the runner swap is silent: `load_tests` hooks are not respected and custom runners are bypassed, so dropped tests fail green. A change is only "revertible in a day" if something tells you to revert; a green-but-hollow CI run does not. Reversibility is real for the config lines and unproven for the test population until the collection-count parity check from my Objection 2 has run. The steelman also calls the mixed estate "a tolerable steady state" without evidence, while conceding the confusion cost exists. Tolerable-in-writing, chosen by the author, was my Objection 3's exact ask; asserting tolerability in a debate transcript is not the same as the author accepting it in the proposal.

**Steelman 2 (fixtures fix a structural defect).** I accept the structural argument. But the added claim that fixtures are "the enabling work" for xdist cuts against the proposal's own headline: if explicit-dependency tests are what parallelize safely, then parallelism is not "for free" with a command-line flag; it is downstream of the style migration, which has no owner, no conventions, and no finish line. Steelman 2 quietly converts benefit 3 from "flip a flag" into "complete the migration first," which raises the price of Objection 3's governance gap.

**Steelman 3 (parametrize beats subTest).** Conceded on the merits; per-case reporting and `-k` selection are operational wins. Note only that parametrize does not work on TestCase methods, so this benefit also accrues solely to migrated tests. It strengthens the destination and does nothing for the unmigrated 6,000.

**Steelman 4 (ecosystem default).** Conceded. This is the strongest argument for the destination, it needs no in-house measurement, and none of my objections dispute the destination.

**Steelman 5 (latent defects surfaced are a benefit).** This is the steelman's weakest move. Reframing isolation failures as "defects the serial runner was masking" does not move the cost anywhere: someone still audits, triages, and fixes them, and that work appears in no estimate. Some of those failures are not even defects; a suite that intentionally shares one expensive database fixture is correct for serial execution, and making it parallel-safe is pure migration cost, not deferred value. The graceful-degradation claim ("keep incompatible packages serial") requires knowing which packages are incompatible, and the only way to know is the per-package pilot my Objection 1 demands. Steelman 5 thus concedes my mechanism while disputing my label.

**Steelman 6 (gaps are cheap and none gates the first step).** Half right. Cheap: agreed, and that agreement is decisive. But "none gates the first step" is wrong for exactly one item: the compatibility audit. The first step is the runner swap; the runner swap's failure mode is silent test loss; the audit plus a collect-count comparison is the detection mechanism. A one-day check that prevents a fail-green outcome on step one gates step one. For the rest, the Advocate and I now disagree only about sequencing, and cheapness argues my way: running a one-day grep before deciding costs nothing measurable, while skipping it buys one specific catastrophic mode.

#### Part 2 — Objections re-assessed

**Objection 1 (xdist unverified) — sustained, narrowed.** The Advocate's per-package fallback genuinely caps the worst case, and I credit that: xdist failure is no longer "the benefit evaporates," it is "the benefit shrinks to the isolable subset." But identifying that subset is the pilot. The objection stands as: run the two-or-three-package pilot before the proposal cites parallelism as a benefit, and record baseline wall-clock and speedup while doing it (see Objection 4's disposition below).

**Objection 2 (unaudited compatibility layer) — sustained, and now stronger.** Steelman 6 concedes the audit is one day of grep. Nothing in the steelman disputes that `load_tests` and custom runners break silently. A conceded-cheap check against a conceded-catastrophic failure mode is the clearest gate in this debate. Grep, attach the hit list, compare collected counts per package, then swap the runner.

**Objection 3 (no migration governance) — sustained.** Steelman 1 argues the mixed estate is tolerable and steelman 6 argues the governance page is a day of writing. Both can be true and neither answers the objection: the author must choose the mixed estate in the proposal, not inherit it from entropy. Steelman 2 raised the stakes by tying parallelism to migration progress. The one-page ask stands: named conftest.py owner, new-tests-are-pytest lint rule, per-package tracker, and an explicit funded-finish-line-or-permanent-mix decision.

**Objection 4 (no numbers) — dropped as a standalone gate.** Two steelman points convinced me. First, the low-irreversibility argument (steelman 1, as it applies to the config change itself) lowers the evidential bar for starting: a cheaply reversible step does not need a fully quantified justification. Second, steelman 4 shows three of the four benefits (fixtures, parametrize, ecosystem) do not depend on any of the numbers I demanded; only the parallelism claim does. The surviving measurement need, baseline CI wall-clock, folds into Objection 1's pilot, since a speedup number requires a baseline anyway. Dropping this leaves four objections I hold without reservation.

**Objection 5 (CI churn unmitigated) — sustained, unanswered.** The steelman never addresses CI churn. The shadow-CI mechanism also happens to be what makes steelman 1's reversibility claim true in practice: parity data per package is the evidence that reverting is unnecessary, or the alarm that triggers it. One mechanism still retires three risks (isolation evidence, collection parity, cutover safety), and no one has argued against it.

#### Revised summary for the Judge

The destination is no longer in dispute; steelman 4 is conceded and Objection 4 is dropped. What remains is sequencing, and it has collapsed to a narrow, concrete disagreement: the Advocate says no verification gates the first step; I say exactly one does (the one-day compatibility audit plus collection parity), one gates citing parallelism as a benefit (the pilot), one gates declaring the plan complete (the governance page), and one de-risks cutover (shadow CI, which also proves the reversibility the steelman relies on). Every gate is priced between half a day and a few weeks, and the Advocate has conceded the prices. The proposal plus that "gates before commitment" section is the best version of itself; I recommend the Judge order the gates by the failure mode each prevents, with the fail-green audit first.

### Advocate's rebuttal

I answer each objection in order, then flag which steelman points fall.

**Objection 1 (xdist unverified) — concede the gate, dispute the framing.** I concede that the parallelism claim needs the pilot before it can be sold as a benefit. What convinced me: the Defender's Phase 3 answer is a full concession in his own words — "an unverified assumption in the proposal, not an established fact" — and the Adversary's pilot design (three representative packages, `pytest -n auto`, record speedup and parallel-only failures) is a week of work that converts the claim either way. I dispute the framing that this is "the claim most likely to fail." xdist fails gracefully per-package: incompatible packages stay serial, and the speedup is collected on the rest, so the realistic downside is a smaller number, not zero. I also dispute the implied weight: parallelism is one of three arguments, and fixtures and parametrize deliver value at zero xdist risk. The objection trims argument 3 to "pending pilot"; it does not touch arguments 1 and 2.

**Objection 2 (unaudited compatibility layer) — concede.** This is the Adversary's strongest objection and I concede it in full. What convinced me: the failure mode. `load_tests` and custom `TestRunner`/`TestResult` bypass means dropped tests fail green — reversion only rescues you from failures you can see, so my "revertible in a day" safety net does not cover this hole. The evidence is documented pytest behavior plus the Defender's admission that no grep has been run. The fix the Adversary proposes is exactly right and cheap: run the one-day grep, and make collected-count parity between `unittest discover` and `pytest --collect-only` a release blocker per package. The runner swap stays cheap; it just moves behind a one-day gate.

**Objection 3 (no governance, permanent two-framework estate) — concede the fix, dispute the severity.** I concede the governance page: named conftest.py owner, lint rule requiring pytest-style for new test files, per-package tracker, and an explicit written choice between a funded finish line and an accepted mixed estate. What convinced me: the Defender called the gap "not a deliberate accepted trade-off" — an unchosen default is exactly what a proposal with an author who has final say should not contain, and the fix costs a page. I dispute "the benefits never arrive for unmigrated tests" as a cost projection. Opportunistic migration is not uniform-random: files migrate when touched, so migration concentrates in the hottest packages, which is where readability and per-case triage pay most. Entropy delivers benefit-weighted coverage. Cold packages that nobody touches also generate little of the pain the proposal targets. The mixed-estate tax is real but front-loaded on active code that migrates first.

**Objection 4 (no numbers) — largely convergent; dispute one framing.** My own case already conceded the substance: the honest-constraint paragraph says measure before the style migration. I adopt the Adversary's half-day script list (CI wall-clock from 20 runs, TestCase inheritance-depth count, sampled variant-family count) as the concrete form of that concession. I dispute the framing "unmeasured gains against a measured 6,000-test blast radius." The 6,000 figure is the estate size, not the cost; the compatibility path prices the first commitment as a CI config change plus the Objection 2 audit. Counting the whole estate as blast radius repeats the error my steelman point 1 identified. The wall-clock number gates only the xdist argument; the ecosystem-default and explicit-dependency arguments do not depend on it.

**Objection 5 (CI churn unmitigated) — concede and adopt.** The shadow-CI proposal convinced me on its merits: a non-blocking parallel pytest job comparing collected counts, pass/fail parity, and coverage deltas per package, with per-package cutover on parity. It is the mechanism my steelman point 1 implies but never specifies — it makes "revertible" checkable instead of asserted, and it retires Objections 1, 2, and 5 with one job. This is the rare objection whose remedy strengthens the proposal's own philosophy rather than constraining it. Add it.

**Steelman points that fall.**

- Point 6's claim that "none of them gates the first step" falls to Objection 2. The compatibility grep and the collect-count parity check do gate the runner swap, because the swap's failure mode (silently dropped tests) is invisible after the fact. The corrected claim: every unknown converts to a known for about two days of gated work before the swap — still cheap, no longer free-ordered.
- Point 1's "revertible in a day" survives only as amended: reversion covers visible breakage; the parity check from Objections 2 and 5 is what covers invisible breakage. With the shadow job in place, the point stands stronger than originally written.

**Net position.** The destination is undamaged — the Adversary's own summary declines to contest it. Every objection resolves into a cheap gate the proposal can absorb: one-day grep with collect-parity blocker, one-week xdist pilot, half-day baseline scripts, a governance page, and a shadow CI job that subsumes three of the five. I recommend the Judge treat these as agreed amendments, not open disputes: the proposal as amended — same position, plus a "gates before commitment" section — is the strongest plan on the table, and I hold that the original's runner-first architecture is precisely what makes all five amendments affordable.

## Phase 6 — Judge's Final Report

### ## Agreed changes

The Advocate conceded five concrete amendments in rebuttal. Both sides now support all of them; they are ready to act on.

1. **One-day compatibility audit, gating the runner swap** (from Objection 2, conceded in full). Grep the estate for `load_tests`, custom `TestRunner`/`TestResult`, `subTest`, and `setUpModule`; attach the hit list to the proposal with per-item dispositions. Make collected-count parity between `unittest discover` and `pytest --collect-only` a per-package release blocker. The Advocate also conceded that its own steelman point 6 ("none of them gates the first step") falls on this item: the swap's failure mode is silently dropped tests that fail green, so reversibility does not cover it.
2. **Time-boxed xdist pilot before parallelism is cited as a benefit** (from Objection 1, gate conceded). Two or three representative packages under `pytest -n auto`; record speedup and count of parallel-only failures. Record baseline CI wall-clock while doing it.
3. **Governance page** (from Objection 3, fix conceded). Named conftest.py owner, lint/CI rule that new test files are pytest-style, per-package migration tracker, and an explicit written choice between a funded finish line and an accepted permanent mixed estate.
4. **Shadow CI job before cutover** (from Objection 5, conceded and adopted). Non-blocking parallel pytest job for two to four weeks comparing collected counts, pass/fail parity, and coverage deltas; per-package cutover only on parity. Both sides note this one mechanism retires the isolation-evidence, collection-parity, and cutover-safety risks, and makes the "revertible in a day" claim checkable rather than asserted.
5. **Half-day baseline scripts** (from Objection 4's remedy, adopted by the Advocate even after the Adversary dropped the objection as a gate). CI wall-clock from the last 20 runs, TestCase inheritance-depth count, sampled variant-family count.

### ## Dropped objections

- **Objection 4 (no numbers) — dropped by the Adversary as a standalone gate.** Two arguments answered it: the runner swap is cheaply reversible, so it does not need a fully quantified justification, and three of the four benefits (fixtures, parametrize, ecosystem default) do not depend on any of the demanded numbers — only the parallelism claim does, and its baseline measurement folds into the pilot. The measurements still happen (item 5 above), but they no longer block the decision.
- **The destination itself.** The Adversary's opening summary declined to contest pytest as the destination and its rebuttal conceded steelman 4 (ecosystem default) outright, calling it the strongest argument and noting it needs no in-house measurement. The record shows no live argument for staying on unittest.

### ## Contested points

Only two disputes survive rebuttal, and both are severity framings, not action items.

**A. How costly is the mixed-framework estate under opportunistic migration?**
- *Adversary:* without a finish line, benefits may reach 20% of tests while 100% pays the mixed-codebase tax; worse, the Advocate's own steelman 2 tied safe parallelization to explicit-dependency tests, making parallelism downstream of a migration that has no finish line — the flag is not "free."
- *Advocate:* opportunistic migration is benefit-weighted, not uniform-random — files migrate when touched, so migration concentrates in hot packages where readability and triage pay most, while cold packages generate little of the targeted pain.

**B. How fragile is the parallelism claim?**
- *Adversary (narrowed):* still the least-verified claim, but credits the per-package fallback — failure now means "the benefit shrinks to the isolable subset," not "the benefit evaporates."
- *Advocate:* xdist fails gracefully per-package, parallelism is one argument of three, and isolation failures the pilot surfaces are partly latent test defects worth finding anyway.

### ## Rulings

**Point A — split, with the sharper catch going to the Adversary.** The Advocate wins the entropy argument on mechanism: touch frequency correlates with the pain the proposal targets, so unmanaged migration lands where it pays most, and the Adversary offered no evidence for the 20% figure. But the Adversary landed a real hit that the Advocate never answered: steelman 2 claimed fixtures are "the enabling work" for xdist, which quietly converts parallelism from "flip a flag" into "downstream of migration progress." On this record that inference stands, and it means the finish-line-versus-permanent-mix choice in the governance page is not cosmetic — in packages where the pilot shows isolation failures, the parallelism benefit waits on funded migration, not entropy. No compromise is needed; the agreed governance page is where the author resolves this, now with the stakes correctly priced.

**Point B — Advocate wins.** The Adversary itself narrowed the objection after crediting the per-package fallback. The realistic downside of the parallelism claim is a smaller speedup, not zero, and the pilot both sides agreed to will replace this dispute with two numbers. Nothing further to rule.

### ## Judge's recommendation

Adopt the proposal amended with a "gates before commitment" section, ordered by the failure mode each gate prevents:

1. Compatibility grep plus collect-count parity blocker — before the runner swap, because its failure mode (fail-green test loss) is invisible after the fact. One day.
2. Shadow CI job, non-blocking, with per-package cutover on parity — because it is the single mechanism that proves the reversibility the whole risk story rests on. Two to four weeks of wall time, little labor.
3. xdist pilot on two or three representative packages, recording baseline and speedup — before the proposal cites parallelism as a benefit. About a week.
4. Governance page, including the explicit funded-finish-line-or-accepted-mix decision — before declaring the plan complete. A day of writing, plus one genuine decision only you can make.

My reasoning: this debate ended in near-total convergence. The destination went uncontested, four of five objections resolved into amendments the Advocate adopted, and the fifth was dropped. The total gate cost is roughly two days of work plus shadow-CI calendar time, all before any hard-to-reverse step. The one decision the gates cannot make for you is Point A's residue: whether to fund a migration finish line. The Adversary's steelman-2 catch means that choice partly controls whether the parallelism benefit ever reaches isolation-unsafe packages — decide it with the pilot results in hand, not by default.

### ## Your decision

1. **Adopt as amended (recommended).** Run gate 1 this week, start the shadow job, run the pilot, write the governance page. Within the governance page, choose: (a) funded finish line with a date, or (b) permanent mixed estate accepted in writing.
2. **Adopt as originally written.** Swap the runner now, defer all gates. This accepts the fail-green collection risk that both debaters, independently, called the worst failure mode. No one in the transcript defends this option.
3. **Defer the decision until gates 1 and 3 report.** Costs one to two weeks; buys hard numbers before commitment. Rational only if you doubt the destination — which neither side does.
4. **Reject; stay on unittest.** The ecosystem-default argument stands unrebutted on this record. Choosing this means supplying an argument the debate did not produce.
