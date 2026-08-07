# Adversarial Review Transcript

**Artifact:** /Users/admin/claude-learning/skills/adversarial-review-workspace/iteration-1/eval-3-inline-proposal-attack/with_skill/work/billing-migration-plan.md
**Date:** 2026-08-07

Append-only. Each phase's content lands under its own heading, transcribed verbatim by the
Defender. No role's text is ever edited after it is written.

---

## Phase 1 — Defender: Opening Statement

The artifact is a three-step migration plan for replacing a billing system. The author is the
user; I defend it from the plan text and the conversation, which contains no additional context
— no team size, traffic volume, invoice count, or compliance regime. Gaps I cannot fill from the
text become verification items, not invented facts.

The plan's goal: replace the old billing system with a new billing service in roughly two
sprints, with a rollback lever during the transition.

Why each decision is reasonable:

1. **Feature flag for the new service.** The flag gives an instant kill switch. If the new
   service miscomputes charges, the team flips the flag and old billing keeps running. This is
   the industry-standard way to de-risk a service cutover, and it costs little to build.

2. **One-off backfill script in the same week.** Backfilling immediately after shipping keeps
   the two systems' data close in time, shrinking the window in which the new service serves
   from an empty or stale invoice store. A one-off script matches the one-off nature of the
   work: this migration happens once, so an idempotent pipeline is arguably over-engineering.

3. **Delete old tables one sprint later.** Deleting quickly avoids the well-known failure mode
   where "temporary" legacy tables live for years, accrue accidental readers, and double
   storage and mental overhead. One sprint of overlap gives a validation window before the
   point of no return.

Decisions I am least sure of:

- **The deletion timeline.** One sprint of parallel running may be too short to observe a full
  billing cycle (monthly invoicing would need 4+ weeks), and deletion is the only irreversible
  step in the plan.
- **What "behind a feature flag" means for writes.** The plan does not say whether the flag
  gates reads, writes, or both, or whether the old system keeps writing while the flag ramps.
  If both systems write during the transition, the backfill's consistency story is undefined.
- **Verification.** The plan has no explicit step that proves the new service and backfilled
  data are correct before deletion.

Constraints invisible in the artifact: none are stated in the conversation. Deadlines, team
size, invoice volume, audit or tax-retention requirements, and downstream consumers of the old
tables are all unknown.

## Phase 2 — Adversary's Questions

1. What is the billing cycle length and the sprint length? I need this to judge whether one sprint of parallel running covers at least one full cycle of invoice generation before the old tables are deleted.

2. During the flagged period, which system writes new invoices and payment events — old, new, or both? And does the backfill script run while those writes continue, or during a write freeze?

3. Before deletion in Sprint N+1, what consumes the old billing tables today (reports, finance exports, other services), and is any backup, snapshot, or retention obligation (tax, audit) known to apply to that data?

## Phase 3 — Defender's Answers

**Q1 — billing cycle length and sprint length.** Unknown. The plan and the conversation state
neither. Most teams run 1- or 2-week sprints and monthly billing cycles; if that holds here, one
sprint of parallel running does not cover a full cycle. But that is inference, not fact.

**Q2 — which system writes during the flagged period, and does backfill run against live
writes.** Unknown. The plan says only "behind a feature flag" and "backfill invoices with a
one-off script the same week." It does not specify whether the flag gates writes, whether old
billing keeps writing while flagged users move to the new service, or whether the backfill runs
during a write freeze. No dual-write or cutover mechanism is described.

**Q3 — consumers of the old tables and retention obligations.** Unknown. No downstream
consumers (reports, finance exports, other services) are named, and no backup, snapshot, or
tax/audit retention requirement is stated. Billing data commonly carries multi-year retention
obligations (for example, 6-7 years for tax records in many jurisdictions), but whether any
apply here is not established in the conversation.

## Phase 4 — Adversary's Objections

### Objection 1 — The only irreversible step is gated by the calendar, not by evidence

**Problem.** Step 3 deletes the old billing tables in Sprint N+1 because a sprint has passed, not because anything has been proven. Deletion is the plan's single point of no return, and the plan schedules it before the new service can have produced even one full billing cycle under real load. If sprints are 1-2 weeks and billing is monthly — the common case, per the Defender's own Phase 3 answer — the new service is deleted-into before it has ever generated a month-end invoice run. Any defect found after deletion (proration bugs, tax rounding, dunning logic) has no old-system data to reconcile against.

**Evidence.** The plan text contains no exit criteria for deletion — only "the sprint after." The Defender confirmed in Phase 1 that deletion is "the only irreversible step" and in Phase 3 that cycle length is unknown. A plan that makes its sole irreversible action unconditional on any observation is defective regardless of what the unknown values turn out to be.

**Better way.** Replace the date gate with a criteria gate: delete only after (a) the new service has completed at least one full billing cycle at 100% flag rollout, and (b) a reconciliation run over that cycle shows zero unexplained diffs. Keep "Sprint N+1" as the earliest review date, not the deletion date.

### Objection 2 — Write ownership during the flag period is undefined, so the backfill cannot be correct by construction

**Problem.** The plan backfills "the same week" the flagged service ships, but never says which system writes new invoices while the flag ramps. Every possible answer breaks the stated plan: if the old system keeps writing, the backfill is stale the moment it finishes and Sprint N+1 deletes rows that were never copied; if both write, the same charge can exist twice; if only the new system writes, un-flagged users generate no invoices at all. This is not a missing detail — it is the mechanism the whole migration depends on, and each unstated resolution produces either double-billing or lost invoices, i.e., wrong charges to customers.

**Evidence.** Defender's Phase 3 answer to Q2: "Unknown... No dual-write or cutover mechanism is described." The plan's own sequencing (backfill during week 1, delete in Sprint N+1) guarantees a divergence window unless writes are frozen or dual-written, and the plan specifies neither.

**Better way.** Add an explicit cutover mechanism to the plan: old system remains the sole writer during the ramp; new service reads through to old data or dual-writes are mirrored old→new; run the backfill with a checkpointed cursor; then run a catch-up sync plus reconciliation immediately before flipping write ownership. One paragraph in the plan closes this.

### Objection 3 — No verification step exists anywhere between "ship" and "delete"

**Problem.** The feature flag is sold as the safety lever, but the plan defines nothing that would ever trip it. No comparison of old-vs-new invoice output, no ramp stages, no acceptance criteria — so the team learns the new service miscomputes charges from customer complaints or a finance close mismatch, which for billing means refunds, credit memos, and possibly regulator contact. A kill switch nobody knows to pull is not a rollback strategy.

**Evidence.** Defender's Phase 1 statement: "The plan has no explicit step that proves the new service and backfilled data are correct before deletion." The flag's claimed value in the opening statement ("flips the flag and old billing keeps running") presupposes a detection mechanism the plan does not contain.

**Better way.** Insert a shadow-comparison stage: run the new service in parallel on real events with the flag off, diff its computed invoices against the old system's per account, and set ramp gates (e.g., 1% → 25% → 100%) that each require a clean diff over a defined window. This also supplies the reconciliation evidence Objection 1 needs.

### Objection 4 — Deletion ignores unknown consumers and retention obligations; "delete" should be "archive and revoke"

**Problem.** Dropping the old tables in Sprint N+1 assumes nothing else reads them and no law requires keeping them. Neither assumption is checked. Finance exports, reports, or another service reading those tables breaks at DROP time, and billing records commonly carry 6-7 year tax retention — deleting them can convert a clean migration into a compliance incident that no code rollback fixes.

**Evidence.** Defender's Phase 3 answer to Q3: consumers and retention requirements are both unstated, and the Defender volunteered the multi-year retention norm. The plan spends a step on deletion but zero words on who reads the data or whether it may be destroyed.

**Better way.** Split step 3 into: (a) inventory readers via query logs and grants, migrate or cut them over; (b) snapshot the tables to cold storage with a retention label; (c) revoke access / rename the tables for one cycle to smoke out unknown readers; (d) drop only after the quiet period and a retention sign-off. This preserves the plan's anti-zombie-table intent — the tables leave the hot path on schedule — without the irreversibility.

### Objection 5 — "One-off script" is the wrong spec for a backfill that runs against a live system on a deadline

**Problem.** A backfill executed "the same week" as a new-service launch will run while the system is changing and will plausibly fail partway (timeout, bad row, deploy). A one-off script with no idempotency or resume point leaves the invoice store in a half-copied state that is worse than either endpoint, and the same-week deadline pressures the team to patch-and-rerun by hand.

**Evidence.** The plan's own words: "one-off script the same week." The Defender's Phase 1 justification — idempotent design is "arguably over-engineering" for one-time work — inverts the real cost: idempotency here is a checkpoint table and insert-if-absent semantics, roughly a day of work, while a non-resumable failure mid-backfill costs far more than that in cleanup and delayed cutover.

**Better way.** Spec the script as idempotent and resumable (keyed upserts, checkpointed cursor, per-batch row-count and sum verification), and decouple it from the ship week: run it as many times as needed, with the final catch-up pass tied to the cutover event from Objection 2 rather than to the calendar.

## Phase 5 — Defender's Defense

First the steelman duty: the plan's core virtues are real. Feature-flag cutover is the right
architecture — it beats a big-bang switch on every axis. The two-sprint timeline forces
momentum; migrations that lack a deletion date become permanent dual systems, and the plan's
author clearly knows that failure mode. A second-order virtue the plan does not state: deleting
the old tables ends the era in which "check the old table" is an acceptable debugging answer,
which forces the team to make the new service fully observable. The objections below do not
attack these virtues; they attack the connective tissue between the three steps. Now each
objection.

**Objection 1 — conceded.** The proof that convinced me: the objection is sound under every
resolution of the unknowns. If the cycle is monthly and sprints are short, deletion precedes
the first real invoice run; if the cycle is shorter, the criteria gate costs nothing extra
because it is satisfied on the same calendar. A gate that is strictly safer in one case and
free in the other has no honest counterargument. Deletion should require one clean billing
cycle at 100% rollout plus a clean reconciliation, with Sprint N+1 as the earliest review
date.

**Objection 2 — conceded.** The proof: the case enumeration. Old-writes-only makes the
backfill stale before deletion; dual-writes risks duplicate charges; new-writes-only orphans
un-flagged users. I cannot produce a fourth case that keeps the plan safe as written, and a
plan whose safety depends on an unstated mechanism is unspecified, not merely terse. The plan
must name the writer during the ramp and the catch-up-then-flip sequence.

**Objection 3 — conceded.** The proof: my own opening statement conceded the fact ("no
explicit step that proves... correct before deletion"), and the objection converts that fact
into the failure scenario — a kill switch with no tripwire is pulled only after customer-visible
damage. The flag's value, which I claimed in Phase 1, is only realized if a shadow diff or
staged ramp with acceptance criteria exists to trip it. The better way also feeds Objection 1's
reconciliation gate, so one mechanism satisfies both.

**Objection 4 — conceded.** The proof: asymmetry of cost. The rename-and-snapshot path costs
hours and delays true deletion by one cycle; a DROP against unknown readers or an unmet
retention obligation is unrecoverable. With both unknowns still open (Phase 3, Q3), choosing
the irreversible branch is indefensible. The archive-revoke-drop sequence preserves the plan's
anti-zombie intent, which is the thing worth defending.

**Objection 5 — contested in part, conceded in part.** I contest the evidence for the
mandatory-idempotency claim: "will plausibly fail partway" assumes a backfill large or long
enough to be interrupted, and the record establishes no volume. For a small invoice table the
honest resume strategy is TRUNCATE-and-rerun inside a transaction, and the checkpoint table is
pure ceremony — the objection's own cost figure ("roughly a day of work") is a day spent only
if the data size demands it. I concede the sequencing half, and the proof is Objection 2's
enumeration, which I already accepted: the final catch-up pass must be tied to the write-
ownership flip, not to the calendar week, or the backfill is stale by construction. So: verify
the invoice volume first; spec checkpointed idempotency only if the backfill cannot complete
comfortably inside one transaction or maintenance window.

## Phase 6 — Adversary's Rebuttal

<!-- Adversary: sustain each objection with new substance or drop it, naming what convinced you. -->

## Phase 7 — Final Report

<!-- Defender: agreed changes / dropped objections / contested points / recommendation with declared interest / user's options. -->
