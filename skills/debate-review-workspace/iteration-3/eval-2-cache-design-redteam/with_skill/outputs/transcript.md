# Debate Review Transcript

**Artifact:** /Users/admin/claude-learning/skills/debate-review-workspace/iteration-3/eval-2-cache-design-redteam/with_skill/work/cache-design.md
**Date:** 2026-08-07

Append-only. Each phase's content lands under its own heading, transcribed verbatim by the
Defender. No role's text is ever edited after it is written.

---

## Phase 1 — Defender: Opening Statement

I did not author this design; the user brought it for red-teaming before building it. I present the case the document itself makes, plus the one piece of real context the user gave: their main worry is whether the in-process cache will bite them, and they want both sides argued honestly.

**Goal.** Cut read latency on `/products` and `/products/<id>`, which currently hit Postgres on every request at ~180ms p95, and insulate reads from latency spikes caused by the catalog team's bulk imports.

**Key decisions and their stated reasons:**

1. **In-process Python dict cache per API worker.** The design's core bet. Reason: a network hop per read (Redis) would defeat the latency goal, and the catalog is small enough — ~12k products at ~2KB serialized, roughly 25MB — that duplicating it across 8 gunicorn workers is cheap (~200MB total).

2. **Cache shape: `{product_id: serialized_product}` plus one `all_products` key** for the list endpoint. Simple, covers both endpoints.

3. **Lazy population.** On miss: read Postgres, store, return. No warm-up machinery.

4. **TTL-only invalidation at 10 minutes.** No explicit invalidation. The PM has accepted staleness of up to 10 minutes, and catalog data changes only ~50 times a day, so event-driven invalidation is judged not worth its complexity.

5. **No Redis.** Avoids a network hop and new infra for a dataset that fits in memory.

6. **No CDN.** Responses carry per-region pricing, so shared edge caching would need cache-key work the team doesn't want to do now.

7. **Rollout behind a `CATALOG_CACHE` env flag**, default on in staging for a week, then production.

**Decisions I am least sure of, reading the document honestly:** the document does not state a target latency number, does not say whether workers are threaded (concurrent access to a shared dict), does not address what happens when all workers' TTLs expire around the same time after an import (thundering herd of misses), and the per-region pricing note in the CDN section raises a question the cache-shape section doesn't answer — whether a single `serialized_product` entry can serve all regions. Those are gaps for the debate to probe, not defects I assert.

## Phase 2 — Clarifying Questions

### Adversary's questions

#### Q1. Region and cache key

Does the `serialized_product` value stored under `{product_id: ...}` include the per-region price fields that the CDN section refers to, or is pricing applied after the cache read? And what carries the region on an incoming request (header, path, authenticated user attribute), and how many distinct regions are in play today?

#### Q2. Runtime and shape facts

What gunicorn worker class and thread count are configured, and what memory limit is set per worker or per container? Separately: what exactly does the `all_products` key hold — the full serialized list as a single blob, and does the `/products` endpoint accept pagination, filter, or sort parameters that vary the response body?

#### Q3. Import and traffic mechanics

For the catalog team's bulk imports: how long does a typical import run, roughly how many rows does it touch, how often do imports occur, and is there any existing signal at import start or completion (job hook, notify, log event) that the API workers could already observe? Also, what is the current request rate on the two endpoints, and how often do API workers restart or redeploy on a normal day?

### Advocate's questions

#### Q1 — What is the read volume and the gunicorn worker type?

Requests per second (and the split between `/products` list reads and `/products/<id>` point reads) at peak, and whether the 8 gunicorn workers are sync workers or threaded/gevent workers with more than one concurrent request per process. If the user gave a number for expected cache hit rate or a target p95, what was it?

#### Q2 — What is the ~180ms p95 actually made of?

Is the 180ms dominated by Postgres query time, by connection-pool wait during the bulk imports, or by Python-side serialization of the response? Put differently: for a request that would be a cache hit, how much of that 180ms does the cache remove — and is there a measured number for the same query when Postgres is warm and idle?

#### Q3 — Where does per-region pricing get applied?

Does `serialized_product` in the cache shape already contain a region's prices, or is pricing applied after the cache read on the way out? How many regions are there, and does the same worker serve requests from all of them? Also: what does the deploy/restart cadence look like (how often does a worker process recycle), and how much memory headroom does each worker container have above the ~25MB the design claims?

## Phase 3 — Defender's Answers

I answer only from the artifact text and the user's request. This design arrived as a standalone file; I hold no facts beyond it, so several answers are honestly "unknown." Each unknown is a finding for the debate to convert into a verification item.

**Adversary Q1 / Advocate Q3 (per-region pricing and the cache key).** Unknown, and this is the sharpest gap in the document. The cache shape is `{product_id: serialized_product}` plus one `all_products` key, with no region dimension. The CDN section says responses "are personalized with per-region pricing." The document does not say whether `serialized_product` contains region-specific prices, where pricing is applied relative to the cache read, what carries the region on a request, or how many regions exist. Whether one worker serves all regions: unknown, though nothing in the document suggests region-pinned workers.

**Adversary Q2 / Advocate Q1 (worker class, threads, memory limits).** Unknown. The document says "8 gunicorn workers" and nothing about worker class (sync, gthread, gevent), thread count, or per-worker/container memory limits. It claims ~25MB per worker is "fine" but states no headroom figure.

**Adversary Q2 (what `all_products` holds; list-endpoint parameters).** The document shows a single `all_products` key, which reads as the full serialized list as one blob. Whether `/products` accepts pagination, filter, or sort parameters: unknown — the document does not mention any.

**Adversary Q3 (import mechanics).** Unknown across the board: import duration, rows touched, frequency, and whether any completion signal (job hook, NOTIFY, log event) exists. The document says only that bulk imports cause read latency spikes and that catalog data changes "maybe 50 times a day" — it does not say whether those 50 changes are individual edits, imports, or a mix.

**Adversary Q3 / Advocate Q1 (request rate, endpoint split, hit-rate or p95 target).** Unknown. The document gives p95 ~180ms as the current state but sets no numeric target and no request-rate or hit-rate figures.

**Advocate Q2 (composition of the 180ms).** Unknown. No breakdown exists in the document between Postgres query time, pool wait during imports, and serialization. No warm-Postgres baseline measurement is given.

**Advocate Q3 / Adversary Q3 (deploy/restart cadence).** Unknown. The document does not describe deploy frequency or worker recycling (e.g., gunicorn `max_requests`).

## Phase 4 — Cases

### Adversary's case

#### Objection 1 — The cache key has no region dimension, so the design as written can serve one region's prices to another

**Problem.** The cache shape is `{product_id: serialized_product}` (line 13) with exactly one dimension: product id. Section 6 states responses "are personalized with per-region pricing." Both cannot be true unless pricing is applied strictly after the cache read, and the document never says that it is. Under the shape as written, the first request for product 4711 from `us-east` populates the entry, and every subsequent request for 4711 from any other region is served US pricing until the TTL expires. That is not stale data the PM accepted — the PM accepted a product being *out of date* by 10 minutes, not a European customer seeing a US price. It is also silent: no error, no log, no latency signal. You find it in a billing dispute.

**Evidence.** The document contradicts itself between sections 1 and 6, and the Defender confirmed in Phase 3 that the resolution is unknown: "no region dimension… The document does not say whether `serialized_product` contains region-specific prices, where pricing is applied relative to the cache read." Also unknown per Phase 3: whether workers are region-pinned. Nothing in the doc suggests they are, so the safe assumption is that any worker serves any region — which is exactly the condition that makes the bug fire. The `all_products` blob has the same defect and a wider blast radius: one poisoned list response covers all 12k products at once.

**Better way.** Resolve this before writing code, and write the answer into the design as a stated invariant, not a comment:

- If pricing is baked into `serialized_product`: key on `(region, product_id)` and `all_products:{region}`. Then restate the memory math — it is 25MB × *R* regions per worker, not 25MB, and the doc's "fine for our 8 workers" claim needs redoing with the real region count.
- If pricing is applied after the read (the better design): make the cached value provably region-free — cache the base product with a `price_base` field only, apply the region overlay in the serializer — and add a unit test that asserts no cached value ever contains a region-scoped field, so a future field addition cannot silently reintroduce the bug.

Either way the doc must name what carries the region on the request (header, JWT claim, path) and the current region count, because the second one changes the memory decision and possibly the Redis decision.

#### Objection 2 — Lazy fill plus a flat 10-minute TTL and no single-flight turns the cache into a load amplifier during exactly the event it was built to survive

**Problem.** The stated goal (line 6) is insulating reads from bulk-import latency spikes. The chosen mechanism does the opposite at the worst moment. Entries are filled lazily, so after a deploy or a worker recycle the whole working set fills within a few seconds of first traffic and therefore *expires within the same few seconds*, ten minutes later. At that instant every one of the 8 workers has a synchronized miss wave, and with no per-key single-flight, concurrent requests for the same product each issue their own query. The `all_products` key is the sharp edge: it is one key backing the list endpoint, so its expiry means 8 workers simultaneously run a full-catalog query and serialize 12k rows, repeating every 10 minutes forever. If that wave lands on top of a bulk import — a coin flip over a 10-minute cycle — Postgres sees the import write load plus a burst of 8 full-catalog scans, which is a strictly worse read-latency spike than today's steady query stream.

**Evidence.** Structural, not speculative. TTL is set at fill time and fill is triggered by traffic, so fill times cluster and expiry times inherit the cluster; nothing in the design breaks that correlation. The design specifies no lock, no in-flight-request map, and no jitter. Phase 3 confirms import duration, frequency, and request rate are all unknown, so the team cannot currently show the waves do not overlap. Also unknown per Phase 3: deploy cadence and `max_requests` — if gunicorn recycles workers on a request count, cold-fill waves happen far more often than the deploy schedule suggests.

**Better way.** Three changes, all small:

1. **Jitter the TTL**: `600s × uniform(0.8, 1.2)` per entry, decorrelating expiry across keys and across workers.
2. **Single-flight per key**: a per-worker `dict[key, Future]`; the first miss fetches, concurrent misses await the same future. Roughly 15 lines, and it caps concurrent Postgres queries at one per key per worker instead of one per request.
3. **Serve stale while revalidating**: on expiry, return the stale value immediately and refresh in the background. This is the change that actually delivers the stated goal — during a bulk import, readers keep getting sub-millisecond stale responses instead of queueing behind a degraded Postgres. Since the PM has already accepted 10-minute staleness, extending to "stale up to 10 minutes, or longer if the database is unhealthy" is a small ask for a large availability win.

Add a hard stale ceiling (say 60 minutes) so a permanently failing refresh cannot serve indefinitely-old data unnoticed.

#### Objection 3 — The memory model undercounts, and the cache is unbounded in three separate ways

**Problem.** "~25MB per worker, fine" (line 18) is doing a lot of load-bearing work for a number that is a back-of-envelope product of two guesses, and at least three effects push the real figure well above it.

- **Double storage.** `all_products` is a second full copy of the catalog, so the floor is ~50MB per worker, not 25MB — ~400MB across 8 workers rather than 200MB.
- **Representation overhead.** "2KB serialized" is the payload size. If entries are stored as Python dicts rather than `bytes`, the in-heap cost is commonly 3–10× the JSON size, and the 12k-entry dict itself, plus per-object headers, is not free. 25MB of payload can be 150MB+ of RSS.
- **No eviction and no key bound.** There is no max size and no LRU. The catalog is 12k today; nothing in the design notices when it is 60k. Worse, if misses on nonexistent ids are not cached, `/products/<random>` never hits cache and always reaches Postgres, which is a cheap way for a scraper to bypass the cache entirely; if they *are* cached, an attacker grows the dict without bound.

Python also does not return freed heap to the OS reliably, so a transient spike becomes a permanent RSS floor, and an OOM-killed gunicorn worker under a container memory limit looks like random 502s, not like a cache problem.

**Evidence.** The doc states the size claim with no measurement and no headroom figure; Phase 3 confirms worker class, thread count, and per-worker or container memory limits are all unknown. You cannot call 25MB "fine" without knowing the limit it is fine against. The `all_products` duplication is visible in the design's own cache shape — it is listed as a separate key, not as a list of references.

**Better way.** Before the flag ships anywhere:

- Store one canonical `bytes` per product (`orjson.dumps`) and make `all_products` hold *references* to those same objects, or store the assembled list blob and derive point reads from it — either way, one copy, not two.
- Measure rather than estimate: load all 12k products into one worker and record RSS delta with `tracemalloc` / RSS before-after. Put the measured number and the container limit side by side in the doc.
- Add `maxsize` with LRU eviction (`cachetools.TTLCache` gives TTL + max size + jitter-friendly wrapping in a few lines) so growth degrades hit rate instead of killing the process, and never cache negative lookups without a separate, small, short-TTL negative cache.

#### Objection 4 — Nobody has shown the cache fixes the 180ms, and there is a much cheaper experiment that would tell you

**Problem.** The design commits to per-worker caching, TTL policy, memory duplication, and a correctness hazard (Objection 1) on the strength of one unattributed number. If the 180ms p95 is dominated by connection-pool wait during imports, the cache removes it only for hits and leaves every miss queued behind the same exhausted pool — and the synchronized miss waves from Objection 2 land squarely in the pool. If it is dominated by Python-side response serialization, caching *serialized* bytes is the whole win and the Postgres story is a red herring. If it is dominated by a missing index on the list query, the correct fix is a 10-minute migration with zero staleness and zero memory cost, and shipping the cache instead permanently hides the real defect.

**Evidence.** Phase 3: "Unknown. No breakdown exists in the document between Postgres query time, pool wait during imports, and serialization. No warm-Postgres baseline measurement is given." The document also sets no target p95 and no expected hit rate, so there is no definition of success and therefore nothing that can fail. A design that cannot fail is a design nobody can evaluate after the fact.

**Better way.** An afternoon of measurement plus a staged first cut:

1. Pull `pg_stat_statements` for the two endpoint queries (mean and p95 exec time), record pool checkout wait, and take a `py-spy` profile of one worker at peak. That decomposes the 180ms into three buckets and settles whether a cache is even the right tool. If the warm-Postgres query time is 8ms and the p95 is 180ms, the cache is not the fix.
2. Write a target into the doc: p95 under Nms at an expected hit rate of H%, plus the rollback trigger if it is not met.
3. Ship the narrow version first: cache only `all_products` (or only the list query result) with a short TTL and single-flight. One key, one region dimension to reason about, trivial memory, no per-id dict, no unbounded growth. If the list endpoint carries most of the traffic — which Phase 3 says is unmeasured but is typical for catalog browsing — that single key captures most of the benefit at a fraction of the risk surface, and it gives you the hit-rate data needed to justify the full design.

#### Objection 5 — The rollout plan cannot detect any of the above failures, because the cache emits nothing and staging proves nothing

**Problem.** "Behind a `CATALOG_CACHE` env flag, default on in staging for a week, then production" (line 27) reads like caution but provides almost no information. Staging does not have production request volume, production region mix, production catalog cardinality, or production bulk imports, so a clean week in staging is not evidence about memory, hit rate, stampedes, or region bleed — the four things most likely to go wrong. And an env-var flag is per-process and set at boot, so turning it off during a production incident requires a full redeploy or restart at exactly the moment you least want to restart 8 workers with cold caches into a degraded database.

**Evidence.** The design specifies no metrics at all: no hit/miss counters, no entry count, no bytes resident, no stale-age, no refresh-failure counter. Every failure mode raised in Objections 1–3 is silent by construction — wrong-region pricing produces a correct-looking 200, a stampede shows up only as a Postgres graph nobody is watching, and memory growth surfaces as an OOM kill attributed to something else. Compounding it: Phase 3 confirms deploy cadence and worker recycling are unknown, so the team cannot even predict how often cold-start waves occur in production.

**Better way.**

- **Instrument first, in the same PR as the cache**: `cache_hits`, `cache_misses`, `cache_entries`, `cache_bytes`, `refresh_failures`, and a histogram of served-entry age. Without these, the staging week and the production rollout produce no evidence either way.
- **Make the flag runtime-flippable** — a config value re-read per request or per N seconds, not a boot-time env var — so kill-switching does not require a restart. Add a second flag that switches to "read-through, do-not-store" so you can drain the cache without dropping to cold Postgres in one step.
- **Roll out by traffic share in production, not by environment**: 1 worker, then 25%, then 100%, comparing p95 and Postgres load between cached and uncached workers on the same live traffic. That is a real control group; staging is not.
- **Write the rollback triggers into the doc as numbers**: revert if worker RSS exceeds the container limit minus headroom, if hit rate is below the assumed H%, if p95 has not improved by the target after 24 hours at full traffic, or if Postgres read QPS shows a periodic spike matching the TTL interval.

### Advocate's case

#### The case in one line

This design buys the largest available latency win with the smallest available blast radius, behind a flag that makes being wrong cost one environment variable. Every alternative on the table (Redis, CDN, event-driven invalidation) is strictly more expensive, more permanent, and — for the specific workload described — not obviously faster.

#### 1. The workload shape is the textbook fit, and the numbers are not close

Three facts from the problem statement determine the answer: the dataset is ~24MB, it changes ~50 times a day, and it is read on every request to two hot endpoints. That is a read:write ratio in the thousands-to-one range against a dataset that fits in a fraction of a single process's heap.

In-process caching is the correct answer for exactly this shape, and it wins by orders of magnitude rather than by margin. A Python dict lookup is roughly 50–100ns. A Redis GET on a warm connection over a datacenter network is 300µs–1ms before deserialization. That is a 3,000–10,000x difference on the lookup itself, against a stated baseline of 180ms. The design's core bet is not a close call that got decided by taste; it is the only option that removes essentially all of the per-request cost rather than trading Postgres latency for network latency.

The design also states its memory arithmetic, which most caching proposals do not: 12k × 2KB × 8 workers ≈ 200MB total. That number is checkable, it is small on any modern container fleet, and it is an upper bound rather than a typical (see point 5).

#### 2. The Redis rejection is stronger than the document argues, and for the list endpoint Redis is plausibly a latency regression

The document says a network hop "defeats the latency goal." That undersells it. The single `all_products` key implies the list endpoint returns the full catalog: roughly 24MB of serialized payload. Redis does not charge a fixed hop for that. It charges bandwidth.

24MB over a 10 Gbps link is ~19ms of pure transfer before any deserialization, before any parsing, before the response is assembled. Over 1 Gbps it is ~192ms, which is *worse than the 180ms p95 the design is trying to fix*. Add Redis-side serialization and client-side deserialization and the list endpoint could come out slower than the uncached Postgres path it replaced.

The in-process cache does not merely avoid this cost. It avoids serialization entirely, because the cached value is already the serialized form. The design's cache shape stores `serialized_product`, not a model object. That single word means a hit skips the query, the ORM hydration, and the serialization pass. Redis skips only the query, then adds transfer and re-parse. The gap between the two options is far larger than "one network hop."

(This argument depends on the list endpoint returning a large payload. If it turns out `/products` returns a small page, the Redis penalty shrinks toward the constant hop. It does not reverse.)

#### 3. TTL-only invalidation is the only scheme here that self-heals, and event-driven invalidation smuggles Redis back in through the side door

The obvious "improvement" to TTL-only is explicit invalidation on write. That upgrade is not free, and its cost lands precisely where the design was trying to avoid cost.

Invalidating an in-process cache across 8 independent OS processes requires a fan-out channel: pub/sub, a message bus, or Postgres `LISTEN/NOTIFY` with a listener thread in every worker. The first two mean adding the infrastructure dependency the design explicitly declined. All three add a permanent correctness surface with genuinely nasty failure modes:

- A worker that was restarting when the message fired never receives it, and stays stale **forever**.
- A worker whose subscriber thread dies silently stays stale forever, and looks healthy.
- A worker that starts after the message has no way to know it missed anything.
- Message ordering versus read-your-own-write across 8 processes is a distributed-systems problem, not a caching feature.

Every one of those failure modes is unbounded staleness that requires human detection. TTL has exactly one failure mode, it is bounded at 10 minutes, and it is self-correcting without anyone noticing or intervening. Every process converges regardless of what it missed, what it dropped, when it started, or whether it was even running.

That property is worth naming plainly: **TTL is stateless convergence.** It has no memory, so it cannot have corrupt memory. For a system where the accepted staleness window is already 10 minutes, buying tighter freshness by trading a bounded self-healing failure for an unbounded silent one is a bad trade, and the design is right to decline it.

#### 4. The staleness budget is already owned, and the arithmetic is better than "10 minutes" sounds

Two things about item 3 deserve defending.

First, the PM accepted 10-minute staleness. That is a product decision with a named owner and a rendered verdict. Treating it as settled input rather than an open engineering question is correct discipline, not hand-waving. Engineering review that relitigates a decision already made by the person who owns it is scope creep.

Second, "10 minutes stale" overstates the actual exposure, and the design never does the math that would defend it. 50 changes/day × 10 minutes each = 500 product-minutes of staleness against 12,000 products × 1,440 minutes = 17.28 million product-minutes available per day. That is **0.003% of catalog-time stale**, and the *average* staleness of a changed product is 5 minutes, not 10, because changes land uniformly within the TTL window.

Even under heavy read skew the number stays small. Suppose the 50 changed products absorb a wildly disproportionate 10% of all read traffic: those products are stale for 500 of their 72,000 product-minutes (0.69%), so the share of all reads served stale data is roughly 0.07%. Seven reads in ten thousand. That is the number that justifies TTL-only, and it justifies it comfortably.

#### 5. Lazy population avoids a deploy-time stampede that eager warm-up would create

Lazy population reads as "we didn't bother building warm-up." It is better than that.

Eager warm-up means every worker issues a full-catalog read at boot. With 8 workers that is 8 simultaneous 12k-row queries against Postgres on every single deploy and every worker recycle. That is a self-inflicted version of the exact load spike the design exists to prevent. Lazy population spreads the fill across organic traffic instead of concentrating it at the moment the system is least stable.

Lazy also has two quieter benefits. The cache is self-limiting: memory tracks actual traffic, so 25MB is a ceiling and the working set is likely far smaller if reads are skewed toward popular products. And a cold cache is trivially correct — there is no warm-up path that can populate stale or partial data, because there is no warm-up path.

#### 6. The CDN rejection holds for a reason beyond cache keys

The document rejects the CDN on cache-key work. Two further reasons support it.

A CDN would not solve the stated problem even if the key work were done. The problem is Postgres read latency and pool contention during bulk imports. A CDN only relieves origin load in proportion to its edge hit rate, and region-splitting the cache key divides that hit rate by the number of regions. A CDN sitting in front of personalized responses protects the origin least at exactly the moment the origin needs protecting most.

And a CDN would not buy better freshness either. Purge propagation across an edge network is itself measured in seconds to minutes, so the team would take on cache-key engineering, a purge integration, and a new vendor in the read path in exchange for a freshness story no better than the 10-minute TTL they already have. The CDN is more work for the same staleness and less spike protection.

#### 7. The flag rollout makes this a cheap reversible experiment, and it manufactures the data the expensive decision needs

This is the strongest structural argument for the design and the document states it in a single line without defending it.

`CATALOG_CACHE` off is byte-identical to today's behavior. Rollback is an environment variable, not a revert, not a migration, not a redeploy of an infrastructure change, not a teardown. There is no schema change, no API contract change, no new deployable, no new secret, no new on-call surface, no data that must be migrated if the approach is abandoned. If this fails in production, the fix is a config flip and the cleanup is deleting a module.

Contrast the alternative that reviewers reach for. Once Redis is provisioned and on the read path, it is in the architecture: it needs connection pooling, timeouts, a circuit breaker so a Redis outage does not take down reads, an eviction policy, capacity planning, monitoring, a runbook, and a line item. It is a one-way door in practice even when it is a two-way door in theory, because nobody removes infrastructure.

The correct sequencing is therefore exactly what the design proposes. Run the reversible experiment first, and it produces the measurements — real hit rate, real latency delta, real memory profile, real staleness complaints — that would either justify Redis or prove it unnecessary. A week in staging with the flag on converts the design's unknowns into observations at essentially zero risk. Building Redis first means committing to permanent infrastructure on the strength of an estimate.

The question this design should be judged against is not "is this the perfect end-state architecture." It is "is the cheapest reversible experiment worth running before the expensive irreversible one." It plainly is.

#### 8. The open questions are parameters, not refutations

The Defender honestly flagged several unknowns: region in the cache key, worker class and threading, thundering herd at TTL expiry, list-endpoint parameters. Worth noticing what kind of unknowns these are.

Every one of them is answerable *without changing the design's shape*. Region becomes part of the key: `{(product_id, region): ...}`, a one-line change that multiplies memory by the region count (still trivial at, say, 4 regions and 100MB/worker). Threading is answered by putting the dict behind the GIL's atomic operations or a lock, which for a read-mostly dict costs nothing measurable. Herd at expiry is answered by jittering the TTL per entry, which is one line. Pagination is answered by keying the list cache on its parameters.

A design whose open questions are all *parameterizations* is a robust design. A fragile design is one where a single unknown, resolved the wrong way, invalidates the whole approach. Nothing on the Defender's list has that character. The load-bearing bets — small dataset, read-mostly, in-process, TTL-only, flagged rollout — survive every resolution of every open question.

#### 9. Simplicity is a real engineering property, not an aesthetic one

This is on the order of 50 lines of code. No new deploy artifact, no new dashboard required to ship, no new dependency, no new failure mode that is not already handled (a worker process dying is a case the fleet already survives). The blast radius of any bug is one process, and gunicorn already restarts those.

The team also stated a capacity constraint directly: they do not want to do cache-key work "now." That is a real constraint with a real cost, and the design respects it rather than routing around it. A proposal that spends the team's scarce attention on infrastructure they did not ask for, to solve a freshness problem the PM already priced, is the more expensive plan even when it is the more sophisticated one.

#### What evidence would move me

Naming this in advance so the standard is fixed before the argument, not after:

- A measurement showing the 180ms p95 is dominated by connection-pool wait rather than query plus serialization time. A cache reduces pool pressure but does not eliminate it for misses, so this would shrink the claimed win.
- A container memory limit low enough that 25MB per worker (or 100MB after regional keying) is not comfortable headroom.
- Evidence that `/products` takes pagination, filter, or sort parameters with high cardinality, which would break the single `all_products` blob as a design rather than as a parameter.
- A concrete correctness requirement, from someone with standing to set it, that contradicts the PM's accepted 10-minute staleness window.

Absent those, the design as written is the right first move.

## Phase 5 — Rebuttals

### Adversary's rebuttal

#### Rebuttal to the steelman

##### On point 1 (workload shape, 3,000–10,000x on the lookup)

The multiplier is real and irrelevant. Against a 180ms baseline, a 100ns dict hit and a 500µs Redis hit are 0.00006% and 0.28% of the current cost. Both round to zero on the user-visible p95; the choice between them cannot be made on latency and the doc should stop pretending it can. What actually selects in-process is "no new infrastructure," which is a legitimate argument the Advocate makes properly in point 7 — but presenting a 3,000x ratio on a term that is already noise makes the case look stronger than it is, and it is the kind of number a reviewer repeats later as if it settled something.

Also, "a fraction of a single process's heap" quietly drops the multiplier the design turns on. It is ~24MB per copy, ~48MB with `all_products`, times 8 processes, times the region count the Advocate himself introduces in point 8.

##### On point 2 (Redis is a latency regression for the list endpoint)

This is the point that does the most damage — to the design. Take the premise seriously: if `/products` really returns the full 24MB catalog, then 24MB over 10 Gbps is 19ms of Redis transfer, yes, but it is also a 24MB HTTP response body produced today in 180ms p95, which is 133 MB/s sustained through ORM hydration of 12k rows, Python serialization, and gunicorn. That is not credible. So one of two things is true, and the design must say which:

- `/products` is paginated, filtered, or field-limited. Then `all_products` as a single blob is wrong as a design, not as a parameter — it is one of the four things the Advocate himself named as evidence that would move him — and the Redis-bandwidth argument collapses to the constant hop.
- `/products` really ships 24MB. Then the 180ms number is measuring something other than what everyone assumes, and egress, not Postgres, is the problem.

Either branch forces a resolution the doc currently ducks. Separately, the claim that "the gap is far larger than one network hop" because in-process "avoids serialization entirely" does not survive inspection: Redis also stores serialized bytes, and a pass-through of cached bytes skips the query, the ORM hydration, and the serialization pass exactly as the dict does. The extra cost of Redis really is the hop plus transfer. And nobody would put a 24MB value in one Redis key anyway — it blocks the single-threaded event loop for every other client — so the 192ms figure is arithmetic against a configuration no one would build.

##### On point 3 (TTL is stateless convergence)

Correct, well argued, and aimed at a proposal nobody made. None of my five objections asks for event-driven invalidation, pub/sub, or `LISTEN/NOTIFY`. Jitter, single-flight, stale-while-revalidate, bounds, and metrics are all TTL-only mechanisms. The dichotomy is also false on its own terms — TTL plus best-effort invalidation inherits TTL's bound, so a dropped message costs at most the staleness already accepted, not "stale forever." Being right about a bad idea does not carry any of the other eight points.

##### On point 4 (0.003% of catalog-time stale)

The arithmetic assumes the 50 daily changes are 50 independent single-row edits landing uniformly in time. The problem statement says the catalog team runs **bulk imports**, and Phase 3 confirms nobody knows whether the 50 changes are edits, imports, or a mix. If one import touches 3,000 rows, then for the 10 minutes after it lands, 25% of the catalog is stale in every worker at once — not 0.003%. The metric also measures the wrong thing: staleness harm is not spread over product-minutes, it concentrates on the products someone just changed, and a product gets changed precisely because someone cares about it right now. Assuming changed products absorb "a wildly disproportionate 10%" of reads is not a worst case for a price drop or a launch; it is roughly the base rate.

None of this touches Objection 1, which is about serving the *wrong* region's price, not old data. The PM priced staleness. Nobody priced incorrectness.

##### On point 5 (lazy avoids the deploy-time stampede)

Lazy does not avoid the stampede; it moves it to a time you did not choose and then repeats it every TTL forever. Eager warm-up pays one fill per deploy, at a moment you control, with a concurrency you can stagger. Lazy pays one fill at first traffic after every deploy and recycle, plus a synchronized re-fill every 10 minutes for the life of the process.

The bigger reversal is on correctness. "A cold cache is trivially correct — there is no warm-up path that can populate stale or partial data" is backwards. Lazy fill *is* a warm-up path, spread over arbitrary times, so a fill that straddles a bulk import pins a torn view: some entries pre-import, some post-import, frozen together for 10 minutes. A single-snapshot warm query is strictly more coherent than lazy fill, not less. The same defect appears between the two cache shapes: `all_products` and the per-id entries are filled and expire independently, so the list page and the detail page can disagree about the same product's price for up to 10 minutes. "Stale" was accepted. "Self-contradictory within one session" was not.

##### On point 6 (CDN)

Uncontested. I never argued for a CDN, and both added reasons are sound. It argues against a third option; it says nothing about the first two.

##### On point 7 (the flag makes this a cheap reversible experiment)

The load-bearing sentence is factually wrong. "Rollback is an environment variable, not a revert, not a redeploy" — an env var is read at process boot. Changing `CATALOG_CACHE` requires restarting all 8 gunicorn workers. That is a deploy toggle, not a kill switch, and the moment you want it is the moment restarting 8 workers cold into a degraded Postgres is most dangerous. The design's headline safety property costs the exact operation you are trying to avoid.

The second half is worse for the Advocate: "it manufactures the data the expensive decision needs" is conditional on something measuring, and the design specifies zero metrics. A week in staging with no counters produces no hit rate, no memory profile, no stampede signal, and no staleness data. The strongest structural argument in the steelman is true only if Objection 5 is adopted first.

##### On point 8 (open questions are parameters, not refutations)

Granted for threading, jitter, and pagination-keying. Refused for region, on the Advocate's own numbers. He writes "4 regions and 100MB/worker (still trivial)" — that is 800MB fleet-wide before counting the `all_products` duplication, which at 4 regions adds another ~96MB per worker. A "parameter" whose resolution multiplies the design's stated resource claim by roughly 8x is exactly the kind of unknown that can invalidate "fine for our 8 gunicorn workers." And "it is a one-line change" is an argument for making the change before shipping, not for shipping without it. The hazard in Objection 1 was never that it is hard to fix; it is that it is silent if unfixed.

##### On point 9 and the evidence standard

Simplicity is real, and I grant that 50 lines with no new deployable is a genuine advantage. But the blast radius claim is wrong: region bleed is not "one process," it is every customer in the wrong region across the fleet, and it is not cured by the restart the Advocate points to. The 50-line figure is also the version without jitter, single-flight, bounds, region keys, or metrics — the additions the Advocate concedes in point 8. The honest count is closer to 150 lines and one dependency, still cheap, but the number can no longer be used to resist the additions that make it correct.

On the four items in "what evidence would move me": Phase 3 records three of them as *unknown*, not as false. A standard nobody can currently evaluate in either direction is not a fixed standard. Measuring is what fixes that, which is Objection 4.

#### Re-assessment of the objections

##### Objection 1 (no region dimension in the cache key) — sustained, and now the strongest

Nothing in the steelman contests it. Point 8 concedes the fix is needed and calls it one line; point 4's staleness arithmetic covers old data, not wrong data. The Advocate's own memory figure for the fix (100MB/worker at 4 regions) makes it a cross-cutting change to the memory claim rather than a local edit. Unchanged demand: state in the doc where pricing is applied, what carries the region, how many regions exist, and either key on `(region, product_id)` with redone memory math or make the cached value provably region-free with a test that fails if a region-scoped field ever enters it.

##### Objection 2 (lazy fill, flat TTL, no single-flight) — sustained, one claim narrowed, one added

Narrowed: I called the overlap between a miss wave and a bulk import "a coin flip over a 10-minute cycle." Import frequency is unknown, so that probability is unsupported and I withdraw it. The objection does not need it — the periodic 8-worker full-catalog re-scan every 10 minutes is a permanent cost that exists whether or not it ever collides with an import.

Added, from the Advocate's point 5: lazy fill can capture a torn mid-import view and pin it for the TTL, and independently-filled `all_products` and per-id entries can contradict each other. Both are fixed by the same change as Objection 3's deduplication — fill from one snapshot query, derive point reads from it. Jitter, single-flight, and stale-while-revalidate with a hard stale ceiling all stand.

##### Objection 3 (memory model) — sustained, with one sub-claim dropped

Dropped: the "3–10x Python heap multiplier, 25MB becomes 150MB+ RSS" sub-claim. The design says `serialized_product`, and the Advocate's point 2 leans on the value already being serialized bytes; a 2KB `bytes` object carries roughly 33 bytes of overhead, so the multiplier applies only if entries are stored as live dicts, which the doc gives no reason to assume. That number was wrong and I withdraw it.

What remains is stronger without it: `all_products` is a second full copy (~48MB per worker floor, not 25MB), point 8 multiplies that by the region count (~192MB per worker at four regions, ~1.5GB fleet-wide), there is no `maxsize` and no eviction so a 60k catalog degrades into an OOM rather than a hit-rate drop, and negative lookups are unspecified — uncached means `/products/<random>` bypasses the cache entirely, cached means unbounded growth from a URL loop. The doc still states no container limit to measure "fine" against.

##### Objection 4 (no measurement) — narrowed to its defensible core

Dropped: the claim that the cache may be the wrong tool. Point 2 convinced me — the cached value is the serialized form, so a hit removes the query, the ORM hydration, and the serialization pass, which covers every bucket the 180ms could decompose into, and pool wait shrinks in proportion to hit rate rather than surviving it. The cache will help under any plausible decomposition. I withdraw "the Postgres story may be a red herring."

Sustained: the doc names no target p95, no expected hit rate, and no rollback trigger, so there is no condition under which this design can be judged to have failed. And one hour of `pg_stat_statements` on the list query is still worth spending first, because a missing index is the one outcome where the cache works and is still the wrong fix — it would deliver the same latency with zero staleness, zero memory, and zero region hazard, and shipping the cache would hide it permanently.

##### Objection 5 (rollout cannot detect any of this) — sustained and promoted

The steelman raised this objection's value rather than lowering it. Point 7 argues the design's central merit is that it manufactures the data for the next decision, and the design collects nothing; point 7 also claims a rollback that a boot-time env var cannot deliver. Unchanged demands, now with the Advocate's own case behind them: ship `cache_hits`, `cache_misses`, `cache_entries`, `cache_bytes`, `refresh_failures`, and a served-age histogram in the same PR; make the flag runtime-readable so a kill switch is not a fleet restart; roll out by traffic share against a live control group rather than by environment; and write the numeric revert triggers into the doc.

### Advocate's rebuttal

#### Objection 1 (region in the cache key) — conceded in part, on the evidence of the document's own contradiction

I dispute the severity and the likely branch; I concede the demand.

The dispute first. The document does not have one dimension where it needs two by accident of carelessness. It uses two different nouns in the two places the Adversary reads as contradictory. Line 13 caches `serialized_product`. Section 6 says *responses* are personalized with per-region pricing. Product and response are not the same object, and the design keeps them apart in exactly the place where conflating them would be the bug. That reading also explains why section 6 exists at all: the CDN was rejected *because* personalization happens at response-assembly time, which is downstream of anything a shared edge or a shared cache could hold. A design that baked prices into the cached value would have had no reason to describe the CDN problem as cache-key work it had not done.

So the branch the Adversary treats as a coin flip is not one. The plain reading of the text is the post-read-overlay design, which is also the Adversary's own preferred resolution. On that branch the memory arithmetic does not multiply by region count, the `all_products` blast radius does not exist, and the fix is a test asserting an invariant that the design already holds.

The concession. That reading rests on one word, and an invariant that lives in a word choice is not an invariant. The Adversary is right that this must be written into the design as a stated rule with a test that fails when a future field addition puts a region-scoped value into a cached object. I take that as written, including the requirement that the doc name what carries the region on a request. The cost is a paragraph and a unit test, and the failure it prevents is silent and financial. There is no argument for declining it.

What I do not concede: that this is a refutation of the design's shape. Both branches of the Adversary's own "better way" leave the in-process dict, the TTL, the lazy fill, and the flag intact. This is a specification gap in a correct-shaped design, and it is cheap to close before code.

#### Objection 2 (synchronized expiry, no single-flight) — the "load amplifier" claim is false as stated; the fixes are partly conceded anyway

The load-bearing claim is that the miss wave is "a strictly worse read-latency spike than today's steady query stream." That is arithmetically wrong, in two independent ways, and it is the claim the whole objection rests on.

**Aggregate volume.** Under the design, the `all_products` query runs 8 times per TTL cycle: 48 full-catalog queries per hour, fleet-wide. Today it runs once per request to `/products`. At 1 rps that is 3,600 per hour. The crossover point where the cache stops reducing full-catalog query volume is roughly one list request every 75 seconds. Below that rate the endpoint is not a latency problem worth a design doc. At any traffic level that motivates this document, the cache cuts full-catalog query load by two to four orders of magnitude, and the periodic wave is a rounding error against what Postgres absorbs continuously today.

**Instantaneous concurrency.** With 8 gunicorn sync workers, the maximum number of concurrent Postgres queries the API can generate is 8. That is the whole process pool. A synchronized miss wave produces 8 concurrent full-catalog queries, which is precisely the concurrency the uncached system sustains at every busy moment right now. The wave cannot be worse than steady state because the wave *is* steady state, arriving for a few hundred milliseconds every ten minutes instead of continuously. Single-flight per key is a no-op under sync workers: one request per process at a time means there is never a second concurrent miss on the same key within a process to deduplicate.

The objection therefore does not stand on its own; it stands on the unknown from Phase 3. If workers are gthread or gevent with concurrency N per process, the wave is 8N concurrent queries and single-flight becomes load-bearing. That makes worker class a verification item that selects a 15-line addition, which is what my point 8 claimed this class of unknown does.

The same inversion applies to the import claim. Today, during a bulk import, one hundred percent of reads queue behind degraded Postgres. With the cache, the fraction that touches Postgres during an import is the miss rate. The design reduces import exposure by whatever the hit rate is; it does not do "the opposite at the worst moment." The worst moment is worse than the average moment under both designs, and it is strictly less bad under this one.

**Conceded.** Jitter, which I had already argued for in point 8 and now take as required rather than optional. And stale-while-revalidate, which I concede on the argument's merits: it is the change that converts "insulate reads from import spikes" from a hit-rate-proportional benefit into a near-total one, and the PM has already priced staleness, so extending the window under database distress is a small marginal ask against a decision already owned. The hard stale ceiling comes with it, for the reason given.

I flag the cost honestly rather than accepting it silently: SWR requires a background refresh path in every worker, which is real machinery, and it introduces the one failure mode TTL-only did not have — a refresh that fails forever while readers see success. The ceiling and a `refresh_failures` counter are not optional decorations on SWR; they are what makes it safe. This is the point where my point 9 starts to cost something, and I address that below.

#### Objection 3 (memory) — the double-storage arithmetic is conceded outright; the 150MB+ figure is not

**Conceded, from the design's own text.** `all_products` is listed as a key alongside the per-id entries, not as a list of references to them. That is a second full copy. The floor is ~50MB per worker and ~400MB fleet-wide, not the 25MB and 200MB the document states and that I repeated in point 1 as "checkable." It was checkable, and it checks out at double. The fix the Adversary proposes — one canonical `bytes` per product with `all_products` holding references, or the reverse — costs nothing and removes the copy entirely, so this is a correction to make rather than a tradeoff to weigh.

**Disputed: the 3–10x representation multiplier.** That estimate is computed for entries "stored as Python dicts rather than `bytes`." The design's cache shape says `serialized_product`. For 12k `bytes` objects the overhead is roughly 33 bytes of object header each plus about 100 bytes per dict slot, call it 2MB against 24MB of payload. The "25MB of payload can be 150MB+ of RSS" figure requires substituting a different design for the one on the page — and it is the same substitution Objection 1 makes in the other direction. Serialized storage is the design's decision, it is load-bearing for my point 2, and the memory objection does not survive it.

**Disputed: the scraper bypass.** If `/products/<random>` misses are not cached, those requests reach Postgres — which is exactly what all requests do today. That is not a new attack surface introduced by the cache; it is the unchanged status quo for a request class the cache declines to serve. The unbounded-growth branch requires assuming the design caches negative lookups, which it never says. "Read Postgres, store, return" on a nonexistent id has nothing to store.

**Conceded, cheaply:** measure RSS rather than estimate it, and put the measured number next to the container limit in the doc. I named the container limit in advance as evidence that would move me. The Adversary has not produced one, because Phase 3 says it is unknown — so this objection has not met my stated standard, but the standard is trivially cheap to satisfy and the doc is weaker for asserting "fine" against an unnamed limit. A `maxsize` with LRU is insurance I would take at the price quoted.

#### Objection 4 (unvalidated 180ms) — the measurement is conceded; the decomposition mostly argues for this design, and the narrow first cut is worse than the full one

**Conceded:** the afternoon of measurement, and the target p95 plus expected hit rate plus rollback trigger written into the document. The second one matters more than the first. My point 7 argued this is the cheapest reversible experiment worth running, and an experiment with no success criterion is not an experiment, it is a deployment. That is a genuine hole in the case I made and the Adversary found it.

But run the Adversary's own three-way decomposition to its conclusions and two of the three branches favor this design.

*Serialization-dominated:* the Adversary says caching serialized bytes is "the whole win." The design caches serialized bytes. This branch is a point for the artifact, not against it.

*Query-time-dominated:* the cache removes the query. Straightforward win.

*Pool-wait-dominated:* the Adversary claims the cache "removes it only for hits and leaves every miss queued behind the same exhausted pool." That reasoning treats pool wait as a constant per request, and queueing does not work that way. Wait time scales as ρ/(1−ρ). A pool at ρ = 0.95 imposes roughly 19 service times of queueing; remove 90% of arrivals via cache hits and ρ falls to 0.095, where queueing is about a tenth of one service time. The misses do not queue behind an exhausted pool, because the pool is no longer exhausted once the cache has absorbed the arrivals that exhausted it. Under the pool-wait hypothesis the cache helps *more* than under the query-time hypothesis, not less. This is the branch the Adversary treats as most damaging and it is the strongest one for the design.

The missing-index branch is the only genuine one, and a cache and an index are not alternatives. Both should exist if the index is missing.

**Disputed on its merits: "ship only `all_products` first."** This is internally inconsistent with Objection 2. The narrow cut is one hot key, holding the entire catalog, expiring simultaneously across 8 workers — the exact shape Objection 2 correctly identifies as the sharpest edge in the design, now with the per-id cache removed so that every list-key miss must do the full-catalog work with no partial fallback. It also delivers zero improvement to `/products/<id>`, one of the two endpoints named in the problem statement, so it cannot produce the hit-rate data for point reads that the Adversary wants it to produce. The full design's per-id map is what makes the single blob's expiry survivable. Narrowing concentrates the risk the Adversary just finished objecting to.

#### Objection 5 (rollout emits nothing) — conceded almost entirely; this is the objection that lands hardest

**Conceded without reservation:** metrics ship in the same PR as the cache. `cache_hits`, `cache_misses`, `cache_entries`, `cache_bytes`, `refresh_failures`, served-entry-age histogram. My point 7 claimed the flagged rollout "manufactures the data the expensive Redis decision needs." As written, the design manufactures no data at all. That claim was false and the Adversary proved it from the document's own silence. Instrumentation is what makes point 7 true rather than aspirational, so I am not conceding a point against my case — I am conceding that my case requires a change the document does not contain.

**Conceded:** rollback triggers as numbers in the doc, for the same reason as Objection 4's target.

**Conceded, and stronger than the Adversary claims:** rolling out by traffic share rather than by environment. Worth naming that the design makes this nearly free and does not notice. A boot-time per-process env var means canarying to one worker in eight is setting the variable on one worker — the flag mechanism the Adversary criticizes is precisely what gives a same-traffic control group without any new machinery. That should be written into the rollout section.

**Disputed: the incident-restart argument.** The claimed harm of a boot-time flag is having to "restart 8 workers with cold caches into a degraded database." But the action being taken is turning the cache *off*. Post-flip, every request goes to Postgres by definition, whether the flip happened at runtime or through a graceful `SIGHUP` reload. There is no cold-cache penalty attached to a decision to stop using the cache; the two paths converge on identical Postgres load. A runtime-flippable flag is nicer and I would take it, but the incident scenario offered as its justification cancels itself out, and this belongs well below instrumentation in priority.

**Disputed in part: "staging proves nothing."** Overstated. A staging week with a multi-region smoke test is exactly where the Objection 1 hazard gets caught before a customer sees a wrong price, and it catches crashes, leaks with an obvious slope, and serialization bugs. It is not evidence about hit rate, production memory, or stampede behavior, and the Adversary is right that the doc treats it as though it were.

#### Steelman points that fall or need amending

Naming these rather than leaving them for the Judge to find.

**Point 1 — "200MB total, checkable."** Falls at the stated figure. The floor is ~400MB because `all_products` is a second copy, provable from the design's own cache shape. The argument that the dataset is small enough for per-worker duplication survives at 400MB, but the specific number I praised as checkable was wrong, and the doc's confidence in it was unearned.

**Point 5 — "lazy is self-limiting, 25MB is a ceiling and the working set is likely smaller."** Falls for half the cache. Read skew shrinks the per-id map, but the first request to `/products` materializes the entire catalog into `all_products` regardless of skew. The self-limiting property applies to point reads only. The rest of point 5 — that eager warm-up would create the deploy-time stampede the design exists to avoid, and that a cold cache is trivially correct — is untouched, and Objection 2's cold-fill-wave concern is an argument against warm-up as much as against lazy fill.

**Point 7 — "the flag rollout manufactures the data the expensive decision needs."** Falls as written, restored by the instrumentation concession above. The reversibility half of point 7 stands entirely: no schema change, no new deployable, no infrastructure to decommission, and nothing in Objections 1 through 5 disputes it.

**Point 8 — "the open questions are parameters, not refutations."** Holds for worker class, pagination, and expiry herding, each of which resolves into a bounded addition that leaves the design's shape intact, exactly as claimed. It does not hold for region. A contradiction between two sections of the same document is not a parameter awaiting a value; it is an unresolved question about what the design *is*, and it has to be settled in prose before anyone writes code. Partially conceded.

**Point 9 — "simplicity, on the order of 50 lines."** Weakened and I will not defend the number. Jitter, single-flight where the worker class requires it, stale-while-revalidate with a ceiling, `maxsize`, and six metrics is more like 150 to 250 lines. What survives is the part that was actually load-bearing: still zero new infrastructure, still no new deploy artifact, still no new on-call surface, still a blast radius of one process, and still deletable in a single PR. The gap between 50 lines and 250 lines of in-process Python is not the gap that made the Redis comparison lopsided.

**What is unmoved.** Points 2, 3, 4, and 6 drew no fire. The Redis bandwidth argument, TTL's stateless convergence against event-driven invalidation's unbounded silent staleness, the 0.003% catalog-time staleness arithmetic, and the CDN's failure to protect the origin at the moment of an import all stand unchallenged. Those are the four load-bearing bets. Every objection sustained above is an addition to this design or a correction inside it, and not one of them proposes replacing it with Redis, a CDN, or event-driven invalidation. The Adversary and I now disagree about a bill of amendments, not about the plan.

## Phase 6 — Judge's Final Report

### Agreed changes

Both sides now support these. The Advocate conceded each one explicitly in rebuttal; several he conceded outright as corrections rather than tradeoffs.

1. **Deduplicate the two copies of the catalog.** `all_products` is listed as a key alongside the per-id entries (line 13), not as a list of references, so the floor is ~48–50MB per worker and ~400MB fleet-wide, not the ~25MB and ~200MB the doc asserts (line 18). Fix: one canonical `bytes` per product, with `all_products` holding references — or store the assembled blob and derive point reads from it. Advocate: "It was checkable, and it checks out at double."
2. **Fill from a single snapshot.** Same change as (1), and it also closes the Adversary's late-added defect: independently filled `all_products` and per-id entries can disagree about the same product's price for up to 10 minutes, and a lazy fill straddling a bulk import pins a torn view. Nobody priced "self-contradictory within one session."
3. **Resolve the region question in prose before code.** State where per-region pricing is applied relative to the cache read, what carries the region on a request, and how many regions exist. Then either key on `(region, product_id)` and `all_products:{region}` with the memory math redone, or make the cached value provably region-free and add a test that fails when any region-scoped field enters a cached object. Advocate: "an invariant that lives in a word choice is not an invariant… There is no argument for declining it."
4. **Jitter the TTL** (`600s × uniform(0.8, 1.2)` per entry). Advocate had already argued for it and now takes it as required.
5. **Stale-while-revalidate with a hard stale ceiling** (~60 min) plus a `refresh_failures` counter. Advocate conceded on the merits and correctly flagged that SWR introduces the one failure mode TTL-only lacks — a refresh failing forever behind successful-looking reads — so the ceiling and the counter are load-bearing, not decoration.
6. **Metrics in the same PR as the cache:** `cache_hits`, `cache_misses`, `cache_entries`, `cache_bytes`, `refresh_failures`, and a served-entry-age histogram. This is the concession the Advocate made most completely: his point 7 claimed the flagged rollout "manufactures the data the expensive Redis decision needs," and as written the design manufactures nothing.
7. **Write numbers into the doc:** a target p95, an expected hit rate, and the rollback triggers. "An experiment with no success criterion is not an experiment, it is a deployment."
8. **Measure before shipping:** `pg_stat_statements` for both endpoint queries, pool-checkout wait, a `py-spy` profile at peak, and a measured RSS delta after loading 12k products — with the measured number placed next to the container memory limit in the doc.
9. **`maxsize` with LRU eviction** so catalog growth degrades hit rate instead of OOM-killing a worker. Advocate: "insurance I would take at the price quoted."
10. **Roll out by traffic share in production against a live control group,** not by environment alone. Both sides now agree; see the mechanism caveat in Rulings 6.

### Dropped objections

The Adversary withdrew these in rebuttal. This is the record of where the artifact is fine as written.

- **The 3–10× Python heap multiplier ("25MB becomes 150MB+ RSS").** Withdrawn. The design says `serialized_product`, and a 2KB `bytes` object carries ~33 bytes of header, not 3–10× the payload. The Adversary conceded that the multiplier only applies if entries are stored as live dicts, which the doc gives no reason to assume. (The Advocate disputed this figure too, apparently without having seen the withdrawal — both sides landed in the same place.)
- **"The cache may be the wrong tool; the Postgres story may be a red herring."** Withdrawn on the Advocate's point 2. Because the cached value is the serialized form, a hit removes the query, the ORM hydration, and the serialization pass, so the cache helps under every branch of the 180ms decomposition rather than only one.
- **"A coin flip over a 10-minute cycle" that a miss wave collides with a bulk import.** Withdrawn as unsupported — import frequency is unknown (Phase 3). The Adversary correctly noted the objection does not depend on it.
- **The CDN rejection (section 6).** Never contested. The Adversary: "Uncontested. I never argued for a CDN, and both added reasons are sound."
- **Worker class, pagination-keying, and expiry herding as design-invalidating unknowns.** Granted as parameterizations that leave the design's shape intact.
- **The "50 lines / no new infrastructure" advantage in its load-bearing form.** The Adversary granted the genuine advantage while disputing the line count; the Advocate then conceded 150–250 lines himself.

### Contested points

**C1 — Severity of the region gap.** *Adversary:* lines 13 and 22 contradict each other; under the shape as written, the first request for product 4711 from `us-east` poisons every region's price for that product for 10 minutes, silently, with `all_products` amplifying it across all 12k products. Strongest surviving objection. *Advocate:* not a contradiction — line 13 caches a *product*, line 22 personalizes a *response*; the plain reading is a post-read overlay, which is also the Adversary's own preferred branch, so the memory multiplication and the blast radius do not exist. Concedes the demand, disputes that it refutes the design's shape.

**C2 — Is the miss wave a "load amplifier"?** *Adversary:* lazy fill correlates fill times, so TTLs expire in a synchronized wave; 8 workers each run a full-catalog query every 10 minutes forever, with no single-flight, which is "a strictly worse read-latency spike than today's steady query stream." *Advocate:* arithmetically false twice over. Aggregate: 8 full-catalog queries per TTL cycle = 48/hour, versus 3,600/hour at 1 rps uncached — crossover is one list request every 75 seconds. Instantaneous: 8 sync workers can generate at most 8 concurrent queries, which is exactly today's busy-moment concurrency, so single-flight is a no-op under sync workers.

**C3 — Does `/products` really return 24MB?** *Adversary (rebuttal, unanswered):* if it does, 180ms p95 implies 133 MB/s sustained through ORM hydration of 12k rows plus Python serialization, which is not credible — so either the endpoint is paginated/field-limited (and `all_products` as one blob is wrong as a design, which is one of the Advocate's own named movers) or the 180ms is measuring egress rather than Postgres. Also: Redis stores serialized bytes too, so "in-process avoids serialization entirely" is not a differentiator; the real Redis delta is the hop plus transfer, and nobody puts a 24MB value in one Redis key. *Advocate:* no reply on the credibility dilemma; his point 2 (Redis bandwidth) is listed as "unmoved."

**C4 — Does the 3,000–10,000× lookup ratio select in-process?** *Adversary (rebuttal, unanswered):* against a 180ms baseline, 100ns and 500µs are 0.000056% and 0.28% — both round to zero on user-visible p95, so latency cannot select between them; "no new infrastructure" (point 7) is the real argument. *Advocate:* did not reply.

**C5 — Scraper bypass and negative lookups.** *Adversary:* uncached misses on nonexistent ids let `/products/<random>` bypass the cache; cached ones grow the dict without bound. *Advocate:* uncached misses reaching Postgres is the unchanged status quo, not a new attack surface, and the doc never says negative lookups are cached — "read Postgres, store, return" on a nonexistent id has nothing to store.

**C6 — Ship only `all_products` first?** *Adversary:* narrower risk surface, one region dimension, trivial memory, and it yields hit-rate data. *Advocate (unanswered):* internally inconsistent with Objection 2 — it keeps the single hot key expiring simultaneously across 8 workers while removing the per-id map that makes that expiry survivable, and delivers zero improvement to `/products/<id>`, so it cannot produce the point-read data it is meant to produce.

**C7 — Is the boot-time env flag a kill switch?** *Adversary:* no — flipping it restarts all 8 workers cold into a degraded Postgres at the worst moment. *Advocate (unanswered):* the action is turning the cache *off*, after which every request goes to Postgres by definition; the two paths converge on identical load, so the cold-cache harm cancels. Also claims the per-process env var makes a same-traffic canary free.

**C8 — Does the staging week prove anything?** *Adversary:* no production volume, region mix, cardinality, or imports, so it is not evidence on the four things most likely to break. *Advocate:* overstated — a staging week with a multi-region smoke test is exactly where the C1 hazard gets caught before a customer sees a wrong price; it is not evidence about hit rate, memory, or stampedes.

### Rulings

**R1 (C2) — Advocate wins the headline claim; Adversary keeps the remedy.** I checked the arithmetic: 3600/48 = 75 seconds, and 8 sync workers can hold at most 8 in-flight queries. At any traffic level that justifies this document, the cache cuts full-catalog query volume by orders of magnitude, and the wave's peak concurrency equals today's steady-state concurrency. "Strictly worse than today" is false as stated, and the Adversary should not have led with it. But the fixes survive independently — jitter is conceded, SWR is conceded, and single-flight resolves on the worker-class unknown. **Compromise:** the Adversary gives up "load amplifier"; the Advocate gives up treating worker class as a detail. Make it a blocking verification item: if the workers are `gthread` or `gevent` with concurrency N, the wave is 8N and single-flight ships; if they are sync, it does not. The artifact gains a stated worker-class fact and a conditional 15 lines instead of an argument.

**R2 (C1) — Split, and both sides overstate.** The Advocate is right that "contradiction" is too strong: line 13 says *product*, line 22 says *responses*, and those are different objects. But his supporting inference does not hold — a CDN caches *responses*, so "cache-key work we don't want to do now" is equally true under a post-read-overlay design. Section 6 is consistent with either branch; the doc is silent, not self-contradicting. The Adversary is right about what silence costs: the failure is a correct-looking 200 with the wrong price, found in a billing dispute, and the memory claim in line 18 is conditional on the answer (at 4 regions with prices baked in, the Adversary's ~192MB/worker and ~1.5GB fleet figures check out). Since the Advocate conceded the full remedy, the dispute is only about how to label it. **Ruling:** it is a specification gap in a correct-shaped design, and it blocks code. Both branches of the fix leave the dict, the TTL, the lazy fill, and the flag intact — the Adversary won the demand, the Advocate won the claim that the shape survives.

**R3 (C3) — Adversary wins, and this is the most under-weighted point in the debate.** 24MB / 0.18s = 133 MB/s is correct, and it is not a plausible throughput for ORM hydration of 12k rows plus Python serialization plus gunicorn. Something in the doc's implied picture is wrong. The Advocate's closing claim that "points 2, 3, 4, and 6 drew no fire" is contradicted by the transcript — the Adversary's rebuttal attacks points 2, 3, and 4 by name — so his summary of the Redis argument as unmoved does not stand. **Consequence:** the Redis-bandwidth argument (point 2) is not load-bearing; the Redis rejection survives on point 7's reversibility-and-no-new-infrastructure grounds, which nobody disputed. Add to the agreed list: **state what `/products` actually returns** — full catalog, page, or field-limited projection — and what the 180ms is measured on. If it is paginated or filtered, `all_products` as a single blob has to be re-specified, which the Advocate himself named as evidence that would move him.

**R4 (C4) — Adversary wins, narrowly and cheaply.** Both figures check out (0.000056% and 0.28% of 180ms). Line 20's "a network hop per read defeats the latency goal" is weak reasoning for a conclusion that is nonetheless right. Fix the sentence, not the decision: rewrite the Redis rejection to rest on operational cost and reversibility rather than on nanoseconds.

**R5 (C5) — Advocate wins on the attack-surface framing; Adversary wins a line of spec.** Misses reaching Postgres is today's behavior, not a regression the cache introduces, and the doc never claims to cache negatives. But leaving it unstated is what let the argument happen. **Compromise:** one sentence saying negative lookups are not cached, or are cached in a separate small short-TTL negative cache. Cost: a sentence.

**R6 (C6, C7) — Advocate wins both, with one correction of my own.** The narrow-first-cut proposal is internally inconsistent with Objection 2 and abandons one of the two named endpoints; drop it. On the flag: the Adversary is right about the *mechanism* (an env var is read at process boot, and a gunicorn `SIGHUP` reload does not re-read a changed master environment, so flipping it is a redeploy, not a kill switch) and the Advocate is right about the *consequence* (there is no cold-cache penalty attached to deciding to stop using the cache). Net: runtime-flippability is a real nice-to-have that ranks well below instrumentation. **My correction to the Advocate:** "canarying to one worker in eight is setting the variable on one worker" is wrong under gunicorn's prefork model — workers inherit the master's environment, so a same-traffic control group needs a separate deployment or pod with the flag on, or a decision keyed off worker id. The traffic-share rollout is still right; the mechanism has to be written down rather than assumed free.

**R7 (C8) — Compromise, close to the Advocate's version.** A staging week catches crashes, obvious leak slopes, serialization bugs, and — with an explicit multi-region smoke test — the C1 hazard, which is worth having before a customer sees a wrong price. It is not evidence about hit rate, memory, or stampedes, and the doc currently treats it as though it were. Keep the staging week, add the multi-region smoke test to it as a named exit criterion, and stop calling it the evidence stage; production traffic-share with metrics is the evidence stage.

**R8 (uncontested, for the record)** — the four bets the Adversary never attacked stand: TTL's stateless convergence against event-driven invalidation's unbounded silent staleness (the Adversary confirmed he never asked for event-driven invalidation, so this point is correct and inert), the CDN rejection, the flag's reversibility, and the basic read:write shape. The staleness arithmetic (0.003% of catalog-time) survives only for the "50 independent edits" reading; the Adversary's counter is sound — if one import touches 3,000 rows, 25% of the catalog is stale in every worker at once, and that arithmetic checks out. Whether the 50 daily changes are edits, imports, or a mix is unknown per Phase 3 and belongs in the doc.

### Judge's recommendation

**Do not ship the document as written, and do not narrow it. Close the two specification gaps in prose, spend the measurement afternoon, then implement the full design with the ten agreed changes behind the flag, with production traffic-share as the real rollout.**

The reasoning: the Adversary attacked the design's *shape* in Objections 2 and 4 and lost both — his own withdrawals in rebuttal ("I withdraw the Postgres story may be a red herring") plus the queueing and concurrency arithmetic settle that an in-process serialized-bytes cache is the right tool for this workload. But he won nearly the whole bill of amendments, and the Advocate conceded it almost without resistance, including the concession that his own strongest structural argument — "the flag manufactures the data the expensive decision needs" — is false about the document as written. A design whose best argument is falsified by its own silence needs the instrumentation before it needs anything else.

Two things block code rather than accompany it: what `/products` returns (R3) and where region pricing is applied (R2). Both are prose, both are cheap, and both change downstream numbers — the first decides whether `all_products` is even the right shape, the second decides whether line 18's memory claim is off by a factor of R. Everything else on the agreed list is implementation.

Priority order if effort is constrained: metrics and numeric targets first (without them nothing else can be evaluated), then dedup and the region invariant, then jitter, then SWR with its ceiling, then `maxsize`, then the runtime-flippable flag last.

### Your decision

1. **Amended design (my recommendation).** Answer the two prose questions, run the measurement afternoon, implement the full design plus the ten agreed changes, staging week with a multi-region smoke test, then 1 worker → 25% → 100% by traffic share against a live control group with numeric revert triggers. Cost: roughly 150–250 lines instead of 50, one afternoon of measurement, and a day of doc work. Buys: the latency win with the silent failure modes made loud.
2. **Amended design, minus SWR.** Everything in option 1 except stale-while-revalidate. Gives up the near-total import insulation that SWR buys, keeps TTL's single bounded failure mode, and avoids the background-refresh machinery plus its forever-failing-refresh hazard. Reasonable if the import spikes turn out to be rarer or milder than the problem statement implies — the measurement afternoon will tell you.
3. **Ship as written, behind the flag, today.** Accepts an unmeasured 180ms, no success criterion, an unspecified region behavior whose failure is a silent wrong price, and ~400MB fleet-wide rather than the stated 200MB. Defensible only if you treat the flag as a true experiment and are willing to fly blind for a week; both debaters, including the Advocate, argued against this.
4. **Measure only, decide later.** Spend the afternoon on `pg_stat_statements`, pool wait, and `py-spy`, and defer the cache. Worth choosing if you suspect the missing-index branch — it is the one outcome where the cache works and is still the wrong first fix. Note both sides agreed a cache and an index are not alternatives, so this delays rather than replaces option 1.
5. **Redis.** Nobody in this debate argued for it, and the Adversary explicitly did not. Choose it only if the region count or catalog growth makes per-worker duplication untenable — which is a number you do not have yet and which the agreed measurements would produce.
