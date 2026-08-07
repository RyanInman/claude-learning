Red-team of jwt-migration-plan.md. Goal survives; four of the six design decisions don't.

## What survives

- Retiring the per-request Redis lookup is a sound goal, and Bearer-token auth fits the mobile client.
- RS256 over HS256: right call. Verifiers never hold the signing key.
- Forcing one re-auth at cutover: acceptable for 40k DAU.
- Two-sprint sequencing (issuance/middleware, then SPA) is reasonable.

## Deal-breakers — fix before the pitch

1. **Logout is fake (decision 4 + 24h expiry).** Client-side "logout" leaves a valid credential for up to 24 hours. Password reset, account compromise, offboarding, and role revocation all have zero effect until expiry. Any security reviewer kills the plan here. Fix: 10–15 min access tokens + refresh tokens stored in Postgres with rotation. That touches state only at refresh, not per request, so the hot path stays stateless and Redis still retires. The plan's rationale ("refresh state defeats going stateless") conflates per-request state with any state.

2. **localStorage storage (decision 2).** Any XSS exfiltrates the token, and with 24h validity and no revocation the attacker keeps a full day of silent access. Fix: deliver the JWT to the SPA in an httpOnly + Secure + SameSite cookie; reserve the Bearer header for mobile. If the team insists on localStorage, it only becomes defensible with the short expiry from fix 1 plus a strict CSP.

3. **Key management breaks on its own terms (decision 6).** "Generated at deploy time" means every deploy mints a new keypair, which invalidates all outstanding tokens — every deploy logs out every user. With multiple API instances, instances can also disagree on the key. And with no `kid` header, the deferred v2 rotation forces yet another all-user logout. Fix: generate the keypair once, store it in a secrets manager, add `kid` now, verify against a key set. Cheap now, expensive later.

4. **Single-release cutover has no rollback (decision 5).** A verification bug locks out all users, and rolling back breaks whoever logged in on the new path. Fix: one release where middleware accepts both `sid` and JWT and `/login` issues both; delete the session path a release later, after JWTs are proven in production.

5. **`role` claim goes stale for 24h (decision 1).** An admin demotion doesn't take effect until the token expires. Fix 1 shrinks this to ~15 minutes; document that window, or resolve the role server-side for privileged routes.

## Smaller gaps

- No refresh tokens plus 24h expiry means the mobile app forces a login every day. Mobile users expect persistent sessions, so decision 3 undermines the plan's own mobile goal. Fix 1 resolves this — a good pitch angle.
- Claims lack `aud` and `iss`. Add both now; they prevent cross-service token confusion and cost nothing.
- The current session TTL is presumably sliding; a fixed 24h `exp` hard-logs-out users mid-action at hour 24. Refresh tokens restore the sliding behavior.
- Pin `alg=RS256` in the verification middleware and reject `none`/HS256, to close the algorithm-confusion hole.

## Bottom line

One change rescues most of the plan: 15-minute access tokens plus Postgres-backed refresh-token rotation. That single move fixes logout, stolen-token exposure, stale roles, the mobile UX problem, and the sliding-TTL mismatch, while still retiring Redis and keeping the request path stateless. Pair it with the cookie storage fix, stable keys with `kid`, and a dual-accept cutover, and the plan holds up to a hostile room.
