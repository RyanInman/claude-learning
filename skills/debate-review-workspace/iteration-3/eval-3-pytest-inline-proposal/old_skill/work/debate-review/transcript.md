# Debate Review Transcript

**Artifact:** /Users/admin/claude-learning/skills/debate-review-workspace/iteration-3/eval-3-pytest-inline-proposal/old_skill/work/pytest-migration-proposal.md
**Date:** 2026-08-07

Append-only. Each phase's content lands under its own heading, transcribed verbatim by the
Defender. No role's text is ever edited after it is written.

---

## Phase 1 — Defender: Opening Statement

The proposal: migrate our Python monorepo's test suite from `unittest` to `pytest`. I hold
the proposer's context; the artifact is the proposer's inline case, written out verbatim
plus a structured restatement.

**Goal.** Reduce the ongoing cost of writing and maintaining tests. The proposer's three
reasons are all maintenance-cost arguments, not one-off wins.

**Decision 1 — fixtures over `setUp` inheritance.** The suite reportedly leans on `setUp`
and test-class inheritance for shared state. That pattern couples tests to a class
hierarchy: adding one shared resource means threading it through base classes, and reading
a test means walking the inheritance chain. Pytest fixtures are injected by name, compose
without inheritance, and scope explicitly (function/module/session). Why it matters here:
in a monorepo, many teams share test infrastructure, and inheritance-based sharing is the
mechanism that rots first.

**Decision 2 — `parametrize` over copy-pasted variants.** The proposer states the suite has
copy-pasted test variants — the same test body repeated with different inputs. Each copy is
a divergence risk: fix a bug in one copy, miss its siblings. `@pytest.mark.parametrize`
collapses N copies into one test plus a data table.

**Decision 3 — plugin ecosystem, specifically `pytest-xdist`.** Parallel execution without
writing our own runner orchestration. "For free" means no bespoke code, not zero effort —
tests must be isolation-safe to parallelize, which is true under any parallel runner.

**Key mitigating fact.** Pytest runs `unittest.TestCase` suites natively. Migration does
not require rewriting 6k tests up front: the runner can switch first, and tests convert to
pytest idioms incrementally or never. This reframes the "6k tests" downside from a rewrite
cost to a long-tail cleanup option.

**Acknowledged downsides.** (1) 6k existing tests — mitigated as above, but a mixed-idiom
suite has its own carrying cost. (2) CI churn — pipelines and reporting need rework;
unmeasured. (3) Team familiarity — some devs know `unittest` well; pytest idioms
(fixtures, plain asserts, conftest resolution) are a real learning curve.

**Least sure of:** the true size of CI churn, and whether any tests depend on
runner-specific behavior (custom `TestResult`, load ordering) that pytest's runner would
break. Neither has been measured.

## Phase 2 — Clarifying Questions

### Adversary's questions

1. What is the current runner and CI setup concretely — plain `python -m unittest`, `pytest` already invoked in some packages, or a third-party runner (nose2, `unittest2`, Bazel/pants `py_test`, `manage.py test`)? And what consumes the test output today (JUnit XML, coverage combine, flaky-test tracking, code-owner routing)?

2. What measurements exist about the suite as it runs today: total wall-clock time in CI, whether tests currently run in parallel or serially, the count of tests using `setUp`/inheritance versus plain functions, and the count of copy-pasted variants that `parametrize` would actually collapse?

3. What is the intended end state and its enforcement — permanent mixed-idiom suite (pytest runner, `TestCase` classes stay), or full conversion of all 6k tests? If full conversion, who does it, over what window, and what stops new `TestCase` tests from being written during that window?

### Advocate's questions

**Q1 — How big is the pain the migration is buying down?** Concretely: roughly how many test classes sit on shared base classes, how deep does that inheritance run at its worst, and roughly how many copy-pasted test variants exist (or how were they estimated)? If there is any signal on time spent authoring or debugging tests today, that too.

**Q2 — Has anyone actually run `pytest` against the suite as-is, even locally?** If so: how many of the 6k tests collected, passed, failed, or errored at collection, and what was the wall-clock delta versus the current runner (serial, and under `-n auto`)? If nobody has run it, is there anything blocking a spike?

**Q3 — What exactly does CI consume from the test runner today?** Naming the pieces: the invocation command, the report format the dashboard/PR checks parse (JUnit XML, something bespoke), coverage tooling, test sharding or selection logic, flaky-test retry or quarantine machinery, and any custom `TestResult` / loader / runner subclasses in the repo. Also: what does the current suite's wall-clock time and flake rate look like, and is anything already blocked on either?

## Phase 3 — Defender's Answers

The proposal exists only as the proposer's inline case; no audit of the repo or CI has been
done. I answer from that case and mark everything unmeasured as unknown, because the Judge's
rulings inherit every answer as evidence.

**Adversary Q1 (current runner and output consumers):** Unknown. The proposal says "switch
from unittest to pytest", which implies the stock `unittest` runner rather than nose2 or a
build-system wrapper, but the exact invocation and whatever consumes its output (JUnit XML,
coverage, flaky-test tracking) are unstated and unaudited. "CI churn" was raised internally
as a downside, which implies CI has real integration with the current runner, but nobody has
inventoried it.

**Adversary Q2 (measurements):** None exist. Wall-clock time: unknown. Parallel today:
unknown; the proposer's interest in xdist parallelism suggests the suite runs serially or
close to it, but that is inference, not measurement. Counts of `setUp`/inheritance tests and
copy-pasted variants: unknown. The proposer asserts both patterns exist and hurt ("fixtures
beat setUp inheritance", "parametrize kills our copy-pasted test variants") from direct
experience of the codebase, but nobody has counted.

**Adversary Q3 (end state and enforcement):** Unspecified. The proposal argues for
switching runners and idioms but contains no conversion plan, owner, window, or lint
enforcement against new `TestCase` tests. Whether the end state is a permanent mixed suite
or full conversion is a decision the proposer has not yet made.

**Advocate Q1 (size of the pain):** Unknown in numbers. The evidence is the proposer's
working experience: shared-state management via `setUp` inheritance and copy-pasted
variants are pain points felt strongly enough to propose a migration. Depth of inheritance,
counts, and time-spent data: unknown.

**Advocate Q2 (has anyone run pytest against the suite):** Unknown — no spike is mentioned
in the proposal, and no collection or timing numbers exist. Nothing known blocks running
one; pytest collects `unittest.TestCase` suites natively, so a spike is cheap in principle.

**Advocate Q3 (what CI consumes):** Unknown in every particular — invocation, report
format, coverage tooling, sharding, retry machinery, and custom `TestResult`/loader
subclasses are all unaudited. The internally-raised "CI churn" downside is the only signal
that these integrations exist and are nontrivial. Current wall-clock time and flake rate:
unknown. Nothing is known to be blocked on either today.

## Phase 4 — Cases

### Adversary's case

Five objections, strongest first. My read of the artifact is that the *direction* is probably right and the *case as written* cannot support a decision yet — and that two of the three headline benefits are load-bearing in a way the mitigation quietly cancels.

---

#### 1. The mitigation that defuses the biggest downside also cancels the two biggest upsides

**Problem.** The Defender's "key mitigating fact" is that pytest runs `unittest.TestCase` natively, so the runner can switch first and the 6k tests convert "incrementally or never." That is true for *execution* and false for *benefits*. Pytest documents that fixtures (other than autouse) and `@pytest.mark.parametrize` do not work on `unittest.TestCase` subclasses, and states this is a design difference unlikely to ever change. So on the day after the runner switch, benefit 1 (fixtures over `setUp` inheritance) and benefit 2 (parametrize over copy-paste) apply to exactly **zero** of the 6,000 existing tests. They apply only to tests that have already been rewritten. The proposal's cost model ("no rewrite needed") and its benefit model ("fixtures and parametrize fix our pain") describe two different worlds, and the recommendation currently banks both.

**Evidence.** Pytest's own `unittest.TestCase` support docs carry an explicit warning listing non-autouse fixtures, parametrization, and custom hooks as non-functional for `TestCase` subclasses. Also note where the pain lives: the `setUp` base classes and the copy-pasted variants *are* the existing 6k — that is by definition the population the "convert later or never" escape hatch excludes.

**Better way.** Split into two decisions and price them separately. **Decision A (runner switch):** buys xdist access, better assertion output, plugin ecosystem; costs CI rework; leaves test-authoring pain untouched. **Decision B (idiom conversion):** buys fixtures and parametrize; costs N engineer-weeks; pays off only if actually executed. Approve A on A's merits. Require B to carry a scoped budget and a first-slice target (the highest-churn package) or strike fixtures/parametrize from the justification entirely. And set the bar honestly: if copy-pasted variants are the acute pain, `parameterized`'s `@parameterized.expand` and stdlib `subTest` both work on `TestCase` *today*, in days not months, with no migration. That is the alternative the migration has to beat, and the artifact never prices it.

---

#### 2. Every input to the decision is unmeasured, and the spike that would produce most of them is one day of work

**Problem.** Six clarifying questions, six answers of "unknown." No wall-clock baseline, no serial-vs-parallel fact, no count of inheritance-based test classes, no count of copy-pasted variants, no collection-error count, no CI inventory. Both sides of the ledger are assertion. A recommendation issued now is a recommendation about a suite nobody has looked at.

**Evidence.** Phase 3 in full. Worse, the unmeasurement is *asymmetric*: the benefits rest on the proposer's lived experience of the codebase (real evidence, just uncounted), while the costs rest on nothing at all. The Defender's own "least sure of" names the two largest cost drivers — CI churn size and runner-specific dependencies like custom `TestResult` or load ordering — as unmeasured. An asymmetrically-evidenced ledger systematically reads as favorable.

**Better way.** Gate the decision on a one-day spike, with the numbers named *before* it runs: (a) `pytest --collect-only -q` — collected count vs. the expected 6k, plus every collection error, which is the cheapest possible detector for `load_tests` protocol use, custom loaders, and import-time ordering assumptions; (b) full serial run — wall-clock and pass/fail delta against today; (c) `pytest -n auto` — wall-clock and the list of tests that fail *only* under distribution; (d) two greps — `TestCase` subclasses with a non-trivial base class, and near-duplicate test bodies. Then write the decision rule in advance, e.g. "if collection errors exceed X, or the parallel-only failure list exceeds Y, this is a project with a headcount, not a config change." One day of measurement converts nearly every "unknown" in this transcript into a number.

---

#### 3. Test identifiers change shape, silently invalidating flake history, quarantine lists, and ownership routing

**Problem.** unittest names a test as a dotted path (`pkg.module.TestClass.test_method`); pytest names it as a nodeid (`pkg/module.py::TestClass::test_method`) and emits a different JUnit XML shape. Everything keyed on the old identifier — flaky-test databases, quarantine and skip lists, retry rules, per-test code-owner routing, historical dashboards and trend lines — will not raise an error. It will simply stop matching and treat every test as new. Quarantined flakes silently return to blocking, the flake dashboard resets to zero and reads as an improvement, and ownership routing sends failures to nobody.

**Evidence.** The identifier formats genuinely differ, and this failure class is silent *by construction*: a lookup miss is not an exception. "CI churn" was raised internally, which is the only signal this machinery exists at all; the Defender confirms none of it has been inventoried. A silent, unbudgeted, high-probability breakage is exactly the kind that ships.

**Better way.** Make the CI inventory a hard prerequisite deliverable rather than a follow-up: the invocation command, every report consumer and the exact fields it keys on, the coverage collection method, sharding/selection logic, the retry/quarantine store, and any custom `TestResult`/loader/runner subclass in the repo. For each consumer, choose up front between migrate-the-key, dual-write during a transition window, or accept-the-reset. If the answer is accept-the-reset, say it out loud — "we lose two years of flake history" is a real cost someone should agree to in advance rather than discover in a postmortem.

---

#### 4. No end state, no owner, no window, no enforcement — so the modal outcome is a permanent two-idiom suite

**Problem.** The Defender confirms the end state is unspecified. Without a written end state and a ratchet, the easy half lands (runner switch, one PR) and the hard half does not (conversion: unglamorous, unowned, always deprioritized). Meanwhile new tests get written in whichever idiom the author already knows, so the mixed suite *grows*. A permanent mixed suite does not retire the "some devs know unittest" downside — it doubles it, because now every engineer must read both idioms and know which pytest features silently do nothing inside a `TestCase`. And it delivers benefits 1 and 2 only across the converted fraction.

**Evidence.** Phase 3, Adversary Q3: "no conversion plan, owner, window, or lint enforcement… a decision the proposer has not yet made." The Defender's opening concedes "a mixed-idiom suite has its own carrying cost" and then never prices it — that unpriced cost is the most likely thing the team actually buys.

**Better way.** Force the choice inside the recommendation and attach a mechanism to each branch. If the end state is *permanent mixed*, state it plainly and drop fixtures and parametrize from the justification — the honest pitch becomes "better runner, better output, parallelism." If the end state is *full conversion*, then from day one: a lint rule (ruff/flake8 custom check, or a CI grep) rejecting new `unittest.TestCase` subclasses; conversion assigned per-package to the owning team with dates; a codemod pass (`unittest2pytest` or equivalent) doing the assertion rewriting mechanically so the work is review, not typing; and a burn-down count published by the same CI job every run. No ratchet, no conversion — the count going up instead of down is the signal, and without publishing it nobody sees the drift for a year.

---

#### 5. "xdist for free" is the claim most likely to be false, and it turns on a property nobody has tested

**Problem.** xdist is free to *install* and potentially expensive to *use*. It pays off only if the suite is isolation-safe. A 6k-test unittest suite leaning on `setUpClass` and shared base classes is precisely the population where shared module state, shared database or temp-directory fixtures, global singletons, and implicit ordering dependencies accumulate. Under xdist's default `--dist load`, tests scatter across workers arbitrarily, so every one of those dependencies surfaces at once as a burst of new flakes that will be read as "the migration broke the suite." Separately, the speedup can be eaten whole by per-worker fixed costs — DB setup, container spin-up, and import time multiplied by N workers — which is a live risk in a monorepo with a heavy import graph, and is unmeasured.

**Evidence.** The Defender's answers: parallel-today is unknown, isolation-safety is never raised at all. The existence of xdist's `--dist loadscope` and `--dist loadfile` modes is itself the ecosystem's admission that arbitrary distribution breaks real suites. And the Defender's own hedge — "'for free' means no bespoke code, not zero effort" — concedes the point while the proposal still lists it as a benefit.

**Better way.** Measure isolation-safety now, independently of the migration and cheaply: run the existing suite under randomized order (`pytest-randomly`, or a shuffled unittest ordering) and record the failure list; then run `-n auto` and record the delta. Report parallelism as a *measured* wall-clock number with an isolation-repair cost attached, never as "free," and specify which `--dist` mode the number was obtained under. There is an ordering consequence worth stating in the recommendation: if the suite is not isolation-safe, that is a pre-existing defect the migration merely exposes. Fixing it may be the higher-value project on its own, and it does not require pytest.

### Advocate's case

The proposal is a **direction decision made at the right altitude, with an unusually cheap and reversible adoption path**. Its three arguments are structural claims about how test code is maintained, not empirical claims that need a benchmark to be true, and the one fact the Defender put at the centre — pytest runs `unittest.TestCase` natively — converts the entire downside list from "costs" into "options". Below is the affirmative case, including reasons the Defender did not articulate.

---

**1. The adoption is additive, not a migration, and that changes the whole risk profile.**

Pytest collects and runs `unittest.TestCase` subclasses as-is. `setUp`, `tearDown`, `setUpClass`, and the ~40 `assertX` methods keep working, because they are `TestCase` methods, not runner features. So the decision on the table is *"which runner invokes the suite"*, and that is a one-line change to a CI command.

The second-order consequence is what matters: **this is not a migration with a rollback plan, it is a config flip whose rollback is `git revert` on a CI file.** No production code is touched. No test is rewritten to switch. The failure is observed in CI, which is the most observable surface in the system, and the blast radius is bounded by the pipeline. Compare that to any refactor whose failure mode is discovered in production. Decisions with this shape — cheap to try, cheap to undo, failure visible immediately — deserve a much lower evidentiary bar than the debate has been implicitly applying to this one.

**2. The three "for" arguments are structural, and structural claims do not need counts to hold.**

The counts are unknown (Defender, Phase 3), and that is a real gap for *sizing*. It is not a gap for *validity*.

- *Copy-pasted variants:* the defect mechanism is "fix a bug in one copy, miss its siblings." That mechanism is real at N=200 as much as at N=2000; only the magnitude of the win scales with N, never its sign. There is no count at which collapsing duplicated bodies into a data table becomes the wrong move.
- *`setUp` inheritance:* the cost is that shared state is threaded through a class hierarchy, so reading one test means walking its ancestors and adding one resource means editing a base class that other teams depend on. Injection by name removes the hierarchy from the dependency path. Again: directionally true regardless of depth.
- *Parallelism:* `unittest` ships no parallel execution at all. This is not "pytest is somewhat better here" — it is that **there is no incremental path to parallelism from inside `unittest`.** Staying put means either staying serial or hand-rolling file-level sharding in CI. That is a genuine capability discontinuity, and it is the one argument of the three that cannot be replicated by disciplined refactoring of the existing suite.

**3. The monorepo context is doing more work than the Defender claimed — `conftest.py` versus base classes is an import-graph argument.**

The Defender said inheritance-based sharing "rots first" in a monorepo. The sharper version: **a shared test base class is an importable module, so every package that inherits from it acquires a real import edge to wherever it lives.** In a monorepo that means cross-package coupling in test code, a shared file that no single team owns, and a change to it that can break packages its author never opened.

`conftest.py` resolution is directory-scoped and implicit. Fixtures are found by walking up the tree, so a package's test infrastructure lives in the package's own directory, under that package's code owners, with no import statement anywhere. **This maps pytest's sharing mechanism onto the monorepo's existing ownership boundaries for free.** That is a monorepo-specific argument that does not appear in the generic pytest-vs-unittest comparison, and it is the strongest form of the proposer's first point.

**4. "Some devs know unittest well" is the weakest of the three downsides, because under this proposal those devs lose nothing.**

The compat layer means a developer who knows `unittest` continues writing `TestCase` classes that continue to pass. There is no retraining event, no cutover date by which everyone must know fixtures, no frozen period. **The learning curve is paid per-developer, per-test, at the moment someone chooses to use a pytest idiom — the most granular and most deferrable form a training cost can take.**

Two further points cut against this downside. First, pytest's core surface is *smaller* than `unittest`'s: plain `assert` with assertion rewriting replaces the `assertEqual`/`assertIn`/`assertRaises`/`assertAlmostEqual` catalogue that must currently be memorised, and it produces better failure output because the rewriter introspects the expression. Second, the direction of the talent flow is one-way. Pytest is the de facto standard in Python; new hires arrive knowing it, third-party testing docs assume it, and the plugin ecosystem (`pytest-cov`, `pytest-xdist`, `pytest-django`, `pytest-asyncio`, `pytest-timeout`, `pytest-randomly`, Hypothesis integration) is where all current investment is going. `unittest`'s ecosystem is effectively frozen. **"Some devs know unittest well" is a depreciating asset, and the number of people to whom it applies goes down every quarter without anyone doing anything.**

**5. Not deciding is itself a decision, and its cost compounds.**

The suite is 6,000 tests *today*. Every test written between now and whenever this is revisited is written in the idiom the proposer is arguing against, on top of the base classes he wants to dissolve. **The tail of this migration only ever grows, and the option's price rises monotonically with delay.** Meanwhile the parallelism ceiling stays where it is, so any future CI wall-clock problem arrives with no lever available except sharding built by hand.

This also reframes the "6k tests" downside correctly. Six thousand tests is an argument for *starting sooner*, not for not starting — a large suite is exactly the condition under which per-test maintenance cost dominates and under which the compat layer's value is highest.

**6. The likeliest CI integrations are already covered out of the box.**

CI churn is unmeasured, and I will not pretend otherwise. But the specific integrations named in the clarifying questions have known answers ahead of any audit:

- **JUnit XML** — pytest emits it natively via `--junitxml`. This is what dashboards, PR checks, and flaky-test trackers overwhelmingly parse.
- **Coverage** — `unittest` users already run `coverage.py`; `pytest-cov` is a wrapper over the same library, and `coverage run -m pytest` works unchanged.
- **Selection and sharding** — pytest node IDs are stable strings, and `parametrize` gives each case a distinct ID, which is *strictly better* than `subTest` for anything that selects, shards, retries, or quarantines individual cases. `subTest` failures do not surface as separate test IDs in most reporting tooling.

So the plausible worst case for CI is not "rebuild the pipeline"; it is "swap an invocation line and fix whatever bespoke reporting sits downstream." That residual is real and unaudited. But **the base case is close to free, and the residual is enumerable rather than open-ended.**

**7. The unknowns are cheap to close, and the proposal's own design is what makes them cheap.**

Every answer in Phase 3 was "unknown." I want to name what that is and is not.

It is not fabrication. The Defender declined to invent numbers under direct pressure to produce them, three times. Given that everything in this transcript becomes evidence for the Judge, a document that says "unmeasured" where it is unmeasured is worth more than one with plausible-looking estimates.

And the unknowns are *unusually* cheap to close, precisely because of point 1. **A spike is: check out the repo, `pip install pytest`, run it, read the collection summary.** An afternoon returns the collection count, the error count, the failure count, and — with `-n auto` — both the serial and parallel wall-clock deltas. That single number set answers Adversary Q2 and most of Q3 at once. The risk surface it probes is also finite and already known: `load_tests` protocol is not honoured, `subTest` needs `pytest-subtests`, custom `TestResult`/loader subclasses are bypassed, and pytest funcargs cannot be injected into `TestCase` methods. **That is a closed list of four things, each detected at collection time, each with a known workaround or a known "keep those packages on unittest" fallback.**

Note also that the demand for measurement is symmetric. "CI churn" is asserted with exactly as much evidence as "parametrize kills our copy-pasted variants" — both are internal claims from people who work in the repo, neither is counted. A standard that discounts the upside for being unmeasured must discount the downside on the same grounds, and when you do, the compat layer breaks the tie.

**8. The artifact's scope is correct for the decision being made.**

The proposal contains no owner, window, or lint rule against new `TestCase` tests. That is not an omission; it is sequencing. **You do not staff, schedule, or write enforcement for a migration you have not yet decided to do.** The proposer asked for both sides and a recommendation, holds final say, and needs a direction. Requiring the implementation plan as a precondition for endorsing the direction inverts the order of the two decisions and makes the cheap decision hostage to the expensive one.

And the end-state question has a defensible default that the proposal does not need to resolve today: **pytest runner, mixed idioms, new tests written pytest-style, old `TestCase` tests converted only when someone is already editing them.** That is opportunistic conversion, it needs no window and no owner, and it is available precisely because the compat layer never forces a deadline.

---

#### What I am not claiming

- Not that CI churn is zero. It is unaudited, and points 6 and 7 argue it is bounded and enumerable, not absent.
- Not that a permanent mixed-idiom suite is free. Two idioms means two things to read, and that carrying cost is real — it is the price of never having a big-bang cutover, and I think it is the right trade, but it is a price.
- Not that the sizing questions are illegitimate. They are good questions. My claim is that they gate *how much to invest in conversion*, not *whether to switch runners*, and that they are an afternoon's work to answer.

#### The core of it

Strip everything else away and the case is this: **the runner switch and the idiom migration are separable, and the proposal's critics are pricing them as one thing.** Separated, the runner switch is a one-line, natively-supported, immediately-reversible change that unlocks a capability (`xdist`) with no equivalent inside `unittest`, and the idiom migration becomes an ongoing option that can be exercised at any rate from zero to full, including never. The unknowns in this transcript all attach to the second half. None of them block the first.

## Phase 5 — Rebuttals

### Adversary's rebuttal

The steelman is the strongest version of this case, and it moved me on three things. It also rests, in four places, on claims that are stated more absolutely than the facts support. Point-by-point first, then my objection ledger.

---

#### Against the steelman, point by point

**P1 — "Additive, not a migration; rollback is `git revert` on a CI file."**

Largely true, with two bounded corrections.

*Reversibility has a half-life.* It is one line to revert on day 1. It is not one line on day 30, because under the Advocate's own default (P8: "new tests written pytest-style") every test authored in the interim uses plain asserts, conftest fixtures, and parametrize — none of which run under the `unittest` loader. Reverting then means rewriting the new tests. The option is cheap and it is also *decaying*, which is an argument for deciding the end state early, not for deferring it.

*"Failure is observed in CI, the most observable surface"* is true for loud failures and precisely false for the failure class in my objection 3. A quarantine list that stops matching, a flake DB that treats every test as new, a coverage threshold that shifts because a `load_tests`-generated suite is no longer collected — none of these raise. A lookup miss is not an exception. P1's risk argument holds for collection errors and does not reach silent identity breakage, which is the risk I actually raised.

**P2 — "Structural claims don't need counts; only magnitude scales, never sign."**

The sign of the *benefit* doesn't flip with N. The sign of *benefit minus cost* absolutely does, because conversion cost scales with N on the same axis. And under P8's opportunistic-conversion default, realized benefit is (per-test win) × (fraction converted), where the second term is unmeasured and structurally near zero for years.

More concretely: "there is no count at which collapsing duplicated bodies into a data table becomes the wrong move" is true and not the question. The question is whether `@pytest.mark.parametrize` beats `@parameterized.expand`, which does the same collapse *on `TestCase`, today, with no migration*. P6 answers a different alternative — it disparages `subTest`'s reporting, which is a fair hit on `subTest`, and says nothing about `parameterized.expand`, which generates distinct test methods with distinct IDs and therefore has the exact property P6 claims pytest is "strictly better" at. The cheapest substitute for headline benefit #2 is still unpriced.

**P3 — "`conftest.py` maps sharing onto ownership boundaries for free."**

This is the most interesting argument in the steelman and I think it inverts under monorepo conditions. It trades an explicit import edge — greppable, IDE-navigable, breaks loudly when it breaks — for implicit directory-scoped resolution. In a monorepo you will end up with a root `conftest.py` (shared DB, session, plugin registration), and from that moment every package inherits fixtures it never referenced, name collisions resolve nearest-wins with no error, and "where does this fixture come from" has no static answer. That is *more* invisible cross-package coupling than a base class, not less.

Also: nothing in `unittest` forces the shared base class to live outside the owning package. Base classes rotting into a cross-team shared file is a code-organization failure that pytest does not prevent and `unittest` does not cause. P3 attributes an org problem to a framework.

**P4 — "unittest-fluent devs lose nothing."**

I concede the ecosystem half outright: pytest is the de facto standard, `unittest` fluency is a depreciating asset, and the hiring flow argument is correct and durable. That is the best argument in the steelman and I have no counter to it.

The "lose nothing" half is too strong, and the cost is not retraining — it is that **shared test infrastructure cannot cross the idiom boundary.** A pytest fixture cannot be consumed by a `TestCase` method. During a mixed period of unknown length, any new shared harness must be written twice, or written once in the awkward autouse-plus-`request.cls` style that gives up the injection benefit the migration was justified by. That is a concrete, recurring maintainability cost of the mixed state, and it is unpriced in both P4 and P8. (I withdraw a weaker version of this claim below.)

**P5 — "Not deciding is a decision; the option price rises monotonically."**

P5 and P8 contradict each other. The urgency argument — "the tail only grows" — is only a cost if the tail is meant to be burned down. P8's recommended end state is that the tail is burned down opportunistically or never. Under P8, tests written between now and a later decision would have been left as `TestCase` anyway, so delay costs nothing on that axis. And the runner flip itself is one line whether the suite is 6k tests or 9k. P5 borrows the urgency of a full-conversion end state to argue for a proposal that P8 says needs no conversion. One of the two has to go.

**P6 — "The likeliest CI integrations are covered out of the box."**

The format facts are right and I concede them: `--junitxml` exists, `pytest-cov` wraps `coverage.py`, `coverage run -m pytest` works. But "the format parses" is not "the keys match," and P6 is offered as an answer to objection 3, where only key-matching counts. pytest derives the JUnit `classname` from the collected file path relative to rootdir; a test under a directory that is not an importable package path gets a *near-miss* identity rather than an obvious break — worse than a clean break, because near-misses defeat eyeballing. `junit_family` (xunit1 vs xunit2) is a second schema-shifting knob.

One correction to the strongest sub-claim: parametrized node IDs are **not** uniformly stable. For non-primitive arguments pytest synthesizes `param0`, `param1`, …, which renumber when a case is inserted or reordered. A quarantine or retry rule keyed on such an ID breaks silently on an unrelated edit. "Strictly better than `subTest`" is right; "stable strings" is not, and objection 3's remedy is what makes it safe.

**P7 — "A closed list of four things, each detected at collection time."**

This is the weakest empirical claim in the steelman, and it matters because P1's whole risk case leans on it. Of the four named, at least two are not detected at collection time and produce no error:

- **`load_tests` protocol** — not honored. The tests it would have generated are simply not collected. The signal is a *count difference*, visible only if you already know the expected count.
- **Custom `TestResult` / loader / runner subclasses** — bypassed. Whatever they did (retry, timing, failure classification, per-test cleanup, ownership tagging) silently stops happening. Green suite, fewer guarantees.
- **`subTest`** — the existence of `pytest-subtests` is itself the admission that stock behavior under-reports subtest results. Under-reporting is a silent reduction in failures.

Only the fourth (fixture injection into `TestCase`) is loud. So the risk surface P7 describes as "closed and collection-time-detected" is in fact "closed and mostly silent," and silent under-collection means **tests stop running and CI stays green** — the one failure mode that P1's observability argument cannot catch.

**On the symmetry argument** ("discount the downside on the same grounds"): the asymmetry is justified, and not by bias. Benefits here are optional and deferrable — if parametrize is worth less than hoped, you don't convert, and you lose nothing. Costs are mandatory and front-loaded — if CI churn is bigger than hoped, you pay it anyway, because the pipeline has to work the morning after the flip. Asymmetric optionality warrants asymmetric evidentiary treatment. Symmetry of *measurement status* does not imply symmetry of *decision weight*.

**P8 — "Scope is correct; you don't staff a migration you haven't decided to do."**

Agreed, and this is why I am narrowing objection 4 below. But my ask after the two-decision split is not staffing. It is that the recommendation not approve Decision A while quoting Decision B's benefits as the reason. P8 argues against a precondition I am no longer asking for.

One gap remains inside P8's own default. "New tests written pytest-style" is stated as a behavior with no mechanism. Without a CI grep rejecting new `unittest.TestCase` subclasses, that sentence is aspiration; with one, it is true. It costs one line in a lint job and no headcount, and it is the only part of the conversion story that P8's sequencing argument does not cover.

---

#### Objection ledger

**1. The mitigation cancels the two headline upsides — SUSTAINED, unchanged.** P8 and "what I am not claiming" #2 concede the fact; the disagreement is only over whether it belongs in the recommendation. The two-decision split resolves it at zero cost. Unanswered: `@parameterized.expand` remains the un-priced alternative for benefit #2.

**2. Everything is unmeasured — SUSTAINED BUT NARROWED.** P1's reversibility argument convinced me that a full measurement program should not gate the runner decision; a cheap reversible flip does not deserve a heavyweight evidentiary bar, and I withdraw "gate the decision on a day of measurement." I replace it with one artifact, because P7's silent-failure list is what a spike must catch:

> Produce a **set diff of normalized test IDs between the two runners** — enumerate them from the incumbent runner, enumerate `pytest --collect-only -q`, normalize both to `module.Class.method`, and diff the sets. Not the totals; the sets. This is minutes of work, and it is the only artifact that detects `load_tests` shortfalls, dynamically generated suites, and collection-order assumptions *before* the suite silently gets smaller. Ship the runner flip when that diff is empty or explained.

Wall-clock, isolation-safety, and inheritance counts drop to informational.

**3. Identifier shape change silently invalidates flake history, quarantine, ownership routing — SUSTAINED AND STRENGTHENED.** P6 was the refutation attempt and it addresses format support, not key identity; the `classname` derivation and the `param0` renumbering above are new failure paths in the same class. Ask unchanged and still cheap: inventory each consumer, and for each pick migrate-the-key / dual-write / accept-the-reset in advance. "We lose two years of flake history" is a legitimate choice; discovering it in a postmortem is not.

**4. No end state, no enforcement — SUSTAINED, SUBSTANTIALLY NARROWED, with one sub-claim dropped.** I drop the demand for owner, window, and per-package dates as a precondition; P8's sequencing argument is correct that those follow the direction decision. I also **withdraw the claim that a permanent mixed suite "doubles" the familiarity downside** — P4 convinced me it does not: unittest-fluent devs are not forced to learn anything, most cross-idiom misuse fails loudly, and incoming pytest fluency is free. What survives is narrower and verifiable: shared test infrastructure cannot cross the idiom boundary, so a long mixed period means writing harnesses twice. Reduced ask: **name the end state in the recommendation, align the stated benefits to it, and add the one-line CI grep against new `TestCase` subclasses.** No headcount required.

**5. "xdist for free" — SUSTAINED, REFRAMED.** I concede P2's capability point: there is no in-process parallel runner in stdlib `unittest`, and that is a real discontinuity. But "no incremental path to parallelism" overclaims — file-level sharding across CI jobs is a standard matrix pattern, available today with zero migration risk, and it has *better* isolation properties than `--dist load` because each shard is a separate process on a separate machine. That is the honest comparison baseline for wall-clock, and P2 waves it away in a subordinate clause.

Two things the steelman never addresses at all: **isolation-safety is not mentioned anywhere in it**, and Phase 3 states nothing is currently blocked on wall-clock or flake rate. So the one benefit that survives the runner/idiom split intact is buying down a pain that has not been shown to exist, at a cost (isolation repair) that has not been measured. Ask unchanged: run the existing suite under randomized order first, report parallelism as a measured number with the `--dist` mode named and an isolation-repair estimate attached, and note that if the suite is not isolation-safe, that is a pre-existing defect the migration merely exposes — and fixing it may be the higher-value project, with no pytest required.

---

#### Where this actually lands

After the concessions, the gap between the two cases is small and the Judge should see it plainly. I now agree the runner flip is cheap, reversible, and probably right, and that the sizing questions gate conversion rather than direction. What I still hold is that shipping it needs three artifacts that cost hours, not headcount: **the test-ID set diff** (objection 2, because silent under-collection defeats the observability the whole optimistic case rests on), **the CI consumer inventory with an explicit choice per consumer** (objection 3, because silent key misses are the one failure CI cannot show you), and **a named end state with the benefits list trimmed to match it** (objections 1 and 4, because approving fixtures-and-parametrize while buying a runner is approving something that will not be delivered).

### Advocate's rebuttal

Five objections. I concede two outright, concede a material part of a third, and dispute two. I also name three points of my own steelman that do not survive.

---

#### On objection 1 — "the mitigation cancels the upsides"

**Conceded in part, and it is the sharpest thing said in this transcript.** The factual claim is correct and I did not have it: pytest's `unittest.TestCase` support carries an explicit warning that non-autouse fixtures, `@pytest.mark.parametrize`, and custom hooks do not work on `TestCase` subclasses, and that this is a design difference, not a gap awaiting a fix. Parametrize on an unconverted test is unavailable, full stop. Any recommendation that lists "parametrize kills our copy-pasted variants" as a benefit of *switching runners* is mispriced, and the proposal as written does exactly that.

**But "zero of the 6,000" overstates the evidence, and the exception is the load-bearing one.** Autouse fixtures *do* work on `TestCase` subclasses — the documented pattern injects a conftest-defined resource onto the instance via `request.instance`. That is precisely the mechanism my point 3 was about: shared test infrastructure moving out of an importable base class and into a directory-scoped `conftest.py` under the owning team's code owners. A `TestCase` test can consume that without being rewritten. So benefit 1 is *degraded* for unconverted tests, not absent; benefit 2 is absent. The objection collapses two different findings into one number.

**And the "better way" is my position, not a correction to it.** Decision A / Decision B priced separately is what point 8 and "the core of it" argued for — "the runner switch and the idiom migration are separable, and the proposal's critics are pricing them as one thing." I accept the objection's version because it is more explicit than mine, and I accept the honesty requirement: the recommendation must state that on day one, parametrize applies to new and rewritten tests only.

**Where I dispute the alternative.** `subTest` as the thing the migration must beat does not survive contact with the objector's own objection 3. Objection 3's whole force is that per-test identifiers are load-bearing for quarantine, retry, sharding, and ownership routing. `subTest`'s defining weakness is that its sub-cases do not surface as distinct test identifiers in most reporting tooling — one failing sub-case reports as one failing method. You cannot argue that identifier integrity is the highest-stakes silent failure in the migration and then recommend the mechanism that produces no identifiers. `parameterized` avoids that problem and is a fair cheap alternative, but it buys one of the three benefits, adds a third-party dependency, and leaves the parallelism ceiling exactly where it is. Priced honestly it is a *complement* to the runner switch, not a substitute for it.

---

#### On objection 2 — "every input unmeasured; the spike is one day"

**Conceded, and I adopt the stronger version.** My point 7 said the unknowns were cheap to close in an afternoon. The objection adds something I did not have: write the decision rule *before* the spike runs. That is a real improvement, because a spike whose pass/fail bar is set after the numbers arrive is not a measurement, it is a rationalization with a command line attached. Pre-registering "if collection errors exceed X, or the parallel-only failure list exceeds Y, this is a project with headcount" removes the degrees of freedom that let a motivated reader — me, plausibly — read any result as favorable. Gating a direction decision on one day of work is not an unreasonable bar, and refusing it to protect a recommendation is the behavior of someone who suspects the numbers.

**One dispute, narrow.** The asymmetry claim does not hold as stated. "CI churn" was raised internally, by people who work in the repo, which is the same evidence class as "parametrize kills our copy-pasted variants" — practitioner assertion, uncounted. The objection grants the benefits "real evidence, just uncounted" and assigns the costs "nothing at all," but both entries have the same provenance. This matters little once the spike runs, which is why I concede the remedy while disputing the framing.

---

#### On objection 3 — "test identifiers change shape, silently"

**Conceded outright. This is the objection that changed my position.** What convinced me is that the failure class is silent by construction: a lookup miss against a flake database, a quarantine list, or an ownership map raises no exception. The dotted path and the nodeid genuinely differ, and pytest's JUnit XML populates `classname`/`name` differently from unittest's. My point 6 answered the wrong question — I established that pytest *emits* JUnit XML, which is about format, and then claimed the base case is "close to free," which is about key stability. Those are different claims and I conflated them. A quarantined flake silently returning to blocking, and a flake dashboard resetting to zero while reading as an improvement, are exactly the outcomes that ship.

I accept the remedy: the CI inventory becomes a hard prerequisite deliverable, with a per-consumer choice of migrate-the-key, dual-write, or accept-the-reset, made in advance and out loud.

**Two bounding facts I want on the record, which change the size and not the direction.** First, the dotted-path-to-nodeid transform is a pure function for the ordinary case — module path maps to file path — so "migrate the key" on a quarantine list is a script, not a project. It is the *enumeration* of consumers that costs, and that is the same one-day audit objection 2 already requires. Second, this cost attaches to Decision A, the runner switch, which the objector says he would approve on its merits. So objection 3 does not argue against the direction; it argues that the direction cannot ship as a one-line CI change. That is correct and I withdraw the "one-line change" characterization.

---

#### On objection 4 — "no end state, so the modal outcome is a permanent two-idiom suite"

**Disputed on the substance, conceded on the mechanism.**

The objection treats a permanent mixed suite as the failure mode. Under the default I named in point 8 — opportunistic conversion, new tests pytest-style, old tests converted when someone is already editing them — a permanent mixed suite is the plan, not its collapse. And the carrying cost the objection says I never priced has a specific shape: **an unconverted test that nobody opens imposes approximately no maintenance cost, because maintenance cost is incurred on read and edit.** The mixed-idiom reading burden concentrates in the files people actually open, which is precisely the population opportunistic conversion converts. The objection prices the carrying cost as if it were spread evenly across 6,000 tests. It is spread across the churn distribution, which in any monorepo is heavily skewed.

I also dispute "it doubles the familiarity downside." A Python engineer in 2026 reads pytest whether or not this repo adopts it, so the marginal load is not two idioms versus one. It is the delta of knowing which pytest features silently no-op inside a `TestCase` — a short closed list, teachable in a paragraph, and mechanically detectable. Which is the good part of the objection: **the silence is fixable.** A lint rule or CI grep rejecting `@pytest.mark.parametrize` and non-autouse fixture parameters inside `TestCase` subclasses converts the one genuinely nasty property of the mixed suite from silent to loud.

**Conceded:** the ratchet. A CI check rejecting *new* `unittest.TestCase` subclasses, plus a burn-down count published by the same job every run, together cost about a day and are the only thing that makes opportunistic conversion monotonic rather than merely hopeful. Without them the mixed suite grows and nobody sees the drift for a year. My point 8 argued you do not staff a migration you have not decided to do — that is still right about *owners and windows*, and wrong about the ratchet, which is cheap enough that sequencing is not a defense. I adopt it.

I hold the rest of point 8. Requiring per-package assignment and dates as a precondition for endorsing a direction still inverts the two decisions.

---

#### On objection 5 — "xdist for free is the claim most likely to be false"

**Conceded on the word, disputed on the conclusion.** "Free" should be struck. Parallelism should be reported as a measured wall-clock number, under a named `--dist` mode, with an isolation-repair cost attached. The per-worker fixed-cost risk — DB setup, container spin-up, import time times N in a heavy monorepo import graph — is real, unmeasured, and can eat the speedup whole. The same one-day spike measures it.

**But the objection's own closing sentence concedes my point 2.** "If the suite is not isolation-safe, that is a pre-existing defect the migration merely exposes. Fixing it may be the higher-value project on its own, and it does not require pytest." Agreed on all three clauses — and note where that lands. The isolation-repair project ends with a suite that is safe to distribute and a runner that cannot distribute it. `unittest` ships no parallel execution. So the objection relocates the cost to a prerequisite without producing a path to parallelism from inside `unittest`, which is the capability discontinuity point 2 rests on, and that point stands unrebutted.

Second, the diagnostics the objection prescribes — `pytest-randomly` for randomized ordering, `pytest -n auto` for the distribution delta — are pytest plugins. **The cheapest available instrument for measuring the pre-existing defect is to install pytest and run the existing suite under it.** That is an argument for doing the spike, and the spike is most of the runner switch.

Third, a correction on the evidence. `--dist loadscope` and `--dist loadfile` are not only an admission that arbitrary distribution breaks suites; `loadscope` groups by class and module specifically so that expensive `setUpClass` work runs once per group rather than once per worker. For the `setUpClass`-heavy suite the objection describes, the ecosystem ships the mitigation alongside the problem, and the right spike measures `-n auto` under both `load` and `loadscope`.

---

#### Steelman points that fall

Three, named plainly.

**Point 6 — "the base case is close to free."** Falls to objection 3. Native `--junitxml` answers report *format* and says nothing about *key stability*, and I presented the first as if it settled the second. Anything keyed on a test identifier — flake store, quarantine list, retry rules, ownership routing, historical trend lines — breaks silently at the switch. The residual is still enumerable, which was my other claim in that point, but "close to free" is withdrawn.

**Point 7 — "a closed list of four things, each detected at collection time."** Falls in its completeness claim. My four (`load_tests`, `subTest`, custom `TestResult`/loader, funcarg injection) are collection-time-detectable, but the list is not the list of migration risks — objection 3's identifier break is post-collection and produces no diagnostic at all. The list of *collection* risks may be closed. The list of *migration* risks is not, and I presented one as the other.

**Point 2, bullets 1 and 2 — the fixtures and parametrize arguments.** They survive as claims about validity, which is what that point was arguing: the defect mechanism in copy-pasted variants is real at any N, and no count flips its sign. But I stated them without naming the population they apply to. Corrected: they apply to new tests and rewritten tests, not to the standing 6,000 — degraded for fixtures, absent for parametrize. That qualifier belongs in the recommendation, not in a footnote.

Bullet 3 of point 2, and points 3, 4, and 5, were not engaged and I let them stand as written.

---

#### Where this leaves my case

Narrower and, I think, better. The direction survives every objection — objection 1 endorses the split I argued for, objection 3 attaches its cost to the runner switch the objector would approve, and objection 5 concedes there is no path to parallelism from inside `unittest`. What does not survive is the *cheapness*. I argued a one-line CI change with a `git revert` rollback. Objection 3 shows that is only true if no bespoke machinery is keyed on test identifiers, and nobody has looked.

So the honest version of my case is: switch the runner, after a one-day spike with its decision rule written first and a CI-consumer inventory attached; ship the lint ratchet on day one; strike "for free" from the parallelism claim and "fixes our copy-paste" from the runner-switch justification; and let conversion be opportunistic with a published burn-down. That is my original position with the objector's four cheapest mechanisms bolted on, and I would rather ship that than what I wrote in Phase 4.

## Phase 6 — Judge's Final Report

**Note on procedure.** The two rebuttals were written in parallel: each side answered the other's Phase 4 case, not the other's rebuttal. So several of the Adversary's sharpest points (the `conftest.py` inversion, the P5/P8 contradiction, the "mostly silent, not collection-detected" correction, `param0` instability, reversibility half-life) were never seen by the Advocate. I have not scored those as unopposed wins. I judged them on merits and flagged where the Advocate had a plausible answer available.

## Agreed changes

Objections the Advocate conceded in rebuttal. Both sides now support these; they are ready to act on.

1. **Split the decision in two and price them separately.** Decision A: switch the runner. Decision B: convert idioms. The Advocate accepted the Adversary's framing as more explicit than his own.
2. **State the population the benefits apply to.** On the day after a runner flip, `@pytest.mark.parametrize` applies to new and rewritten tests only — not to the standing 6,000. The Advocate conceded this outright: "Parametrize on an unconverted test is unavailable, full stop." The proposal as written misprices it.
3. **Run a one-day spike with the decision rule written before the numbers arrive.** The Advocate adopted the stronger version of his own point 7, and named why: "a spike whose pass/fail bar is set after the numbers arrive is not a measurement, it is a rationalization with a command line attached."
4. **Produce a set diff of normalized test IDs between the two runners** (incumbent enumeration vs `pytest --collect-only -q`, both normalized to `module.Class.method`, diff the sets, not the totals). This is the artifact that catches silent under-collection from `load_tests`, dynamically generated suites, and ordering assumptions.
5. **Make the CI consumer inventory a hard prerequisite deliverable**, with a per-consumer choice of migrate-the-key / dual-write / accept-the-reset made in advance. The Advocate conceded objection 3 outright and called it "the objection that changed my position."
6. **Withdraw "one-line CI change."** The Advocate retracted this characterization himself.
7. **Ship the lint ratchet on day one**: a CI check rejecting new `unittest.TestCase` subclasses, plus a burn-down count published by the same job every run. The Advocate conceded that sequencing is not a defense for something this cheap.
8. **Strike "for free" from the parallelism claim.** Report parallelism as a measured wall-clock number under a named `--dist` mode with an isolation-repair cost attached.
9. **Add a lint rule making cross-idiom misuse loud** — reject `@pytest.mark.parametrize` and non-autouse fixture parameters inside `TestCase` subclasses. The Advocate proposed this himself as the fix for the mixed suite's one genuinely nasty property.

## Dropped objections

Objections the Adversary withdrew or narrowed, and what answered each.

- **"Gate the decision on a full day of measurement."** Withdrawn. Answered by the Advocate's P1: a cheap, reversible flip does not deserve a heavyweight evidentiary bar. The Adversary replaced the measurement program with one artifact (the test-ID set diff) and demoted wall-clock, isolation-safety, and inheritance counts to informational.
- **"Owner, window, and per-package dates as a precondition."** Dropped. Answered by the Advocate's P8: you do not staff, schedule, or write enforcement for a migration you have not decided to do. The Adversary agreed this inverts the two decisions.
- **"A permanent mixed suite doubles the familiarity downside."** Explicitly withdrawn. Answered by the Advocate's P4: unittest-fluent devs are not forced to learn anything, most cross-idiom misuse fails loudly (and can be made to fail loudly where it doesn't), and incoming pytest fluency arrives free.
- **The ecosystem half of the familiarity downside.** Conceded outright: "pytest is the de facto standard, `unittest` fluency is a depreciating asset, and the hiring flow argument is correct and durable. That is the best argument in the steelman and I have no counter to it."
- **The capability-discontinuity denial.** Conceded in objection 5's reframe: stdlib `unittest` ships no in-process parallel runner, and that is a real discontinuity.

For symmetry, three of the Advocate's own points fell by his own hand: **"the base case is close to free"** (answers format, not key identity), **"a closed list of four things, each detected at collection time"** (a closed list of *collection* risks, presented as the list of *migration* risks), and the **unqualified fixtures/parametrize claims** (valid as mechanisms, wrong about population).

## Contested points

**C1 — How much of benefit 1 survives for unconverted tests.**
Adversary: fixtures and parametrize apply to exactly zero of the 6,000; the cost model and the benefit model describe two different worlds. Advocate: parametrize is absent, but autouse fixtures do work on `TestCase` via `request.instance`, so benefit 1 is degraded, not absent, and the objection collapses two findings into one number. Adversary (rebuttal, unseen by Advocate): the autouse-plus-`request.cls` style "gives up the injection benefit the migration was justified by."

**C2 — Whether `@parameterized.expand` is the alternative the migration has to beat.**
Adversary: it does the same collapse, on `TestCase`, today, with no migration, and produces distinct test IDs — the exact property the Advocate claimed pytest was strictly better at. It remains unpriced. Advocate: it buys one of three benefits, adds a third-party dependency, and leaves the parallelism ceiling untouched — a complement, not a substitute.

**C3 — `conftest.py` vs shared base classes in a monorepo.**
Advocate: directory-scoped resolution maps sharing onto existing ownership boundaries for free, with no import edge; this is the strongest form of the proposer's first point. Adversary (rebuttal, unanswered): it inverts. You end up with a root `conftest.py`, every package inherits fixtures it never referenced, name collisions resolve nearest-wins with no error, and "where does this fixture come from" loses its static answer. Separately, nothing in `unittest` forces the base class outside the owning package — that is an org failure attributed to a framework.

**C4 — Does delay cost anything?**
Advocate (P5): the tail only grows, the option price rises monotonically. Adversary (rebuttal, unanswered): P5 and P8 contradict. Under opportunistic conversion, interim tests would have been `TestCase` anyway, and the runner flip is one line at 6k or 9k.

**C5 — Is asymmetric evidentiary treatment justified?**
Advocate: "CI churn" and "parametrize kills our copy-paste" have identical provenance — uncounted practitioner assertion — so a standard that discounts one must discount the other. Adversary (rebuttal): the asymmetry is optionality, not provenance. Benefits are deferrable (if parametrize disappoints, don't convert); costs are mandatory and front-loaded (the pipeline has to work the morning after).

**C6 — Is a permanent mixed suite the plan or the failure mode?**
Advocate: the plan. Maintenance cost is incurred on read and edit, so the mixed-idiom burden concentrates in the churn distribution, which is exactly what opportunistic conversion converts; the objection prices it as if spread evenly across 6,000 tests. Adversary: what survives is narrower — shared test infrastructure cannot cross the idiom boundary, so a long mixed period means writing new harnesses twice.

**C7 — What parallelism is actually worth here.**
Advocate: no path to parallelism exists inside `unittest`; the diagnostics the Adversary prescribes are themselves pytest plugins, so the cheapest instrument for measuring the pre-existing defect is pytest; `--dist loadscope` groups by class and module specifically to amortize `setUpClass`, so the ecosystem ships the mitigation with the problem. Adversary: file-level sharding across CI jobs is a standard matrix pattern available today with zero migration risk and better isolation properties than `--dist load`; that is the honest baseline, and it was waved away in a subordinate clause. Also, Phase 3 says nothing is currently blocked on wall-clock or flake rate.

## Rulings

**C1 — Split. Advocate wins the fact, Adversary wins the consequence.**
"Zero of the 6,000" is factually wrong: autouse fixtures with `request.instance` do reach `TestCase` subclasses, and that is the documented pattern. But the Adversary's unanswered follow-up lands — what an unconverted test can consume that way is the *relocation* benefit (infrastructure moves from an importable base class into a directory-scoped `conftest.py` under the owning team) and not the *composition-by-injection* benefit that the proposal's first argument is actually about. Correct wording for the recommendation: for unconverted tests, fixtures buy ownership and locality, not injection; parametrize buys nothing. The number is not zero, and the headline benefit still does not apply.

**C2 — Adversary wins.** The Advocate's counter is correct that `parameterized` is not a substitute for the whole proposal, but that was never the claim. The claim is that the cheapest path to headline benefit 2 costs days, requires no migration, and was never priced — and it still isn't. The Advocate's `subTest` demolition is a clean hit on a target the Adversary offered only in passing; it does nothing to `@parameterized.expand`, which produces distinct test IDs. **Concrete outcome:** name `parameterized` in the recommendation as the day-one remedy for copy-paste pain, explicitly decoupled from the runner decision. The Adversary gives up the implication that this defeats the runner switch; the Advocate gives up a benefit line item. The artifact gains an honest floor: the user can buy the most-cited pain relief this week without deciding anything about runners.

**C3 — Adversary wins the narrow claim; the underlying question is a genuine toss-up this transcript cannot settle.** "For free" is too strong — root-level `conftest.py`, nearest-wins shadowing without error, and non-greppable fixture origin are real monorepo failure modes, and the point that `unittest` does not *cause* base classes to migrate into cross-team files is a fair hit. The Advocate had answers available (`pytest --fixtures-per-test` gives a runtime origin; MRO shadowing is silent too; a conftest creates no build-graph edge, which matters in a monorepo with a build system) and simply never saw the argument. I rule the claim overstated rather than wrong, and I give it low decision weight: nothing here moves the recommendation either way.

**C4 — Adversary wins.** The contradiction is real. If the end state is opportunistic conversion, delay costs approximately nothing on the tail axis, and the flip is one line at any suite size. The only surviving delay cost is that the parallelism ceiling stays put, and Phase 3 says nothing is blocked on it. **Concrete outcome:** strike the "delay compounds" urgency argument, or adopt a conversion end state that earns it. Don't keep both.

**C5 — Adversary wins on the reframe; Advocate wins on the original framing.** The Advocate is right that provenance is identical — both entries are uncounted practitioner assertion, and the Phase 4 case did grade them differently for no stated reason. But the rebuttal's replacement argument is correct and the Advocate never got to answer it: optionality is asymmetric, so decision weight can be asymmetric even when measurement status is symmetric. Both sides agree this stops mattering the moment the spike runs, which is why it changes nothing downstream.

**C6 — Advocate wins the main argument; Adversary keeps a real residual.** "Maintenance cost is incurred on read and edit, and churn is heavily skewed" is the best-formed argument either side made, and it defuses the even-spread pricing the objection relied on. The residual is genuine and untouched by it: new shared harnesses serve both populations at once, so they get written twice regardless of churn skew. **Compromise, and I'll flag it as my synthesis rather than either side's:** name permanent-mixed as the intended end state, ship the ratchet, and add one authoring rule — new shared test infrastructure lives in `conftest.py` with an autouse bridge for `TestCase` consumers, so it is written once. The Adversary's caveat from C1 applies: the bridge gives `TestCase` consumers the resource, not the injection ergonomics. That is a real reduction in the duplication cost, not its elimination.

**C7 — Split, and the split is decision-relevant.** The Advocate wins the capability discontinuity outright (conceded) and wins the sharpest tactical point in his rebuttal: the cheapest instrument for measuring isolation-safety is pytest itself, which collapses the isolation question and the spike into one piece of work. `loadscope` amortizing `setUpClass` is also a correct and useful correction. The Adversary wins the baseline: CI-matrix file sharding is standard, available today, carries zero migration risk, and has better isolation properties than `--dist load` — and the Advocate never priced it. The Adversary also wins on the record that nothing is currently blocked on wall-clock or flake rate. **Concrete outcome:** parallelism drops from a headline benefit to a measured, conditional one, and the spike reports four numbers, not two — today serial, CI-matrix sharded, `-n auto --dist load`, `-n auto --dist loadscope` — plus the list of tests that fail only under distribution.

## Judge's recommendation

**Run the spike this week, with the pass/fail rule written before it runs. Do not decide the runner question until the numbers exist.**

The reasoning is that both sides ended up in nearly the same place, and the remaining gap is entirely about what you must produce *before* flipping, not about whether the direction is right. The Adversary conceded the direction is probably right; the Advocate conceded it cannot ship as a one-line change. The three artifacts the Adversary still holds — the test-ID set diff, the CI consumer inventory with a per-consumer choice, and a named end state with the benefits list trimmed to match — cost hours and are the difference between a switch that works and one that goes green while running fewer tests.

The spike does triple duty: it answers the runner question, it measures isolation-safety (which is a pre-existing property of your suite worth knowing regardless), and it produces the ID set diff. That is one day of work returning nearly every "unknown" in this transcript.

Two things I want to flag that neither side foregrounded enough.

First, **nothing in this transcript establishes a problem that is currently hurting.** Phase 3 says nothing is blocked on wall-clock or flake rate. The live case is authoring and maintenance friction, which is real, is the proposer's direct experience, and is uncounted. That bears on *priority*, not on correctness. If your team has something more urgent this quarter, the spike still makes sense as a cheap information purchase; the flip and the CI inventory can wait for a quiet window.

Second, **the copy-paste pain has a same-week fix that does not require any of this.** `@parameterized.expand` collapses duplicated bodies on `TestCase` today, with distinct test IDs. If copy-pasted variants are the acute pain rather than one item on a list, buy that immediately and let the runner decision proceed on its own merits and its own timeline.

What I would not do: approve the migration on the strength of fixtures and parametrize. Those are the two arguments that survive the debate least intact — parametrize does not reach the existing suite at all, fixtures reach it only in degraded form, and the copy-paste win has a cheaper substitute. The arguments that survive strongest are the ones the proposal mentions least: the parallelism capability discontinuity, and the one-way talent flow that makes `unittest` fluency a depreciating asset.

## Your decision

**Option 1 — Spike, then flip (the converged position, and my recommendation).**
Write the decision rule first. Run `pytest --collect-only -q`, produce the normalized test-ID set diff, run serial and `-n auto` under both `load` and `loadscope`, and inventory every CI consumer with a migrate-key / dual-write / accept-the-reset choice per consumer. If the diff is empty or explained and the inventory is tractable, flip the runner with the lint ratchet and burn-down count on day one. Benefits list trimmed: better runner, better assertion output, plugin access, measured parallelism. Conversion is opportunistic, end state is permanent mixed, stated out loud.
Cost: roughly one day of spike plus the inventory. Risk retired: silent under-collection and silent key misses.

**Option 2 — Flip now, artifacts after.**
Cheaper by a day. You accept that quarantine lists, flake history, retry rules, and ownership routing may silently stop matching, and that under-collected tests may leave CI green. Reasonable only if you already know no bespoke machinery is keyed on test identifiers — and nobody has looked.

**Option 3 — Don't flip yet; buy the pain relief directly.**
Adopt `@parameterized.expand` for the copy-pasted variants this week. If wall-clock ever becomes a problem, add file-level CI matrix sharding. Revisit the runner in a quarter. You forgo fixtures, plugin access, and in-process parallelism; you take on essentially no risk. Note the Adversary's own concession here: this leaves you with no path to in-process parallelism at all.

**Option 4 — Commit to full conversion with a budget and an owner.**
Nothing in this transcript prices this. It requires Decision B costed in engineer-weeks, a first-slice target (the highest-churn package), a codemod pass so the work is review rather than typing, and per-package assignment. Both sides agree this is premature today. It becomes a live option only after the spike, and only if the spike shows the conversion is mechanically cheap.

You have final say. The strongest reason to disagree with me: if you already know your CI has no per-test-identifier machinery — no flake DB, no quarantine list, no ownership routing — then objection 3 evaporates, most of the spike's value with it, and Option 2 becomes the right call.
