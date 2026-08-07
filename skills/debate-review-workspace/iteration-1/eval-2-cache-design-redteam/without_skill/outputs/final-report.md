# Red-Team Review: Product Catalog Read Cache

Reviewed: `cache-design.md` (in-process dict cache, lazy fill, 10-min TTL, 8 gunicorn workers).

## Verdict

In-process is the right architecture for this workload, but the design as written has one
correctness bug that will ship wrong prices, one unbounded-memory hole, and two operational
failure modes. Fix those four and this is a good, low-risk design. Redis is not needed yet.

## Blocking issue: cache key ignores personalization

The doc says responses are "personalized with per-region pricing" (the stated reason to skip
CDN), but the cache shape is `{product_id: serialized_product}`. Two possibilities:

- Serialization happens after pricing is applied. Then the first region to warm an entry pins
  its prices for everyone for up to 10 minutes. First requester after each expiry wins. This
  serves wrong prices, silently, and staging (likely single-region traffic) will never catch it.
- Serialization happens before pricing. Then the design is fine, but the doc does not say so.

Fix: cache the region-neutral product record and apply pricing per request, or key by
`(product_id, region)`. Region count is presumably small, so `(product_id, region)` keeps memory
bounded. Either way, state it in the doc. This is the single most likely way this design bites
you, and it is not an in-process-vs-Redis issue; Redis with the same key has the same bug.

## Second issue: unbounded key space on `/products/<id>` misses

`<id>` is caller-supplied. The design must pick one:

- Do not cache DB misses: every request with an invalid ID hits Postgres. A scraper or enum
  attack bypasses the cache entirely and you are back to the original load problem.
- Cache misses (negative caching): key space is now attacker-controlled and the dict grows
  without bound. 25MB estimate is void.

Fix: cache negative results but bound the cache (LRU with max size, e.g. `cachetools.TTLCache`
with `maxsize`), or validate ID shape before lookup and cache misses under the bound. Never use
a raw unbounded dict keyed by user input.

## The question asked: will in-process bite us?

### Case against (steelman)

1. Deploy-time stampede. All 8 workers restart cold on every deploy. First requests all miss;
   the `all_products` rebuild is a full-catalog query, times 8, at once. Same event class as the
   bulk-import spikes this design exists to fix. Per-entry lazy TTLs desynchronize over time,
   but deploys resynchronize them. Also `gunicorn --max-requests` (if set) silently wipes a
   worker's cache mid-day.
2. Cross-worker inconsistency. Consecutive requests land on different workers with different
   snapshots. A user refreshes and a price flips new, old, new across requests for up to 10
   minutes. PM approved "stale up to 10 min"; verify they approved "stale and oscillating."
   Related: `all_products` and per-product entries expire independently, so the list can show a
   product state that the detail endpoint contradicts.
3. Bulk-import capture. Imports write row-by-row. A lazy fill during an import can cache a
   half-imported `all_products` snapshot and pin it for 10 minutes. Combined with no explicit
   invalidation, the freshest data after an import arrives up to 10 minutes late, per worker,
   at different times per worker.
4. Memory estimate is optimistic. 12k x 2KB is ~24MB for per-product entries, but the
   `all_products` value is another ~24MB, so ~50MB/worker, ~400MB across 8 workers. If entries
   are stored as Python dicts rather than serialized bytes, multiply by 3-5x for object
   overhead. Storing bytes (as the doc implies) is the right call; keep it that way, also
   because handing a cached mutable dict to handlers invites one handler mutating it and
   corrupting responses for every later hit on that worker.
5. Blocking rebuilds. With sync gunicorn workers, the request that misses `all_products` blocks
   that worker for the full DB query. During an import-induced slow-query window, 8 workers can
   all be stuck rebuilding simultaneously; the cache amplifies rather than absorbs the spike.
6. No observability. Without hit-rate, memory, and fill-latency metrics, "default on in staging
   for a week" verifies nothing; staging traffic will not reproduce production key distribution
   or deploy cadence.

### Case for (also steelman)

1. Workload fit is textbook. Small (tens of MB), bounded, read-dominated, ~50 writes/day,
   staleness explicitly accepted. This is exactly what in-process caches are for.
2. The Redis alternative buys little here. A Redis GET is ~1ms plus serialization plus a
   connection pool plus a new infra dependency, new failure modes (Redis down, network
   partition, maxmemory eviction), and an ops burden. It does not fix the real issues above:
   stampede on cold start, import capture, and the personalization key bug all exist
   identically with Redis. The only things Redis genuinely adds are cross-worker consistency
   and a single warm cache, and consistency is already conceded by the 10-min TTL.
3. Duplication cost is trivial. ~50MB x 8 workers is noise on any reasonable API host.
4. Simplicity and reversibility. ~50 lines behind a flag, removable in one commit. A Redis
   deployment is not.
5. Latency argument is honest-ish. The doc overstates it (1ms Redis hop is irrelevant against a
   180ms p95; the win is hit rate on the hot list endpoint either way), but the infra-cost
   argument stands on its own.

### Where the balance lands

In-process wins for this workload. The failure modes in the case against are real but all
cheaply mitigable inside the in-process design; none require Redis. Revisit Redis when any of
these become true: worker or host count grows enough that per-worker hit rate drops, the
catalog stops fitting in memory, or product/PM requires explicit invalidation ("price must
update within seconds"). That last one is the likely eventual trigger; 10-min TTL acceptance
tends to erode after the first pricing incident.

## Required changes before build

1. Region-aware caching: cache pre-pricing records or key by `(product_id, region)`. Blocking.
2. Bounded cache with negative caching for unknown IDs (TTLCache with maxsize, short TTL for
   negatives, e.g. 60s). Blocking.
3. TTL jitter (e.g. 10min +/- 20%) so entries do not resynchronize after deploys, plus
   per-worker single-flight on the `all_products` rebuild (one lock; concurrent missers wait or
   serve stale). Cheap, kills the stampede.
4. Serve-stale-while-revalidate for `all_products` if sync workers: on expiry, return the stale
   value and refresh; only block when the cache is truly empty. Optional but removes the
   blocking-rebuild spike.
5. Metrics: hit rate per endpoint, cache fill latency, entry count, resident memory. Define the
   staging exit criterion numerically (e.g. list-endpoint hit rate > 95%, p95 < 50ms) instead
   of "a week."
6. Doc clarifications: store serialized bytes (never share mutable objects), confirm PM
   accepted cross-worker oscillation not just staleness, note `max_requests` interaction if
   configured.

## Rollout notes

- The `CATALOG_CACHE` flag is good; also make TTL an env var so production can be tuned without
  deploy (which itself wipes the cache).
- Staging for a week validates correctness, not load. Add a one-off check in production early:
  deploy during low traffic and watch the cold-start DB spike with 8 workers before calling it
  done.
- Test the flag-off path stays exercised (it is the incident escape hatch).
