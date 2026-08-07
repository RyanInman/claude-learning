# Red-team verdict: will the in-process cache bite us?

Short answer: **the architecture won't bite you; the document as written would have, in three
specific places.** A four-role debate (Defender, Adversary, Advocate, neutral Judge) ran the
design through five objections, one rebuttal cycle, and a final report. Every objection was
resolved in debate — nothing stayed contested — but five amendments came out of it, all bounded
edits to the doc and rollout plan, none touching the core architecture.

## The case FOR the in-process cache (what survived attack)

- **The workload is the textbook case for TTL-only caching.** ~50 writes/day against
  read-dominated traffic; most 10-minute TTL entries expire without the row ever changing.
- **Every degraded state is the status quo.** Cold worker, expired entry, flag off — each is
  exactly today's direct Postgres read. The change is purely additive, with one new failure
  class (staleness) explicitly bounded and PM-priced.
- **Rejecting Redis is correct at 25MB, not just convenient.** A shared tier adds a service to
  run plus ~1ms RTT per read in a latency project, and creates a fleet-wide failure domain.
  Per-worker duplication costs ~200MB RAM and zero operations. No role argued for Redis.
- **The stampede fear is overblown.** The Adversary withdrew it after doing the arithmetic:
  8 workers re-running the list query once per 10-minute window is a strict load *reduction*
  from today, where Postgres runs that query at the full request rate continuously. Under the
  GIL, concurrent dict assignment means duplicate work, not corruption.

## The three ways it would have bitten you (all caught, all cheap to fix)

1. **Region poisoning — a wrong-price bug, not staleness.** The cache key is `product_id`, but
   responses carry per-region pricing. If anyone serializes the priced response body into the
   cache, region A's prices get served to region B for up to 10 minutes. Fix: write the
   invariant into the design (cache stores the region-neutral row; pricing applies after the
   read) and add a two-region test. Confirm where pricing lives with a one-hour code read; if
   it's baked in, key by `(region, product_id)` and redo the memory math.
2. **The single `all_products` key rests on an unverified assumption.** If `/products` supports
   pagination/filter/sort, the key either misses most traffic or serves wrong responses. Fix:
   enumerate the endpoint's real parameter space (route code + a day of access logs) as a
   build gate. Canonical → keep the design. Parameterized → cache raw rows and filter
   per request, after measuring serialization cost.
3. **The staleness sign-off is narrower than the design assumes, and there's no emergency
   lever.** "Stale product for 10 minutes" was never checked against legal takedowns, price
   corrections, or the fact that a rolling import leaves list/detail pages inconsistent for up
   to 10 minutes *after* the import commits, on every import. And the only flush path — flip
   `CATALOG_CACHE` and rolling-restart — appears nowhere in the doc, with unmeasured
   propagation time. Fix: document the emergency-flush runbook, measure its propagation in
   staging, then take the PM a concrete scenario list. Add a `catalog_version` check (one
   cheap read/sec per worker, drops cache on bump) only if the PM needs sub-10-minute
   propagation — it re-adds write-path coupling, so keep it conditional.

## Two smaller agreed upgrades

4. **Stampede hardening as implementation notes (~20 lines):** ±20% TTL jitter plus a
   per-worker serve-stale-while-refreshing flag; read the gunicorn config (sync vs. threaded)
   and state the concurrency model in the design.
5. **Make the rollout criterion-gated, not calendar-gated:** hit/miss/refresh counters,
   latency tagged by cache on/off, and a numeric bar (e.g. p95 < 30ms, hit rate > 90%) that
   staging must meet before production default-on.

## Judge's recommendation

Adopt the amended plan. Treat the parameter-space enumeration and the PM scenario meeting as
hard gates before build — each has an agreed contingency, so neither outcome reopens the
debate. The one place you might reasonably override the consensus: if takedown risk is real
for your catalog (regulated products, DMCA), add `catalog_version` unconditionally — it fails
back to the TTL bound, so it's near-free insurance.

Full debate: `transcript.md`. Judge's report verbatim: `final-report.md` (both in this
directory). Building the original doc unmodified is the one option no role supported — the
region-key gap alone is a live wrong-price bug.
