# Proposal: Switch the Python monorepo from unittest to pytest

## Position

We should switch our Python monorepo from unittest to pytest.

## Arguments for

1. **Fixtures beat setUp inheritance.** pytest fixtures compose by injection instead of
   class inheritance, replacing deep setUp/tearDown hierarchies.
2. **parametrize kills copy-pasted test variants.** `@pytest.mark.parametrize` collapses
   the copy-pasted test variants we currently maintain by hand.
3. **Plugins give xdist parallelism for free.** The pytest plugin ecosystem, notably
   pytest-xdist, provides test parallelism without building it ourselves.

## Downsides raised internally

- 6,000 existing tests would be affected.
- CI churn from changing the test runner.
- Some developers know unittest well and would face a learning curve.

## Decision context

The team is debating this internally. The proposal author has final say and wants both
sides argued properly before deciding.
