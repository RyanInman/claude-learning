# Brief: evals/fixtures/ledger-design.md

## TL;DR
- Design doc for a Ledger service that records account transfers: idempotency keys per request, month-partitioned transfers table with account_id covering index, nightly bank-feed reconciliation, and a risk-engine timeout with two retries.
- Contradiction: Timeouts section says the risk engine times out after 30 seconds (L37); Operations tells on-call the timeout is 90 seconds (L85). One of these misleads on-call.
- Every claim is unverified: no numbers, dates, or reviews cite a source, and the 200 ms p95 target sits next to a 30 to 90 second downstream timeout with no explanation.
- Most of the document is the same dozen operational sentences repeated; only one sentence per section carries design content.

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

### chunk-01 [low] Ledger Service Design .. Ledger Service Design > Overview (L1-L18)

Overview of the Ledger service, which records every transfer between accounts. The section is a repetitive list of operational assertions: a three-phase zero-downtime migration, structured logging with request ids, unit test coverage, schema review for index impact, a 200 ms p95 read latency target, health/readiness endpoints, low-priority backfills, single YAML config, alerts paging after five minutes, ninety-day secret rotation, and per-region dashboards. No evidence, data, or references accompany any statement.

### chunk-02 [low] Ledger Service Design > Request handling (L19-L34)

The Request handling section states one design point, idempotency keys on every request to prevent double posting on retry, then lists operational properties of the ledger service in heavily repeated sentences: 200 ms p95 read latency target, alerts paging after five minutes, low-priority backfills, health and readiness endpoints, structured logs with request id, ninety-day secret rotation, single YAML config, schema review for index impact, unit test coverage, per-region dashboards, and a three-phase zero-downtime migration.

### chunk-03 [low] Ledger Service Design > Timeouts and retries (L35-L50)

The chunk states the risk-engine timeout (30 seconds) and retry policy (two retries with backoff), then fills the rest with repeated boilerplate sentences about dashboards, low-priority backfills, structured logging, alert routing, secret rotation, schema review, unit tests, health endpoints, a three-phase migration, a 200 ms p95 read latency target, and single-YAML configuration. No sentence conflicts with another inside this chunk; the padding repeats the same claims many times.

### chunk-04 [low] Ledger Service Design > Storage (L51-L66)

The Storage section states one concrete design fact: transfers go into a month-partitioned transfers table with a covering index on account_id. The rest is boilerplate sentences repeated many times covering logging with request ids, secret rotation, health endpoints, alerting, schema review, a 200 ms p95 read latency target, YAML config, low-priority backfills, unit test coverage, dashboards, and a three-phase migration. No evidence, code, or data supports any of it.

### chunk-05 [low] Ledger Service Design > Reconciliation (L67-L82)

The Reconciliation section states that a nightly job compares ledger totals to the bank feed and opens a ticket on mismatch. The rest of the chunk is repeated boilerplate operational statements: structured logging with request ids, low-priority backfills, per-region dashboards, schema review for index impact, health and readiness endpoints, 90-day secret rotation, 200 ms p95 read latency target, single YAML config, alerts paging after five minutes, and a three-phase zero-downtime migration.

### chunk-06 [low] Ledger Service Design > Operations (L83-L97)

Operations section of the ledger service design. Opens with an on-call note: the risk engine timeout is 90 seconds, so a slow engine stalls 90 seconds before retry. The rest is heavily repeated boilerplate: per-region dashboards, low-priority backfills, health/readiness endpoints, single YAML config, 90-day secret rotation, alerts paging after five minutes, structured logs per write, unit test coverage, 200 ms p95 read latency target, index-impact schema review, and a three-phase no-downtime migration.

## Claims

| status | claim | anchor |
|---|---|---|
| contradicted | Downstream calls to the risk engine time out after 30 seconds. | L37 'time out after 30 seconds' vs L85 'timeout is 90 seconds' |
| contradicted | Risk engine timeout is 90 seconds; a slow engine stalls 90 seconds before retry. | L37 'time out after 30 seconds' vs L85 'timeout is 90 seconds' |
| unverified | The migration ran in three phases over two weekends without downtime. | L7 |
| unverified | Read latency targets stay under 200 ms at the 95th percentile. | L7 |
| unverified | Unit tests cover the parser, the validator, and the posting logic. | L7 |
| unverified | Alerts route to the payments channel and page after five minutes. | L11 |
| unverified | Secrets rotate every ninety days through the platform vault. | L15 |
| unverified | Backfills run at low priority so they do not starve live traffic. | L7 |
| unverified | Each request carries an idempotency key so retried transfers do not post twice. | L21 |
| unverified | Read latency target is under 200 ms at the 95th percentile. | L23 |
| unverified | Alerts route to the payments channel and page after five minutes. | L23 |
| unverified | The migration ran in three phases over two weekends without downtime. | L23 |
| unverified | Secrets rotate every ninety days through the platform vault. | L25 |
| unverified | Unit tests cover the parser, the validator, and the posting logic. | L23 |
| unverified | The client retries risk-engine calls twice with backoff. | L37 |
| unverified | Alerts route to the payments channel and page after five minutes. | L39 |
| unverified | Secrets rotate every ninety days through the platform vault. | L41 |
| unverified | Read latency target is under 200 ms at the 95th percentile. | L43 |
| unverified | The migration ran in three phases over two weekends without downtime. | L39 |
| unverified | Transfers table is partitioned by month with a covering index on account_id. | L53 |
| unverified | Read latency target is under 200 ms at the 95th percentile. | L55 |
| unverified | The migration ran in three phases over two weekends without downtime. | L55 |
| unverified | Alerts route to the payments channel and page after five minutes. | L55 |
| unverified | Secrets rotate every ninety days through the platform vault. | L55 |
| unverified | Configuration lives in a single YAML file loaded at startup. | L57 |
| unverified | A nightly job compares ledger totals against the bank feed and opens a ticket on any mismatch. | L69 |
| unverified | The migration ran in three phases over two weekends without downtime. | L71 |
| unverified | Latency targets stay under 200 ms at the 95th percentile for reads. | L73 |
| unverified | Secrets rotate every ninety days through the platform vault. | L73 |
| unverified | Alerts route to the payments channel and page after five minutes. | L73 |
| unverified | Every write path emits a structured log line with the request id. | L71 |
| unverified | Alerts route to the payments channel and page after five minutes. | L87 |
| unverified | Secrets rotate every ninety days through the platform vault. | L87 |
| unverified | Read latency target is under 200 ms at the 95th percentile. | L89 |
| unverified | Migration ran in three phases over two weekends without downtime. | L87 |
| unverified | Unit tests cover the parser, validator, and posting logic. | L89 |

## Risks

- **uncited-number** [low] L7: 200 ms p95 target stated repeatedly with no measurement or source.
- **uncited-number** [low] L7: Three phases, two weekends, zero downtime asserted without migration record.
- **uncited-number** [low] L23: 200 ms p95 target and five-minute page threshold given with no measurements or source.
- **uncited-number** [low] L37: 30-second timeout and two retries stated with no source or rationale.
- **uncited-number** [low] L43: 200 ms p95 read target has no measurement or source.
- **uncited-number** [low] L55: 200 ms p95 target, five-minute page delay, ninety-day rotation stated with no source.
- **uncited-number** [low] L73: 200 ms p95 read target stated with no measurement or source.
- **uncited-number** [low] L85: 90 second timeout stated without config or source reference; check against the rest of the design.
- **uncited-number** [low] L89: 200 ms p95 read target given with no measurement or SLO source.
- **unsupported-claim** [low] L7: Unit test coverage claimed with no test list or coverage figure.
- **unsupported-claim** [low] L7: Section repeats the same sentences many times; reads as filler, not design content.
- **unsupported-claim** [low] L23: Zero-downtime migration claim has no evidence; also stated as past fact in a design doc.
- **unsupported-claim** [low] L23: Section titled Request handling but most text is unrelated ops boilerplate, repeated many times.
- **unsupported-claim** [low] L39: Migration completed without downtime is asserted, not evidenced.
- **unsupported-claim** [low] L39: Paragraphs repeat identical sentences; reads as filler, not design content.
- **unsupported-claim** [low] L55: Migration completed without downtime is asserted with no evidence or date.
- **unsupported-claim** [low] L53: Partitioning and index design given without schema or query evidence.
- **unsupported-claim** [low] L57: Section is heavily repeated boilerplate; unclear which sentences are real design decisions.
- **unsupported-claim** [low] L71: Zero-downtime three-phase migration asserted without dates, evidence, or link.
- **unsupported-claim** [low] L69: Nightly reconciliation job described with no job name, schedule, or ticket system reference.
- **unsupported-claim** [low] L87: Zero-downtime three-phase migration asserted with no dates or evidence.
- **unsupported-claim** [low] L95: Design reviewed in spring planning cycle; no reviewers or record named.

## Least confident

- chunk-01: Whether the heavy repetition hides a subtle variant of a sentence that I missed; I found no internal contradiction in this chunk.
- chunk-02: I could not tell whether the repeated sentences are intentional content or filler, and no sentence in the chunk cites evidence for any claim.
- chunk-03: I could not check whether the 30-second timeout with two retries is compatible with the 200 ms p95 latency target or other sections' timeout values.
- chunk-04: I could not tell whether the repeated sentences in L55-L65 are intended content or filler, so I cannot judge which of them a reviewer should treat as real commitments.
- chunk-05: The chunk is mostly repeated boilerplate sentences, so I could not tell which statements are specific to reconciliation versus generic filler.
- chunk-06: The 90 second risk engine timeout on L85 is the one specific figure here, and I cannot check it against the timeout stated elsewhere in the document.

_6 chunks, 36 claims (0 verified, 34 unverified, 2 contradicted), 22 risks._
