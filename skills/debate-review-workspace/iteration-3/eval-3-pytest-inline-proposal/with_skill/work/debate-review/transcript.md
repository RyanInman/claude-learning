# Debate Review Transcript

**Artifact:** /Users/admin/claude-learning/skills/debate-review-workspace/iteration-3/eval-3-pytest-inline-proposal/with_skill/work/pytest-migration-proposal.md
**Date:** 2026-08-07

Append-only. Each phase's content lands under its own heading, transcribed verbatim by the
Defender. No role's text is ever edited after it is written.

---

## Phase 1 — Defender: Opening Statement

I did not author this proposal. The proposer is an engineer on the team, stated it inline, and holds the final decision. I present the case the proposal makes, plus the real context the request supplies. Anything beyond that context is unknown, and I will say so rather than invent it.

**Goal.** Replace unittest with pytest as the test framework for the team's Python monorepo.

**The three arguments, and the reasoning each carries:**

1. **Fixtures beat setUp inheritance.** unittest shares test setup through class inheritance: a base TestCase's `setUp`, extended by subclass `setUp` calls chained with `super()`. Deep or diamond-shaped inheritance makes it hard to see what state a given test starts with. pytest fixtures are named, composable, request-scoped dependencies — a test declares exactly what it needs, and scope (function/class/module/session) is explicit rather than implied by class structure.

2. **`parametrize` kills copy-pasted test variants.** The proposer states the codebase has copy-pasted test variants — near-identical test methods differing only in inputs and expected outputs. `@pytest.mark.parametrize` collapses those into one test body with a table of cases. unittest's closest tool, `subTest`, keeps the variants inside one test method with weaker per-case reporting and no per-case selection.

3. **Plugins give xdist parallelism for free.** `pytest-xdist` distributes tests across CPU cores with a command-line flag. unittest has no built-in parallel runner; parallelism there means bolting on external tooling. On a 6k-test monorepo, wall-clock CI time plausibly matters, though no current CI duration was stated.

**Acknowledged downsides, as the proposal frames them:** 6,000 existing tests to migrate, CI churn during the transition, and unittest expertise some developers would partially lose.

**A fact that bounds the migration cost, from pytest itself rather than the proposal:** pytest runs unittest.TestCase suites natively. Switching the runner does not require rewriting the 6k tests up front; rewriting is required only to gain fixtures and parametrize in old tests.

**Least certain points:** the proposal names no timeline, no team size, no CI setup, no measurement of current test suite pain, and no migration plan — it is a position, not a plan. Those gaps are real and the debate should weigh them.

## Phase 2 — Clarifying Questions

### Adversary's questions

1. What does the proposer's team currently use to run the 6k tests in CI — plain `unittest`/`python -m unittest`, `nose`, or an existing third-party runner — and are there any existing custom `TestCase` base classes, `load_tests` protocol hooks, or runner-level plugins (coverage, retries, sharding, custom result reporters) that the current setup depends on?

2. Is the monorepo's test suite currently known to be safe to run in parallel — i.e. are there existing shared-state dependencies (module-level singletons, shared DB or fixture files, temp-dir collisions, test ordering assumptions) that would need to be resolved before `pytest-xdist` could actually be turned on?

3. On the two claims the proposal treats as established facts — "copy-pasted test variants" and "unittest expertise some developers would partially lose" — what is actually known: any count or share of tests that are copy-paste variants, and any number for how many developers hold the unittest expertise versus how many already know pytest?

### Advocate's questions

**Q1. Scope of "switch."** Does the proposer's "switch" mean swapping the runner and writing new tests pytest-style while the existing 6,000 `unittest.TestCase` tests stay as-is, or does it mean converting those 6,000 tests to fixtures and `parametrize`? Is there anything in the request that settles which one the proposer meant, or is that genuinely unstated?

**Q2. Limits of the compatibility path.** On the point that pytest runs `unittest.TestCase` suites natively — what does that compatibility actually cover and not cover for a suite like this one (for example `setUpClass`/`setUpModule`, `addCleanup`, `subTest`, the `load_tests` protocol, custom `TestRunner`/`TestResult` subclasses, and whether pytest fixtures can be requested from inside a `TestCase` method)? And is any of that known about this specific codebase, or is it a general property of pytest?

**Q3. Facts vs. inferences in the stated context.** Which of these are stated by the proposer and which are your inference: that copy-pasted test variants exist in meaningful volume, that setUp inheritance is deep or diamond-shaped, and that CI wall-clock time is a felt pain? Separately, is anything known about CI runner core count, the current CI configuration, coverage/reporting tooling tied to unittest output, team size, or existing pytest familiarity — or is each of those simply absent from the request?

## Phase 3 — Defender's Answers

**Adversary Q1 (current runner, base classes, runner-level tooling).** Unknown. The request states only that the monorepo uses unittest and has 6k tests. Nothing is stated about how CI invokes them, whether custom `TestCase` base classes exist, whether `load_tests` is used, or what coverage/retry/sharding/reporting tooling the CI depends on.

**Adversary Q2 (parallel safety).** Unknown. The request does not state whether tests share state or assume ordering. The proposal's "xdist parallelism for free" claim assumes parallel safety; that assumption is unverified. Note the phrase "for free" is the proposer's; no measurement supports or contradicts it.

**Adversary Q3 (quantified copy-paste and expertise).** No counts exist in the request. "Copy-pasted test variants" is stated by the proposer as a fact about the codebase, but with no number or share. "Some devs know unittest well" is likewise stated without a count, and nothing is stated about how many devs already know pytest.

**Advocate Q1 (scope of "switch").** Genuinely unstated. The proposer says "switch our python monorepo from unittest to pytest" and cites benefits that only arrive in tests written pytest-style, but names no scope: runner-only, full conversion of the 6k tests, or something between. The proposal is a position, not a plan.

**Advocate Q2 (limits of pytest's unittest compatibility).** This is a general property of pytest, not knowledge of this codebase. What the compatibility covers, per pytest's own documentation: `TestCase` subclasses are collected and run, including `setUp`/`tearDown`, `setUpClass`/`tearDownClass`, `setUpModule`/`tearDownModule`, `addCleanup`, skip/expectedFailure decorators, and `subTest`. What it does not cover: the `load_tests` protocol is not respected; custom `TestRunner`/`TestResult` subclasses are bypassed entirely because pytest replaces the runner; `pytest.mark.parametrize` does not work on `TestCase` methods; and pytest fixtures cannot be requested as arguments in `TestCase` methods — only autouse fixtures and `usefixtures`-marked class-level injection reach them. Whether this codebase uses `load_tests` or a custom runner is unknown (see Adversary Q1).

**Advocate Q3 (facts vs. inferences).** Stated by the proposer: copy-pasted test variants exist ("parametrize kills our copy-pasted test variants" — volume unstated); fixtures-vs-setUp framed as a felt problem ("fixtures beat setUp inheritance" — depth and shape of the inheritance are my illustration of the general unittest pattern, not stated facts about this codebase); CI churn as a downside of switching (raised by colleagues — but current CI pain from wall-clock time is not stated anywhere; my opening said "plausibly matters," which is inference). Absent from the request entirely: CI runner core count, CI configuration, coverage/reporting tooling, team size, and existing pytest familiarity. All unknown.

## Phase 4 — Cases

### Adversary's case

#### Objection 1 — The cost-bounding fact and the benefits are mutually exclusive; the proposal never picks a scope, so it prices neither

**Problem.** The proposal's three benefits and its one affordability argument cannot both be true of the same migration. The Defender's opening bounds the cost with "pytest runs unittest.TestCase suites natively — switching the runner does not require rewriting the 6k tests up front." But the Defender's own Phase 3 answer to Advocate Q2 states that on `TestCase` methods, `pytest.mark.parametrize` does not work and fixtures cannot be requested as arguments. So in the cheap scope (runner swap, tests untouched), arguments 1 and 2 deliver **zero** value against the existing 6,000 tests — they apply only to tests written after the switch. In the scope where arguments 1 and 2 pay off, the 6,000 tests must be rewritten and the affordability argument evaporates. The proposal reads as if you get both, because it never names a scope. That is not a gap in detail; it is the decision itself going unmade.

**Evidence.** Transcript Phase 3, Advocate Q1: scope is "genuinely unstated… The proposal is a position, not a plan." Phase 3, Advocate Q2: the compatibility path explicitly excludes `parametrize` and argument-injected fixtures on `TestCase`. Two-thirds of the affirmative case rests on features that are unavailable in exactly the mode that makes the migration cheap.

**Better way.** Split the artifact into two independently-decidable proposals with separate price tags, and make the proposer choose:

- **Decision A — runner swap.** Adopt pytest as the CI runner, leave all 6,000 tests as `unittest.TestCase`. Benefit delivered: xdist, better failure output, richer selection. Cost: days, and reversible by changing one CI command. Arguments 1 and 2 are explicitly *not* claimed here.
- **Decision B — idiom conversion.** Convert `TestCase` tests to pytest-style functions. Benefit delivered: fixtures and `parametrize` on old tests. Cost: 6,000 tests of mechanical-but-not-automatic edits, with a real number attached before approval (convert 50 representative tests, measure minutes-per-test, multiply).

Decision A can be approved today on its own merits. Decision B needs the evidence Objection 4 asks for. Bundling them lets the cheap decision's affordability launder the expensive decision's cost.

#### Objection 2 — "xdist parallelism for free" is the load-bearing claim, it is the one claim with a known-unverified precondition, and a cheaper alternative delivers most of the same win

**Problem.** After Objection 1, parallelism is the *only* argument that pays off against the existing 6,000 tests without rewriting them — so the whole near-term case rests on it. And it is the claim the Defender concedes is unverified: the suite's parallel-safety is unknown. "For free" is false in the ordinary case. Turning on `-n auto` against a suite that has never run concurrently surfaces shared-DB collisions, temp-dir and fixture-file collisions, module-level singletons, and order dependencies. That debugging work is the dominant cost of parallelising a legacy suite, and it is a cost you pay *whatever* runner you use — it is not caused by unittest and not cured by pytest. Meanwhile there is an alternative the proposal never mentions: sharding tests across CI containers requires no framework change at all and scales across machines rather than across one machine's cores.

**Evidence.** Transcript Phase 3, Adversary Q2: "Unknown… The proposal's 'xdist parallelism for free' claim assumes parallel safety; that assumption is unverified." Phase 3, Advocate Q3: CI runner core count, CI configuration, and current CI wall-clock are all absent — so nobody has established that intra-machine parallelism is even the binding constraint, or that CI wall-clock is a felt pain at all (the Defender flags their own "plausibly matters" as inference).

**Better way.** Run a one-day spike *before* the decision, and let its output settle the argument:

1. `pip install pytest pytest-xdist`; run `pytest` over the existing tree with no code changes. Record: collected count, pass/fail delta vs. the current runner, wall-clock.
2. Run `pytest -n auto`, then `-n 4`, `-n 8`. Record wall-clock at each and the list of tests that fail only under concurrency.
3. Report three numbers: serial wall-clock, best parallel wall-clock, and count of parallel-unsafe tests.

If the parallel-unsafe count is small, "for free" is roughly true and Decision A is a clear yes. If it is large, the honest framing is "pytest plus N days of de-sharing shared state," and it must be compared against CI-level sharding, which buys similar wall-clock for zero framework risk. Either way the debate's biggest unknown becomes a measured number for less effort than writing the proposal took.

#### Objection 3 — Swapping the runner can silently drop tests, and the proposal has no reconciliation gate

**Problem.** The Defender established that pytest does not respect the `load_tests` protocol and bypasses custom `TestRunner`/`TestResult` subclasses entirely, and separately that whether this monorepo uses any of them is unknown. That combination is the worst kind of risk: the failure is silent. A `load_tests` hook that generates a suite programmatically does not error under pytest — those tests simply stop being collected. CI goes green while running fewer tests than before. Same for a custom `TestResult` that a coverage gate, flake-retry, or reporting pipeline hangs off: it is not invoked, and downstream tooling reports success on no data. In a monorepo, runner-level hooks are exactly where teams put their sharding, retry, and reporting glue, so the prior that *something* is hooked there is high.

**Evidence.** Transcript Phase 3, Advocate Q2 (what compatibility does not cover) combined with Adversary Q1 ("Unknown… whether custom `TestCase` base classes exist, whether `load_tests` is used, or what coverage/retry/sharding/reporting tooling the CI depends on"). Unknown presence plus silent bypass equals unbounded, undetectable blast radius.

**Better way.** Make one mechanical gate a hard precondition of any CI change, and put it in the proposal:

- Enumerate collected test IDs under the current runner and under pytest over the same tree, diff the two sets, and require the diff to be empty or every entry individually explained. A non-empty unexplained diff blocks the switch.
- Grep the repo for `load_tests`, `TestResult`, `TestRunner`, `TextTestRunner`, and custom `TestCase` base classes, and list every hit with its owner.
- Run both runners in CI in parallel for one to two weeks, comparing pass/fail *and* counts, before the old runner is removed.

This costs hours and converts the single unbounded risk in the proposal into a bounded, checkable one.

#### Objection 4 — There is no baseline, so success is undefinable and the migration cannot be stopped on evidence

**Problem.** Every quantity that would justify the migration is absent: no CI wall-clock, no flake rate, no count or share of copy-paste variants, no measure of `setUp` inheritance depth, no team size, no count of devs who already know pytest. A change touching 6,000 tests with no baseline has two failure modes. First, it cannot be evaluated afterward — six months in, nobody can say whether it helped, so the sunk cost defends itself. Second, it cannot be *abandoned* on evidence, because there is no threshold that would count as disconfirmation. Note also that the two facts the proposal asserts about the codebase — that copy-pasted variants exist in meaningful volume, and that `setUp` inheritance is painful — are, per the Defender, one unquantified proposer assertion and one illustration of the general unittest pattern rather than a stated fact about this repo.

**Evidence.** Transcript Phase 3, Adversary Q3: "No counts exist in the request." Phase 3, Advocate Q3: the inheritance-depth characterisation is the Defender's illustration, "not stated facts about this codebase," and CI pain is inference.

**Better way.** Require four numbers and three thresholds in the proposal before approval:

| Measure | How | Threshold that kills the matching argument |
|---|---|---|
| Near-duplicate test methods | AST-normalise test bodies, cluster identical shapes; report share of the 6k | Under ~15% → argument 2 is not worth a migration |
| Max and median `TestCase` inheritance depth; count of custom base classes | Static walk of the class graph | Median depth ≤ 2 with no diamonds → argument 1 is theoretical here |
| CI wall-clock p50 and p90 today | CI history | If nobody is waiting on it, argument 3 has no payoff to buy |
| Devs who wrote a pytest test in the last 12 months | `git log` over test files | Informs the training cost the proposal currently prices at zero |

Then state the success criterion the same way: e.g. "CI p50 down 40% within one quarter, and duplicate-cluster share below 5% within one year, or we stop and re-evaluate."

#### Objection 5 — The dual-idiom period is the real people cost, it is unbounded, and the proposal names the wrong one

**Problem.** The proposal lists "some devs know unittest well" as the human downside. That is the weakest version of the real cost, and it is close to a non-cost: nobody unlearns unittest, and the knowledge stays useful. The actual cost is that any scope short of a big-bang rewrite leaves the monorepo with **two test idioms simultaneously**, for a duration the proposal does not bound. Every reviewer must know both. Every new dev learns a hybrid. Worse, per the Defender's Q2 answer, the two idioms cannot share setup cleanly — a pytest fixture cannot be requested as an argument by a `TestCase` method, so shared setup gets written twice, once as a fixture and once as a base-class `setUp`, and the two drift. That duplication is precisely the maintainability problem argument 1 claims to solve, reintroduced by the migration itself and left running for years.

**Evidence.** Transcript Phase 3, Advocate Q1 (scope unstated — so the dual period has no stated end) and Advocate Q2 (fixtures unreachable from `TestCase` methods except via autouse or `usefixtures`, which is a coarser, less composable channel). At 6,000 tests with opportunistic conversion, the dual period is measured in years, not weeks.

**Better way.** Force the proposal to name an end state and a bridge:

- **End state, pick one and write it down.** Either (a) conversion completes by a dated milestone, tracked as a converted-percentage metric emitted by CI so the number is visible and cannot quietly stall; or (b) permanent dual idiom, accepted explicitly, with a written rule — new test files are pytest-style, `TestCase` files are converted only when already being modified for another reason, and never as standalone churn.
- **Bridge for shared setup during the dual period.** Put shared setup in plain functions and context managers in a `testsupport` module. A pytest fixture becomes a thin wrapper around it; a `TestCase.setUp` calls it directly. Neither idiom owns the logic, so nothing is written twice and nothing drifts. This is worth doing on day one regardless of which end state is chosen, and it is cheap.

### Advocate's case

#### The case in one line

The proposal picks the one direction in this decision whose exit is cheap, whose costs are one-time and whose benefits are recurring, and it does so at the right altitude for the question the proposer actually asked. Its brevity is not thinness — it is a directional call submitted for a directional debate, held by the person with both the context and the decision authority.

#### 1. This is a one-way door in only one direction, and the proposal walks through the cheap side

pytest collects and runs `unittest.TestCase` suites natively. unittest cannot run pytest-style tests — no `parametrize`, no fixture injection, no conftest resolution. The two frameworks are not symmetric alternatives; pytest is a superset runner.

That asymmetry does most of the work in this decision:

- **Adoption is reversible in practice.** Swapping the runner is a CI command change. If it goes badly before any test is rewritten, reverting is the inverse command change. Framework migrations are usually dangerous because the first step is irreversible; here it is not.
- **Deferral is not neutral.** Every test written under unittest between now and a later decision is a test that must be converted later to get the stated benefits. The inventory that the "6,000 existing tests" downside describes grows monotonically while the decision is open.
- **The reverse migration is the expensive one.** If the team adopts pytest and later wants out, that is the costly direction. Choosing pytest strictly expands the option set; staying on unittest does not.

A decision that expands options, whose first step is a config change, and whose cost of delay is positive is exactly the kind that should be made on direction rather than on measurement.

#### 2. The benefit curve starts above zero on day one, before a single test is rewritten

The Defender established that pytest runs the existing suite natively and framed that as *bounding the migration cost*. It does more than that: it means a meaningful share of the value lands on the unconverted 6,000 tests immediately, at runner-swap cost.

What the 6,000 untouched `TestCase` tests get the day the runner changes:

- `-k` expression selection and node-id selection, which unittest supports far more coarsely
- `--lf` / `--ff` (rerun last failures, failures first) and `-x` / `--sw`, which change the inner debugging loop on a large suite more than any authoring feature does
- Richer failure output and traceback control (`--tb`), and structured reporting through the plugin layer rather than through a custom `TestResult`
- The plugin ecosystem itself — `pytest-cov`, `pytest-timeout`, `pytest-randomly`, `pytest-rerunfailures`, JUnit XML output — as installs rather than as in-house runner code
- `pytest-xdist`, subject to the parallel-safety caveat in point 4

This matters for how the "6,000 tests" downside should be read. The 6,000 tests are an *inventory to convert opportunistically*, not a *bill due at migration time*. The proposal's benefits and its largest stated cost are not actually coupled the way a naive reading suggests, and a migration whose value is front-loaded and whose cost is amortized over ordinary maintenance is the favorable shape.

#### 3. "Fixtures beat setUp inheritance" is a monorepo argument, not a style preference

The Defender argued fixtures on visibility grounds — a test declares what it needs, scope is explicit. True, but the sharper version is structural, and it turns on the word *monorepo* in the proposal's title.

Sharing setup through `setUp` inheritance requires a shared base class. In a monorepo, shared setup that spans teams means a base `TestCase` that spans ownership boundaries. That produces the failure modes monorepos are specifically prone to:

- One team's change to the shared base class can break another team's tests, so the base class ossifies and grows by accretion rather than being refactored.
- A test class can only inherit one setup lineage cleanly; needing two orthogonal setups (a DB and a fake clock, say) forces either multiple inheritance or a fatter base.
- Setup a test does not need still runs, because inheritance is all-or-nothing. On a suite this size that is a direct wall-clock cost.

Fixtures invert all three. `conftest.py` resolves by directory, which maps onto monorepo ownership boundaries — a team's fixtures live in that team's directory and are visible to that team's tests without any global registry. Composition is by request, not by lineage, so orthogonal setups compose without a class hierarchy. And a test that does not request a fixture does not pay for it.

Fixture scoping (`session`, `module`, `class`, `function`) is separately a CI-time lever independent of parallelism: a session-scoped database or container is expressible in one decorator argument, where the unittest equivalent means `setUpModule`/`setUpClass` plus manual lifecycle management. On a 6k suite with any I/O-bound setup, this is plausibly the larger of the two speed levers, and the proposal gets it as a side effect of argument 1.

#### 4. "xdist for free" is correctly attributed, even granting that parallel safety is unverified

The Defender flagged that the suite's parallel safety is unknown. That is true and worth knowing — but it is not a mark against the argument, for two reasons.

**Parallel-safety work is framework-independent.** Shared module-level state, temp-dir collisions, ordering assumptions, and shared DB fixtures are properties of the tests, not of the runner. If the team wanted parallelism under unittest, they would pay the same audit. The audit is therefore not a cost of migrating to pytest; it is a cost of wanting parallelism at all. What the proposal claims is free is *the distribution mechanism*, and that claim is correct: under pytest it is `pip install pytest-xdist` and `-n auto`; under unittest it is a build-it-yourself sharding harness plus its own maintenance.

**xdist degrades gracefully rather than requiring a clean bill of health.** `--dist loadfile` and `--dist loadscope` schedule whole files or whole classes to a single worker, which preserves within-file and within-class ordering and isolates most shared-state hazards. A team with unaudited state can capture the coarse-grained speedup first and tighten the granularity as isolation improves. The parallel-safety unknown therefore gates *how much* speedup is available on day one, not *whether* the argument holds.

#### 5. `parametrize`'s payoff is behavioral, and `subTest` is genuinely not a substitute

The Defender's comparison to `subTest` was correct but understated. The differences that matter in practice:

- **Per-case selection.** A parametrized case is a distinct node id, so a single failing case can be rerun in isolation, `-k`-filtered, xfailed, or skipped individually. A `subTest` case cannot be addressed from the command line at all — you rerun the whole method.
- **Per-case reporting.** Parametrized cases are counted and reported as separate tests, so a flaky case is visible in CI history as a flaky test. `subTest` failures collapse into one test's result.
- **Per-case marking.** `pytest.param(..., marks=pytest.mark.xfail)` lets one known-broken case be quarantined without disabling the rest. `subTest` has no equivalent.
- **Cost of adding a case.** This is the second-order one. Under parametrize, adding a case is a one-line diff to a table. Under copy-paste, it is a new method. The marginal cost of a test case is what determines whether engineers actually add edge cases, so this is a coverage argument disguised as a deduplication argument.

The proposer states copy-pasted variants exist in their codebase. Volume is unquantified, but the direction of the claim is a statement about their own code, made by someone who reads it daily, in an internal debate where colleagues could contradict it. That is weaker than a count and stronger than speculation.

#### 6. The cost/benefit shapes are asymmetric in time, and the downside list is honestly ordered

All three stated costs are one-time or decaying: the 6,000-test inventory is converted once and never again; CI churn is a transition-window phenomenon; unittest familiarity is a learning curve that flattens. All three stated benefits are per-test-written and per-CI-run — they recur for the life of the codebase. Integrated over any horizon a monorepo implies, that shape favors switching, and it is the standard justification for paying migration cost at all.

The third downside deserves particular credit for being listed *last*, because it is the weakest and the proposal did not inflate it:

- The knowledge is not destroyed. pytest runs `TestCase` suites, so existing unittest fluency stays directly productive on the existing 6,000 tests indefinitely.
- The transfer is asymmetric in the easy direction. pytest's core authoring model is a plain function and a bare `assert`. Someone who knows `assertEqual`, `assertRaises`, and `setUp` is not learning a harder API; they are dropping one.
- The pool is growing, not shrinking. pytest is the de facto standard for Python testing; new hires increasingly arrive already fluent, and major library test integrations (`pytest-django`, `pytest-asyncio`, `pytest-mock`, Hypothesis) target it. unittest's ecosystem is effectively frozen at the standard library. Betting on the framework the ecosystem is already flowing toward is a hiring and dependency argument, not just a taste one.

That a pro-switch proposal volunteered three real costs, unprompted, and ordered them by weight rather than leading with the softest, is evidence the document is an honest position rather than advocacy dressed as analysis.

#### 7. Being a position rather than a plan is the correct sequencing, not an omission

The Defender listed as "least certain": no timeline, no team size, no CI setup, no measurement, no migration plan. Every one of those is true. None of them is a defect in this artifact.

The proposer asked, verbatim, "Can you debate both sides of this properly and give me a recommendation? I get final say." They asked for a directional verdict on a go/no-go. A migration plan authored before the go/no-go is sunk work if the answer is no-go, and a plan authored by a debate participant would prejudge the very question under debate. The correct sequence is decide direction, then plan; the artifact sits at the first step and does not pretend otherwise.

The missing measurements are worth a second look too. "Measure current CI pain before deciding" sounds rigorous, but on a decision with this shape — cheap reversible first step, positive cost of delay, benefits that arrive incrementally — a measurement gate is a common way that correct migrations die. The measurement that would actually settle the question (what does the suite look like after conversion) can only be obtained by converting some of it, and the incremental path makes that a pilot rather than a study.

The proposer also holds context the artifact does not transcribe. They work in this codebase, they raised this in an internal debate where colleagues pushed back with three specific objections, and they retain final say. The document is a faithful record of a live internal disagreement, not a research report that failed to cite sources.

#### 8. What this case does not carry

Stated plainly so the Judge can weigh it: I am not arguing that the proposal is a plan, that the 6,000 tests should be converted wholesale, that xdist can be enabled without a parallel-safety pass, or that any of the three benefits has been quantified for this codebase. I am arguing that the direction is right, that the reasons given are the right reasons, that the costs are correctly named and correctly ordered, and that the level of detail matches the decision being made. The gaps the Defender flagged are real — they are gaps in the *next* document, not errors in this one.

## Phase 5 — Rebuttals

### Adversary's rebuttal

#### Rebutting the steelman, point by point

##### Against 1 — "reversible first step" and "deferral is not neutral" cannot both be cashed, and "superset" is the wrong word

The reversibility claim is true only in the state where no pytest-style test exists and no `conftest.py` has been written. Point 1's own second bullet urges the team out of that state immediately: if deferral is costly because every new unittest test is future conversion work, then the first sprint after adoption produces function-style tests that `python -m unittest` cannot collect at all. The reversible window is days wide, and the steelman's own advice is to close it. A property that expires on first use should not be doing "most of the work in this decision."

Second, "pytest is a superset runner" is an overclaim that the Defender's own Phase 3 answer refutes. pytest is a superset of the `TestCase` *authoring* API and a strict non-superset of the unittest *runner* API: `load_tests` is ignored, and custom `TestRunner`/`TestResult` subclasses are bypassed. Whatever the team has hanging off those hooks does not survive the "inverse command change" round trip unnoticed, because during the pytest window that tooling was not running.

Third, "choosing pytest strictly expands the option set" is false in one direction the proposal prices at zero. unittest is stdlib: it does not break your CI on a release you did not ask for. Adopting pytest puts a third-party runner plus a plugin compatibility matrix (`pytest-cov`, `pytest-xdist`, and whatever else accretes) on the critical path of every merge, to be pinned, upgraded, and unbroken across Python version bumps. That is small, but it is a recurring maintenance cost, and "strictly expands" denies it exists.

##### Against 2 — the day-one list is real, and roughly half of it is already available under unittest

This is the most useful thing in the steelman and it deserves auditing rather than acceptance. Taking the list item by item against a plain `python -m unittest` baseline:

- `-k` expression selection: unittest has had `-k` since Python 3.7. Node-id selection by dotted path has always existed. Not a delta.
- `-x`: unittest has `--failfast`/`-f`. Not a delta.
- `pytest-cov`: a wrapper around coverage.py, which already runs unittest via `coverage run -m unittest`. JUnit XML: available today via `unittest-xml-reporting`. Not deltas.
- "Richer failure output": this is the one that matters least where the steelman needs it most. pytest's assertion introspection rewrites bare `assert` statements. The 6,000 existing tests call `self.assertEqual`, which routes through unittest's own failure messages. Those tests get better *traceback formatting*, not better assertion diffs. The flagship day-one benefit largely does not land on the inventory point 2 invokes it for.

What survives as genuinely new on day one for untouched `TestCase` tests: `--lf`/`--ff`/`--sw`, traceback control, `pytest-randomly` / `pytest-rerunfailures` / `pytest-timeout` as installs, and xdist. That is a real and worthwhile list. It is also a list of things the proposal never claims. Point 2 wins the argument for a document nobody wrote — and the document it wins it for is Decision A from Objection 1. It concedes the split rather than defeating it.

##### Against 3 — `conftest.py` is not the opposite of a shared base class, it is the same object with implicit resolution

The monorepo framing is the sharpest reasoning in the steelman, and the ownership-by-directory mapping is genuinely attractive. But "fixtures invert all three" does not survive contact with how large pytest monorepos actually age.

- Cross-team ossification is not solved, it is relocated. Every large pytest monorepo grows a root `conftest.py` that spans ownership boundaries, and it ossifies for exactly the reason the base `TestCase` did: one team's edit breaks another team's tests. The mechanism is unchanged; only the file name is.
- Explicitness is traded away, not gained. A base class appears on the class declaration line. Fixture resolution is by *name*, walking up the directory tree, with silent shadowing when a child `conftest.py` defines the same name — and the test site shows nothing. Autouse fixtures show nothing at all.
- "A test that does not request a fixture does not pay for it" is exactly false under autouse, which is the mechanism monorepo root conftests reach for and the only mechanism that reaches `TestCase` methods at all. So during the dual-idiom period, the shared setup that must serve both idioms is forced into the one fixture form that reintroduces the all-or-nothing cost this bullet claims to eliminate.

And the session-scoped-database lever collides with point 4. Under xdist each worker is a separate process, so a `scope="session"` fixture runs **once per worker**. A session-scoped container or database is either instantiated N times (cost multiplier) or shared across N workers that were written assuming exclusive access (correctness hazard). Getting one shared session resource across workers requires the file-lock coordination dance from the xdist docs. Points 3 and 4 are each other's counterexample: the two speed levers the steelman offers cannot be pulled together without work neither point prices.

##### Against 4 — `--dist loadfile` is the concession that hands the argument to CI sharding

I accept the accounting correction: the parallel-safety audit is chargeable to *wanting parallelism*, not to pytest. My Objection 2 said so in those words. What that correction does is not rescue the argument — it dissolves argument 3's ability to discriminate between the options.

Point 4's own escape hatch proves it. If the safe day-one configuration for an unaudited suite is `--dist loadfile` — whole files pinned to one worker, process-isolated — then the safe day-one configuration is behaviorally identical to sharding test files across CI containers, which needs no framework change, no plugin, no audit, and scales across machines rather than across one machine's cores. "Under unittest it is a build-it-yourself sharding harness plus its own maintenance" overstates the alternative: shard-by-file is a CI matrix strategy over a split file list, not a harness.

So the honest statement of argument 3 is: pytest gives you a nicer interface to coarse-grained parallelism you can already have. That may well be worth it. It is not "for free," and it cannot carry the near-term case alone. Meanwhile nobody in this debate knows the current CI wall-clock, so nobody knows whether single-machine core count is even the binding constraint.

##### Against 5 — the mechanism is conceded; the volume defense is not evidence

Per-case node ids, per-case `xfail` via `pytest.param(marks=...)`, per-case flake visibility in CI history, and the marginal cost of adding a case are all correct, and the coverage-argument-in-disguise framing is the best reasoning in the steelman on this point. I concede the mechanism entirely and withdraw any implication that `subTest` is close.

Two things do not follow. First, none of it reaches the 6,000 existing tests: `parametrize` does not work on `TestCase` methods, per Phase 3. This is an argument for Decision B or for new tests, not for the bundle. Second, the volume defense — "a statement about their own code, made by someone who reads it daily, in an internal debate where colleagues could contradict it" — is not evidence. Colleagues *did* contradict, three times, and none of the three was "there aren't many duplicates." That silence is uninformative precisely because nobody has a count. An AST-normalise-and-cluster pass over the test tree is an afternoon and converts the claim into a number.

##### Against 6 — the cost list is honestly ordered and materially incomplete

Ordering is not the property under test. Completeness is. "All three stated costs are one-time or decaying" is true of the three that are stated and false of the decision, because the recurring cost — two simultaneous idioms in one repo, with shared setup unable to cross the boundary cleanly — is not on the list. Worse, points 2 and 7 both recommend the policy (opportunistic conversion) that makes that cost permanent rather than transitional. "Converted once and never again" quietly assumes conversion finishes; under the steelman's own recommended path there is no mechanism that finishes it.

I do concede one bullet outright, and it is the strongest directional argument anywhere in this transcript: the ecosystem is flowing to pytest, `pytest-django` / `pytest-asyncio` / `pytest-mock` / Hypothesis target it, unittest's ecosystem is frozen at the stdlib, and new hires increasingly arrive fluent. I had not weighted that. It makes "new tests are written pytest-style" close to unarguable on a multi-year horizon. Note what it argues for: adopting the runner and setting a convention. That is Decision A.

##### Against 7 — this point proves too much, and it concedes the mechanism it rejects

"A measurement gate is a common way correct migrations die" is asserted with no instance and generalises to a rule under which no migration should ever be measured. It also contradicts itself two sentences later: "the incremental path makes that a pilot rather than a study." A pilot with a decision attached *is* a measurement gate. Objection 4's core ask — convert ~50 representative tests, measure minutes-per-test, multiply — is that pilot, renamed. The steelman has conceded the mechanism and disputed the label.

Separately, three of the four numbers I asked for require converting nothing and cost hours, not a study: a grep, an AST pass, and a query against CI history. And the cheapest gate of all, Objection 3's collected-test-ID diff, is not a study at all — it is a safety check. No correct migration has ever died of running `pytest --collect-only` and diffing the output.

Finally, "the proposer holds context the artifact does not transcribe" is an appeal to evidence that cannot be examined. In a debate whose entire record is this artifact, untranscribed context is unweighable by construction — and the Defender already established that one of the three arguments (setUp inheritance pain) has no stated codebase evidence at all, only the Defender's illustration of the general unittest pattern. Deference to unstated context is what the proposer asked us *not* to give when they asked for the debate.

#### Re-assessment of the objections

##### Objection 1 — sustained, narrowed

Sustained. The steelman did not close the scope gap; it demonstrated it by spending its two strongest sections on two different scopes — point 2 argues Decision A, points 3 and 5 argue Decision B — without ever naming which one is being approved.

Narrowed on one point: I wrote that in the cheap scope the migration delivers "zero" value against the 6,000 tests. That is correct as stated about arguments 1 and 2, and I stand on it. But point 2 established that the runner swap has real day-one value the proposal never claimed (`--lf`/`--ff`/`--sw`, traceback control, plugin ergonomics), and that raises Decision A's expected value. Decision A is now, on this record, a likely yes. Decision B is still unpriced. The split is more necessary after the steelman, not less.

##### Objection 2 — sustained, reframed

Sustained, with the framing moved. I drop the implication that unverified parallel safety is a cost of choosing pytest; it is a cost of choosing parallelism, and point 4 is right about that. What I now argue instead is stronger: point 4's own `--dist loadfile` fallback establishes that the safely-available day-one configuration is file-granular distribution, which CI-level sharding already provides at zero framework risk. Argument 3 therefore cannot discriminate between the options until someone produces a wall-clock number.

I also credit the graceful-degradation fact as new to me and materially risk-reducing for Decision A. And I add a cost the steelman created: session-scoped fixtures run once per xdist worker, so points 3 and 4 cannot be banked together without lock coordination.

The one-day spike stands unchanged and is now cheaper to justify than any other item in this transcript: three numbers — serial wall-clock, best parallel wall-clock, count of concurrency-only failures.

##### Objection 3 — sustained and strengthened; nothing in the steelman touches it

Sustained, and it is now my primary objection. Eight sections of steelman never mention `load_tests`, custom `TestResult`, or the collection-set diff. Two of them make the risk worse: point 1's reversibility guarantee silently assumes the two runners collect the same set of tests, which is the unverified thing; and point 2 recommends moving reporting off a custom `TestResult` onto the plugin layer, which is the exact bypass whose failure mode is a green CI over a shrunken suite.

The ask is unchanged and costs hours: diff collected test IDs between runners and require an empty or fully-explained diff; grep for `load_tests`, `TestRunner`, `TestResult`, `TextTestRunner`, and custom base classes; run both runners in CI for one to two weeks comparing counts as well as pass/fail. This should be a hard precondition on Decision A, which is otherwise approvable today.

##### Objection 4 — mostly dropped; a slimmed version survives

I drop the following, and name what convinced me.

- The claim that the migration "cannot be abandoned on evidence" and that sunk cost will defend it. Point 1's cheap-exit argument defeats this for Decision A: a runner swap that has not yet been built on is abandoned by reverting a CI command. My objection borrowed the psychology of expensive migrations and applied it to a cheap one.
- The inheritance-depth measure and the `git log` pytest-familiarity measure. Both produce numbers with no non-arbitrary threshold attached, and point 6's ecosystem argument makes the familiarity number backward-looking and near-useless. They were table filler.
- My "under ~15%" duplicate threshold as a specific figure. It was invented. What matters is that the proposer names *a* threshold, not that I name it.

What survives, narrowed to two numbers. CI wall-clock p50/p90 from existing CI history, because argument 3 has no payoff to buy without it and it is free to obtain. And duplicate-cluster share via an AST pass, required before **Decision B only**, because Decision B is the expensive one and it is the number that prices it. Point 7 is right that a directional go/no-go on Decision A does not need a research phase; it is wrong that a 6,000-test conversion does not need a price.

##### Objection 5 — sustained and strengthened by the steelman itself

Sustained, and the steelman raised its severity three ways. Point 6 lists every cost as one-time while omitting the only recurring one. Points 2 and 7 both recommend opportunistic conversion, which is the policy under which the dual-idiom period never ends. And point 3's `conftest.py` mechanism makes the bridge worse than I described: because fixtures cannot be argument-injected into `TestCase` methods, shared setup that must serve both idioms is pushed into autouse fixtures, which are the least visible and least selective fixture form — the opposite of the explicitness argument 1 is sold on.

The ask is unchanged and both halves are cheap. Name an end state in writing: either a dated conversion milestone with a converted-percentage metric emitted by CI so the number cannot quietly stall, or an explicitly accepted permanent dual idiom with a written rule that `TestCase` files convert only when already being touched. And build the `testsupport` bridge on day one regardless — shared setup as plain functions and context managers, with a thin fixture wrapper on one side and a `setUp` call on the other, so no logic is written twice and nothing drifts. The steelman offered no argument against the bridge, and under its own recommended path the bridge is what keeps the dual period survivable for the years it will last.

### Advocate's rebuttal

#### Objection 1 — Scope is unnamed. Disputed in its framing, conceded in its remedy.

**What I dispute: the artifact never bundles the two.** Objection 1's charge is that "the proposal reads as if you get both, because it never names a scope," and that bundling "lets the cheap decision's affordability launder the expensive decision's cost." Check the source. The affordability fact is not in the proposal. It appears at transcript line 27, introduced by the Defender under the explicit label "from pytest itself rather than the proposal," and the artifact itself lists "6,000 existing tests" as an unmitigated downside with no offsetting claim attached. The proposal makes no affordability argument at all. The laundering Objection 1 describes is a Defender contribution to the debate, and the correct target of that criticism is Phase 1, not the artifact under review.

**What I dispute second: A and B are not independently decidable.** The proposed split asks the proposer to choose between two proposals with separate price tags. But Decision B is unreachable without Decision A — you cannot convert `TestCase` tests to fixtures and `parametrize` while unittest is still the runner, because unittest cannot execute the output. They are strictly sequential, not independent. And the dichotomy omits the path both my point 2 and the Adversary's own Objection 5 end-state (b) describe: runner swap now, conversion opportunistically on files already being touched. On that path there is never a 6,000-test bill due, and arguments 1 and 2 pay off from day one on new and newly-modified tests. "Zero value against the existing 6,000 tests" is true only of tests nobody touches, and a test nobody touches is a test whose authoring ergonomics cost nothing.

**What I concede.** The scope sentence should exist, and its absence is a real defect in the artifact. One line — "adopt pytest as the runner now; convert `TestCase` tests only when already modifying them" — resolves the ambiguity, costs nothing, and is the sentence the Adversary's Objection 5 independently arrives at. I would hand the Judge that sentence rather than the two-proposal split.

#### Objection 2 — Sustained against, except the spike, which I adopt.

**The framework-independence argument went unanswered.** Objection 2 asserts the de-sharing work "is the dominant cost of parallelising a legacy suite" and then concedes in the same breath that "it is a cost you pay whatever runner you use." Those two sentences settle it: a cost incurred identically under both options is not a discriminator between them. What differs is the distribution mechanism, and there `pip install pytest-xdist` against a build-it-yourself harness is not a close comparison.

**The objection does not engage `--dist loadfile` / `--dist loadscope`.** My point 4 argued that xdist degrades gracefully: scheduling whole files or classes to one worker preserves within-file and within-class ordering and isolates the majority of shared-state hazards. Objection 2's failure list (temp-dir collisions, module-level singletons, order dependencies) is largely a fine-grained-distribution failure list. The unknown gates how much speedup arrives on day one, not whether any does.

**The CI-sharding alternative is weaker than presented, and it collides with Objection 3.** Sharding across containers requires the same file-granularity isolation as `--dist loadfile`, plus cross-container isolation of shared external resources like a shared DB, which is harder because separate containers cannot coordinate through process-local state. It also requires building and balancing the split, and merging coverage and reporting. "No framework change at all" is true; "no work at all" is not. More pointedly: Objection 3 argues the prior is high that this monorepo already has sharding glue hanging off a custom runner. If that prior is right, the suite already runs distributed, file-level parallel safety is already established, and "for free" is closer to true than either objection allows. Objections 2 and 3 lean on opposite priors about the same unknown and cannot both be at full strength.

**What I concede: run the spike.** `pip install pytest pytest-xdist`, collect, run serial, run `-n auto`, record three numbers. It costs a day, requires converting nothing, and turns Adversary Q2's unknown into data. What convinced me is the cost: my point 7 argued against measurement gates because the measurement that settles this question requires conversion to obtain — that argument does not reach a measurement obtainable in a day with zero code changes. I dispute only its status as a *precondition to the direction*. No spike output makes unittest the better long-term framework; it reprices argument 3. Run it alongside the decision, not in front of it.

#### Objection 3 — Conceded. This is the objection that found something my case missed.

Silent collection loss through `load_tests` and bypassed custom `TestResult` is a real failure mode, it is silent by construction, and my case did not address it anywhere. The proof is the Defender's own Phase 3 Q2 answer — pytest does not respect `load_tests` and bypasses custom runners entirely — sitting against Adversary Q1's "unknown whether this codebase uses them." I adopt the collected-test-ID diff as a hard precondition.

One addition the Adversary did not state, which strengthens their case: the failure compounds with argument 3. If collection silently drops a subset of tests and xdist lands in the same change, the wall-clock improvement gets attributed to parallelism when part of it is the suite running fewer tests. The parity diff must therefore run *before* xdist is enabled, not alongside it.

Where I hold: "unbounded, undetectable blast radius" overstates it. The risk is undetectable without the gate and fully detectable with it, and the gate is a set diff of two ID lists. That is the class of risk that becomes a checklist item, not the class that reprices a direction.

#### Objection 4 — Baseline conceded, thresholds disputed on specifics.

**Concede:** CI wall-clock p50/p90 comes free from CI history, it is the honest denominator for argument 3, and a written success criterion is worth having. Take those two rows.

**Dispute the duplicate-share threshold, on causality.** "Under ~15% near-duplicate share → argument 2 is not worth a migration" reads low duplication as evidence of no problem. Per my point 5, `parametrize`'s dominant effect is on the marginal cost of *adding* a case going forward. A codebase at 3% duplication may sit there precisely because adding a variant costs a new method, so engineers do not add them. Under-duplication is a plausible symptom of missing edge-case coverage, not proof of its absence. The threshold can kill a live argument with the metric pointing the wrong way.

**Dispute the inheritance-depth threshold, on statistic choice.** "Median depth ≤ 2 with no diamonds → argument 1 is theoretical here" measures the wrong dimension. The monorepo pain my point 3 described is fan-in, not depth: one shared base `TestCase` inherited by 2,000 test classes across eight teams ossifies exactly as described, and scores as depth 2 with no diamonds. Measure fan-in of the widest shared base class and the count of cross-team dependents, or the measurement will exonerate the problem it was built to find.

#### Objection 5 — Naming conceded, severity disputed.

The dual-idiom period is a better name for the human cost than "some devs know unittest well," and the `testsupport` bridge — shared setup in plain functions, a fixture wrapping it, `setUp` calling it — is correct and cheap. Both belong in the next document.

The severity does not survive its own remedy. An objection that supplies a fix it calls "cheap" and "worth doing on day one regardless" has described a checklist item, not an unbounded cost. And the drift it warns of is not introduced by the migration: under unittest in a monorepo, orthogonal setups already force duplication across inheritance lineages because a class inherits one setup lineage cleanly. The dual period rotates that duplication's axis rather than creating it. Note also that Objection 5's end state (b) — new files pytest-style, `TestCase` files converted only when already being modified, never as standalone churn — is the opportunistic path from my point 2, endorsed by the Adversary as acceptable. The two cases converge on the same operating rule.

#### Steelman points that fall or narrow

**Point 1, "adoption is reversible in practice" — narrows, and only Objection 3's gate restores it.** I claimed reverting is the inverse CI command change. That is true of the configuration and false of the consequences: if collection silently dropped tests, reverting the command does not undo weeks of green CI over a smaller suite, nor the defects that shipped under it. Reversibility of the switch is not reversibility of the damage taken while it was on. With the collected-ID parity gate in place the claim holds as stated; without it, it does not. Objection 3 earns this.

**Point 7, "measurement gates are how correct migrations die" — stated too broadly.** The argument holds against measurement that requires the migration to answer. It does not reach a one-day install-and-run spike or a query against CI history already recorded. I withdraw the general form and keep the narrow one.

**Point 2's reporting bullet — the same mechanism, two signs.** I listed "structured reporting through the plugin layer rather than through a custom `TestResult`" as a day-one benefit. Objection 3 correctly identifies that if a custom `TestResult` exists today, pytest bypasses it silently. It is one fact, and whether it reads as benefit or hazard depends entirely on Adversary Q1's unknown. Until the grep for `TestResult` / `TestRunner` / `load_tests` runs, I should not have counted it as a benefit.

#### What the Judge is left with

Five objections, one of which (3) found a genuine hole in my case and earns a hard precondition; three of which (1, 4, 5) resolve into cheap annotations — a scope sentence, two baseline numbers with better-chosen statistics, a `testsupport` bridge and a written dual-idiom rule; and one (2) whose central mechanism I sustain, minus a one-day spike I am glad to adopt. Total added cost before the switch: roughly two days of grep, diff, and instrumentation. None of it reprices the asymmetry that drives the direction — pytest runs `TestCase`, unittest does not run pytest, delay grows the inventory, and the first step is a config change. The artifact should be approved with those preconditions attached, not split, deferred, or gated on a study.

## Phase 6 — Judge's Final Report

### Agreed changes

These are objections the Advocate conceded in rebuttal. Both sides now support them.

1. **Collection-parity gate before the runner switch (Objection 3).** Enumerate collected test IDs under the current runner and under pytest over the same tree, diff the two sets, and require the diff to be empty or every entry individually explained. Grep for `load_tests`, `TestRunner`, `TestResult`, `TextTestRunner`, and custom `TestCase` base classes, and list every hit with an owner. The Advocate called this "the objection that found something my case missed" and adopted the diff as a hard precondition. The Advocate added a sequencing point the Adversary had not stated: run the parity diff *before* enabling xdist, so a wall-clock improvement caused by silently running fewer tests cannot be misattributed to parallelism.

2. **A scope sentence in the artifact (Objection 1's remedy).** The Advocate conceded the absence is "a real defect in the artifact" and offered the sentence: adopt pytest as the runner now; convert `TestCase` tests only when already modifying them. Note that this is identical to the Adversary's own Objection 5 end state (b). The two cases converged on the same operating rule from opposite directions.

3. **The one-day spike (Objection 2's remedy).** Install pytest and pytest-xdist, run `--collect-only`, run serial, run `-n auto`, record three numbers: serial wall-clock, best parallel wall-clock, count of concurrency-only failures. The Advocate adopted it and named what changed their mind — their point 7 argued against measurement that requires the migration to obtain, and that argument does not reach a measurement obtainable in a day with zero code changes. (They still dispute its *ordering*; see Contested points.)

4. **Two baseline numbers and a written success criterion (Objection 4, surviving portion).** CI wall-clock p50/p90 from existing CI history, conceded as "the honest denominator for argument 3." A written success criterion in the proposal.

5. **Rename the human cost and build the bridge (Objection 5, conceded portion).** "The dual-idiom period" is a better name for the people cost than "some devs know unittest well." The `testsupport` bridge — shared setup as plain functions and context managers, with a thin fixture wrapper on one side and a `setUp` call on the other — is "correct and cheap" and belongs in the next document.

6. **Three self-corrections the Advocate volunteered.** Point 2's "structured reporting through the plugin layer rather than through a custom `TestResult`" should not be counted as a day-one benefit until the grep runs, because the same fact is a hazard if a custom `TestResult` exists. Point 7's general claim that measurement gates kill correct migrations was "stated too broadly" and is withdrawn in its general form. Point 1's reversibility claim holds only with the parity gate in place.

### Dropped objections

- **"The migration cannot be abandoned on evidence; sunk cost will defend it" (Objection 4).** Dropped by the Adversary, who named what convinced them: the Advocate's cheap-exit argument. A runner swap not yet built on is abandoned by reverting a CI command. The Adversary said their objection "borrowed the psychology of expensive migrations and applied it to a cheap one."

- **Inheritance-depth and `git log` pytest-familiarity measures (Objection 4).** Dropped as "table filler" — both produce numbers with no non-arbitrary threshold, and the ecosystem argument makes a backward-looking familiarity count near-useless.

- **The "~15%" duplicate-share threshold (Objection 4).** Dropped as invented. The Adversary's residual position is that the proposer must name *a* threshold, not that the Adversary names it.

- **"Unverified parallel safety is a cost of choosing pytest" (Objection 2's original framing).** Dropped. The Adversary accepted the accounting correction: de-sharing work is chargeable to wanting parallelism, not to pytest, and is therefore not a discriminator between the options.

- **Any implication that `subTest` approaches `parametrize`.** Conceded outright. The Adversary accepted per-case node ids, per-case `xfail` via `pytest.param(marks=...)`, per-case flake visibility, and the marginal-cost-of-adding-a-case framing, calling the coverage-argument-in-disguise reading the best reasoning in the steelman on that point.

- **Implicit in the above: the direction itself.** The Adversary conceded the ecosystem bullet as "the strongest directional argument anywhere in this transcript" and said it makes "new tests are written pytest-style" close to unarguable on a multi-year horizon. Both sides now support adopting the runner. Nothing in the record argues for staying on unittest.

### Contested points

**1. Split into two proposals, or one proposal with a scope sentence.** Adversary: bundle the cheap runner swap with the expensive idiom conversion and the cheap decision's affordability launders the expensive one's cost; approve Decision A today, price Decision B first. Advocate: the laundering charge mis-targets the artifact, because the affordability fact is a Defender contribution at Phase 1, not a claim the proposal makes; and A and B are not independently decidable, since you cannot convert tests to `parametrize` while unittest is still the runner. One scope sentence resolves it.

**2. Does the spike gate the decision, or run alongside it.** Adversary: the spike settles the debate's biggest unknown for less effort than writing the proposal took, so run it before deciding. Advocate: no spike output makes unittest the better long-term framework, so it reprices argument 3 rather than settling direction; run it alongside.

**3. Can argument 3 (xdist) discriminate between the options.** Adversary: `--dist loadfile` is behaviorally the same as sharding files across CI containers, which needs no framework change and scales across machines, so argument 3 cannot discriminate until someone produces a wall-clock number. Advocate: CI sharding is not free — it needs the split built and balanced, coverage and reporting merged, and cross-container isolation of shared external resources, which is harder than process-local isolation.

**4. How much day-one value lands on the untouched 6,000 tests.** Adversary's audit: `-k`, `-x`/`--failfast`, coverage.py, and JUnit XML are all available under unittest today; pytest's assertion introspection rewrites bare `assert`, so 6,000 `self.assertEqual` tests get better traceback formatting but not better assertion diffs. Advocate did not reply to the audit (same round). Both agree a residual list survives: `--lf`/`--ff`/`--sw`, traceback control, `pytest-randomly` / `pytest-rerunfailures` / `pytest-timeout` as installs, and xdist.

**5. Do fixtures actually invert the monorepo problem.** Adversary: a root `conftest.py` ossifies for the same reason a shared base `TestCase` does; fixture resolution is by name up the directory tree with silent shadowing; autouse — the only form that reaches `TestCase` methods — reintroduces the all-or-nothing cost; and a `scope="session"` fixture runs once per xdist worker, so points 3 and 4 cannot be banked together without file-lock coordination. Advocate's prior position: `conftest.py` maps onto ownership boundaries, composition is by request rather than lineage, and unrequested fixtures cost nothing.

**6. Severity of the dual-idiom period.** Adversary: "all three stated costs are one-time or decaying" is false, because the recurring cost — two idioms with shared setup unable to cross the boundary cleanly — is not on the list, and the opportunistic path both sides now endorse never finishes the conversion. Advocate: an objection that supplies a fix it calls cheap and worth doing regardless has described a checklist item; and the drift is not created by the migration, since a class already inherits only one setup lineage cleanly.

**7. Two smaller unanswered Adversary points.** The reversibility window is "days wide" because the steelman's own deferral argument urges writing function-style tests immediately. And "choosing pytest strictly expands the option set" denies a real recurring cost: a third-party runner plus a plugin compatibility matrix on the critical path of every merge, to be pinned and unbroken across Python version bumps.

### Rulings

**1. Split vs. scope sentence — compromise, and the Advocate wins the two factual sub-points.** I checked the artifact. It is 26 lines, it lists "6,000 existing tests" as an unmitigated downside, and it contains no affordability claim. The affordability fact appears only at transcript line 27, explicitly labeled by the Defender as "from pytest itself rather than the proposal." The laundering charge is aimed at the wrong document. The Advocate is also right that B is unreachable without A; they are sequential, not independent, so "two independently-decidable proposals" is the wrong shape. But the Adversary wins the substance underneath: a 6,000-test conversion campaign must not be approved by the same act that approves a CI command change. Compromise: one document, one scope sentence, and that sentence must do two jobs — approve the runner swap plus opportunistic conversion, *and* state explicitly that any wholesale conversion campaign is a separate future decision requiring a price. The Adversary gives up the two-document split; the Advocate gives up a scope sentence that only names the near-term path and stays silent on the expensive one.

**2. Spike ordering — Advocate, narrowly.** The Adversary conceded the ecosystem argument, which is a directional argument no spike can overturn. That concession makes the Advocate's position correct as stated: the spike reprices argument 3, it does not decide direction. But the distinction is nearly free to honor. The spike takes a day and the parity gate is already agreed as a hard precondition, so both run before CI is flipped anyway. Practical resolution: run the spike before flipping CI, do not make it a gate on the go/no-go.

**3. xdist vs. CI sharding — unresolved on the record, and neither side can win it here.** The Adversary is right that `--dist loadfile` and file-sharded CI containers are behaviorally similar and that no one in this debate knows the current CI wall-clock. The Advocate is right that "no framework change" is not "no work." Neither claim can be adjudicated without the number both sides have now agreed to obtain. Ruling: argument 3 carries no weight in the decision until the spike and the CI-history query report. Strike it from the justification for now; restore it if the numbers support it.

The Advocate's collision argument — that Objections 2 and 3 lean on opposite priors about the same unknown, since a monorepo with sharding glue already runs distributed and has file-level parallel safety established — is clever but only half-lands. Objection 3's prior is disjunctive ("sharding, retry, *and* reporting glue"); retry or reporting glue implies nothing about parallel safety. The agreed grep resolves it either way, so nothing turns on it.

**4. Day-one benefit audit — Adversary wins, with one overstatement corrected.** I verified the checkable claims. unittest has had `-k` since Python 3.7 and `-f`/`--failfast` for far longer; coverage.py runs `coverage run -m unittest`; `unittest-xml-reporting` provides JUnit XML. The assertion-introspection point is the sharpest and is correct: pytest rewrites bare `assert` statements, so 6,000 tests calling `self.assertEqual` route through unittest's own failure messages and gain traceback formatting, not assertion diffs. One correction against the Adversary: pytest's `-k` supports a boolean expression language (`"a and not b"`), while unittest's `-k` accepts substring/glob patterns OR'd together. "Not a delta" overstates; it is a small delta. Net effect: the Advocate's point 2 list should be trimmed to the residual both sides accept. That residual is real and worth having, and it is smaller than the steelman implied.

**5. Fixtures in a monorepo — split, with one clean Adversary win.** The session-scope-per-xdist-worker point is correct and unanswered: each xdist worker is a separate process, a `scope="session"` fixture runs once per worker, and sharing one external resource across workers requires lock coordination. The Advocate's "one decorator argument" framing for a session-scoped database is wrong as soon as xdist is on. Adversary wins that outright. On the broader claim, I do not accept "the same object with implicit resolution." A root `conftest.py` can ossify exactly as described, and silent fixture shadowing is a real cost the steelman did not price — but directory-scoped resolution and composition-by-request are genuine structural differences from single-lineage inheritance, and the Adversary's rebuttal does not dispute those, only their sufficiency. Score it: the Adversary lands the two concrete corrections (autouse is all-or-nothing and is the only channel to `TestCase` methods; session scope breaks under xdist), the Advocate keeps the structural claim.

**6. Dual-idiom severity — Adversary wins the framing, Advocate wins the severity.** The Adversary is factually right that "all three stated costs are one-time or decaying" is false under the path both sides now endorse. Opportunistic conversion has no completion mechanism, so the dual-idiom state is permanent by design, not transitional. That should be written down as an accepted permanent state rather than described as a transition. The Advocate is right that a cost with a cheap, agreed remedy is a checklist item, not something that reprices the direction, and right that a monorepo on unittest already duplicates setup across lineages. Both halves belong in the output: name the state as permanent, accept it explicitly, build the bridge, and do not treat it as a reason to hesitate.

**7. The two unanswered smaller points.** On reversibility: the Adversary is right that the window is not permanent and that the steelman's own deferral argument closes it, but "days wide" overstates. The exit cost grows linearly with the number of function-style tests written, and converting a few dozen back is small. Reversibility degrades gradually over months, not abruptly. The Advocate's own narrowing — reversibility of the switch is not reversibility of the damage taken while it was on — is the more serious version of this point and is already handled by the agreed parity gate. On third-party dependency: the Adversary wins this cleanly and it is unanswered. A pinned third-party runner plus a plugin matrix on the critical path of every merge is a small recurring cost, and "strictly expands the option set" denies it exists. Add one line to the downside list; do not weight it heavily.

**8. Duplicate-share number.** The Adversary dropped the specific threshold; the Advocate disputed the causality (low duplication can be a symptom of engineers not adding cases, because adding one costs a new method). The Advocate's causal argument is sound and defeats using the number as a kill threshold. It does not defeat obtaining the number. Compromise: run the AST-normalise-and-cluster pass only if a wholesale conversion campaign is proposed, and use the output as a price input, not as a kill switch. The Advocate's fan-in statistic (widest shared base class, count of cross-team dependents) is the better measure if anyone measures inheritance at all — the Adversary had already dropped the depth measure, so there is no dispute here, just a better suggestion left on the table.

### Judge's recommendation

**Approve the direction with preconditions attached, and require the scope sentence to name what is *not* being approved.**

The reasoning: the Adversary conceded the ecosystem argument and, with it, the direction. No argument surviving this transcript favors staying on unittest. What the Adversary won is not "don't switch" — it is precision about what the switch buys and what it silently risks. Objection 3 is the one finding that would have caused real harm if missed, and the Advocate conceded it completely; it costs hours and converts the only unbounded risk into a checklist item. Objection 1 identified a real hole (no scope) even though its diagnosis mis-attributed a Defender sentence to the artifact, and both sides independently arrived at the same fix. Objection 5's mechanism was conceded and its remedy is cheap.

Where I part from the Advocate: their day-one benefit list is materially thinner than presented, and argument 3 currently carries no weight at all. That does not change the recommendation, but it changes the honesty of the justification. If this proposal is approved on "xdist parallelism for free" and "richer failure output," it is approved on two claims that this debate substantially deflated. It should be approved on the two that survived intact — pytest runs `TestCase` and unittest does not run pytest, and the ecosystem is flowing one way — plus the deferral cost that follows from them.

Where I part from the Adversary: the two-proposal split imposes structure the decision does not have, since B strictly requires A. The scope sentence does the same work at lower cost, provided it explicitly says a wholesale conversion campaign is a separate decision.

On cost: the Advocate's "roughly two days" covers the spike, the grep, the parity diff, and the CI-history query, and that arithmetic holds. It omits the Adversary's ask to run both runners in CI for one to two weeks before removing the old one. That is calendar time rather than effort, and I would keep it — it is nearly free and it is the second net that catches what a single parity diff misses.

### Your decision

**Option 1 (recommended).** Approve the direction with a revised artifact containing: a scope sentence approving the runner swap plus opportunistic conversion, and stating that any wholesale conversion campaign is a separate decision requiring a price; the collection-parity diff and hook grep as hard preconditions; the one-day spike run before flipping CI but not gating the go/no-go; CI wall-clock p50/p90 and a written success criterion; the dual-idiom period named as a permanent accepted state with the `testsupport` bridge built on day one; the third-party dependency cost added to the downside list; and argument 3 held in abeyance until the spike reports. Both runners in CI for one to two weeks before the old one is removed. Roughly two days of work plus a two-week overlap window.

**Option 2.** The Adversary's original structure: two separately approved decisions, A now and B priced later. You give up nothing in safety and gain a harder separation between the cheap and expensive commitments, at the cost of a document structure that does not match the sequential dependency between them. Choose this if you expect organizational pressure to treat approval of the runner swap as approval of a conversion campaign — the structure resists that better than a sentence does.

**Option 3.** Approve as-is with only the Objection 3 gate attached, and skip the spike, the baselines, the scope sentence, and the bridge. Defensible if you are confident the proposer will make those calls in the plan document that follows. The cost is that the two deflated arguments stay in the record as justification, and the dual-idiom end state stays unnamed.

**Option 4.** Gate the decision on the spike and the CI-history numbers, deciding nothing until they land. I do not recommend this — the Adversary themselves conceded the direction is carried by an argument no measurement can overturn — but it is the honest choice if your real uncertainty is whether the team has bandwidth for any migration right now, which is a question this debate never touched.
