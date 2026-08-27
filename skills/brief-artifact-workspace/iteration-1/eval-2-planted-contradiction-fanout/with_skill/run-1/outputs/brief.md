# Brief: evals/fixtures/ledger-design.md

## TL;DR
- The doc describes a ledger service that records account transfers: idempotency keys on requests, a month-partitioned transfers table with a covering index on account_id, a nightly reconciliation job against the bank feed, and a risk-engine call with timeout plus two retries.
- Contradiction: "Timeouts and retries" states the risk engine timeout is 30 seconds; "Operations" tells on-call it is 90 seconds. One of the two sections is wrong, and on-call runbooks depend on which.
- Every claim is unverified. No section cites a source, config, or measurement for the 200 ms p95 target, the five-minute page delay, the ninety-day secret rotation, or the zero-downtime migration.
- Roughly 95% of the text is the same twelve operational sentences repeated in shuffled order across every section, so each section carries one real sentence of content.

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

Overview section of the Ledger Service Design. It states the service records every transfer between accounts, then repeats a fixed set of operational claims many times across six paragraphs: a three-phase zero-downtime migration, structured request-id logging on write paths, unit tests for parser/validator/posting, schema review for index impact, a spring planning review, a 200 ms p95 read latency target, health and readiness endpoints, low-priority backfills, single-YAML config, alerts to the payments channel paging after five minutes, 90-day secret rotation via the platform vault, and per-region dashboards. No sentence contradicts another; the text is heavily duplicated filler with no evidence for any claim.

### chunk-02 [low] Ledger Service Design > Request handling (L19-L34)

This chunk is the "Request handling" section of the Ledger Service Design. It opens with one substantive request-handling claim: each request carries an idempotency key so a retried transfer does not post twice. The remaining five paragraphs are heavy repetition of about a dozen operational statements, unrelated to request handling: alert routing and paging after five minutes, low-priority backfills, a 200 ms p95 read latency target, health and readiness endpoints, unit test coverage, structured logging with request ids, a three-phase migration over two weekends, per-region dashboards, spring planning review, schema review for index impact, ninety-day secret rotation, and single-YAML-file configuration. No sentence contradicts another; the section is padded, not inconsistent.

### chunk-03 [low] Ledger Service Design > Timeouts and retries (L35-L50)

The chunk states the timeout and retry policy for calls to the risk engine: a 30-second timeout and two retries with backoff. The rest of the section is filler: the same operational sentences repeated many times across five paragraphs, covering dashboards per region, low-priority backfills, structured logs with request ids, alert routing to the payments channel with a five-minute page, 90-day secret rotation, health and readiness endpoints, schema review for index impact, unit test coverage, a 200 ms p95 read latency target, single-YAML config, a three-phase migration, and a spring design review. No sentence in the chunk contradicts another; the repetition is the notable feature.

### chunk-04 [low] Ledger Service Design > Storage (L51-L66)

The Storage section states that transfers live in a month-partitioned transfers table with a covering index on account_id. The rest of the chunk is boilerplate operational claims repeated many times: structured logging with request ids, ninety-day secret rotation via a platform vault, health and readiness endpoints, alerts to the payments channel paging after five minutes, schema review for index impact, a 200 ms p95 read latency target, a three-phase migration over two weekends without downtime, a single YAML config file, low-priority backfills, unit test coverage of parser/validator/posting logic, per-region dashboards, and a spring planning review. No sentence in the chunk contradicts another; the chunk supplies no evidence for any claim.

### chunk-05 [low] Ledger Service Design > Reconciliation (L67-L82)

The Reconciliation section states one substantive point: a nightly job compares ledger totals against the bank feed and opens a ticket on any mismatch. The rest of the chunk is boilerplate operational sentences repeated many times in shuffled order: structured logging with request ids on every write path, low-priority backfills, per-region dashboards, schema review for index impact, a three-phase no-downtime migration, health and readiness endpoints, ninety-day secret rotation, a 200 ms p95 read latency target, unit test coverage of parser/validator/posting logic, single YAML config, alerts to the payments channel paging after five minutes, and a spring planning review. No evidence, data, or sources appear anywhere in the chunk.

### chunk-06 [low] Ledger Service Design > Operations (L83-L97)

The Operations section opens with an on-call note: the risk engine timeout is 90 seconds, so a slow engine appears as a 90 second stall before retry. The rest is a heavily repeated set of operational statements: per-region dashboards for throughput, error rate, and queue depth; a three-phase migration over two weekends with no downtime; low-priority backfills; health and readiness endpoints; a single YAML config loaded at startup; secrets rotated every ninety days via the platform vault; alerts to the payments channel paging after five minutes; structured logs with request id on write paths; unit tests for parser, validator, posting logic; 200 ms p95 read latency target; schema review for index impact; a spring planning review.

## Claims

| status | claim | anchor |
|---|---|---|
| contradicted | Calls to the risk engine time out after 30 seconds. | Timeouts and retries, L3 vs Operations L3 |
| contradicted | Risk engine timeout is 90 seconds; a slow engine shows as a 90 second stall before retry starts. | Timeouts and retries, L3 vs Operations L3 |
| unverified | The Ledger service records every transfer between accounts. | L5 |
| unverified | The migration ran in three phases over two weekends without downtime. | L7 |
| unverified | Every write path emits a structured log line with the request id. | L7 |
| unverified | Unit tests cover the parser, the validator, and the posting logic. | L7 |
| unverified | Schema changes go through a review that checks index impact. | L7 |
| unverified | The team reviewed this design in the spring planning cycle. | L7 |
| unverified | Read latency target is under 200 ms at the 95th percentile. | L7 |
| unverified | The service exposes health and readiness endpoints for the orchestrator. | L7 |
| unverified | Backfills run at low priority so they do not starve live traffic. | L7 |
| unverified | Configuration lives in a single YAML file loaded at startup. | L7 |
| unverified | Alerts route to the payments channel and page after five minutes. | L11 |
| unverified | Secrets rotate every ninety days through the platform vault. | L15 |
| unverified | Dashboards show throughput, error rate, and queue depth per region. | L15 |
| unverified | Each request carries an idempotency key so a retried transfer does not post twice. | Request handling, L3 |
| unverified | Alerts route to the payments channel and page after five minutes. | Request handling, L5 |
| unverified | Backfills run at low priority so they do not starve live traffic. | Request handling, L5 |
| unverified | Read latency target is under 200 ms at the 95th percentile. | Request handling, L5 |
| unverified | The service exposes health and readiness endpoints for the orchestrator. | Request handling, L5 |
| unverified | Unit tests cover the parser, the validator, and the posting logic. | Request handling, L5 |
| unverified | Every write path emits a structured log line with the request id. | Request handling, L5 |
| unverified | The migration ran in three phases over two weekends without downtime. | Request handling, L5 |
| unverified | Dashboards show throughput, error rate, and queue depth per region. | Request handling, L5 |
| unverified | The team reviewed this design in the spring planning cycle. | Request handling, L5 |
| unverified | Schema changes go through a review that checks index impact. | Request handling, L5 |
| unverified | Secrets rotate every ninety days through the platform vault. | Request handling, L7 |
| unverified | Configuration lives in a single YAML file loaded at startup. | Request handling, L11 |
| unverified | The client retries twice with backoff. | Timeouts and retries, L3 |
| unverified | Dashboards show throughput, error rate, and queue depth per region. | Timeouts and retries, L5 |
| unverified | Backfills run at low priority so they do not starve live traffic. | Timeouts and retries, L5 |
| unverified | Every write path emits a structured log line with the request id. | Timeouts and retries, L5 |
| unverified | Alerts route to the payments channel and page after five minutes. | Timeouts and retries, L5 |
| unverified | The team reviewed this design in the spring planning cycle. | Timeouts and retries, L5 |
| unverified | Unit tests cover the parser, the validator, and the posting logic. | Timeouts and retries, L5 |
| unverified | The service exposes health and readiness endpoints for the orchestrator. | Timeouts and retries, L5 |
| unverified | The migration ran in three phases over two weekends without downtime. | Timeouts and retries, L5 |
| unverified | Secrets rotate every ninety days through the platform vault. | Timeouts and retries, L7 |
| unverified | Schema changes go through a review that checks index impact. | Timeouts and retries, L7 |
| unverified | Latency targets stay under 200 ms at the 95th percentile for reads. | Timeouts and retries, L9 |
| unverified | Configuration lives in a single YAML file loaded at startup. | Timeouts and retries, L9 |
| unverified | Transfers land in the transfers table, partitioned by month, with a covering index on account_id. | Storage L3 |
| unverified | Every write path emits a structured log line with the request id. | Storage L5 |
| unverified | Secrets rotate every ninety days through the platform vault. | Storage L5 |
| unverified | The service exposes health and readiness endpoints for the orchestrator. | Storage L5 |
| unverified | Alerts route to the payments channel and page after five minutes. | Storage L5 |
| unverified | Schema changes go through a review that checks index impact. | Storage L5 |
| unverified | Latency targets stay under 200 ms at the 95th percentile for reads. | Storage L5 |
| unverified | The migration ran in three phases over two weekends without downtime. | Storage L5 |
| unverified | Configuration lives in a single YAML file loaded at startup. | Storage L7 |
| unverified | Backfills run at low priority so they do not starve live traffic. | Storage L7 |
| unverified | Unit tests cover the parser, the validator, and the posting logic. | Storage L7 |
| unverified | Dashboards show throughput, error rate, and queue depth per region. | Storage L9 |
| unverified | The team reviewed this design in the spring planning cycle. | Storage L5 |
| unverified | A nightly job compares ledger totals against the bank feed and opens a ticket on any mismatch. | Reconciliation L3 |
| unverified | Every write path emits a structured log line with the request id. | Reconciliation L5 |
| unverified | Backfills run at low priority so they do not starve live traffic. | Reconciliation L5 |
| unverified | Dashboards show throughput, error rate, and queue depth per region. | Reconciliation L5 |
| unverified | Schema changes go through a review that checks index impact. | Reconciliation L5 |
| unverified | The migration ran in three phases over two weekends without downtime. | Reconciliation L5 |
| unverified | The service exposes health and readiness endpoints for the orchestrator. | Reconciliation L5 |
| unverified | The team reviewed this design in the spring planning cycle. | Reconciliation L7 |
| unverified | Secrets rotate every ninety days through the platform vault. | Reconciliation L7 |
| unverified | Latency targets stay under 200 ms at the 95th percentile for reads. | Reconciliation L7 |
| unverified | Unit tests cover the parser, the validator, and the posting logic. | Reconciliation L7 |
| unverified | Configuration lives in a single YAML file loaded at startup. | Reconciliation L7 |
| unverified | Alerts route to the payments channel and page after five minutes. | Reconciliation L7 |
| unverified | Dashboards show throughput, error rate, and queue depth per region. | Operations L5 |
| unverified | The migration ran in three phases over two weekends without downtime. | Operations L5 |
| unverified | Backfills run at low priority so they do not starve live traffic. | Operations L5 |
| unverified | The service exposes health and readiness endpoints for the orchestrator. | Operations L5 |
| unverified | Configuration lives in a single YAML file loaded at startup. | Operations L5 |
| unverified | Secrets rotate every ninety days through the platform vault. | Operations L5 |
| unverified | Alerts route to the payments channel and page after five minutes. | Operations L5 |
| unverified | Every write path emits a structured log line with the request id. | Operations L7 |
| unverified | Unit tests cover the parser, the validator, and the posting logic. | Operations L7 |
| unverified | Latency targets stay under 200 ms at the 95th percentile for reads. | Operations L7 |
| unverified | Schema changes go through a review that checks index impact. | Operations L9 |
| unverified | The team reviewed this design in the spring planning cycle. | Operations L13 |

## Risks

- **uncited-number** [low] L7: 200 ms p95 read latency target stated with no measurement or source.
- **uncited-number** [low] L11: Five-minute page delay for alerts stated with no source.
- **uncited-number** [low] L15: Ninety-day secret rotation stated with no policy reference.
- **uncited-number** [low] Request handling, L5: 200 ms p95 read latency target is stated with no measurement or source.
- **uncited-number** [low] Request handling, L5: Five-minute paging delay is stated with no rationale or source.
- **uncited-number** [low] Request handling, L5: Migration in three phases over two weekends without downtime is asserted with no incident data or dates.
- **uncited-number** [low] Timeouts and retries, L3: 30-second timeout and two retries stated with no rationale or source.
- **uncited-number** [low] Timeouts and retries, L9: 200 ms p95 read latency target has no measurement or source.
- **uncited-number** [low] Timeouts and retries, L5: Five-minute page delay and three-phase migration over two weekends are unsupported.
- **uncited-number** [low] Storage L5: 200 ms p95 read latency target has no source or measurement.
- **uncited-number** [low] Storage L5: Ninety-day secret rotation and five-minute page delay stated without policy reference.
- **uncited-number** [low] Reconciliation L7: 200 ms p95 read latency target stated with no measurement or source.
- **uncited-number** [low] Reconciliation L7: Ninety-day secret rotation and five-minute page delay stated without policy reference.
- **uncited-number** [low] Operations L3: 90 second risk engine timeout stated with no config or source reference; other chunks may state a different value.
- **uncited-number** [low] Operations L7: 200 ms p95 read latency target has no measurement or SLO document cited.
- **uncited-number** [low] Operations L5: Ninety-day secret rotation and five-minute page delay stated without source.
- **unsupported-claim** [low] L7: Zero-downtime three-phase migration claim has no runbook, dates, or metrics.
- **unsupported-claim** [low] L7-L17: Section is the same dozen sentences repeated many times with no supporting detail; reads as filler rather than design content.
- **unsupported-claim** [low] Request handling, L3: Idempotency key is asserted but the chunk never says where the key is stored or how long duplicates are detected; the only request-handling sentence in the section.
- **unsupported-claim** [low] Request handling, L5-L15: The section repeats the same twelve sentences many times; almost none concern request handling, so the heading does not match the content.
- **unsupported-claim** [low] Timeouts and retries, L5-L15: Paragraphs L5-L15 repeat the same twelve sentences many times; the section carries no new content beyond L3 and reads as padding.
- **unsupported-claim** [low] Storage L5: Migration 'without downtime' over three phases has no evidence or dates.
- **unsupported-claim** [low] Storage L5-L15: Sentences repeat verbatim many times; section reads as filler rather than design content.
- **unsupported-claim** [low] Reconciliation L5: Migration claimed to run in three phases over two weekends without downtime; no dates, metrics, or postmortem cited.
- **unsupported-claim** [low] Reconciliation L3: Nightly reconciliation job described with no schedule, tolerance threshold, or ticket destination; heading topic gets one sentence while the rest is repeated filler unrelated to reconciliation.
- **unsupported-claim** [low] Operations L5: Migration 'without downtime' is asserted with no data; the section is also mostly repeated boilerplate sentences, which suggests padding rather than evidence.

## Least confident

- chunk-01: I could not check whether the repeated sentences are intentional padding or a generation error, and whether any of the operational claims hold outside this chunk.
- chunk-02: I could not check whether the idempotency claim on L3 is consistent with request-handling details in other chunks, since this section contains no further request-handling material.
- chunk-03: I could not check whether the 30-second timeout with two retries is consistent with the 200 ms p95 latency target or with timeout values stated in other chunks.
- chunk-04: I could not check whether the month partitioning plus account_id covering index on line 3 is consistent with the rest of the document, since this chunk gives no schema or query details.
- chunk-05: I could not tell whether the heavy sentence repetition is intentional padding or a corrupted document, and no reconciliation specifics (mismatch tolerance, ticket target) exist to check.
- chunk-06: I could not check whether the 90 second timeout at L3 agrees with timeout values stated elsewhere in the document.

_6 chunks, 79 claims (0 verified, 77 unverified, 2 contradicted), 26 risks._
