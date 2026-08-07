# Red-Team Result: cache-design.md

Structured debate review (Defender, fresh-eyes Adversary, fresh-eyes Advocate, neutral Judge; 11 phases). Full transcript: `transcript.md` next to this file. Judge's verbatim final report is Phase 11 of the transcript; this is the answer for you.

## Headline answer: will the in-process cache bite us?

**No, provided you build the amended version, not the doc as written.** The in-process choice itself survived five adversarial objections intact. Nothing in the debate argued for Redis or a CDN; every fix landed inside the in-process design. The workload is near best-case for caching: ~500,000:1 read:write ratio, 25MB dataset against worker RAM, product-approved staleness budget. The Adversary's own strongest attacks (expiry stampede, stale deletions, mixed vintages) apply equally to a Redis cache with TTLs, so they are arguments about TTL caching, not about in-process.

The doc as written had two real teeth. Both were caught, both have cheap fixes:

1. **Unpinned `serialized_product` (correctness risk).** The doc doesn't say whether cached values are region-neutral records or rendered, region-priced responses. Cache the rendered response and whichever region populates an entry first serves its prices to every other region for up to 10 minutes, silently. Fix: one sentence pinning cached values as region-neutral records priced post-read, plus one guard test (populate as region A, read as region B, assert region-B pricing).

2. **Two independent TTL clocks (unapproved product behavior).** `all_products` and per-id entries expire independently across 8 workers. Because your writes are bulk imports (correlated, not spread), every import opens a window where list and detail views disagree for the whole import set at once. A daily scheduled anomaly, not a rare coincidence. The PM approved "a product may be 10 minutes old"; the PM never saw this.

## The five agreed amendments (all roles converged; Defender priced at ~1 day total)

1. **Pin cache semantics** + cross-region guard test (fix for tooth 1).
2. **Serve-stale/single-flight background refresh** (~30-50 lines). On soft-TTL expiry keep serving stale while one refresher rebuilds. Kills the expiry latency blip; matters mainly because deploys cold-start all 8 workers at once and align their TTL clocks.
3. **Atomic per-worker catalog snapshot** as the v1 structure (fix for tooth 2). One object holding the id-index and the assembled list, swapped by single reference assignment (atomic under CPython, no read locks), one TTL clock, one refresh path. Key insight from the debate: the design already runs the full-catalog query every TTL interval to rebuild `all_products`, so the snapshot is that same query plus a dict comprehension. It is less code than two coordinated caches, makes list-vs-detail disagreement structurally impossible, and gives deletion drop-out and nonexistent-id answers for free. Notes: transient ~50MB/worker peak during rebuild; cold start pays one ~200-400ms rebuild per worker (same as today's uncached request).
4. **One paragraph to the PM before build.** Two residual anomalies still need sign-off: cross-worker flip-flop (consecutive requests seeing different vintages; no in-process design removes this) and mid-import snapshot vintage (a snapshot cut mid-import serves a mixed but self-consistent state). Also verify one assumption the whole severity analysis rests on: **no cart/checkout path reads these endpoints.** If money flows through them, staleness stops being cosmetic and this review's calculus changes.
5. **Rollout section rewrite.** Metrics (hits, misses, refresh duration, entry age); exit criteria (p95 < 30ms steady state, hit rate > 99% after warmup); one production bulk import observed under canary by host subset via the existing flag. Staging alone can't exercise import-load behavior.

Also documented: `CATALOG_CACHE` is read at process start, so the emergency kill switch is a rolling restart (~2 min), not a flag flip. State that in the doc.

## What did not survive scrutiny (the steelman held)

- **Expiry stampede as a p95 risk.** Arithmetic killed it: one 1-2s rebuild per 10-minute interval affects ~0.2-0.6% of a worker's requests, a p99 event. Baseline comparison is decisive: today every list request pays the import-window cost; the cache converts "everyone pays" into "a fraction of a percent pay." Amendment 2 removes even that.
- **Deletion/takedown risk.** Rolling restart already empties every cache with zero new code; post-flush load equals today's baseline. The proposed cache-epoch mechanism guarded a sub-10-minute takedown SLA that exists nowhere in requirements.
- **Negative-caching gap.** Nonexistent-id misses are primary-key point lookups at exactly today's rate; the cache makes nothing worse.
- **"Staging proves nothing."** Overstated; staging validates the correctness paths including the region guard test. What it can't validate (import-load behavior) is what the production canary in amendment 5 covers.

## Debate integrity note

No contested points reached the Judge and zero compromises were needed. This was earned, not fatigue: of five objections, four were dropped (three because the Advocate accepted the substantive remedy, one on a demonstrated false premise), and the one sustained objection was conceded by the Advocate on two verified proofs (a cost-accounting error and a broken independence assumption about write patterns). The Judge re-checked the arithmetic on both before accepting. Concessions flowed both directions, and both sides corrected the record against their own interest.

## Your decision

1. **Build the amended design (recommended by Judge, Defender agrees).** Original architecture + 5 amendments, ~1 extra day, gated on the PM paragraph and checkout-path verification.
2. **Build the doc as written.** A day faster; keeps the unpinned pricing semantics, the daily post-import inconsistency window, and an unapproved staleness surface. All roles rate this worse.
3. **Redis/CDN instead.** No participant advocated this at any point. Only relevant if checkout-path verification fails badly enough to demand shared, explicitly invalidated state.
4. **Defer the snapshot, ship TTLCache-per-id first.** The Advocate's original position, abandoned after the cost accounting showed the snapshot is net-simpler. Pick only if you dispute that accounting.

Judge's recommendation is option 1. Two five-minute conversations (PM staleness paragraph, checkout-path check) are the only gates before you start building.
