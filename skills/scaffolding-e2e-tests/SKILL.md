---
name: scaffolding-e2e-tests
description: >-
  Designs and builds end-to-end UI test harnesses that drive the real user surface - browser
  suites (Playwright reference) and mobile suites (Maestro reference): discovers surfaces and
  flows, drafts the observable boundary, writes an E2E Harness Plan with a scenario index and
  blocking questions, then implements it. Covers flow-per-scenario design, stable-ID selectors,
  event-driven waits, fresh identity per flow, per-scenario state reset, the conditional
  isolation ladder, smoke tagging, and CI cadence. Use whenever the user asks to set up,
  bootstrap, scaffold, or fix e2e tests, browser tests, UI tests, Playwright, Cypress, Maestro,
  mobile UI tests, smoke tests, or flaky UI tests - even if they only say "test the signup
  flow in a real browser". Also runs in evaluation-only mode for auditing-test-harnesses. Do
  NOT use for suites that only call HTTP with no UI (use scaffolding-integration-tests - that
  is the system tier), or to score a whole harness (use auditing-test-harnesses).
---

# Scaffolding e2e tests

## Guiding principle

E2E means driving the real user surface, a browser or a simulator, against a running system. A
scenario belongs here only if a user could have performed it. A suite that talks HTTP to a
backend with no UI in the loop is the system tier. Route it to `scaffolding-integration-tests`.

The harness invariants below are stack-agnostic. Playwright (web) and Maestro (mobile) are reference
implementations. Any tool that drives the real surface and satisfies the invariants below
qualifies.

## Reference files

- `references/decisions.md`: backend strategy, the conditional isolation ladder, spec format,
  CI cadence, and tactical defaults. Read it before writing the plan.
- `references/scenario-design.md`: the survives-a-rewrite rule, Given/When/Then, negative
  pinning, provider recorders, and async waits. Read it before writing the scenario index.

## Step 0: Before starting

1. **Mode.** Was the argument `evaluation-only`? If so, run Phases 1 and 2 without asking the
   user anything. Record every open question in the plan's Blocking questions table. When
   both surfaces exist, plan both. Check each existing flow against the Harness invariants and
   `references/scenario-design.md`, and list each violation with its file:line in the plan.
   Return the plan to the caller as text only, and stop. Write no code and no files, because an
   audit is running inside a sub-agent that cannot wait for answers.
2. **Surface.** Web, mobile, or both? When both exist, ask which gets the harness first.
3. **Target system.** Does the suite run against a local stack? Never point it at production.

Mine the conversation and the repo for the answers first. Ask only for what is missing. When
all three are known, proceed without asking.

## Phase 1: Discover

Scaffold nothing until Phases 1 and 2 are done and the blocking questions are resolved.

| Question | Where to look |
| --- | --- |
| User surfaces: web, mobile, or both | app dirs, `package.json`, build configs |
| Existing UI tests | `e2e/`, `.maestro/`, Playwright config, CI workflows |
| User flows worth a scenario | routes, screens, navigation, product docs |
| How a user signs up and signs in | auth provider, onboarding screens, invite gates |
| Does the backend run locally and deterministically? | compose files; payment-network and third-party SaaS deps |
| Shared mutable state across scenarios | inventory counts, quotas, rate limits, global counters |
| Eventual consistency visible in the UI | queues, pipelines, workers that feed the UI |
| Consent gates and animations | cookie banners, onboarding modals, motion libraries |
| CI runner economics | platform, macOS or device billing, simulator needs |

Then draft the observable boundary as two lists, before any scenario exists:

1. **Outside (the contract):** what a user or third party observes. Visible UI state, persisted
   effects they can see, provider side effects such as email, push, and payment.
2. **Inside (implementation detail):** internal modules, orchestration mechanics, selectors of
   convenience. Tests never touch this list.

Also note deliberate no-ops worth pinning, such as "we don't send an email on X on purpose."

## Phase 2: Plan

Read `references/decisions.md` and `references/scenario-design.md`. Pick from their decisions,
or raise a blocking question. Then write the E2E Harness Plan.

### Harness invariants

Every suite meets these, whatever the tool:

- One flow file per user scenario, plus shared subflows for common paths (sign-up, login).
- Stable-ID selectors first: `testID`, or role plus test-id. Do not use positional or CSS-of-convenience
  selectors, because they break on a restyle that changes no behaviour.
- Event-driven waits. Do not use sleep or any fixed-duration wait (such as
  `waitForTimeout`),
  because a fixed wait is either too short under load or wasted time.
- A module tag on every flow, plus a `smoke` tag. Add three named
  scripts: suite, one, tag.
- A fresh identity per flow, minted with `randomUUID()`. No shared fixed accounts. Caching an
  authenticated session (Playwright `storageState`) is fine only when a freshly minted identity
  sits behind it.
- Retries pinned to 0 in every config. Any flake fix carries its root-cause story as a comment
  on that line, because a flake is a bug with a measurement, never a retry knob.

### Stop and ask when

- The backend cannot run locally and deterministically, because a sandbox is a real build.
- Runner economics are unclear (macOS billing, device farms), because cadence is a money call.
- The app cannot mint fresh identities (invite-only auth, an external IdP with no test
  tenant), because rung 0 depends on them.
- Shared mutable state exists but no control plane does, because rung 1 needs backend work.
- Both web and mobile exist, and nobody has said which comes first.

Present options plus a recommendation.

### E2E Harness Plan template

Write the plan in chat, or at `.artifacts/plans/YYYY-MM-DD-e2e-harness-<project>.md`, before any
code. Use this template, because the audit skill and later work read these exact sections.

```markdown
# E2E Harness Plan - <project>

## Summary
<One paragraph: surface(s), tool, backend strategy, cadence recommendation.>

## Observable boundary
- Outside (tests assert on): ...
- Inside (tests never touch): ...
- Deliberate no-ops to pin: ...

## Per-area decisions
| Area | Choice | Rationale | Risk |
| --- | --- | --- | --- |
| Backend | real local stack / sandbox (justified by <dep>) | | |
| Isolation | rung <N> (trigger: <trigger>) | | |
| Spec format | plain specs / Gherkin (justified by <reason>) | | |
| CI cadence | per-PR smoke / scheduled full suite + boot-and-poke | <cost picture> | **owner decision** |

## Scenario index
| # | Module | Given / When / Then (one line) | Tags |
| --- | --- | --- | --- |

## Blocking questions
| # | Question | Options | Recommendation |
| --- | --- | --- | --- |
<omit this section when there are none>

## Implementation checklist
- [ ] Harness config with tactical defaults and app boot
- [ ] Shared subflows: sign-up (randomUUID identity), login, consent/nav preamble
- [ ] Proof scenario tagged `smoke`, green locally, then in CI
- [ ] Scripts: suite / one / tag
- [ ] Remaining scenarios by module, breadth first
- [ ] CI workflow at the agreed cadence
```

## Phase 3: Implement

Implement only after the user agrees to the plan. When the plan holds more than a proof scenario plus five flow files, hand it to the `brainstorming` skill first for a formal
build order.

1. Write the harness config with the tactical defaults from `references/decisions.md`. Boot the
   app through a `webServer` entry or a local stack script.
2. Write the shared subflows: sign-up minting a `randomUUID()` identity, login, and the consent
   or navigation preamble.
3. Land one proof scenario end to end, tagged `smoke`. Get it green locally, then in CI.
4. Add the named scripts: suite, one, tag.
5. Add the remaining scenarios by module, breadth first.
6. Add the CI workflow at the agreed cadence, running the same command as local.

## Example

Scenario index rows for a web shop with email receipts:

```markdown
| # | Module | Given / When / Then (one line) | Tags |
| --- | --- | --- | --- |
| 1 | checkout | Given a fresh user with one cart item / When they pay with the test card / Then the order page shows "Paid" and exactly one receipt email arrives | checkout, smoke |
| 2 | checkout | Given a fresh user / When payment is declined / Then the cart keeps its item and no receipt email is sent | checkout |
```

## Gotchas

- Never mint an identity from `Date.now()`. Two workers that start in the same millisecond mint the same
  identity.
- Never label a backend black-box suite E2E. It is the system tier of
  `scaffolding-integration-tests`.
- Never raise retries above 0 to bury a flake. Root-cause it and comment the fix.
- Never build a sandbox when the real stack runs locally and deterministically. Never build one
  just to reach isolation rung 3.
- Never adopt Gherkin without a non-engineer readership or a permutation-heavy domain,
  because its step files add indirection that no one reads.
- Never choose CI cadence silently. Flag it as an owner decision with the cost picture.
- Never run parallel workers without per-worker isolation and a tripwire that proves it,
  because workers that share a DB corrupt each other's state silently.
- Never ship a suite without a `smoke` subset and a way to run one flow or one tag, because
  without them no PR gate or single-flow debug run is possible.
- An assertion like "and the FooService was called" is a stop sign. Assert the resulting
  observable, or move the test down a tier.

## After the harness works

1. Record prerequisites (stack up, simulator, seed) in README or AGENTS.md.
2. Offer to capture the repo's conventions (tags, scripts, subflows) as a project skill with
   `skillit:create`.
3. Keep the scenario index in the plan current as flows are added, because it is the suite's
   map.
