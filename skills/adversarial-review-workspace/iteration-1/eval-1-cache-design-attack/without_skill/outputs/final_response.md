Attacked cache-design.md. Two design gaps block building as written; the rest are prod risks you should decide on explicitly.

## Blockers

**1. Region pricing breaks the cache key.** Section 6 says responses carry per-region pricing, but the cache key is `product_id`. As written, the first region to miss populates the entry and every other region gets that region's prices. Fix one of two ways: key by `(product_id, region)` and multiply the memory estimate by region count, or cache the region-neutral product and apply pricing after the cache read. The doc must say which.

**2. `all_products` is underspecified.** Does `/products` take pagination, filter, or sort params? If yes, one key cannot serve it: you either cache only the bare query or key by querystring, which is an unbounded key space. If no params, the blob is ~24MB, which roughly doubles the 25MB/worker estimate, before Python object overhead (real footprint is typically 2-3x serialized size).

## Will bite in production

**3. The cache barely addresses the stated problem.** The pain is read spikes during bulk imports. During an import: misses still hit Postgres while it is loaded, TTL expiries mid-import re-hit it, and lazy fill can cache a half-imported snapshot and pin it for 10 minutes. Add import-triggered warmup or refresh-ahead, or at minimum accept in the doc that imports still spike the miss path.

**4. Stampede on expiry.** With threaded or async gunicorn workers, every concurrent request that sees an expired `all_products` runs the full-catalog query. Single-flight the rebuild: serve the stale entry while one thread refreshes. Cheap to add now, painful to retrofit after an incident.

**5. Incoherent and non-monotonic reads.** `all_products`, per-id entries, and all 8 workers expire independently. A user can see the new price on the detail page, the old price on the list, then the old price again on refresh. The PM approved "stale up to 10 minutes," probably not flip-flopping. Either accept it explicitly (tell the PM) or refresh the per-id entry when the list rebuilds.

**6. No escape hatch.** If a wrong price gets cached, the only remedies are waiting out the TTL or restarting workers, and the `CATALOG_CACHE` flag also needs a restart. Add a cheap flush: a cache epoch checked per request, or an admin endpoint per worker.

## Fix before calling rollout done

**7. Rollout has no success criteria, and staging cannot produce them.** Staging traffic yields near-zero hit rates, so "a week in staging" only proves the code does not crash. Add hit/miss/stale-serve metrics and a concrete gate for prod default-on, e.g. hit rate > 95% and cached p95 < 30ms.

**8. Misses for nonexistent IDs always hit the DB.** A scraper enumerating `/products/<id>` bypasses the cache entirely. Decide: negative-cache 404s with a short TTL, or accept the exposure.

## Nits

- The Redis rejection reasons wrong: a network hop is ~1ms against a 180ms baseline, so it does not "defeat the latency goal." The real argument is operational simplicity. Write that, or someone will relitigate the decision on a false premise.
- State the honest memory number: 24MB serialized + duplicate `all_products` blob + Python overhead, not "roughly 25MB."

**Bottom line:** fix #1 and #2 before writing code; #3 and #4 decide whether the cache helps during the exact incident it exists for; #5-#8 are one-line decisions to record either way.
