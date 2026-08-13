# Red-team charter: session cache for checkout service

## Artifact and context
Under review: `session-cache-design.md`, a design for caching per-session pricing context
(catalog prices, promos, tax rates) in Redis to cut `/checkout/quote` p95 from 480ms to
under 150ms. It backs the production checkout flow: every quote a customer sees comes from
this path. The Redis cluster is shared with rate limiting and feature flags, so a cache
failure can take down more than caching.

## Harm categories, ranked
1. **Customers see or pay wrong prices.** Stale or incomplete cached pricing (expired promos,
   changed catalog prices, changed tax rates) produces incorrect quote totals. Downstream:
   revenue loss, tax non-compliance, customer trust damage, possible legal exposure.
2. **Shared Redis cluster meltdown.** This cache's traffic, memory footprint, or invalidation
   pattern degrades the cluster that also serves rate limiting and feature flags. Downstream:
   outage blast radius far beyond checkout.
3. **Checkout latency or availability regression.** Cache invalidation or failure sends a
   synchronized surge of fallthrough traffic to catalog, promo, and tax services, or otherwise
   makes quotes slow or fail. Downstream: abandoned checkouts during the exact window the
   cache was built to protect.
4. **Unsafe rollout and operations.** The rollout plan or the design's operational gaps
   (metrics, gates, kill criteria) let one of the above harms reach 100% of traffic before
   anyone notices.

## Out of scope
- Prose style and document formatting.
- The current (pre-cache) architecture's own problems.
- Alternative caching technologies (Memcached vs Redis, etc.) unless the choice itself causes
  a ranked harm.

## Success criterion
A finding counts only if it would plausibly change a decision at arch review about
correctness, cost, risk, or maintainability of this design — a concrete failure scenario with
real downstream impact, not a preference.
