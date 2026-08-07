# Debate review: JWT migration plan — what survives

I ran the full four-role debate: a Defender opening, clarifying questions from three fresh-eyes reviewers, a five-objection Adversary case, an Advocate steelman, one rebuttal cycle, and a Judge's final report. Phases 7–8 (compromise brokering) were skipped because every objection was resolved in debate — three dropped by the Adversary, two conceded by the Advocate on the Adversary's own terms. Full transcript: `transcript.md`. Judge's report: `final-report.md`.

## The verdict in one line

The architecture survives — stateless RS256 JWTs, no Redis, two sprints. Six of your write-ups needed no defense change; but the plan as written has two outright defects and three under-priced risks, and the debate converged on seven cheap amendments (days and hours, not sprints) that all three roles endorse.

## What survives intact

- **The core bet.** Nobody in nine phases proposed a different architecture. Every accepted fix is additive. Stateless JWTs, RS256 over HS256, minimal claims, no-Redis end state, two-sprint scope: all stand.
- **No refresh tokens in v1** — survives, but only behind an evidence gate (below). The Adversary opened demanding refresh tokens in v1 and withdrew that demand for lack of written evidence.
- **localStorage** — survives conditionally. The Advocate's point stood: httpOnly cookies stop exfiltration but not XSS-driven request forgery, while adding CSRF machinery and a divergent mobile story. But localStorage is only defensible with the CSP and vendor-isolation amendments landed.

## What did not survive

1. **"Keypair generated at deploy time" is a bug, not a decision.** As written, every deploy mints a new keypair and logs out all 40k users. Fix: generate once, out of band, in the secret store; stamp a `kid` in every token header now (one line, cannot be retrofitted without invalidating tokens). Multi-key verification correctly stays in v2 — the debate established that graceful multi-key acceptance after a key leak would accept attacker-minted tokens.
2. **Client-side-only logout silently regresses three live behaviors:** password change killing other sessions, support force-logout (~10x/year), and role downgrade taking effect on next request. Fix: a `token_version` integer per user in Postgres, embedded as a claim, checked in middleware with a 60-second in-process cache. Revocation latency drops from 24h to ~1 minute with zero Redis. The Judge flags this as the single fix that must not slip in sprint planning — two other resolutions depend on it.
3. **Single-release cutover with an untested 15–30 minute redeploy as the only rollback.** Redis stays running through the cutover window anyway (ops retires it next quarter), so the dual-system cost the plan feared is already being paid. Fix: JWT-first-else-sid middleware for exactly one release, `/login` issuing JWTs behind a flag; rollback becomes a seconds-long flag flip. Agreed sunset: sprint 2 ends with session middleware deleted.
4. **24-hour tokens in localStorage with no CSP and two third-party scripts on authenticated pages.** The debate's sharpest exchange: a `script-src` CSP allowlisting the two vendors does nothing against compromise of those vendors, and `token_version` only covers detected theft — exfiltration is silent. Fixes: CSP with both `script-src` and `connect-src` (the latter blocks beaconing to attacker infrastructure), iframe-sandbox or remove the chat widget and analytics from authenticated pages (time-boxed to two days), SRI hashes if the vendors serve versioned bundles, and a written accepted-risk entry for whatever residue remains.
5. **"Same auth as the web app" for mobile was underspecified.** Mobile users will not accept daily re-login, and deciding by default what one meeting can decide by evidence lost the debate. Fix: sprint 1 includes getting the mobile team's written session-length requirement; spec the `/login` response shape and 401 contract refresh-ready now; agree the `refresh_tokens` Postgres table design on paper. If mobile confirms persistent login (expected), refresh tokens become the committed first post-cutover item, dropping access-token life to ~15 minutes and closing the silent-exfiltration window.

## The Judge's recommendation

Adopt the amended plan (original architecture + the seven changes above). The one structural risk the amendments contain but do not eliminate: the 24-hour token that is irrevocable if theft goes undetected. Only short-lived tokens with refresh eliminate it, and that fix is deliberately gated on the sprint-1 mobile evidence. The Judge's condition: if the gate confirms persistent login, treat refresh-tokens-post-cutover as a commitment, not an intention.

Your options, from the Judge's report:

1. **Adopt the amended plan** (recommended) — fits two sprints, keeps the no-Redis end state.
2. **Amendments + refresh tokens in v1** — closes the exfiltration window now at the cost of most of a sprint; choose only if you weight the vendor-compromise residual higher than the debate did.
3. **Patches without the mobile gate** — severable, but rejects the one point both fresh-eyes reviewers agreed on.
4. **Ship as originally written** — nobody defends this by the end; listed for completeness.

Pitch-ready framing for your team: the plan's core is sound and survived a hostile review; bring it with the seven amendments already folded in, and the two former defects (deploy-logout and silent revocation regression) fixed in the text before anyone else finds them.
