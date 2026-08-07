# Debate Review — Round 2: Judge's Adjudication of Contested Points

Round 1 produced four Advocate concessions (settled, no rebuttal needed) and five contested defenses. Critic's rebuttal (delivered late, summarized below) concurs with the judge's independent rulings; its additions are folded in.

## Critic rebuttal summary (round 2)

1. localStorage: partial rebuttal, severity downgraded Critical→High conditional on per-request `token_not_before`. Three deltas stand vs session riding: exfiltrated token is durable offline credential usable after XSS is patched; ridden httpOnly session is killable on detection; CSP mitigation FAILS against the plan's own primary vector (compromised npm deps ship inside the first-party bundle as allowed-origin script). "One code path with mobile" is transport, not storage; mobile uses Keychain/Keystore.
2. No refresh v1: holds, conditional on per-request not_before + `jti` now + refresh tokens landing BEFORE mobile ships.
3. not_before amendment: broken as Advocate described ("checked only on admin path" enforces nothing); salvageable form is write-on-admin-path, READ on every authenticated request, 60s in-process cache. Plan text must say "checked on every request" or the implemented version will be the broken one. Works precisely because it abandons statelessness; must be named. Same-second login-after-kill semantics must be specified.
4. Cutover flag: holds with riders — Redis stays alive until flag deleted (ops retirement date moves; plan must say so), `/login` bcrypt cost profiled/load-tested for re-auth burst, flag tested both directions.
5. Premise: partial rebuttal, downgraded High→Medium. Correction: plan DOES claim shared session store impedes horizontal scaling (defense misquoted it). Post-amendment, JWT and opaque tokens have the same per-request load profile and opaque wins on revocation/key custody/alg surface; but drivers are real, design converges to workable. Verdict must record: the plan reached workable by abandoning the statelessness that was its stated rationale.

## Settled by concession (Advocate could not defend)

1. **D6 "generated at deploy time"** — every deploy invalidates all outstanding tokens; contradicts the plan's own 24h design. Ruled: defect, not tradeoff.
2. **No emergency revocation path anywhere** — worse than status quo (ops can flush a Redis key today). Ruled: defect.
3. **No rollback plan for cutover** — session middleware removed in same deploy; post-cutover auth bug locks users out in both directions. Ruled: defect.
4. **Stale `role` claim unaddressed** — demoted/offboarded users keep old role up to 24h; plan silent. Ruled: gap; acceptable only if accepted explicitly.

## Contested point rulings

### 1. localStorage vs httpOnly ("XSS defeats cookies too via session riding")
Partially valid, does not fully hold. True: XSS on the SPA compromises the user either way; httpOnly is not an XSS cure. False equivalence on blast radius: session riding requires the victim's page open and dies when the XSS is patched or session revoked; an exfiltrated localStorage token gives the attacker durable, offline, off-origin access for the full remaining TTL from their own infra. Under the current plan (24h TTL, zero revocation) exfiltration is strictly worse than riding. The defense becomes tenable only after the kill-switch amendment and/or shorter TTL exist; the plan's actual stated rationale (reload convenience, easy Bearer header) is a convenience argument for a security decision and fails on its own terms.
**Ruling: decision survives only as an explicitly argued tradeoff with compensating controls (CSP, kill switch, shorter TTL when refresh lands). As written: fails.**

### 2. No refresh tokens v1 ("refresh only matters for short tokens; 24h is status quo")
Holds for v1 web, with two corrections. (a) The plan's rationale is wrong: refresh-token state can live in Postgres; it "defeats the purpose" only if the purpose is stateless purity, which is not a real goal; the real goal is retiring Redis. (b) Mobile next quarter makes refresh tokens near-inevitable (daily re-login unacceptable on mobile), so v2 commitment must be explicit, and `jti` must ship in v1 tokens now.
**Ruling: survives amended (explicit v2 commitment + `jti` now + corrected rationale).**

### 3. `token_not_before` kill-switch amendment (load-bearing for #1 and #2)
Works, but the Advocate's phrasing was incoherent as stated. "Checked only on an admin-triggered path" cannot be right: to be effective the check must run on EVERY request; only the WRITE is admin-triggered. Correct form: per-user `token_not_before` column in Postgres, middleware compares token `iat` against it on each request, in-process cache with ~60s TTL bounds the DB load; revocation latency = cache TTL. Consequence the team must own: auth is no longer strictly stateless in the hot path. At 40k DAU this is trivial load and it does not reintroduce Redis.
**Ruling: amendment valid with correction; it is the price of admission for shipping without refresh tokens.**

### 4. Big-bang cutover ("dual-stack doubles surface; flag restores rollback")
Holds. Dual-accept window is the textbook answer, but for a monolith with one client deployed by one team, single-release with the session middleware retained behind a config flag for one release achieves rollback without dual-stack semantics. Forced re-auth of 40k DAU is tolerable if scheduled off-peak with `/login` load headroom verified.
**Ruling: survives amended (flag + off-peak cutover + login load check). As written (middleware deleted same deploy): fails.**

### 5. Premise ("JWT serves ops mandate + mobile; Postgres sessions just relocate state")
Split ruling. The Critic is right that all three stated goals are achievable with Postgres-backed opaque bearer tokens, that 40k DAU has no scaling problem Redis causes, and that the plan never costs this alternative; the "session-table write load on Postgres" counter is weak at this scale. The Advocate is right that the plan's actual drivers (ops retiring Redis, mobile bearer-token auth) are real and JWTs do serve them, and the plan never claimed a perf bottleneck. JWT is a defensible choice, not a required one.
**Ruling: premise survives as a choice, not as a necessity. Plan must add an alternatives-considered section covering Postgres opaque tokens, or the first senior engineer in the pitch meeting will add it for you.**
