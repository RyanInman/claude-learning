# Debate result: switch to pytest, behind four cheap gates

I ran your proposal through a structured four-role debate: I defended it with your three
arguments, a fresh-eyes Adversary attacked it, a fresh-eyes Advocate steelmanned it, both
rebutted each other, and a neutral Judge ruled. Full transcript is in transcript.md; the
Judge's report is in final-report.md. Here is what you need.

## The headline

Nobody, on either side, ended up arguing for staying on unittest. The Adversary opened
with five objections and closed by saying the destination is not in dispute. The debate
instead converged on a sharper claim: your proposal is right, but it asks for a decision
before running four cheap verifications, and one of them genuinely must run first.

## How your three arguments fared

- **Fixtures beat setUp inheritance: survived intact.** The Adversary accepted the
  structural argument (dependency injection over inherited hidden state) and never
  contested it. One caveat it surfaced: pytest fixtures cannot be injected into TestCase
  methods, so this benefit only reaches migrated tests.
- **parametrize kills copy-paste: survived intact.** Conceded on the merits — per-case
  reporting, `-k` selection of a single failing variant, and per-case flake attribution
  all beat `subTest`. Same caveat: parametrize does not work on TestCase methods.
- **Plugins give xdist parallelism for free: survived, minus the word "free."** This was
  the debate's main casualty. Nothing about your suite has been measured: no xdist trial,
  no audit of shared state or order dependence, no baseline CI wall-clock. The Advocate
  itself argued that explicit-dependency (fixture-style) tests are what parallelize
  safely — which quietly makes parallelism downstream of the style migration, not a
  command-line flag. The realistic outcome is a per-package speedup on the isolable
  subset, sized by a pilot.

## How the three downsides fared

- **6,000 existing tests:** mostly defused. pytest runs unittest-style suites natively, so
  the first commitment is a runner swap plus CI config, not a rewrite. But the swap has
  one nasty failure mode both sides flagged: pytest ignores `load_tests` hooks and
  bypasses custom `TestRunner`/`TestResult` classes, so if your estate uses them, tests
  get silently dropped and CI stays green. That is why the compatibility audit gates the
  swap.
- **CI churn:** real, and the debate produced its mitigation — a non-blocking shadow
  pytest job running alongside unittest for 2–4 weeks, comparing collected-test counts,
  pass/fail parity, and coverage per package, with cutover only on parity.
- **Devs know unittest:** the weakest downside. pytest is the ecosystem default; new-hire
  and open-source knowledge skews pytest, and pytest skill transfers while deep unittest
  skill increasingly does not. The learning curve (fixture resolution, conftest scoping)
  is real but bounded by conventions, which need a named owner.

## My recommendation (matching the Judge's)

Switch — but adopt the proposal with a "gates before commitment" section, ordered by the
failure mode each gate prevents:

1. **One-day compatibility audit, before the runner swap.** Grep for `load_tests`, custom
   `TestRunner`/`TestResult`, `subTest`, `setUpModule`. Then require collected-count
   parity between `unittest discover` and `pytest --collect-only` per package, as a
   blocker. This closes the only fail-green risk.
2. **Shadow CI job, 2–4 weeks, per-package cutover on parity.** This turns "we can
   revert" from an assertion into a checked fact and absorbs the CI-churn risk.
3. **One-week xdist pilot on 2–3 representative packages** (one DB-heavy, one pure-unit,
   one integration-flavored). Record baseline wall-clock, speedup, and parallel-only
   failures. Until this runs, stop selling parallelism as "free" in the internal debate —
   it is your most attackable claim.
4. **A one-page governance plan:** named conftest.py owner, a lint rule that new test
   files must be pytest-style, a per-package migration tracker, and one decision only you
   can make — fund a migration finish line with a date, or accept a permanently mixed
   estate in writing. Make that choice with the pilot results in hand: if the pilot shows
   isolation failures, parallelism in those packages waits on funded migration, not
   entropy.

Total gate cost: roughly two days of work plus shadow-CI calendar time, all before any
hard-to-reverse step.

## For your internal debate

The strongest concession to carry back to the skeptics: they are right that "6k tests,
CI churn" deserves respect, and the gated plan spends about two days buying that respect
with numbers. The strongest point for your side: the compatibility path makes the first
step a reversible config change, the ecosystem-default argument went unrebutted through
an adversarial review, and the only option nobody in the debate defended was swapping the
runner with no gates at all.

You have final say. The four options the Judge laid out, with option 1 recommended, are
at the end of final-report.md.
