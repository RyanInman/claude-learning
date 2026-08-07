# Debate Review Transcript

**Artifact:** /Users/admin/claude-learning/skills/debate-review-workspace/iteration-1/jwt-migration-plan/with_skill/work/jwt-migration-plan.md
**Date:** 2026-08-01

Append-only. Each role writes under its own heading and never edits another role's text.

---

## Phase 1 — Defender: Opening Statement

Goal: retire Redis as a session store and get one auth mechanism that works for today's React SPA and next quarter's mobile app. Two forces drive this: ops wants Redis gone (it is our only stateful infra besides Postgres, and it is on the critical path of every request), and the mobile team needs token-based auth anyway — cookies are awkward on native clients.

Why each decision:

1. **RS256 JWTs, 24h expiry, minimal claims.** RS256 over HS256 so future services can verify tokens with the public key without holding the signing secret. 24h matches our current session TTL, so user-visible behavior (log in roughly once a day) is unchanged. Claims kept minimal to keep tokens small and avoid stuffing authorization data that goes stale.

2. **localStorage.** It survives reloads, works identically across tabs, and our fetch wrapper already centralizes header injection. Cookies would need CSRF protection and don't carry over to mobile; localStorage gives one storage story per platform.

3. **No refresh tokens in v1.** Refresh rotation means server-side state (token family tracking), which reintroduces exactly the stateful store we're removing. With a 24h access token, the UX equals today's sessions, so refresh tokens buy little in v1.

4. **Client-side logout.** A server denylist means a Redis-like store checked on every request — the architecture we're leaving. Deleting the token locally matches what most stateless-JWT shops do at this scale.

5. **Single-release cutover.** Dual-stack auth (sessions AND JWTs live simultaneously) doubles middleware surface and test matrix for a one-time migration. Forcing 40k DAU to re-login once is a cheap, bounded cost.

6. **One keypair in env vars, rotation deferred.** Key rotation infrastructure (JWKS endpoint, kid headers, overlap windows) is real work; deferring it keeps sprint 1 shippable. Env vars are how we manage every other secret today.

Constraints not visible in the doc: small team (this is two sprints of one team's capacity), no dedicated security engineer, and ops has already scheduled Redis decommission for next quarter, which is the forcing function on the timeline.

Least confident decisions, flagged honestly: **localStorage vs. cookie storage** (XSS exposure is the known tradeoff), **no revocation path at all** (client-side logout means a stolen token lives up to 24h), and **single-release cutover** (no rollback story if JWT middleware misbehaves in production).

## Phase 2 — Clarifying Questions

### Adversary's questions

1. Today, with Redis sessions, what happens when an account is compromised, an employee is offboarded, or a user's `role` changes — do you delete the session server-side for immediate effect? Is there any policy, compliance, or customer-facing commitment (e.g. "access revoked within N minutes") that depends on that capability?

2. During the transition quarter, is the Redis cluster still running after the cutover deploy? Concretely: if the JWT middleware misbehaves in production, what is the rollback path, and how long would it take to restore session-based auth?

3. For the mobile app shipping next quarter: is the plan for it to use the same 24h-expiry, no-refresh-token model, and is a forced re-login every 24 hours considered acceptable UX on mobile? Where will the token be stored on the native clients?

### Advocate's questions

1. What is the SPA's current XSS posture — is there a Content-Security-Policy in place, and how is third-party JS (analytics, dependency supply chain) controlled? This determines how much real-world weight the localStorage-vs-cookie tradeoff carries for this specific app.
2. In an emergency (mass token theft, signing key leak), how fast can the team redeploy with a new keypair via the existing env-var pipeline — minutes, or hours? Rotating the key invalidates every outstanding token, so this is the de facto revoke-all lever; its speed defines the actual worst-case exposure window.
3. For the single-release cutover: does the deploy pipeline support fast rollback, and if the JWT middleware were rolled back within hours, would re-enabling session middleware work cleanly (is Redis still running during the transition quarter)? A cheap rollback path materially changes the risk math on doing it in one release.

### Judge's questions

1. What is the actual risk appetite for a stolen-token window? Concretely: does the product handle data or actions (payments, PII export, admin operations) where a token valid for up to 24 hours with no revocation path is unacceptable, or is worst-case exposure limited enough that "wait out the expiry" is tolerable? This determines how much weight the no-revocation and localStorage objections deserve.

2. Is the Redis decommission date truly fixed, and what happens if this migration slips? If ops's next-quarter deadline is negotiable, arguments for a phased cutover or v1 refresh tokens gain feasibility; if it is hard, compromises that add sprints must identify what they displace.

3. On the single-release cutover: is there any rollback mechanism at all (feature flag, ability to redeploy session middleware, keeping Redis warm for N days post-cutover), or does the plan assume forward-only? The Defender flagged "no rollback story" as a low-confidence point; I need to know whether that is a plan gap or a deliberate accepted risk.

### Defender's answers

**To Adversary Q1 (revocation today):** Yes — today support and ops can kill a session instantly by deleting the Redis key. We use it for offboarding and the occasional compromised account (a handful of times a quarter). There is no contractual or compliance SLA that promises revocation within N minutes; it is internal practice, not a commitment. Role changes take effect on next request because the middleware re-reads the user row for permissions beyond the coarse `role`.

**To Adversary Q2 / Advocate Q3 / Judge Q3 (rollback):** Redis stays running until its decommission next quarter, so during the transition window rollback = redeploy the previous release (~15–30 min through the pipeline), which restores session middleware against the still-warm Redis cluster. Everyone re-authenticates again. There is no feature flag in the current plan; the "no rollback story" I flagged means no *designed* rollback — the previous-release redeploy exists but is untested for this path. That is a gap, not a deliberate accepted risk.

**To Adversary Q3 (mobile):** The working assumption is the same token model on mobile, stored in Keychain (iOS) / Keystore (Android). A forced re-login every 24h on mobile has not been UX-reviewed — honest answer: the plan was written web-first and mobile inherits it. Mobile norms (stay logged in for weeks) may conflict with the no-refresh-token decision.

**To Advocate Q1 (XSS posture):** Moderate. We have a CSP but it is not strict — it allows our analytics vendor's script and does not use nonces. Standard npm supply chain, no SRI on third-party tags. React gives default escaping but we have two `dangerouslySetInnerHTML` uses in the rich-text renderer.

**To Advocate Q2 (emergency key rotation):** New keypair = env var change + rolling redeploy: roughly 30–60 minutes including approval. It logs out all 40k users, which is acceptable in a genuine emergency. That redeploy is the de facto revoke-all lever; there is no per-user lever.

**To Judge Q1 (risk appetite):** SaaS handling customer PII; admin accounts can export data and manage users. No in-app payments. A 24h irrevocable token for a regular user is tolerable; for an admin it is uncomfortable and would likely fail a customer security review.

**To Judge Q2 (deadline):** The Redis decommission date is ops-internal, negotiable by a few weeks, not by a quarter. Adding a full sprint of scope would push into mobile-app-support work already committed for next quarter.

## Phase 3 — Adversary's Case

Five objections, strongest first. Note that objections 1–3 share one root cause — the 24h irrevocable access token — and my proposed fix for #1 resolves #2 and substantially mitigates #3. This is not five separate demands; it is largely one architectural correction plus two operational ones.

**Objection 1 — The plan deletes a revocation capability the org actively uses, and the Defender concedes the result fails a bar the product must meet.**

- **Problem:** Today support/ops kill sessions instantly for offboarding and compromised accounts, and they do it "a handful of times a quarter" — this is a load-bearing capability, not a theoretical one. Post-migration there is no per-user revocation at all; the only lever is a global key rotation that logs out 40k users and takes 30–60 minutes. An admin token — which can export customer PII and manage users — remains valid for up to 24 hours after compromise or offboarding. The Defender's own answer: this "would likely fail a customer security review." A plan that knowingly ships a state that fails customer security review for a PII-handling SaaS is not a v2 deferral; it is a v1 defect. The stale `role` claim compounds it: a demoted or offboarded admin's token still asserts `admin` for up to 24h.
- **Evidence:** Defender's answers to Adversary Q1 and Judge Q1 (transcript lines above): instant revocation is current practice; no per-user lever exists post-migration; admin exposure is "uncomfortable and would likely fail a customer security review."
- **Better way:** The goal is "retire Redis," not "zero server state" — Postgres stays. Issue short-lived access tokens (10–15 min) plus an opaque refresh token stored hashed in a Postgres table. Per-request verification stays fully stateless (signature + `exp` only); the DB is touched only at refresh, i.e. once per ~15 min per user instead of every request. Revocation = delete the refresh-token row; worst-case exposure drops from 24h to 15 min, which restores parity with today's practice. This is one table, one `/refresh` endpoint, and an interceptor change in the fetch wrapper — well inside the existing two-sprint envelope, because it replaces (not adds to) the 24h-token work.

**Objection 2 — "No refresh tokens in v1" builds the wrong token contract for the migration's own second goal (mobile).**

- **Problem:** The stated purpose includes serving next quarter's mobile app, but the Defender admits the plan is web-first and mobile inherits it un-reviewed. Mobile norms are weeks-long sessions; a forced re-login every 24h will not survive mobile UX review. So refresh tokens are not optional v2 polish — they are a known v1.5 requirement arriving in one quarter. Shipping v1 without them means the mobile app either builds against a token contract that is about to change, or its schedule absorbs an auth rework. Deferral here does not avoid the work; it moves the work to the worst possible time (mobile launch quarter, already committed capacity).
- **Evidence:** Defender's answer to Adversary Q3: "the plan was written web-first and mobile inherits it… Mobile norms (stay logged in for weeks) may conflict with the no-refresh-token decision." Defender's answer to Judge Q2: next quarter's capacity is already committed to mobile-app support.
- **Better way:** Same fix as Objection 1. Refresh tokens in v1 give mobile long-lived sessions (long-expiry refresh token in Keychain/Keystore, short access token in memory) with zero rework at mobile launch. One design serves both clients, which was the point of the migration.

**Objection 3 — 24h bearer token in localStorage, in an app with an admittedly weak XSS posture, concentrates risk the plan itself created.**

- **Problem:** The artifact treats localStorage as a convenience decision, but the Defender's answers establish the actual exposure: non-strict CSP, un-nonced third-party analytics script, no SRI, standard npm supply chain, and two `dangerouslySetInnerHTML` sites. Any one XSS or supply-chain script gives an attacker a token that is valid for 24h with no revocation. The combination — long-lived + irrevocable + JS-readable — is the problem; each leg alone would be tolerable.
- **Evidence:** Defender's answer to Advocate Q1 (XSS posture) and Q2 (only lever is a 30–60 min global logout). Analytics-vendor supply-chain token theft is a well-precedented attack class (e.g. Magecart-style script compromises).
- **Better way:** Two independent mitigations, both cheap: (a) with Objection 1's fix, the JS-readable artifact is a 15-min access token — stolen tokens age out before most exfiltration is even noticed, and the refresh token can be revoked; (b) since the Flask monolith serves the SPA (same origin), the web client can carry the refresh token in an HttpOnly `SameSite=Strict` cookie scoped to `/refresh`, keeping it out of JS reach entirely, while mobile uses the Bearer flow. "One storage story per platform" is already false — mobile uses Keychain/Keystore — so platform-appropriate storage on web costs no architectural purity. If (b) is judged too much scope, (a) alone plus a tightened CSP moves the risk from "uncomfortable" to "defensible."

**Objection 4 — Single-release cutover whose only rollback is an untested redeploy is an avoidable gamble on the auth path of a 40k-DAU product.**

- **Problem:** Auth middleware is the one component where a bad deploy takes down every request. The plan removes session middleware in the same release that introduces JWT middleware, with no feature flag; rollback is "redeploy previous release" — 15–30 min of full outage-or-degradation for all users, and that path is untested. The Defender classifies this as "a gap, not a deliberate accepted risk," i.e. the plan's author agrees it is unhandled.
- **Evidence:** Defender's answer to Adversary Q2/Judge Q3: no feature flag, rollback untested, previous-release redeploy is the only path.
- **Better way:** Not dual-stack-forever — a bounded transition inside the same two sprints. Ship one release where session middleware remains in the code behind a config flag while `/login` starts issuing JWTs and the JWT middleware runs first (fall through to session check). Rollback becomes a config flip (seconds, no redeploy), and the flag plus dead session code is deleted in a cleanup release once JWT auth has soaked for a week. Redis is still running until next quarter anyway, so keeping the session path warm for days costs nothing. Test the rollback flip in staging before cutover. This converts a 15–30 min untested rollback into a tested seconds-long one for roughly a day of work.

**Objection 5 — "Keypair generated at deploy time" is either a global-logout-per-deploy bug or an unrotatable key; and omitting `kid` now makes v2 rotation a breaking change.**

- **Problem:** As written, "generated at deploy time, stored in the deployment environment variables" is ambiguous. If the pair is regenerated on each deploy, every deploy invalidates every outstanding token — a global logout per release, which contradicts the 24h-expiry design. If it is generated once and pasted into env vars, the plan has no `kid` header and no JWKS, so the deferred v2 rotation cannot do an overlap window — first rotation is a forced global logout, and emergency rotation (the team's only revoke-all lever) cannot be distinguished from routine rotation.
- **Evidence:** Artifact decision 6 ("generated at deploy time"); Defender's answer to Advocate Q2 confirms key rotation is the de facto revoke-all mechanism, so its ergonomics are operationally load-bearing, not v2 polish.
- **Better way:** Generate the keypair once, out of band; store the private key in the existing secret pipeline; and include a `kid` header in every token from day one plus a static two-entry JWKS-style public-key config in the verifier. That is a few hours of work now and makes v2 rotation (and emergency rotation with an overlap window) non-breaking. Clarify the deploy-time ambiguity in the plan text either way — as written it reads as a per-deploy regeneration.

## Phase 4 — Advocate's Case

### Part 1 — Steelman

The plan's defining virtue is disciplined scope under real constraints: one team, two sprints, no security engineer, and an ops forcing function (Redis decommission) negotiable by weeks, not quarters. Every decision the Adversary attacks is a deliberate trade of tail risk against delivery risk, and several strengths go beyond what the Defender articulated:

1. **Zero-dependency auth hot path is an availability win, not just an ops convenience.** Today a Redis outage is a total auth outage for 40k DAU on every request. Post-plan, request verification needs only a public key in memory: auth survives Redis loss, Postgres blips, and network partitions to stateful infra. The Adversary's refresh-token fix quietly re-attaches a database to the auth lifecycle; the plan as written detaches auth from all stateful infra, which is the strongest version of the stated goal.

2. **Simplicity is itself a security property for this team.** Refresh-token rotation done wrong (no reuse detection, mishandled token families, a `/refresh` endpoint with a race in the SPA interceptor) is a well-known source of real vulnerabilities. A team with no security engineer shipping the minimal, widely-understood design (signed token, expiry check) has a smaller misimplementation surface than the same team shipping rotation semantics in the same two sprints.

3. **The plan is not "no revocation," it is coarse revocation.** Emergency key rotation via the existing env-var pipeline (30-60 min, exercised deployment path) is a real revoke-all lever. For the mass-theft and key-leak scenarios, that lever is the correct one regardless of whether per-user revocation exists.

4. **Single cutover minimizes the dual-auth window, which is itself an attack and defect surface.** Two live auth paths with a fall-through mean forgotten fallback bugs, ambiguous audit logs, and a doubled test matrix. Decision 5 buys a bounded, one-time cost (one forced re-login) to avoid an open-ended one.

5. **RS256 and minimal claims are forward-looking choices that cost nothing now** and pre-position for service decomposition (public-key verification without secret distribution) and avoid stale-authorization bugs (permissions re-read from the user row, per the Defender's Q1 answer, so the coarse `role` claim is not the whole authorization story).

### Part 2 — Answers to the Adversary's objections

**Objection 1 (revocation).** I dispute the scope of the problem and the better way, and concede a narrow core. The Defender's own risk assessment (Judge Q1 answer) is that 24h irrevocable tokens are *tolerable for regular users* and uncomfortable *for admins*. The Adversary generalizes an admin-specific finding into a whole-design defect. The evidence also shows no compliance SLA and "a handful" of revocations a quarter, mostly offboarding, and offboarded staff are the admin population. The proportionate fix is therefore per-role expiry: admin tokens get 15-minute expiry (one conditional at issuance, zero server state, zero new endpoints); admins are few and internal, so hourly re-login is acceptable UX. That directly retires the "fails customer security review" quote, which was about admin exposure. Against the Adversary's better way: "one table, one endpoint, an interceptor change" understates it. It also requires rotation/reuse semantics, a concurrent-refresh mutex in the fetch wrapper, and new failure modes on the auth path, and it re-couples auth to Postgres, surrendering strength 1 above. Concession: instant kill for a *compromised regular user* account does drop from minutes to up-to-24h. Given the Defender's stated tolerance for that class and its rarity, that is an acceptable, explicitly-priced risk, not a defect.

**Objection 2 (mobile).** I dispute the problem's characterization. Adding refresh tokens later is *additive, not breaking*: the access-token contract (Bearer JWT, signature + `exp` verification) is unchanged when a `/refresh` endpoint appears beside it. Mobile in v1.5 gets a long-lived refresh token in Keychain/Keystore and consumes access tokens exactly as the web client does; no client rework, no middleware rework, one new endpoint. So the claimed "auth rework at the worst possible time" is actually "one endpoint next quarter, informed by real mobile UX requirements" (refresh lifetime, biometric re-auth policy) that do not exist yet. Building the refresh contract now, web-first, guessing at mobile requirements, is exactly the speculative design the two-sprint envelope cannot afford, and the Defender's Q2 answer says next quarter's displaced work would be the mobile support itself.

**Objection 3 (localStorage + XSS).** I dispute the magnitude and part of the better way; I concede the persistence regression. The honest technical point the objection skips: with the XSS posture described, an attacker who executes JS in the page does not need the token. They can drive the fetch wrapper as the logged-in user in real time; an HttpOnly cookie stops offline exfiltration, not exploitation. So mitigation (b) buys less than claimed, and it breaks the single Bearer-header code path plus adds cookie semantics to `/refresh`. The root fix for this risk class is the XSS posture itself: nonce the CSP, add SRI to the analytics tag, audit the two `dangerouslySetInnerHTML` sites. That work is cheap, is required under *any* auth architecture including today's sessions, and I endorse adding it to sprint 2. Concession: localStorage does extend attacker persistence from "while the tab is open" to "24h offline" versus today's HttpOnly session cookie. With Objection 1's per-role fix, the highest-value (admin) tokens age out in 15 minutes, which caps the worst case where it matters most.

**Objection 4 (cutover).** I dispute the better way and concede the actual gap. The gap the Defender flagged is not "no rollback," it is "untested rollback": previous-release redeploy against a still-warm Redis is a real path with a 15-30 min bound. The proportionate fix is to rehearse it: in staging, deploy the JWT release, roll back to the session release, verify sessions authenticate. Hours of work, converts the flagged gap into a tested procedure, changes nothing in the plan's architecture. The Adversary's flag-plus-fall-through alternative reintroduces exactly what decision 5 avoided: two simultaneously-live auth paths, a fall-through that must itself be security-reviewed, a four-state test matrix, and a cleanup release that history says gets deferred. "Roughly a day of work" is the cost of writing the flag, not of validating the matrix. For a one-time migration with a bounded 15-30 min worst case and Redis warm for a full quarter, tested-redeploy is the better risk trade than a third auth configuration. Concession: rollback rehearsal must be added to sprint 2 as an explicit task; the plan text should name it.

**Objection 5 (key management).** Conceded in part, on textual evidence. "Generated at deploy time" as written does read as per-deploy regeneration, which would be a global logout on every release and contradicts the 24h design; the Adversary's reading of the artifact's own words is proof enough. The plan text must say: generated once, out of band, stored via the existing secret pipeline. I also concede emitting a `kid` header from day one: a few lines at issuance, and it is the one thing that cannot be retrofitted onto tokens already in flight when v2 rotation arrives. What convinced me: the asymmetry between cost now (hours) and cost later (first rotation becomes a forced global logout). I dispute only the remainder: the static two-entry JWKS-style verifier config is not needed until a second key exists; verifier-side multi-key lookup is straightforwardly v2 work once `kid` is already in every token.

**Net position:** Keep the plan's architecture (stateless 24h tokens, no refresh in v1, single cutover) with four surgical amendments that stay inside the two-sprint envelope: per-role short expiry for admins, XSS-posture hardening (CSP nonces, SRI, `dangerouslySetInnerHTML` audit), a rehearsed rollback in staging, and key-management text fixed to once-generated keys with `kid` emitted from day one. The Adversary's refresh-token architecture solves a problem the Defender's own risk assessment confines to admins, at the price of the plan's central property: an auth path with no stateful dependency.

## Phase 5 — Adversary's Rebuttal

### Objection 1 (revocation) — SUSTAINED, with a smaller remedy

The Advocate's two strongest counters both fail on the record, and one piece of my own proposal deserves withdrawal.

First, the availability premise. Part 1, strength 1 — "the plan as written detaches auth from all stateful infra" — is contradicted by the Defender's Phase 2 answer to my Q1: "the middleware re-reads the user row for permissions beyond the coarse `role`." Either the JWT middleware keeps that per-request Postgres read, in which case the zero-stateful-dependency hot path never existed and per-user revocation costs zero additional queries; or the plan silently drops the read, in which case fine-grained permissions also go stale for up to 24h — a regression no phase of this debate has priced. The Advocate must pick a horn, and both favor the objection.

Second, the per-role-expiry remedy is self-defeating on its own numbers. A 15-minute admin token with no refresh mechanism means a full re-login every 15 minutes — not the "hourly re-login" the Advocate calls acceptable. That UX gets reverted under internal pressure or worked around within weeks, and the exposure returns. Short expiry without a refresh path is not a stable design point; that instability is exactly why the industry pairs the two. The supporting claim that "offboarded staff are the admin population" is also asserted, not evidenced — the Defender named offboarding and compromised accounts without restricting either to admins.

Third, updating where the Advocate earned it: I withdraw the full refresh-token architecture for v1. The complexity critique — rotation/reuse semantics, a concurrent-refresh mutex in the fetch wrapper, new failure modes on the auth path, no security engineer — is fair. My replacement is strictly smaller: add a `tokens_invalid_before` timestamp to the user row the middleware already reads; verification compares it against the token's existing `iat` claim. Revocation becomes one column update with instant effect for offboarding, compromise, and demotion; it covers all users, not only admins; zero new endpoints, no token families, no client changes; the 24h expiry and localStorage decisions stand untouched. This preserves everything the Advocate defends about the plan while restoring the capability the org uses today. Once the fix is this cheap, the regular-vs-admin scoping debate is moot — a "tolerable" risk is not worth keeping when eliminating it costs one column.

### Objection 2 (mobile) — DROPPED

Convinced by contract additivity: a `/refresh` endpoint added beside an unchanged Bearer-JWT verification contract is additive, not breaking, and mobile builds against it fresh rather than reworking anything. The observation that refresh lifetime and biometric re-auth policy are real requirements that do not yet exist — and that guessing at them web-first is exactly the speculative design a two-sprint envelope cannot afford — completed it. What remained of this objection was Objection 1's revocation problem wearing mobile clothes, and Objection 1 no longer requires refresh tokens to resolve.

### Objection 3 (localStorage + XSS) — DROPPED, with stated contingency

Two things convinced me. The exploitation-versus-exfiltration point is correct: an attacker executing JS in the page drives the live session regardless of where the token sits, so the HttpOnly-refresh-cookie mitigation (b) buys less than I claimed while breaking the single Bearer code path — withdrawn. And the Advocate did not merely parry: they endorsed CSP nonces, SRI on the analytics tag, and the `dangerouslySetInnerHTML` audit as sprint-2 work, which is the root fix under any auth architecture. The contingency, stated plainly: this drop assumes (i) the XSS hardening becomes named plan text, not debate goodwill, and (ii) Objection 1 lands, making a stolen token revocable — the Advocate's own concession that localStorage extends attacker persistence to "24h offline" is precisely what makes revocability the load-bearing residual. If Objection 1 fails, this objection revives as JS-readable + 24h + irrevocable, with the persistence leg already conceded.

### Objection 4 (cutover) — SUSTAINED, narrowed

The Advocate's critique of my remedy is better than their defense of the plan. I concede fall-through: two simultaneously-live auth paths are a real security and test surface, and old session cookies remaining valid alongside JWTs is a regression my own proposal introduced — withdrawn. But that concession does not rescue rehearsed-redeploy, and the Advocate quietly conceded the objection's core by requiring the rehearsal become named plan text. What remains unanswered: (a) 15–30 minutes is the pipeline's happy-path number — a real incident adds detection time, the rollback decision, and locating the correct prior release, and if internal tooling shares this auth, the responders may themselves be locked out; (b) rollback forces a second global re-login on 40k users; (c) a staging rehearsal validates mechanics, not production behavior under load.

Narrowed remedy that answers the dual-path objection in full: ship both middlewares in one binary behind a mutually exclusive mode flag — `auth_mode = jwt | session`, never both live. Two states, each identical to a pure architecture: no fall-through to security-review, no four-state matrix. Rollback becomes a tested config flip in seconds instead of a redeploy under incident pressure. The flag and session code are deleted in the cleanup work the Redis decommission already forces next quarter, so "cleanup gets deferred" has a forcing function attached. If the Advocate shows the exclusive flag costs materially more than the rehearsal they already conceded, I yield; a flag selecting one of two middlewares is not a third auth configuration.

### Objection 5 (key management) — DROPPED as resolved

The Advocate conceded the substance: plan text corrected to once-generated, out-of-band keys in the existing secret pipeline, and `kid` emitted in every token from day one. Their one remaining dispute — deferring the multi-key verifier lookup until a second key exists — is correct and I accept it: `kid` in issued tokens is the only piece that cannot be retrofitted; the verifier is server-side and changes freely at rotation time. Nothing remains contested, provided the concessions land as plan-text amendments rather than transcript-only agreements.

**Net position:** Objections 1 and 4 sustained, each with a remedy smaller than originally proposed (`tokens_invalid_before` column instead of refresh-token architecture; exclusive mode flag instead of fall-through dual-stack). Objections 2, 3, and 5 dropped. The two sustained objections are now cheap enough that rejecting them requires arguing the plan is better off without instant revocation and without a seconds-long rollback — neither of which the Advocate's Phase 4 attempted to argue.

## Phase 6 — Advocate's Surrebuttal

Two objections remain sustained. I concede one and defend one, and close with the consolidated amendment list so the Judge rules on plan text, not transcript goodwill.

### Objection 1 (revocation) — CONCEDED. Accept `tokens_invalid_before`.

What convinced me, precisely:

1. **The dilemma is real and I lose on both horns.** My Part 1 strength 1 ("detaches auth from all stateful infra") is contradicted by the Defender's own Phase 2 answer: the middleware re-reads the user row per request for fine-grained permissions. If that read survives the migration, the zero-stateful-dependency hot path I defended never existed, and checking one more column on a row already fetched costs zero additional queries — my complexity-and-availability argument against server-side revocation evaporates. If the read is instead dropped, fine-grained permissions go stale for up to 24h, a regression no phase priced and I cannot defend. Either horn favors the objection.

2. **My per-role remedy was arithmetically and structurally unsound.** The Adversary is right: I wrote "15-minute expiry" and called the result "hourly re-login" — it is a re-login every 15 minutes, and short expiry without a refresh path is not a stable design point; it gets reverted under internal pressure and the exposure returns. I withdraw the per-role-expiry amendment. I also withdraw the claim that "offboarded staff are the admin population" — it was asserted, not on the record.

The `tokens_invalid_before` column is the remedy I should have proposed: one column on a row the middleware already reads, compared against the token's existing `iat`; instant effect for offboarding, compromise, and demotion; covers all users; no new endpoints, no token families, no client changes; 24h expiry and localStorage stand untouched. Once revocation costs one column update, arguing the plan is better off without it is indefensible, and I will not.

Final substance so the concession lands as plan text, not vaguely:

- Plan must state explicitly that the per-request user-row read is retained in the JWT middleware and the invalidation check rides on it (zero added queries). If a future version removes that read for a fully stateless verifier, revocation semantics get re-decided then — not silently lost.
- Semantics to specify: reject when `iat < tokens_invalid_before`; second granularity suffices; setting the column doubles as a user-initiated "log out everywhere." No clock-skew leeway on this comparison — leeway re-opens the window the column exists to close, and issuer and verifier are the same monolith.
- Failure mode: DB unreachable already fails auth today (the permissions read), so the check adds no new availability dependency. Nothing further to price.

### Objection 4 (cutover) — DEFENDED. The exclusive flag fails the Adversary's own yield test.

The Adversary offered a yield condition: show the exclusive `auth_mode` flag costs materially more than the rehearsal I conceded. It does, for a reason the "a flag selecting one of two middlewares" framing hides: **auth mode is not a server-middleware property. It spans `/login` issuance, logout, and the client.** On the record (Phase 3, Objection 3), the Flask monolith serves the SPA — and that fact cuts for the redeploy, not the flag:

1. **The flag flip desynchronizes server from client; the redeploy structurally cannot.** Roll back by redeploy and the previous release restores server middleware *and* the previous SPA bundle atomically — the client that expects cookies ships with the server that issues them. Flip `auth_mode=session` at runtime and the *new* SPA remains deployed: a login flow written to receive a JWT, store it, and attach Bearer headers, now pointed at a `/login` that sets a cookie and returns no token. Making that flip safe requires a mode-agnostic SPA that detects and handles both cookie and Bearer flows — which is the dual-stack surface the Adversary just withdrew server-side, rebuilt client-side. The two states are not "each identical to a pure architecture"; they are two server states times one client that must tolerate both.

2. **Both modes must be tested in the new binary anyway.** Session-mode-in-the-new-release is not the old release: `/login`, logout, and shared code paths all changed. The redeploy's rollback target, by contrast, is a binary already proven by months of production traffic. A tested flip to an untested combination is not safer than a rehearsed redeploy to a proven one.

The three residual points, answered one at a time rather than left implied:

- **(a) Incident overhead.** Detection time and the rollback decision are identical under both remedies — a flag is not flipped faster than it is decided. The asymmetric delta is decision-to-restored: seconds vs 15–30 min. I answer that delta by strengthening the conceded task, not by changing architecture: the sprint-2 rehearsal deliverable includes a written runbook with the prior release identified and pinned before cutover and pre-agreed rollback criteria, removing "locating the correct prior release" from the incident path. The responder-lockout scenario is conditional and unevidenced — the deploy pipeline authenticates via CI/CD credentials, not product JWTs — but it is a legitimate question, so I put it to the Defender for Phase 10: confirm no ops or deploy tooling rides on product auth. If any does, that is a finding against both remedies equally and must be fixed regardless of cutover design.
- **(b) Second global re-login on rollback.** Symmetric, not a differentiator: flipping `auth_mode=session` also invalidates every outstanding JWT login — users hold Bearer tokens that session middleware does not honor, so 40k users re-authenticate under either remedy.
- **(c) Staging validates mechanics, not production load.** Equally true of a flag flip rehearsed in staging. This argument does not select between remedies; it is a general truth about staging.

Net: (b) and (c) are symmetric, (a) reduces to a seconds-vs-minutes delta answered by a pinned runbook, and against that delta the flag charges a mode-agnostic client, a doubled test matrix in the new binary, and a server–client desync hazard the redeploy cannot have. That is "materially more than the rehearsal," which is the Adversary's stated yield condition. One correction for the record: I did not "quietly concede the objection's core" in Phase 4 — I conceded the gap (untested rollback) explicitly and disputed the remedy. That remains my position: rehearsed, runbook-backed redeploy, named in plan text.

### Consolidated amendments (for the Judge)

The dropped objections carried contingencies; this is the full list I stand behind as plan-text changes, leaving nothing as transcript goodwill:

1. `tokens_invalid_before` column checked against `iat` on the retained per-request user-row read, with the semantics specified above (Objection 1 — conceded).
2. XSS hardening in sprint 2: CSP nonces, SRI on the analytics tag, audit of both `dangerouslySetInnerHTML` sites (Objection 3's stated contingency — its revocability leg is now satisfied by amendment 1).
3. Rollback rehearsal in staging plus pinned-release runbook with pre-agreed rollback criteria, as a named sprint-2 task; Defender to confirm in Phase 10 that no ops tooling depends on product auth (Objection 4 — defended, with the conceded task strengthened).
4. Key-management text corrected to a once-generated, out-of-band keypair in the existing secret pipeline; `kid` emitted in every token from day one; multi-key verifier lookup deferred to rotation time (Objection 5 — resolved).
5. Withdrawn: my per-role admin expiry proposal (superseded by amendment 1).

The plan's architecture — 24h stateless-verification tokens, no refresh in v1, single-release cutover, localStorage — survives intact. What the debate changed is one column, one rehearsal with a runbook, one text fix, and hardening any architecture needed.

## Phase 7 — Judge's Interim: Assessment and Compromises

Assessed on evidence quality, not confidence of delivery. Four objections resolved, one compromise proposed.

### Objection 1 (revocation) — RESOLVED. Adversary won; remedy is the narrowed `tokens_invalid_before` column, which the Advocate conceded.

**Adversary's strengths:** Grounded every claim in the Defender's own record — revocation is used "a handful of times a quarter" (load-bearing, not theoretical), and admin exposure "would likely fail a customer security review" (a v1 defect for a PII SaaS, not a v2 deferral). The dilemma built on the Defender's Q1 answer (per-request user-row read for fine-grained permissions) was the decisive move: either the read survives and revocation costs zero additional queries, or it is dropped and permissions go stale 24h — both horns favor the objection. Best-practice moment of the debate: withdrew their own refresh-token architecture when the Advocate's complexity critique landed, and replaced it with something strictly smaller.

**Adversary's weaknesses:** The original refresh-token remedy did understate its cost (rotation semantics, concurrent-refresh mutex, new auth-path failure modes) — the Advocate was right to attack it, and the Adversary's withdrawal confirms it.

**Advocate's strengths:** The complexity critique of refresh tokens was correct and productively reshaped the remedy. The concession in Phase 6 was precise, itemized what convinced them, and added real value: explicit semantics (`iat < tokens_invalid_before`, no clock-skew leeway, doubles as "log out everywhere"), the requirement that the plan state the user-row read is retained, and the no-new-availability-dependency analysis.

**Advocate's weaknesses:** Part 1 strength 1 ("detaches auth from all stateful infra") was factually wrong on the record. The per-role-expiry remedy contained an arithmetic error (15-min expiry described as "hourly re-login") and a structural one (short expiry with no refresh path is unstable), plus an unevidenced claim ("offboarded staff are the admin population"). All withdrawn — correctly.

**Winning evidence:** Defender's Q1 answer (retained per-request DB read) collapsing the statelessness defense, plus the Defender's own "fails customer security review" risk assessment. Amendment: Advocate's consolidated amendment 1, with the stated semantics. Nothing left to broker.

### Objection 2 (mobile) — RESOLVED. Advocate won; Adversary dropped it.

**Advocate's strengths:** The contract-additivity argument is technically correct — adding a `/refresh` endpoint beside an unchanged Bearer-JWT verification contract breaks no client, so "auth rework at the worst possible time" overstated the v1.5 cost to one endpoint. The point that refresh lifetime and biometric re-auth policy are real requirements that do not yet exist, and guessing at them web-first is speculative design, completed the win.

**Adversary's strengths/weaknesses:** The underlying observation was legitimate — mobile inherits an un-reviewed 24h forced re-login — but as the Adversary themselves recognized, what remained after additivity was Objection 1 in mobile clothes, and Objection 1 no longer needs refresh tokens. The drop was correct.

**Winning evidence:** Additivity of the token contract. One residual for the record: the plan should note that mobile UX review of session length is a known v1.5 input, so the deferral is documented rather than silent. That is a plan-text sentence, not a contested point.

### Objection 3 (localStorage + XSS) — RESOLVED. Advocate won the architecture point; the Adversary's drop-contingencies are both satisfied and become binding plan text.

**Advocate's strengths:** The exploitation-vs-exfiltration distinction is the sharpest technical point in the debate — with XSS on the page, the attacker drives the live session regardless of token location, so the HttpOnly-cookie mitigation buys less than claimed. Correctly identified the root fix (CSP nonces, SRI, `dangerouslySetInnerHTML` audit) as required under any auth architecture, and endorsed it as sprint-2 work rather than merely parrying.

**Advocate's weaknesses:** Conceded the persistence regression (attacker retention extends from "tab open" to "24h offline" vs today's HttpOnly session cookie) — an honest concession that makes revocability the load-bearing residual.

**Adversary's strengths:** The drop was conditional, and the conditions were well-chosen: (i) XSS hardening as named plan text, (ii) Objection 1 landing. Condition (ii) is now satisfied by the Objection 1 concession — a stolen token is revocable via `tokens_invalid_before`. Condition (i) I hereby convert from debate goodwill to a required amendment (Advocate's consolidated amendment 2).

**Winning evidence:** Exploitation-vs-exfiltration, plus the satisfied contingency chain. If a future revision removes the `tokens_invalid_before` check, this objection revives per the Adversary's stated terms — that revival clause should ride in the plan text alongside amendment 1.

### Objection 4 (cutover) — the one live dispute. Advocate won the architecture question; compromise C1 proposed on the residual timing gap.

**Advocate's strengths:** The Phase 6 surrebuttal met the Adversary's own yield condition ("show the exclusive flag costs materially more than the rehearsal"). The desync argument is grounded in an on-record fact (the monolith serves the SPA, established in Phase 3): redeploy restores server middleware and SPA bundle atomically; a runtime `auth_mode=session` flip leaves the new JWT-expecting SPA bundle live against a cookie-issuing `/login`. Making that safe requires a mode-agnostic client — the dual-stack surface rebuilt client-side. Second point also lands: session-mode-in-the-new-binary is an untested combination, while the redeploy target is a binary proven by months of production traffic. The symmetry analyses of residuals (b) (both remedies force a second global re-login) and (c) (staging limits apply to both) are correct.

**Advocate's weaknesses:** Residual (a) is mitigated, not eliminated — a pinned runbook removes "locate the prior release" from the incident path but the decision-to-restored delta remains minutes vs seconds, and "15–30 min" is a happy-path pipeline number under incident pressure. The rehearsal, as proposed, has no pass/fail criterion.

**Adversary's strengths:** Forced two real concessions into the plan (rehearsal as named plan text; pinned runbook with pre-agreed rollback criteria). The incident-pressure critique of the 15–30 min figure is legitimate and unanswered by anything except the runbook. Withdrawing fall-through when its dual-path flaw was shown was the right move.

**Adversary's weaknesses:** The exclusive-flag remedy treats auth mode as a server-only property; it is not, and the Adversary has not answered the client-desync point (Phase 6 is after their last word, but the argument is sound on its face and rests on established record, not new facts). The responder-lockout scenario remains conditional and unevidenced.

**Ruling on the architecture:** exclusive flag rejected, rehearsed redeploy adopted — the yield condition is met. The residual seconds-vs-minutes delta is genuine, so:

**C1 (compromise on Objection 4's residual):** Rehearsed redeploy with a measurable gate and a reopening trigger.
- The Advocate gives up "rehearsal as an unmeasured task": the sprint-2 rehearsal must *time* the full rollback in staging against a written target (proposed: restored auth within 15 minutes of the rollback decision), with the prior release pinned and rollback criteria written before cutover. If the rehearsal cannot meet the target, the exclusive-flag question reopens before cutover — not after an incident.
- The Adversary gives up the exclusive `auth_mode` flag and the residual (a) objection, contingent on the gate existing.
- The artifact gains: a tested, bounded rollback with a pass/fail number instead of a hoped-for one, and no mode-agnostic client surface.
- Condition attached: the Defender must answer in Phase 10 whether any ops or deploy tooling authenticates via product auth. If yes, that is a finding against both remedies equally (the Advocate said this; I agree) and must be fixed independently of cutover design.

### Objection 5 (key management) — RESOLVED by mutual concession; nothing contested.

**Adversary's strengths:** Caught a genuine textual defect ("generated at deploy time" reads as per-deploy regeneration → global logout every release) and the one non-retrofittable item (`kid` in issued tokens). **Advocate's strengths:** Conceded on textual evidence without wriggling, and correctly narrowed the remedy — multi-key verifier lookup is server-side and deferrable until a second key exists, which the Adversary accepted. **Winning evidence:** the artifact's own wording; the cost asymmetry (hours now vs forced global logout at first rotation). Amendment: Advocate's consolidated amendment 4, verbatim. Both sides conditioned resolution on plan-text landing; that condition carries to Phase 11.

### Summary for Phases 8–10

Resolved: Objections 1, 2, 3, 5. One compromise on the table: C1 (Objection 4). Phases 8 and 9 should accept or reject C1 specifically — the four resolutions are closed and their amendments (Advocate's consolidated list 1, 2, 4, plus the mobile-deferral note from Objection 2) are not up for re-litigation, only for the Defender's feasibility check in Phase 10. Phase 10 must also answer the ops-tooling-on-product-auth question attached to C1.

## Phase 8 — Advocate on Compromises

**C1 (Objection 4 residual: rehearsed redeploy with timed gate and reopening trigger) — ACCEPT.** The compromise keeps everything I defended — no exclusive flag, no mode-agnostic client, single-cutover architecture intact — and asks only that the rehearsal I already conceded carry a pass/fail number (restored auth within 15 minutes of the rollback decision) with a pre-cutover reopening trigger; converting a hoped-for bound into a measured one strengthens my own remedy rather than trading it away, and the trigger fires in staging before cutover, where reopening the flag question would be legitimate anyway if the redeploy path cannot meet its number.

For the record on the Judge's four resolved points, none of which I re-litigate:

- **Objection 1 resolution — accepted.** My Phase 6 concession stands as written, including the amendment-1 semantics (retained user-row read stated in plan text, `iat < tokens_invalid_before`, no clock-skew leeway).
- **Objection 2 resolution — accepted**, including the Judge's residual: the plan-text sentence documenting mobile session-length UX review as a known v1.5 input is a fair addition I endorse.
- **Objection 3 resolution — accepted**, including conversion of the XSS-hardening contingency into binding amendment 2 and the revival clause riding alongside amendment 1; that clause is the honest price of my exploitation-vs-exfiltration win.
- **Objection 5 resolution — accepted**; amendment 4 verbatim, with multi-key verifier lookup deferred to rotation time as agreed.

Both C1 and the resolutions remain contingent on the Defender's Phase 10 answer to the ops-tooling-on-product-auth question, which I raised and the Judge attached; if any deploy tooling rides on product auth, that is a defect to fix under any cutover design, not grounds to reopen C1.

## Phase 9 — Adversary on Compromises

**C1 (Objection 4 residual: rehearsed redeploy with timed gate and reopening trigger) — ACCEPT.** I set the yield condition in Phase 5 — show the exclusive flag costs materially more than the rehearsal — and the Advocate's client-desync argument met it: auth mode spans `/login`, logout, and the SPA bundle, so a runtime flip to `auth_mode=session` leaves a JWT-expecting client live against a cookie-issuing server, and making that safe rebuilds client-side the dual-stack surface I had already withdrawn server-side; that argument rests on the on-record fact that the monolith serves the SPA, not on new claims, so I honor the condition and withdraw the flag. What C1 adds is exactly what my residual (a) demanded in substance: the 15–30 min figure stops being a hoped-for happy-path number and becomes a measured pass/fail gate (restored auth within 15 minutes of the rollback decision, prior release pinned, criteria written before cutover), and — decisively — if the rehearsal misses the target, the flag question reopens *before* cutover rather than being discovered during an incident. A rejected remedy that automatically revives when the accepted one fails its own number is the strongest form my objection could survive in. Accepted as stated, including the attached condition: the Defender's Phase 10 answer on ops/deploy tooling authenticating via product auth is load-bearing, and a "yes" there is a defect to fix under any cutover design, not grounds to relitigate C1.

For the record on the Judge's four resolutions, none re-litigated:

- **Objection 1 — accepted.** The `tokens_invalid_before` remedy is my own narrowed proposal; the Advocate's amendment-1 semantics (retained user-row read stated in plan text, `iat < tokens_invalid_before`, no clock-skew leeway, doubles as "log out everywhere") are stricter than what I asked for, and I endorse them verbatim.
- **Objection 2 — accepted.** I dropped it on contract additivity in Phase 5; the Judge's residual (plan-text sentence naming mobile session-length UX review as a known v1.5 input) documents the deferral I worried was silent, which is all that remained of the objection.
- **Objection 3 — accepted.** Both of my stated drop contingencies are satisfied and hardened: XSS work is now binding amendment 2, and the revival clause riding in plan text alongside amendment 1 is precisely the enforcement mechanism I asked for when I said the drop must not rest on debate goodwill.
- **Objection 5 — accepted.** Amendment 4 verbatim; the multi-key verifier deferral was already agreed in Phase 5. My only condition — concessions land as plan text, not transcript — carries to Phase 11, where the Judge has already placed it.

## Phase 10 — Defender's Weigh-In

Feasibility and appetite, per surviving item. Short version: I would implement all of it; nothing here threatens the two-sprint envelope.

**C1 (rehearsed redeploy with timed gate) — would implement.** The rehearsal itself is half a day in staging; the runbook (pinned prior release, written rollback criteria) is an afternoon of writing plus a review. The 15-minute restored-auth target is realistic: the pipeline's 15–30 min spread is dominated by image pull and rolling restart, and pinning the exact prior release ahead of time removes the slowest human step. If staging shows we cannot hit 15 minutes, I accept the reopening trigger — better to have that argument before cutover than during an incident. Total cost: about one day of sprint 2. Appetite: high; this converts my own flagged low-confidence point into a tested procedure.

**C1's attached question — ops/deploy tooling on product auth: No.** Deploys authenticate via CI/CD credentials (pipeline service account); the admin panel used by support rides on product auth, but it is not needed to execute a rollback. Kubernetes and pipeline access are SSO-based, separate from product JWTs. So responder lockout does not apply to the rollback path. Caveat for the plan text: the internal admin panel *does* use product auth, so during any auth outage support tooling degrades — worth one sentence in the runbook, not a design change.

**Amendment 1 (`tokens_invalid_before`) — would implement.** The middleware does retain the per-request user-row read (fine-grained permissions require it), so the check is one extra column on a row already fetched: a migration, one comparison in the middleware, and a one-line admin action to set it. Roughly a day including tests. The specified semantics (`iat < tokens_invalid_before`, second granularity, no leeway, doubles as "log out everywhere") are all implementable as stated; issuer and verifier are the same process, so no skew concern. This also quietly restores the support workflow we'd have lost, which I undervalued in the original plan. Appetite: high.

**Amendment 2 (XSS hardening in sprint 2) — would implement, with one scope note.** SRI on the analytics tag and the `dangerouslySetInnerHTML` audit are cheap (hours). CSP nonces are the real cost: our analytics vendor's snippet injects child scripts, so moving to a nonced, `'strict-dynamic'` CSP needs a test pass across the SPA — call it two to three days, not hours. I still commit to it in sprint 2; if the vendor snippet fights the nonce policy, the fallback is hash-based allowlisting for that one tag, and I will say so in the plan rather than silently shipping a weaker CSP.

**Amendment 4 (key management text + `kid`) — would implement.** The "generated at deploy time" wording was genuinely ambiguous; the intent was generate-once, but the Adversary read the text as written and the text was wrong. Fix: generate once out of band, store in the existing secret pipeline, emit `kid` from day one. Hours of work. Appetite: high — the per-deploy-regeneration reading would have been a production bug if an ops engineer had implemented the sentence literally.

**Mobile-deferral note (Objection 2 residual) — would implement.** One sentence in the plan naming mobile session-length UX review as a v1.5 input. Free.

**What I am not signing up for:** nothing on the surviving list is rejected. The debate's earlier, heavier remedies (refresh-token architecture, exclusive `auth_mode` flag, HttpOnly refresh cookie) are all withdrawn or rejected by the Judge, and I agree with those outcomes — each would have cost multiples of the surviving amendments for marginal additional risk reduction. Net added scope across everything: roughly 4–5 days inside sprint 2, which fits without displacing the cutover work.

## Phase 11 — Judge's Final Report

# Debate Review: JWT Migration Plan

## Agreed changes

All five items below have three-way convergence: proposed or conceded in debate, accepted by both Advocate (Phase 8) and Adversary (Phase 9), and confirmed implementable by the Defender (Phase 10). Ready to act on as plan-text amendments.

1. **`tokens_invalid_before` revocation column** (Objection 1). One column on the user row the JWT middleware already reads per request; reject when `iat < tokens_invalid_before`; second granularity; no clock-skew leeway; doubles as user-initiated "log out everywhere." Plan text must state explicitly that the per-request user-row read is retained and the check rides on it. Restores instant revocation for offboarding, compromise, and demotion — the capability the org uses a handful of times a quarter and the original plan silently deleted. Defender: ~1 day including tests.

2. **XSS hardening in sprint 2** (Objection 3's contingency, now binding). CSP nonces, SRI on the analytics tag, audit of both `dangerouslySetInnerHTML` sites. Defender's scope note stands: nonced CSP is 2–3 days (analytics vendor snippet injects child scripts); fallback is hash-based allowlisting for that one tag, named in the plan rather than silently shipped weaker.

3. **Rollback rehearsal with timed gate** (C1, replacing Objection 4's exclusive flag). See Compromises below. ~1 day of sprint 2.

4. **Key-management text fix + `kid`** (Objection 5). Keypair generated once, out of band, stored in the existing secret pipeline; `kid` emitted in every token from day one; multi-key verifier lookup deferred until a second key exists. The "generated at deploy time" wording was a latent production bug — Defender confirms the literal reading (per-deploy regeneration → global logout every release) was not the intent but was what the text said. Hours of work.

5. **Two documentation sentences.** (a) Mobile session-length UX review named as a known v1.5 input (Objection 2 residual). (b) Runbook note that the internal admin panel rides on product auth, so support tooling degrades during any auth outage (Defender's Phase 10 caveat). Free.

Also agreed: a **revival clause** rides in plan text alongside amendment 1 — if a future revision removes the `tokens_invalid_before` check, Objection 3 (localStorage + XSS) reopens on the Adversary's stated terms, since revocability is the load-bearing residual behind that drop.

The plan's core architecture survives: RS256 24h stateless-verification tokens, no refresh tokens in v1, localStorage on web, single-release cutover.

## Contested points

**Nothing remains contested.** Every objection resolved with an explicit position from all three roles:

- Objection 1 (revocation): Adversary won; Advocate conceded in Phase 6 after the user-row-read dilemma collapsed the statelessness defense and their per-role-expiry remedy failed arithmetically. Remedy is the Adversary's own narrowed proposal.
- Objection 2 (mobile): Advocate won on contract additivity; Adversary dropped it in Phase 5.
- Objection 3 (localStorage + XSS): Advocate won the architecture point (exploitation-vs-exfiltration); Adversary's drop contingencies both satisfied and made binding.
- Objection 4 (cutover): Advocate won the architecture question (client-desync argument met the Adversary's yield condition); residual timing gap settled by C1, accepted by both sides.
- Objection 5 (key management): mutual concession; nothing was contested after Phase 5.

The heavier remedies — v1 refresh-token architecture (withdrawn by Adversary, Phase 5), HttpOnly refresh cookie (withdrawn, Phase 5), per-role admin expiry (withdrawn by Advocate, Phase 6), exclusive `auth_mode` flag (withdrawn by Adversary, Phase 9) — are all off the table by their proposers' own hands, not by fiat.

## Compromises

One compromise was proposed in Phase 7; its fate:

**C1 — rehearsed redeploy with timed gate and reopening trigger** (Objection 4 residual).
- *Terms:* Sprint-2 staging rehearsal must time the full rollback against a written target — restored auth within 15 minutes of the rollback decision — with the prior release pinned and rollback criteria written before cutover. If the rehearsal misses the target, the exclusive-flag question reopens before cutover. Advocate gives up the unmeasured rehearsal; Adversary gives up the flag and residual (a).
- *Phase 8 (Advocate):* ACCEPT. The gate strengthens their own conceded remedy; the trigger fires pre-cutover where reopening would be legitimate anyway.
- *Phase 9 (Adversary):* ACCEPT, honoring their own Phase 5 yield condition — the client-desync argument showed the flag rebuilds dual-stack surface client-side. Called the reopening trigger "the strongest form my objection could survive in."
- *Phase 10 (Defender):* Would implement; ~1 day total; 15-minute target realistic (pipeline spread dominated by image pull + rolling restart; pinning the release removes the slowest human step); accepts the reopening trigger.
- *Attached condition — ops tooling on product auth:* Answered **No**. Deploys use CI/CD service-account credentials; Kubernetes and pipeline access are SSO-based. Responder lockout does not apply to the rollback path. The admin panel does use product auth — handled by the runbook sentence in agreed change 5b, not a design change.

C1 stands accepted with its condition discharged.

## Judge's recommendation

**Adopt the plan with all five agreed amendments.** Reasoning:

- The amendments fix the three defects the debate proved on the record — an actively-used revocation capability deleted (with the Defender's own "would likely fail a customer security review" admission), an untested rollback on the auth path of a 40k-DAU product, and key-management text whose literal reading was a global-logout-per-deploy bug — at a total cost the Defender prices at 4–5 days inside sprint 2, without displacing cutover work or slipping the Redis decommission.
- Every heavier alternative was withdrawn by its own proposer after argument, not overruled. That is the strongest evidence available that the surviving remedy set is the right size: the Adversary's `tokens_invalid_before` column delivers the revocation outcome of refresh tokens at a fraction of the complexity, and C1 delivers a measured rollback bound without the mode-agnostic client the flag would have forced.
- The one number I flagged as unverified — the 15-minute rollback target — is exactly what the C1 gate exists to test, and the reopening trigger means a miss surfaces in staging, not in an incident.

Residual risks the user should accept knowingly: a stolen *regular-user* token remains live until revoked or expired (up to 24h if theft goes unnoticed — mitigated but not eliminated by amendment 1), and mobile inherits the 24h model until v1.5 refresh tokens, now a documented rather than silent deferral.

## Your decision

You are choosing between:

1. **Amended plan (recommended):** original architecture + the five agreed changes. Cost: ~4–5 days added to sprint 2. All three debate roles endorse this outcome.
2. **Original plan unamended:** ships faster by ~a week, but knowingly ships no per-user revocation (Defender: fails customer security review for admins), an untested rollback path, and key-management text whose literal implementation is a per-deploy global logout.
3. **Heavier variants the debate rejected:** v1 refresh tokens (mobile-ready now, at the cost of rotation semantics a team with no security engineer must get right) or the exclusive `auth_mode` flag (seconds-long rollback, at the cost of a mode-agnostic client and a doubled test matrix). Choose these only if you disagree with the withdrawal reasoning in Phases 5, 6, and 9.
4. **Conditional path built into option 1:** if the C1 rehearsal misses the 15-minute gate in staging, the flag question reopens automatically before cutover — you will face a narrower version of this decision then, with a measured number in hand.
