# Unit tier - golden state

Weight: 20%. The unit tier is the always-on fast loop: seconds locally, minutes at worst in CI.

## What "unit" means

A unit test runs in-process and talks to no external service. The tier boundary is what the
test talks to, not how long it takes.

- Mock only at owned seams: your HTTP client wrapper, your model wrapper, a payment-gateway stub.
- Never mock your own business modules to force a pass.
- A real DB, PGlite, or in-memory SQLite is an integration tool, however fast it runs.

## Coverage policy

- **Measure and publish always.** Report-only is the floor, because zero measurement leaves thin
  spots invisible. Publish where a human sees it, such as a sticky PR comment.
- **Gate with an increase-only ratchet** on server and business-logic packages once the repo
  stabilizes. On a greenfield backend, gate from day one, where the ratchet is free. Commit
  floors that only rise. In vitest, use `coverage.thresholds` with `autoUpdate: true`.
- Never set a blanket fixed percentage.
- Never gate a UI package on coverage.

## UI components

Components with logic (state, branches, hooks) get co-located behaviour tests. Purely
presentational markup is exempt, because mandated markup tests are the low-value tests the
ratchet exists to avoid.

## Per-artifact minimum shapes

Each repo documents a minimum test shape per artifact type in its AGENTS.md, so the shape is in
context at write time. Example list: "every API procedure: happy path plus error; every schema:
parse both ways; every component with logic: a behaviour test."

- The repo sets the list contents. The finding is a missing list.
- Use no snapshots for structured data, because snapshot updates get approved without
  review.
- Pair a mechanically checkable shape with a custom lint rule (`tier-static.md`).

## Runner

The doctrine is runner-neutral. Enforce the conventions that transcend the runner: imported
globals, no ambient types, junit output. Recommend vitest for new TypeScript. Recommend jest
where the ecosystem forces it (jest-expo, Nest).

## Opt-in instruments

- **Mutation testing** is the only instrument that proves tests fail when behaviour changes.
  Recommend it narrowly, on money-path packages, as a scheduled job. Never make it a PR gate.
- **Property-based testing** fits invariant-heavy code only: parsers, codecs, money math.

## Brownfield ramp

1. Measure coverage.
2. Publish it.
3. Ratchet the packages where correctness is the product.

Pair the ramp with characterization tests before refactors (`rubric.md` Part 5). Never answer
low coverage with a blanket threshold.
