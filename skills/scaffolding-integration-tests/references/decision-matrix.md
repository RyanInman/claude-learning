# Integration harness decision matrix

Use this file in Phase 2. Pick one rung on the DB ladder and one row from each other table.
Record every choice in the Integration Harness Plan.

## Contents

- [Database isolation ladder](#database-isolation-ladder)
- [Auth tiers](#auth-tiers)
- [External dependencies](#external-dependencies)
- [The live tier](#the-live-tier)
- [Async work](#async-work)
- [Test tier and the system tier](#test-tier-and-the-system-tier)
- [Endpoint coverage](#endpoint-coverage)
- [CI checklist](#ci-checklist)

## Database isolation ladder

One ladder serves CI and local. Rungs 2 and 3 unify both behind one provisioning code path.

| Rung | Pattern | Mechanism |
| --- | --- | --- |
| 0 | Shared DB with scoped cleanup. Brownfield fallback only. | A dedicated integration server; scope rows by prefix, `sub`, or tenant; delete in FK order; sweep stale rows at run start. |
| 1 | Fresh state per run. "The cliff": the floor for any suite that gates. | globalSetup schema-drop or migrate-reset; a Neon branch or a service container in CI. |
| 2 | The suite provisions its own DB server. | Testcontainers (random port, readiness wait) when the deps are a DB. Compose plus a preflight check for multi-service or emulator stacks, because a test library must not own five processes. |
| 3 | Template-clone DB per spec file. Postgres only. | `CREATE DATABASE … TEMPLATE` in a custom test environment (`examples.md` Example K). Contamination becomes structurally impossible. |

### Choosing a rung

- **Greenfield:** stack rungs 2 and 3 from commit one. Flag the shape as trial-gated in the plan,
  because no repo practices it yet.
- **Brownfield:** climb 1 → 2 → 3 in value order. Stop when the marginal value runs out.
- **Jump to rung 3** only when all preconditions hold:
  - a Postgres engine,
  - an injectable per-file `DATABASE_URL` with no import-time config singletons,
  - no cross-file test coupling,
  - seeds split into a template baseline and per-test fixtures.
- **Rung 0** is never for a new harness, because a shared DB leaks state between runs. State the move-up path whenever the plan keeps it.
- **No DB in PR CI** is not a rung. Record it as a documented gap.
- Never target production or a prod copy.
- Never substitute transaction-rollback-per-test for a rung. The app pool and the test
  transaction see different worlds, and commit-time behaviour becomes untestable.

### Inspectability

- Drop at next start, never at run end.
- Keep every local spec DB connectable (for example, in DBeaver) in its final state. Print the
  connection coordinates.
- Reuse containers locally. Auto-reap in CI only.

### Parallelism

- Default to serial execution, which is always safe.
- Parallelise only after every stateful dependency (emulators, Redis, filesystem) is per-worker
  and the connection budget is sized: per-file pools × workers against `max_connections`.
- Never run parallel workers on one shared schema.
- Keep the revert to serial at one config line.

### SQL Server

- Reach rung 1 with a `mcr.microsoft.com/mssql/server` service container, Azure SQL Edge,
  Testcontainers, or an ephemeral Azure SQL DB.
- When cost or startup is prohibitive, fall back to rung 0 on a dedicated instance. Put the
  move-up path in the plan.
- Rung 3 does not apply.

### Always

- Run an explicit `migrate deploy` before seeding whenever schema matters.
- Use in-memory SQLite only when it is prod-compatible, and confirm with the user first.

## Auth tiers

Pick the tier by the weight of the auth system, not by habit. Bypassing light auth discards
free fidelity. Running heavy auth for real makes every test pay an external round-trip.

| Tier | When | Mechanism |
| --- | --- | --- |
| Real (preferred when light) | Self-contained auth: DB-backed sessions, local email/password, no external IdP (Better Auth, Lucia, custom sessions) | Drive the real sign-up and sign-in through the app. Capture the issued session token or cookie. Send it on every request. Use no bypass flag. |
| Mint plus gated verify (when heavy) | An external IdP round-trip (OAuth/OIDC, Auth0, Cognito, Okta) | Mint a JWT in-test. Gate only signature or IdP verification with `AUTH_DISABLE_JWT_VERIFICATION` in test and CI. Keep `authorizeFromClaims` shared with prod. |
| Test IdP tenant | A real OAuth round-trip is needed, but the token shape is not controllable | A dedicated Auth0 or Cognito dev tenant or realm. |
| Defer | Auth is not yet testable | Document the gap. Defer authenticated scenarios. |

```text
Light auth:  real sign-in → real session cookie/token → real context extraction (no bypass)
Heavy auth:  verifyBearerToken(token)
               → decode or verify (gated in test)
               → authorizeFromClaims(payload)   // always shared with prod
```

Checklist:

- [ ] Real flow when cheap.
- [ ] If bypassing: production refuses `AUTH_DISABLE_JWT_VERIFICATION=true` at startup.
- [ ] If bypassing: the test secret differs from the prod secret.
- [ ] Cleanup keys on a stable identity (real `user.id`, `sub`, or an email prefix), never on
      token shape.
- [ ] Any mirrored authz (in-memory permission map, dev verifier) has a drift check against the
      real catalog: a spec that diffs the two, or generation from source.

## External dependencies

Pick the most faithful option that costs nothing and has no external side effect. Order of
preference: emulator → live (gated) → stub. An integration test that stubs the thing under test
is barely an integration test.

```text
Your code path (handlers, services, DB, authz after decode)? → REAL, always
Infrastructure you control (DB, Redis)?                      → REAL, container or emulator
Third party you do not control?
  Official emulator or runnable local server?  → EMULATOR (local and CI)
  Else, costs money or has a side effect?      → LIVE, gated (skipped offline and in CI)
  Else (no cost, but cannot run offline or deterministically) → STUB through config or DI; document the gap
Worker not running in the test?                              → SEED downstream state
```

| Dependency | Preferred (emulator or real) | Live (gated, local-first) | Last resort (stub) |
| --- | --- | --- | --- |
| Your HTTP API | In-process real handlers | - | - |
| Relational DB | Ephemeral DB or container | - | - |
| Queue (Pub/Sub, SQS) | Emulator in CI and local | - | Stub publisher when no emulator exists |
| Firestore | Emulator in CI and local | - | Stub client when no emulator exists |
| Email / SMS | Emulator (Mailpit, smtp4dev) | Real send, gated | Stub transport |
| Payments | Provider mock or CLI (Stripe mock) | Real sandbox call, gated | Deterministic stub |
| LLM, transcription, paid AI API | Usually no emulator | Live gated: a real model call behind `it.runIf(isLive)` | Record/replay or a stub client |
| Third-party API you do not control | Official emulator or local server, if one exists | Live gated, if it costs money or mutates remote state | Interface stub, documented |
| Background worker | In-process trigger, or seed downstream tables | - | Sidecar (heavy) |
| Rate limiting | Disabled in the test env | - | - |

Rules:

- Keep your own code path real: handlers, services, DB, and authorization after decode.
- Never mock your own HTTP handlers. Cover that logic with unit tests instead.
- To stub a dep, inject the stub through config or DI. When a worker does not run, seed
  downstream tables. Document each gap with a `describe.skip` note.
- Where a dep has both an emulator and a live mode, use the emulator for the default tier. Keep
  a thin live smoke for end-to-end confidence.

## The live tier

Every external seam that costs money or has an external side effect gets live tests,
co-located with the integration suite. Run them for real, locally, behind a gate. A stub alone
discards the fidelity you want.

- **Separate script:** `test:integration:live` beside the offline `test:integration`.
- **Gate:** `it.runIf(isLive)`, where `isLive` requires a documented env flag and the
  credential together. Per-provider flags are fine (`LIVE_OPENAI=1`).
- **Skip, never fail,** when the gate is absent, so offline CI stays green.
- **Tolerant assertions:** substrings, counts, shape. Never exact strings, because real external
  output is non-deterministic.
- **Timeouts:** scope a longer `{ timeout }` to the live cases, not to the global config.
- **Off the PR gate:** live runs are local-first and on demand. A scheduled live run is an owner
  budget decision.
- **Pairing rule:** each live seam also has a default-suite substitute (emulator, recorded
  fixture, or stub at the owned wrapper).
- **Discoverable:** document the flags and commands in the AGENTS.md routing table.
- **Quality measurement:** measure output quality of the same dep in a sibling `*.eval.ts`
  harness excluded from the default test command. Keep quality scores out of the pass-or-fail result.

## Async work

Fire-and-forget endpoints return before the work completes. Pick by whether the worker runs in
the test.

| Worker in the test? | Approach |
| --- | --- |
| Does not run (suppressed) | Seed downstream tables (materializer pattern). |
| Runs (real or live pipeline) | Poll the observable read model to a terminal state with `waitFor({ read, done })` (`patterns.md`). |

Polling rules:

- Poll the client-facing query, never internal worker state.
- Include success and failure in the terminal predicate, so a failed job ends the poll at once.
- Make the timeout and interval configurable. Raise the timeout for live tiers.
- Never sleep a fixed interval before an assert, because a fixed sleep is too short on slow
  runs and wasted time on fast ones.

## Test tier and the system tier

| Signal | Tier |
| --- | --- |
| REST, tRPC, or GraphQL contract | HTTP integration, in-process (default) |
| Service logic only | Service integration (DI resolve) |
| Real infra between components: queues, outbox or relay, workflow engines, SSE | System tier: booted stack with a test-physics compose override |
| Browser or DOM | Out of scope: `scaffolding-e2e-tests` |
| CLI | Spawn the process; assert on stdout and exit code |

The system tier replaces the old "backend E2E" concept. Add it only when Phase 1 detects its triggers. The test-physics compose override collapses timers and captures side
effects, so durable lifecycles run in seconds.

## Endpoint coverage

Recommend an endpoint-coverage gate on API servers: at least one spec hits every served route.

- Take the denominator from the OpenAPI spec or the router table.
- Keep exceptions in an allowlist, each with a reason.
- Treat the gate as a breadth instrument, not a mandate. It resists line-coverage gaming and is
  the best brownfield on-ramp: breadth first, then depth follows change.
- Schedule the gate after the DB-ladder increment.

## CI checklist

Pipeline:

- [ ] The same test command as local; only env vars and provision steps differ.
- [ ] The DB strategy matches the chosen rung.
- [ ] Migrate and seed are explicit steps.
- [ ] Teardown and auto-reap run in CI only. Local containers are reused.
- [ ] `CI=true` is set for conditional skips.
- [ ] No prod secrets on the gated JWT path.
- [ ] Rung 0 scoping limits, or any no-CI-DB gap, are documented.
- [ ] API servers: the endpoint-coverage gate, with an allowlist-with-reason.

Cadence, triggers, and reporting hold on any CI platform. Adapt the syntax, never the
principles.

- [ ] The fast suite gates change: it runs on every pull or merge request to a protected branch
      and on push to it.
- [ ] Slow or expensive suites (heavy integration, the live tier) run on a schedule, usually
      nightly.
- [ ] Every suite has a manual or on-demand trigger. A suite a human cannot run on demand
      leaves the harness incomplete.
- [ ] Every run publishes pass/fail/skip, plus coverage where supported, on failure as well as
      success.
- [ ] Change-gated triggers cancel superseded in-flight runs with a concurrency group keyed by
      ref.
- [ ] Per-run steps stay constant across cadences: provision, build, migrate deploy, seed, run
      the suite, publish results, teardown.
