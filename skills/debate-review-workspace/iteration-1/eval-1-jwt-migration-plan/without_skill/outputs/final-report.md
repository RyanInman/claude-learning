# Debate Review: JWT Migration Plan

Method: adversarial debate. Critic agent attacked plan, Advocate agent steelmanned it, Critic rebutted the defenses, judge adjudicated. Full transcripts: `round1-critic-brief.md`, `round1-advocate-brief.md`, `round2-adjudication.md` (includes Critic rebuttal).

## Scoreboard

| Plan element | Verdict |
|---|---|
| Goal: retire Redis, support mobile | Survives (as a choice, not a necessity) |
| D1: RS256 JWTs via `/login` | Survives with claim fixes (`jti`, `iss`, `aud`, pinned alg) |
| D1: 24h expiry | Survives only paired with kill switch; dies once refresh tokens land |
| D2: localStorage | Fails as written; conditionally survivable with CSP + kill switch |
| D3: No refresh tokens v1 | Survives with explicit v2 commitment; rationale given is wrong |
| D4: Client-side-only logout | Fails as written; needs server-side kill switch |
| D5: Single-release cutover, middleware deleted | Fails as written; survives with rollback flag |
| D6: Keypair generated at deploy time, env vars | Fails outright; plan's worst defect |
| Timeline: two sprints | Survives only with amendments included; prices happy path |

## Indefensible as written (Advocate conceded all four)

1. **D6 key management is a bug, not a decision.** "Generated at deploy time" literally means every deploy mints a new keypair and invalidates every outstanding token: deploys silently log out all 40k users, and instances deploying at different moments issue tokens other instances reject (intermittent 401 heisenbugs). If a key leaks, there is no `kid`, no rotation path, and an attacker can mint `role: admin` tokens for any user, indistinguishable from real ones in logs. Fix: generate once, store in secret store, verify against a key list, add `kid`.
2. **Zero revocation is worse than today.** Banned user, fired employee, "someone is in my account," password change: all keep working for up to 24h with no kill switch. Today ops can flush a Redis key. Critic's kill chain: localStorage exposure x 24h TTL x no revocation means one XSS or compromised npm dependency yields thousands of irrevocable credentials.
3. **No rollback.** Session middleware removed in the same deploy: any post-cutover auth bug locks out the entire user base in both directions (old build rejects JWTs, `sid` cookies are gone).
4. **Stale `role` claim never addressed.** Demote an admin, they stay admin up to 24h. Acceptable only if stated and accepted explicitly.

## Contested points, adjudicated

- **localStorage.** Advocate's best argument: XSS defeats httpOnly cookies too (attacker rides the session in-page). Partially true, but false equivalence on blast radius: session riding needs the victim's page open and dies when patched or revoked; an exfiltrated token gives durable offline access from attacker infra for the full remaining TTL, and this plan has no revocation. Critic's rebuttal additions, upheld: the proposed CSP mitigation fails against the plan's own primary XSS vector (a compromised npm dependency ships inside the first-party bundle as allowed-origin script), and "one code path with mobile" conflates transport with storage: mobile stores in Keychain/Keystore; only the Bearer header is shared. The plan's stated rationale (reload convenience) is a convenience argument for a security decision. Verdict: pick httpOnly cookie for the SPA, or keep localStorage as an explicit tradeoff whose severity drops from Critical to High only once the per-request kill switch exists; shorter TTL once refresh tokens land. As written it fails.
- **No refresh tokens v1.** Defensible sequencing: 24h matches current session TTL, users feel no change, half-done refresh tokens would be worse. But the plan's rationale ("adds server state, defeats the purpose") is wrong: refresh state fits in Postgres; the goal is retiring Redis, not stateless purity. And mobile next quarter makes refresh tokens near-inevitable (nobody ships daily re-login on mobile), so commit v2 now and put `jti` in v1 tokens so it slots in.
- **Big-bang cutover.** Dual-accept window is textbook, but for a monolith + single client + same-team deploy, single release is fine IF the session middleware stays in the artifact behind a config flag for one release (rollback restored, no dual-stack semantics). Riders from rebuttal, upheld: Redis stays alive until the flag is deleted, so the ops retirement date moves and the plan must say so; profile `/login` bcrypt cost and load-test the re-auth burst; test the flag in both directions before deploy.
- **The premise itself.** Critic's strongest structural point: every stated goal (retire Redis, mobile, horizontal scale) is also met by opaque bearer tokens in a Postgres `sessions` table, which keeps instant revocation, needs no key custody, has no alg-confusion surface, and skips this entire risk area; at 40k DAU session writes are ~logins, trivial. Opaque tokens in a Bearer header are equally standard on mobile; bearer-vs-cookie is a separate axis from stateless-vs-stateful. The plan's own text leaks the problem: it rejects refresh tokens and denylists for violating stateless purity, but purity was never the requirement, and the amended plan reaches workable precisely by abandoning strict statelessness (the per-request kill-switch read). Final severity: Medium, an architecture-cleanliness argument, not a security blocker. Verdict: JWTs remain a defensible choice (real ops mandate, standard mobile pattern), but the plan must contain an alternatives-considered section for Postgres opaque tokens, or the first senior engineer in your pitch meeting will write it for you.

## The kill-switch amendment (load-bearing, with a correction)

Advocate's cheapest fix for revocation: per-user `token_not_before` timestamp in Postgres. Both judge and Critic caught the same flaw: as the Advocate described it ("checked only on an admin-triggered path") it enforces nothing; a killed user's token validates forever on every ordinary endpoint. Correct form: column WRITTEN via admin paths, READ on every authenticated request (reject when token `iat` < user's `token_not_before`), in-process cache with ~60s TTL, DB on miss. Revocation lag under 60s; per-user granularity kills all the user's tokens (fine for a v1 kill switch; `jti` enables finer grain later); specify same-second login-after-kill semantics. Plan text must say "checked on every request" or the implemented version will be the broken one. Honest consequence: auth is no longer strictly stateless in the hot path. That is fine; stateless was never the actual requirement.

## What to change before pitching (fits in the two sprints)

1. D6: keypair generated once, stored in secret store, `kid` header, middleware verifies against key list. (~0.5 day)
2. Add `jti`, `iss`, `aud` claims; pin verification to RS256 (reject `alg: none`/HS256 confusion). (~0.5 day)
3. Add `token_not_before` kill switch, checked per request ("checked on every request" in the plan text, verbatim), 60s in-process cache. (~1 day)
4. Keep session middleware behind config flag for one release; off-peak cutover; profile `/login` bcrypt cost for the re-auth burst; note Redis retirement date slips until flag deletion. (~0.5 day)
5. Rewrite D3's rationale (Postgres state is allowed; Redis retirement is the goal) and commit refresh tokens + short TTL to v2, landing before mobile ships.
6. Decide localStorage vs httpOnly cookie as an explicit XSS-vs-CSRF tradeoff; if localStorage stays, add strict CSP + npm audit in CI, and do not present CSP as covering the compromised-dependency vector (it does not).
7. Add alternatives-considered section: Postgres opaque sessions. State why JWT anyway (ops mandate, mobile bearer pattern, no dual token scheme later).
8. Address stale roles explicitly: accepted for <=24h in v1, resolved by short TTL in v2.

## Bottom line

Architecture (RS256 JWTs, bearer headers, no refresh in v1, single-release cutover) survives the debate once amended; roughly two days of added work, inside the existing timeline. What does not survive: deploy-time key generation, zero revocation, no rollback, the "stateless purity" argument used to justify decisions 3 and 4, and CSP-as-answer-to-npm-supply-chain. One honest framing note for the pitch: the amended plan works because it quietly gives up strict statelessness (per-request kill-switch read); say that out loud rather than letting a reviewer discover it. The premise-level question to be ready for in the room: "why not opaque tokens in Postgres?"
