# Debate Review: unittest → pytest migration

Your proposal went through a structured four-role debate: a Defender (arguing your position with
full context), a fresh-eyes Adversary, a fresh-eyes Advocate, and a neutral Judge. Five
objections, one rebuttal cycle each way, two brokered compromises, eleven phases. Full transcript:
`transcript.md` alongside this report; the amended proposal is
`../work/proposal.md`.

## Bottom line

**Switch — but your original three arguments needed surgery, and the debate found two real
defects your proposal missed.** No role, at any phase, produced an argument against the
destination. Every surviving disagreement was about execution discipline. The Judge's
recommendation: approve the amended proposal and run a week-one pilot.

## How your three arguments held up

1. **Fixtures beat setUp inheritance — held, and it's your load-bearing argument.** It is
   speedup-independent and survived every attack. Both sides ended up agreeing this justifies the
   migration even if CI gets zero faster.
2. **Parametrize kills copy-pasted variants — held, with a catch you'd have hit in month one.**
   `parametrize` does not work inside `TestCase` subclasses. So your copy-paste families can't be
   collapsed "on contact" — the family must be converted out of `TestCase` first. The benefit is
   real but gated on deliberate conversion work, not free.
3. **xdist parallelism for free — did not hold as stated.** Your slow tests and your
   isolation-unsafe tests (shared Postgres, fixed ports) are substantially the same tests, and
   they dominate the longest CI shard — the one that gates PR feedback. `-n auto` speeds up the
   shards that don't matter. The honest version: parallelism is conditional on ~4 person-weeks of
   isolation work (DB-per-worker, ephemeral ports). The twist that killed this objection anyway:
   that isolation remedy is itself a mature pytest fixture pattern with no unittest equivalent —
   the fix for your CI critical path *requires* pytest.

## Two defects the debate found that nobody had raised internally

1. **Silent correctness loss at cutover.** pytest ignores the `load_tests` protocol outright and
   mishandles `subTest` without the `pytest-subtests` plugin — both failures are silent. A suite
   that goes green on day one while collecting fewer tests than yesterday is a correctness
   regression wearing a passing badge. Fix (cheap, mechanical): before CI switches, diff unittest
   discovery test IDs against `pytest --collect-only -q` IDs and explain every delta; grep for
   `load_tests`; install `pytest-subtests` and verify it reports a deliberately failing
   `subTest` case.
2. **"Convert opportunistically" is a fiction for exactly the tests that hurt.** The humane lint
   ratchet (ban new `TestCase` subclasses, allow new methods on existing classes) creates a
   lint-clean escape hatch: when touching a hairy legacy family, the path of least resistance is
   to extend it, never convert it — because you can't convert one method without porting the
   base-class machinery. Conversion-on-touch is most expensive precisely where the pain is worst.
   The pain you're citing to justify the migration only gets fixed by a deliberate, owned
   conversion workstream.

## The six amendments (all roles converged; now in the proposal)

1. **Week-one pilot** — full-suite collection check under plain pytest; two slow packages under
   `-n auto`. Sizes the isolation work. Approval is NOT conditional on it.
2. **Hard cutover gate** — the ID-diff + `pytest-subtests` verification above. This one gates.
3. **Isolation workstream** — the two slow packages, costed, wall-time target 15 min → under 7
   min for the longest shard.
4. **Targeted conversion workstream** — greppable inventory of deepest inheritance chains and
   largest copy-paste families, named owner, one package per quarter.
5. **Ratchet sequencing** — ship `conftest.py` fixture equivalents for top shared base classes
   (~2 person-weeks) before enabling the per-package `TestCase` ban.
6. **Shrink metric** — CI-tracked `TestCase` subclass count, monotonically non-increasing,
   quarterly review. Turns "shrinks over time" from hope into a checked invariant.

Plus one decision rule (C1): state your appetite for the isolation work — the Defender proposed
4 person-weeks — and if the pilot prices it higher, delete the CI-speed claim from the proposal
entirely and let the migration stand on fixtures/parametrize/ecosystem alone. A headline
deletable by a measurement is worth more than an evergreen conditional.

## On the downsides your colleagues raised

- **6k existing tests**: mostly a non-issue for the switch itself — pytest runs unittest tests
  natively, so day-one cost is a runner change, not a rewrite. It's a real issue for realizing
  the benefits (see amendment 4).
- **CI churn**: priced out to a bounded list — runner invocation, coverage (`pytest-cov` is a
  drop-in), JUnit XML (pytest emits natively), one stdout-parsing script to rework. Roughly a
  day of pipeline work, plus the cutover gate.
- **Devs know unittest**: a one-time, decaying cost (and ~a third of the team already knows
  pytest; two services already use it — the mixed suite is your current state, not a new risk).
  unittest-only friction on every future test is a growing cost. The asymmetry favors switching.

## Your decision

1. **Approve as amended** (Judge's recommendation): pilot in week one, cutover gate before CI
   switches, isolation work capped at your stated appetite, one converted package per quarter.
2. **Approve with a different C1 appetite** — the 4 person-weeks is a judgment call; the pilot
   will test it either way.
3. **Approve the bare runner switch (your original plan, no amendments 4-6)** — the debate
   record is squarely against this: everyone ended up agreeing opportunistic conversion never
   reaches the painful legacy families, so benefits would accrue mostly to future tests.
4. **Reject** — no role produced support for this; the strongest objection inverted into an
   argument for pytest.

You have final say. The debate's honest summary: your conclusion was right, your strongest
stated argument (xdist "for free") was your weakest, your least-emphasized argument (fixtures)
was your strongest, and the plan needed a cutover safety gate and a deliberate conversion
workstream it didn't have.
