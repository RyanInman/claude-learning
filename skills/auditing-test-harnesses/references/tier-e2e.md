# E2E tier - audit lens

Weight: 20%. E2E means driving the real user surface, a browser or a simulator, against a
running system. Reclassify any backend black-box suite labelled E2E as a misfiled system-tier
suite. Report it under the integration tier.

The golden state for this tier lives in one place: the `scaffolding-e2e-tests` skill. Invoke it
with the argument `evaluation-only`. It runs its discover and plan phases, then stops before
implementation. Its plan is this tier's golden-state evidence. Cite the skill. Restate its content nowhere,
because two copies drift apart.

## What to check

The golden state of each item lives in the scaffold skill.

- **Lexicon.** Does anything called E2E never drive a UI?
- **Invariants.**
  - Flow-per-scenario, with shared subflows.
  - Stable-ID selectors.
  - Event-driven waits.
  - Module and `smoke` tags.
  - Documented suite / one / tag scripts.
  - A fresh identity per flow, minted with `randomUUID()`.
- **Retries.** Are retries pinned to 0? Does every flake fix carry a root-cause comment?
- **Backend.** Is it a real local stack? If it is a sandbox, does a dependency that cannot run
  locally and deterministically justify it? Does per-scenario state reset exist either way?
- **Isolation ladder.** Is each rung adopted only where its trigger exists: shared mutable
  state, parallelism, or deterministic eventual consistency?
- **Spec format.** Plain specs, or Gherkin with a real justification: a non-engineer readership
  or a permutation-heavy domain?
- **Cadence.** Per-PR smoke, or a scheduled full suite with boot-and-poke as the named
  compensating control? Is cadence flagged as an owner decision? Is every suite manually
  runnable?
- **Scenario quality.** Judge by the scaffold skill's scenario-design reference: the
  survives-a-rewrite rule and the observable-boundary lists.

## Remediation

- Brownfield: recommend a smoke-tagged, PR-gateable slice before breadth.
- Greenfield and harness construction: route to `scaffolding-e2e-tests` as the action.
