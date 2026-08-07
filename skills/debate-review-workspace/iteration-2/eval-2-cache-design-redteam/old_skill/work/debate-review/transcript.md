# Debate Review Transcript

**Artifact:** /Users/admin/claude-learning/skills/debate-review-workspace/iteration-2/eval-2-cache-design-redteam/old_skill/work/cache-design.md
**Date:** 2026-08-06

**Review focus (from the design's owner):** Red-team this caching design before implementation
starts. The owner's central question: will the in-process cache bite us? Argue both sides
properly — this is a pressure test, not a takedown.

Append-only. Each role writes under its own heading and never edits another role's text.

---

## Phase 1 — Defender: Opening Statement

**Goal.** Cut p95 latency on `/products` and `/products/<id>` from ~180ms and stop bulk-import
read spikes, with minimal new moving parts. Catalog reads dominate traffic; the data changes
roughly 50 times a day, so it is an almost-static read-heavy workload — the easiest kind to cache.

**Key decisions and why:**

1. **In-process dict cache, not Redis.** The latency goal is the point of the project. A Redis
   round trip costs a network hop per read and adds a service to provision, monitor, and fail
   over. A local dict read is nanoseconds. The whole catalog is ~25MB serialized, so duplicating
   it across 8 gunicorn workers costs ~200MB total — cheap against the operational cost of new
   infra.
2. **Lazy population.** No warm-up job to build or schedule. First request per key pays the
   Postgres read; everyone after rides the cache. Simple, and the miss path is identical to
   today's behavior.
3. **10-minute TTL, no explicit invalidation.** The PM signed off on up to 10 minutes of
   staleness. That sign-off buys us out of the hardest part of caching — invalidation — entirely.
   No pub/sub, no cache-bust hooks in the write path, no coupling between the catalog team's
   import pipeline and our API workers.
4. **One `all_products` key for the list endpoint.** The list endpoint is the expensive query;
   caching the assembled list directly means one key, one TTL, no assembly cost on hit.
5. **No CDN.** Responses carry per-region pricing, so edge caching needs cache-key
   normalization work we are not ready to do. Deferred, not rejected.
6. **Rollout behind `CATALOG_CACHE` env flag.** Staging for a week, then production. Instant
   kill switch: flip the flag, and behavior reverts to today's direct-read path.

**What I'm least sure of.** Three honest soft spots. First, per-worker TTLs expire independently,
so two consecutive requests can hit workers with different cache ages — cross-worker
inconsistency is visible for up to the TTL. Second, the `all_products` key and the per-id keys
expire independently, so the list and detail views can disagree. Third, cache-miss stampede: when
the `all_products` TTL lapses on a busy worker, several in-flight requests may all run the
expensive list query at once. None of these looked disqualifying at design time, but the
Adversary should press on them — and on anything worse I haven't seen.



## Phase 2 — Clarifying Questions

### Adversary's questions

1. Responses are "personalized with per-region pricing." Is the region-specific price baked into the `serialized_product` stored in the cache, or applied after the cache read? If baked in, how many regions are there, and does the cache key include the region?

2. Does `/products` accept query parameters — pagination, filtering, sorting — or does it always return the full 12k-product list that the single `all_products` key would hold? And roughly what share of traffic and of the 180ms p95 comes from the list endpoint versus `/products/<id>`?

3. What is the gunicorn worker configuration — sync or async workers, and is worker recycling (`max_requests`) or autoscaling in play? I want to know how long a worker's cache actually lives and how many concurrent requests one worker can have in flight during a TTL lapse.

### Advocate's questions

1. What is the gunicorn worker model (sync, threaded, or async), and what is the concurrent request rate per worker on `/products`? I need this to gauge how real the `all_products` stampede window is and whether a dict read/write needs any locking defense.

2. How often do workers restart in practice — deploy cadence, max-requests recycling, autoscaling churn? Frequent restarts already impose cold-cache misses today, which bears on whether lazy population's first-hit cost is a new problem or an existing, tolerated one.

3. Does the PM's 10-minute staleness sign-off cover every write path, including price corrections and product takedowns (legal/compliance removals), or only routine catalog edits? The no-invalidation decision is the design's biggest simplification, and I want to know exactly how far the sign-off extends before I defend it.

### Judge's questions

1. What are the request rates for `/products` and `/products/<id>` (roughly, requests/sec at peak), and are the gunicorn workers sync or async with what concurrency per worker? I need this to judge how severe the acknowledged stampede risk actually is when the `all_products` TTL lapses — a stampede argument reads very differently at 5 rps versus 500 rps.

2. Does the list endpoint support filtering, sorting, pagination, or per-region variation, or is it truly one canonical response? The single `all_products` key only works if the response is one shape; the design mentions per-region pricing in the CDN section, which suggests responses vary by region — if so, what is actually stored under that one key?

3. What does the catalog team's bulk import look like from the readers' side — one transaction, or a rolling window of row updates? During an import, a lazy per-id cache can capture a mix of pre- and post-import products for up to 10 minutes; I need to know whether the PM's staleness sign-off covered "uniformly stale" only, or also "internally inconsistent" (list showing products whose detail pages 404, prices from two import generations side by side).

### Defender's answers

Facts where the design states them, and honest gap-flagging where it doesn't. Several questions
converge on the same three unknowns, so I answer by topic.

**Per-region pricing vs. the cache key (Adversary Q1, Judge Q2).** The design does not specify.
As written, the cache key is `product_id` (plus one `all_products` key) with no region dimension,
while the CDN section says responses are "personalized with per-region pricing." Two readings are
possible: (a) `serialized_product` is region-neutral and pricing is applied after the cache read
in the response layer, or (b) the serialized form includes the price, in which case the key as
designed is wrong — worker A could serve region-1 prices to a region-2 user, which is a
correctness bug, not staleness. The design intends reading (a), but it is not stated and nothing
in the doc enforces it. I classify this as a gap the debate should treat as unresolved, not a
deliberate decision.

**List endpoint shape and traffic split (Adversary Q2, Judge Q1).** Not specified. The design
assumes one canonical full-catalog response for `/products`; pagination, filtering, and sorting
are not addressed. No request-rate numbers or endpoint traffic split were gathered — the only
measured fact is the ~180ms p95 and the import-time spikes. The stampede question therefore
cannot be settled with data on hand; treat request volume as unknown.

**Worker model and lifecycle (Adversary Q3, Advocate Q1, Advocate Q2).** The design says 8
gunicorn workers and nothing else. Sync vs. async/threaded is unspecified, as are `max_requests`
recycling, autoscaling, and deploy cadence. If workers are plain sync, one worker has one request
in flight and per-worker stampedes shrink to n=1 per worker (8 concurrent duplicate queries
worst case across the fleet); if gthread or async, in-worker concurrency exists and a dict
read/write needs a thread-safety look. Unknown — a fact to pin down before build.

**Scope of the PM's staleness sign-off (Advocate Q3, Judge Q3).** The design records only "a
stale product for up to 10 minutes is acceptable per the PM." Whether that covers legal
takedowns, price corrections, or internally inconsistent views (list vs. detail disagreeing,
mixed import generations during a rolling bulk import) was not discussed with the PM. The bulk
import's transactional shape from the readers' side is also unknown. These are gaps, not
accepted risks.

## Phase 3 — Adversary's Case

### Objection 1 — The cache key omits the region, and responses are region-priced (correctness)

**Problem.** The cache key is `product_id`, but the design itself says responses are
"personalized with per-region pricing." If the serialized product carries a price, the first
region to populate a key poisons it for every other region on that worker: a region-2 user gets
region-1 prices for up to 10 minutes. That is not staleness — it is serving the wrong price, the
one failure class the PM's sign-off cannot cover.

**Evidence.** The Defender's own Phase 2 answer: "the key as designed is wrong — worker A could
serve region-1 prices to a region-2 user, which is a correctness bug, not staleness... nothing in
the doc enforces it. I classify this as a gap the debate should treat as unresolved." The design
intends the region-neutral reading (a), but intent unstated is intent unenforced; the next
engineer who serializes the response body instead of the product row ships the bug.

**Better way.** Write the invariant into the design as a hard rule: the cache stores the
region-neutral product row; pricing is applied after the cache read, in the response layer. Add
one test that requests the same product from two regions and asserts different prices, so the
invariant survives refactors. If pricing turns out to be baked into serialization, key by
`(region, product_id)` and redo the memory math (25MB × region count × 8 workers) before
approving.

### Objection 2 — The single `all_products` key assumes a list endpoint that may not exist (efficacy and correctness)

**Problem.** The design caches `/products` under one key. That only works if the endpoint returns
one canonical response. If it accepts pagination, filtering, or sorting — the norm for a
12k-product catalog — then either the key misses most real traffic (hit rate near zero, no
latency win on the endpoint that motivated the project) or, worse, one parameterized response
gets cached and served for different parameters.

**Evidence.** The Defender's answer: "pagination, filtering, and sorting are not addressed... No
request-rate numbers or endpoint traffic split were gathered." The design's central latency claim
rests on an endpoint whose request shape nobody has looked at. Also unstated: whether the key
holds the raw product list or a fully serialized HTTP body — with per-region pricing, a cached
serialized body is Objection 1 again at list scale.

**Better way.** Before build, enumerate the endpoint's actual parameter space from route code and
a day of access logs. If parameterized, cache the canonical full dataset (raw rows, one key) and
apply filter/sort/pagination per request from memory — an in-memory scan of 12k items is
microseconds and keeps one key, one TTL. Reject caching per-query-string keys; the key space is
unbounded.

### Objection 3 — "No invalidation" rests on a sign-off nobody verified, and rolling imports break it anyway (risk)

**Problem.** Two distinct failures hide under "10 minutes of staleness is fine." First, scope: a
legal takedown or a bad-price correction that must propagate now cannot, because the design ships
no flush mechanism at all — the only lever is restarting workers. Second, consistency: during a
rolling bulk import, lazy per-id population captures a mix of pre- and post-import rows, so the
list page and detail pages can disagree, and prices from two import generations sit side by side
for up to 10 minutes.

**Evidence.** The Defender's answer: "Whether that covers legal takedowns, price corrections, or
internally inconsistent views... was not discussed with the PM. These are gaps, not accepted
risks." Bulk imports happen — they are the stated cause of today's latency spikes — so the mixed-
generation window occurs on every import, not in a rare corner.

**Better way.** Two cheap additions, not a pub/sub system. (1) Add a `catalog_version` value in
Postgres that the import pipeline and any takedown path bump; each worker checks it at most once
per second and drops its whole cache on change. One indexed single-row read per worker per second
is negligible, and it converts both takedown latency and mixed-generation windows from 10 minutes
to about 1 second. (2) Take the PM a concrete scenario list — takedown, price error, mid-import
inconsistency — and get sign-off on those, not on the abstract phrase "stale product."

### Objection 4 — TTL lapse recreates the exact spike the cache exists to prevent (risk)

**Problem.** Every 10 minutes, each worker's `all_products` entry expires and the expensive list
query runs again. After a deploy, all 8 workers start cold together, so their TTLs stay roughly
phase-aligned: 8 expensive list queries hit Postgres in the same window, every 10 minutes —
and if the worker model is threaded or async, each worker multiplies that by its in-flight
request count. The worst timing is during a bulk import, when Postgres is already loaded: the
design's failure mode fires precisely when the design's motivating problem is happening. Separately,
if workers are threaded/async, concurrent dict mutation needs a thread-safety decision the design
never makes.

**Evidence.** The Defender flags the stampede as a known soft spot but offers no mitigation, and
answers that the worker model is "unknown — a fact to pin down before build." A design whose
blast radius ranges from "8 duplicate queries" to "8 × concurrency duplicate queries" depending
on an unread config line is not done.

**Better way.** Serve-stale-while-revalidate: keep a soft TTL; on expiry, one request per worker
(guarded by a per-key lock or flag) refreshes while others serve the stale entry. Add ±20%
jitter to TTLs so workers desynchronize after deploys. Both fit in roughly 20 lines and remove
the periodic spike entirely. Read the gunicorn config before implementation and state the
concurrency model in the design.

### Objection 5 — No metrics, so "will it bite us" stays unanswerable after launch (maintainability)

**Problem.** The rollout plan is a flag and a week in staging, with no success criterion and no
observability. Without hit/miss counters and per-endpoint latency, nobody can tell whether the
cache achieved the latency goal, what the real hit rate is (which Objection 2 puts in doubt), or
whether a production incident is cache-related. The kill switch is an env var, so even using it
requires a restart plus a hunch.

**Evidence.** The design's Rollout section is two lines; no metric, threshold, or dashboard is
named anywhere in the doc, and the Defender's answers confirm no baseline traffic data exists.

**Better way.** Define the success criterion now (for example: p95 on both endpoints under 30ms
at current traffic, hit rate above 90%). Emit three counters — hit, miss, refresh — and tag
existing latency metrics with cache on/off. Gate the production default-on decision on the
staging numbers meeting the criterion, not on a week elapsing.

## Phase 4 — Advocate's Case

### Part 1 — Steelman: why this design is the right one

1. **The workload is the textbook case for TTL-only caching.** The catalog changes ~50 times a
   day, one write every ~29 minutes on average, against a read-dominated endpoint. With a
   10-minute TTL, most entries expire without the underlying row ever having changed. TTL caching
   is weak when writes are frequent relative to the TTL; here they are not. The design matches
   the mechanism to the data's actual change rate instead of building for a write rate it
   doesn't have.

2. **The failure mode is the status quo.** The miss path is today's direct Postgres read, and the
   `CATALOG_CACHE` flag reverts the whole feature. Every degraded state of this design, cold
   worker, expired entry, flag off, is exactly the system we run now. That is the risk profile of
   a purely additive change, and it is rare in caching designs, which usually add new ways to be
   wrong. This design adds one: staleness, explicitly bounded and explicitly priced.

3. **Rejecting Redis is correct at this scale, not merely convenient.** The dataset is ~25MB. A
   Redis tier for 25MB buys a service to provision, monitor, secure, and fail over, plus roughly
   a millisecond of RTT and a deserialize on every read, in a project whose stated goal is
   latency. Per-worker duplication costs ~200MB of RAM and zero operations. The design also gains
   fault isolation for free: there is no shared cache tier whose outage or poisoning becomes a
   fleet-wide event. A bad worker cache dies with its worker.

4. **"No invalidation" is a purchased simplification, not an oversight.** The design converts the
   hardest problem in caching into a product decision: the PM accepted 10 minutes of staleness,
   so no pub/sub, no write-path hooks, no coupling to the catalog team's import pipeline. That
   trade is the design's core insight. The legitimate criticism, which I take up under
   Objection 3, is the scope of the sign-off, not the mechanism chosen.

5. **The bulk-import spike fix falls out for free.** Imports cause today's read-latency spikes
   because reads and import writes contend. With the cache absorbing reads, Postgres sees at most
   a handful of list queries per TTL window during an import instead of the full read rate. The
   design's secondary goal is met by the same mechanism as the primary one, with no
   import-specific code.

The design is ~50 lines of code, no new infrastructure, one new failure class with a negotiated
bound, and instant reversion. Every alternative on the table adds a moving part. That is the case
for keeping it.

### Part 2 — Answers to the Adversary's objections

**Objection 1 (region poisoning): I concede the gap and accept the fix; I dispute that it
indicts the design.** The Defender already classified the missing region invariant as unresolved,
and the Adversary is right that unstated intent is unenforced intent. What convinced me is the
concrete failure path: the next engineer serializes the response body instead of the product row
and ships wrong prices. But note what the fix is: one sentence in the design ("the cache stores
the region-neutral product row; pricing applies after the read") and one two-region test. That is
a documentation defect in an otherwise sound design, not an architectural error. Accept the
better way's first half as written. The `(region, product_id)` fallback should stay contingent on
the pricing-location fact, which is a one-hour code read.

**Objection 2 (the `all_products` key): I dispute the evidence, and half of the better way.** The
Adversary's problem statement rests on "pagination, filtering, or sorting — the norm for a
12k-product catalog." That is speculation standing on the same absence of data as the design's
assumption of a canonical response; the ignorance is symmetric, and symmetric ignorance does not
sustain an objection, it sustains a fact-check. Accept the fact-check: enumerate the endpoint's
parameter space from route code and a day of access logs before build. Reject the pre-emptive
redesign. The proposed "cache raw rows, apply filter/sort/pagination per request" quietly gives
up the design's main win on the hot path: it re-serializes the response on every request, and
JSON-encoding a large slice of 12k products per request is not "microseconds." If the endpoint
turns out canonical, the original single cached body is strictly better. If it turns out
parameterized, adopt the Adversary's scheme then, with the serialization cost measured. Sequence:
verify first, redesign only on evidence.

**Objection 3 (invalidation and the sign-off): I concede the sign-off verification; I dispute
the `catalog_version` mechanism as unconditional, and I dispute the severity of the
mixed-generation claim.** What convinced me on the first part: the Defender's own admission that
takedowns, price corrections, and internal inconsistency "were not discussed with the PM." A
sign-off on the abstract phrase "stale product" does not cover a legal takedown, and the design's
biggest simplification deserves a sign-off that names the ugly cases. Take the PM the scenario
list; that costs a meeting. But `catalog_version` should be the conditional outcome of that
meeting, not a default. It quietly reinstalls the coupling the design paid to avoid: every write
path, including future ones, must remember to bump the version, and a forgotten bump fails
silent, degrading back to the TTL while everyone believes a flush mechanism exists. A false
safety net is worse than a documented 10-minute bound plus the existing lever (flip the flag,
restart workers) for the rare emergency. Adopt versioning only if the PM says sub-10-minute
propagation is a requirement. On mixed generations: a rolling import exposes readers to mixed
pre- and post-import state today, with no cache, for the duration of the import. The cache
extends that window by up to the TTL; it does not create the phenomenon. That is a difference of
degree, priced by the same staleness budget, and it belongs on the PM's scenario list rather
than in the design as a defect.

**Objection 4 (TTL-lapse stampede): I dispute the evidence on magnitude; I accept the cheap
hardening.** The claim that TTL expiry "recreates the exact spike the cache exists to prevent"
inverts the arithmetic. Today, Postgres runs the expensive list query at the full request rate,
continuously, including during imports. Under the design, worst case is 8 workers, times
in-flight concurrency if workers are threaded, running that query once per 10-minute window. Even
the pessimistic version is a small fraction of the load Postgres demonstrably survives right now
at 180ms p95. The failure mode is a large strict reduction from the baseline the design replaces.
The thread-safety alarm is also overdrawn for CPython: assigning a fully built value to a dict
key is atomic under the GIL, so the worst concurrent outcome is duplicate work, not corruption.
That said, the Adversary's mitigations are correctly sized at ~20 lines: TTL jitter and a
per-worker refresh flag remove even the residual cluster, and reading the gunicorn config before
build is due diligence, not a design change. Accept both as implementation notes. The objection
earns a paragraph in the design; it does not earn "not done."

**Objection 5 (no metrics): I concede the substance; I dispute one clause.** Hit, miss, and
refresh counters plus a numeric success criterion (the proposed p95 and hit-rate thresholds are
reasonable defaults) cost little and convert the staging week from "time elapsed" into "criterion
met." They also settle Objection 2's hit-rate question with production data. The design loses
nothing by adopting this, and its absence from a short design doc reflects the doc's altitude
more than a plan to fly blind; still, write it down. The clause I dispute: the env-flag kill
switch is not a defect. A restart-gated flag is an adequate lever for a cache whose worst failure
is bounded staleness, and worker restarts are a routine operation. Gating production default-on
upon the staging numbers: accept.

### Summary of positions

- Conceded: region invariant must be written and tested (O1); PM sign-off must be re-scoped
  against concrete scenarios (O3, part); counters and a success criterion added to rollout (O5).
- Disputed: parameterization of `/products` as asserted fact and the scan-per-request redesign
  (O2); `catalog_version` as an unconditional addition, and mixed-generation severity (O3, part);
  the stampede's claimed magnitude and the thread-safety framing (O4); the kill-switch complaint
  (O5, part).
- Every concession is a bounded edit to the document or the rollout plan. None changes the
  architecture: in-process dict, lazy fill, TTL, flag. The plan as shaped remains the best one
  on the table.

## Phase 5 — Adversary's Rebuttal

**Objection 1 (region poisoning) — dropped, resolved by concession.** The Advocate accepted the
whole remedy: the region-neutral invariant written into the design, the two-region test, and the
`(region, product_id)` fallback held contingent on the one-hour pricing-location code read. That
is everything the objection asked for. The residual dispute — "documentation defect" versus
"architectural error" — is a label and changes no line of the plan, so I do not argue it.

**Objection 2 (the `all_products` key) — dropped.** Two things convinced me. First, the
sequencing argument is right: my "pagination is the norm" claim stood on the same missing data as
the design's canonical-response assumption, and the Advocate accepted the part that carries the
outcome — enumerate the parameter space from route code and access logs before build. Second, the
Advocate's own text already commits to adopting my scan-per-request scheme, with serialization
cost measured, if the endpoint turns out parameterized. Both branches of the contingency are now
agreed; nothing remains for the Judge. I note only that the enumeration must gate the build, not
run alongside it — which the Advocate's "verify first, redesign only on evidence" already grants.

**Objection 3 (invalidation and the sign-off) — sustained, narrowed.** The PM scenario meeting is
conceded; I keep the objection because two substantive points survive the Advocate's defense.

First, the Advocate's case against a flush mechanism leans entirely on an emergency lever —
"flip the flag, restart workers" — that appears nowhere in the design. The doc describes
`CATALOG_CACHE` only as a rollout switch. An undocumented emergency path is the same defect the
Advocate conceded in Objection 1: unstated intent is unenforced. And it makes the conceded PM
meeting unanswerable — the PM cannot accept "10-minute staleness plus an emergency path" without
knowing the path's propagation time. Concrete fix: write into the design "emergency flush =
disable `CATALOG_CACHE` + rolling restart, measured propagation ≤ X minutes, runbook entry," then
take X to the meeting alongside the takedown and price-correction scenarios.

Second, the "false safety net" argument against `catalog_version` inverts its own arithmetic. A
forgotten version bump degrades to exactly the TTL bound — the design's own accepted worst case.
A net whose failure mode equals the no-net baseline is not worse than the baseline; it is worse
only if its existence tempts someone to widen the TTL or skip the PM conversation. So the correct
statement is "a net that fails back to the documented bound," not "a false net worse than the
bound." That said, I accept the conditionality: adopt `catalog_version` only if the PM meeting
yields a sub-10-minute propagation requirement. The mechanism dispute collapses into the
meeting's outcome; the undocumented-lever gap does not, and that is what I sustain.

On mixed generations, I accept the difference-of-degree framing with one correction that must
reach the PM: today the inconsistency window closes when the import commits; under the cache it
persists up to a full TTL after the import completes. Put that number — "inconsistent views for
up to 10 minutes past import completion, on every import" — on the scenario list, not the
abstract phrase "stale product."

**Objection 4 (TTL-lapse stampede) — dropped.** The magnitude arithmetic convinced me: today
Postgres runs the list query at the full request rate continuously, so 8-to-8×concurrency
duplicate queries once per 10-minute window is a strict reduction from a load the database
demonstrably survives at 180ms p95. "Recreates the exact spike" was wrong; the correct claim was
"a small residual cluster," and the Advocate accepted the ~20-line hardening (TTL jitter,
per-worker refresh flag) plus the gunicorn-config read that removes even that. The GIL point on
dict assignment is also correct — duplicate work, not corruption. With the mitigations adopted as
implementation notes, no outcome remains in dispute.

**Objection 5 (no metrics) — dropped, resolved by concession.** The Advocate accepted the
counters, the numeric success criterion, and gating production default-on upon the staging
numbers. On the disputed clause, the Advocate's point stands: for a cache whose worst failure is
bounded staleness, a restart-gated flag is a proportionate kill switch, and worker restarts are
routine. The one live question about that flag — its speed as an emergency takedown lever — now
lives inside sustained Objection 3, where it belongs.

**Net position.** One objection sustained, narrowed to two edits: document and measure the
emergency-flush path before the PM meeting, and reframe `catalog_version` as the conditional
outcome of that meeting rather than rejecting it as a false net. Everything else is agreed:
region invariant plus test, parameter-space enumeration as a build gate, PM scenario list with
the post-import inconsistency window stated, stampede hardening as implementation notes, and a
criterion-gated rollout with hit/miss/refresh counters.

## Phase 6 — Advocate's Surrebuttal

Only Objection 3 survives, narrowed to two points and a phrasing correction. I answer all three
explicitly; nothing is left implied for the Judge.

**Point 1 — the undocumented emergency lever: conceded.** What convinced me is my own standard.
In Objection 1 I accepted that "unstated intent is unenforced intent" and called one missing
sentence a defect worth fixing; the emergency path I leaned on in Phase 4 — "flip the flag,
restart workers" — is the identical defect, and I cannot apply the principle to the region
invariant and exempt my own argument from it. The Adversary's second proof is independently
decisive: the PM meeting I already conceded cannot produce an informed sign-off on "10-minute
staleness plus an emergency path" when the path's propagation time is unmeasured — the meeting's
key input would be a blank. Accept the fix as specified: write "emergency flush = disable
`CATALOG_CACHE` + rolling restart, measured propagation ≤ X minutes, runbook entry" into the
design, measure X in staging (a rolling restart of 8 gunicorn workers is a routine, timeable
operation — this costs an afternoon, not a redesign), and take X to the PM meeting. Note what
this concession is: a documentation-and-measurement edit. The architecture — in-process dict,
lazy fill, TTL, flag — is untouched, consistent with my Phase 4 summary.

**Point 2 — the "false safety net" arithmetic: I concede the correction; my conditionality
stands, and the Adversary adopted it.** The Adversary's arithmetic is right and mine was wrong:
a forgotten `catalog_version` bump degrades to exactly the TTL bound, the design's own accepted
worst case, so the honest label is "a net that fails back to the documented bound," not "worse
than no net." What convinced me is the direct comparison of failure modes — I had no scenario in
which the forgotten bump produces an outcome the no-net design doesn't already accept. The
residue of my argument — that a believed-in flush mechanism tempts someone to widen the TTL or
soften the PM conversation — the Adversary granted verbatim, and it is exactly why the mechanism
must stay conditional rather than default. On that conditionality the Adversary moved to my
position: adopt `catalog_version` only if the PM meeting yields a sub-10-minute propagation
requirement. So the mechanism dispute is closed by agreement on my terms, and the label dispute
is closed by concession on the Adversary's terms. Nothing here remains for the Judge.

**Point 3 — the mixed-generation window number: accepted as an amendment to my own concession.**
The correction is factually right: today the inconsistency window closes when the import commits;
under the cache it persists up to one full TTL after commit, on every import. My Phase 4
"difference of degree" framing stands, but a degree needs a number, and "inconsistent views for
up to 10 minutes past import completion, on every import" is the number the PM must see. This
folds into the scenario list I already conceded in Phase 4; it changes the list's wording, not
its existence.

**Final position.** Every line of the plan is now agreed between Advocate and Adversary:

- Region-neutral invariant in the design plus the two-region test; `(region, product_id)`
  fallback contingent on the pricing-location code read (O1).
- Parameter-space enumeration from route code and access logs as a build gate; scan-per-request
  adopted only if the endpoint proves parameterized, with serialization cost measured (O2).
- Emergency-flush path documented and its propagation measured; PM scenario meeting covering
  takedowns, price corrections, and the quantified post-import inconsistency window;
  `catalog_version` conditional on a sub-10-minute requirement emerging from that meeting (O3).
- TTL jitter, per-worker refresh flag, and the gunicorn-config read as implementation notes (O4).
- Hit/miss/refresh counters, numeric success criterion, criterion-gated production default-on
  (O5).

None of these changes the architecture: in-process dict, lazy fill, TTL, env flag. The design
survives the red team as shaped, amended by bounded edits to its document and rollout plan. No
objection remains in dispute, so the Judge may proceed directly to the final report; phases 7–8
have nothing left to arbitrate.

## Phase 7 — Judge's Interim: Assessment and Compromises

<!-- Skip phases 7-8 if every objection was dropped or conceded in phases 5-6. -->
<!-- Judge: per objection — strengths/weaknesses of each side; resolved or compromise proposed. -->

## Phase 8 — Reactions to Compromises

### Advocate's reactions

<!-- Advocate: accept/reject each, one reason. Transcribed verbatim by the Defender. -->

### Adversary's reactions

<!-- Adversary: accept/reject each, one reason. Transcribed verbatim by the Defender. -->

### Defender's weigh-in

<!-- Defender: feasibility and appetite per compromise. -->

## Phase 9 — Judge's Final Report

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
