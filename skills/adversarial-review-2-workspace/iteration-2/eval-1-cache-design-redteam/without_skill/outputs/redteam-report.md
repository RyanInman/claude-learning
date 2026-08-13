# Red-team review: session-cache-design.md

Target: `session-cache-design.md` (session pricing cache for `/checkout/quote`).
Review lens: the two stated nightmares — serving a wrong price, and taking down the shared Redis cluster.

## Severity scale

| Severity | Meaning |
|---|---|
| Critical | Can charge a customer the wrong price, or can take down Redis / checkout. Block arch review sign-off until fixed. |
| High | Likely production incident under a realistic event (Redis outage, promo blast, traffic growth). Fix before rollout. |
| Medium | Gap that turns a small incident into a big one, or an unverifiable claim. Fix before 100%. |
| Low | Hygiene. Fix when convenient. |

## Findings

Each finding has a stable ID. The re-check checklist at the bottom maps IDs to pass criteria.

---

### F-01 (Critical) — `KEYS session:*:pricing` on the shared cluster is a meltdown trigger

`KEYS` is O(N) over the entire keyspace and blocks the Redis event loop while it scans. This cluster also serves rate limiting and feature flags, so one `promo_changed` event stalls every keyspace consumer at once. At ~200k session keys plus everything else on the cluster, a single scan can block for hundreds of milliseconds to seconds; rate-limit checks and flag reads time out; checkout and unrelated services degrade together. On Redis Cluster topology, `KEYS` also only sees one node per call, so the delete is incomplete on top of being dangerous.

**Fix direction:** never mass-delete. Put a promo-generation number in the cache key (e.g. `session:{id}:pricing:{promo_epoch}`) and bump the epoch on `promo_changed`; old entries die by TTL. If deletion is truly required, use `SCAN` with a small `COUNT` and `UNLINK`, per node — but versioned keys remove the whole class of problem.

### F-02 (Critical) — No invalidation for catalog prices or tax rates

The invalidation section covers promos only. A catalog price change or tax-rate change leaves stale data live for up to 30 minutes, and the doc's fix for that window is nothing. A price cut is annoying (you undercharge); a price increase or tax correction means quoting — and presumably charging — the wrong amount. This is nightmare #1 realized by design, not by bug.

**Fix direction:** either (a) subscribe to catalog/tax change events the same versioned-key way as F-01, (b) revalidate price-bearing fields at order placement (see F-03), or (c) shrink the TTL for the price fields specifically and document the accepted staleness window with business sign-off.

### F-03 (Critical) — No revalidation at the point of charge

The doc caches "pricing context" and computes totals locally, but never states that the final order placement re-prices against source-of-truth. If the quote path and the charge path both read the cache, every staleness bug (F-02, F-05, F-06) becomes a wrong charge, not just a wrong display. If the charge path already re-prices, most staleness findings drop a level — but the doc doesn't say, and an arch review will ask.

**Fix direction:** state explicitly that `/checkout/confirm` (or equivalent) re-prices from downstream services, or re-validates a cache-entry version/hash before charging. One sentence in the doc; large blast-radius reduction.

### F-04 (High) — Mass invalidation causes a thundering herd on downstream services

Even with a safe deletion mechanism, invalidating all ~200k session entries at once means every active session's next quote is a miss. All of them fan out to catalog, promo engine, and tax service simultaneously — three services that, post-rollout, will be sized for ~cache-miss traffic only. A routine promo publish becomes a self-inflicted DDoS of your own downstreams.

**Fix direction:** versioned keys plus lazy refill spreads the herd only slightly; add jitter (serve-stale-while-revalidate, or stagger epoch adoption over 1–2 minutes) and confirm downstream capacity for a full-miss stampede. Also ask: does every promo change actually affect every session? Scoping invalidation to affected SKUs/segments may shrink the herd by orders of magnitude.

### F-05 (High) — Promos expire mid-session but the cache doesn't know

A promo valid at first quote is cached for 30 minutes. If it expires at minute 10 (flash sale, midnight boundary), quotes at minute 11–30 still apply it. `promo_changed` may not fire for time-based expiry at all — expiry is often implicit, not an event. This is a wrong-price path independent of F-02.

**Fix direction:** store the earliest promo-expiry timestamp in the hash and treat the entry as expired at `min(TTL, earliest_promo_expiry)`; or have the local total computation check promo validity windows.

### F-06 (High) — Session-ID-only key ignores pricing inputs that change mid-session

Tax depends on shipping address; promos can depend on cart contents, coupon entry, or customer segment. All of these can change mid-session, but the key is session ID only and the entry is written once. Change your shipping state after the first quote and you get the old state's tax rate for up to 30 minutes.

**Fix direction:** enumerate every input to the cached pricing context; for each, either include it in the key, invalidate the entry when it changes (delete-on-write from the session's own mutation paths is a single-key `DEL`, cheap and safe), or prove it cannot change within a session.

### F-07 (High) — Sizing has zero headroom and eviction policy is unexamined

40KB × 200k sessions = 8GB — exactly the stated free capacity. That leaves no room for: Redis per-key overhead (~10–15% on hashes), replication buffers, fragmentation (real RSS often 1.3–1.5× dataset), traffic growth, or a marketing spike. When the cluster hits `maxmemory`, behavior depends on eviction policy: `allkeys-lru` starts evicting rate-limit counters and feature flags (breaking unrelated systems silently); `noeviction` fails writes cluster-wide. Either way the shared tenants pay for this feature's growth. This is nightmare #2 with a slow fuse.

**Fix direction:** measure real per-entry size from the 5% rollout, target ≤50% of free memory, shrink the payload (40KB per session is a lot — cache only cart-relevant SKUs, not broad catalog slices), and strongly consider a dedicated Redis (or at least a dedicated maxmemory-limited logical DB/tier) so checkout growth cannot evict rate limiting.

### F-08 (High) — Kill switch may live inside the thing that's on fire

Feature flags are served from the same Redis cluster. The rollback plan for "Redis is melting down" is a feature flag read... from the melting cluster. If flag reads fail closed (flag off) you're safe by accident; if they fail to last-known-value or default-on, you cannot turn the cache off during the exact incident that requires it.

**Fix direction:** confirm the flag client's failure semantics; ensure `cache_pricing_v1` defaults to off on flag-fetch failure, or add an env-var/deploy-level kill switch that doesn't depend on Redis.

### F-09 (High) — "Fallthrough is the current behavior" is false after rollout

Pre-rollout, downstreams handle 100% of quote traffic. Post-rollout at steady state they handle only misses. Capacity planning, autoscaling baselines, and connection pools will quietly shrink to match. A Redis outage then delivers a step-function of full traffic to downsized services — plus, without a circuit breaker, every request first burns a Redis connect/timeout before falling through, so p95 goes up, not back to 480ms. "No circuit breaker needed" is exactly backwards.

**Fix direction:** add a circuit breaker with a short Redis timeout (e.g. 20–50ms) that fails fast to downstream; pin minimum downstream capacity at full-traffic levels or document load-shedding; load-test the cold path at 100% traffic.

### F-10 (Medium) — Invalidation depends on unspecified event-delivery guarantees

If the `promo_changed` consumer misses an event (redeploy, lag, at-most-once delivery), stale promos persist until TTL with no detection. The doc names no delivery guarantee, no consumer-lag alert, and no reconciliation.

**Fix direction:** state the delivery guarantee; alert on consumer lag; the versioned-key design from F-01 also helps here because a missed bump is observable (epoch in Redis vs. epoch in promo engine).

### F-11 (Medium) — Rollout plan can't observe the failure modes that matter

One day at 5% then straight to 100% tests almost nothing this review worries about: at 5%, memory footprint is ~400MB (F-07 invisible), the invalidation herd is 5% sized (F-04 invisible), and a day may not include a single promo publish or a Redis blip. There are also no stated success/abort criteria and no metrics named (hit rate, staleness age, Redis memory, quote-vs-confirm price mismatch count).

**Fix direction:** define exit criteria per stage (error rate, price-mismatch rate = 0, memory projection under target); add 25%/50% stages; trigger at least one controlled promo invalidation during rollout; add a dashboard before enabling the flag. A quote-vs-source-of-truth shadow comparison at 5% is the cheapest way to prove "no wrong prices."

### F-12 (Medium) — No schema versioning on the cached hash

At 100%, a deploy that changes the hash layout has old-format entries read by new code (and, during the deploy, vice versa). Silent misparse of pricing data is a wrong-price vector.

**Fix direction:** put a schema version in the key suffix or a `v` field checked on read; treat mismatch as a miss.

### F-13 (Low) — First-quote latency and downstream errors are cached without qualification

The design caches whatever the three downstream calls return on first quote. A degraded downstream returning partial/default data (e.g. empty promo set during a promo-engine incident) gets frozen for 30 minutes. Also, two concurrent first quotes both fan out and both write — harmless for correctness, worth a note so nobody "fixes" it with a lock later.

**Fix direction:** only cache fully-successful fan-out results; on partial failure, serve without caching.

---

## Summary

| ID | Severity | One-liner |
|---|---|---|
| F-01 | Critical | `KEYS` scan on shared cluster blocks Redis; use versioned keys, never mass-delete |
| F-02 | Critical | Catalog and tax changes have no invalidation path — stale prices up to 30 min |
| F-03 | Critical | Doc never says the charge path re-prices; staleness may become wrong charges |
| F-04 | High | Full invalidation stampedes catalog/promo/tax with ~200k simultaneous misses |
| F-05 | High | Time-expiring promos stay applied from cache after expiry |
| F-06 | High | Key omits mid-session-mutable inputs (shipping address → tax, coupons) |
| F-07 | High | 8GB estimate consumes 100% of free memory; eviction policy can break rate limiting |
| F-08 | High | Kill switch (feature flag) lives on the same Redis it must rescue |
| F-09 | High | Post-rollout Redis outage sends full traffic to shrunken downstreams; no breaker |
| F-10 | Medium | `promo_changed` delivery guarantee, lag alerting, reconciliation unspecified |
| F-11 | Medium | 5%-for-a-day rollout can't surface memory, herd, or staleness issues; no exit criteria |
| F-12 | Medium | No schema version on the hash; deploys can misparse cached pricing |
| F-13 | Low | Partial downstream failures can be cached; concurrent first quotes double-write |

Counts: 3 Critical, 6 High, 3 Medium, 1 Low.

The Criticals share one root cause: invalidation is designed around a single event type and a dangerous primitive. Versioned/epoch keys (F-01) plus charge-time revalidation (F-03) plus explicit invalidation for all three data sources (F-02) resolve the wrong-price nightmare; F-07/F-08/F-09 together are the Redis-meltdown nightmare.

---

## Re-check protocol

After you revise the doc, re-check like this:

1. Update the doc.
2. Ask: "re-check session-cache-design.md against redteam-report.md" (or name specific IDs: "re-check F-01, F-07").
3. The reviewer verifies each ID against its pass criterion below and flips its status. A finding closes only if the revised doc states the mechanism, not an intention ("we'll handle invalidation" does not close F-02; "catalog publishes `price_changed`; consumer bumps the pricing epoch" does).

| ID | Pass criterion (what the revised doc must state) | Status |
|---|---|---|
| F-01 | Invalidation mechanism contains no `KEYS`; mass-delete replaced by versioned keys or documented per-node `SCAN`+`UNLINK` | Open |
| F-02 | Explicit invalidation or bounded-staleness decision for catalog prices AND tax rates, with the staleness window signed off | Open |
| F-03 | Charge/confirm path re-prices from source of truth, or validates entry version before charging | Open |
| F-04 | Herd math: expected miss burst after invalidation vs. downstream capacity; mitigation (jitter, scoped invalidation, stale-while-revalidate) | Open |
| F-05 | Entry expiry = min(TTL, earliest promo expiry), or per-quote promo-window check | Open |
| F-06 | Enumerated list of pricing inputs; each is in the key, invalidated on mutation, or proven immutable per session | Open |
| F-07 | Measured entry size, projected peak memory ≤ stated fraction of free memory with headroom, and named eviction policy / isolation decision | Open |
| F-08 | Flag-read failure mode documented as fail-closed, or Redis-independent kill switch added | Open |
| F-09 | Redis client timeout value, circuit breaker (or explicit justified rejection), and cold-path load-test plan at 100% traffic | Open |
| F-10 | Event delivery guarantee named; consumer-lag alert; detection path for missed invalidations | Open |
| F-11 | Staged rollout with per-stage exit criteria and named metrics, including a wrong-price detection signal | Open |
| F-12 | Schema version in key or hash field, mismatch treated as miss | Open |
| F-13 | Cache-write happens only on fully successful fan-out | Open |
