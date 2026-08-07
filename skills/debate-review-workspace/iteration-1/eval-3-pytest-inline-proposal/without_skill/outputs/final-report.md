# Debate: Migrate Python Monorepo from unittest to pytest

Decision owner: you. This document steelmans both sides, stress-tests each argument, then gives a recommendation.

---

## Framing

The real question is not "is pytest better than unittest" (largely settled: yes, for most teams). It is:

**Does the marginal value of pytest features exceed the migration cost and risk for a 6k-test monorepo with an unittest-fluent team?**

Key fact that shapes everything below: **pytest runs unittest-style tests natively.** You do not have to convert 6k tests to switch runners. That decouples "adopt pytest" from "rewrite the suite," and most of the debate hinges on whether people conflate those two.

---

## Case FOR switching (steelmanned)

### 1. Fixtures beat setUp inheritance
- `setUp`/`tearDown` composition happens through class inheritance and mixins. In large suites this produces deep `TestCase` hierarchies where figuring out what state a test actually has requires walking the MRO. This is a real, compounding maintenance tax.
- pytest fixtures are explicit at the point of use (named in the signature), composable without inheritance, scoped (`function`/`class`/`module`/`session`), and lazily instantiated. Session-scoped fixtures alone (e.g., one DB container for the whole run instead of per-class setup) often produce large wall-clock wins.
- `conftest.py` gives directory-scoped shared fixtures, which maps naturally onto a monorepo layout: each package gets its own fixtures without a central "test utils" god-module.

### 2. Parametrize kills copy-pasted variants
- `@pytest.mark.parametrize` replaces N near-identical test methods with one test and a table. Each case reports as a separate test with its own ID, unlike `subTest`, which is clunkier, reports less clearly, and interacts poorly with some CI reporters.
- If you have copy-pasted variants today, you also have variant drift: someone fixes one copy and not the other four. Parametrization eliminates that failure class, not just the boilerplate.

### 3. Plugin ecosystem, xdist in particular
- `pytest-xdist` gives multi-core parallelism with a flag. For 6k tests, this is frequently a 3-8x CI wall-clock reduction, which is a recurring dividend on every push, forever.
- The rest of the ecosystem compounds: `pytest-cov`, `pytest-randomly` (surfaces hidden inter-test coupling), `pytest-timeout`, flaky-test rerun plugins, rich `--lf`/`--ff` (rerun last failures first) for local dev loops.
- Bare `assert` with assertion rewriting: failure output shows actual values (diffs of dicts, lists, strings) instead of `assertEqual` opacity. Better failure messages mean faster debugging, which is a per-failure dividend across the whole team.

### 4. Ecosystem direction and hiring
- pytest is the de facto community standard. New hires are more likely to know it; modern tooling, docs, and examples assume it. Staying on unittest is a slowly appreciating form of legacy.

### 5. The migration is incremental, not big-bang
- Because pytest collects and runs `unittest.TestCase` classes, you can switch the runner in one small CI change, then migrate tests opportunistically. Cost is spread, not front-loaded.

---

## Case AGAINST switching (steelmanned)

### 1. 6k tests is real inertia
- Even with native `TestCase` support, edge cases exist: heavy custom `TestLoader`/`TestRunner` usage, `load_tests` protocols, custom result classes, and some `setUpClass`/`setUpModule` interactions behave subtly differently under pytest collection. In a monorepo, someone somewhere has done something weird. You will find it the hard way.
- Important limitation: **pytest fixtures cannot be injected into `TestCase` methods, and `parametrize` does not work on `TestCase` classes.** So unconverted tests get none of the headline benefits. The value proposition only materializes as tests are actually rewritten, and 6k tests will not rewrite themselves.

### 2. CI churn is not free
- Runner swap touches CI config, coverage reporting, JUnit XML output paths, flake-detection tooling, any dashboards keyed to test names (pytest node IDs differ from unittest dotted names), and possibly merge-queue rules. Each is small; together they consume real weeks and create a window of "is CI red because of my change or the migration?"
- xdist specifically is not free parallelism: it exposes every hidden test-order dependency and shared-state assumption in the suite. Suites that pass serially often fail under `-n auto` until those are fixed. That is a good long-term outcome but a real short-term cost, and it is the exact moment people will blame the migration.

### 3. Team knowledge is an asset you would be writing off
- Devs fluent in unittest are productive today. pytest fixtures have their own failure modes: fixture spaghetti, magic name-based injection that's hard to trace, overuse of `autouse`, and conftest scoping surprises. A team that half-learns pytest can produce test code worse than disciplined unittest.
- "It's in the standard library" matters at the margin: zero dependency management, guaranteed availability, extremely stable API. pytest majors occasionally break plugins.

### 4. Opportunity cost
- The strongest anti argument: engineering weeks spent on migration are weeks not spent on product or on other test-health work (flakiness, coverage gaps, speed). If the current suite is healthy and CI time is acceptable, "better test framework" is a want, not a need.

### 5. A half-migrated suite is a worse steady state than either endpoint
- If the migration stalls, you own two idioms forever: new devs must learn both, reviewers must enforce two style guides, and shared helpers exist in duplicate. Mixed suites are a known long-term tax. Do not start unless you are willing to govern the long tail.

---

## Weighing the arguments

Where the pro case is strongest:
- The runner-level benefits (xdist, `--lf`, better assertions on new tests, plugins) arrive almost immediately and do NOT require converting old tests. High value, low cost.
- Parametrize and fixtures fix a problem you say you actually have (copy-pasted variants, setUp inheritance). This is not speculative benefit.

Where the anti case is strongest:
- The "convert 6k tests" cost is real, but it is only mandatory if you make it mandatory. The anti case mostly defeats a big-bang rewrite, which nobody needs to propose.
- The xdist-exposes-coupling risk is real and should be planned for, not discovered.
- The half-migrated steady state is the most serious risk and needs an explicit policy, not hope.

The decisive point: **the costs are one-time and capped; the benefits are recurring and compounding.** CI minutes saved, debugging time saved, and boilerplate avoided accrue on every commit indefinitely. The main anti arguments (churn, learning curve) amortize to near zero within a couple of quarters. The only anti argument that survives amortization is opportunity cost, and the incremental strategy shrinks that to a small, controllable spend.

---

## Recommendation

**Switch, via incremental strangler migration. Do not big-bang rewrite the 6k tests.**

Concrete plan:

1. **Phase 0 — runner swap (days, not weeks).** Run the existing unittest suite under pytest in CI. Fix collection edge cases. Keep unittest green in parallel for one sprint if you want a safety net, then delete the old job. Update JUnit XML/coverage wiring once.
2. **Phase 1 — new tests are pytest-style.** Ratchet policy: all new test files use plain functions, fixtures, parametrize. Enforce with a lint rule or CI check (e.g., forbid new `unittest.TestCase` subclasses outside a legacy allowlist). Add a short internal "pytest idioms" guide and one brown-bag session to address the "devs know unittest" concern; the subset of pytest a team needs daily is learnable in an afternoon.
3. **Phase 2 — enable xdist deliberately.** Turn on `-n auto` per-package, not globally, fixing order/state coupling as it surfaces (`pytest-randomly` helps find it early). Bank the CI-time win package by package.
4. **Phase 3 — opportunistic conversion with a ratchet.** Convert old `TestCase` tests only when touched, or when a file would benefit materially (heavy setUp inheritance, copy-paste variants). Track the legacy-allowlist count so it only shrinks. Accept that some stable, never-touched tests may stay unittest-style for years; that is fine because pytest runs them.

Guardrails:
- Timebox Phase 0; if collection edge cases exceed the box, that is new information — pause and reassess.
- Nominate an owner for the migration ratchet so it does not stall into the permanent two-idiom state.
- Fixture hygiene rules from day one: no `autouse` without justification, fixtures live in the nearest `conftest.py`, prefer explicit over clever.

Why this beats "stay": you capture parallelism and dev-loop wins almost immediately for a capped cost, stop accumulating new legacy-style tests, and never pay for a rewrite you don't need. Why this beats "big-bang": all the same end state, a fraction of the risk, no frozen feature work.

Dissent worth honoring: if CI time is currently acceptable AND the copy-paste/setUp pain is mild AND the team has zero slack this quarter, deferring Phase 1+ is defensible. But Phase 0 is cheap enough that there is little reason not to at least put pytest in the driver's seat now.
