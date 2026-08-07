# Design: Product Catalog Read Cache

## Problem

The `/products` and `/products/<id>` endpoints hit Postgres on every request. p95 latency is
~180ms and the catalog team's bulk imports cause read latency spikes. Catalog data changes maybe
50 times a day.

## Proposal

Add an in-process Python dict cache in each API worker:

1. **Cache shape:** `{product_id: serialized_product}`, plus one `all_products` key for the list
   endpoint.
2. **Population:** Lazy — on cache miss, read Postgres, store, return.
3. **Invalidation:** TTL of 10 minutes on every entry. No explicit invalidation; a stale product
   for up to 10 minutes is acceptable per the PM.
4. **Memory:** Catalog is ~12k products, ~2KB serialized each — roughly 25MB per worker, fine for
   our 8 gunicorn workers.
5. **Why not Redis:** A network hop per read defeats the latency goal, and it adds infra. The
   catalog fits in memory; per-worker duplication is cheap.
6. **Why not a CDN:** Responses are personalized with per-region pricing, so shared edge caching
   would need cache-key work we don't want to do now.

## Rollout

Behind a `CATALOG_CACHE` env flag, default on in staging for a week, then production.
