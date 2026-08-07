# Debate Review — Judge's Final Report

**Artifact:** jwt-migration-plan.md (migrate auth from Redis sessions to JWTs)
**Date:** 2026-08-07

## Agreed changes

The Advocate conceded four objections in rebuttal. Both sides now support these amendments, and each traces to the plan's own goal of retiring Redis:

1. **Per-user revocation (Objection 1).** Add a `jti` claim to every token and a Postgres denylist table `(jti, expires_at)` holding only explicitly revoked tokens, purged after expiry. The plan's stated reason for rejecting a denylist — "reintroduces Redis" — was factually false: Postgres stays in the architecture permanently, and the API already depends on it. Estimated cost: about one day.
2. **Audit-gated storage (Objection 2, remedy portion).** Make a CSP audit and a third-party-script inventory of authenticated pages a named sprint-1 deliverable that gates the cutover. The `localStorage` decision currently rests on convenience with the entire risk side of the ledger blank.
3. **Two-release cutover (Objection 3).** Release 1: `/login` issues JWTs and the middleware accepts both `sid` cookies and Bearer JWTs (one branch). Release 2, after one to two weeks of clean JWT traffic: remove the session middleware. Redis stays up through this window anyway, so the dual-accept period costs an `if` statement and eliminates the full-user-lockout scenario. The Advocate's original cost comparison attacked a phased-dual-auth program the Adversary never proposed.
4. **Key lifecycle, three sentences (Objection 4).** Generate the keypair once, out of band, in the secrets manager — not per deploy. Include a `kid` header from day one. Serve the public key at `/.well-known/jwks.json`. Without these, the plan's own claimed RS256 benefit — independent verification by the mobile backend — is unimplementable, and v2 rotation becomes a forced global logout.

Combined estimate from the Adversary: roughly two days of work. Both sides also endorse a fifth, non-blocking item: the half-day measurement task (Redis spend, incident count, ops hours), attached to the Goal section.

## Dropped objections

**Objection 5 (unquantified benefit) — dropped by the Adversary.** Two arguments answered it. First, the mobile app ships next quarter and needs Bearer-token auth regardless of what Redis costs, so the migration has a concrete driver even with the infra numbers blank. Second, "ops wants Redis gone" is an organizational mandate; a debate review pressure-tests execution, it does not relitigate a decision the organization made. The measurement task survives as documentation hygiene, but it no longer blocks approval. The plan is fine as-is on this point, subject to the note in my recommendation about what the numbers may still size.

## Contested points

Only one point remains genuinely live.

**Token storage: `localStorage` versus `httpOnly` cookie.**

- *Adversary's final position:* Objection 2 sustained at narrowed weight. The exfiltration delta is real — a stolen token grants offline, off-site access that survives the closed tab and the CSP fix — and this plan as originally written maximized it. But the Adversary explicitly coupled the objection's severity to Objection 1: "if revocation or short TTLs land, `localStorage` becomes a defensible convenience and I would not block on it," provided the audit gates cutover.
- *Advocate's final position:* Keep `localStorage`, gated on the audit. The cookie switch buys less than its reputation: an XSS payload that cannot read an `httpOnly` cookie still issues fully authenticated requests from the victim's page, so the switch converts exfiltration into in-session abuse rather than eliminating the risk — while adding CSRF defense as a permanent obligation and splitting the web and mobile auth paths. The real XSS defense is CSP and script hygiene, identical under either storage.

A second candidate — 15–30-minute TTL with refresh tokens (the Adversary's option (b)) — is not truly contested: the Adversary offered it as an alternative to the denylist, not in addition, and accepts option (a) as the minimum viable fix.

## Rulings

**Storage: the Advocate wins, conditionally.** The technical argument is sound and the Adversary conceded its core in rebuttal: `httpOnly` narrows XSS damage, it does not eliminate it, and it charges a permanent CSRF tax plus a split client story for that narrowing. Once the denylist makes a stolen token revocable and the audit measures the actual XSS surface, `localStorage` is a defensible v1 choice — and the Adversary's own narrowed position agrees. The condition matters: this ruling holds only if amendment 1 (the denylist) and amendment 2 (the audit gate) both ship in v1. If either slips from scope, the objection returns at full weight and the cookie switch becomes the live question again. This is not a manufactured middle ground; it is the resolution both sides converged on.

One honest caveat neither side dwelt on: the denylist adds one Postgres read per authenticated request. At 40k DAU this is trivial and it does not touch Redis, so the plan's goal survives intact — but "stateless" should be restated in the plan as "no Redis, no per-session state," which is what the architecture actually achieves.

## Judge's recommendation

**Adopt the amended plan: all four agreed changes plus the non-blocking measurement task.** The debate converged unusually cleanly — the Advocate conceded on evidence, not pressure, and the Adversary dropped and narrowed where the evidence went against it. The amended plan retires Redis exactly as well as the original, keeps the two-sprint shape (the amendments cost roughly two days), and removes three concrete failure modes: a 24-hour irrevocable credential at 40k users, a cutover-day lockout with an untested rollback, and a forced global logout at v2 rotation.

Run the measurement task early in sprint 1. Treat its output the way the Advocate framed it: it sizes the migration (full cutover versus JWTs-for-mobile-only), it does not veto the token work, which the mobile deadline requires regardless.

## Your decision

You are choosing between:

1. **Amended plan (recommended).** Original design plus: `jti` + Postgres denylist, CSP/script audit gating cutover, two-release dual-accept cutover, generate-once keypair with `kid` and JWKS, half-day Redis measurement. Adds ~2 days; fits the two-sprint timeline.
2. **Plan as written.** Ships a 24-hour token with no per-user revocation, a single-cut deploy with an untested rollback, and no key-distribution mechanism. Both debaters ended the debate opposed to this option.
3. **Amended plan, but with `httpOnly` cookies for the web SPA.** Take the Adversary's original storage remedy anyway. Buys a narrower exfiltration window at the cost of CSRF defense forever and divergent web/mobile auth paths. Defensible if you weight token exfiltration above the debate's consensus.
4. **Larger redesign: 15–30-minute access tokens with Postgres-backed refresh rotation.** Strongest security posture; largest scope increase. Neither side prefers it once the denylist exists.
5. **Measure first, then scope.** Run the half-day measurement before committing, and choose between full cutover and the hybrid (JWTs for mobile, sessions for web) based on the numbers. Slowest path, but the only one that makes the Redis payoff explicit before work starts.
