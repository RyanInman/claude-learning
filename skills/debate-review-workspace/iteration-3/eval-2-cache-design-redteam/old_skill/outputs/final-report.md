# Judge's Final Report

**Artifact:** /Users/admin/claude-learning/skills/debate-review-workspace/iteration-3/eval-2-cache-design-redteam/old_skill/work/cache-design.md
**Debate transcript:** /Users/admin/claude-learning/skills/debate-review-workspace/iteration-3/eval-2-cache-design-redteam/old_skill/work/debate-review/transcript.md
**Date:** 2026-08-07

This debate converged unusually far. The Advocate conceded, in whole or in part, all five objections; the Adversary withdrew half of one. What remains contested is narrow, and I rule on it below.

## Agreed changes

The Advocate conceded these in rebuttal. Both sides now support them; they are ready to act on.

1. **Pricing contract, as a release gate.** Add the sentence stating where pricing is applied relative to the cache, confirm it against the code, and add a test: with the cache on, the same product requested from two regions must return region-correct prices. The Advocate conceded that steelman point 7 was inference, not evidence, and upgraded this from "editing fix" to release gate before any multi-region production traffic.

2. **Atomic imports.** Adopt the Adversary's fix (a): imports run in a transaction or shadow table and swap at commit, so lazy reads never cache a partial catalog. Take the torn-catalog scenario to the PM in writing regardless, because the one-sentence sign-off plausibly covers "one product is 10 minutes stale" and not "the catalog disagrees with itself across endpoints and workers." The Advocate conceded steelman point 5 overclaimed.

3. **Soft-TTL, per-key rebuild lock, ±60s jitter.** Roughly 15 lines, no infra. The Advocate accepted this as a friendly amendment after the Adversary showed the "herd of eight" bound only holds under sync gunicorn workers, which the design never states. Record the worker class in the design either way.

4. **State the real `/products` contract; cache the neutral list, not a rendered response.** The arithmetic went unanswered: 12k × 2KB is a ~24MB body, so the single rendered `all_products` key is either dead code or wrong results if the endpoint paginates or filters. Cache the full neutral list per worker and slice/filter/serialize per request. Conceded in full.

5. **Instrumentation and a numeric staging gate.** Hit/miss/rebuild-duration counters, a target p95, and a one-day p95 breakdown to confirm Postgres (not serialization) dominates the 180ms. Conceded in full; "measurement has no counterargument" drew no counterargument.

## Dropped objections

- **Objection 3's strong form (thundering herd "re-creates the latency spike"; DB overload).** The Adversary withdrew both claims and said what convinced him: cached DB load is bounded above by the uncached baseline, since every rebuilding request would have hit Postgres anyway, and expiry misses peak at today's 180ms rather than above it. The sawtooth is a tail effect. What survives of Objection 3 is the agreed amendment 3 above, not an architectural objection.
- **The architecture itself was never attacked.** The Adversary explicitly accepted the in-process choice over Redis (steelman point 1), the CDN deferral (point 8), lazy population and the flag rollout shape (point 6, minus "observable"). Nobody argued for different infrastructure at any point. The record shows the dict, the TTL, the lazy fill, and the flag standing on their merits.

## Contested points

**Point A — severity of the region-less cache key (Objection 1).** Adversary: this is a latent correctness bug; the design cannot be correct by accident, the failure is invisible in single-region staging, and the fix cost is asymmetric — one sentence if pricing is applied post-read, but region-keyed caches and memory math × region count if prices are baked in, which is structural. Advocate: it is an unresolved ambiguity, not a wrong decision; both resolutions preserve the architecture and either outcome is a small diff.

**Point B — where the import fix belongs (Objection 2 residual).** Advocate: atomic imports repair the source, protect uncached readers too, and require zero cache changes; non-transactional imports already expose partial state today, so the cache extends an existing window rather than creating one. Adversary: the torn-catalog state across endpoints and workers has no uncached analogue (every uncached read sees one consistent Postgres snapshot), so the cache design owns the exposure and must either fix it or carry the `catalog_version` check itself.

## Rulings

**Point A — Adversary wins on substance; the Advocate's label survives only as vocabulary.** The Advocate's "small diff either way" understates the region-baked branch: 25MB × region count × 8 workers can move the memory budget materially, and the `all_products` scheme would need redesign. The Adversary's asymmetry argument, plus the single-region-staging invisibility, is why this must be resolved before the design is called done, and the Advocate already conceded the operative point by accepting the release gate. Whether we call it "bug" or "ambiguity" changes nothing the user must do.

**Point B — split, with a concrete compromise.** The Adversary is right that the torn catalog is a cache-created state: uncached reads never disagree with themselves. The Advocate is right that the durable fix lives in the import pipeline, which the cache team may not own. Compromise: the design document records atomic imports as a stated precondition of the cache. If the import pipeline cannot be made atomic before rollout, the cache carries the `catalog_version` read-time check as its own mitigation until it can. The Adversary gives up demanding the cache-side check unconditionally; the Advocate gives up shipping on an assumption about another team's pipeline; the artifact gains an explicit dependency instead of a silent one.

## Judge's recommendation

Approve the architecture; require the five agreed amendments; sequence the fact-finding first. Before any code: (1) find where pricing is applied relative to serialization, (2) read the `/products` route for pagination and filter params, (3) run the one-day p95 breakdown. Each is under a day, and each can invalidate a piece of the design on paper — item 3 especially, because if serialization dominates the 180ms, the cache hypothesis itself is wrong and no amendment saves it. Then implement with amendments 1 through 5, treating 1, 2 (per the Point B compromise), 4, and 5 as ship gates and 3 as cheap hardening in the same change.

I recommend this over "ship as written" because the two sustained top objections fail silently: wrong-region prices error nothing, and a torn catalog errors nothing, so the flag protects against neither. The Advocate's own final position asks for the same five conditions; the debate's endpoint is one plan, not two.

## Your decision

- **Option 1 (both sides' converged position, and mine):** Adopt the design plus all five amendments, fact-finding first, ship gates as listed above.
- **Option 2:** Adopt the design as written and ship now. You accept three documented risks: possible wrong-region prices if pricing turns out to be baked into serialization, a torn catalog visible for up to 10 minutes after each bulk import, and a staging week that cannot pass or fail because nothing is measured.
- **Option 3:** Run only the three fact-finds (pricing location, `/products` contract, p95 breakdown) and return for a decision with facts in hand. Cheapest path; defers commitment by a few days.
- **Sub-decision under Option 1:** for the import window, make imports atomic at the source (preferred, fixes uncached readers too) or add the `catalog_version` read-time check in the cache (fallback if the import pipeline cannot change on this timeline).
