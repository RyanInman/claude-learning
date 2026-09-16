# Integration Test Harness — Examples

Stack-specific applications of the patterns in `patterns.md` and `decision-matrix.md`. Adapt names and paths — the problems and solutions transfer. Browser/full-stack E2E is out of scope. Where an example conflicts with `decision-matrix.md`, the matrix wins.

## Contents

- [Example A: NestJS + REST + Postgres + Prisma](#example-a-nestjs--rest--postgres--prisma)
- [Example B: tRPC + Neon + Prisma (same patterns, different transport)](#example-b-trpc--neon--prisma-same-patterns-different-transport)
- [Example C: Express + raw SQL (no Prisma)](#example-c-express--raw-sql-no-prisma)
- [Example D: Next.js API routes + Postgres](#example-d-nextjs-api-routes--postgres)
- [Example E: Service integration without HTTP (ingestion pattern)](#example-e-service-integration-without-http-ingestion-pattern)
- [Example F: Pub/Sub emulator (local and CI), direct injection as a documented gap](#example-f-pubsub-emulator-local-and-ci-direct-injection-as-a-documented-gap)
- [Example G: CI with Docker Postgres (no Neon)](#example-g-ci-with-docker-postgres-no-neon)
- [Example H: SQL Server - rung 0 plan excerpt (shared DB, brownfield fallback)](#example-h-sql-server---rung-0-plan-excerpt-shared-db-brownfield-fallback)
- [Example I: Live tier for deps with no emulator (LLM / OCR / paid AI APIs)](#example-i-live-tier-for-deps-with-no-emulator-llm--ocr--paid-ai-apis)
- [Example J: Real (light) auth + async polling — Better Auth + tRPC](#example-j-real-light-auth--async-polling--better-auth--trpc)
- [Example K: Template-clone per spec file (rung 3) - custom Jest environment](#example-k-template-clone-per-spec-file-rung-3---custom-jest-environment)
- [Mapping your stack (Phase 2)](#mapping-your-stack-phase-2)

---

## Example A: NestJS + REST + Postgres + Prisma

**Stack:** TypeScript, NestJS, REST, Postgres, Prisma, Jest, supertest, Turbo monorepo, Neon (CI).

### File layout

```
apps/api/test/
  setup-env.ts
  jest-e2e.json
  helpers/
    test-client.ts
    cleanup.ts
    order-factory.ts
  orders.e2e-spec.ts

packages/database/prisma/seeders/
  index.ts
  catalog/catalog.data.ts  # "Integration Test Catalog"

.github/workflows/e2e-tests.yml
```

### Env setup (pre-pin)

```typescript
// apps/api/test/setup-env.ts
process.env.NODE_ENV = 'test'
process.env.AUTH_DISABLE_JWT_VERIFICATION = 'true'
process.env.JWT_TEST_SECRET = 'integration-test-secret'  // not prod secret
process.env.PAYMENT_GATEWAY_URL = ''  // falsy → stub module
process.env.DISABLE_THROTTLE = 'true'
process.env.LOG_LEVEL = 'silent'

import { config } from 'dotenv'
config({ path: resolve(__dirname, '../.env') })
```

### Test JWT helper

```typescript
// test/helpers/test-jwt.ts
import { sign } from 'jsonwebtoken'

export function createTestJwt(claims: { sub: string; roles?: string[] }) {
  return sign(claims, process.env.JWT_TEST_SECRET!, { algorithm: 'HS256', expiresIn: '1h' })
}
```

### Auth provider (single path; gated verify only)

```typescript
async verifyBearerToken(token: string): Promise<RequestUser> {
  const payload = this.config.get('AUTH_DISABLE_JWT_VERIFICATION') === 'true'
    ? decodeJwtUnsafe(token)                    // parse only — reject malformed
    : await this.verifyWithIdp(token)         // prod: signature / IdP

  return this.authorizeFromClaims(payload)      // DB lookup, roles — always real
}
```

### Test client

```typescript
class TestClient {
  private _suffixes = new Set<string>()

  async registerTestUser(suffix: string) {
    this._suffixes.add(suffix)
    const sub = `test-user-e2e-${suffix}`
    const token = createTestJwt({ sub, roles: ['user'] })
    const res = await request(app).post('/auth/register')
      .set('Authorization', `Bearer ${token}`)
    return { token, userId: res.body.id, sub }
  }

  get registeredSuffixes() { return [...this._suffixes] }
}
```

### Cleanup (FK order)

```typescript
async function cleanupTestUsers(source: string[] | TestClient) {
  const suffixes = Array.isArray(source) ? source : source.registeredSuffixes
  const users = await prisma.user.findMany({
    where: { externalId: { in: suffixes.map(s => `idp|test-user-e2e-${s}`) } }
  })
  const ids = users.map(u => u.id)
  await prisma.order.deleteMany({ where: { userId: { in: ids } } })
  await prisma.user.deleteMany({ where: { id: { in: ids } } })
}
```

### CI (Neon branch)

```yaml
- uses: neondatabase/create-branch-action@v6
  id: branch
  with:
    branch_name: e2e-${{ github.run_id }}
- run: pnpm build && pnpm prisma migrate deploy && pnpm db:seed && pnpm test:e2e
  env:
    DATABASE_URL: ${{ steps.branch.outputs.db_url_pooled }}
    AUTH_DISABLE_JWT_VERIFICATION: "true"
    JWT_TEST_SECRET: ${{ secrets.JWT_TEST_SECRET }}
    CI: "true"
- uses: neondatabase/delete-branch-action@v3
  if: always()
```

### External services

| Service | Mechanism |
|---------|-----------|
| Payment gateway | `PAYMENT_GATEWAY_URL=''` → `PaymentGatewayStub` |
| External IdP | Gated JWT verify; IdP client optional in CI; shared `authorizeFromClaims` |
| Pub/Sub | Emulator locally and in CI (service container); see Example F |
| Materializer worker | Don't run; seed order/shipment rows via factories |

---

## Example B: tRPC + Neon + Prisma (same patterns, different transport)

**Changes from Example A:**

| Concern | Nest+REST | tRPC |
|---------|-----------|------|
| HTTP client | supertest | `appRouter.createCaller({ ctx })` or supertest on `/trpc` |
| Test client | `.get('/products/:id/price')` | `.price({ productId, quantity })` |
| Validation | Nest ValidationPipe | Zod input schemas (same — real) |
| Bootstrap | `Test.createTestingModule` | `createContext` + caller, or Fastify/Express adapter |

Everything else identical: setup-env, test JWT auth, seed by name, cleanup by `sub`, Neon branch CI.

```typescript
// Service-tier alternative — no HTTP
const caller = appRouter.createCaller(await createTestContext({ token: testToken }))
const result = await caller.orders.place({ productId, quantity: 2 })
```

Use HTTP tier when testing middleware; use caller tier when testing business logic only.

---

## Example C: Express + raw SQL (no Prisma)

**Changes:**

| Concern | Prisma | Raw SQL |
|---------|--------|---------|
| Seed | `prisma/seeders/` with upsert | SQL seed file or `db:seed` script |
| Cleanup | `deleteMany` in FK order | `DELETE FROM orders WHERE user_id = ANY(:ids)` |
| Prerequisite check | `findFirst({ where: { sku }})` | `SELECT id FROM products WHERE sku = :sku` |
| CI DB | Same Neon/container options | Same |

Auth bypass, env pre-pin, test client, and CI shape unchanged.

---

## Example D: Next.js API routes + Postgres

**Bootstrap:** use `next-test-api-route-handler` or start Next in test mode and hit routes via fetch/supertest.

```typescript
// test/setup-env.ts — same pre-pin pattern
process.env.NODE_ENV = 'test'
process.env.AUTH_BYPASS = 'true'

// test/helpers/test-client.ts
async function registerTestUser(suffix: string) {
  const res = await fetch(`${baseUrl}/api/auth/register`, {
    headers: { Authorization: `Bearer ${createTestJwt({ sub: `test-user-e2e-${suffix}` })}` }
  })
  return res.json()
}
```

CI: identical workflow — ephemeral DB, seed, `pnpm test:e2e`.

---

## Example E: Service integration without HTTP (ingestion pattern)

When the observable boundary is a service method, not an endpoint:

```typescript
// low-stock-alerts.e2e-spec.ts
beforeAll(async () => {
  const module = await Test.createTestingModule({ imports: [AppModule] })
    .overrideProvider(PubSubPublisherService)
    .useValue({ publish: async () => null, isEnabled: false })
    .compile()

  app = module.createNestApplication()
  await app.init()
  detector = app.get(LowStockDetectorService)
  TEST_IDS = await loadInventoryTestIds()  // lookup seeded products by SKU
})

beforeEach(async () => {
  await cleanupInventoryTestData(TEST_IDS)  // reset mutable stock levels
})

it('raises an alert when stock falls below the threshold', async () => {
  await createTestStockMovement({ productId: TEST_IDS.products.widget, delta: -95 })
  const stats = await detector.detectAll()
  expect(stats.alertsRaised).toBe(1)
})
```

Same seed/cleanup/factory patterns; no TestClient needed unless you also test HTTP ingress separately.

---

## Example F: Pub/Sub emulator (local and CI), direct injection as a documented gap

**Problem:** Full webhook → queue → push → process pipeline needs emulator running.

**Local:** emulator + setup script:
```bash
gcloud beta emulators pubsub start --project=local-dev &
pnpm pubsub:setup-emulator  # creates topics + push subscription
PUBSUB_EMULATOR_HOST=localhost:8085 pnpm test:e2e
```

**CI:** run the same emulator as a service container and the same setup script. This is the default, because an emulator exists.

**Documented gap (only while the CI emulator is not yet provisioned):** test the consumer directly, and record the gap in the plan:
```typescript
// Instead of publishing to queue, POST push envelope to handler
await request(app).post('/webhook/process')
  .set('Authorization', TEST_WEBHOOK_AUTH)
  .send(buildPubSubPushEnvelope(webhookPayload))
```

**Closing the gap:** add the service container to the workflow, run the setup script, remove `SKIP_PUBSUB_TESTS`.

---

## Example G: CI with Docker Postgres (no Neon)

```yaml
jobs:
  e2e:
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: e2e
        ports: ['5432:5432']
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - run: pnpm db:migrate deploy && pnpm db:seed && pnpm test:e2e
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/e2e
          CI: "true"
```

No branch teardown needed — container destroyed with job.

### Triggers & reporting (applies to every CI example above)

The job *steps* differ per DB tier; the *triggers* and *reporting* follow the same four rules everywhere (see `decision-matrix.md` → "CI checklist"). GitHub Actions shown; map to your platform.

```yaml
# Fast suite gates change (rule 1); slow/live suite on a clock (rule 2); always runnable (rule 3).
on:
  pull_request:
  push: { branches: [main] }
  schedule: [{ cron: '0 3 * * *' }]   # nightly home for the slow/live suite
  workflow_dispatch:

# Within a job, publish results + coverage on success AND failure (rule 4):
- run: pnpm test:integration -- --coverage
- if: always()                        # report even when the suite failed
  uses: mikepenz/action-junit-report@v5
  with: { report_paths: '**/test-results/*.xml', check_name: Integration results }
- if: always()
  uses: actions/upload-artifact@v4
  with: { name: coverage, path: coverage/ }
```

For a multi-suite repo, gate the fast suite on `pull_request`/`push` and guard the slow job with `if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'` so heavy/live tests stay off the PR path but remain runnable on demand.

---

## Example H: SQL Server - rung 0 plan excerpt (shared DB, brownfield fallback)

Use when Phase 2 finds ephemeral CI DB too costly; present this in the Integration Harness Plan before coding. Rung 0 is never for new harnesses - kept, or introduced, only when constraints force it.

```markdown
## DB - CI: rung 0 (brownfield fallback)
- Target: `integration-sql.company.internal` / database `app_integration`
- No per-PR database spin-up; migrations run once per deploy or weekly job
- Test data: `ExternalId` prefixed `integ-{suite}-{suffix}-`
- Cleanup: stale sweep at run start + ordered DELETE by prefix (drop-at-next-start
  keeps post-run state inspectable)
- Risk: parallel PR jobs must not share DB - use concurrency group 1 per integration DB
  OR partition by `integ-{GITHUB_RUN_ID}-` prefix

## Blocking question
Run integration tests on every PR (rung 1 container, ~3–5 min overhead)
vs nightly on rung 0 shared DB (faster PR CI, less isolation)?
Recommendation: rung 0 nightly first for bootstrap; move up to rung 1 when the team wants PR gates.
```

---

## Example I: Live tier for deps with no emulator (LLM / OCR / paid AI APIs)

When a dependency has **no official emulator** and a real call costs money or has an external side effect, don't stub it away - that discards the fidelity an integration test exists for. Add a **gated, local-first live tier** alongside the offline suite.

### Gate in setup-env

```typescript
// test/integration/setup-env.ts
export const isLive = process.env.INTEGRATION_LIVE === 'true' && !!process.env.OPENAI_API_KEY
// per-dep gate when a second key is needed:
export const isLiveClassification = isLive && !!process.env.CLASSIFIER_API_KEY
```

### Scripts (offline vs live are separate commands)

```jsonc
// package.json — offline default stays green in CI; live is opt-in, local-first
"test:integration":      "vitest run -c vitest.integration.config.ts",
"test:integration:live": "INTEGRATION_LIVE=true vitest run -c vitest.integration.config.ts"
```

### Test shape — gated, tolerant, longer timeout

```typescript
import { isLive } from './setup-env'

// runIf → SKIPPED (not failed) when the flag/credential is absent: offline CI passes
it.runIf(isLive)('summarises a real document end-to-end', async () => {
  const { documentId } = await client.document.create.mutate({ folderId, sourceUrl: SAMPLE_PDF_URL })
  const doc = await waitForSummary({ client, documentId })           // poll async job to terminal state

  expect(doc.summaryJob?.status).toBe('COMPLETED')
  // non-deterministic output → assert substance + a distinctive phrase, never an exact string
  expect(doc.summaryJob?.summary).toMatch(/invoice/i)
}, { timeout: 180_000 })                                              // scoped, not the global config
```

### Quality sibling (optional): an eval harness, not a pass/fail test

For *measuring* summary quality of the same live dep, keep an Evalite `*.eval.ts` suite — **excluded from `pnpm test`** so unit runs never call the real model. It scores against a labelled fixture set rather than asserting; a score floor can gate later.

| Concern | Mechanism |
|---------|-----------|
| Gate | `it.runIf(isLive)` — flag + required key both present |
| Failure mode when ungated | **Skipped**, never failed; offline/CI stays green |
| Assertions | Substrings, counts, shape — tolerant of model/version drift |
| Timeout | Per-test `{ timeout: 180_000 }`, not global |
| CI | Offline `test:integration` only; live runs on demand locally (scheduled live runs are an owner budget decision) |
| Default-suite substitute | Emulator / recorded fixture / stub at the owned wrapper - the seam stays covered when live is off |
| Quality measurement | Separate `*.eval.ts`, excluded from `pnpm test` |

---

## Example J: Real (light) auth + async polling — Better Auth + tRPC

When auth is lightweight (DB-backed sessions, no external IdP), skip the mint/bypass machinery entirely and run the **real** flow - it's cheap and exercises session issuance plus the real context lookup. Pair it with a **poll-to-terminal** helper for fire-and-forget work.

### Real auth — drive sign-up, reuse the issued cookie

```typescript
// test/integration/helpers/auth.ts
const TEST_PASSWORD = 'Integration-Test-P@ss1'

export async function signUpTestUser(app: Hono, suffix: string) {
  const email = `integ-${suffix}@app.test`
  const res = await app.request('/api/auth/sign-up/email', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password: TEST_PASSWORD, name: `Test ${suffix}` }),
  })
  if (!res.ok) throw new Error(`Sign-up failed (${res.status}): ${await res.text()}`)
  const cookies = res.headers.getSetCookie().map((c) => c.split(';')[0]).join('; ')
  return { cookies, user: (await res.json()).user }
}

// test/integration/helpers/test-client.ts — real session cookie on every request
export function createAuthenticatedClient(app: Hono, cookies: string) {
  return createTRPCClient<AppRouter>({
    links: [httpBatchLink({
      url: 'http://localhost/api/trpc',
      transformer: superjson,
      headers: () => ({ cookie: cookies }),
      fetch: (input, init) => app.request(input as string, init as RequestInit),
    })],
  })
}
```

No `AUTH_DISABLE_*` flag exists in this harness — the prod auth path (session issuance, cookie, tRPC `getSession`) runs unmodified. Switch to mint+gated-verify only if the auth system grows an external IdP round-trip.

### Async polling — poll the read model to terminal status

```typescript
// test/integration/helpers/wait-for-summary.ts
export async function waitForSummary(req: {
  client: AuthedClient; documentId: string; timeoutMs?: number; pollIntervalMs?: number
}) {
  const { client, documentId, timeoutMs = 120_000, pollIntervalMs = 2_000 } = req
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    const doc = await client.document.getById.query({ id: documentId })   // client-facing query
    const job = doc.summaryJob
    if (job && (job.status === 'COMPLETED' || job.status === 'FAILED')) return doc  // terminal: success OR failure
    await new Promise((r) => setTimeout(r, pollIntervalMs))
  }
  throw new Error(`Summary did not complete within ${timeoutMs}ms`)
}
```

`waitForClassification` is the same shape on `document.classification.status` — when you have several async stages, prefer the generic `waitFor({ read, done })` from `patterns.md` over copy-pasting per-stage helpers.

---

## Example K: Template-clone per spec file (rung 3) - custom Jest environment

Each spec file gets its own Postgres database, cloned from a migrated template in ~100-200ms -
`CREATE DATABASE … TEMPLATE` is a file-level copy, not a migration re-run. Cleanup is
drop-at-next-start, so after a run every spec DB stays connectable for inspection.

```ts
// test-env/per-file-db-environment.ts - wired via jest `testEnvironment`
import { TestEnvironment } from 'jest-environment-node'
import { Client } from 'pg'

// Migrated + seeded once in globalSetup; never connected to afterwards
// (Postgres refuses TEMPLATE cloning while any session is attached).
const TEMPLATE_DB = 'integration_template'

// apps/api/test/orders.integration-spec.ts → integration__apps__api__test__orders
function deriveDbName(testPath: string): string {
  return (
    'integration__' +
    testPath
      .replace(/\.integration-spec\.ts$/, '')
      .replace(/^.*?((?:apps|packages|tools)\/.*)$/, '$1')
      .replace(/\//g, '__')
      .replace(/[^a-z0-9_]/gi, '_')
      .toLowerCase()
  )
}

export default class PerFileDbEnvironment extends TestEnvironment {
  private readonly dbName: string
  private readonly baseUrl: string

  constructor(config, context) {
    const dbName = deriveDbName(context.testPath)
    const baseUrl = process.env.DATABASE_URL!.replace(/\/[^/?]*(\?.*)?$/, '')
    // Before setupFiles run, so the app module boots against this file's DB
    process.env.DATABASE_URL = `${baseUrl}/${dbName}`
    super(config, context)
    this.dbName = dbName
    this.baseUrl = baseUrl
  }

  override async setup() {
    const admin = new Client({ connectionString: `${this.baseUrl}/postgres` })
    await admin.connect()
    try {
      // Own-role backends only: terminating others' needs superuser and isn't ours to do
      await admin.query(
        `SELECT pg_terminate_backend(pid) FROM pg_stat_activity
         WHERE datname = '${this.dbName}' AND pid <> pg_backend_pid() AND usename = current_user`,
      )
      await admin.query(`DROP DATABASE IF EXISTS "${this.dbName}"`)
      await admin.query(`CREATE DATABASE "${this.dbName}" TEMPLATE "${TEMPLATE_DB}"`)
    } finally {
      await admin.end()
    }
    await super.setup()
  }
}
```

Notes: build the template in globalSetup, or self-heal a missing one here under a
`pg_advisory_lock` so parallel workers don't race the build; a stale template (schema/seed
changed) needs its own gate outside this environment. Parallel workers additionally require a
bounded per-file connection pool - per-file pools × workers must fit `max_connections`.

---

## Mapping your stack (Phase 2)

Fill during assessment; every row needs a tier or blocking question:

| Area | Tier / choice | Notes |
|------|---------------|-------|
| Test runner | ? | Jest / Vitest |
| App bootstrap | ? | In-process / black-box |
| Transport | ? | REST / tRPC / GraphQL |
| DB local | ? | Ladder rung 0–3 |
| DB CI | ? | Ladder rung 0–3, or documented no-CI-DB gap |
| Auth | ? | Real (light) / mint+gated (heavy IdP) |
| Async work | ? | Seed (suppressed) / poll-to-terminal (worker runs) |
| Queue / Firestore | ? | Emulator / live / stub |
| LLM / paid API | ? | Emulator (rare) / live gated / stub |
| System tier | ? | Only if real infra sits between components |
| Endpoint coverage | ? | Recommended gate for API servers |
| Seed command | ? | |
| CI entrypoint | ? | |

When implementing, fill this table for the target project:

