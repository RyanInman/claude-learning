# Proposal: Migrate Python monorepo test suite from unittest to pytest

## Position

We should switch the Python monorepo from unittest to pytest.

## Arguments for

1. **Fixtures beat setUp inheritance.** pytest fixtures compose via dependency injection;
   unittest forces shared state through `setUp`/`tearDown` and inheritance hierarchies, which get
   brittle and hard to trace as suites grow.
2. **`parametrize` kills copy-pasted test variants.** We currently duplicate near-identical test
   methods for input variations; `@pytest.mark.parametrize` collapses these into one test with a
   data table.
3. **Plugin ecosystem gives xdist parallelism for free.** `pytest-xdist` provides parallel test
   execution with no custom runner work, plus access to plugins like `pytest-cov`,
   `pytest-timeout`, etc.

## Known downsides (raised internally)

1. **Scale:** ~6,000 existing unittest tests.
2. **CI churn:** CI pipelines are built around the current unittest runner.
3. **Team familiarity:** some developers know unittest well and would need to learn pytest idioms.

## Decision context

- Internal debate is ongoing; the proposer has final say.
- No hard deadline stated.

## Amendments (adopted per debate review, phases 7-10)

Note: the CI-speed argument (item 3 under "Arguments for") is now conditional on amendment 3
below; see amendment 1's decision rule.

1. **Week-one pilot.** Run the full suite under plain `pytest` (count collection errors and
   behavior diffs); run the two slow packages under `pytest -n auto` and record parallel failure
   rate and wall-time delta. The pilot sizes the isolation workstream; approval is NOT
   conditional on it. Decision rule (C1): proposer's stated appetite for the isolation
   workstream is 4 person-weeks; if the pilot prices it above that, the CI-speed claim is
   deleted from this proposal and the migration stands on fixture/parametrize/ecosystem grounds
   alone.
2. **Hard cutover gate.** Before CI switches runner: diff unittest discovery test IDs against
   `pytest --collect-only -q` IDs and explain every delta; grep for `load_tests` usage; install
   `pytest-subtests` and verify it reports a deliberately failing `subTest` case. Rationale:
   pytest silently ignores the `load_tests` protocol and mishandles `subTest` without the
   plugin, and this suite uses `subTest`.
3. **Isolation workstream** on the two slow packages (DB-per-worker via template databases,
   ephemeral-port fixtures) as an explicit, costed prerequisite of the CI-speed claim.
   Wall-time target: longest shard 15 min → under 7 min. Appetite: 4 person-weeks (see
   amendment 1).
4. **Targeted conversion workstream.** Greppable inventory of deepest `TestCase` base-class
   chains and largest copy-paste variant families; named owner (proposer); named package list;
   budget one converted package per quarter. Rationale: conversion-on-touch cannot reach the
   hairy families (`parametrize` does not work inside `TestCase` subclasses), so deliberate
   conversion is load-bearing, not optional.
5. **Ratchet sequencing.** Ship `conftest.py` fixture equivalents for the top shared base
   classes (~2 person-weeks), then enable the new-`TestCase`-ban lint per-package as coverage
   lands; tracked suppression comments for the narrow residual case. Adding methods to existing
   `TestCase` classes remains legal.
6. **Shrink metric.** CI-tracked count of `TestCase` subclasses, required monotonically
   non-increasing; proposer reviews the trend quarterly.
