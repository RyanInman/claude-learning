# Judge's Final Report — pytest migration debate review

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
