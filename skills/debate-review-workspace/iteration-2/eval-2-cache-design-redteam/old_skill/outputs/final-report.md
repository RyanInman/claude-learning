# Judge's Final Report

## Agreed changes

All three roles converged on five amendments. Each is a bounded edit to the document or the
rollout plan; none changes the architecture (in-process dict, lazy fill, TTL, env flag).

1. **Region invariant (O1).** Write into the design: the cache stores the region-neutral product
   row; pricing applies after the cache read, in the response layer. Add a test that requests the
   same product from two regions and asserts different prices. Run the one-hour code read to
   confirm where pricing lives; if it is baked into serialization, key by `(region, product_id)`
   and redo the memory math before approving.
2. **Parameter-space enumeration as a build gate (O2).** Before any build, enumerate `/products`'
   actual parameters from route code and a day of access logs. If the endpoint is canonical, keep
   the single `all_products` key. If it is parameterized, adopt the cache-raw-rows,
   filter-per-request scheme — with the per-request serialization cost measured first.
3. **Emergency flush and PM scenario meeting (O3).** Document the emergency path in the design:
   "emergency flush = disable `CATALOG_CACHE` + rolling restart, measured propagation ≤ X
   minutes, runbook entry." Measure X in staging. Then take the PM a concrete scenario list —
   legal takedown, price correction, and "inconsistent views for up to 10 minutes past import
   completion, on every import" — plus the measured X. Adopt `catalog_version` only if the
   meeting yields a sub-10-minute propagation requirement.
4. **Stampede hardening as implementation notes (O4).** Add ±20% TTL jitter and a per-worker
   refresh flag (serve stale while one request refreshes). Read the gunicorn config and state the
   concurrency model in the design before build.
5. **Observable, criterion-gated rollout (O5).** Emit hit/miss/refresh counters and tag latency
   metrics with cache on/off. Set a numeric success criterion (proposed defaults: p95 under 30ms
   on both endpoints, hit rate above 90%). Gate production default-on on staging meeting the
   criterion, not on a week elapsing.

## Contested points

None remain. Objections 1, 2, 4, and 5 were dropped in Phase 5 after the Advocate's answers;
Objection 3 was sustained in narrowed form, and the Advocate conceded both surviving points in
Phase 6 — the undocumented emergency lever (by the Advocate's own "unstated intent is unenforced"
standard from O1) and the "false safety net" arithmetic (a forgotten `catalog_version` bump
degrades to the TTL bound, not below it). The only residue is a label — "documentation defect"
versus "architectural error" on O1 — which both sides agreed changes no line of the plan.

## Compromises

None needed — all objections resolved in debate.

## Judge's recommendation

**Will the in-process cache bite us? Not as architecture — but the document as written would
have, in three specific ways the debate caught.** The architectural choices survived genuine
pressure: the Adversary himself withdrew the stampede objection once the arithmetic showed a TTL
lapse is a strict load reduction from today's baseline, and no role argued for Redis at 25MB.
The workload — ~50 writes a day against read-dominated traffic — is the textbook case for
TTL-only caching, and every degraded state of the design is the status quo.

The bites were all in what the document left unstated: a cache key that silently omits region
while responses carry region pricing (a wrong-price bug, not staleness), a single `all_products`
key resting on an unverified assumption about the endpoint's shape, and a staleness sign-off
whose scope — takedowns, price corrections, post-import inconsistency — nobody checked with the
PM. Each has an agreed, cheap fix.

Adopt the design with all five agreed changes, and treat two of them as hard gates that can still
reshape the plan: the parameter-space enumeration (which decides the `all_products` mechanism)
and the PM scenario meeting with the measured flush time (which decides whether `catalog_version`
ships). If either gate returns a surprise — a heavily parameterized endpoint, or a PM who needs
fast takedowns — the debate has already agreed on what to do next, so neither outcome reopens the
argument.

Where you might disagree with me: I am siding with the consensus that `catalog_version` stays
conditional. The Adversary's corrected arithmetic shows it is nearly free insurance that fails
back to the documented bound. If your organization's takedown risk is real (regulated products,
DMCA exposure), adding it unconditionally is defensible and costs one indexed read per worker per
second — you would be overriding the debate's sequencing, not its analysis.

## Your decision

1. **Adopt the amended plan (recommended).** In-process cache as designed, plus the five agreed
   changes, with the enumeration and PM meeting as build gates.
2. **Adopt the amended plan but add `catalog_version` now**, without waiting on the PM meeting.
   Choose this if takedown speed is a known requirement; it re-adds write-path coupling the
   design deliberately avoided.
3. **Build the original document as written.** No role — including the Defender — supports this
   after Phase 2; the region-key gap alone is a live wrong-price bug.
4. **Switch to a shared cache (Redis).** No side argued for it; both agreed per-worker
   duplication is correct at 25MB. Choose this only if the enumeration or PM gates return
   answers that break the in-process model (for example, per-region serialized bodies inflating
   memory beyond the fleet's budget).
