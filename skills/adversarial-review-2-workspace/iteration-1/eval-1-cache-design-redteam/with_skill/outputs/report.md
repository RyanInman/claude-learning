# Red-team report: session cache for checkout service

Artifact: `session-cache-design.md`. Charter: `charter.md`. Three fresh-eyes adversaries
attacked in parallel (lenses: pricing correctness, shared-Redis meltdown,
availability/rollout). 12 raw findings; 2 merged pairs; 0 killed; 10 survive.

## Summary table

| ID | Title | Category | Severity | Status |
|----|-------|----------|----------|--------|
| F1 | Cache sized to exactly the cluster's free memory; peak evicts rate-limit and flag keys or errors all writes | 2 — Redis meltdown | Critical | Plausible |
| F2 | `KEYS session:*:pricing` + mass `DEL` blocks the shared cluster on every promo change | 2 — Redis meltdown | High | Confirmed |
| F3 | One `promo_changed` event flushes 200k sessions: synchronized fallthrough surge to downstreams plus an 8GB Redis rewrite burst | 3 — Checkout availability | High | Confirmed |
| F4 | No Redis read timeout or breaker: a slow (not failing) Redis makes every quote slower than the 480ms baseline | 3 — Checkout availability | High | Confirmed |
| F5 | Catalog price and tax rate changes have no invalidation path; quotes stale up to 30 minutes | 1 — Wrong prices | High | Confirmed |
| F6 | Session-ID-only cache key serves the wrong tax rate after a mid-session shipping address change | 1 — Wrong prices | High | Plausible |
| F7 | Locally recomputed totals diverge from promo/tax engine results, so the quote differs from the charge | 1 — Wrong prices | High | Plausible |
| F8 | Kill switch and fallback both depend on the Redis the cache is melting | 4 — Unsafe ops | High | Plausible |
| F9 | In-flight requests repopulate stale promo data right after invalidation, giving it a fresh 30-minute lease | 1 — Wrong prices | Medium | Confirmed |
| F10 | Rollout gate is "a day at 5%" with no metrics or kill criteria, and 5% cannot exercise the failure modes that matter | 4 — Unsafe ops | Medium | Confirmed |

Severity inflation check: six Highs is a lot, so they are ranked — F2 through F8 appear in
descending order of expected downstream harm. If the arch review can absorb only three
fixes, take F1, F2, F3.

## Findings

### F1 — Cache sized to exactly the cluster's free memory, so peak traffic evicts rate-limit and flag keys
- **Category:** 2 — Shared Redis cluster meltdown
- **Severity:** Critical — Plausible
- **Failure scenario:** 40KB × 200k sessions = 8GB — precisely the stated free capacity. Reach peak (or exceed the estimate: a large cart, a promo-heavy day, sessions above forecast, or the 30-minute TTL outliving real session churn) and the cluster hits maxmemory. Under an `allkeys-*` eviction policy Redis evicts whatever is coldest, including feature-flag keys and rate-limit counters — flags silently read as missing and rate limiting stops enforcing. Under `noeviction`, every write in the cluster starts erroring, including the other tenants'. Either way the blast radius is exactly the harm the charter ranks second.
- **Root cause:** Sizing section (line 23) budgets 100% of free memory with zero headroom, no maxmemory/eviction-policy analysis, and no per-tenant memory bound on the shared cluster.
- **Suggested fix:** Cap the cache below ~50% of free memory (shorter TTL, compressed or trimmed payload, or cache only the hot fields), and state the cluster's eviction policy plus a memory alarm threshold as a rollout precondition.
- **Notes:** Plausible only because the cluster's eviction policy and the real hash-size distribution live outside the artifact (see Verification items). Graded Critical because silently disabled rate limiting and misread feature flags harm users at scale across systems and are discovered only after the damage.

### F2 — `KEYS session:*:pricing` blocks the shared cluster on every promo change
- **Category:** 2 — Shared Redis cluster meltdown
- **Severity:** High — Confirmed
- **Failure scenario:** A merchandiser edits any promo during peak (200k active sessions). The consumer runs `KEYS session:*:pricing` against the shared cluster. `KEYS` is a blocking O(N) scan of the entire keyspace — including every rate-limit counter and feature-flag key, not just cache keys — and Redis is single-threaded, so all other commands queue behind it. The follow-up `DEL` of up to 200k keys (~8GB of hashes) blocks again while Redis frees the memory. During these stalls, rate-limit checks and feature-flag reads time out cluster-wide. Promo edits happen many times per day, so this is a recurring, operator-triggered outage of two unrelated systems.
- **Root cause:** Invalidation section (lines 19-20) specifies `KEYS session:*:pricing` then `DEL` with no mention of `SCAN`, batching, `UNLINK`, or the cost of a full-keyspace scan on a shared single-threaded server.
- **Suggested fix:** Replace delete-by-scan with a version key: invalidation increments `pricing:promo_version`; readers store the version in each hash and treat a mismatch as a miss. No scan, no mass delete — stale entries expire via TTL.
- **Notes:** High, not Critical, because each stall is transient and recoverable — but it recurs on every promo edit. The version-key fix also closes F9's race and removes F3's flush entirely; it is the highest-leverage single change in this report.

### F3 — A single `promo_changed` event flushes every session and sends a synchronized fallthrough surge to all three downstream services
- **Category:** 3 — Checkout latency or availability regression
- **Severity:** High — Confirmed
- **Failure scenario:** Run at 100% with ~200k active sessions cached. A marketer edits one promo; the promo engine publishes `promo_changed`; the consumer deletes all `session:*:pricing` keys. Within the next few seconds, every in-flight session's next quote misses and falls through, so catalog, promo, and tax each receive a near-simultaneous burst approaching full peak quote traffic — traffic they no longer see day-to-day once the cache absorbs it. The burst is worst exactly when promos change: sale launches, i.e. peak checkout load. Downstream services saturate or shed load, quotes slow or fail, checkouts abandon during the highest-revenue window. Repro check against a revised design: change one promo at peak and measure downstream QPS — if it still spikes to uncached levels, the finding stands.
- **Root cause:** Invalidation section (lines 19–20): global flush of every session key on any promo change, with no scoping to affected promos, no jitter/staggering, and no request coalescing on refill. Failure handling (lines 26–27) assumes fallthrough load equals "current behavior," which stops being true once downstreams run at cached traffic levels.
- **Suggested fix:** Invalidate only the promo field (or only sessions referencing the changed promo) instead of deleting whole hashes, and refill with jittered lazy re-fetch plus per-key single-flight so N concurrent misses produce one downstream call.
- **Corroboration:** Two adversaries hit this root cause independently; the second scenario adds the Redis-side cost — repopulation writes up to ~8GB of fresh hashes into the shared cluster in the minutes after the flush, spiking cluster CPU and bandwidth right after the F2 stall.

### F4 — No Redis read timeout: a slow (not failing) Redis makes every quote slower than the 480ms baseline
- **Category:** 3 — Checkout latency or availability regression
- **Severity:** High — Confirmed
- **Failure scenario:** The shared cluster degrades from another tenant's load (rate limiting burst) or from this design's own `KEYS` scan. Redis doesn't error; it answers in 2–5s. "Fall through on any cache error" (line 26) never triggers, so every quote waits the full Redis latency, then — on eventual timeout at whatever the client default is (often seconds) — still pays the three downstream calls. p95 goes from 480ms to multiple seconds across 100% of quotes. The "no circuit breaker needed" claim (lines 26–27) is exactly wrong: without a breaker, a degraded Redis is strictly worse than no cache, and the checkout keeps hammering the sick cluster.
- **Root cause:** Failure handling (lines 26–27) covers only hard errors, specifies no read timeout budget, and explicitly rejects a circuit breaker on the false premise that fallthrough cost equals current behavior.
- **Suggested fix:** Set an aggressive cache-read timeout (e.g. 20–50ms) that counts as a miss, and add a simple breaker that bypasses Redis entirely after N consecutive timeouts.
- **Corroboration:** A second adversary independently flagged that fallthrough without a breaker keeps issuing reads and 40KB writes into the degraded cluster, prolonging the exact meltdown it should escape.

### F5 — Catalog price and tax rate changes serve stale quotes for up to 30 minutes with no invalidation path
- **Category:** 1 — Customers see or pay wrong prices
- **Severity:** High — Confirmed
- **Failure scenario:** At 10:00 a customer starts a session; the cache stores catalog prices and tax rates. At 10:05 merchandising raises an item's price (or a tax rate table updates). Every quote in that session until 10:30 uses the old price and old tax rate. Repro: change a catalog price mid-session, request a quote, compare against the live catalog. Downstream: undercharging is direct revenue loss at scale; a stale tax rate is charged-tax mismatch with the filed rate, which is tax non-compliance, not just a bad customer experience.
- **Root cause:** The Invalidation section (lines 18–20) handles only `promo_changed`. Catalog and tax services have no invalidation hook; their staleness bound is silently the 30-minute TTL, and the design never states that bound is acceptable for prices or legally acceptable for tax.
- **Suggested fix:** Subscribe the same consumer to catalog-price-change and tax-rate-change events, or drop the TTL to a value the pricing and tax owners sign off on as an acceptable staleness bound, and record that sign-off in the design.

### F6 — Session-ID-only cache key serves the wrong tax rate after a mid-session shipping address change
- **Category:** 1 — Customers see or pay wrong prices
- **Severity:** High — Plausible
- **Failure scenario:** A customer in New York starts checkout; the cache stores NY tax rates under `session:{id}:pricing`. They edit the shipping address to an Oregon address (no sales tax) and re-quote. The key is unchanged, the hash is still valid, so the quote applies NY tax to an Oregon shipment. Repro: quote, change shipping address cross-jurisdiction, quote again, compare tax lines. Downstream: overcharged tax the customer can dispute, or undercollected tax the company owes; every mid-session change to a pricing-relevant input (address, currency, customer-tier login) hits the same hole.
- **Root cause:** Line 13: "Cache key includes session ID only." The design assumes pricing context is constant for a session's lifetime, but tax rates are a function of destination, which the customer edits inside the session.
- **Suggested fix:** Include a hash of pricing-relevant session inputs (at minimum shipping jurisdiction and currency) in the cache key, so any change to them is an automatic miss.
- **Notes:** Plausible because the artifact never states which inputs pricing depends on or whether the checkout flow allows mid-session address edits — but address edit during checkout is a standard flow, so treat the verification item as urgent.

### F7 — Locally recomputed totals diverge from promo/tax engine results, so the quote differs from the charge
- **Category:** 1 — Customers see or pay wrong prices
- **Severity:** High — Plausible
- **Failure scenario:** The design moves total computation from the promo and tax services into the checkout service ("compute the total locally", line 12) using cached raw inputs. Take any promo with logic beyond a flat discount — stacking rules, per-customer usage caps, category exclusions, or a tax rule like shipping-taxability by jurisdiction. The local reimplementation applies it differently than the engine that later prices the actual order. Repro: quote a cart hitting a stacking-rule promo via the cache path and via the fallthrough path; the totals differ. Downstream: the customer sees one price at quote and is charged another at capture, or the local logic silently drifts as the promo engine adds rule types — a permanent correctness maintenance burden.
- **Root cause:** Line 12 introduces a second pricing implementation but the design never specifies what "compute the total locally" covers, how promo/tax rule semantics are replicated, or how parity with the engines is verified over time.
- **Suggested fix:** Cache resolved per-item prices and applied-promo/tax amounts (engine outputs), not raw context requiring rule re-evaluation; if raw context must be cached, add a continuous shadow-comparison of cached-path totals against fallthrough totals with an alert threshold.

### F8 — Kill switch and fallback both depend on the Redis the cache is melting
- **Category:** 4 — Unsafe rollout and operations (compounds category 2)
- **Severity:** High — Plausible
- **Failure scenario:** Either F1 or F2 degrades the cluster. Operators reach for the documented control, feature flag `cache_pricing_v1` — but feature flags are served from the same cluster, so flag reads now time out or return stale values, and the cache cannot be turned off. Meanwhile "fall through on any cache error" with "no circuit breaker" means every quote still attempts a Redis read, waits out its timeout, then writes a fresh 40KB hash back into the sick cluster. The cache keeps hammering the cluster it is killing, and the only off switch lives inside the blast radius. Recovery requires an emergency deploy instead of a flag flip.
- **Root cause:** Rollout (line 16) and failure handling (lines 26-27): the kill mechanism is a flag stored in the shared cluster, and the design has no kill path independent of Redis.
- **Suggested fix:** Require a disable path that does not read Redis — a config/env toggle or in-process flag cache with a short local TTL that fails to "cache off" — and add the circuit breaker from F4 so fallthrough stops touching a degraded cluster.
- **Corroboration:** Two adversaries found this independently. Plausible because the flag SDK's behavior (synchronous Redis read vs. local cache with defaults) is outside the artifact — see Verification items.

### F9 — In-flight requests repopulate stale promo data immediately after invalidation, giving it a fresh 30-minute lease
- **Category:** 1 — Customers see or pay wrong prices
- **Severity:** Medium — Confirmed
- **Failure scenario:** T0: session S starts a first quote, reads active promos from the promo engine (slow call, ~480ms). T0+100ms: a promo is deactivated; `promo_changed` fires; the consumer runs `KEYS`/`DEL` — S has no key yet, nothing deleted. T0+480ms: S's request writes the pre-change promo set to Redis with a full 30-minute TTL. Every subsequent quote in S applies the dead promo for up to 30 minutes, after the operator believes invalidation succeeded. Repro: delay a cache-fill write past a promo deactivation and observe the stale write land post-DEL. Downstream: expired discounts honored at scale during exactly the windows (flash-sale ends) when promo changes cluster, and the invalidation mechanism reports success.
- **Root cause:** Lines 10–11 and 19–20: cache fill is read-then-write with no version or timestamp guard, so a delete-then-write race resurrects stale data; the design treats delete-all as sufficient.
- **Suggested fix:** Stamp each cached hash with the promo dataset version (or fetch timestamp) and have readers reject hashes older than the last `promo_changed` version; a single monotonically-increasing `promo_version` key checked on read closes the race without the KEYS sweep.
- **Notes:** Medium because exposure is bounded: only sessions mid-fill at the moment of a promo change, stale for at most one TTL. The same version-key fix as F2 closes it.

### F10 — Rollout gate is "a day at 5%" with no metrics or kill criteria, and 5% cannot exercise the failure modes that matter
- **Category:** 4 — Unsafe rollout and operations
- **Severity:** Medium — Confirmed
- **Failure scenario:** Run the plan as written (line 16). At 5%, the cache holds ~10k sessions (~400MB) and a promo-change flush produces a surge downstreams absorb without symptoms; memory pressure, `KEYS` scan cost, and fallthrough-surge amplitude all scale with population, so the day at 5% passes clean. The flag flips to 100% in one step. The first promo change or Redis hiccup after that hits all traffic at once, and because the design names no metrics (fallthrough rate, cache-read latency, downstream QPS, Redis memory) and no abort thresholds, nobody detects it until checkout conversion drops. Repro check: ask what dashboard and what numeric threshold would have blocked the 100% flip — the artifact names none.
- **Root cause:** Line 16 is the entire rollout plan: one intermediate stage, no monitored metrics, no gate conditions, no staged ramp (5→25→50→100), no scheduled test of a promo-change flush at partial rollout.
- **Suggested fix:** Add a rollout section with a staged ramp, named gate metrics with numeric abort thresholds, and a deliberate promo-invalidation drill at an intermediate stage before 100%.
- **Notes:** Medium on its own — it causes no harm directly — but it is the multiplier that lets F1–F7 reach 100% of traffic undetected.

## Killed findings

None. All 12 raw findings cited the artifact accurately and met the charter's success
criterion. Two pairs were merged as duplicates of one root cause: the invalidation flush
(F3, corroborated by the Redis-rewrite-burst scenario) and the Redis-dependent kill switch
(F8, found by two adversaries).

## Verification items

Plausible findings depend on these facts outside the artifact. Check each before arch review:

1. **F1:** The shared cluster's `maxmemory` value and eviction policy (`noeviction` vs `allkeys-*`), and the real per-session hash size distribution (is 40KB an average or a cap?).
2. **F6:** Whether the checkout flow allows mid-session changes to pricing-relevant inputs — shipping address, currency, logged-in customer tier — and which of those the pricing context depends on.
3. **F7:** Whether promo and tax rules require engine evaluation (stacking, usage caps, jurisdiction rules) or reduce to flat per-item amounts a local computation can apply exactly; and whether the final charge at capture uses the same path as the quote.
4. **F8:** Whether the feature-flag client reads Redis synchronously per request or serves from an in-process cache with a safe default when Redis is unreachable.

## Retest list

Re-run each scenario verbatim against the revised design after fixes land. A fix counts only
when its original scenario no longer fails.

1. **F2:** A merchandiser edits any promo during peak (200k active sessions). The consumer runs `KEYS session:*:pricing` against the shared cluster. `KEYS` is a blocking O(N) scan of the entire keyspace — including every rate-limit counter and feature-flag key, not just cache keys — and Redis is single-threaded, so all other commands queue behind it. The follow-up `DEL` of up to 200k keys (~8GB of hashes) blocks again while Redis frees the memory. During these stalls, rate-limit checks and feature-flag reads time out cluster-wide. Promo edits happen many times per day, so this is a recurring, operator-triggered outage of two unrelated systems.
2. **F3:** Run at 100% with ~200k active sessions cached. A marketer edits one promo; the promo engine publishes `promo_changed`; the consumer deletes all `session:*:pricing` keys. Within the next few seconds, every in-flight session's next quote misses and falls through, so catalog, promo, and tax each receive a near-simultaneous burst approaching full peak quote traffic — traffic they no longer see day-to-day once the cache absorbs it. The burst is worst exactly when promos change: sale launches, i.e. peak checkout load. Downstream services saturate or shed load, quotes slow or fail, checkouts abandon during the highest-revenue window. Repro check against a revised design: change one promo at peak and measure downstream QPS — if it still spikes to uncached levels, the finding stands.
3. **F4:** The shared cluster degrades from another tenant's load (rate limiting burst) or from this design's own `KEYS` scan. Redis doesn't error; it answers in 2–5s. "Fall through on any cache error" (line 26) never triggers, so every quote waits the full Redis latency, then — on eventual timeout at whatever the client default is (often seconds) — still pays the three downstream calls. p95 goes from 480ms to multiple seconds across 100% of quotes. The "no circuit breaker needed" claim (lines 26–27) is exactly wrong: without a breaker, a degraded Redis is strictly worse than no cache, and the checkout keeps hammering the sick cluster.
4. **F5:** At 10:00 a customer starts a session; the cache stores catalog prices and tax rates. At 10:05 merchandising raises an item's price (or a tax rate table updates). Every quote in that session until 10:30 uses the old price and old tax rate. Repro: change a catalog price mid-session, request a quote, compare against the live catalog. Downstream: undercharging is direct revenue loss at scale; a stale tax rate is charged-tax mismatch with the filed rate, which is tax non-compliance, not just a bad customer experience.
5. **F9:** T0: session S starts a first quote, reads active promos from the promo engine (slow call, ~480ms). T0+100ms: a promo is deactivated; `promo_changed` fires; the consumer runs `KEYS`/`DEL` — S has no key yet, nothing deleted. T0+480ms: S's request writes the pre-change promo set to Redis with a full 30-minute TTL. Every subsequent quote in S applies the dead promo for up to 30 minutes, after the operator believes invalidation succeeded. Repro: delay a cache-fill write past a promo deactivation and observe the stale write land post-DEL. Downstream: expired discounts honored at scale during exactly the windows (flash-sale ends) when promo changes cluster, and the invalidation mechanism reports success.
6. **F10:** Run the plan as written (line 16). At 5%, the cache holds ~10k sessions (~400MB) and a promo-change flush produces a surge downstreams absorb without symptoms; memory pressure, `KEYS` scan cost, and fallthrough-surge amplitude all scale with population, so the day at 5% passes clean. The flag flips to 100% in one step. The first promo change or Redis hiccup after that hits all traffic at once, and because the design names no metrics (fallthrough rate, cache-read latency, downstream QPS, Redis memory) and no abort thresholds, nobody detects it until checkout conversion drops. Repro check: ask what dashboard and what numeric threshold would have blocked the 100% flip — the artifact names none.

Plausible findings (F1, F6, F7, F8) join this list once their verification item confirms
them; retest those by re-checking the scenario against both the revised design and the
verified fact.
