# Red-team charter: session cache for checkout service

## Artifact and context

Under review: `session-cache-design.md`, a design for caching per-session pricing context
(catalog prices, promos, tax rates) in Redis to cut `/checkout/quote` p95 from 480ms to
under 150ms. It backs the production checkout flow. The Redis cluster is shared with rate
limiting and feature flags. Downstream consumers of a failure: customers who pay the quoted
price, finance/tax reconciliation, and every service on the shared Redis cluster.

## Harm categories, ranked

1. **Customers charged wrong prices.** Stale or incorrect cached prices, promos, or tax
   rates produce quotes that customers pay. Money moves on these numbers; errors at scale
   are a refund/compliance incident.
2. **Shared Redis cluster meltdown.** This cluster also serves rate limiting and feature
   flags. Memory exhaustion, blocking commands, or eviction storms take down unrelated
   production systems, not just this cache.
3. **Checkout latency or availability collapse.** The design's own goal fails: cache
   stampedes, mass invalidation, or fallthrough storms push load onto the three downstream
   services and make checkout slower or unavailable — worst during peak traffic, exactly
   when the cache matters.
4. **Silent failure.** Wrong prices or degraded behavior that no metric or alert surfaces,
   discovered only by customer complaints or month-end reconciliation.

## Out of scope

- Code style, naming, and doc formatting.
- Whether Redis was the right technology versus alternatives (Memcached, in-process cache).
- The checkout service's existing 480ms baseline behavior.

## Success criterion

A finding counts if it would plausibly change a decision about correctness (prices, tax),
cost, risk (cluster stability, checkout availability), or maintainability before this design
passes architecture review. "I would have designed it differently" does not count.
