# Proposal: Switch the Python monorepo from unittest to pytest

Written out from the proposer's inline request, verbatim:

> ok so we're debating internally whether to switch our python monorepo from unittest to
> pytest. My take: we should switch, because fixtures beat setUp inheritance, parametrize
> kills our copy-pasted test variants, and plugins give us xdist parallelism for free.
> Downsides people raised: 6k existing tests, CI churn, and some devs know unittest well.
> Can you debate both sides of this properly and give me a recommendation? I get final say.

## Structured restatement

**Decision under review:** migrate the Python monorepo's test suite from `unittest` to
`pytest`.

**Arguments for (proposer's case):**

1. Fixtures beat `setUp` inheritance — pytest fixtures compose by injection instead of
   class-hierarchy inheritance.
2. `@pytest.mark.parametrize` eliminates copy-pasted test variants.
3. The plugin ecosystem gives parallelism via `pytest-xdist` "for free".

**Downsides raised internally:**

1. 6,000 existing tests would need migration.
2. CI churn — pipelines, reporting, and tooling built around the current runner.
3. Some developers know `unittest` well and would need to learn pytest idioms.

**Decision authority:** the proposer has final say; this review recommends, it does not
decide.
