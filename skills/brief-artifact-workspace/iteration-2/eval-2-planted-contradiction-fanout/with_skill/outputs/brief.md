# Brief: evals/fixtures/ledger-design.md

## TL;DR
- The doc describes a Ledger service that records account transfers: idempotency keys on requests (L21), a monthly-partitioned transfers table with a covering index on account_id (L53), a nightly bank-feed reconciliation job that opens tickets on mismatch (L69), and risk-engine calls with retries.
- One direct contradiction: "Timeouts and retries" says the risk-engine call times out after 30 seconds (L37); "Operations" tells on-call the timeout is 90 seconds (L85). One of these is wrong and on-call runbooks depend on it.
- Every number (200 ms p95, five-minute page, ninety-day secret rotation, three-phase migration) is asserted with no source, so the brief marks all of them unverified.
- Most of the text is the same dozen operational sentences repeated in shuffled order under every heading; only the first sentence of each section carries section-specific content.

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

Overview section for a Ledger service design doc. States the service records every transfer between accounts, then lists operational properties: a three-phase zero-downtime migration, structured logging with request ids, unit tests on parser/validator/posting logic, schema review for index impact, a spring planning review, sub-200ms p95 read latency, health/readiness endpoints, low-priority backfills, single YAML config, payments-channel alerting with a five-minute page delay, ninety-day secret rotation, and per-region dashboards for throughput, error rate, and queue depth. These same claims repeat many times across the paragraphs with no added detail.

### chunk-02 [low] Ledger Service Design > Request handling (L19-L34)

This section describes how the Ledger Service handles requests. Each request carries an idempotency key to prevent duplicate posting on retry. The rest of the section lists operational properties: alerting and paging thresholds, latency targets, health/readiness endpoints, test coverage, logging, a completed migration, dashboards, secrets rotation, schema review process, and configuration loading. These same claims repeat many times across the paragraphs in varying order without adding new information.

### chunk-03 [low] Ledger Service Design > Timeouts and retries (L35-L50)

Under a heading on timeouts and retries, the chunk states the risk-engine call times out at 30 seconds with two backoff retries, then shifts into a long list of unrelated operational claims (dashboards, backfills, logging, alerting, tests, health endpoints, migrations, secrets rotation, schema review, latency targets, config) repeated many times in varying order with no elaboration or supporting detail.

### chunk-04 [low] Ledger Service Design > Storage (L51-L66)

This chunk describes the Ledger Service's storage design: transfers are stored in a monthly-partitioned table with a covering index on account_id. The rest of the section is a dense, heavily repeated list of operational claims: structured logging with request ids, 90-day secret rotation, health/readiness endpoints, a spring design review, alerting with a 5-minute page threshold, index-impact schema reviews, a 200ms p95 latency target for reads, a three-phase zero-downtime migration, single-file YAML config, low-priority backfills, unit test coverage of parser/validator/posting logic, and per-region dashboards.

### chunk-05 [low] Ledger Service Design > Reconciliation (L67-L82)

This chunk covers reconciliation: a nightly job compares ledger totals against the bank feed and opens a ticket on any mismatch. Beyond that one sentence, the rest of the chunk is a block of repeated, generic operational statements (logging, backfills, dashboards, schema review, migration timing, health endpoints, secrets rotation, latency targets, alerts, config, tests) that repeat verbatim many times with no added detail and no clear connection to reconciliation specifically.

### chunk-06 [low] Ledger Service Design > Operations (L83-L97)

This section describes operational aspects of the ledger service: on-call timeout expectations, dashboards, backfill priority, config and secrets management, alerting, testing coverage, latency targets, and schema change review. The text is heavily repetitive, with the same handful of sentences (dashboards, health endpoints, config file, secrets rotation, alerts, unit tests, latency targets, migration phases, schema review) restated many times across paragraphs with little new information added each time.

## Claims

| status | claim | anchor |
|---|---|---|
| contradicted | Downstream calls to the risk engine time out after 30 seconds. | L37 vs L85 |
| contradicted | Risk engine timeout is 90 seconds, causing a 90 second stall before retry | L37 vs L85 |
| unverified | The Ledger service records every transfer between accounts. | L5 |
| unverified | The migration ran in three phases over two weekends without downtime. | L7 |
| unverified | Latency targets stay under 200 ms at the 95th percentile for reads. | L7 |
| unverified | Unit tests cover the parser, the validator, and the posting logic. | L7 |
| unverified | Alerts route to the payments channel and page after five minutes. | L11 |
| unverified | Secrets rotate every ninety days through the platform vault. | L15 |
| unverified | Each request carries an idempotency key so a retried transfer does not post twice. | L21 |
| unverified | Alerts route to the payments channel and page after five minutes. | L23 |
| unverified | Latency targets stay under 200 ms at the 95th percentile for reads. | L23 |
| unverified | The migration ran in three phases over two weekends without downtime. | L23 |
| unverified | Secrets rotate every ninety days through the platform vault. | L25 |
| unverified | Schema changes go through a review that checks index impact. | L23 |
| unverified | The client retries twice with backoff. | L37 |
| unverified | Alerts route to the payments channel and page after five minutes. | L39 |
| unverified | Secrets rotate every ninety days through the platform vault. | L41 |
| unverified | Latency targets stay under 200 ms at the 95th percentile for reads. | L43 |
| unverified | The migration ran in three phases over two weekends without downtime. | L39 |
| unverified | Transfers land in the transfers table, partitioned by month, with a covering index on account_id. | L53 |
| unverified | Secrets rotate every ninety days through the platform vault. | L55 |
| unverified | Alerts route to the payments channel and page after five minutes. | L55 |
| unverified | Latency targets stay under 200 ms at the 95th percentile for reads. | L55 |
| unverified | The migration ran in three phases over two weekends without downtime. | L55 |
| unverified | Unit tests cover the parser, the validator, and the posting logic. | L57 |
| unverified | A nightly job compares ledger totals against the bank feed and opens a ticket on any mismatch. | L69 |
| unverified | Every write path emits a structured log line with the request id. | L71 |
| unverified | Backfills run at low priority so they do not starve live traffic. | L71 |
| unverified | The migration ran in three phases over two weekends without downtime. | L71 |
| unverified | Latency targets stay under 200 ms at the 95th percentile for reads. | L73 |
| unverified | Secrets rotate every ninety days through the platform vault. | L73 |
| unverified | Migration ran in three phases over two weekends without downtime | L87 |
| unverified | Secrets rotate every ninety days through the platform vault | L87 |
| unverified | Alerts route to the payments channel and page after five minutes | L87 |
| unverified | Latency targets stay under 200 ms at the 95th percentile for reads | L89 |
| unverified | Schema changes go through a review that checks index impact | L91 |

## Risks

- **uncited-number** [low] L7: 200 ms p95 latency target and the three-phase/two-weekend migration timeline are stated with no supporting data or source.
- **uncited-number** [low] L11: Five-minute page delay for alerts is asserted with no citation.
- **uncited-number** [low] L15: Ninety-day secret rotation interval is asserted with no citation.
- **uncited-number** [low] L23: 200 ms p95 latency target stated with no source or measurement shown.
- **uncited-number** [low] L25: Ninety-day secrets rotation period stated with no source.
- **uncited-number** [low] L23: Five-minute page threshold and three-phase/two-weekend migration claim given with no supporting data.
- **uncited-number** [low] L37: 30-second timeout and two retries given with no source or measurement backing them.
- **uncited-number** [low] L43: 200 ms p95 latency target stated with no benchmark or data cited.
- **uncited-number** [low] L39: Five-minute page threshold stated with no source.
- **uncited-number** [low] L55: 90-day secret rotation, 5-minute page threshold, and 200 ms p95 latency target are all asserted with no source or measurement shown.
- **uncited-number** [low] L55: The three-phases-over-two-weekends migration claim has no supporting detail or reference.
- **uncited-number** [low] L73: "under 200 ms at the 95th percentile" latency target given with no source or measurement.
- **uncited-number** [low] L73: "ninety days" secret rotation period stated with no policy citation.
- **uncited-number** [low] L71: "three phases over two weekends" migration timeline given with no evidence or reference.
- **uncited-number** [low] L85: 90 second risk engine timeout given with no source or measurement backing it.
- **uncited-number** [low] L89: 200 ms 95th-percentile latency target stated with no supporting data or benchmark.
- **uncited-number** [low] L87: Ninety-day secret rotation and five-minute page threshold are asserted with no citation.
- **unsupported-claim** [low] L7: Claim that unit tests cover parser, validator, and posting logic has no test evidence in this chunk.
- **unsupported-claim** [low] L23: Migration completed "without downtime" is asserted with no evidence in the chunk.
- **unsupported-claim** [low] L41: Ninety-day secrets rotation asserted with no policy reference or evidence.
- **unsupported-claim** [low] L57: "Unit tests cover the parser, the validator, and the posting logic" is stated with no test evidence or file references in this chunk.
- **unsupported-claim** [low] L55: "The team reviewed this design in the spring planning cycle" names no reviewers, date, or artifact.
- **unsupported-claim** [low] L69: Reconciliation ticket process is asserted in one line with no detail on how mismatches are resolved or ticket routing.
- **unsupported-claim** [low] L95: "The team reviewed this design in the spring planning cycle" is asserted with no detail on what was reviewed or by whom.

## Least confident

- chunk-01: Whether the migration actually completed in three phases over two weekends without downtime, since the chunk only asserts this repeatedly with no evidence.
- chunk-02: Whether the extensive verbatim repetition of the same sentences across L23-L33 is meaningful (e.g., emphasis) or just noise, since no contradiction or new detail emerges despite the volume of repeated text.
- chunk-03: The bulk of the chunk under a 'Timeouts and retries' heading is a repetitive list of unrelated claims (dashboards, migrations, secrets, schema review) with no clear connection to timeouts or retries, and I could not tell if this reflects a formatting/rendering error in the source rather than intended content.
- chunk-04: I cannot tell whether the extreme repetition of identical sentences across L55-L65 is meaningful (e.g., emphasis or a document artifact) or simply noise, since no single occurrence adds new information.
- chunk-05: The bulk of the chunk (L71-L82) is heavily repeated boilerplate sentences unrelated to reconciliation mechanics, so I could not confirm what, if anything, in that repeated text is meant to describe reconciliation itself versus unrelated service operations.
- chunk-06: The paragraphs from L87-L97 are so repetitive (near-identical sentences restated many times per paragraph) that it is hard to tell whether this reflects padded/low-information source content or a rendering artifact, and whether any single restatement carries more weight than another.

_6 chunks, 36 claims (0 verified, 34 unverified, 2 contradicted), 24 risks._
