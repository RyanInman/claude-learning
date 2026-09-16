---
name: scaffolding-integration-tests
description: >-
  Designs and builds API/service integration test harnesses with a real database, real
  handlers, and real authorization: discovers the stack, writes an Integration Harness Plan
  with per-area trade-offs and blocking questions, then implements it. Covers the four-rung DB
  isolation ladder, real-versus-minted test auth, seeds, factories and cleanup, emulator →
  live-gated → stub choices for external deps, async polling, the booted-stack system tier,
  and CI cadence. Use whenever the user asks to set up, bootstrap, scaffold, fix, or speed up
  integration tests, API tests, backend tests, "e2e" tests that only hit HTTP, Testcontainers,
  a test database, test JWTs, or CI for a backend test suite - even if they only say "our
  backend tests are flaky" or "add tests that hit the real DB". Also runs in evaluation-only
  mode for auditing-test-harnesses. Do NOT use for browser or mobile UI tests (use
  scaffolding-e2e-tests), for unit tests alone, or to score a whole harness (use
  auditing-test-harnesses).
---

# Scaffolding integration tests

## Guiding principle

Maximize fidelity. Bypass the real thing only when it is expensive or external. This rule
decides every choice in the skill:

- **External deps:** emulator (default) → live, gated (no emulator and a real cost) → stub
  (last resort).
- **Auth:** real flow when light → mint plus gated verify when heavy (external IdP).
- **Async work:** poll the real read model when the worker runs → seed downstream only when the
  worker is suppressed.

A bypass is a cost or dependency decision, never a habit.

## Scope

- **In scope:** API and service integration tests with a real database, real handlers, and real
  authorization logic. Stub or emulate only infrastructure you do not control.
- **Out of scope:** browser and mobile UI tests. Route them to `scaffolding-e2e-tests`.

Repos often name these suites `test:e2e` or `*.e2e-spec.ts`. Judge a suite by its architecture,
not its script name. A suite that talks HTTP with no UI in the loop belongs here.

## Reference files

- `references/decision-matrix.md`: the DB ladder, auth tiers, external deps, the live tier,
  async work, the system tier, endpoint coverage, and the CI checklist. Read it before Phase 2.
- `references/patterns.md`: code for env setup, auth helpers, `waitFor`, the live gate, and the
  CI workflow. Read it before Phase 3.
- `references/examples.md`: stack-specific harnesses (NestJS, tRPC, Express, Next.js, SQL
  Server, Better Auth, template-clone rung 3). Read the matching or closest example before
  writing harness code.

Open the reference files at the named phases. The summaries in this file omit the detail that
the plan and the code need.

## Step 0: Before starting

1. **Mode.** Was the argument `evaluation-only`? If so, run Phases 1 and 2 without asking the
   user anything. Record every open question in the plan's Blocking questions table. Return
   the plan to the caller as text only, and stop. Write no code and no files, because an audit
   is running inside a sub-agent that cannot wait for answers.
2. **Target.** Which repo or package gets the harness?
3. **Production data.** Does any env file or config point tests at production or a prod copy?
   If so, stop and ask. Tests never target production. In evaluation-only mode, record it as
   blocking question 1 and plan no DB tier against it.

Mine the conversation and the repo for the answers first. Ask only for what is missing. When
all three are known, proceed without asking.

## Phase 1: Discover

Scaffold no code until Phases 1 and 2 are done and the blocking questions are resolved.

| Question | Where to look |
| --- | --- |
| Framework and how HTTP is served | `package.json`, `main.ts`, the app entry |
| Existing tests | `**/*.spec.ts`, `**/test/`, CI workflows |
| Database and ORM | Prisma or Drizzle schema, `DATABASE_URL`, migrations |
| Auth model | JWT or session; which IdP; guards and middleware |
| External deps | queues, object storage, email, payment gateways, search, LLM and AI APIs |
| Per external dep | emulator availability; cost; side effects (sends, charges, remote mutation) |
| CI platform and constraints | CI config; Docker availability; secrets; scheduled and manual triggers; results and coverage reporting surface |
| Background and async work | workers, cron, materializers, webhooks. Queues, outbox, and SSE are system-tier triggers. |

## Phase 2: Assess and plan

Read `references/decision-matrix.md`. For each problem area, pick a tier from the matrix or
raise a blocking question. Then write the Integration Harness Plan.

Stop and ask the user when:

- CI cannot reasonably provision an isolated DB (heavy SQL Server, no Docker, no branching API).
- Auth is not JWT-shaped and test minting needs design input.
- Tests would hit production or prod-copy data.
- A dep has no emulator and a real call costs money or has a side effect. Confirm live-gated
  tier or stub.
- More than one tier is viable and the trade-off materially changes cost, flakiness, or
  coverage.
- You cannot tell whether the real auth flow is cheap enough.

Present options plus a recommendation. Never silently pick the ideal tier when it is expensive
or uncertain.

### Integration Harness Plan template

Write the plan in chat, or at `.artifacts/plans/YYYY-MM-DD-integration-harness-<project>.md`,
before any code. Use this template, because the audit skill and later increments read these
exact sections.

```markdown
# Integration Harness Plan - <project>

## Summary
<One paragraph: the recommended approach and why it fits this repo.>

## Observable test tier
- Tier: HTTP integration, in-process (default) | service-only | system tier (booted stack; trigger: <queue/outbox/SSE>)
- Entrypoint: `<pnpm test:integration or the existing convention>`

## Per-area decisions
| Area | Choice (tier) | Rationale | Risk |
| --- | --- | --- | --- |
| DB - local | <rung N, mechanism> | | |
| DB - CI | <rung N, mechanism> | | |
| Auth | <real / mint + gated verify / test tenant / defer> | | |
| <Queue X> | <emulator / live gated / stub> | | |
| <Paid API Y> | <live gated, `it.runIf(isLive)`; substitute: <fixture/stub>> | | |

## Blocking questions
| # | Question | Options | Recommendation |
| --- | --- | --- | --- |
<omit this section when there are none>

## Next step (increments, highest-value structural move first)
1. <usually the DB-isolation cliff, rung 0 → 1>
2. ...

## CI cadence and reporting
- Triggers: fast suite on PR and push to <branch>; slow and live suites on <schedule>; manual trigger on every suite.
- Per run: provision → build → migrate deploy → seed → test → publish results → teardown (CI only).
- Reporting: pass/fail/skip summary plus coverage, on success and failure.
- Breadth (API servers): endpoint-coverage gate, every served route hit by at least one spec.

## Out of scope / deferred
<What v1 does not do.>
```

## Phase 3: Gate on the delta, then implement

Measure the delta between the repo and the plan, then route the work:

- **Non-trivial delta** (several structural moves, such as a seed to design, an auth change
  across services, or a CI rewrite): sequence the work into increments, highest-value
  structural move first. Hand the first increment to the `brainstorming` skill for a formal
  plan with file-path tasks, acceptance criteria, and per-tier test cases. Let `brainstorming`
  own that spec, and restate it nowhere else. Track progress against it. Hold later increments
  until their turn.
- **Trivial delta** (one or two moves, such as adding Testcontainers and pinning retries to 0):
  skip `brainstorming`. Implement from a checklist in the plan, and track progress against it.

Read `references/patterns.md` and the matching example in `references/examples.md`. Then
implement in this order:

1. The env setup file, pinning test vars before `.env` loads.
2. The test auth helper: a real sign-in helper, or a JWT minter for the mint plus gated verify tier.
3. The database path from the plan: provision, `migrate deploy`, seed.
4. `TestClient`, factories, and cleanup at next-run start.
5. External deps from the plan: emulator, live gate with its substitute, or stub.
6. The CI workflow: the same command as local, with triggers and reporting per the plan.
7. One proof scenario, green locally and then in CI.

## Problems every harness must solve

| # | Problem | Solved when |
| --- | --- | --- |
| 1 | Bootstrap | The app runs in-process, or against a documented black-box URL, with real handlers. |
| 2 | Auth | Test and prod use the same authorization logic, under either auth tier. |
| 3 | Database | Tests run on a real DB. The plan names the ladder rung. |
| 4 | Data | Seeds hold reference data for stable lookups. Factories create per-test rows. |
| 5 | External deps | The plan assigns each dep the most faithful tier it can afford. |
| 6 | Async gaps | Worker suppressed → seed downstream. Worker runs → poll the read model to a terminal state. |
| 7 | Cleanup | Cleanup runs at next-run start, so post-run state stays inspectable. Rung 0 uses scoped deletes in FK order. |
| 8 | Local/CI parity | One command; CI automates provision and seed. |
| 9 | Noise | Logs are silent; rate limits are off in the test env. |
| 10 | Prerequisites | A missing prerequisite fails fast and names the fix ("run db:seed", "start emulator"). |
| 11 | CI cadence and visibility | The fast suite gates PRs; slow and live suites run on a schedule; every suite runs on demand; every run publishes pass/fail and coverage. |

## Example

A blocking-question row for a repo that calls OpenAI from its summary endpoint:

```markdown
| # | Question | Options | Recommendation |
| --- | --- | --- | --- |
| 1 | `summarize()` calls OpenAI with no emulator; each call costs tokens. How should the default suite cover it? | A: live gated only / B: live gated + recorded-fixture substitute / C: stub only | B, because the seam stays covered offline and the live run keeps real-model confidence |
```

## Gotchas

- Transaction-rollback-per-test is not a ladder rung. The app pool and the test transaction see
  different worlds, so commit-time behaviour becomes untestable.
- Drop DB state at next start, never at run end. A developer debugging a red test needs the
  final state, so keep local DBs connectable and print their coordinates.
- A live test must skip, never fail, when its flag or credential is absent. A failing live test
  turns offline CI red with no code change.
- Every live seam needs a default-suite substitute (emulator, recorded fixture, or stub at the
  owned wrapper). Without one, the seam goes untested whenever live is off.
- Never bypass light auth. Real sign-in costs nothing and exercises session
  issuance and context extraction.
- If the plan uses `AUTH_DISABLE_JWT_VERIFICATION`, production must refuse to start with it set.
  Keep the test secret different from the prod secret.
- A mirrored authz map (in-memory permissions, a dev verifier) needs a drift check against the
  real catalog: a spec that diffs the two, or generation from source.
- Never run parallel workers on one shared schema. Serial is the safe default. Parallelise only
  after every stateful dep is per-worker and the connection budget is sized.
- Never hardcode seed UUIDs in tests, because a reseed can change them. Look up reference data by a stable name or key.
- Provision every emulator in the CI workflow, because CI runners start with none.
- Never gate every PR on a slow or live suite. Put it on a schedule, and flag a scheduled live
  run as an owner budget decision.
- Never sleep a fixed interval before asserting on async work. Poll a terminal predicate that
  includes the failure state.

## After the harness works

1. Record prerequisites (`db:seed`, emulators, live flags, commands) in README or AGENTS.md.
2. Offer to capture the repo's testing conventions as a project skill with `skillit:create`.
3. Route UI scenario breadth to `scaffolding-e2e-tests`.
