# Proposal: Migrate the Python monorepo test suite from unittest to pytest

## Position

We should switch the Python monorepo from unittest to pytest.

## Arguments for

1. **Fixtures beat setUp inheritance.** pytest fixtures compose by injection instead of
   class inheritance. Our setUp/tearDown hierarchies force tests to inherit state they do
   not use, and fixtures make each test's dependencies explicit.
2. **Parametrize kills copy-pasted test variants.** Many of our tests exist as
   near-duplicate methods differing only in inputs. `@pytest.mark.parametrize` collapses
   these into one test with a case table.
3. **Plugins give us xdist parallelism for free.** The pytest plugin ecosystem, in
   particular `pytest-xdist`, gives parallel test execution without building our own
   runner infrastructure.

## Known downsides (raised internally)

1. **Scale of migration:** roughly 6,000 existing tests.
2. **CI churn:** the CI pipeline is built around the current unittest invocation and
   would need to change.
3. **Team familiarity:** some developers know unittest well and would need to learn
   pytest idioms.

## Decision context

The team is debating this internally. The proposal author has final say and wants both
sides argued properly before deciding.
