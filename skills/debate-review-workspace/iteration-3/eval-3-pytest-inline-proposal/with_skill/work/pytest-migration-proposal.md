# Proposal: Switch the Python monorepo from unittest to pytest

Stated by the proposer, verbatim from their request:

> ok so we're debating internally whether to switch our python monorepo from unittest to
> pytest. My take: we should switch, because fixtures beat setUp inheritance, parametrize
> kills our copy-pasted test variants, and plugins give us xdist parallelism for free.
> Downsides people raised: 6k existing tests, CI churn, and some devs know unittest well.
> Can you debate both sides of this properly and give me a recommendation? I get final say.

## Position

Switch the Python monorepo's test framework from unittest to pytest.

## Arguments for (proposer's)

1. Fixtures beat setUp inheritance.
2. `parametrize` kills copy-pasted test variants.
3. Plugins give xdist parallelism for free.

## Downsides raised internally

1. 6,000 existing tests.
2. CI churn.
3. Some devs know unittest well.
