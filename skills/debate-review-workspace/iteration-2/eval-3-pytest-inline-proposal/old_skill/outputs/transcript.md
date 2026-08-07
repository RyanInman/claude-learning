# Debate Review Transcript

**Artifact:** /Users/admin/claude-learning/skills/debate-review-workspace/iteration-2/eval-3-pytest-inline-proposal/old_skill/work/proposal.md
**Date:** 2026-08-06

Append-only. Each role writes under its own heading and never edits another role's text.

---

## Phase 1 — Defender: Opening Statement

The proposal: migrate our Python monorepo's test suite (~6,000 tests) from unittest to
pytest. The goal is not tooling fashion — it is to remove three concrete drags on test
authorship and CI speed.

**Decision 1: adopt pytest fixtures over setUp inheritance.** Our test base classes have
grown into inheritance hierarchies where a test class inherits setUp state it never uses,
and changing a shared setUp risks breaking distant subclasses. Fixtures invert this:
each test declares exactly the dependencies it needs, and fixtures compose without
inheritance. This is the strongest argument because it changes how every future test is
written, not just how old ones run.

**Decision 2: use parametrize to collapse copy-pasted variants.** A meaningful fraction of
our 6,000 tests are near-duplicates differing only in input values, because unittest has
no first-class parametrization (subTest exists but reports poorly and is rarely used
here). `@pytest.mark.parametrize` turns N copies into one test plus a case table, which
shrinks the suite's maintenance surface.

**Decision 3: buy parallelism via the plugin ecosystem.** `pytest-xdist` gives
multi-process test execution with a command-line flag. Building equivalent parallelism on
unittest means writing and owning runner infrastructure. CI wall-clock time is a real
cost today and grows with the suite.

**A key fact lowering migration risk:** pytest runs unittest-style TestCase classes
natively. The 6,000 existing tests do not need rewriting on day one — the runner can
switch first, and tests can migrate to pytest idioms incrementally, or never.

**Constraints and honest uncertainty:**

- *Migration scale (6k tests):* real, but mitigated by pytest's unittest compatibility.
  The cost is not "rewrite 6k tests"; it is "switch the runner, then convert
  opportunistically."
- *CI churn:* one-time cost. I have not scoped it precisely — this is the decision I am
  least sure of. If our CI does exotic things with unittest's runner API or custom
  TestResult classes, the cost grows.
- *Team familiarity:* some developers know unittest well. pytest's surface for a test
  author is smaller (plain functions, plain asserts), so I judge the learning curve
  shallow, but fixture scoping and autouse have real gotchas.
- *xdist caveat I flag myself:* parallelism is only "free" if tests are independent.
  Tests sharing databases, ports, or global state will need isolation work before xdist
  pays off.

I want the best outcome, not victory: if a staged or partial migration beats a full one,
I will take it.

## Phase 2 — Clarifying Questions

### Adversary's questions

1. What does the CI pipeline actually do with unittest today — does it use a custom runner, custom TestResult classes, the `load_tests` protocol, or test sharding logic, and has anyone scoped the replacement work in engineer-days?

2. What fraction of the 6,000 tests share external state (databases, ports, filesystem paths, module-level globals), and do you have any measurement of current CI wall-clock time versus the projected time with xdist after isolation work?

3. What is the concrete plan for the incremental migration after the runner switch — is there a defined end state, an owner, and a mechanism (lint rule, review policy) that prevents the codebase from living in two test idioms indefinitely, and which pytest features are you accepting won't work on the unmigrated TestCase classes (e.g., fixtures injected into TestCase methods, parametrize on them)?

### Advocate's questions

1. Has anyone measured what fraction of the ~6,000 tests already pass under pytest's native unittest collection (e.g., a trial `pytest` run on the current tree), and does the suite use unittest features pytest does not support, such as `load_tests` hooks or custom TestResult/TestRunner classes?
2. What does CI wall-clock time look like today, and are the tests largely independent (no shared databases, ports, or module-level global state), so I can gauge how much of the xdist parallelism win is realizable without isolation work?
3. Does the CI pipeline invoke unittest through a plain command line (`python -m unittest ...`) that a `pytest` command can replace one-for-one, or does it depend programmatically on unittest's runner API for reporting, sharding, or result parsing?

### Judge's questions

1. CI coupling depth: does the current CI invoke tests through a plain `python -m unittest` command, or does it hook into unittest's runner API or custom TestResult classes (for reporting, sharding, retries)? The Defender named this his least-certain point, and the answer determines whether "CI churn" is a config edit or an infrastructure project.

2. Test isolation baseline: roughly what fraction of the 6,000 tests touch shared state (databases, ports, files, globals)? The xdist parallelism benefit — argument 3 — depends entirely on this number, and no one has estimated it yet.

3. Compatibility limits: which pytest features are unavailable to tests that stay as unittest TestCase classes (fixtures and parametrize do not apply to them), and is the plan's value contingent on tests actually converting, or does the runner switch alone deliver enough? This tells me whether "migrate incrementally, or never" is a real mitigation or deferral of the whole cost.

### Defender's answers

All three roles asked essentially the same three questions, so I answer them as three
topics. Where the team has not measured something, I say so — treating an unknown as a
known would corrupt the debate.

**Topic 1 — CI coupling depth (Adversary Q1, Advocate Q3, Judge Q1).** Not scoped in
engineer-days. To the best of my knowledge the pipeline invokes the suite through a
standard command-line unittest invocation and consumes results as XML for the CI
dashboard; I have no evidence of custom TestResult classes or programmatic runner-API
use, but I have not audited for `load_tests` hooks or sharding logic. I flagged this in
my opening as my least-certain point, and it still is. Honest answer: unknown pending a
one-day audit. If the audit finds runner-API coupling, the CI cost estimate must grow
from "swap the command and the XML flag (`pytest --junitxml`)" to real work.

**Topic 2 — shared state and wall-clock (Adversary Q2, Advocate Q2, Judge Q2).** Not
measured. No one has run the suite under xdist or audited for shared databases, ports,
or module-level globals. Current CI wall-clock is long enough that developers complain
and it was a motivator for this proposal, but I cannot give a number or a projected
speedup. I concede the xdist benefit is currently an expectation, not a measurement.

**Topic 3 — incremental migration plan and compatibility limits (Adversary Q3, Advocate
Q1, Judge Q3).** No trial `pytest` collection run has been done on the tree. The
compatibility facts as I understand them: pytest collects and runs TestCase classes
natively, but unmigrated TestCase tests cannot use `@pytest.mark.parametrize` on methods
or receive fixtures as arguments (autouse fixtures can reach them indirectly via class
attributes, which is a workaround, not the idiom). `load_tests` protocol and
subtests have partial/limited support under pytest. So: the runner switch alone delivers
unified invocation, better failure reporting, plugin access (including xdist, which does
run TestCase tests), and richer selection — but arguments 1 and 2 (fixtures,
parametrize) only pay off for tests actually converted. There is currently no defined
end state, no named owner, and no ratchet mechanism (lint rule or review policy) for
conversion; "migrate incrementally, or never" is today an intention, not a plan. That is
a fair gap to attack.

## Phase 3 — Adversary's Case

I accept the premise that pytest is the better tool. My objections target the proposal as
argued: its two strongest benefits are contingent on work it does not plan, its one
CI-speed benefit is unmeasured, and its "low-risk" runner switch carries a silent
correctness hazard.

### Objection 1 — The two strongest arguments deliver nothing under the actual plan

**Problem.** Arguments 1 and 2 (fixtures, parametrize) only pay off for tests converted to
pytest idioms. The migration plan is "switch the runner, then convert opportunistically,
or never." Under that plan, all 6,000 tests stay as TestCase classes, where parametrize
does not work on methods and fixtures cannot be injected as arguments. The proposal's
headline benefits are gated on conversion work that has no owner, no end state, and no
mechanism — so the expected value of arguments 1 and 2, as planned, is near zero.

**Evidence.** The Defender's Topic 3 answer concedes every element: unmigrated TestCase
tests cannot use parametrize or fixture injection; "there is currently no defined end
state, no named owner, and no ratchet mechanism"; "migrate incrementally, or never is
today an intention, not a plan." Industry experience with opportunistic migrations and no
ratchet is that they stall: the old idiom persists wherever the code is not otherwise
touched.

**Better way.** Attach a conversion ratchet to the proposal before approval: (a) a named
owner; (b) a lint or review rule that new test files must be pytest-style, so the TestCase
count only decreases; (c) a boy-scout rule — convert a test file when you materially edit
it; (d) a quarterly count of remaining TestCase files as the progress metric. If the team
will not fund the ratchet, re-scope the proposal honestly as "runner switch only" and let
it be judged on the runner's benefits alone (unified invocation, reporting, selection,
xdist), not on fixtures and parametrize it will not deliver.

### Objection 2 — The xdist speedup is an unmeasured expectation, and isolation cost may be runner-independent

**Problem.** CI wall-clock pain is the proposal's stated motivator, and xdist is its only
argument that addresses it. But no one has run the suite under xdist, audited shared
state, or recorded a baseline wall-clock number. If a large fraction of tests share
databases, ports, or globals, the isolation work needed before xdist pays off could
exceed the migration itself. Worse for the argument: that isolation work is
runner-independent — once tests are isolated, unittest suites can also be parallelized by
sharding across CI workers — so xdist may not be a differentiating benefit at all, just a
convenient flag on top of work the proposal has not costed.

**Evidence.** The Defender's Topic 2 answer: "Not measured. No one has run the suite
under xdist or audited for shared databases, ports, or module-level globals... I concede
the xdist benefit is currently an expectation, not a measurement." The Defender's own
opening flags the same caveat.

**Better way.** Run a half-day spike before deciding: on a branch, run
`pytest -n auto` over the current tree, record pass rate and wall-clock against the
recorded unittest baseline. Three outcomes, all useful: it mostly passes (the benefit is
real and now quantified), it fails broadly (the isolation cost is now visible and must be
added to the proposal), or collection itself breaks (see Objection 3 — you needed to know
anyway).

### Objection 3 — The runner switch can silently drop tests

**Problem.** The "key fact lowering migration risk" — pytest runs TestCase classes
natively — hides a correctness hazard: pytest's collection is not identical to unittest
discovery. `load_tests` hooks are not honored and subtest support is partial, both
conceded by the Defender, and the tree has not been audited for either. A runner switch
that silently collects fewer tests than before is worse than no switch: CI goes green
while coverage quietly shrinks, and nothing alerts anyone.

**Evidence.** Defender's Topic 3: "`load_tests` protocol and subtests have partial/limited
support under pytest," and Topic 1: "I have not audited for `load_tests` hooks or sharding
logic." No trial `pytest --collect-only` run has been done, so today nobody can state the
collected-test delta between the two runners.

**Better way.** Make collection parity a hard gate on the cutover: diff the test IDs from
unittest discovery against `pytest --collect-only -q`, and require the sets to match (or
every difference to be explained in writing) before CI switches. This is a one-script
check and converts a silent risk into a visible, verifiable one.

### Objection 4 — Without a ratchet, "team familiarity" becomes a permanent tax, not a transition cost

**Problem.** The proposal books "team familiarity" as a one-time learning curve. But the
plan explicitly allows a terminal state where the suite lives in two idioms forever. In
that state every developer must know unittest, pytest, and the interop seam between them
— including genuinely confusing corners like autouse fixtures reaching TestCase tests via
class attributes, and setUpClass interacting with fixture scopes. That is a permanent
increase in the knowledge needed to work on tests, which is the opposite of the
maintainability the proposal promises.

**Evidence.** Defender's Topic 3 concedes "or never" is an allowed outcome and names the
class-attribute workaround as "a workaround, not the idiom." Mixed-idiom suites are a
well-known failure mode of runner-first migrations that never fund conversion.

**Better way.** Same ratchet as Objection 1, plus one page of written interop guidance
(what unconverted tests can and cannot use) committed alongside the cutover. If the team
accepts "never" as a real outcome, the proposal must count the two-idiom tax as a
permanent cost, not a transition cost, and re-weigh the decision.

### Objection 5 — The decision is sequenced before its cheapest de-risking steps

**Problem.** Every load-bearing unknown in this debate — CI coupling depth, shared-state
fraction, collection parity — resolves with about two days of work: a one-day CI audit
(the Defender's own estimate), a `--collect-only` diff, and the xdist spike. Approving
the migration before running them means committing on expectations where data is nearly
free, and the commitment buys nothing: the cutover cannot land before the audit happens
anyway.

**Evidence.** Defender's answers: "unknown pending a one-day audit" (Topic 1), "not
measured" (Topic 2), "no trial pytest collection run has been done" (Topic 3). Three of
three factual questions from three independent roles came back unmeasured.

**Better way.** Split the decision. Approve the ~2-day spike now (CI audit, collect-only
diff, xdist trial run — all read-only, no production risk). Re-present the proposal with
those three numbers attached, at which point Objections 2 and 3 become data instead of
argument, and the go/no-go is made on evidence.

## Phase 4 — Advocate's Case

### Part 1 — The steelman: the strongest honest case for the proposal as-is

**Strength 1 — The risk profile is asymmetric, and that is rare for a migration.** Most
migrations of this scale require touching the assets to get any benefit. This one does
not: pytest runs TestCase classes natively, so the 6,000 tests stay byte-identical while
the runner changes underneath them. That makes the cutover reversible — keep the unittest
invocation alive in CI until parity is proven, and rollback is a one-line revert because
no test was edited. The Defender undersold this: it is not merely "lower migration risk,"
it is the property that lets every downstream risk be gated instead of gambled.

**Strength 2 — The value floor with zero conversion is still positive.** The Adversary
treats "runner switch only" as a consolation prize, but the runner alone delivers:
unified `-k`/`-m` test selection, better failure output, `--junitxml` for the existing CI
dashboard, and the plugin ecosystem — including xdist, which the Defender confirmed runs
TestCase tests. Above that floor, every *new* test written from the cutover onward gets
fixtures, plain asserts, and parametrize immediately. A monorepo's test count grows;
in a growing suite the pytest-idiom share rises every quarter even if not one legacy test
is ever converted. Arguments 1 and 2 are not gated on converting the 6,000 — they are
gated on writing test number 6,001, which happens next week regardless.

**Strength 3 — Every alternative carries the same costs plus one the proposal avoids.**
Doing nothing keeps the setUp inheritance tangle, the copy-pasted variants, and the CI
wall-clock pain that motivated the proposal. Building parallelism on unittest means
writing and permanently owning runner infrastructure — sharding, load balancing, result
merging — that pytest-xdist ships maintained by someone else. The isolation work the
Adversary correctly flags (Objection 2) is owed under *every* option that pursues
parallelism. The proposal is the only option on the table whose marginal cost is mostly
one-time and whose tooling is maintained upstream.

**Strength 4 — The ecosystem argument, which the Defender never made.** pytest is the de
facto standard for Python testing. New hires arrive knowing it; documentation, plugins
(coverage, flake detection, timeouts, randomization), and third-party integrations are
pytest-first; unittest evolves at the pace of the standard library. "Team familiarity"
is listed as a cost, but it points the other way over any multi-year horizon: the team
member who must learn something today is the unittest-only developer, and that debt grows
the longer the switch is deferred.

### Part 2 — Answers to the Adversary's objections

**Objection 1 (headline benefits deliver nothing under the actual plan) — dispute the
problem; accept one piece of the better way.** The "expected value near zero" claim
assumes benefits accrue only through converting old tests. Wrong denominator: as argued
in Strength 2, fixtures and parametrize pay on every new test from day one, and new tests
arrive continuously in a monorepo. The value is not gated on a conversion program; it is
gated on the runner switch. That said, I accept the Adversary's ratchet items (a) and (b)
— a named owner and a rule that new test files must be pytest-style — as friendly
amendments: they are cheap, they guarantee the TestCase count only falls, and they cost
the proposal nothing. I dispute that the full ratchet (boy-scout rule, quarterly metric)
is a *precondition for approval*; it is follow-through policy, and making approval hostage
to it inverts the priority. The re-scope to "runner switch only" is unnecessary once the
new-test rule exists, because the fixtures/parametrize benefit is then structurally
guaranteed, not aspirational.

**Objection 2 (xdist speedup unmeasured; isolation is runner-independent) — dispute the
better-way's premise; accept the spike.** The claim that isolated tests make xdist
non-differentiating because "unittest suites can also be parallelized by sharding across
CI workers" understates what sharding costs: someone must build and own shard assignment,
balancing, and result merging — exactly the runner infrastructure Decision 3 exists to
avoid — and coarse file-level shards balance worse than xdist's per-test distribution.
Isolation work being runner-independent is an argument *for* pytest, not against it: it
is the option where isolation, once paid for, converts to parallelism with a flag instead
of a project. I concede the benefit is unmeasured — the Defender already conceded it —
and I accept the half-day `pytest -n auto` spike without reservation. Note what accepting
it means: the spike is only this cheap *because* of the compatibility bridge in Strength 1.
The proposal's own architecture is what makes the Adversary's test of it nearly free.

**Objection 3 (the runner switch can silently drop tests) — concede.** This is the
Adversary's best point and I will not defend against it. The evidence is real: `load_tests`
is not honored, subtest support is partial, the tree is unaudited, and a green CI over a
silently smaller test set is strictly worse than the status quo. What convinced me is the
cost asymmetry of the fix: a `--collect-only` diff against unittest discovery is one
script, and it converts an invisible correctness hazard into a visible, verifiable gate.
The collection-parity gate should be a hard precondition of cutover, written into the
proposal. I note this amends the proposal rather than defeating it — but the point itself
is conceded in full.

**Objection 4 (two-idiom permanent tax) — dispute the problem's size, accept the
mitigation.** The "every developer must know both idioms plus the interop seam" framing
overstates the seam. An unconverted TestCase test remains a plain unittest test: reading
or editing it requires only unittest knowledge, exactly as today. The confusing corners
the Adversary names — autouse fixtures reaching into TestCase via class attributes,
setUpClass versus fixture scopes — arise only when someone deliberately mixes idioms
inside one test class, which the one-page interop guide should simply prohibit ("convert
the file or leave it alone"). With that rule the seam is a boundary, not a blend, and the
residual tax is "developers know both frameworks" — which Strength 4 argues they must
anyway, since pytest is the ecosystem default. I accept the interop page; it is one page.
I dispute that "never converting" forces re-weighing the decision, because the value
floor of Strength 2 is positive even in that terminal state.

**Objection 5 (decision sequenced before cheap de-risking) — accept the spike, dispute
the split.** The two days of audits are obviously worth running; nothing in the proposal
conflicts with them, and I endorse making all three (CI audit, collect-only diff, xdist
trial) preconditions of cutover. But the Adversary's "commitment buys nothing" claim is
wrong on two counts. First, the spikes size the *cost* of the migration; no spike outcome
bears on whether pytest is the right destination, which is the actual decision before the
author — the arguments about fixtures, parametrize, and ecosystem are not waiting on any
measurement. Second, commitment buys the one benefit with no gate at all: the moment the
direction is approved, the new-test rule from Objection 1 can take effect and every test
written during the spike fortnight is born pytest-style instead of adding to the
conversion backlog. The right structure is not "defer the decision, run the spike" but
"approve the destination now; gate the cutover on the three checks." That preserves the
Adversary's entire evidentiary demand while stopping the team from relitigating the
direction each quarter.

### Summary position

The proposal survives all five objections with amendments, not retreat. Conceded in full:
the collection-parity gate (Objection 3). Accepted as amendments: the named owner and
new-tests-are-pytest rule, the interop page, and the three pre-cutover checks. Disputed
and, I contend, answered: that the headline benefits have near-zero expected value, that
xdist is non-differentiating, that the two-idiom tax is permanent and heavy, and that
approval must wait on the spikes. Every accepted amendment is cheap precisely because of
the proposal's own core design choice — the compatibility-bridge cutover — which is the
strongest evidence that the original plan was built correctly.

## Phase 5 — Adversary's Rebuttal

Disposition: two dropped, three sustained (one uncontested, one narrowed, one with a
compromise attached).

### Objection 1 (headline benefits deliver nothing under the plan) — DROPPED

The Advocate's denominator correction convinced me. I computed expected value only over
the existing 6,000 tests; Strength 2 shows fixtures and parametrize pay on every test
written after cutover, and a monorepo writes test 6,001 next week regardless. "Near-zero
expected value" was wrong. The Advocate also accepted the two ratchet items that do the
structural work — a named owner and the new-tests-are-pytest rule — which is what my
better way actually needed; the boy-scout rule and quarterly metric were pressure toward
that end, and with an owner in place I no longer press them. One condition on the drop:
both accepted amendments must be written into the proposal text, not just this
transcript, because an amendment that lives only in a debate record is not policy.

### Objection 2 (xdist unmeasured; isolation runner-independent) — DROPPED

Two things convinced me. First, the sharding counter: parallelizing isolated unittest
tests via CI sharding requires building and owning shard assignment, balancing, and
result merging — exactly the runner infrastructure Decision 3 exists to avoid — and
file-level shards balance worse than xdist's per-test distribution. So "isolation is
runner-independent" does not make xdist non-differentiating; it makes pytest the option
where isolation, once paid, converts to parallelism with a flag. Second, the measurement
gap I raised is fully resolved procedurally: all sides now treat the `pytest -n auto`
spike as a precondition, so the unmeasured expectation becomes a number before anything
irreversible happens.

### Objection 3 (runner switch can silently drop tests) — SUSTAINED, uncontested

The Advocate conceded in full. There is nothing to rebut; I carry it into the record as
an agreed hard gate: diff unittest discovery against `pytest --collect-only -q`, and
require the test-ID sets to match — or every difference explained in writing — before CI
switches runners.

### Objection 4 (two-idiom permanent tax) — SUSTAINED, narrowed

The Advocate's defense rests on the claim that the confusing seam "arises only when
someone deliberately mixes idioms inside one test class," so a one-page rule — "convert
the file or leave it alone" — turns the seam into a boundary. That rule is not
enforceable, because pytest crosses the boundary implicitly: an autouse fixture defined
in any `conftest.py` applies to every test below it in the tree, TestCase tests
included, with no one deliberately mixing anything. Suite-wide concerns — logging
config, tmp-dir policy, and above all the isolation work the Objection 2 spike may
reveal — are exactly what teams implement as session-scoped autouse conftest fixtures.

Worse, the isolation work has a second seam problem the Advocate did not address: it
cannot reach the 6,000 unconverted tests as injected fixtures at all, so it must be
built in unittest idiom (setUp mixins) or through the class-attribute workaround the
Defender himself called "a workaround, not the idiom." The two-idiom tax therefore
concentrates precisely where the proposal's parallelism benefit needs engineering.

Narrowed better way: keep the interop page, and add one rule to it — suite-wide autouse
fixtures must be TestCase-safe (no injected arguments the TestCase tests cannot
receive), and isolation infrastructure for an unconverted subtree must be written in
unittest idiom or dual-idiom until that subtree converts. I drop the broader demand to
re-weigh the whole decision under the "never converted" scenario: Strength 2's value
floor holds even in that terminal state, and I was wrong to treat the tax as
decision-reversing rather than plan-shaping.

### Objection 5 (decision sequenced before its cheapest de-risking steps) — SUSTAINED

The Advocate's approve-now-gate-cutover structure rests on one concrete claimed benefit
of early approval: "every test written during the spike fortnight is born pytest-style
instead of adding to the conversion backlog." That claim is technically impossible.
unittest cannot collect pytest-style function tests, so until the runner actually cuts
over — which the Advocate himself gates on the three checks — a pytest-style test does
not run in CI. The new-test rule takes effect at cutover under either sequencing;
approving two weeks earlier activates nothing. Strip that claim and the two structures
deliver identical evidence at identical times, differing only in anchoring risk: an
already-approved "destination" survives bad spike numbers as a sunk commitment ("we
decided; find a way"), while a split decision prices them in.

The Advocate's second argument — "no spike outcome bears on whether pytest is the right
destination" — proves too much. A destination decision at unmeasured cost is not a
decision; if the CI audit finds runner-API coupling and the collect-only diff finds a
large `load_tests` delta, the cost side moves enough to flip the go/no-go, which is why
the checks exist.

Compromise I will accept: approve the direction now if and only if the approval is
written as conditional — the three checks are hard gates with pre-agreed pass criteria
(collection parity per Objection 3; CI audit finds no runner-API coupling beyond an
agreed effort bound; xdist spike shows a measured wall-clock gain), and any failed gate
returns the proposal for re-decision rather than remediation-by-default. Under that
wording the distance between our positions is zero and I will drop this objection in
Phase 6.

## Phase 6 — Advocate's Surrebuttal

Objections 1 and 2 were dropped in Phase 5; I address only the Adversary's condition on
the drop of Objection 1, then the three sustained objections.

**Condition on Objection 1's drop — accepted.** The two amendments (named owner,
new-tests-are-pytest rule) go into the proposal text, not just this transcript. The
Adversary is right that an amendment living only in a debate record is not policy.

### Objection 3 (silent test drops) — conceded in Phase 4; concession stands

Nothing changed and nothing should. The agreed hard gate goes into the record as written:
diff unittest discovery against `pytest --collect-only -q`, require the test-ID sets to
match or every difference explained in writing, before CI switches runners. What
convinced me in Phase 4 still holds — a green CI over a silently smaller test set is
strictly worse than the status quo, and the fix costs one script.

### Objection 4 (two-idiom tax at the seam) — defended on severity; amendment accepted

The Adversary's technical claim is correct and I do not contest it: an autouse fixture in
a `conftest.py` applies to every test below it, TestCase tests included, so "convert the
file or leave it alone" cannot by itself keep the seam closed. That was a real hole in my
Phase 4 defense.

But the narrowed objection overstates where the tax lands, and this is the new substance:
the isolation work xdist needs is overwhelmingly *ambient*, not *injected*. Per-worker
isolation is normally written as a session-scoped autouse fixture that keys resources off
the xdist worker id and delivers them through the environment — a per-worker database
name, a per-worker tmp root, a rebound port — with nothing handed to any test as an
argument. The fixture may request `worker_id` itself; the TestCase test receives nothing
and needs to receive nothing. That is not the class-attribute workaround and it is not
unittest-idiom mixin code — it is ordinary pytest, and it reaches all 6,000 unconverted
tests today. Only isolation that must hand a *value* to the test body (a per-test client
handle, say) hits the seam the Adversary describes, and that is the minority case.

So the tax does not "concentrate precisely where the parallelism benefit needs
engineering" — most of that engineering lives on the safe side of the seam. I accept the
Adversary's narrowed rule for the interop page without reservation, because it codifies
exactly this design: suite-wide autouse fixtures must be TestCase-safe (ambient effects
only, no arguments the test must receive), and value-consuming isolation for an
unconverted subtree is written in unittest idiom until that subtree converts. The rule
costs one paragraph and makes the natural design the mandatory one. With it, the residual
objection is a maintenance guideline, not a cost that shapes the decision — which the
Adversary himself granted by dropping the re-weigh demand.

### Objection 5 (sequencing) — specific claim conceded; compromise accepted

**Conceded:** my "tests born pytest-style during the spike fortnight" claim. The
Adversary's proof is exact and I cannot answer it: unittest discovery cannot collect
pytest-style function tests, so until the runner cuts over, a pytest-style test does not
run in CI, and the new-test rule activates at cutover under either sequencing. Approving
two weeks earlier activates nothing. That was the only concrete early-approval benefit I
named, and it was wrong.

**Accepted:** the Adversary's compromise, in full and as worded. Approval is written as
conditional: the three checks are hard gates with pre-agreed pass criteria — collection
parity per Objection 3, CI audit finds no runner-API coupling beyond an agreed effort
bound, xdist spike shows a measured wall-clock gain — and any failed gate returns the
proposal for re-decision, not remediation-by-default.

I accept this not as a loss but because it delivers what my approve-now structure was
actually for, minus the flaw the Adversary exposed. My real concern was relitigation risk
— a team that re-argues the direction each quarter. Conditional approval with pre-agreed
pass criteria answers that concern *and* the Adversary's anchoring concern
simultaneously: the criteria are fixed before the data arrive, so a failed gate cannot be
argued down as "we decided; find a way," and a passed gate cannot be relitigated as "but
are we sure about pytest." Fixing the pass/fail line in advance is strictly better than
either of our original structures. The Adversary said that under this wording the
distance between us is zero; I confirm zero from my side.

### Final position for the Judge

Every objection now resolves: 1 and 2 dropped; 3 conceded with the collection-parity
gate agreed; 4 answered on severity with the TestCase-safe-fixture rule accepted; 5
resolved by conditional approval with pre-agreed gate criteria. The amended proposal —
compatibility-bridge cutover, named owner, new-tests-are-pytest rule, interop page with
the seam rule, three hard gates with written pass criteria — is stronger than the
original and preserves its core design. Nothing before the Judge remains contested.

## Phase 7 — Judge's Interim: Assessment and Compromises

Skipped. Main-agent check of phases 5–6: objections 1 and 2 dropped in phase 5;
objection 3 conceded by the Advocate with the collection-parity gate agreed; objection
4's narrowed amendment accepted by the Advocate in phase 6; objection 5 resolved by the
Adversary's conditional-approval compromise, accepted by the Advocate in full and as
worded. No contested point remains, so there is nothing for the Judge to broker.

## Phase 8 — Reactions to Compromises

Skipped — see phase 7 note. All resolutions were reached inside the debate itself.

## Phase 9 — Judge's Final Report

## Agreed changes

All three roles converged on six amendments. Each is ready to act on, and per the
Adversary's condition (accepted by the Advocate in Phase 6), every one must be written
into the proposal text itself — an amendment living only in this transcript is not policy.

1. **Named conversion owner.** One person owns the incremental migration and its progress.
   (From Adversary Objection 1; accepted Phase 4, drop conditioned and confirmed Phases 5–6.)
2. **New-tests-are-pytest rule.** New test files must be pytest-style from cutover onward,
   so the TestCase count only falls. (Same provenance as item 1.)
3. **Collection-parity hard gate.** Before CI switches runners, diff unittest discovery
   against `pytest --collect-only -q` and require the test-ID sets to match, or every
   difference explained in writing. (Adversary Objection 3; conceded in full by the
   Advocate — the debate's cleanest exchange.)
4. **One-page interop guide with the seam rule.** Suite-wide autouse fixtures must be
   TestCase-safe: ambient effects only (per-worker database names, tmp roots, ports keyed
   off worker id), no arguments the test body must receive. Value-consuming isolation for
   an unconverted subtree is written in unittest idiom until that subtree converts.
   (Adversary Objection 4, narrowed; Advocate accepted the rule while winning the
   severity argument — see Contested points.)
5. **Three pre-cutover checks as hard gates, roughly two days of read-only work:**
   the CI coupling audit, the collect-only diff (item 3), and a `pytest -n auto` spike
   against a recorded unittest wall-clock baseline. (Adversary Objections 2 and 5;
   endorsed by the Advocate in Phase 4.)
6. **Conditional-approval structure.** Approval of the direction is written as
   conditional: the three gates carry pre-agreed pass criteria, and any failed gate
   returns the proposal for re-decision, not remediation-by-default. (Adversary's Phase 5
   compromise, accepted by the Advocate in Phase 6 "in full and as worded.")

## Contested points

None remain. For the record, how each resolved — and who won where the sides genuinely
disagreed:

- **Objection 1 (headline benefits deliver nothing).** The Advocate won on the merits.
  The denominator correction — fixtures and parametrize pay on every new test, and a
  monorepo writes test 6,001 next week — was a real refutation, and the Adversary said so
  when dropping it. The ratchet items survived as agreed changes 1–2.
- **Objection 2 (xdist unmeasured, non-differentiating).** The Advocate won the argument
  (CI sharding costs exactly the runner infrastructure the proposal avoids); the
  Adversary won the procedure (the spike is now a hard gate). Both halves stand.
- **Objection 3 (silent test drops).** The Adversary won outright; the Advocate conceded
  in Phase 4 and never wavered.
- **Objection 4 (two-idiom tax).** Split, and fairly so. The Adversary's technical claim
  was correct — conftest autouse fixtures cross the seam with no one deliberately mixing
  idioms, which broke the Advocate's Phase 4 defense. The Advocate then won on severity:
  xdist isolation work is overwhelmingly ambient, not injected, so it reaches all 6,000
  TestCase tests as ordinary pytest. The accepted seam rule (agreed change 4) codifies
  the Advocate's design under the Adversary's constraint.
- **Objection 5 (sequencing).** The Adversary's proof that "tests born pytest-style
  during the spike fortnight" is technically impossible was exact, and the Advocate
  conceded it. The conditional-approval compromise then genuinely dissolved the dispute:
  it answers the Advocate's relitigation concern and the Adversary's anchoring concern
  with one mechanism. Both sides declared the distance zero; I verified the exchange and
  agree.

## Compromises

None needed — all objections resolved in debate. (The one formal compromise, conditional
approval with pre-agreed gate criteria, was proposed by the Adversary inside Phase 5 and
accepted by the Advocate inside Phase 6, so it appears above as agreed change 6 rather
than as a Phase 7 brokered item.)

## Judge's recommendation

**Adopt the amended proposal under the conditional-approval structure — with one task the
debate left unfinished: quantify the two gate criteria that are still words, not numbers.**

The convergence here is real, not performative. I checked each drop and concession
against the argument that produced it: Objection 1 fell to an actual counter-argument,
Objection 3 was conceded against interest, and Objection 5's resolution required the
Advocate to abandon a claim the Adversary had proven impossible. No one split differences
to look agreeable.

The amended proposal is also strictly stronger than the original. The Defender's opening
honestly flagged three unknowns (CI coupling, shared state, compatibility limits); the
debate converted all three from open risks into gated checks. The Advocate's best
structural point holds throughout: the compatibility-bridge cutover is what makes every
one of these checks cheap, which is evidence the core design was right.

The unfinished task: agreed change 6 requires "pre-agreed pass criteria," but two of the
three gates still lack numbers. Gate 1's criterion is "no runner-API coupling beyond an
agreed effort bound" — no bound was agreed. Gate 3's is "a measured wall-clock gain" —
any gain, or a meaningful one? A conditional approval whose conditions are vague
reintroduces exactly the remediation-by-default risk the compromise exists to prevent.
Set both numbers (for example: an effort bound in engineer-days for CI remediation, and a
minimum speedup or pass-rate threshold for the xdist spike) before signing the approval.
Gate 2, collection parity, is already precise.

## Your decision

You are choosing between four options:

1. **Conditional approval as amended** (my recommendation). Approve pytest as the
   destination now; write agreed changes 1–6 into the proposal text; set the two missing
   gate numbers; run the ~2-day checks; cut over only if all three gates pass, and return
   to re-decision if any fails.
2. **Split decision.** Approve only the 2-day spike now and re-present the proposal with
   the three measurements attached. This was the Adversary's original Objection 5
   position; he moved off it, but it remains coherent if you distrust conditional
   approvals surviving bad news in your team's culture.
3. **Runner switch only.** Re-scope to the cutover benefits alone (unified invocation,
   reporting, selection, xdist on TestCase tests) with no conversion program. The debate
   established this floor is positive, but both sides agreed the ratchet items are cheap,
   so choosing this forfeits value for little saved cost.
4. **Reject / status quo.** Keep unittest. Nothing in the debate supports this — even the
   Adversary opened by accepting pytest as the better tool — but it is the null option
   you are entitled to.
