# Integration harness code patterns

Use these patterns in Phase 3, after the plan is agreed. Adapt names and paths to the repo.
`examples.md` applies them to specific stacks.

## Contents

- [Env setup (pre-pin)](#env-setup-pre-pin)
- [Real auth helper (light auth)](#real-auth-helper-light-auth)
- [Test JWT helper (heavy auth)](#test-jwt-helper-heavy-auth)
- [Seeds, factories, cleanup](#seeds-factories-cleanup)
- [TestClient](#testclient)
- [waitFor (async polling)](#waitfor-async-polling)
- [Live-tier gate](#live-tier-gate)
- [CI workflow](#ci-workflow)

## Env setup (pre-pin)

Pin test vars before `dotenv` loads, because `dotenv` never overrides a var that is already set.

```typescript
process.env.NODE_ENV = 'test'
process.env.LOG_LEVEL = 'silent'
// Mint + gated-verify auth tier only. Omit both lines for real (light) auth:
process.env.AUTH_DISABLE_JWT_VERIFICATION = 'true'
process.env.JWT_TEST_SECRET = 'integration-test-secret'
// A falsy env value selects the stub, e.g. process.env.PAYMENT_GATEWAY_URL = ''
// The live-tier opt-in lives here too:
export const isLive = process.env.INTEGRATION_LIVE === 'true' && !!process.env.OPENAI_API_KEY

import { resolve } from 'node:path'
import { config } from 'dotenv'
config({ path: resolve(__dirname, '../.env') }) // does not override pinned vars
```

When the plan uses the bypass flag, add a startup check that makes production refuse
`AUTH_DISABLE_JWT_VERIFICATION=true`.

## Real auth helper (light auth)

Drive the real sign-up and reuse the issued session. The prod auth path runs end to end.

```typescript
// test/helpers/auth.ts - real Better Auth flow; capture the real session cookie
export async function signUpTestUser(app, suffix: string) {
  const email = `integ-${suffix}@app.test`
  const res = await app.request('/api/auth/sign-up/email', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password: TEST_PASSWORD, name: `Test ${suffix}` }),
  })
  if (!res.ok) throw new Error(`Sign-up failed (${res.status}): ${await res.text()}`)
  const cookies = res.headers.getSetCookie().map((c) => c.split(';')[0]).join('; ')
  return { cookies, user: (await res.json()).user }
}
// then: createAuthenticatedClient(app, cookies) sends `cookie: cookies` on every request
```

## Test JWT helper (heavy auth)

Keep one app code path. Gate verification only, never authorization, because
tests must exercise the prod authorization logic.

```text
Prod/CI-test:  verify OR decode (gated) → authorizeFromClaims(payload)
```

```typescript
// test/helpers/test-jwt.ts
export function createTestJwt(claims: { sub: string; roles?: string[] }) {
  return sign(claims, process.env.JWT_TEST_SECRET!, { algorithm: 'HS256', expiresIn: '1h' })
}
```

Clean up by a stable identity (real `user.id`, `sub`, or an email prefix), never by token shape.

## Seeds, factories, cleanup

- **Reference data:** seed idempotently. Look rows up by a stable name or key, never by a
  hardcoded UUID.
- **Ephemeral data:** create rows through factories with defaults and overrides.
- **Cleanup:** run at next-run start (drop and re-clone, or a stale sweep), never at run end,
  so post-run state stays inspectable.
  On rung 0, scope deletes by prefix, `sub`, or tenant, in FK order.

## TestClient

Wrap HTTP or the tRPC caller in a `TestClient` that:

- mints JWTs, or carries the real session cookie,
- tracks created scopes for cleanup,
- exposes typed helpers for common flows,
- offers `expectError` to assert on error response shape.

## waitFor (async polling)

Poll the read model a client would query, until a terminal state.

```typescript
// test/helpers/wait-for.ts
type WaitReq<T> = { read: () => Promise<T>; done: (r: T) => boolean; timeoutMs?: number; pollMs?: number }

export async function waitFor<T>({ read, done, timeoutMs = 120_000, pollMs = 2_000 }: WaitReq<T>) {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    const r = await read()
    if (done(r)) return r
    await new Promise((res) => setTimeout(res, pollMs))
  }
  throw new Error(`Async work did not reach terminal state within ${timeoutMs}ms`)
}

// usage: the terminal predicate covers success AND failure
const doc = await waitFor({
  read: () => client.document.getById.query({ id: documentId }),
  done: (d) => d.summaryJob?.status === 'COMPLETED' || d.summaryJob?.status === 'FAILED',
})
```

## Live-tier gate

```typescript
// summary.integration.test.ts
import { isLive } from './setup-env'

it.runIf(isLive)('summarises a real document end-to-end', async () => {
  // real pipeline; tolerant asserts: substrings and counts, never exact strings
}, { timeout: 180_000 })
```

```json
{
  "scripts": {
    "test:integration": "vitest run --project integration",
    "test:integration:live": "INTEGRATION_LIVE=true vitest run --project integration"
  }
}
```

## CI workflow

The triggers encode the cadence rules. The steps stay the same for every cadence. The example
uses GitHub Actions syntax; map it to the repo's platform.

```yaml
on:
  pull_request:                       # the fast suite gates change
  push: { branches: [main] }
  schedule: [{ cron: '0 3 * * *' }]   # slow and live suites on a nightly clock
  workflow_dispatch:                  # every suite runs on demand

concurrency:
  group: integration-${{ github.ref }}
  cancel-in-progress: true

# steps (adapt provision and teardown to the plan's rung):
#   - provision the database
#   - build → migrate deploy → seed
#   - run the suite (same command as local)
#       env: DATABASE_URL, CI=true
#       (+ AUTH_DISABLE_JWT_VERIFICATION, JWT_TEST_SECRET only for the mint + gated-verify tier)
#   - schedule and dispatch only: run test:integration:live
#       (if: github.event_name != 'pull_request')
#   - publish results and coverage (if: always(), so failures publish too)
#   - teardown (CI only; local state stays inspectable)
```
