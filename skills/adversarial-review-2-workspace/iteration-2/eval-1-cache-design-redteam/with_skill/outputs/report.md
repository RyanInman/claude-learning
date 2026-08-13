# Red-team report: session cache for checkout service

Artifact: `session-cache-design.md`. Charter: `charter.md`. Three adversary lenses: pricing
correctness, shared-cluster meltdown, availability/observability. 12 raw findings, 1 merge,
1 seam-sweep addition, 0 killed -> 12 final findings.

## Verdict

As written, the design does not safely achieve its goal: its sizing consumes 100% of the
shared cluster's free memory (meltdown at the first post-rollout peak), and its correctness
rests on an invalidation path that covers only promos and is itself the cluster's largest
operational hazard - both of the stated nightmares (wrong prices, Redis meltdown) are live.

Minimum-changes path (five fixes clear the top findings; the first closes four root causes):

1. **Replace `KEYS`+`DEL` invalidation with version-stamped entries** - store a
   promo/catalog/tax config version in each hash (or in the key) and treat the entry as a
   miss when the current version differs. Closes F-3 (blocking scan), F-4 (stampede),
   F-10 (write-after-delete race), and provides the mechanism for F-2.
2. **Invalidate on catalog and tax changes, not just promos** - subscribe the same version
   counter to `price_changed` and tax-rate events (F-2, F-11).
3. **Cap the cache below ~50% of free memory or give it a dedicated instance**, and confirm
   the shared cluster's eviction policy before rollout (F-1).
4. **Key or invalidate on tax-relevant session inputs** - shipping jurisdiction and cart
   contents (F-6, F-8).
5. **Add instrumentation, a staged rollout with an invalidation drill, and a
   locally-cached kill switch** (F-5, F-7, F-9, F-12).

## Summary table

| Rank | ID | Title | Category | Severity | Status |
|------|----|-------|----------|----------|--------|
| 1 | F-1 | 8GB footprint equals total free memory; evictions hit rate-limit and flag keys | Cluster meltdown | Critical | Confirmed |
| 2 | F-2 | Catalog price and tax changes never invalidate the cache | Wrong prices | Critical | Confirmed |
| 3 | F-3 | `KEYS session:*:pricing` blocks the shared cluster on every promo change | Cluster meltdown | High | Confirmed |
| 4 | F-4 | Delete-all invalidation triggers a synchronized stampede (downstream reads + 8GB Redis rewrite) | Latency/availability | High | Confirmed |
| 5 | F-5 | Kill switch lives on the cluster the cache melts down | Cluster meltdown | High | Confirmed |
| 6 | F-6 | Tax cached before shipping address is known; address change mid-session charges wrong tax | Wrong prices | High | Plausible |
| 7 | F-7 | "No circuit breaker needed" is false once downstreams shed capacity | Latency/availability | High | Plausible |
| 8 | F-8 | Cart mutation mid-session hits a hash that lacks the new item's price; behavior undefined | Wrong prices | Medium | Plausible |
| 9 | F-9 | Zero metrics: a dead or degraded cache is invisible | Silent failure | Medium | Confirmed |
| 10 | F-10 | Write-after-delete race repopulates stale promo data after invalidation | Wrong prices | Medium | Confirmed |
| 11 | F-11 | Time-boxed promos apply past expiry because totals are computed locally | Wrong prices | Medium | Plausible |
| 12 | F-12 | 5%-for-a-day rollout never exercises invalidation or memory at scale; flag-off is itself a stampede | Latency/availability | Medium | Confirmed |

## Findings

### F-1: 8GB cache footprint equals the cluster's total free memory, triggering eviction of rate-limit and flag keys
- **Category:** Shared Redis cluster meltdown
- **Severity:** Critical - Confirmed
- **Failure scenario:** 200k sessions x 40KB = 8GB of payload - exactly the stated free memory, before Redis per-key overhead (hash structures, expiry tracking, ~10-20% extra) and before any traffic growth. At the first peak after the 100% rollout, the cluster hits maxmemory. If eviction policy is `allkeys-lru`, Redis evicts whatever is coldest - including feature-flag keys and rate-limit counters, breaking those systems; if `noeviction`, all writes fail cluster-wide, including rate-limit INCRs. Either way the blast lands on the co-tenants. Repro: load 200k 40KB hashes into a staging cluster with 8GB headroom and observe evictions/write errors on other keyspaces.
- **Root cause:** Sizing section plans to consume 100% of free memory with no headroom, no overhead accounting, no growth margin, and no statement of the cluster's eviction policy.
- **Suggested fix:** Cap the cache's footprint below ~50% of free memory: shrink the payload (store only price-relevant fields, compress, or cap hash size) or cap active cached sessions, and confirm the shared cluster's maxmemory policy before rollout. Better: state that this workload gets its own Redis instance if it cannot fit under the cap.
- **Note:** Grade is Critical despite the eviction policy being unverified because both policy branches produce a co-tenant production outage; the policy only selects which one. The arithmetic comes from the design's own numbers, so the finding stays Confirmed with the policy listed as a verification item.

### F-2: Catalog price and tax-rate changes never invalidate the cache - customers pay stale prices for up to 30 minutes, silently
- **Category:** Customers charged wrong prices; Silent failure
- **Severity:** Critical - Confirmed
- **Failure scenario:** Merchandising raises SKU X from $49 to $79 at 14:00 (or a tax-rate table update lands). Every session that quoted before 14:00 keeps its `session:{id}:pricing` hash for the remainder of its 30-minute TTL and computes totals locally from the old $49 price. At 200k active sessions, thousands of checkouts complete at the wrong price. Nothing errors, no fallthrough triggers, no metric moves - the mismatch surfaces only in finance reconciliation or a repricing audit. The reverse direction (price drop, customer overcharged) is a refund/compliance incident.
- **Root cause:** The Invalidation section handles only the `promo_changed` event. Catalog price changes and tax-rate changes have no invalidation path at all; their only bound is the 30-minute TTL. The design nowhere states that a 30-minute price-staleness window is an accepted business decision.
- **Suggested fix:** Subscribe the same invalidation mechanism to catalog `price_changed` and tax-rate-change events, or store a catalog/tax version stamp in the hash and reject the cache when the current version differs. If the business genuinely accepts 30-minute staleness, write that acceptance and its owner into the design.

### F-3: `KEYS session:*:pricing` on invalidation blocks the shared cluster, stalling rate limiting and feature flags
- **Category:** Shared Redis cluster meltdown
- **Severity:** High - Confirmed
- **Failure scenario:** A promo team edits any promo mid-day. The `promo_changed` consumer runs `KEYS session:*:pricing` against a cluster holding ~200k pricing keys plus every rate-limit and feature-flag key. `KEYS` is O(total keyspace) and blocks the Redis event loop for the full scan; the follow-up `DEL` of up to 200k keys (each freeing a 40KB hash) blocks again while freeing ~8GB. During that stall, every rate-limit check and feature-flag read on the cluster times out: services either fail open on rate limiting (abuse window) or fail their flag reads (unpredictable behavior fleet-wide). Promo changes happen most often during sale events, so the stall lands at peak. Repro: publish one `promo_changed` event with 200k sessions active and measure rate-limit call latency on the shared cluster.
- **Root cause:** Invalidation section specifies `KEYS` + bulk `DEL`, both blocking commands, on a cluster explicitly shared with rate limiting and feature flags.
- **Suggested fix:** Replace key-scan invalidation with a versioned key scheme: include a promo-generation counter in the cache key (`session:{id}:pricing:{promo_ver}`); on `promo_changed`, INCR the counter so old entries miss and expire via TTL. No scan, no bulk delete.
- **Note:** High, not Critical: the stall is severe but self-recovering once the scan and delete complete. It fires deterministically on every promo change, which is why it outranks the conditional High findings below.

### F-4: Delete-all invalidation triggers a synchronized stampede - downstream fallthrough storm plus an ~8GB Redis rewrite burst
- **Category:** Checkout latency or availability collapse; Shared Redis cluster meltdown
- **Severity:** High - Confirmed
- **Failure scenario:** Marketing launches a flash sale, which fires `promo_changed` at the exact moment traffic peaks. The consumer deletes every `session:*:pricing` key - up to 200k at once. Every active session's next quote is a simultaneous cache miss, so the checkout fleet fires 3 x (miss rate) downstream calls within seconds against catalog, promo, and tax services that, post-rollout, have been receiving only a trickle of traffic. All three saturate, quotes time out, checkout is down during the sale the invalidation was announcing. Simultaneously the refill path writes up to ~8GB of fresh 40KB hashes into the shared cluster in minutes, saturating network and replication bandwidth and delaying rate-limit and flag operations; on a replicated setup, the replication backlog overflows and replicas full-resync, doubling the load. Repro: fire one `promo_changed` with 200k warm sessions at peak QPS and measure downstream RPS, quote p95, and co-tenant command latency in the following 60 seconds.
- **Root cause:** Invalidation section: a single event deletes the entire keyspace with no jitter, no staggering, no versioning, and the fallthrough-then-write path synchronizes 200k downstream calls and large writes; promo-change timing correlates with traffic peaks.
- **Suggested fix:** The versioned-key fix from F-3 makes invalidation lazy - old entries become stale-but-present and expire via TTL, so refills spread across each session's next natural quote. Add TTL jitter (30min +/- random 20%) so expiries never synchronize.
- **Corroboration:** Two adversaries independently hit this root cause - one from the downstream-load side, one from the Redis-write side. Merged here; both scenarios must pass at retest.

### F-5: The kill switch for the cache lives on the cluster the cache melts down
- **Category:** Shared Redis cluster meltdown
- **Severity:** High - Confirmed
- **Failure scenario:** The cache exhausts memory or blocks the cluster (F-1, F-3). Operators try to disable it by flipping `cache_pricing_v1` off - but feature flags are served from the same degraded cluster. Flag reads time out or return stale values, so checkout instances keep writing 40KB hashes into the dying cluster. The incident cannot be mitigated by its own designed control; recovery requires a deploy or manual Redis surgery, extending the outage for every co-tenant workload. Repro: in staging, fill the cluster to maxmemory, then attempt to flip the flag and measure how long instances keep writing.
- **Root cause:** Rollout section puts the only off switch behind a dependency that the failure mode it must mitigate takes down; the Failure handling section explicitly rejects a circuit breaker, so no client-side write breaker exists either.
- **Suggested fix:** Require flag clients to cache the last-known flag value locally and fail closed (cache disabled) on flag-read errors, and add a client-side breaker that stops Redis writes after N consecutive cache errors.

### F-6: Tax rate cached before the shipping address is known - wrong tax charged when the address changes mid-session
- **Category:** Customers charged wrong prices
- **Severity:** High - Plausible
- **Failure scenario:** First quote in a session fires before or with a default shipping address (the normal checkout flow: cart -> quote -> enter address). The hash caches tax rates for that initial address. The customer then enters or changes the shipping address to a different tax jurisdiction (OR vs. WA, or cross-EU VAT). Subsequent quotes read the same `session:{id}:pricing` hash - the key is session ID only - and compute tax at the old jurisdiction's rate. The customer is charged the wrong tax; the merchant remits incorrectly, a direct compliance exposure.
- **Root cause:** "Cache key includes session ID only." Tax rates are a function of the shipping address, which is mutable within a session, and no address change invalidates or re-keys the hash.
- **Suggested fix:** Include a hash of the tax-relevant inputs (shipping jurisdiction at minimum) in the cache key, or delete the session's pricing hash on any address change. State which inputs the hash is keyed by and prove each is immutable per session.
- **Plausible because:** depends on whether the first quote can precede final address entry and whether tax rates vary by destination in this system - see Verification items.

### F-7: "No circuit breaker needed" is false - after rollout, full fallthrough is many times today's downstream load, not "same as today"
- **Category:** Checkout latency or availability collapse
- **Severity:** High - Plausible
- **Failure scenario:** The cache runs at ~95% hit rate for weeks; catalog, promo, and tax teams observe low traffic and scale replicas down (or traffic grows into the freed headroom). Then the shared Redis cluster has a failover, a slow `KEYS` scan, or memory pressure from its other tenants. Every quote falls through simultaneously. Downstream services now receive the full pre-cache call volume with post-cache capacity, queue, and time out. Checkout latency exceeds the original 480ms baseline and requests fail - the cache made availability worse than having no cache. Repro: with the cache warm at steady state, black-hole Redis for 5 minutes and verify downstream services absorb 100% of quote traffic within their SLOs.
- **Root cause:** Failure handling: "No circuit breaker needed since fallthrough is the current behavior." Fallthrough is the current behavior only on day one; the design freezes that assumption while the cache's own success invalidates it.
- **Suggested fix:** Add a circuit breaker with load shedding or request coalescing (single-flight per session) on the fallthrough path, and record in the design that downstream teams must keep capacity for 100% fallthrough or the breaker must shed to a degraded quote/queue instead.
- **Plausible because:** depends on whether downstream teams actually reclaim the freed capacity - see Verification items.

### F-8: Cart mutation mid-session hits a hash that lacks the new item's price - behavior is undefined
- **Category:** Customers charged wrong prices
- **Severity:** Medium - Plausible
- **Failure scenario:** The first quote writes the hash from the catalog/promo/tax fetch for that quote's cart. The customer then adds a new SKU and re-quotes. The cached hash has no price for the new SKU, and the design does not say what happens: a full fallthrough (correct but silently erodes hit rate), a per-item fetch (unspecified), or a total computed from incomplete data (wrong price). Any implementation must pick one, and two of the three choices are harmful. Repro: quote a one-item cart, add a second item, re-quote, and check the total and the code path taken.
- **Root cause:** Design section: the hash's contents are scoped to the first quote's inputs, the key is session ID only, and no section defines behavior when cart contents change within the session.
- **Suggested fix:** Specify the miss-on-unknown-SKU behavior explicitly: treat any quote containing a SKU absent from the hash as a full cache miss, refresh the hash, and count it in the miss metrics.
- **Origin:** Added in the seam sweep (boundary between the cached snapshot and mutable session state); no adversary owned this edge. Plausible because the artifact is ambiguous about whether the fetch is cart-scoped.

### F-9: The design defines zero metrics, so a dead or degraded cache is invisible until downstreams saturate
- **Category:** Silent failure
- **Severity:** Medium - Confirmed
- **Failure scenario:** A serialization bug, a key-prefix typo, or eviction pressure drives the hit rate toward zero. Fallthrough masks it: quotes still succeed at the old 480ms, no error is thrown, no alert exists because none is specified. The team believes the latency goal is met; the first signal is downstream capacity pages or the p95 dashboard someone happens to check. Worse, a partial-write bug (hash written without the tax field) surfaces only at reconciliation. Repro check: point the revised design at the question "if hit rate drops from 95% to 0% at 2am, which alert fires?" - today the answer is none.
- **Root cause:** The design (whole document) specifies no hit/miss/fallthrough/eviction metrics, no alerts, and no SLO tied to the cache; fallthrough-on-any-error converts every failure into silence by construction.
- **Suggested fix:** Add a required-instrumentation section: hit rate, fallthrough count by cause (miss vs error), Redis eviction count on this keyspace, and an alert when hit rate drops below a floor or fallthrough QPS exceeds downstream-safe capacity.
- **Note:** Medium on direct outcome (degraded, workaround exists), but it multiplies F-1, F-2, and F-7 by hiding them - fix it in the same pass.

### F-10: Write-after-delete race repopulates stale promo data immediately after invalidation
- **Category:** Customers charged wrong prices; Silent failure
- **Severity:** Medium - Confirmed
- **Failure scenario:** T0: session S starts its first quote and fetches promos (old 20%-off active). T1: promo engine ends the promo and publishes `promo_changed`; the consumer runs `KEYS`/`DEL` and deletes all pricing hashes. T2: session S's in-flight request, holding pre-change promo data, writes `session:S:pricing` to Redis. The dead promo is now cached for a fresh 30 minutes and applied to every subsequent quote in that session - the invalidation the design relies on is defeated by ordinary request timing. The same hole opens whenever the consumer is down or lagging: events are missed, nothing detects it, and stale promos serve until TTL. Reproduce by delaying a first-quote write past the invalidation sweep.
- **Root cause:** Invalidation is a one-shot delete with no ordering guarantee against concurrent cache writes, and no monitoring of consumer lag or delete effectiveness.
- **Suggested fix:** Stamp each cached hash with the promo-config version and treat the cache as invalid when the stamp predates the latest `promo_changed` version; that closes both the race and the consumer-outage gap with one check (same mechanism as F-3's fix). Alarm on invalidation-consumer lag.
- **Note:** Medium: scope is the sessions in flight during the race window plus consumer-outage windows, bounded by the 30-minute TTL.

### F-11: Time-boxed promos stay applied past their expiry because totals are computed locally from the cached hash
- **Category:** Customers charged wrong prices
- **Severity:** Medium - Plausible
- **Failure scenario:** A flash promo ends at 00:00 with no config change afterward - its end time was set at creation, so no `promo_changed` event fires at expiry. A session cached at 23:50 keeps the promo in its hash until 00:20 and the local total computation applies it to every quote in that window. During a high-traffic flash-sale cutoff - exactly when this happens - a burst of orders gets discounts the promo engine would refuse, and the discrepancy only appears in margin reconciliation. Same mechanism applies to effective-dated tax-rate changes.
- **Root cause:** Subsequent quotes "compute the total locally" from cached promo data with no revalidation of time-based eligibility, and the event-driven invalidation fires only on config edits, not on scheduled expiry.
- **Suggested fix:** Cache promos with their validity windows and have the local computation check `now` against each promo's start/end before applying it; cap the hash TTL at the nearest promo or rate-change boundary when writing.
- **Plausible because:** depends on whether the promo engine emits an event at scheduled expiry - see Verification items.

### F-12: The 5%-for-one-day rollout never exercises invalidation or memory pressure at scale, and the flag itself is a stampede trigger
- **Category:** Checkout latency or availability collapse
- **Severity:** Medium - Confirmed
- **Failure scenario:** At 5%, a `promo_changed` deletes ~10k keys and memory use is ~400MB - both trivially survivable, so the one-day soak passes. At 100%, the same event deletes 200k keys (F-4) and memory sits at the 8GB ceiling (F-1); the first realistic test of both happens in production at full traffic. Additionally, the documented remediation for any cache incident - flipping `cache_pricing_v1` off at 100% - instantly converts every quote to three downstream calls, i.e., the operator's kill switch reproduces the fallthrough storm of F-7 at the worst possible moment. Repro check: does the rollout plan include a full-scale invalidation drill and a staged flag ramp-down before GA?
- **Root cause:** Rollout line: a single 5%->100% jump gated only on elapsed time, with no scale-dependent test of invalidation, memory, or flag-off behavior.
- **Suggested fix:** Ramp 5% -> 25% -> 50% -> 100% with a deliberate `promo_changed` fired at each stage, gate promotion on hit-rate and downstream-load metrics (F-9), and ramp the flag down gradually rather than hard-off during incidents.

## Killed findings

None. All 12 raw findings cited the artifact accurately and fell inside the charter's scope; the only consolidation was merging the two stampede findings (shared root cause: delete-all invalidation) into F-4.

## Verification items

Facts outside the artifact that the Plausible findings depend on:

1. **F-1 (grade detail):** the shared cluster's `maxmemory-policy` - determines whether the meltdown manifests as co-tenant eviction (`allkeys-lru`) or cluster-wide write failure (`noeviction`).
2. **F-6:** whether the checkout flow allows a quote before the final shipping address is set, and whether tax rates vary by destination jurisdiction in this system.
3. **F-7:** whether catalog/promo/tax teams autoscale or reclaim capacity when their traffic drops, or are committed to holding 100%-fallthrough headroom.
4. **F-8:** whether the first-quote fetch is cart-scoped (implying missing prices for later-added SKUs) or broader, and what the implementation does on a partial hash hit.
5. **F-11:** whether the promo engine publishes `promo_changed` at a promo's scheduled end time, or only on config edits.

## Retest list

Run each check against the revised design; a finding is closed only when its check passes.

- **F-1:** projected peak cache footprint (200k x per-entry size + overhead) is at most ~50% of the cluster's free memory, or the cache has a dedicated instance, and the eviction policy is stated - yes/no.
- **F-2:** a catalog price change or tax-rate change invalidates or bypasses affected cached entries before the next quote (not merely waiting out the 30-minute TTL), or the design records an explicit, owned business acceptance of the staleness window - yes/no.
- **F-3:** invalidation issues no `KEYS`, mass-`DEL`, or other O(keyspace) blocking operation on the shared cluster - yes/no.
- **F-4:** a single `promo_changed` at 200k warm sessions produces no synchronized miss burst: refills spread over session activity (versioning/lazy expiry) and TTLs carry jitter - yes/no (both sub-scenarios: downstream call rate and Redis write volume stay within stated bounds).
- **F-5:** with Redis fully unavailable, operators can stop cache reads and writes through a path that does not depend on that cluster (locally cached flag value, config push, or client-side breaker) - yes/no.
- **F-9:** the design names the hit-rate, fallthrough-by-cause, and eviction metrics and at least one alert that fires when the hit rate collapses - yes/no.
- **F-10:** a cache write racing a promo-version bump cannot land as valid: a version stamp (or equivalent) causes the stale write to be rejected or read as a miss, and invalidation-consumer lag is alarmed - yes/no.
- **F-12:** the rollout plan includes intermediate percentage stages, a deliberate at-scale invalidation drill, metric-gated promotion, and a gradual flag ramp-down procedure - yes/no.

Plausible findings (F-6, F-7, F-8, F-11) join this list once their verification item confirms the enabling fact; their checks are the "Suggested fix" conditions in each finding.
