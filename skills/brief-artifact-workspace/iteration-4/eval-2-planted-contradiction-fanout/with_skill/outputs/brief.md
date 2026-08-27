# Brief: evals/fixtures/ledger-design.md

## TL;DR
- The doc describes a ledger service that records account transfers: idempotency keys on requests, a month-partitioned transfers table, a 30 s risk-engine timeout with two retries, and a nightly bank-feed reconciliation job.
- Contradiction: "Timeouts and retries" sets the risk-engine timeout at 30 seconds (L37) while "Operations" tells on-call it is 90 seconds (L85). One of them misleads whoever reads it.
- Every claim is unverified: no numbers cite a source, and about 90% of the text is the same twelve boilerplate sentences repeated in shuffled order, which hides the six substantive lines.

## Structure map

| id | type | risk | size | anchor |
|---|---|---|---|---|
| chunk-01 | prose | low | 924 words | Ledger Service Design .. Ledger Service Design > Overview (L1-L18) |
| chunk-02 | prose | low | 921 words | Ledger Service Design > Request handling (L19-L34) |
| chunk-03 | prose | low | 930 words | Ledger Service Design > Timeouts and retries (L35-L50) |
| chunk-04 | prose | low | 900 words | Ledger Service Design > Storage (L51-L66) |
| chunk-05 | prose | low | 914 words | Ledger Service Design > Reconciliation (L67-L82) |
| chunk-06 | prose | low | 921 words | Ledger Service Design > Operations (L83-L97) |

## Chunk summaries

- **chunk-01** [low] Ledger Service Design .. Ledger Service Design > Overview (L1-L18): Overview section of the Ledger Service Design.
- **chunk-02** [low] Ledger Service Design > Request handling (L19-L34): The Request handling section states that each request carries an idempotency key so retried transfers do not post twice.
- **chunk-03** [low] Ledger Service Design > Timeouts and retries (L35-L50): The section states the risk-engine timeout (30 seconds) and retry policy (two retries with backoff), then fills five paragraphs with repeated boilerplate sentences about dashboards, low-priority backfills, structured logging, alerting, secret rotation, schema review, a 200 ms p95 read latency target, YAML config, health endpoints, unit test coverage, and a three-phase migration.
- **chunk-04** [low] Ledger Service Design > Storage (L51-L66): The Storage section states one concrete design fact: transfers live in a month-partitioned transfers table with a covering index on account_id.
- **chunk-05** [low] Ledger Service Design > Reconciliation (L67-L82): The Reconciliation section states one reconciliation mechanism: a nightly job compares ledger totals to the bank feed and opens a ticket on mismatch.
- **chunk-06** [low] Ledger Service Design > Operations (L83-L97): Operations section of the ledger service design.

## Claims

| status | claim | anchor |
|---|---|---|
| contradicted | Downstream calls to the risk engine time out after 30 seconds; the client retries twice with backoff. | L37 'time out after 30 seconds' vs L85 'timeout is 90 seconds' |
| contradicted | Risk engine timeout is 90 seconds; a slow engine stalls 90 seconds before retry starts. | L37 'time out after 30 seconds' vs L85 'timeout is 90 seconds' |
| unverified | The Ledger service records every transfer between accounts. | 5 |
| unverified | The migration ran in three phases over two weekends without downtime. | 7 |
| unverified | Read latency target is under 200 ms at the 95th percentile. | 7 |
| unverified | Unit tests cover the parser, the validator, and the posting logic. | 7 |
| unverified | Alerts route to the payments channel and page after five minutes. | 11 |
| unverified | Secrets rotate every ninety days through the platform vault. | 15 |
| unverified | Each request carries an idempotency key so a retried transfer does not post twice. | 21 |
| unverified | Read latency target is under 200 ms at the 95th percentile. | 23 |
| unverified | Alerts route to the payments channel and page after five minutes. | 23 |
| unverified | Secrets rotate every ninety days through the platform vault. | 25 |
| unverified | The migration ran in three phases over two weekends without downtime. | 23 |
| unverified | Configuration lives in a single YAML file loaded at startup. | 29 |
| unverified | Alerts route to the payments channel and page after five minutes. | 39 |
| unverified | Secrets rotate every ninety days through the platform vault. | 41 |
| unverified | Read latency target is under 200 ms at the 95th percentile. | 43 |
| unverified | The migration ran in three phases over two weekends without downtime. | 39 |
| unverified | Unit tests cover the parser, the validator, and the posting logic. | 39 |
| unverified | Transfers table is partitioned by month with a covering index on account_id. | 53 |
| unverified | Read latency target is under 200 ms at the 95th percentile. | 55 |
| unverified | Secrets rotate every ninety days through the platform vault. | 55 |
| unverified | Alerts route to the payments channel and page after five minutes. | 55 |
| unverified | The migration ran in three phases over two weekends without downtime. | 55 |
| unverified | Configuration lives in a single YAML file loaded at startup. | 57 |
| unverified | A nightly job compares ledger totals against the bank feed and opens a ticket on any mismatch. | 69 |
| unverified | Every write path emits a structured log line with the request id. | 71 |
| unverified | Latency targets stay under 200 ms at the 95th percentile for reads. | 73 |
| unverified | Alerts route to the payments channel and page after five minutes. | 73 |
| unverified | Secrets rotate every ninety days through the platform vault. | 73 |
| unverified | The migration ran in three phases over two weekends without downtime. | 71 |
| unverified | Migration ran in three phases over two weekends without downtime. | 87 |
| unverified | Alerts route to the payments channel and page after five minutes. | 87 |
| unverified | Latency target is under 200 ms at the 95th percentile for reads. | 89 |
| unverified | Secrets rotate every ninety days through the platform vault. | 87 |
| unverified | Unit tests cover the parser, the validator, and the posting logic. | 89 |

## Risks

- **uncited-number** [low] 7: 200 ms p95 read target stated with no measurement or source.
- **uncited-number** [low] 7: Three phases over two weekends without downtime; no migration record cited.
- **uncited-number** [low] 23: 200 ms p95 target and five-minute page delay stated with no measurement or source.
- **uncited-number** [low] 37: 30-second timeout and two retries stated without rationale or source.
- **uncited-number** [low] 43: 200 ms p95 target given with no measurement or data.
- **uncited-number** [low] 55: 200 ms p95 target, 90-day rotation, and five-minute paging stated without source or measurement.
- **uncited-number** [low] 73: 200 ms p95 read target stated with no measurement or source.
- **uncited-number** [low] 85: 90 second timeout stated without source; check against timeout values in other sections.
- **uncited-number** [low] 89: 200 ms p95 read target has no measurement or source.
- **unsupported-claim** [low] 7: Unit test coverage claimed with no test list or coverage data.
- **unsupported-claim** [low] 7: Section repeats the same sentences many times; reads as filler rather than design content.
- **unsupported-claim** [low] 23: Migration claimed complete without downtime; no dates, metrics, or reference given.
- **unsupported-claim** [low] 23: Sentences repeat verbatim across paragraphs; text reads as padding, not design content.
- **unsupported-claim** [low] 39: Migration claimed complete without downtime; no evidence. Paragraphs are repeated boilerplate, likely padding.
- **unsupported-claim** [low] 55: Migration claimed complete without downtime; no dates, metrics, or evidence given.
- **unsupported-claim** [low] 57: Section is mostly duplicated filler sentences unrelated to storage; likely padding, little reviewable content.
- **unsupported-claim** [low] 71: Zero-downtime three-phase migration asserted with no evidence or date.
- **unsupported-claim** [low] 71: Paragraphs 71-81 repeat the same sentences many times; filler, no reconciliation detail beyond line 69.
- **unsupported-claim** [low] 87: Zero-downtime three-phase migration asserted with no evidence.
- **unsupported-claim** [low] 87: Paragraphs repeat the same sentences many times; likely generated filler, content may be padding.

## Least confident

- chunk-03: Whether 30-second timeout with two retries conflicts with the 200 ms latency target or with timeouts stated elsewhere in the document, which this chunk cannot show.
- chunk-06: Whether the 90 second risk engine timeout at line 85 agrees with timeout values stated elsewhere in the document, which this chunk cannot show.

_6 chunks, 36 claims (0 verified, 34 unverified, 2 contradicted), 20 risks. Budget 1500 words, compaction level 3._
