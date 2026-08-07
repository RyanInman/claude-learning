I ran your proposal through a structured debate review: I defended your case with the context you gave, a fresh-eyes Adversary attacked it, a fresh-eyes Advocate steelmanned it, both rebutted each other, and a neutral Judge ruled on every contested point. The full transcript and the Judge's complete report are saved alongside this reply. Here is where it landed.

## The short version

Both sides converged on "switch, but not the way the proposal argues it." The Adversary conceded the direction is probably right. The Advocate conceded it cannot ship as a one-line CI change. The Judge's recommendation: **run a one-day spike this week with the pass/fail rule written before it runs, and don't decide the runner question until those numbers exist.**

## The one fact that reshaped the debate

Pytest runs `unittest.TestCase` suites natively, so the runner can switch without rewriting the 6k tests — but the same compat layer means `@pytest.mark.parametrize` does not work on `TestCase` subclasses at all, and fixtures reach them only in degraded form (autouse via `request.instance`: you get the shared resource, not injection ergonomics). So two of your three arguments — fixtures and parametrize — apply to new and rewritten tests only, not to the standing 6,000. Your cost story ("no rewrite needed") and your benefit story ("fixtures and parametrize fix our pain") describe different worlds; the honest pitch picks one population per claim.

Consequence the Judge endorsed: split it into two decisions. **Decision A** — switch the runner (buys plugin access, better assertion output, measured parallelism). **Decision B** — convert idioms over time (buys fixtures and parametrize, costs engineer-weeks, only pays if actually executed). Approve A on A's merits; never quote B's benefits as A's justification.

## What both sides ended up agreeing on

- **A one-day spike, decision rule written first.** `pytest --collect-only -q`, a full serial run, and `-n auto` under both `--dist load` and `--dist loadscope`, compared against today's serial time and against plain CI-matrix file sharding.
- **A set diff of normalized test IDs between the two runners** — not counts, sets. This is the only artifact that catches `load_tests`-generated or dynamically built tests silently not being collected. Silent under-collection means tests stop running while CI stays green.
- **A CI consumer inventory before the flip.** unittest names tests `pkg.module.Class.method`; pytest uses nodeids and a different JUnit `classname` derivation. Anything keyed on test identity — flake history, quarantine lists, retry rules, ownership routing — breaks silently, not loudly. For each consumer, choose in advance: migrate the key, dual-write, or accept the reset out loud.
- **A ratchet on day one**: a lint/CI check rejecting new `unittest.TestCase` subclasses, a burn-down count published every run, and a rule making cross-idiom misuse loud (reject `parametrize` inside `TestCase`). This is what makes "new tests are pytest-style" true rather than aspirational.
- **Strike "for free" from the xdist claim.** Parallelism pays only if the suite is isolation-safe, which nobody has tested, and the honest baseline is file-level CI sharding, which needs no migration. Report parallelism as a measured number. (Neatly: the cheapest tool for measuring your suite's isolation-safety is pytest itself, so the spike answers this too.)

## What the Judge would not do

Approve the migration on the strength of fixtures and parametrize — the two arguments that survived the debate least intact. The copy-paste pain also has a same-week fix that needs no migration: `@parameterized.expand` collapses duplicated variants on `TestCase` today, with distinct test IDs. The arguments that survived strongest are ones your pitch barely mentions: the parallelism capability discontinuity (stdlib unittest has no in-process parallel runner, and never will) and the one-way talent flow (pytest is the de facto standard; unittest fluency is a depreciating asset — the "some devs know unittest well" downside shrinks every quarter on its own, and under the compat layer those devs lose nothing anyway).

Also on the record: nothing establishes a problem that is hurting *today* — no wall-clock or flake-rate blocker was named. The live case is authoring friction. That affects priority, not correctness.

## Your options (you have final say)

1. **Spike, then flip** — the converged position and the Judge's recommendation. One day of measurement plus the CI inventory; flip with the ratchet on day one; conversion stays opportunistic, end state is a permanent mixed suite, stated out loud.
2. **Flip now, artifacts after** — saves a day; reasonable only if you already know nothing in CI is keyed on per-test identifiers. Nobody has looked.
3. **Don't flip yet** — adopt `@parameterized.expand` for the copy-paste pain this week, CI-matrix sharding if wall-clock ever hurts, revisit in a quarter. Near-zero risk, but no path to in-process parallelism, ever.
4. **Commit to full conversion with budget and owner** — premature today by both sides' agreement; becomes live only after the spike prices it.

The strongest reason to overrule the Judge: if you already know your CI has no flake DB, quarantine list, or ownership routing keyed on test names, the biggest surviving risk evaporates and option 2 is defensible.

My read matches the Judge's: your instinct to switch is right, but pitch it internally as the runner switch plus an option on conversion, gated on the spike — not as fixtures-and-parametrize for the existing 6k, because that version of the pitch is the one your skeptics can legitimately shoot down.
