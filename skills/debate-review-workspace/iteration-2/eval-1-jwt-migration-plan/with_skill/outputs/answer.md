# Debate review: what survives in jwt-migration-plan.md

I ran the full four-role debate: a Defender opened for the plan, a fresh Adversary and Advocate asked clarifying questions, built cases blind to each other, rebutted, and a neutral Judge ruled. Full transcript in `transcript.md`, Judge's report in `final-report.md`. The user decides — nothing below has been applied to the plan.

## What survives intact

The architecture. The Adversary conceded it "without reservation" in rebuttal:

- Migrating from Redis sessions to stateless JWTs — right answer to the Redis-retirement and mobile-app constraints.
- RS256 over HS256 — future verifiers get the public key, not the signing secret.
- No refresh tokens in v1 — consistent with the stateless goal; no sustained fix requires them.
- Minimal user data in claims, and the two-sprint shape of the work.

## What fell — both debaters ended up agreeing on these

The Advocate conceded four of five objections, each on facts the Defender admitted, so these are consensus amendments, not one side's wishlist:

1. **No per-user revocation is a v1 blocker.** Offboarding, admin suspension, and compromise response all fired last year via Redis key deletion; v1 replaces them with "wait 24 hours or log out all 40k users." Fix: the requirement is "no Redis," not "no Postgres" — add an `auth_epoch` claim checked against the users table per request. One indexed read on a DB most requests already hit.
2. **Key lifecycle must be specified, plus a `kid` header.** "Generated at deploy time," read literally, mass-logs-out every user on each of your 2–3 weekly deploys. Write down generate-once provisioning; add `kid` now so v2 rotation is a config change, not a flag day.
3. **Single-release cutover with an untested rollback loses.** Redis runs until next quarter anyway. One dual-accept release (middleware takes JWT, falls back to reading `sid` sessions; `/login` issues only JWTs) turns a 15–30 minute untested lockout into a safe drain. The Advocate's dual-stack fear collapsed once shown the fallback is read-only with single issuance. Rehearse the rollback in staging regardless.
4. **Add `iss`/`aud` claims and pin `algorithms=["RS256"]`.** The plan designs for multiple verifiers while omitting the claims that make multiple verifiers safe; algorithm confusion is a CVE-documented exploit class. About four lines.

## The one genuinely contested point

**`localStorage` vs. httpOnly cookie.** The Advocate defended `localStorage` only conditionally (keep it if CSP plus sanitizing the two `dangerouslySetInnerHTML` sites become named cutover blockers). The Judge ruled narrowly for the cookie: the hardening `localStorage` depends on doesn't exist and isn't scheduled, and a CSP that allowlists your two vendor CDNs doesn't stop a compromised vendor CDN. The cookie's cost (CSRF tokens for endpoints `SameSite=Lax` misses, ~3 lines of dual token extraction) is small and verifiable; mobile keeps the Bearer path untouched. The Judge would flip this only if CSP-plus-SRI work were already scheduled.

## Judge's recommendation

Amend and ship: all four consensus changes, cookie storage, `auth_epoch`. And re-estimate the timeline honestly — these additions plus a dual-accept release add real scope to sprint 2.

Your options, per the Judge: **A** (all amendments, cookie — recommended), **B** (all amendments, keep `localStorage` with CSP/sanitization as hard cutover blockers plus SRI on the vendor scripts), **C** (ship as written — the record supports nobody choosing this). The pitch writes itself either way: the core idea survived a hard adversarial pass untouched; every finding is an amendment measured in lines, not a redesign.
