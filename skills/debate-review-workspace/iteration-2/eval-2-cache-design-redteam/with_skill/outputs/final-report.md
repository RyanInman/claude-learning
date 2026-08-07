# Judge's Final Report — Product Catalog Read Cache Design

## Agreed changes

Both sides now support these; they are ready to act on.

1. **Pre-build verification (one hour of code reading, before any cache code).** Confirm where per-region pricing is applied relative to the cached value, state the region count, and enumerate the `/products` parameter space. The Advocate conceded this cannot wait: "building against an unverified correctness invariant is not acceptable." Record the verified answers in the doc as stated invariants, and add the test asserting two regions get different prices with the cache on — the Adversary's ask, which the Advocate accepted in full.
2. **`cache_generation` purge lever.** An integer in Postgres, checked by each worker at most every ~10 seconds; on change, drop the dict. The Advocate endorsed it as "a victory for the design's principles": a <10-second purge with no new infrastructure. This closes the takedown/urgent-price-fix gap.
3. **Correct the rollback sentence.** "Rollback is a flag flip" is factually false as designed — gunicorn reads the environment at fork, so the flag needs a worker restart. Both sides agree the doc must name the real procedure (restart, or the generation counter making the flag effectively live) and its expected duration.
4. **TTL jitter and stale-while-revalidate on `all_products`.** ~30 lines, no infrastructure. The Advocate conceded on cost grounds: "the cheap fix is cheaper than the argument."
5. **If `/products` takes parameters: cache per-product entries only** and assemble list responses in process. The Advocate called this "strictly better than variant-keyed list caching." (See my note under Rulings — I recommend it even if no parameters exist.)
6. **Rewrite the Redis justification and set a target p95.** Both sides agree "a network hop per read defeats the latency goal" overclaims. Rest the justification on component-wise dominance plus operational simplicity, and state a target p95 so the staging week has a pass/fail criterion.

## Dropped objections

- **"Redis deserves reconsideration" (Objection 5, first half).** The Adversary withdrew it explicitly. What answered it: the Advocate's dominance argument (an in-process hit is ≤ a Redis hit on every latency component, so no measurement can flip the winner), plus the fact that the agreed remedies — generation counter, jitter, stale-while-revalidate — deliver Redis's only distinctive advantages without Redis. The architecture question is settled: in-process stands.
- **"TTL expiry recreates the exact problem" (Objection 3, original framing).** The Adversary dropped the framing after the Advocate's arithmetic: refill queries are a subset of what the status quo issues anyway, so DB load with the cache never exceeds today's. What survives is only the p99 tail at TTL boundaries — covered by agreed change 4.
- **The measurement gate (Objection 5's "spend a day measuring before building").** Never formally withdrawn, but the Adversary's rebuttal quietly relinquished it — the surviving asks are the target p95 and the honest justification, both agreed. The Advocate is right that measurement here refines the size of the win and cannot change the decision. I treat this as dropped.

## Contested points

**A. Architectural weight of the region-pricing question.** Adversary: the region count decides whether a bad resolution is a key tweak or an architecture fork — at 25 regions, ~5GB across workers, per-worker duplication stops being cheap and Redis's shared cache becomes real. Advocate: both resolution branches keep in-process; even baked-in pricing resolves to a compound key or, better, refactoring pricing to apply after the cache read.

**B. Scope of the ~45 lines for v1.** Adversary: generation counter plus stampede control belong in v1 — "the difference between a design that is right when its assumptions hold and one that is safe when they don't." Advocate: conceded the generation counter and jitter/SWR outright, but held that per-key single-flight is conditional — the in-worker stampede exists only if workers are threaded or async, which the doc does not state.

**C. Memory math (Adversary's new finding, unanswered).** The `all_products` value is itself a ~24MB serialized blob on top of the 12k × 2KB ≈ 25MB of per-product entries, so the doc's quoted footprint is roughly half the real one. The Advocate's rebuttal was written against the Adversary's case, not his rebuttal, so this finding drew no response.

## Rulings

**A — split, favoring the Advocate on the outcome, the Adversary on the burden of proof.** The Advocate wins that no branch yet discovered forces Redis: the pricing-after-read refactor keeps in-process even at large N. The Adversary wins that "small keyed variant" is unproven until N is known — the Advocate's own strongest point (worst case is the status quo) is conditional on this resolving favorably, as the Adversary showed. Practical effect: nothing beyond agreed change 1, which both sides already demand. No compromise needed; the dispute dissolves once the hour of verification runs.

**B — compromise, and it is a real one.** Fold the concurrency check into the agreed pre-build code read: confirm the gunicorn worker class (a one-line config read). Add per-key single-flight only if workers are threaded or async; skip it for sync workers, where concurrent in-worker misses cannot occur. The Adversary gives up unconditional inclusion of all ~45 lines; the Advocate gives up leaving the precondition unchecked. The artifact gains stampede protection exactly where the runtime model can produce a stampede, and no dead code where it can't.

**C — Adversary wins, but severity is low and the fix is already on the table.** I checked the arithmetic against the doc: 12k products at ~2KB is ~24MB serialized, so a cached full-list blob does roughly double the quoted 25MB. ~50MB per worker is still cheap, so this is a doc correctness error, not a viability threat. Adopting the Objection-4 remedy — per-product entries only, list assembled in process — eliminates the blob entirely and makes the quoted math true again. For that reason I recommend the per-product-only shape unconditionally, not just if parameters exist.

## Judge's recommendation

**Build it, amended, without a measurement gate.** The debate converged more than either side's rhetoric suggests: the Adversary's net position endorses the in-process architecture, and the Advocate adopted every surviving remedy. Sequence: (1) run the one-hour verification — pricing application point, region count, `/products` parameters, worker concurrency model; if pricing turns out baked-in with large N, stop and revisit, but no evidence so far predicts that; (2) apply agreed changes 2–6, with per-product-only caching adopted unconditionally and single-flight per ruling B; (3) proceed to the staged rollout against the stated target p95. Total added cost is about an hour of reading and ~45 lines of code; in exchange the design gets a working rollback lever, a sub-10-second purge path, verified correctness invariants, and honest memory math. The reasoning to disagree with: if you trust that pricing is applied post-cache and that takedown urgency never arises, the original doc builds faster — but you would be shipping a rollback sentence both sides proved false.

## Your decision

1. **Build as amended (recommended):** one-hour verification, then the four amendments plus per-product-only caching, then rollout.
2. **Minimal path:** run the verifications and fix the doc (rollback sentence, target p95, memory math), but defer the generation counter and stampede code to v1.1. Faster to ship; leaves takedowns on the 10-minutes-plus-restart path in the meantime.
3. **Build the doc as-is:** rejects findings both sides now agree on, including a factually false rollback claim. Not advisable.
4. **Reopen Redis:** both sides now argue against it; choose this only if the verification reveals baked-in pricing with a large region count.
