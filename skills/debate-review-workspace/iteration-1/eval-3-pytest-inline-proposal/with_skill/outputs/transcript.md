# Debate Review Transcript

**Artifact:** /Users/admin/claude-learning/skills/debate-review-workspace/iteration-1/pytest-inline-proposal/with_skill/work/proposal.md
**Date:** 2026-08-01

Append-only. Each role writes under its own heading and never edits another role's text.

---

## Phase 1 — Defender: Opening Statement

<!-- Defender -->

**Goal.** Move the Python monorepo's ~6,000-test suite from unittest to pytest to reduce test
authoring friction and unlock parallel execution. This is a developer-productivity and CI-speed
investment, not a correctness fix — the current suite works.

**Key decisions and why:**

1. **Fixtures over setUp inheritance.** Our test base classes have grown into multi-level
   inheritance chains; understanding what state a test starts with means reading three
   `setUp` methods in three files. pytest fixtures are named, composable, scoped
   (function/module/session), and requested explicitly per test — the dependency is visible in
   the test signature. This is the biggest day-to-day quality win.

2. **`parametrize` over copy-pasted variants.** We have families of near-identical test methods
   differing only in inputs and expected outputs. unittest's `subTest` helps but reports poorly
   and doesn't isolate failures per variant well in most runners. `parametrize` gives one test
   body, a data table, and per-case pass/fail reporting.

3. **Plugin ecosystem, primarily `pytest-xdist`.** Parallelism is the concrete payoff: CI wall
   time should drop substantially with `-n auto` once tests are isolation-safe. We also get
   `pytest-cov`, `pytest-timeout`, `pytest-randomly`, and flaky-test tooling without maintaining
   custom runner code.

**Constraints not visible in the proposal:**

- No hard deadline; this can be incremental.
- pytest runs unittest-style tests natively — the migration does not require rewriting 6,000
  tests up front. Switching the runner is cheap; rewriting tests into idiomatic pytest is the
  long tail.
- Team skill spread: some developers are strong unittest users; nobody is anti-pytest, but
  training time is real.
- CI is built around the unittest runner; changing the invocation and report format touches
  shared pipeline config.

**What I'm least sure of:**

- Whether xdist parallelism actually lands without significant work — tests that share fixtures,
  databases, ports, or global state will fail under parallel execution, and I don't know how many
  of our 6,000 tests are isolation-unsafe.
- Whether a mixed suite (unittest-style and pytest-style coexisting for months or years) creates
  more confusion than the migration removes.
- The true cost of CI churn — report formats, coverage integration, and any tooling that parses
  unittest output.

I hold that the switch is right; the open question is the migration strategy, not the
destination.

## Phase 2 — Clarifying Questions

### Adversary's questions

<!-- Adversary -->

1. Has anyone run any subset of the 6,000 tests under pytest (with or without `-n auto`)? If so,
   what were the results — pass rate, collection errors, and how many tests failed under parallel
   execution? If not, what is the basis for the estimate that CI wall time "should drop
   substantially"?

2. What is the current CI wall time for the full suite, and what specific tooling consumes the
   unittest runner's output today (report parsers, coverage integration, dashboards, merge gates)?
   A list of the concrete integration points would help.

3. Is the proposal runner-switch-only, or does it include a committed plan — owner, timeline,
   enforcement mechanism (e.g., lint rule for new tests) — for rewriting existing tests into
   idiomatic pytest? Equivalently: is the mixed unittest/pytest suite intended to be a transition
   state with an end date, or a permanent condition?

### Advocate's questions

<!-- Advocate -->

1. **CI baseline and parallelism headroom.** What is the current CI wall time for the full suite, and is it dominated by a few slow modules or spread evenly? Any pilot data (even a single package run under `pytest -n auto`) showing actual speedup or the isolation-failure rate? This bounds the size of the xdist payoff you're claiming.

2. **Depth of CI coupling.** Is CI's dependency on unittest limited to the runner invocation and report format (e.g., JUnit XML consumers, coverage upload), or are there custom `TestRunner`/`TestResult` subclasses, output-parsing scripts, or dashboards that would need rework? Rough inventory helps price the "CI churn" downside precisely instead of leaving it vague.

3. **Existing pytest footprint and team baseline.** Are any teams in the monorepo already writing pytest-style tests (or using pytest as a runner locally), and roughly what share of developers have prior pytest experience? This determines whether the mixed-suite period is a new risk or already the de facto state.

### Judge's questions

<!-- Judge -->

1. **What is the defined end state?** Is success "pytest as runner, new tests written in pytest idioms, legacy unittest tests left as-is indefinitely," or does the plan require eventually rewriting the ~6,000 existing tests? The cost-benefit calculus differs by an order of magnitude between these, and the Defender's own "mixed suite confusion" worry can't be judged without knowing which one is proposed.

2. **What baseline measurements exist?** Specifically: current CI wall time, any sampling or audit of how many tests are isolation-unsafe (shared DBs, ports, global state), and how much time the team currently loses to the setUp-inheritance and copy-paste problems. If the answer is "none," say so — the debate should then be about whether to decide on qualitative grounds or measure first.

3. **What concretely consumes unittest runner output today?** An inventory of CI touchpoints — report formats parsed by dashboards, coverage integration, flaky-test tooling, anything scripting the current runner invocation — so "CI churn" can be argued as a bounded list rather than an unknown.

### Defender's answers

<!-- Defender -->

Answering all nine questions. Where the honest answer is "we haven't measured," I say so and
state my working assumption.

**Pilot data / basis for speedup claim (Adversary Q1, Advocate Q1, Judge Q2).** No pilot has been
run. Nobody has executed the suite under pytest, with or without `-n auto`. The speedup claim
rests on precedent (xdist results reported broadly elsewhere) and on the fact that our CI boxes
have 8-16 cores while the suite runs single-process per shard today. No isolation audit exists
either. Known suspects: one package's tests hit a shared local Postgres instance, and a handful
of integration tests bind fixed ports. I estimate those at under 10% of the suite, but that is an
estimate, not a measurement.

**CI baseline (Adversary Q2, Advocate Q1).** Full suite is ~30 minutes single-process. CI splits
it into 4 per-package shards; the longest shard is ~15 minutes and dominates PR feedback time.
Time is spread unevenly: two packages hold most of the slow integration tests.

**Concrete unittest integration points (Adversary Q2, Advocate Q2, Judge Q3).** Bounded list, as
requested: (1) CI invokes `python -m unittest discover` per shard; (2) coverage runs via
`coverage run -m unittest` with results uploaded to our coverage service; (3) JUnit XML for the
results dashboard is produced by `unittest-xml-reporting`; (4) a small script parses runner
stdout to annotate PRs with failure summaries. No custom `TestRunner`/`TestResult` subclasses.
pytest emits JUnit XML natively and works with `pytest-cov`, so (2)-(3) are replacements, not
rewrites; (4) needs rework.

**End state and rewrite plan (Adversary Q3, Judge Q1).** Proposal is runner-switch plus a
ratchet, not a mass rewrite. Concretely: switch CI to pytest as runner (existing unittest tests
run unchanged under it); require new tests to be idiomatic pytest, enforced by a lint rule
banning new `TestCase` subclasses; rewrite legacy tests opportunistically when touched. There is
no owner, timeline, or end date for full conversion — the mixed suite is a permanent condition
that shrinks over time. I flagged this as one of my own uncertainties.

**Existing pytest footprint (Advocate Q3).** Two newer services in the monorepo already run
pytest locally, so the mixed state already exists de facto. Rough guess: a third of developers
have real pytest experience from prior work; the rest have unittest-only muscle memory.

**Time lost to setUp/copy-paste problems (Judge Q2).** Not measured. Qualitative evidence only:
recurring review comments about inheritance confusion, and visible copy-paste families of 5-15
near-identical test methods in several packages.

## Phase 3 — Adversary's Case

<!-- Adversary: up to 5 objections, strongest first. Problem / Evidence / Better way. -->

**Objection 1 — Committing before running a nearly-free pilot.**
*Problem:* The proposal asks for a decision while its only quantitative benefit (CI speedup) is
unmeasured, even though measuring is cheap. If the pilot would change the decision or the plan,
deciding first is pure avoidable risk; if it wouldn't, it costs a day to prove that.
*Evidence:* Defender's own answers: "No pilot has been run. Nobody has executed the suite under
pytest, with or without `-n auto`." Meanwhile pytest runs unittest tests natively — so running one
shard under `pytest` (collection check) and under `pytest -n auto` (isolation check) is hours of
work, no code changes. The 10% isolation-unsafe figure is admitted to be a guess.
*Better way:* Make the pilot a gate, not an afterthought: run the full suite under plain `pytest`
(count collection errors and behavior diffs), then run the two slow packages under `-n auto` and
record the parallel failure rate and actual wall-time delta. Approve the migration conditional on
those numbers, and let them size the isolation-fix workstream.

**Objection 2 — The xdist payoff is structurally capped on the metric that matters.**
*Problem:* PR feedback time is governed by the longest shard (~15 min), and that shard is
dominated by slow integration tests hitting a shared Postgres and fixed ports — exactly the tests
that fail under parallel execution. `-n auto` will speed up the shards that don't matter and may
leave the critical path untouched. "CI wall time should drop substantially" could round to zero
where it counts.
*Evidence:* Defender's answers: suite already sharded 4 ways; "two packages hold most of the slow
integration tests"; known isolation suspects are the shared-Postgres package and fixed-port
integration tests — i.e., the slow tests and the unsafe tests are largely the same tests.
*Better way:* Treat isolation work on the two slow packages as an explicit, costed prerequisite
of the parallelism claim: DB-per-worker (template database or schema-per-worker) and
ephemeral-port fixtures, with a stated wall-time target for the longest shard (e.g., 15 min → 6
min). If that work is out of appetite, re-argue the proposal on fixture/parametrize grounds alone
and drop the CI-speed headline.

**Objection 3 — The plan's benefits don't reach the pain the proposal cites.**
*Problem:* The argument for migrating is built on existing pain — multi-level `setUp` inheritance
chains and copy-paste families of 5-15 test methods. The plan (runner switch + new-tests-only
ratchet + opportunistic rewrites) leaves all 6,000 existing tests as they are, indefinitely. The
"biggest day-to-day quality win" applies only to tests that don't exist yet; the cited pain
persists unaddressed.
*Evidence:* Defender's end-state answer: "no owner, timeline, or end date for full conversion —
the mixed suite is a permanent condition." The qualitative evidence of pain (review comments,
copy-paste families) is all about legacy code.
*Better way:* Add one targeted workstream to the plan: inventory the worst offenders (deepest
base-class chains, largest copy-paste families — greppable), and deliberately convert those
specific packages with an owner. That converts the proposal's own strongest motivation into a
realized benefit instead of a hoped-for side effect.

**Objection 4 — The lint ratchet as specified blocks legitimate work in legacy packages.**
*Problem:* Banning new `TestCase` subclasses monorepo-wide, while shared test infrastructure
lives in `TestCase` base classes, forces a developer adding a test to a legacy package to choose:
violate the rule, bolt a pytest-style test alongside a class-based family with no access to the
shared setup, or hand-port base-class machinery to fixtures under deadline pressure. That is how
ratchets get exception-listed into irrelevance.
*Evidence:* Defender's Phase 1: base classes span "three `setUp` methods in three files" — that
machinery has no fixture equivalent on day one. The ratchet is enforced from day one anyway.
*Better way:* Sequence the ratchet: first ship `conftest.py` fixture equivalents for the top
shared base classes (a bounded, identifiable set), then enable the ban per-package as coverage
lands. Monorepo-wide day-one ban only for packages with no legacy base-class dependence.

**Objection 5 — "Shrinks over time" has no owner and no metric, so it will plateau.**
*Problem:* Opportunistic-only conversion with nobody accountable predictably stalls: the easy
files get converted, the hairy base-class families (the actual pain) are avoided, and the org
carries two testing idioms forever — double documentation, onboarding cost for the two-thirds of
developers without pytest experience, and reviewer ambiguity about which idiom applies.
*Evidence:* Defender flagged mixed-suite confusion as one of his own top uncertainties, and then
presented a plan with "no owner, timeline, or end date." The risk is acknowledged and unmitigated
in the same document.
*Better way:* Don't mandate a full rewrite; mandate visibility and direction: a CI-tracked count
of `TestCase` subclasses that must be monotonically non-increasing, plus a named owner who
reviews the trend quarterly. Cheap to build, and it converts "shrinks over time" from a hope into
a checked invariant.

## Phase 4 — Advocate's Case

<!-- Advocate: steelman, then a direct answer to each objection. -->

### Part 1 — Steelman: the strongest case for the plan as written

1. **The migration is nearly free at the decision layer, and that is a designed property, not
   luck.** pytest runs unittest tests natively, so the runner switch requires zero rewrites of the
   6,000 existing tests. The proposal's shape (switch runner, ratchet new tests, convert
   opportunistically) is the only migration topology with bounded day-one cost and no big-bang
   failure mode. Every alternative that "does more up front" imports the classic mass-rewrite risk
   the plan deliberately avoids, with no deadline forcing that risk.

2. **CI churn is priced, and the price is small.** The Phase 2 inventory is a bounded list of
   four touchpoints: runner invocation (config change), coverage (`pytest-cov` is a drop-in),
   JUnit XML (pytest emits it natively, replacing `unittest-xml-reporting`), and one small
   stdout-parsing script needing rework. No custom `TestRunner`/`TestResult` subclasses exist.
   The proposal's scariest-sounding downside turned out, on inspection, to be roughly a day of
   pipeline work.

3. **The mixed suite is not a new risk the plan creates; it is the current state the plan
   governs.** Two services already run pytest. Today the monorepo has two idioms and no policy.
   The plan declares a winner, enforces it for new code, and points the gradient one direction.
   Rejecting the proposal does not avoid the mixed state; it preserves it without governance.

4. **The fixture/parametrize case stands at zero speedup.** Even if xdist delivered nothing, the
   plan stops the compounding cost: every future test avoids the inheritance chains and
   copy-paste families that generate today's review pain, and pytest is the ecosystem default
   that new hires arrive knowing. unittest-only is not a neutral status quo; it is a choice to
   keep accruing the documented pain in all new code. Notably, the Adversary's own Objection 2
   fallback ("re-argue on fixture/parametrize grounds alone") concedes this core is sound.

### Part 2 — Answers to the five objections

**On Objection 1 (decide only after a pilot).** *Dispute the problem; accept a weakened better
way.* The problem statement assumes the pilot could change the decision. It cannot, only the
plan's sizing. Name the pilot outcome that argues for staying on unittest: high collection-error
count means fixable compat shims (a well-known, enumerable class of issues); high parallel
failure rate means the xdist workstream is bigger and the headline gets softened, exactly as
Objection 2 already argues. No plausible number flips "migrate" to "don't," because the
fixture/parametrize/ecosystem case is speedup-independent (see steelman point 4, and the
Adversary's own fallback). Also note the pilot is cheap *because of* the proposal's central
design fact, native unittest support; the objection borrows the plan's virtue to argue against
approving it. I accept the substance: run the collection check and the two-package `-n auto`
probe in week one of execution, and let the numbers size the isolation workstream. I dispute
making approval conditional on it; that converts a sizing input into a veto with no
decision-relevant failure mode.

**On Objection 2 (xdist capped on the critical path).** *Concede the evidence, dispute the
problem's conclusion, accept the better way as an addition.* Conceded: the Defender's own answers
show the slow tests and the isolation-unsafe tests substantially overlap, so "CI wall time should
drop substantially" is not defensible as an unconditional headline; it should read "conditional
on isolating the two slow packages." What convinced me is the shard math: the longest shard
(~15 min) gates PR feedback, and `-n auto` on the safe shards does not touch it. But follow the
objection to its own remedy: DB-per-worker via template databases and ephemeral-port fixtures.
That remedy is a pytest fixture pattern with mature precedent (`pytest-postgresql`,
pytest-django's DB-per-worker model). Under unittest there is no comparable path without writing
and maintaining a custom parallel runner, which is precisely what the proposal exists to avoid.
The objection, argued through, is an argument *for* the migration: pytest is the prerequisite of
the fix for the critical path. I accept adding the isolation work on the two slow packages as an
explicit, costed workstream with a wall-time target for the longest shard.

**On Objection 3 (benefits don't reach the cited pain).** *Dispute the problem; accept the better
way as a cheap refinement.* The objection treats "legacy tests untouched" as "legacy pain
unaddressed," but pain is frequency-weighted. The review comments and copy-paste friction come
from tests being actively read and modified; those are exactly the tests the opportunistic rule
converts first, because conversion triggers on touch. A test nobody has opened in two years
causes no day-to-day pain, and rewriting it is cost without benefit. The parametrize win also
lands immediately on contact: the next time a 15-method copy-paste family needs a 16th case, the
author collapses it instead of pasting. So the ratchet-plus-opportunistic plan concentrates
conversion effort precisely where the cited pain lives. That said, the better way (grep out the
deepest base-class chains and largest variant families, deliberately convert those packages with
an owner) is cheap, compatible, and accelerates the same gradient; I accept it as an addition,
while disputing that its absence makes the plan's benefits illusory.

**On Objection 4 (day-one lint ratchet blocks legacy work).** *Dispute the evidence's reading;
accept per-package sequencing as sound engineering.* The forced trilemma (violate the rule, bolt
on a fixture-less pytest test, or hand-port base classes under deadline) omits the common case:
banning new `TestCase` *subclasses* does not ban new test *methods* on existing classes. A
developer extending a legacy family adds a method to the existing class, keeps full access to the
shared `setUp` machinery, and trips no lint. The ratchet bites only on new test classes, which is
where pytest style is appropriate and where no legacy machinery is being extended. The residual
case (a genuinely new test class that needs legacy base-class services) is real but narrow, and
standard ratchet hygiene covers it: a tracked suppression comment requiring review, which is not
"exception-listed into irrelevance" when the exception count is visible and trending down (see my
answer to Objection 5). I accept the sequencing idea, ship `conftest.py` equivalents for the top
base classes and enable the ban per-package, as a good implementation of the same ratchet; it
refines the plan rather than refuting it.

**On Objection 5 (no owner, no metric, so it plateaus).** *Accept the better way outright;
dispute the premise that plateau equals failure.* The mechanism proposed, a CI-tracked count of
`TestCase` subclasses that must be monotonically non-increasing plus a named owner reviewing the
trend quarterly, is cheap, enforceable, and directly answers the Defender's own flagged
uncertainty. The plan should adopt it; I concede the plan as written left "shrinks over time" as
a hope rather than an invariant, and the Adversary's fix is the right one. But the objection's
framing, that a plateau strands the org in a costly two-idiom state, overstates the downside.
The value case never depended on reaching zero unittest tests: a suite where all new code is
pytest and legacy shrinks slowly strictly beats today's suite, where all code is unittest and
the pain compounds. The two-idiom cost is already being paid (two services run pytest now), and
the training cost for the unittest-only two-thirds is a one-time, decaying cost, whereas
unittest-only friction on every future test is a growing one. Plateau is a diminished win, not
a loss.

**Summary of positions:** Objections 1 and 3: problem disputed, better ways accepted as
sequencing/refinement. Objection 2: evidence conceded (headline must be conditioned), better way
accepted, and the remedy itself requires pytest. Objection 4: evidence's reading disputed (the
method-vs-subclass distinction dissolves the common case), sequencing accepted. Objection 5:
better way accepted in full, catastrophic framing disputed. None of the five argues for a
different destination; all five are compatible with, and four improve, the plan under review.

## Phase 5 — Adversary's Rebuttal

<!-- Adversary: sustain with new substance, or drop and name what convinced you. -->

**Objection 1 — SUSTAINED, narrowed from approval gate to cutover gate.** I concede the
Advocate's central point: no pilot number flips "migrate" to "don't," because the
fixture/parametrize case is speedup-independent — and I proposed that fallback myself. The
approval-gate framing is dropped. But the Advocate's claim that the pilot is "a sizing input
with no decision-relevant failure mode" is wrong on one axis neither of us had named:
**silent correctness loss at cutover.** pytest's own documentation lists unittest features it
does not support: the `load_tests` protocol is ignored outright, and `subTest` is not properly
supported without the `pytest-subtests` plugin. Both failure modes are silent — `load_tests`
customization means tests that run today are simply not collected under pytest, and `subTest`
failures can be misreported or swallowed. The Defender's Phase 1 explicitly says the team uses
`subTest` today ("unittest's `subTest` helps but reports poorly"), so this is not hypothetical
for this suite. A suite that goes green on day one while running fewer assertions than
yesterday is a correctness regression, not a sizing question. *Narrowed better way:* keep the
Advocate's accepted week-one pilot, but make one number a hard cutover gate, not an
approval gate: collected-test parity (pytest collection count == unittest discovery count, or
every diff explained), plus `pytest-subtests` installed and verified against a known-failing
`subTest` case before CI switches. Cheap, mechanical, and it closes the only genuinely
dangerous path in an otherwise low-risk migration.

**Objection 2 — DROPPED.** What convinced me: the Advocate conceded the evidence (the headline
becomes "conditional on isolating the two slow packages"), accepted my better way in full as a
costed workstream with a wall-time target for the longest shard, and added an argument I find
decisive: the remedy itself — DB-per-worker via template databases, ephemeral-port fixtures —
is a mature pytest fixture pattern with no unittest equivalent short of a custom parallel
runner. My objection, followed to its own remedy, argues for the migration. Nothing left to
sustain.

**Objection 3 — SUSTAINED, with new substance: the Advocate's own answers to Objections 3 and
4 are mutually undermining.** The Obj 3 defense rests on "conversion triggers on touch" —
frequency-weighted pain gets converted because painful tests are the ones being modified. But
the Obj 4 defense establishes the opposite: adding a method to an existing `TestCase` family
is legal, lint-clean, and keeps full access to the shared `setUp` machinery. So the path of
least resistance when touching a hairy legacy family is precisely to extend it, not convert
it — conversion-on-touch is most expensive exactly where the pain is worst, because you cannot
convert one method of a family without porting its base-class machinery. The lint-clean escape
hatch the Advocate correctly identified (and which dissolved my Objection 4) guarantees the
frequency-weighted pain persists where conversion cost is highest. Consequence: the targeted
workstream the Advocate accepted "as a cheap refinement" is not a refinement — it is the
*only* mechanism in the plan that reaches the cited pain, and it must appear in the plan text
with an owner and a named package list (greppable: deepest base-class chains, largest variant
families), not as a debate-transcript aside. I sustain until the plan document itself is
amended to include it.

**Objection 4 — DROPPED.** What convinced me: the method-vs-subclass distinction. My trilemma
omitted the common case — a developer extending a legacy family adds a method to the existing
class, keeps the shared `setUp` machinery, trips no lint. The residual case (genuinely new
test class needing legacy base-class services) is narrow and covered by tracked suppressions
plus the per-package `conftest.py`-first sequencing the Advocate accepted. Note: dropping this
objection is what sharpens Objection 3 above — the escape hatch that makes the ratchet humane
is the same hatch that lets legacy pain persist.

**Objection 5 — DROPPED as resolved.** The Advocate accepted the mechanism outright:
CI-tracked monotonically non-increasing `TestCase` count plus a named owner reviewing
quarterly. That was the entire objection — it targeted the gap between "shrinks over time" and
any instrument that checks it. The remaining dispute (whether a plateau is a "diminished win"
or a "costly stranding") changes no outcome once the metric and owner exist, so arguing it
would be noise. Resolved on the condition that the mechanism, like Objection 3's workstream,
lands in the plan text rather than remaining a concession in this transcript.

**Net position:** two sustained (1 narrowed to a cutover gate on collection/subTest parity;
3 on the grounds that the accepted workstream is load-bearing, not optional, and must be in
the plan document), three dropped (2, 4, 5 — with 5 conditional on the accepted mechanism
being written into the plan). None of what remains disputes the destination; both sustained
objections are about what must be true before and during cutover for the plan's own claims to
hold.

## Phase 6 — Advocate's Surrebuttal

<!-- Advocate: final defense or concession per sustained objection. -->

**On Objection 1 (narrowed to a cutover gate) — CONCEDED.** What convinced me: the Adversary
produced documented, checkable failure modes, not a hypothetical. pytest's unittest-support
documentation states that the `load_tests` protocol is ignored and that `subTest` is not
properly supported without the `pytest-subtests` plugin, and the Defender's own Phase 1 confirms
this suite uses `subTest` today. Both failures are silent: a green suite that collects fewer
tests, or swallows subtest failures, is a correctness regression wearing a passing badge, and no
amount of "the fixture case is speedup-independent" answers that. My Phase 4 claim that the pilot
had "no decision-relevant failure mode" was wrong on exactly this axis; the Adversary found the
one number that must gate something, and correctly gates cutover rather than approval. I accept
the cutover gate in full, and I strengthen it: parity should be checked by diffing collected test
IDs, not by comparing counts, since counts can match while `load_tests`-customized modules drop
tests and stray files are newly collected under pytest's discovery rules. Concretely: (a) dump
unittest discovery IDs and `pytest --collect-only -q` IDs, diff, explain every delta; (b) install
`pytest-subtests` and verify it reports a deliberately failing `subTest` case before CI switches.
Note what this concession does not touch: the gate exists and is cheap precisely because pytest
runs unittest tests natively, which is the plan's central design fact. The decision to migrate
stands; the gate is execution hygiene the plan should have specified.

**On Objection 3 (workstream is load-bearing, must be in the plan text) — DEFENDED in part,
amendment CONCEDED.**

*Conceded, with an admission the Adversary did not have.* The mutual-undermining argument is
correct and I concede it: the lint-clean escape hatch I used to dissolve Objection 4 (add a
method to the existing `TestCase` family) is the path of least resistance exactly where the pain
is worst, so conversion-on-touch will not reach the hairy families on its own. I add a fact that
strengthens the Adversary's case beyond his own evidence: pytest's documentation is explicit that
`parametrize` (and non-autouse fixtures) do not work inside `TestCase` subclasses. So my Phase 4
claim that "the next time a 15-method copy-paste family needs a 16th case, the author collapses
it" was wrong as stated: the author cannot parametrize within the class at all; collapsing the
family requires converting it out of `TestCase` first, which is precisely the high-cost step the
escape hatch routes around. The parametrize benefit is therefore gated on deliberate conversion,
not contact. Given that, I concede the amendment requirement without reservation: the targeted
conversion workstream (greppable inventory of deepest base-class chains and largest variant
families, named owner, named package list) must appear in proposal.md itself. A concession that
lives only in a debate transcript is not a plan, and this one is load-bearing.

*Defended: "the only mechanism in the plan that reaches the cited pain" is too strong.* The plan
as amended in Phase 4 contains a second, mutually reinforcing mechanism: the accepted Objection 4
sequencing ships `conftest.py` fixture equivalents for the top shared base classes before the
per-package ratchet lands. That work attacks the exact premise of the Adversary's cost argument,
that "you cannot convert one method of a family without porting its base-class machinery."
Porting the machinery once, centrally, is what that workstream is; after it lands, converting any
family that depends on those base classes drops from "port the machinery under deadline" to a
mechanical rewrite against existing fixtures. The two mechanisms compose: conftest equivalents
lower the marginal cost of conversion everywhere, and the targeted workstream spends directed
effort on the worst offenders. Neither alone suffices, which is why I concede the amendment; but
the claim that the plan otherwise contains nothing that reaches the pain undercounts what was
already accepted.

**Housekeeping the dropped objections owed to the record.** The Adversary attached a condition to
dropping Objection 5 (and implicitly Objection 2): that the accepted mechanisms be written into
the plan document, not left as transcript concessions. I accept that condition globally. For the
Judge, the full amendment list the Advocate now endorses for proposal.md, none of which changes
the destination:

1. Week-one pilot: full-suite collection check under plain `pytest`; two slow packages under
   `-n auto`; numbers size the isolation workstream (from Objection 1, approval not conditional).
2. Hard cutover gate: collected-test-ID parity with every diff explained, plus `pytest-subtests`
   installed and verified against a known-failing `subTest` case (from Objection 1, conceded).
3. Isolation workstream on the two slow packages as an explicit, costed prerequisite of the
   CI-speed claim, with a wall-time target for the longest shard; headline reworded to be
   conditional on it (from Objection 2).
4. Targeted conversion workstream: greppable inventory, named owner, named package list, in the
   plan text (from Objection 3, conceded).
5. Ratchet sequencing: `conftest.py` equivalents for top shared base classes first, per-package
   enablement of the `TestCase` ban, tracked suppression comments for the narrow residual case
   (from Objection 4).
6. CI-tracked monotonically non-increasing `TestCase` count with a named owner reviewing the
   trend quarterly (from Objection 5).

**Closing position.** Across five objections and two rounds, nothing has disputed the
destination: both sustained objections concern what must be true at and after cutover for the
plan's own claims to hold, and the Adversary dropped Objection 2 partly because its remedy
requires pytest. The plan that emerges is the original plan plus six bounded amendments, four of
which the original's structure made cheap. That is what a sound decision surviving adversarial
review looks like: the core held, the execution spec got sharper, and the two points I conceded,
the cutover gate and the load-bearing status of the targeted workstream, were conceded to
evidence (documented pytest behavior; the logical interaction of my own two answers), not to
pressure. I recommend the Judge treat the migration itself as settled and direct remaining
scrutiny at the amendment list.

## Phase 7 — Judge's Interim: Assessment and Compromises

<!-- Judge: per objection — strengths/weaknesses of each side; resolved or compromise proposed. -->

A note on method before the per-objection rulings: this debate converged unusually far on its
own. Four of five objections ended with one side crediting the other's evidence by name. My job
here is therefore mostly to record who won what and why, and to close the two gaps the
convergence left open. I propose exactly two compromises (C1, C2); everything else is resolved.

**Objection 1 (pilot: approval gate → cutover gate) — RESOLVED, split verdict.**

*Adversary:* The original approval-gate framing overreached and was rightly conceded — the
Advocate's challenge ("name the pilot outcome that argues for staying on unittest") went
unanswered because no such outcome exists; the fixture/parametrize case is speedup-independent,
a fallback the Adversary had himself proposed. But the narrowed rebuttal produced the single
best piece of evidence in the debate: documented, checkable, *silent* failure modes — pytest
ignores the `load_tests` protocol and mishandles `subTest` without `pytest-subtests` — tied to
this specific suite by the Defender's own Phase 1 statement that the team uses `subTest`. That
is not a hypothetical; it is a correctness regression wearing a green badge.

*Advocate:* Won the approval-vs-sizing question cleanly, then conceded the cutover gate to
evidence rather than pressure, and improved it: diffing collected test IDs instead of comparing
counts closes the case where drops and strays cancel out. The Phase 4 claim of "no
decision-relevant failure mode" was wrong and was admitted as such.

*Ruling:* Advocate wins the first half (approval is not conditional on the pilot); Adversary
wins the second half (cutover is gated on collected-ID parity plus verified `pytest-subtests`).
Winning evidence: pytest's own unittest-support documentation plus the Defender's confirmed
`subTest` use. Amendments 1 and 2 embody the resolution; both sides have endorsed them. One
loose thread for Phase 10: nobody established whether this suite actually uses `load_tests`.
The ID-diff gate catches it either way, but the Defender should confirm so the gate's diff
review knows what to expect.

**Objection 2 (xdist capped on the critical path) — RESOLVED; residual gap becomes C1.**

*Adversary:* The shard math was correct and conceded: PR feedback is governed by the longest
shard, and the slow tests and the isolation-unsafe tests are substantially the same tests, so
`-n auto` on the safe shards does not touch the metric that matters. This permanently killed
the unconditional "CI wall time should drop substantially" headline.

*Advocate:* Produced the argument the Adversary himself called decisive — the remedy
(DB-per-worker via template databases, ephemeral-port fixtures) is a mature pytest pattern with
no unittest equivalent short of a custom parallel runner, so the objection, argued through its
own better-way, argues *for* the migration.

*Ruling:* Resolved with each side winning the half it earned: the headline is conditioned
(Adversary), and the condition strengthens rather than weakens the case for pytest (Advocate).
Amendment 3 captures it. But one gap survived both rounds: amendment 3 says the headline is
"conditional on" the isolation workstream, with no decision rule if the pilot prices that
workstream beyond appetite. The Adversary's original better-way contained such a rule ("if that
work is out of appetite, re-argue on fixture/parametrize grounds alone and drop the CI-speed
headline"); the Advocate accepted the workstream but never explicitly accepted that clause. An
indefinitely "conditional" claim is how headlines outlive their evidence.

*C1 — Post-pilot decision rule.* When amendment 3 is written into proposal.md, the Defender
states an explicit appetite (in person-weeks) for isolating the two slow packages. If the
week-one pilot prices the work above that appetite, the CI-speed claim is deleted from the
proposal — not deferred, not softened — and the migration stands on fixture/parametrize/
ecosystem grounds alone. What each side gives up: the Adversary gives up any relitigation of
the destination on bad pilot numbers (the off-ramp edits the claim, not the decision); the
Advocate gives up an evergreen conditional headline (it becomes deletable by a number). What
the artifact gains: the pilot's output maps to a defined edit instead of a renegotiation.

**Objection 3 (benefits don't reach the cited pain) — RESOLVED, split verdict; process
condition becomes C2.**

*Adversary:* The mutual-undermining argument — the lint-clean escape hatch that humanely
dissolved Objection 4 is the same hatch that routes developers around converting the hairy
families — is the sharpest reasoning in the transcript, and it was then strengthened by the
Advocate against his own position: `parametrize` does not work inside `TestCase` subclasses, so
the "collapse the family on contact" story was wrong as stated. Conversion-on-touch is most
expensive exactly where the pain is worst. The demand that the targeted workstream live in
proposal.md with an owner and package list, not in a transcript, is correct.

*Advocate:* Conceded to logic and added the fact that completed the Adversary's case — the kind
of concession that raises confidence in everything else he defended. His partial defense also
lands: "the *only* mechanism that reaches the pain" is an overclaim, because the accepted
Objection 4 sequencing (central `conftest.py` fixture equivalents for the top base classes)
attacks the exact premise of the cost argument — port the machinery once, and per-family
conversion drops to a mechanical rewrite. The two mechanisms compose; neither alone suffices.

*Ruling:* Adversary wins the substance — the targeted conversion workstream is load-bearing and
must appear in the plan text (amendment 4). Advocate wins the narrow point that it is one of
two mechanisms, not the only one (amendment 5 is the other). The Adversary's "sustained until
the plan document is amended" is not a live dispute about content — the content is agreed — it
is a process condition, which C2 operationalizes.

**Objection 4 (day-one ratchet blocks legacy work) — RESOLVED, Advocate won.**

Winning evidence: the method-vs-subclass distinction. The trilemma omitted the common case — a
developer extending a legacy family adds a method to the existing class, keeps the shared
`setUp` machinery, trips no lint. The Adversary dropped the objection and credited exactly this.
The residual case is covered by tracked suppressions plus the per-package sequencing both sides
accepted (amendment 5). Note the honest cost of this win: the same distinction is what revived
Objection 3, and the Advocate paid that price in full. Nothing left to arbitrate.

**Objection 5 (no owner, no metric → plateau) — RESOLVED, split verdict; folded into C2.**

*Adversary:* Won the substance immediately — the plan as written had no instrument connecting
"shrinks over time" to reality, the proposed mechanism (CI-tracked monotonically non-increasing
`TestCase` count, named owner, quarterly review) is cheap and enforceable, and the Advocate
adopted it outright.

*Advocate:* Won the framing — a plateau is a diminished win, not a stranding, since all-new-code-
in-pytest with slowly shrinking legacy strictly beats the status quo, and the two-idiom cost is
already being paid today. The Adversary agreed that arguing this further would change no
outcome, which is the correct call.

*Ruling:* Resolved. The drop was conditional on the mechanism landing in the plan text; that
condition is the same one attached to Objection 3, so it resolves through C2.

**C2 — Amendment protocol.** All six amendments in the Advocate's Phase 6 list are edited into
proposal.md before the Defender exercises final say. Phase 10 is where the Defender accepts,
modifies, or rejects each amendment with a stated reason; any amendment rejected or materially
weakened revives its parent objection as a *contested point* in my final report, rather than
leaving it "sustained" in limbo. What each side gives up: the Adversary gives up open-ended
sustainment as leverage — once an amendment verifiably lands in the document, the objection is
closed, full stop; the Advocate and Defender give up treating transcript concessions as
delivered — a concession that lives only here is, as the Advocate himself put it, not a plan.
What the artifact gains: proposal.md becomes the single source of truth, and this debate's
output is a diff to it, not a companion document.

**Scorecard for the remaining phases.** Five objections, all five resolved on the merits:
Objection 1 split (approval to Advocate, cutover gate to Adversary), Objection 2 split
(headline conditioned, remedy favors pytest), Objection 3 split (load-bearing workstream to
Adversary, two-mechanism point to Advocate), Objection 4 to the Advocate, Objection 5 split
(mechanism to Adversary, framing to Advocate). Two compromises on the table: C1 (post-pilot
decision rule with stated appetite) and C2 (amendments land in proposal.md before final say;
rejection revives the objection as contested). The destination — migrate to pytest — was not
successfully disputed by any objection at any point; every surviving disagreement is about
execution discipline at and after cutover. Phases 8-10 should address C1 and C2 and the
Defender's appetite numbers; the migration question itself needs no further argument.

## Phase 8 — Advocate on Compromises

<!-- Advocate: accept/reject each, one reason. -->

**C1 (post-pilot decision rule: stated appetite in person-weeks; pilot prices isolation above
appetite → CI-speed claim deleted, migration stands on fixture/parametrize/ecosystem grounds) —
ACCEPT.** This trades away nothing I defended: I already argued in Phase 4 that the value case is
speedup-independent and that no pilot number flips the decision, and C1 encodes exactly that — the
off-ramp edits the claim, never the destination, while the Adversary gives up relitigating on bad
numbers. A headline that can be deleted by a number is worth more to the proposal's credibility
than an evergreen conditional, and a plan whose strongest claims survive a defined kill-switch is
a stronger plan, not a weakened one.

**C2 (all six amendments land in proposal.md before the Defender's final say; rejection or
material weakening revives the parent objection as contested) — ACCEPT.** I bound myself to this
in Phase 6 when I accepted the Adversary's condition globally and wrote that "a concession that
lives only in a debate transcript is not a plan"; rejecting C2 now would repudiate my own closing
position. It also closes debates in my favor: once an amendment verifiably lands, the Adversary's
open-ended sustainment ends — Objections 3 and 5 go from "sustained" to closed the moment the
document is edited, which is the best available terminal state for the plan I am defending.

Neither compromise touches a strength I successfully defended: approval remains unconditional on
the pilot (won in Objection 1), the migration destination remains settled (undisputed across all
five objections), and the ratchet design survives intact (won in Objection 4). Both compromises
convert transcript agreements into document text, which is consolidation of wins, not concession
of them. 2 accepted, 0 rejected.

## Phase 9 — Adversary on Compromises

<!-- Adversary: accept/reject each, one reason. -->

**C1 (post-pilot decision rule: Defender states appetite in person-weeks; pilot prices isolation
above appetite → CI-speed claim deleted, migration stands on fixture/parametrize/ecosystem
grounds) — ACCEPT.** This is my own Objection 2 better-way clause ("if that work is out of
appetite, re-argue on fixture/parametrize grounds alone and drop the CI-speed headline") upgraded
from a suggestion into a binding rule with a number attached — the Judge closed the exact gap I
flagged and the Advocate never explicitly accepted, and what I give up (relitigating the
destination on bad pilot numbers) is nothing I hold, since I conceded in Phase 5 that no pilot
number flips "migrate" to "don't."

**C2 (all six amendments land in proposal.md before the Defender's final say; rejection or
material weakening revives the parent objection as contested) — ACCEPT.** My sustainment of
Objection 3 and my conditional drop of Objection 5 were both explicitly "until the plan document
itself is amended" — C2 converts that condition into an enforced protocol with a defined failure
path (revival as contested, on the record, rather than limbo), so trading away open-ended
sustainment costs me nothing: once the amendment verifiably lands in the document, my objection
is resolved by my own stated terms, and if it doesn't land, C2 guarantees the Judge's final
report says so instead of letting the concession evaporate.

Neither compromise weakens the two things I still hold: the cutover gate (collected-ID parity
plus verified `pytest-subtests`) is amendment 2 and lands via C2, and the load-bearing targeted
workstream is amendment 4 and lands via C2. 2 accepted, 0 rejected.

## Phase 10 — Defender's Weigh-In

<!-- Defender: feasibility and appetite per surviving compromise. -->

Both compromises survived phases 8-9 with dual acceptance. My feasibility view, plus the
appetite number C1 demands and the `load_tests` answer the Judge flagged.

**C1 (post-pilot decision rule) — ACCEPT, appetite stated.** Appetite for isolating the two
slow packages (DB-per-worker via template databases, ephemeral-port fixtures): **4
person-weeks**. If the week-one pilot prices the work above that, the CI-speed claim comes out
of the proposal entirely and the migration stands on fixture/parametrize/ecosystem grounds. I
can live with that because I believe the number will come in under: template-database setup is
well-trodden, and the fixed-port tests are a known, small set. Stating the kill-switch costs me
nothing if I'm right and saves the proposal's credibility if I'm wrong.

**C2 (amendments land in proposal.md before final say) — ACCEPT, executed.** All six amendments
are edited into proposal.md as of this phase (see the amended artifact). Per-amendment
feasibility and appetite:

1. *Week-one pilot* — trivial: 1-2 days, no code changes. Would run it regardless of C1.
2. *Cutover gate (collected-ID diff + verified `pytest-subtests`)* — mechanical, half a day.
   On the Judge's loose thread: I know of no `load_tests` usage in the monorepo, but "know of"
   is exactly what the ID diff exists to check; a grep for `load_tests` joins the pilot
   checklist so the diff review knows what to expect.
3. *Isolation workstream with wall-time target* — accepted with the 4 person-week appetite
   above; target for the longest shard: 15 min → under 7 min.
4. *Targeted conversion workstream* — accepted; this is the amendment with real ongoing cost,
   and I accept it knowingly: the debate convinced me conversion-on-touch cannot reach the
   hairy families (the parametrize-inside-TestCase fact was decisive). I will own the inventory
   and name the package list; budget one converted package per quarter to start.
5. *Ratchet sequencing (conftest equivalents first, per-package enablement)* — accepted;
   roughly 2 person-weeks for the top base classes, and it front-loads work we'd pay anyway at
   higher cost during deadline conversions.
6. *CI-tracked `TestCase` count with named owner* — accepted; the counter is an afternoon of
   scripting. I take the quarterly review myself.

Nothing in the surviving list changes the destination, and I would implement all of it. The
debate moved me on two things I originally hand-waved: the cutover gate (I had assumed "pytest
runs unittest tests" meant zero correctness risk; the `load_tests`/`subTest` silent-failure
evidence killed that assumption) and the load-bearing status of deliberate conversion (I had
sold opportunistic conversion as sufficient; it is not).

## Phase 11 — Judge's Final Report

<!-- Judge: agreed changes / contested points / compromises and their fate / recommendation / user's options. -->

# Debate Review: Migrate Python monorepo test suite from unittest to pytest

## Agreed changes

All three roles converged on the six amendments, and I have verified each landed in
proposal.md (per C2, verified rather than assumed):

1. **Week-one pilot** (amendment 1): full-suite collection check under plain `pytest`; two slow
   packages under `-n auto`. Sizes the isolation workstream; approval is explicitly not
   conditional on it. Carries the C1 decision rule with the Defender's stated appetite of 4
   person-weeks.
2. **Hard cutover gate** (amendment 2): diff unittest discovery test IDs against
   `pytest --collect-only -q` IDs with every delta explained; grep for `load_tests`; install
   `pytest-subtests` and verify it reports a deliberately failing `subTest` case before CI
   switches. This closes the debate's one genuine correctness risk — pytest silently ignores
   `load_tests` and mishandles `subTest` without the plugin, and this suite uses `subTest`.
3. **Isolation workstream** (amendment 3): DB-per-worker via template databases and
   ephemeral-port fixtures on the two slow packages, as an explicit costed prerequisite of the
   CI-speed claim. Wall-time target: longest shard 15 min → under 7 min.
4. **Targeted conversion workstream** (amendment 4): greppable inventory of deepest `TestCase`
   chains and largest copy-paste families; proposer owns it; one converted package per quarter.
   Load-bearing, not optional — `parametrize` does not work inside `TestCase` subclasses, so
   conversion-on-touch cannot reach the cited pain.
5. **Ratchet sequencing** (amendment 5): `conftest.py` fixture equivalents for top shared base
   classes (~2 person-weeks) before per-package enablement of the new-`TestCase` ban; tracked
   suppressions for the narrow residual case; adding methods to existing classes stays legal.
6. **Shrink metric** (amendment 6): CI-tracked `TestCase` subclass count, monotonically
   non-increasing, proposer reviews quarterly.

Also agreed by all parties: the destination itself. No objection disputed migrating to pytest at
any point; the Adversary dropped Objection 2 partly because its own remedy requires pytest.

## Contested points

None survive. Per C2, I checked proposal.md for any amendment rejected or materially weakened in
Phase 10: all six were accepted and edited in, the C1 appetite number was stated (4
person-weeks), and the Judge's Phase 7 loose thread (`load_tests` usage unconfirmed) was
answered — the Defender knows of none, and the grep plus ID-diff in amendment 2 verifies it
mechanically. No parent objection revives. The Adversary's two sustained objections (1 narrowed,
3) were both sustained *pending document amendment*, and the amendments landed; by the
Adversary's own stated terms in Phase 9, both are resolved.

For the record, the closest thing to a residual disagreement is framing, not substance: whether
a conversion plateau would be a "diminished win" (Advocate) or a "costly stranding" (Adversary).
Both sides agreed in Phases 5-6 that once the shrink metric and owner exist, this argument
changes no outcome. I concur; it is not actionable.

## Compromises

**C1 — Post-pilot decision rule.** Proposed Phase 7 to close the gap in "conditional on the
isolation workstream": the Defender states an appetite; if the pilot prices isolation above it,
the CI-speed claim is deleted (not deferred), and the migration stands on
fixture/parametrize/ecosystem grounds alone. Fate: Advocate ACCEPT (Phase 8 — encodes his own
speedup-independence argument), Adversary ACCEPT (Phase 9 — it is his own Objection 2 fallback
clause made binding), Defender ACCEPT with appetite stated at 4 person-weeks (Phase 10).
Adopted; now embedded in amendment 1.

**C2 — Amendment protocol.** All six amendments edited into proposal.md before the Defender's
final say; any rejection or material weakening revives the parent objection as contested in this
report. Fate: Advocate ACCEPT (Phase 8 — bound by his own Phase 6 position), Adversary ACCEPT
(Phase 9 — converts his conditional sustainment into an enforced protocol), Defender ACCEPT and
executed (Phase 10). Adopted and discharged: verification above found all six amendments in the
document, none weakened.

## Judge's recommendation

**Approve the amended proposal and proceed to the week-one pilot.**

Reasoning. The core claim (fixtures, parametrize, ecosystem) was never successfully disputed
across five objections and two rebuttal rounds, and the strongest attack (Objection 2) inverted
under scrutiny: the fix for the critical-path shard is a pytest fixture pattern with no unittest
equivalent. The two real defects the debate exposed — silent correctness loss at cutover
(`load_tests`/`subTest`) and the fiction that opportunistic conversion reaches the hairy legacy
families — are both closed by amendments the Defender accepted knowingly, in one case against
his own original position. The remaining uncertainty (whether isolation fits in 4 person-weeks)
has a defined kill-switch: if the pilot prices it out, the CI-speed claim dies and the proposal
survives on its unconditional grounds. A plan whose weakest claim is deletable by a measurement
is decision-ready.

What would change my recommendation: nothing surfaced in this debate. What could change it
later: the pilot revealing a collection-error or behavior-diff rate large enough to make the
cutover gate's "explain every delta" step a major project in itself — that would be new
information outside the debate's evidence, and worth bringing back.

## Your decision

You are choosing between:

1. **Approve as amended** (recommended): adopt proposal.md as it now stands; run the week-one
   pilot; enforce the cutover gate before CI switches; fund the isolation workstream up to 4
   person-weeks per C1; staff the targeted conversion at one package per quarter.
2. **Approve, but adjust the C1 appetite**: same plan, different kill-switch threshold. Raising
   it makes the CI-speed claim harder to kill; lowering it makes the proposal lean earlier on
   its unconditional grounds. The debate gives you no basis for a specific different number —
   the 4 person-weeks is the Defender's judgment, untested until the pilot.
3. **Approve the runner switch but strike amendments 4-6** (conversion workstream, sequencing,
   metric): this is the original pre-debate plan. Be aware the debate's record is squarely
   against it — both Advocate and Defender conceded that opportunistic conversion cannot reach
   the cited pain, so choosing this means accepting the migration's benefits accrue mostly to
   future tests.
4. **Reject the migration**: the debate produced no argument for this — no objection disputed
   the destination, and the Adversary conceded no pilot number flips "migrate" to "don't." You
   would be overriding a unanimous record, which is your right, but the transcript offers no
   support for it.
