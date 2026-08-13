# Design: Session cache for checkout service

## Goal
Cut p95 latency on `/checkout/quote` from 480ms to under 150ms by caching per-session pricing
context in Redis, avoiding the three downstream calls (catalog, promo engine, tax service) on
every quote.

## Design

- On first quote in a session, fetch catalog prices, active promos, and tax rates, then write
  a single `session:{id}:pricing` hash to Redis with TTL 30 minutes.
- Subsequent quotes read the hash and compute the total locally.
- Cache key includes session ID only.
- Redis: existing shared cluster (also serves rate limiting and feature flags).
- On Redis miss or error, fall through to the three downstream calls (same as today).
- Rollout: enable via feature flag `cache_pricing_v1` at 100% after a day at 5%.

## Invalidation
Promo engine publishes a `promo_changed` event; a consumer deletes all `session:*:pricing`
keys via `KEYS session:*:pricing` then `DEL`.

## Sizing
~40KB per session hash, ~200k active sessions peak. Existing cluster has 8GB free.

## Failure handling
Fall through to downstream calls on any cache error. No circuit breaker needed since
fallthrough is the current behavior.
