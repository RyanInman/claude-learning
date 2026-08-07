# Adversarial Review Transcript

**Artifact:** /Users/admin/claude-learning/skills/adversarial-review-workspace/iteration-1/eval-1-cache-design-attack/with_skill/work/cache-design.md
**Date:** 2026-08-07

Append-only. Each phase's content lands under its own heading, transcribed verbatim by the
Defender. No role's text is ever edited after it is written.

---

## Phase 1 — Defender: Opening Statement

I defend this design from the artifact text alone — I did not author it, and the conversation
carries no context beyond the file. Where the design is silent, I answer "unknown" rather than
invent facts.

**Goal.** Cut read latency on `/products` and `/products/<id>`, which hit Postgres on every
request at ~180ms p95, and reduce their exposure to read-latency spikes during the catalog
team's bulk imports. Catalog data changes roughly 50 times a day, so reads dominate writes by
orders of magnitude — a read cache is the natural lever.

**Key decisions and their why:**

1. *In-process dict, not Redis.* The stated latency goal rules out a network hop per read.
   Redis also adds an infra dependency the team would have to run. The whole catalog is ~12k
   products at ~2KB each — about 25MB per worker — so per-worker duplication is cheap in
   memory terms. An in-process dict is the simplest thing that can hit the goal.
2. *Not a CDN.* Responses carry per-region pricing, so shared edge caching needs cache-key
   design work the team is explicitly deferring. Deliberate scope control, not oversight.
3. *Lazy population.* On miss: read Postgres, store, return. No warm-up job to build or
   schedule; the cache converges to the hot set automatically.
4. *TTL-only invalidation, 10 minutes.* The PM has accepted up to 10 minutes of staleness.
   That trade buys the design its simplicity: no invalidation bus, no pub/sub, no
   import-completion signaling.
5. *`all_products` as a single cached key.* The list endpoint gets the same O(1) hit path as
   the detail endpoint without a second mechanism.
6. *Flag-gated rollout.* `CATALOG_CACHE` env flag, staging for a week, then production —
   reversible by flipping the flag.

**Decisions I am least sure of:**

- The cache key is `product_id`, yet the CDN section says responses are personalized with
  per-region pricing. The artifact does not say where personalization is applied relative to
  the cache. If cached entries are post-personalization, the key may be incomplete.
- The `all_products` entry's interaction with per-product TTLs — the artifact does not say
  whether list and detail entries expire together, so they can serve inconsistent views.
- Bulk imports motivate the design, yet TTL is the only freshness mechanism; the artifact
  does not state how the 10-minute staleness window interacts with import timing.

## Phase 2 — Adversary's Questions

1. The CDN section says responses are personalized with per-region pricing, and the cache key is `product_id` alone. What is known — from the artifact or any context available to you — about where in the request path the region-specific price is applied: before the value is stored in the cache, or after it is read back out?

2. What is known about the concurrency model of the 8 gunicorn workers (threads or async per worker, typical concurrent request count), and about what happens when several concurrent requests miss the same key at once — in particular the `all_products` key, whose miss triggers a full 12k-product read from Postgres? Does the design include any single-flight or miss-deduplication mechanism?

3. How long does a catalog bulk import take, and does anything in the artifact state whether a read that lands mid-import can observe and then cache a partially-imported catalog state? Related: does the PM's acceptance of "a stale product for up to 10 minutes" explicitly cover the list endpoint continuing to show deleted or not-yet-priced products?

## Phase 3 — Defender's Answers

**Answer 1.** Unknown. The artifact says only that "responses are personalized with per-region
pricing" as the reason to reject a CDN, and that the cache stores `{product_id:
serialized_product}`. It never states whether serialization happens before or after the
regional price is applied. If personalization happens before caching, the key is incomplete
and a user in one region can be served another region's price; if after, the cached value is
region-neutral and the key is fine. The artifact does not say which. This is a verification
item, not a fact I can supply.

**Answer 2.** Unknown beyond "our 8 gunicorn workers." The artifact does not state the worker
class (sync, threaded, async) or concurrent request volume. The population rule is exactly
"Lazy — on cache miss, read Postgres, store, return"; no single-flight, lock, or
miss-deduplication mechanism appears anywhere in the artifact. Whether concurrent misses on
`all_products` can stampede Postgres depends on the unstated concurrency model.

**Answer 3.** Unknown. The artifact says bulk imports cause read-latency spikes and that
catalog data changes about 50 times a day, but gives no import duration and says nothing about
whether a read landing mid-import can cache a partially-imported state. The PM's acceptance is
quoted only as "a stale product for up to 10 minutes is acceptable"; the artifact does not say
whether that sign-off contemplated the list endpoint showing deleted or not-yet-priced
products, or only price/detail staleness on existing products.

## Phase 4 — Adversary's Objections

<!-- Adversary: up to 5 objections, strongest first. Problem / Evidence / Better way. -->

## Phase 5 — Defender's Defense

<!-- Defender: concede each objection naming the proof, or contest its problem, evidence, or better way. -->

## Phase 6 — Adversary's Rebuttal

<!-- Adversary: sustain each objection with new substance or drop it, naming what convinced you. -->

## Phase 7 — Final Report

<!-- Defender: agreed changes / dropped objections / contested points / recommendation with declared interest / user's options. -->
