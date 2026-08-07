# Debate Review — Round 1: Advocate Defense Brief

(Verbatim output of the Advocate agent steelmanning jwt-migration-plan.md.)

## 1. Premise Defense

The premise is sound and over-determined — three independent forces point the same direction:

- **Ops mandate is real.** Redis is the only stateful infra besides Postgres, and ops wants it gone. That's an operational cost line (cluster maintenance, failover config, on-call surface). Stateless auth is the only auth design that lets Redis actually retire rather than shrink.
- **Mobile is next quarter, not hypothetical.** Cookie/session auth on native mobile is a known pain (cookie jars, WebView hacks). Bearer tokens are the industry-standard native pattern. Building JWT auth now means mobile onboards onto proven infrastructure.
- **Horizontal scaling without shared state.** Signature verification is local CPU, no network hop, no shared dependency. At 40k DAU it removes a failure mode (Redis down = everyone logged out) rather than a performance bottleneck — removing failure modes is a legitimate goal.

Counter-premise ("keep sessions in Postgres") fails the mobile goal less cleanly, fails the ops goal only by relocating state, and adds session-table write load to the one DB everyone depends on.

## 2. Decision-by-Decision Defense

### D1: RS256, 24h expiry, minimal claims
RS256 right over HS256 — mobile app and future services verify with the public key without holding a signing secret. Minimal claims correct: no PII, small header. 24h deliberately matches current session TTL — no user-visible behavior change, de-risks cutover. Scope discipline, not laziness.
**Cheapest amendment:** drop expiry to 1-4h only if refresh tokens are added (package deal with D3). Add `jti` now (one line) so future revocation needs no token format change.

### D2: localStorage
The attack is weaker than its reputation. If an attacker has XSS on your SPA, httpOnly cookies do NOT save you — the attacker rides the session, calls your API as the user, exfiltrates data in-page. Token theft vs session riding is a difference in attack ergonomics, not compromise vs no-compromise. localStorage buys: free CSRF immunity, one code path shared with mobile (both attach Bearer headers), no SameSite/CORS cookie edge cases. Main React XSS vector is compromised npm dependencies — which httpOnly doesn't fix either.
**Cheapest amendment:** keep localStorage, add strict CSP header + `npm audit` in CI.

### D3: No refresh tokens v1
Refresh rotation done properly requires server-side state (rotation detection, family revocation) — reintroducing the store being retired. Half-done refresh tokens (long-lived, no rotation) are worse than none. Users already log in daily today; v1 changes nothing they can feel. Refresh tokens exist to enable SHORT access tokens, which is v2 hardening, not a launch requirement.
**Cheapest amendment:** commit v2 to refresh tokens explicitly; add `jti` claim now.

### D4: Client-side logout
Matches what logout is for the 95% case: "stop being logged in on this device." A denylist is a session store with extra steps. Sessions today already have a 24h tail; a stolen `sid` today is live until TTL unless someone manually flushes Redis, which is not a documented runbook either. Parity with current behavior at lower cost.
**Cheapest amendment:** per-user `token_not_before` timestamp column in Postgres, checked on an admin-triggered kill-switch path (in-process cache, 60s TTL). ~30 lines, no Redis; covers fired-employee/stolen-account emergencies. Stateless hot path, revocable emergency path.

### D5: Single-release cutover
Dual-stack auth doubles middleware surface and test matrix, and creates the worst bug class: requests authenticated by different mechanisms behaving differently. For a monolith + single client + same-team deploy, big-bang is simpler and therefore safer — blast radius is "everyone logs in again," a Tuesday, not an outage. Phased migrations are for when you can't coordinate clients.
**Cheapest amendment:** single release, but JWT middleware behind a config flag with session middleware kept in the artifact for one release, deleted the release after. One flag, no dual-stack semantics (flag picks one mode globally), restores rollback.

### D6: Keypair in env vars, rotation deferred
Partial: one keypair in the deployment environment is the same trust model as every other secret the app holds (DB password, API keys). Deferring rotation AUTOMATION is correct scope control. But "generated at deploy time" as written is a bug, not a decision — see concessions.
**Cheapest amendment:** generate keypair once, manually; store in existing secret store; middleware verifies against a LIST of public keys (3-line loop) so future rotation needs no code change.

### Timeline: two sprints
Credible BECAUSE of decisions 3-6; critics who demand refresh rotation, revocation infra, and phased rollout attack the timeline by first tripling the scope. Sprint 1 (server) / sprint 2 (client + cutover) is the right dependency order.
**Cheapest amendment:** reserve back half of sprint 2 for cutover-flag soak and the kill-switch path.

## 3. Concessions vs. Overblown Criticisms

### Conceded (indefensible as written)
1. **"Generated at deploy time" keys.** Every deploy invalidates every outstanding token; contradicts the plan's own 24h design. Not a tradeoff; an error.
2. **No emergency revocation path at all.** Client-side logout is fine; having NO server-side mechanism for account compromise or offboarding is not. Worse than today, where ops could flush a Redis key.
3. **No rollback plan.** A critical JWT bug post-cutover has no path back except redeploying old code and force-logging-out everyone twice. One config flag fixes this; its absence is a gap, not a choice.
4. **Stale `role` claims, unaddressed.** Defensible to accept the risk explicitly; indefensible not to notice it.

### Overblown for this context
1. "localStorage is disqualifying" — XSS defeats httpOnly cookies too via session riding; cargo-culted from a different threat model.
2. "You must have refresh tokens" — only if you need short access tokens; hardening goal, not launch gate.
3. "24h tokens are reckless" — duration is status quo; the revocation gap is the real issue.
4. "Big-bang cutover is always wrong" — not for monolith + single client + same-team deploy; missing piece is a rollback flag, not phased dual-stack.
5. "JWTs don't help you scale at 40k DAU" — plan never claims Redis is a perf bottleneck; drivers are ops retirement and mobile readiness.

**Net position:** Architecture defensible for this team and scale. Four amendments — fixed keypair, `token_not_before` kill switch, rollback flag, `jti` claim — total perhaps two days of work, fit inside the existing timeline, and convert every conceded point without abandoning any decision's spirit.
