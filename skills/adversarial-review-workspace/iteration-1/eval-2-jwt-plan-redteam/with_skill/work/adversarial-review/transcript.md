# Adversarial Review Transcript

**Artifact:** /Users/admin/claude-learning/skills/adversarial-review-workspace/iteration-1/eval-2-jwt-plan-redteam/with_skill/work/jwt-migration-plan.md
**Date:** 2026-08-07

Append-only. Each phase's content lands under its own heading, transcribed verbatim by the
Defender. No role's text is ever edited after it is written.

---

## Phase 1 — Defender: Opening Statement

I defend `jwt-migration-plan.md`. I did not author it; I argue from the plan's text and will
mark anything it leaves open as unknown rather than invent facts.

**Goal.** Replace Redis-backed session auth with stateless JWTs, for two stated reasons: the
API tier scales horizontally without a shared session store, and the mobile app shipping next
quarter uses the same auth as the web SPA. A third driver is organizational: ops wants to
retire Redis, which is the only stateful infra besides Postgres.

**Why each decision:**

1. *RS256, 24-hour expiry, minimal claims.* RS256 lets any service verify tokens with the
   public key without sharing a secret — this positions the monolith for future service
   splits. The minimal claim set (`sub`, `role`, `exp`, `iat`) keeps tokens small and avoids
   leaking data into a client-readable artifact.
2. *localStorage.* Survives page reloads and integrates with the existing fetch wrapper as a
   `Bearer` header — the same header the mobile app will use, so one auth path serves both
   clients.
3. *No refresh tokens in v1.* The 24-hour expiry matches the current session TTL, so user
   experience is unchanged (one login per day at most). Refresh-token rotation reintroduces
   server state, which contradicts the migration's core purpose.
4. *Client-side logout.* Server-side revocation needs a denylist, which reintroduces the exact
   Redis dependency the plan retires. The plan accepts token validity until expiry as the
   trade.
5. *Single-release cutover.* One deploy, all users re-authenticate once. Avoids running two
   auth systems in parallel and the dual-verification middleware that implies.
6. *One keypair in env vars, rotation deferred.* Smallest thing that works for v1; rotation is
   scoped out, not ignored.

**Decisions I am least sure of.** The plan does not address: XSS exposure of localStorage
tokens; what happens when a user's `role` changes or an account is disabled mid-token-lifetime
(no revocation for 24h); key compromise response with rotation deferred; and whether the
single-release cutover has a rollback path once session middleware is deleted. These are the
soft spots — I expect the attack there and will defend or concede on evidence.

## Phase 2 — Adversary's Questions

1. The plan says the 24-hour expiry "matches our current session TTL." Is the current Redis session TTL a fixed 24 hours from login, or a sliding window that renews on activity? I need to know which behavior users actually experience today.

2. What flows today rely on immediate server-side session invalidation — password change, admin account disable, role demotion, "log out other devices," or any compliance-driven forced logout? For each that exists, what does the plan expect to happen during the up-to-24-hour window a stale token stays valid?

3. On the single-release cutover: after the deploy that removes session middleware and starts issuing JWTs, what is the rollback procedure if a critical defect surfaces — is Redis still running and is the old code path still deployable, or does ops retire Redis in the same release?

## Phase 3 — Defender's Answers

**A1.** Unknown. The plan states only that 24-hour expiry "matches our current session TTL" and never says whether that TTL is fixed-from-login or sliding-on-activity. If the current TTL slides, active users today may effectively never re-login, and the JWT plan would change their experience to a forced daily login. This is a verification item for the plan's author.

**A2.** Unknown. The plan names no invalidation-dependent flow. The only logout it defines is client-side deletion (decision 4), and it acknowledges that server-side logout would need a denylist. It is silent on password change, admin disable, role demotion, log-out-other-devices, and compliance-driven forced logout. If any of these exist today via Redis session deletion, the plan as written leaves stale tokens valid for up to 24 hours and specifies no compensating control.

**A3.** Partially answerable from the text. The cutover decision says the session middleware is removed in the same deploy that starts issuing JWTs — so rollback would mean redeploying the previous release. The plan does not say whether Redis is retired in the same release or later; "ops wants to retire it" states intent, not sequencing. Whether old sessions survive a roll-forward-then-back window (users re-authenticated in between, so their old `sid` cookies are gone or stale) is unaddressed. No rollback procedure is written anywhere in the plan.

## Phase 4 — Adversary's Objections

### Objection 1 — No revocation path breaks flows that must invalidate access immediately (strongest)

**Problem.** A compromised, demoted, or disabled account keeps full API access for up to 24 hours. Password change after a suspected breach, admin account-disable, and role demotion all silently stop working the moment session middleware is deleted, because each relies today on deleting the Redis session. The plan replaces an immediate kill switch with a 24-hour exposure window and names no compensating control — the Defender confirmed this in A2.

**Evidence.** Decision 4 defines logout as client-side deletion only. Client-side deletion does nothing against an attacker who already holds the token — the attacker's copy stays valid until `exp`. The `role` claim is baked in at issue time, so a demoted admin keeps admin for a day. Any app with 40k DAU has password-change; the plan does not mention it once.

**Better way.** The plan's premise — "revocation reintroduces Redis" — is false, because Postgres is already in the stack and already on every write path. Add a `token_version` integer column on the user row and a `ver` claim in the token. Middleware compares them; password change, disable, and demotion increment the column. That is one indexed primary-key read per request against a table Postgres already caches, it revokes instantly, and it retires Redis exactly as intended. If even that read is unacceptable, drop expiry to 15 minutes and accept a 15-minute staleness window — but the plan must pick one; it currently picks neither.

### Objection 2 — localStorage storage turns any XSS into 24-hour offline credential theft

**Problem.** One XSS bug in the React SPA lets injected script read the token and exfiltrate it. The attacker then holds a bearer credential valid for 24 hours, usable from anywhere, and — per Objection 1 — unrevocable. Today's `sid` cookie can at least be HttpOnly (script cannot read it) and server-killed.

**Evidence.** `localStorage` is readable by any script on the origin; that includes every third-party dependency the SPA bundles. This is the textbook argument against localStorage tokens (OWASP token-storage guidance), and the Defender flagged XSS as a known soft spot in the opening statement. The plan's stated reason for localStorage — survives reload, easy Bearer header — is convenience, weighed against nothing.

**Better way.** Split by client. Web: deliver the JWT in an HttpOnly, Secure, SameSite=Lax cookie; the middleware reads the cookie or the `Authorization` header, whichever is present. Mobile: Bearer header with the token in the platform keystore, exactly as planned. This is roughly 20 lines of middleware and preserves the single verification path the plan wants. If the team keeps localStorage anyway, the plan must say why the XSS-theft trade is acceptable — right now the decision is unexamined.

### Objection 3 — "Keypair generated at deploy time" logs out every user on every deploy and makes v2 rotation a breaking change

**Problem.** As written, each deploy can mint a fresh keypair, instantly invalidating every outstanding token — a forced global logout per deploy, which is worse availability than the Redis sessions being retired. Separately, the tokens carry no `kid` header, so when rotation arrives in v2 the verifier cannot tell which key signed a token; rotation becomes another global logout.

**Evidence.** Decision 6: "generated at deploy time, stored in the deployment environment variables." A team that deploys weekly turns the promised once-a-day login into a login on every release; a team that deploys daily makes it worse than that. The claim set in decision 1 (`sub`, `role`, `exp`, `iat`) omits `kid`.

**Better way.** Generate the keypair once, out of band, and store it in the secrets manager the deploy environment already pulls env vars from; deploys reference it, never regenerate it. Add a `kid` header now — it costs one line at issue time and makes v2 rotation a non-event (verifier holds a keyset, old tokens verify against the old `kid` until they expire). Both changes are v1-sized.

### Objection 4 — Single-release cutover has no rollback once session middleware is deleted

**Problem.** If a critical defect surfaces post-deploy — middleware bug, clock skew, mobile-blocking token size, anything — the rollback is "redeploy the old release." But by then users have re-authenticated; their old `sid` sessions are gone or expired, so rolling back forces a second global re-login into a code path that may itself misbehave against whatever Redis state remains. The plan writes no rollback procedure at all, which the Defender confirmed in A3.

**Evidence.** Decision 5 removes session middleware in the same deploy that starts issuing JWTs. Auth is the one subsystem where a bad deploy locks out 100% of users rather than degrading one feature. A3 also confirms Redis retirement sequencing is unstated — "ops wants to retire it" is intent, not a plan step.

**Better way.** Two-phase cutover, still inside the two-sprint budget. Release A: `/login` issues JWTs *and* the middleware accepts both JWT and `sid`; Redis stays up. Bake for one to two weeks while sessions age out naturally. Release B: delete session middleware, then retire Redis as an explicit, dated step. Rollback from Release A is trivial (both paths work); by Release B the JWT path has production mileage. The "dual verification middleware" the plan avoids is an `if` statement, not a system.

### Objection 5 — The 24-hour-expiry UX claim rests on an unverified fact about the current TTL

**Problem.** The plan justifies no-refresh-tokens with "users log in at most once a day, which matches our current session TTL." If the Redis TTL is sliding (renewed on activity) — the common default — active users today effectively never re-login, and this plan converts them to a forced daily login. The UX-parity claim, load-bearing for decision 3, would be false.

**Evidence.** A1: the Defender could not determine from the plan whether the TTL is fixed or sliding. A load-bearing premise the plan's own defense cannot verify is a gap in the plan, not in the defense.

**Better way.** Check the Redis session config before sprint 1 and write the answer into the plan. If the TTL slides, decision 3 must be re-argued honestly: either accept the UX regression explicitly, or adopt short-lived access tokens plus a refresh token — noting that the refresh-token state fits in Postgres (Objection 1's mechanism), so it does not resurrect Redis.

## Phase 5 — Defender's Defense

Before the per-objection answers, the steelman the plan deserves: none of the five objections attacks the plan's goal. Retiring Redis, moving to JWTs, and sharing one auth path with the mobile app survive intact — every objection targets v1 mechanics, and four of the five fixes fit inside the existing two-sprint budget. The plan's instinct to resist server state is also half right: it correctly refuses *session* state per request-path; it only errs in treating one integer of *revocation* state the same way.

**Objection 1 — Concede.** The proof that convinced me is the counterexample to the plan's own premise: decision 4 argues revocation "reintroduces Redis," but a `token_version` integer on the user row lives in Postgres, which the plan already keeps. One primary-key read per request is no worse than today's per-request Redis lookup, so nothing the migration promises is lost. Against that, the failure scenario — a breached or disabled account holding full API access for 24 hours with no kill switch — is not an acceptable trade for an auth system. Adopt the `ver` claim plus `token_version` column, incremented on password change, disable, and demotion.

**Objection 2 — Concede.** HttpOnly removes the token from script reach entirely — a control the SPA's dependency tree cannot undo — and that is the OWASP-documented pattern the plan's convenience rationale never weighed. The objection compounds with Objection 1: as written, the stolen token was also unrevocable. Adopt the split: HttpOnly/Secure/SameSite=Lax cookie for web, keystore plus Bearer header for mobile, middleware accepting either. One condition the better way must absorb: cookie transport reintroduces CSRF surface, so the plan must name its CSRF control (SameSite=Lax plus a custom-header or CSRF-token check on unsafe methods). A fix that swaps a named risk for an unnamed one would repeat the original mistake.

**Objection 3 — Contest the headline, concede the substance.** Contested part: the plan says "One RS256 keypair, generated at deploy time, stored in the deployment environment variables" — a singular keypair persisted in env config. The natural reading is provision-once, and there is no evidence in the artifact that deploys regenerate keys, so "logs out every user on every deploy" overstates what the text establishes. Conceded part: the wording *permits* the catastrophic reading, and key lifecycle is exactly where ambiguity becomes an incident — the plan must state "generated once, stored in the secrets manager, never regenerated by deploys." The missing `kid` I concede in full: decision 1's claim list omits it, it costs one line now, and without it v2 rotation is a forced global logout. That asymmetry — one line now versus a breaking change later — is the proof.

**Objection 4 — Concede.** Precedent convinced me: dual-accept middleware is the standard auth-migration pattern precisely because auth is the one subsystem where a bad deploy locks out 100% of users instead of degrading a feature. The plan's stated reason for a single release — avoiding two parallel auth systems — prices the dual path as a system when it is an `if` statement in one middleware, and prices the no-rollback lockout at zero. Adopt the two-phase cutover; make Redis retirement an explicit, dated step after Release B rather than an ambient intent.

**Objection 5 — Concede as a verification item.** The artifact does not contain the TTL semantics and I will not stipulate them. The premise is load-bearing for decision 3, so: verify whether the Redis TTL is fixed or sliding before sprint 1 starts. If it slides, decision 3 must be re-decided in writing — either accept the daily-login regression explicitly, or move to short-lived access tokens with Postgres-stored refresh tokens, which Objection 1's mechanism already makes cheap.

## Phase 6 — Adversary's Rebuttal

## Phase 7 — Final Report
