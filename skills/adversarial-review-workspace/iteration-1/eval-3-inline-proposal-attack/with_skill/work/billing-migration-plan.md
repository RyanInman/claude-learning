# Billing Migration Plan

Proposal as stated by the author:

> we ship the new billing service behind a feature flag next sprint, backfill invoices with a
> one-off script the same week, and delete the old billing tables the sprint after.

Broken into steps:

1. **Sprint N:** Ship the new billing service behind a feature flag.
2. **Sprint N, same week:** Backfill invoices into the new service with a one-off script.
3. **Sprint N+1:** Delete the old billing tables.
