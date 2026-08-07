# Debate Review: JWT Migration Plan — What Survives

Four-role debate run to completion (Defender, fresh-eyes Adversary, fresh-eyes Advocate, neutral Judge; 11 phases, one rebuttal cycle, compromise round). Full transcript: `transcript.md` alongside this report. Bottom line: **your core architecture survives intact, but the debate proved three real defects — all fixable in ~4–5 days inside sprint 2.**

## What survives unchanged

- RS256 JWTs with 24h expiry and minimal claims
- No refresh tokens in v1 (mobile gets them in v1.5 — the token contract is additive, so nothing gets reworked)
- localStorage on web, Keychain/Keystore on mobile
- Single-release cutover (the dual-stack / feature-flag alternatives were attacked from both sides and lost)

Every heavier alternative — v1 refresh-token architecture, HttpOnly refresh cookie, per-role admin expiry, exclusive `auth_mode` rollback flag — was withdrawn *by its own proposer* after argument, which is strong evidence the surviving remedy set is right-sized.

## What did not survive: three proven defects

1. **Silent deletion of revocation.** Support/ops kill sessions today (offboarding, compromised accounts, a handful of times a quarter). The plan replaces that with nothing; a stolen or offboarded admin token stays valid up to 24h — which by the plan's own risk framing would fail a customer security review. Decisive argument: the JWT middleware retains a per-request user-row read for fine-grained permissions anyway, so "stateless auth" was never fully true — and revocation therefore costs zero extra queries.
2. **Untested rollback on the auth path.** Single-release cutover with rollback = "redeploy previous release," never rehearsed, 15–30 min happy-path estimate, 40k DAU.
3. **Key-management wording is a latent bug.** "Keypair generated at deploy time" reads literally as per-deploy regeneration → global logout on every release. And with no `kid` header, the first key rotation is a forced global logout.

## Agreed amendments (all three roles converged; Defender priced them)

1. **`tokens_invalid_before` column** on the user row (already read per request). Reject tokens with `iat < tokens_invalid_before`; no clock-skew leeway; doubles as "log out everywhere." Restores instant revocation for all users. ~1 day.
2. **XSS hardening in sprint 2:** CSP nonces (fallback: hash allowlist for the analytics tag), SRI, audit both `dangerouslySetInnerHTML` sites. 2–3 days. Required under any auth architecture given the current posture.
3. **Rollback rehearsal with a timed gate (compromise C1):** staging rehearsal must restore auth within 15 minutes of the rollback decision, prior release pinned, criteria written pre-cutover. If it misses the gate, the flag question reopens *before* cutover. ~1 day. (Verified: deploy tooling uses CI/CD credentials, not product auth — no responder lockout.)
4. **Key-management text fix:** keypair generated once, out of band, in the secret pipeline; emit `kid` from day one; multi-key verifier deferred until a second key exists. Hours.
5. **Two documentation sentences:** mobile session-length UX review named as a v1.5 input; runbook note that the internal admin panel rides on product auth.

Plus a revival clause: if a future revision drops the revocation check, the localStorage/XSS objection reopens — revocability is what made that risk acceptable.

## Sharpest points worth keeping for your pitch

- "Stateless" was overstated: the middleware's retained DB read means revocation is nearly free — this defuses the strongest anti-JWT argument your team will raise.
- HttpOnly cookies would not have saved you from XSS anyway (an attacker executing JS drives the live session; cookies stop exfiltration, not exploitation). The real fix is the CSP work.
- Refresh tokens are additive, not breaking — deferring them to v1.5 costs mobile nothing.

## Judge's recommendation

Adopt the plan with all five amendments (option 1). Alternatives you could still choose: ship unamended (~a week faster, knowingly shipping no revocation and an untested rollback), or the heavier variants (only if you disagree with the withdrawal reasoning in transcript Phases 5, 6, and 9). If the C1 rehearsal misses its 15-minute gate, you revisit the rollback-flag question pre-cutover with a measured number in hand.

**Nothing remains contested** — every objection ended with an explicit win, concession, or accepted compromise. Residual risks to accept knowingly: a stolen regular-user token lives until revoked or expired (≤24h), and mobile inherits the 24h model until v1.5.
