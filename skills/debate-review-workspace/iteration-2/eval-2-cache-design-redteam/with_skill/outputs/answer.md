# Red-team verdict: catalog read cache

I ran the full four-role debate — Defender, fresh-eyes Adversary, fresh-eyes Advocate, neutral Judge. Full transcript in `transcript.md`, Judge's report in `final-report.md`.

## Your headline question: will the in-process cache bite you?

**The architecture survived the red-team. In-process beats Redis for this workload, and the Adversary conceded it.** The winning argument: an in-process hit is less than or equal to a Redis hit on every latency component, so no measurement can flip the comparison. Redis's only real advantages — shared cache and central invalidation — buy nothing here, because the 25MB dataset fits in every worker and the invalidation gap closes without Redis (see below). The design also has a rare property Redis designs lack: every failure path degrades to today's behavior (read Postgres at ~180ms). The Adversary explicitly withdrew "reconsider Redis."

**But four specific things will bite you as the doc stands.** Both sides ended up agreeing on all four:

1. **Your rollback lever doesn't work as written.** "Rollback is a flag flip" is false: gunicorn reads env vars at fork, so flipping `CATALOG_CACHE` requires a worker restart. This is the doc's one outright factual error.
2. **There is no emergency purge.** An urgent price fix or legal takedown waits up to 10 minutes plus a restart. The PM signed off on routine staleness, not that. Agreed fix, and it stays true to your no-new-infra principle: a `cache_generation` integer in Postgres, each worker polls it every ~10s and drops its dict on change. ~15 lines, sub-10-second purge, and it makes the flag effectively live — fixing item 1 too.
3. **The cache key is only correct under an unverified assumption.** You key on `product_id` alone, but responses carry per-region pricing. If pricing is baked into the cached value, region A's prices serve to region B — wrong prices, not staleness. Spend one hour before coding: confirm pricing is applied after the cache read, confirm whether `/products` takes pagination/filter params, note the region count and gunicorn worker class. Every branch of the answer keeps the in-process architecture; you just need to know which branch you're on.
4. **The `all_products` key is the weak spot.** It doubles your memory math (the full-list blob is another ~24MB on top of the ~25MB of entries), it can't represent the endpoint if any query params exist, and its TTL expiry puts the heaviest query on user requests every 10 minutes. Judge's ruling: drop the key entirely — cache per-product entries only and assemble the list in process; 12k dict values filter in microseconds. Add TTL jitter and stale-while-revalidate (~30 lines). Add per-key single-flight only if your workers are threaded or async.

## What the Adversary tried and dropped

- "TTL refills recreate the DB-spike problem" — dropped after the Advocate's arithmetic: refill queries are a subset of what the uncached system issues anyway, so DB load never exceeds today's. Only a p99 tail at TTL boundaries survives (covered by the jitter/SWR fix).
- "Measure before building" — reduced to: put a target p95 in the doc so the staging week has a pass/fail criterion, and stop justifying in-process with the unmeasured "network hop defeats the latency goal" claim. Justify it on dominance plus operational simplicity, which is true and sufficient.

## Judge's recommendation

Build it, amended: one hour of code verification (item 3), then the ~45 lines of amendments (generation counter, jitter/SWR, per-product-only cache shape), fix the rollback sentence and memory math, set a target p95, then your staged rollout as planned. Your options, from the Judge:

1. **Build as amended** (recommended).
2. **Minimal path:** do the verification and doc fixes now, defer the generation counter and stampede code to v1.1 — faster, but takedowns stay on the 10-min-plus-restart path.
3. **Build as-is:** ships a rollback claim both sides proved false. Not advisable.
4. **Reopen Redis:** only if verification reveals baked-in pricing with a large region count.

The decision is yours; the debate's full reasoning is in the transcript if you want to disagree with any ruling.
