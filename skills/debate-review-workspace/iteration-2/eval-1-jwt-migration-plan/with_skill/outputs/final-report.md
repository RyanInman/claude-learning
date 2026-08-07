# Judge's Final Report

**Artifact:** jwt-migration-plan.md — migrate auth from Redis sessions to JWTs
**Date:** 2026-08-06

## Agreed changes

The Advocate conceded four objections in rebuttal. Both sides now support these changes, and each stays inside the plan's architecture:

1. **Per-user revocation via a per-request Postgres check (Objection 1) — v1 blocker.** Add a revocation check in the JWT middleware against Postgres. Both sides agree the plan's real requirement is "no Redis," not "no Postgres," that most authenticated requests already hit Postgres, and that v1 is not shippable without this. The Advocate's own steelman proposed the same lever before conceding. Only the mechanism remains contested (see below).
2. **Key lifecycle written into the plan, plus a `kid` header (Objection 3).** Specify generate-once provisioning explicitly — the literal text "generated at deploy time" would force a site-wide logout 2–3 times a week — and add a `kid` header to issued tokens in sprint 1 so v2 rotation is a config change, not a flag day. The Advocate additionally accepted the secrets-manager home for the keypair, which the Adversary had dropped as a demand; treat it as agreed since both sides now endorse it.
3. **One-release dual-accept cutover plus a staged rollback rehearsal (Objection 4).** The middleware validates a JWT if present, else falls back to reading existing `sid` sessions; `/login` issues only JWTs from day one; the fallback is deleted next release, before Redis retires. The Advocate's dual-stack objection collapsed once the Adversary showed the fallback is read-only with single issuance — the bug class the steelman feared comes from dual issuance, which nobody proposed. Rehearse the rollback in staging regardless.
4. **`iss` and `aud` claims plus an explicit `algorithms=["RS256"]` allowlist (Objection 5).** Conceded without reservation. The plan's own RS256 rationale designs for multiple verifiers while omitting the claims that make multiple verifiers safe. Roughly four lines in sprint 1.

## Dropped objections

- **The secrets-manager requirement inside Objection 3.** The Adversary dropped it after the steelman showed the mass-logout reading is a wording defect, not a design flaw: once generate-once provisioning is written down, env-var storage is acceptable for v1. (The Advocate then volunteered the secrets manager anyway — see Agreed changes — so the drop is moot in practice.)
- **The plan's architectural core was never objected to, and the Adversary conceded it explicitly:** the JWT migration itself, RS256 over HS256, no refresh tokens in v1, minimal user data in claims, and the two-sprint scope all survive intact. The record shows all five objections target specification, not architecture.

## Contested points

**1. Revocation mechanism: `auth_epoch` column vs. account-status flag.**
- *Adversary:* prefer an integer `auth_epoch` embedded as a claim and compared per request, because bumping the epoch also revokes tokens after a password reset without disabling the account.
- *Advocate:* wrote "`auth_epoch` (or account-status) check" and offered no argument for the flag over the epoch. Not actively contested, but never conceded either.

**2. Web token storage: httpOnly cookie vs. `localStorage` with hardening blockers.**
- *Adversary:* store the JWT in an `HttpOnly; Secure; SameSite=Lax` cookie; the middleware accepts cookie or Bearer header so mobile is untouched; CSRF for the uncovered endpoints is library-solved. Accepts the alternative branch — `localStorage` with CSP plus sanitization of the two `dangerouslySetInnerHTML` sites as cutover blockers — but the plan must commit to one.
- *Advocate:* concedes the "reasoned acceptance" premise was factually false, but takes the `localStorage`-plus-blockers fork: it preserves the single Bearer-header code path shared with mobile, avoids CSRF machinery, and once revocation lands (Agreed change 1), a stolen token is no longer unstoppable, breaking the compounding that gave the objection its severity. Explicitly falls back to the cookie if the team will not commit to the CSP blocker.

## Rulings

**1. Revocation mechanism — Adversary wins.** The epoch's advantage (revocation after password reset without disabling the account) directly covers one of the three documented ops procedures — compromise response, used twice last year — at identical cost to a status flag. The Advocate offered no counterargument. Adopt `auth_epoch`.

**2. Token storage — Adversary wins on the evidence, narrowly.** The deciding facts: the hardening the `localStorage` branch depends on does not exist and is not scheduled, and the Adversary's named threat — a compromised vendor CDN — is not stopped by a CSP that must allowlist those same vendor scripts. The Advocate never answered that specific vector. The Advocate's best point, that revocation breaks the compounding, is real but partial: revocation helps only after theft is detected, and XSS token theft is typically silent. Against this, the cookie's cost (CSRF tokens for the endpoints `SameSite=Lax` leaves uncovered, ~3 lines of dual token extraction) is small, mechanical, and verifiable, whereas "CSP shipped and CMS content sanitized" is hardening whose completeness is hard to verify under a two-sprint deadline. If the team was already planning CSP work with subresource integrity for the vendor scripts, the Advocate's branch becomes defensible — that is the one condition under which I would flip this ruling. Both sides pre-endorsed the fork, so choosing the branch is genuinely yours.

## Judge's recommendation

Amend the plan and ship it. Adopt all four agreed changes plus both rulings: `auth_epoch` revocation as a v1 blocker; httpOnly cookie for the web SPA with Bearer-header support unchanged for mobile; generate-once key provisioning written into the plan with a `kid` header; one-release dual-accept with a staged rollback rehearsal; `iss`/`aud` claims and a pinned algorithm list.

Reasoning: this debate produced an unusually clean convergence. The Adversary conceded the architecture; the Advocate conceded four of five objections on the Defender's own factual record; every fix is measured in lines or one release of patience, and none reintroduces Redis. The only judgment call I made against a live position is cookie-vs-`localStorage`, and there the winning evidence (unscheduled mitigations, the unanswered vendor-CDN vector) is factual, not rhetorical. One caution: five amendments plus a dual-accept release add real scope to sprint 2 — revisit the two-sprint timeline rather than absorbing the additions silently.

## Your decision

- **Option A (recommended):** Amend the plan with all five changes, cookie storage, `auth_epoch` mechanism. Re-estimate the two-sprint timeline.
- **Option B:** Same amendments, but keep `localStorage` and make CSP plus sanitization of the two `dangerouslySetInnerHTML` sites named cutover blockers — the Advocate's branch. Choose this only if you will genuinely block cutover on that hardening and can add SRI or equivalent for the two vendor scripts.
- **Option C:** Ship the plan as written. The record gives you no support for this: both debaters agree v1 without revocation is not shippable, and the literal key-lifecycle text forces mass logouts 2–3 times a week.
- **Sub-choice under A or B:** account-status flag instead of `auth_epoch`. The record contains no argument for it; pick it only if you have a reason neither debater raised.
