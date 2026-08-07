# Debate Review — Round 1: Critic Attack Brief

(Verbatim output of the Critic agent attacking jwt-migration-plan.md.)

## 1. Premise Attack

Plan's goal: "stateless JWTs so the API tier scales horizontally without a shared session store" + mobile auth + retire Redis. All three goals are achievable without JWTs, and the plan never costs the alternative.

- **Horizontal scaling at 40k DAU is a phantom problem.** 40k DAU is roughly tens of req/s. A single Redis instance handles ~100k lookups/s. The session store is not the scaling bottleneck; the Flask monolith is. Plan cites no latency or throughput measurement showing Redis lookup on every request is a problem.
- **Mobile doesn't require JWTs.** Mobile apps send bearer tokens fine — opaque random tokens in a Postgres `sessions` table work identically (`Authorization: Bearer <opaque>`). "Same auth as the web app" is satisfied by any token scheme.
- **Retiring Redis doesn't require statelessness.** Sessions can move to Postgres (already stateful infra the plan admits keeping). A `sessions` table with an index at this scale is trivial load. The plan trades a solved problem (revocable sessions) for an unsolved one (irrevocable tokens) to avoid a table.
- The plan itself concedes the premise leaks: decision 3 admits refresh rotation "adds server state, which defeats the purpose" and decision 4 admits denylists "reintroduce Redis." When every safety mechanism is rejected because it violates purity of the premise, the premise is the bug.

**Verdict: the stated goals are better served by Postgres-backed opaque tokens. JWT is a solution shopping for a problem.**

## 2. Per-Decision Attacks

### Decision 1 — RS256 JWTs, 24h expiry, claims `sub`, `role`, `exp`, `iat` — **Critical**
- 24h irrevocable lifetime. No `jti`, no revocation path, so every issued token is a 24-hour bearer credential nothing can kill. Ban a user, detect a stolen token, fire an employee: they keep full API access up to 24h.
- `role` baked into token: demote an admin and they stay admin for 24h. Privilege escalation window is the token TTL.
- Missing claims: no `aud`/`iss` (token confusion risk), no `jti` (no audit trail, no future denylist hook), no `nbf`. Library-level risk: `alg` confusion (RS256→HS256 using public key as HMAC secret) if verification isn't pinned — plan doesn't specify pinning.

### Decision 2 — SPA stores JWT in localStorage — **Critical**
- localStorage is synchronously readable by any JS in the origin. One XSS — one compromised npm dependency, one injected analytics snippet, one stored-XSS — and the attacker exfiltrates a credential valid up to 24h from anywhere, no revocation. Current `sid` cookie can be HttpOnly (XSS can't read it) and is server-revocable.
- Rationale ("survives page reloads, easy Bearer header") is a convenience argument for a security decision. HttpOnly cookies also survive reloads; CSRF cost of cookies is mitigable (SameSite=Strict + CSRF token); XSS cost of localStorage is mitigable by nothing.
- Incident sketch: malicious transitive dependency ships; every user who loaded the SPA in the window has tokens exfiltrated; none can be invalidated; forced global key rotation + breach notification.

### Decision 3 — No refresh tokens v1 — **High**
- This decision forces the 24h access-token TTL. With refresh tokens, access tokens could be 5–15 min and the refresh endpoint becomes the revocation checkpoint. Rejecting it removes the only place stateless designs regain control.
- "Matches our current session TTL" is a false equivalence: current sessions are revocable at any instant; same TTL without revocability is a different security posture wearing the same number.
- Mobile impact: mobile users will not tolerate daily re-login; team forced to stretch TTL (worse) or bolt on refresh tokens under deadline pressure.

### Decision 4 — Client-side-only logout — **High**
- Logout that isn't logout: token remains valid server-side up to 24h. "Log out all sessions" (standard compromised-account response) is unimplementable. Support answer becomes "change your password and wait 24 hours."
- Compliance regimes treating "terminate session" as a control fail audit.
- Rationale ignores that a denylist of revoked tokens is tiny (dozens of rows) and fits Postgres or in-process cache — nothing like full session state.

### Decision 5 — Single-release cutover, session middleware removed same deploy — **High**
- No rollback story. After cutover, JWTs are in the wild; old build rejects Bearer JWTs and `sid` cookies are gone → users locked out in both directions. Rollback = second forced global re-auth plus whatever broke.
- Forced re-auth of 40k DAU is a self-inflicted availability event: `/login` burst, password-reset spike, support spike.
- Standard dual-accept window (accept session OR JWT for N days) costs one release and eliminates both failure modes; never considered.

### Decision 6 — One keypair generated at deploy time, env vars, rotation deferred — **Critical**
- "Generated at deploy time" literally means every deploy mints a new keypair → invalidates all outstanding tokens → deploys silently log out all users; multiple instances deploying at different moments issue tokens each other reject → intermittent 401 heisenbugs.
- No `kid`, no JWKS, single key, rotation deferred: when the key leaks, the only response is generate new key → mass logout, with no way to distinguish attacker-forged tokens from legitimate ones in logs. Leaked RS256 private key = attacker mints `role: admin` tokens for any `sub`, indefinitely, undetectably.

### Timeline — two sprints — **Medium**
- No security review, pen test, load test of `/login` under forced re-auth burst, mobile-team consultation, monitoring/alerting work. Prices the happy path only; auth migrations consume estimates in edge cases (clock skew, CORS preflight for Authorization header, logout UX).

## 3. Interaction Attacks

- **D2 × D1 × D4 (kill chain):** localStorage exposure × 24h TTL × no revocation. Any single XSS yields a credential that is long-lived, exfiltratable, and unkillable.
- **D6 × D4:** key compromise has exactly one remedy (rotate key), which is also the disaster: global logout. The only incident-response lever is the worst-case outage.
- **D5 × D6:** single-release cutover ships the deploy-time key bug to 100% of users with no session fallback.
- **D3 × D1:** circular justification ("long TTL so no refresh needed" / "no refresh so TTL must be long"); the circle's cost lands on nonexistent revocation.
- **D1 role claim × D3/D4:** stale authorization by design; permission changes propagate in up-to-24h with no forcing mechanism.

## 4. Silent Gaps

- Revocation/ban story absent (bans, password change, "log out everywhere", offboarding, compromised-account response).
- Rollback plan: none.
- Key custody: who holds the private key, secret manager vs env var, access audit.
- Algorithm pinning / library choice (`alg: none`, HS256 confusion).
- Token size and transport; CORS config change for Authorization header.
- CSRF posture change never stated as a tradeoff.
- Mobile requirements (Keychain/Keystore, token lifetime expectations, push-triggered logout) — the stated motivation gets zero design attention.
- Observability: no auth failure metrics, forged-token detection, or audit logging (`jti` absent).
- Clock skew across instances/clients.
- Password reset does not invalidate tokens.

## 5. Top 5 Attacks by Severity

1. [Critical] D6 — deploy-time keypair: daily global logouts + cross-instance 401 chaos, or an unrotatable single key whose leak means undetectable admin-token forgery.
2. [Critical] D2×D1×D4 — localStorage + 24h + no revocation: one XSS/supply-chain event yields thousands of irrevocable 24h credentials; strictly worse than current HttpOnly revocable sessions.
3. [Critical] D4/D1 — no revocation of any kind: bans, offboarding, demotion, compromised accounts all have a 24h enforcement gap with no kill switch.
4. [High] D5 — single-release cutover with middleware removed: no rollback path; any post-deploy auth bug locks out the entire user base in both directions.
5. [High] Premise — JWT unnecessary for stated goals: Postgres-backed opaque bearer tokens retire Redis, serve mobile, and scale fine at 40k DAU while keeping instant revocation.
