
## Agreed changes

All three roles converged on these; they are ready to act on.

1. **Key lifecycle (Objection 1).** Generate the RS256 keypair once, out of band; store it in the secret store, not regenerated env vars. Stamp a `kid` in every token header at issuance. Defer the multi-key verification set to v2 — the Adversary himself concluded that a graceful multi-key path after a key leak would accept attacker-minted tokens, so the Advocate's narrower version is correct, not merely cheaper.
2. **`token_version` revocation (Objection 2).** One integer column per user in Postgres, embedded as a claim, checked in middleware with a 60-second in-process cache. Password change, support lockout, and role downgrade bump it. This restores all three behaviors the plan silently regressed, with zero Redis. **Scope warning, undisputed by anyone:** this fix is load-bearing for the resolutions of Objections 3 and 4. If sprint planning cuts it, those resolutions collapse with it.
3. **CSP in the cutover release (Objection 4).** Both directives: `script-src 'self'` plus the two vendors, and `connect-src 'self'` plus the vendors' collection endpoints. The `connect-src` line is what blocks the common supply-chain case (poisoned vendor script beaconing to attacker infrastructure); `script-src` alone was shown not to cover the named threat.
4. **Vendor isolation on authenticated pages (Objection 4).** Iframe-sandbox the chat widget or remove it from authenticated pages; move analytics off authenticated pages. Time-boxed to two days in sprint 2. During the same box, add SRI hashes if either vendor serves versioned immutable bundles.
5. **Written accepted risk (Objection 4).** Whatever residue survives connect-src plus vendor isolation goes into the plan text: "compromised-vendor token theft, 24h window, mitigations: connect-src, widget sandboxing." This was the Adversary's own fourth acceptable outcome.
6. **Mobile evidence gate in sprint 1 (Objection 3).** One meeting to obtain the mobile team's written session-length requirement. Spec the `/login` response shape and 401 contract refresh-ready now; agree the Postgres `refresh_tokens` table design on paper now. If mobile confirms persistent login (expected), refresh tokens are the first post-cutover item — a schedule commitment, not a v1 scope change.
7. **One-release sid fallback (Objection 5).** JWT-first-else-sid middleware for exactly one release, `/login` issuing JWTs behind a flag; recovery is a flag flip in seconds instead of an untested 15–30 minute redeploy. Sunset condition agreed by both sides: sprint 2 ends with the session middleware deleted.

The plan text must also fix the key-generation wording ("generated at deploy time"), which as written logs out all 40k users on every deploy — conceded by the Defender in Phase 2 as a gap, not a trade-off.

## Contested points

Nothing remained contested after Phase 6. Objections 1, 2, and 5 were dropped in Phase 5; the narrowed Objections 3 and 4 were conceded in Phase 6 on the Adversary's own stated sustain conditions. Two for-the-record disagreements survive, neither blocking:

- **Rework accounting on the SPA 401 path.** Adversary: refresh-then-retry replaces the redirect-to-login path, so deferral throws code away. Advocate: the refresh-retry logic with concurrent-401 queuing is new work in either timeline; only a few redirect lines exist to replace. The Advocate is right on the narrow point, and the Adversary implicitly accepted this by resting the gate on the evidence principle instead.
- **Refresh tokens in v1.** The Adversary withdrew this demand in Phase 5 ("I no longer insist refresh tokens ship in v1 on informal evidence"). The Advocate's rejection of option (a) in Phase 6 is therefore not a live dispute — the sustain condition required any one of four outcomes, and outcomes (b) and (d) were delivered.

## Compromises

None needed — all objections resolved in debate.

## Judge's recommendation

Adopt the amended plan: the original architecture plus the seven agreed changes. My reasoning:

- The debate converged honestly, not politely. Every concession came with a stated reason tied to evidence, both sides changed position when shown wrong (the Adversary on multi-key verification, the Advocate on `script-src`), and the Adversary's sustain conditions were met on his own terms, not diluted ones. I found no point where a side capitulated to end the argument.
- The amendments cost days and hours, not sprints, and preserve both declared constraints: the two-sprint budget and the no-Redis end state. Nobody in nine phases proposed a different architecture; every accepted fix is additive.
- The one structural risk both sides flagged and neither resolved by construction: the two sustained-then-conceded objections share a root — the 24-hour token that is irrevocable if theft goes undetected. The amendments contain it (revocation in 60s if detected, connect-src plus isolation against the main exfiltration path, a written residual) but only refresh tokens with ~15-minute access tokens eliminate it. That fix is deliberately gated on evidence arriving in sprint 1. If the mobile gate confirms persistent login, treat "refresh tokens as first post-cutover item" as a commitment, not an intention — the written accepted risk is priced on that follow-through.
- Watch item for sprint planning: `token_version` must not slip. It is the single cheap fix holding up two other resolutions.

## Your decision

You are choosing between:

1. **Adopt the amended plan (recommended).** Original architecture, seven patches, mobile evidence gate, written residual risk. Fits two sprints; refresh tokens land post-cutover if mobile confirms persistent login.
2. **Adopt the amendments and pull refresh tokens into v1.** Closes the 24-hour silent-exfiltration window now and pre-empts the mobile requirement, at the cost the whole debate agreed is real: the better part of a sprint, pressuring the cutover deliverable. This was the Adversary's original position, withdrawn for lack of written evidence — choose it only if you weight the vendor-compromise residual higher than the debate did.
3. **Adopt the patches but drop the mobile gate.** Saves one meeting and defers session-length to next quarter's mobile design review. Rejects the one point both fresh-eyes reviewers ended up agreeing on — that the evidence is free to obtain now — so I see no case for it, but it is severable.
4. **Ship the plan as originally written.** No one in the debate defends this by the end; the Defender himself classified two of its decisions as gaps. Listed only for completeness.
