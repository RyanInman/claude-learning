Plan shape is right. Calendar is the danger. Devil's advocate pass:

## 1. Table deletion one sprint after launch — biggest risk

- Deletion kills the rollback path. Billing bugs surface on cycle boundaries (monthly invoicing, proration, dunning), so many cannot appear until week 3-4. By then the old tables are gone.
- One sprint does not cover one full billing cycle. Delete before finance closes a full month on the new service and you delete the data you need to debug discrepancies.
- Billing records usually carry retention obligations (tax, audit — often 7+ years). Confirm with finance/legal before dropping anything.
- Cheaper alternative: revoke writes, rename tables, snapshot, archive. Delete months later, after N clean closes. Same decommission effect, reversible.

## 2. Backfill same week as flag flip — writing into a moving target

- New invoices land while the script runs. Where is the cutover boundary? Seam risks: double-billed or missing invoices at the transition point.
- "One-off script" is a red flag. It must be idempotent and resumable, because a script that dies at row 3M and cannot safely rerun becomes an incident.
- Define proof of correctness before running it: row counts, per-customer amount totals, line-item checksums old vs new. "Script exited 0" is not verification.

## 3. Feature flag questions the plan skips

- Global or per-tenant? Per-tenant rollout means two billing systems live at once. Which is source of truth? Watch invoice-number collisions — some jurisdictions require gapless sequential numbering.
- What does flag-off mean after the backfill ran and the tables are deleted? If the off path reads old tables, the flag becomes a crash switch, not a rollback switch, the moment deletion lands.
- A flag proves nothing about correctness. Run shadow mode first: old system authoritative, new system computes in parallel, diff every invoice. Flip only after N days of zero diffs.

## 4. Missing from the plan entirely

- In-flight state: mid-cycle subscriptions, pending payments, retry/dunning state, partial refunds. Stateful cutover needs an explicit strategy, not just "new reads new."
- Downstream readers of the old tables: finance exports, BI dashboards, other services doing direct reads. Inventory them via DB query logs before deletion, or reporting breaks silently.
- Zero slack: three dependent risky steps in ~3 sprints. If the backfill slips, does deletion still ride the calendar? Gate each step on verification, not on sprint boundaries.

## Suggested reshape

1. Sprint 1: ship dark. Shadow mode plus invoice diffing against the old system.
2. Sprint 2: backfill (idempotent, checkpointed) plus reconciliation report. Flip flag per-tenant once diffs are clean.
3. Sprint 3+: full rollout. Old tables go read-only, renamed, archived.
4. Delete only after one full billing cycle, one finance month-end close on the new service, and legal sign-off on retention.

Deletion is the only irreversible step in your plan. Push it back until at least one clean monthly close; everything else can keep its dates.
