# Ledger Service Design: summary

Source: evals/fixtures/ledger-design.md

## What the design says

- Purpose: Ledger records every transfer between accounts.
- Request handling: each request carries an idempotency key, so a retried transfer does not post twice.
- Timeouts and retries: calls to the risk engine time out after 30 seconds; the client retries twice with backoff.
- Storage: transfers land in the `transfers` table, partitioned by month, with a covering index on `account_id`.
- Reconciliation: a nightly job compares ledger totals against the bank feed and opens a ticket on any mismatch.
- Operations: on-call must know the risk engine timeout so a slow engine is recognizable as a stall before the retry starts.

Cross-cutting claims repeated throughout the doc (13 distinct statements, each restated dozens of times):

- Latency target: reads under 200 ms at p95.
- Config: one YAML file loaded at startup.
- Secrets rotate every 90 days via the platform vault.
- Every write path logs a structured line with the request id.
- Dashboards show throughput, error rate, and queue depth per region.
- Alerts route to the payments channel and page after five minutes.
- Health and readiness endpoints exist for the orchestrator.
- Unit tests cover parser, validator, and posting logic.
- Schema changes go through a review that checks index impact.
- Backfills run at low priority.
- Migration ran in three phases over two weekends with no downtime.
- Team reviewed the design in the spring planning cycle.

## What does not add up

1. Risk engine timeout contradiction (high priority). "Timeouts and retries" states 30 seconds. "Operations" tells on-call the timeout is 90 seconds and that a slow engine shows a 90 second stall before retry. One of these is wrong. On-call runbooks built from the Operations section would misdiagnose stalls if the real value is 30 s, or the retry budget math (30 s x 3 attempts = 90 s worst case vs 90 s x 3 = 270 s) is off by 3x. Confirm the config value and fix one section.
2. Possible source of the confusion: 30 s timeout with two retries totals roughly 90 s end to end. The Operations author may have conflated total retry budget with per-call timeout. Worth stating both numbers explicitly.
3. Retry budget vs latency target. Even at 30 s, a single risk-engine call exceeds the 200 ms p95 read target by two orders of magnitude. The doc never says whether risk-engine calls sit on the read path or only on writes. Clarify.
4. No timeout, retry, or alert details for the reconciliation job. "Opens a ticket on any mismatch" has no owner, SLA, or threshold, while alerts elsewhere have a five-minute page rule.
5. Idempotency key storage is unspecified. The Storage section describes only the transfers table and one index; nothing says where idempotency keys live or how long they are retained, which determines how long a retry stays safe.
6. Document quality: roughly 95% of the text is the same 13 sentences shuffled and repeated. This reads as generated padding, not design content. Each section carries exactly one real sentence.
