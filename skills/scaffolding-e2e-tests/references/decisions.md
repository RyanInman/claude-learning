# E2E harness decisions

Use this file in Phase 2. Record each choice in the Per-area decisions table of the plan.

## Contents

- [Backend and data strategy](#backend-and-data-strategy)
- [Conditional isolation ladder](#conditional-isolation-ladder)
- [Spec format](#spec-format)
- [CI cadence](#ci-cadence)
- [Tactical defaults](#tactical-defaults)

## Backend and data strategy

- **Default:** a real local stack. The real API and the real DB boot locally.
- **Sandbox or simulated backend:** build one only when a dependency cannot run locally and
  deterministically, such as a payment network or third-party SaaS. Never build one for
  convenience. A sandbox is a real build, so confirm scope with the user.
- **Per-scenario state reset** is required under either strategy:
  - by fresh identity, when identity fences all state;
  - by restore, when it does not.

## Conditional isolation ladder

Climb a rung only when its trigger exists. Each rung adds machinery, and unused machinery is
cost with no benefit.

| Rung | Mechanism | Trigger |
| --- | --- | --- |
| 0 (default) | Fresh identity per flow; serial suite | Identity fences all state. |
| 1 | Per-scenario restore through one sub-second control-plane call, such as a template-cloned DB | Shared mutable state that identity cannot fence, or a reset cost that makes the suite too slow to run before every commit. |
| 2 | Per-worker sessions: one isolated DB per worker, with a session id on every request through one `extraHTTPHeaders` override. The backend echoes the resolved DB name in a response header (for example `x-test-db`). | The suite parallelises. Web only, because a simulator is inherently serial. |
| 2+ | Isolation tripwire: assert on every response that the DB header names the worker's expected DB | Isolation rests on routing machinery. Prove the invariant; never assume it. |
| 3 | Stepped-bus mode: pause the pipeline, assert the pending UI, advance a named stage, assert convergence | Deterministic eventual-consistency testing, only where a sandbox with a control API already exists. |

Never build a sandbox to reach rung 3. Rung 3 piggybacks on a sandbox that a dependency already
forced into existence.

## Spec format

- **Default:** plain flow-per-scenario specs (Playwright specs, Maestro YAML).
- **Gherkin:** adopt it only when non-engineers actually read the feature files, or the domain is
  permutation-heavy state-machine behaviour.
- Do not adopt Gherkin on speculation, because it adds step files with module-level mutable
  state and bookkeeping phrases.

## CI cadence

Flag CI cadence as an owner decision and attach the cost picture, because cadence spends
runner budget. Never
choose it silently.

- **Preferred:** run the `smoke` tag on every PR when runner economics allow.
- **Otherwise:** schedule the full suite nightly or weekly. Name agent boot-and-poke as the
  compensating control: before closing a change that touches a user flow, the agent boots the app and
  exercises that flow.
- Make every suite runnable by hand, whatever the cadence.
- CI runs the same command as local.

## Tactical defaults

### Web (Playwright reference)

- Set `reducedMotion: 'reduce'`, so tests never race exit animations.
- Pre-seed consent and cookie state through `storageState`, instead of clicking banners away in
  each test.
- Bound per-request timeouts under the test timeout, so a hang names the endpoint instead of
  timing out the whole scenario.
- Set `retries: 0`.

### Mobile (Maestro reference)

- Select by `testID`.
- Wait with `extendedWaitUntil`, never sleep.
- Put tags in the flow frontmatter.
- Mint the fresh identity in a shared sign-up subflow.
