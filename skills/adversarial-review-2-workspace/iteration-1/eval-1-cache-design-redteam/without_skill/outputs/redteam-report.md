# Red-team: session-cache-design.md

Target: `session-cache-design.md` (session pricing cache for `/checkout/quote`).
Focus per request: wrong prices and Redis meltdown. Every finding has an ID, a severity, and a re-check step. Run the re-check steps after each revision; the checklist at the end tracks status.

Severity scale:
- **Critical** — can charge a customer the wrong price, or can take down the shared Redis cluster.
- **High** — likely production incident or defeats the design's goal.
- **Medium** — degrades correctness, operability, or the rollout under realistic conditions.
- **Low** — worth a line in the doc; unlikely to hurt alone.

---

## Critical

### F1. `KEYS session:*:pricing` blocks the shared cluster
**Severity: Critical (Redis meltdown — the exact nightmare).**
`KEYS` is O(N) over the whole keyspace and blocks the Redis event loop while it scans. The cluster also serves rate limiting and feature flags, so one `promo_changed` event stalls rate-limit checks and flag reads for every service on the cluster. At 200k sessions plus the other tenants' keys, the scan runs long enough to trip client timeouts fleet-wide. The follow-up `DEL` of ~200k keys (~8GB) blocks again.
**Fix direction:** drop delete-on-event entirely. Embed a promo version (or config epoch) in the cache key or in the hash, bump the version on `promo_changed`, and let old entries die by TTL. If a scan is ever unavoidable, use `SCAN` with `UNLINK` — but versioning makes invalidation O(1).
**Re-check:** the doc contains no `KEYS` command anywhere, and invalidation is O(1) (version bump or TTL expiry), not a keyspace walk.

### F2. Catalog price and tax changes never invalidate the cache
**Severity: Critical (wrong prices).**
The only invalidation trigger is `promo_changed`. A catalog price change or a tax-rate change serves the old price for up to 30 minutes to every active session. That is a direct wrong-price-at-checkout path, and for tax it is a compliance problem, not just a UX one.
**Fix direction:** either (a) subscribe to catalog/tax change events with the same versioning scheme as F1, or (b) state explicitly, with sign-off from pricing owners, that a 30-minute staleness window is acceptable for catalog and tax — and shorten the TTL to match what they accept.
**Re-check:** the doc names every upstream source of price change (catalog, promo, tax) and gives each one either an invalidation path or an explicitly accepted staleness bound.

### F3. Cache key ignores everything that changes pricing within a session
**Severity: Critical (wrong prices).**
The key is session ID only, and the hash is written once on the first quote. Anything the shopper changes mid-session that affects pricing — shipping address (tax jurisdiction), applied coupon, currency, cart contents that trigger a different promo tier — still hits the 30-minute-old hash. Example: shopper gets a quote, changes shipping state, requotes; tax rate is the old state's for up to 30 minutes.
**Fix direction:** include the pricing-relevant inputs in the key (e.g. hash of address+coupon+currency), or invalidate the session's entry on any cart/address/coupon mutation. The doc must enumerate which session mutations reprice.
**Re-check:** the doc lists every in-session action that changes pricing inputs and shows how each one misses or invalidates the cache.

---

## High

### F4. Sizing has zero headroom on a shared cluster
**Severity: High (Redis meltdown path).**
40KB × 200k sessions = ~8GB — exactly the stated free capacity. Redis per-key overhead, fragmentation, and any traffic above "peak" push it past free memory. The eviction (or OOM) then lands on the cluster's other tenants: evicted rate-limit keys and feature flags, or a stalled cluster. Peak session count also grows; 8GB free today is not 8GB free at Black Friday.
**Fix direction:** budget for overhead and growth (rule of thumb: plan for ≤50% of free memory), shrink the payload (40KB per session is large — cache only the fields the total needs), or move to a dedicated cache instance/keyspace with its own maxmemory and eviction policy.
**Re-check:** projected footprint including Redis overhead is ≤50% of free memory at forecast peak, or the cache runs on capacity isolated from rate limiting and flags.

### F5. Kill switch lives inside the failure it must stop
**Severity: High.**
Feature flags are served from the same Redis cluster. If this cache melts the cluster (F1, F4), the `cache_pricing_v1` flag read fails too — the one lever meant to stop the incident is unavailable during the incident.
**Fix direction:** give the flag a safe local default (cache off) when the flag read fails, or serve the kill switch from a source independent of this cluster.
**Re-check:** the doc states what the service does when the flag itself is unreadable, and the answer is "cache disabled."

### F6. "No circuit breaker needed" is wrong for slow Redis and for stampedes
**Severity: High.**
Fallthrough equals today's behavior only when Redis fails fast. Two cases where it doesn't:
1. **Slow Redis:** every request pays the Redis timeout *plus* the three downstream calls — strictly worse than today, at 100% of checkout traffic.
2. **Mass invalidation stampede:** a `promo_changed` wipe (or Redis restart) sends all ~200k active sessions to catalog, promo, and tax simultaneously. After running cached for weeks, those services will have been implicitly re-sized for post-cache traffic; the surge is a self-inflicted downstream outage.
**Fix direction:** short (single-digit ms) Redis timeout with a breaker that stops querying Redis after repeated failures; make invalidation gradual (versioning per F1 lets old entries expire over the TTL window instead of all at once); confirm downstream capacity for a 100%-miss burst.
**Re-check:** the doc states the Redis timeout, the breaker behavior, and the worst-case downstream QPS on a full cache wipe, with confirmation the three services absorb it.

### F7. Event-driven invalidation has a lost-event and a race window
**Severity: High (wrong prices — promos specifically).**
Two holes even if F1's mechanism is fixed:
1. **Lost/lagging event:** if the consumer is down or behind, expired promos keep applying for up to 30 minutes with no bound stated and no detection.
2. **Write-after-delete race:** a request reads pricing from the promo engine just before the change, the consumer deletes keys, then the in-flight request writes its stale snapshot back — a stale entry that survives the invalidation.
**Fix direction:** versioned keys (F1) close the race — a stale writer writes to a dead version. State the acceptable consumer lag and alert on it.
**Re-check:** the invalidation design shows why a concurrent read-then-write cannot resurrect stale data, and consumer lag has a stated bound plus an alert.

---

## Medium

### F8. Quote/charge consistency is unspecified
**Severity: Medium (escalates to Critical if the charge path differs).**
The doc caches the *quote* path. It doesn't say what prices the final charge uses. If capture reprices via live downstream calls, quote and charge can diverge within a session — the shopper sees one total and pays another. If capture uses the cached total, F2/F3 staleness flows into the actual charge.
**Fix direction:** state the contract: either the charge honors the quoted total (with a quote ID / price token), or requoting at capture is explicit and surfaced to the shopper.
**Re-check:** the doc names the price source at capture time and the behavior when it differs from the quote.

### F9. Rollout plan has no success criteria and a blunt ramp
**Severity: Medium.**
"5% for a day, then 100%" defines no metrics gating the jump: no hit-rate target, no p95 comparison, no price-mismatch counter, no Redis memory/latency watch. 5%→100% is also a 20× step onto a shared cluster — the memory math in F4 was never tested above 5%.
**Fix direction:** define go/no-go metrics (p95, cache hit rate, Redis memory and p99 command latency, downstream error rate, quote-vs-recompute mismatch rate) and add an intermediate step (5% → 25% → 100%) since memory scales with rollout percentage.
**Re-check:** each ramp step has named metrics with thresholds, and one of them is a price-correctness signal, not just latency.

### F10. No observability for staleness or invalidation
**Severity: Medium.**
Nothing in the doc measures the two nightmare conditions. Without a hit/miss counter, a cache-age histogram, an invalidation-lag gauge, and a sampled quote-vs-live-recompute comparison, the first detection of wrong prices is a customer complaint.
**Fix direction:** add those four signals; the shadow comparison (recompute a small sample of cached quotes against live downstream calls, alert on mismatch) directly guards the wrong-price nightmare.
**Re-check:** the doc lists emitted metrics and includes a mismatch-detection mechanism with an alert.

---

## Low

### F11. 30-minute TTL vs. session length is unstated
**Severity: Low.**
Sessions longer than 30 minutes silently refetch and may reprice mid-session. Probably fine — but say so, since a shopper can see the total change with no action of theirs. (Interacts with F8.)
**Re-check:** the doc states expected session-length distribution and calls the mid-session reprice acceptable.

### F12. Shared keyspace has no namespace or ownership convention
**Severity: Low.**
`session:{id}:pricing` sits in a cluster shared with rate limiting and flags. A prefix collision or a future team's `session:*` pattern operation (someone else's cleanup job) can eat these keys — or this design's pattern (F1) can eat theirs.
**Re-check:** the key prefix is namespaced to this service (e.g. `checkout:pricing:{session}`) and documented in the cluster's keyspace registry, if one exists.

---

## Re-check checklist

Re-run after each revision of the doc. A finding closes only when its re-check line passes against the *current* text.

| ID | Severity | One-line re-check | Status |
|----|----------|-------------------|--------|
| F1 | Critical | No `KEYS` anywhere; invalidation is O(1) version bump or TTL | ☐ |
| F2 | Critical | Catalog + tax changes each have invalidation or signed-off staleness bound | ☐ |
| F3 | Critical | Every in-session pricing mutation (address, coupon, currency, cart) misses or invalidates | ☐ |
| F4 | High | Footprint incl. overhead ≤50% of free memory at forecast peak, or capacity isolated | ☐ |
| F5 | High | Flag-read failure → cache disabled | ☐ |
| F6 | High | Redis timeout + breaker stated; full-wipe downstream QPS computed and confirmed absorbable | ☐ |
| F7 | High | Stale write-after-delete impossible by construction; consumer lag bounded + alerted | ☐ |
| F8 | Medium | Price source at capture stated; quote/charge divergence behavior defined | ☐ |
| F9 | Medium | Ramp steps gated by named thresholds incl. a price-correctness metric | ☐ |
| F10 | Medium | Hit rate, cache age, invalidation lag, and sampled mismatch alert all specified | ☐ |
| F11 | Low | Mid-session reprice at TTL expiry acknowledged as acceptable | ☐ |
| F12 | Low | Key prefix namespaced to the service | ☐ |

**Fastest path to arch-review-ready:** F1+F7 collapse into one fix (versioned keys), F2+F3 into one fix (enumerate pricing inputs; key or invalidate on each), and F4+F5 argue for a dedicated cache instance. Three design changes clear all five Criticals/most Highs.
