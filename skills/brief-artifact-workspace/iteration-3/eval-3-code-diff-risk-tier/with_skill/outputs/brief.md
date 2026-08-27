# Brief: diff 5e3c12b~3

## TL;DR
- Diff adds three new skills (adversarial-review-2, debug-loop, p-review), their eval suites and fixtures, three research notes, and a brief-artifact plan; one existing file edited (adversarial-review/SKILL.md routes to adversarial-review-2).
- Highest-risk code is fixture code with planted bugs: BOM-breaking CSV report, session tie-break on same-second created_at, float half-cent rounding, O(n*m) enrichment scan, a .stip() typo.
- Two intra-file inconsistencies: adversarial-review-2 says "four subagents" but spawns three; thinking-budget ordering in efficient-debug-loop-strategies.md conflicts with the cited Willison decompilation.
- Research notes carry many unsourced numbers (60% compact threshold, 8-block Stop hook override, 3x subagent cost, bug-bounty stats); treat as unverified.
- Skill boundaries shift: debug-loop declares it supersedes diagnose, and adversarial-review defers severity-graded work to adversarial-review-2.

## Structure map

| id | type | risk | size | anchor |
|---|---|---|---|---|
| chunk-01 | diff | low | 188 lines | docs/plans/brief-artifact-plan.md:1+, resources/efficient-debug-loop-strategies.md:1+ (diff) |
| chunk-02 | diff | low | 80 lines | resources/good-adversarial-review.md:1+ (diff) |
| chunk-03 | diff | low | 229 lines | skills/adversarial-review-2/SKILL.md:1+ (diff) |
| chunk-04 | diff | high | 110 lines | skills/adversarial-review-2/evals/evals.json:1+, skills/adversarial-review-2/evals/files/oncall-rotation-plan.md:1+, skills/adversarial-review-2/evals/files/session-cache-design.md:1+, skills/adversarial-review/SKILL.md:7+ (diff) |
| chunk-05 | diff | low | 255 lines | skills/debug-loop/SKILL.md:1+ (diff) |
| chunk-06 | diff | low | 83 lines | skills/debug-loop/evals/eval_queries.json:1+ (diff) |
| chunk-07 | diff | high | 171 lines | skills/debug-loop/evals/evals.json:1+, skills/debug-loop/evals/fixtures/csv-report/data/sales-2026-08.csv:1+, skills/debug-loop/evals/fixtures/csv-report/report.py:1+, skills/debug-loop/evals/fixtures/csv-report/tests/data/clean.csv:1+, skills/debug-loop/evals/fixtures/csv-report/tests/data/header_only.csv:1+, skills/debug-loop/evals/fixtures/csv-report/tests/test_report.py:1+ (diff) |
| chunk-08 | diff | high | 196 lines | skills/debug-loop/evals/fixtures/expired-sessions/sessions.py:1+, skills/debug-loop/evals/fixtures/expired-sessions/tests/test_sessions.py:1+, skills/debug-loop/evals/fixtures/pricing-regression/pricing.py:1+, skills/debug-loop/evals/fixtures/pricing-regression/tests/test_pricing.py:1+, skills/debug-loop/evals/fixtures/slow-enrichment/enrich.py:1+, skills/debug-loop/evals/fixtures/slow-enrichment/run_nightly.py:1+, skills/debug-loop/evals/fixtures/slow-enrichment/tests/test_enrich.py:1+ (diff) |
| chunk-09 | diff | low | 136 lines | skills/debug-loop/evals/fixtures/slug-typo/slug.py:1+, skills/debug-loop/evals/fixtures/slug-typo/tests/test_slug.py:1+, skills/debug-loop/references/tactics.md:1+ (diff) |
| chunk-10 | diff | low | 131 lines | skills/p-review/SKILL.md:1+ (diff) |

## Chunk summaries

### chunk-04 [high] skills/adversarial-review-2/evals/evals.json:1+, skills/adversarial-review-2/evals/files/oncall-rotation-plan.md:1+, skills/adversarial-review-2/evals/files/session-cache-design.md:1+, skills/adversarial-review/SKILL.md:7+ (diff)

Diff adds an eval suite for a new adversarial-review-2 skill: evals.json defines two red-team evals (a Redis session-cache design and a follow-the-sun on-call plan), each with a prompt, expected output, and expectation checklist. It adds the two fixture documents with planted flaws (KEYS-based invalidation, 8GB sizing, timezone coverage gap, untested Krakow team). It also edits adversarial-review/SKILL.md description to route severity-graded or retest requests to adversarial-review-2.

### chunk-07 [high] skills/debug-loop/evals/evals.json:1+, skills/debug-loop/evals/fixtures/csv-report/data/sales-2026-08.csv:1+, skills/debug-loop/evals/fixtures/csv-report/report.py:1+, skills/debug-loop/evals/fixtures/csv-report/tests/data/clean.csv:1+, skills/debug-loop/evals/fixtures/csv-report/tests/data/header_only.csv:1+, skills/debug-loop/evals/fixtures/csv-report/tests/test_report.py:1+ (diff)

Adds evals.json for the debug-loop skill with five evals (vague login failure, pasted traceback, red tests after merge, trivial typo fast path, perf regression), each with a fixture path, prompt, and expectations. Also adds the csv-report fixture: a BOM-prefixed sales CSV, a report.py that opens files as plain utf-8 and reads row["region"], two clean test CSVs, and a two-test suite that passes on the clean data.

### chunk-08 [high] skills/debug-loop/evals/fixtures/expired-sessions/sessions.py:1+, skills/debug-loop/evals/fixtures/expired-sessions/tests/test_sessions.py:1+, skills/debug-loop/evals/fixtures/pricing-regression/pricing.py:1+, skills/debug-loop/evals/fixtures/pricing-regression/tests/test_pricing.py:1+, skills/debug-loop/evals/fixtures/slow-enrichment/enrich.py:1+, skills/debug-loop/evals/fixtures/slow-enrichment/run_nightly.py:1+, skills/debug-loop/evals/fixtures/slow-enrichment/tests/test_enrich.py:1+ (diff)

Adds three new debug-loop eval fixtures, each a small Python module plus pytest tests. expired-sessions: an append-only in-memory session store where get_session picks the newest row by created_at and refresh returns 404/401/200. pricing-regression: line_total and order_total with cent rounding. slow-enrichment: enrich_orders attaches customers to orders via a linear scan over a list, plus a nightly runner that times 20000x20000 records.

### chunk-01 [low] docs/plans/brief-artifact-plan.md:1+, resources/efficient-debug-loop-strategies.md:1+ (diff)

Diff adds two new markdown files. First is a plan for a brief-artifact skill: chunk prose, code, or diffs; read chunks sequentially or via subagents; extract claims with anchors and status; render a layered brief. Second is a debug-loop playbook for Claude Code: verification-driven loops, context management (/clear after two failed corrections, /compact at ~60%), prompting tips, hooks and subagents, anti-patterns table, hallucinated-package statistics, staged recommendations, and caveats about secondary numbers.

### chunk-02 [low] resources/good-adversarial-review.md:1+ (diff)

Adds a new 78-line markdown resource arguing that a good adversarial review of an AI chatbot depends on discipline: explicit impact-first threat model, diverse and partly independent testers, taxonomy-anchored reproducible methodology, manual plus automated probing, severity grading, and a closed remediate-retest loop. It cites NIST, OWASP, MITRE ATLAS, Microsoft, OpenAI, Anthropic, DeepMind, and Feffer et al., lists pitfalls of weak reviews, gives a four-stage recommendation, and closes with caveats about field immaturity and metric fragility.

### chunk-03 [low] skills/adversarial-review-2/SKILL.md:1+ (diff)

New file adding the adversarial-review-2 skill. It defines a five-stage red-team workflow: intake, a one-page charter naming ranked harm categories, three parallel fresh-eyes adversary subagents with distinct lenses and a fixed finding format, main-agent verification/dedup/seam-sweep with an outcome-based Critical-to-Low severity rubric and strict total ranking, a fixed-section report, and a retest stage that re-runs each failing scenario after fixes. Ends with gotchas and a worked example finding.

### chunk-05 [low] skills/debug-loop/SKILL.md:1+ (diff)

New debug-loop skill file. Description triggers on any bug report and supersedes the diagnose skill. Workflow: gather symptom, repro, check, scope (Step 0); emit a Debug Brief with ranked hypotheses or a three-line fast-path brief (Step 1/1a); commit a failing test before fixing (Step 2); instrument (Step 3); one change then run the check (Step 4); verify via full run and revert (Step 5); hand off after two failed fixes (Step 6). Ends with example, gotchas, and references/tactics.md pointers.

### chunk-06 [low] skills/debug-loop/evals/eval_queries.json:1+ (diff)

Adds a new file eval_queries.json for the debug-loop skill: a JSON array of 20 trigger-test cases. Each entry pairs a user query with a should_trigger boolean. Eleven positive cases cover build failures, red tests, pasted tracebacks, CI logs, regressions, intermittent bugs, performance slowdowns, and a trivial typo. Nine negative cases cover feature work, PR review, refactoring, TDD, cleanup, code explanation, lint fixes, brainstorming, and theory questions.

### chunk-09 [low] skills/debug-loop/evals/fixtures/slug-typo/slug.py:1+, skills/debug-loop/evals/fixtures/slug-typo/tests/test_slug.py:1+, skills/debug-loop/references/tactics.md:1+ (diff)

Adds three new files. A slug-typo eval fixture: slug.py with a deliberate typo (`.stip()` instead of `.strip()`) and a pytest file with three slugify tests that will fail on AttributeError. And references/tactics.md, a debug guide covering git bisect, building a check when none exists, PostToolUse/Stop hooks as gates, delegating disposable investigation to subagents, catching overfitted fixes, and context hygiene (compact at ~60%, /clear between bugs).

### chunk-10 [low] skills/p-review/SKILL.md:1+ (diff)

Adds a new skill file skills/p-review/SKILL.md defining a one-reviewer adversarial review. The conductor establishes artifact, baseline (via git merge-base fallbacks), and intent, dispatches a fresh subagent with a verbatim brief, rules on findings by vetoing only false premises, then presents Concerns, noted-not-recommended, Rejected, and writes Minor findings to minor-findings.md. A --inline flag skips the subagent and the Ruling step.

## Claims

| status | claim | anchor |
|---|---|---|
| contradicted | Thinking budget ordering: blog implies strict order, Willison decompilation says think harder and ultrathink both 31,999. | resources/efficient-debug-loop-strategies.md:63 vs resources/efficient-debug-loop-strategies.md:116 |
| contradicted | Overkill check says 'four subagents' though Stage 2 spawns three adversaries. | skills/adversarial-review-2/SKILL.md:50 vs skills/adversarial-review-2/SKILL.md:75 |
| unverified | Chroma Context Rot report evaluated 18 frontier models and found performance degrades with input length. | resources/efficient-debug-loop-strategies.md:14 |
| unverified | Anthropic docs recommend /clear after correcting Claude more than twice on same issue. | resources/efficient-debug-loop-strategies.md:16 |
| unverified | USENIX 2025 study found 19.7% of recommended packages across 576,000 samples were hallucinated. | resources/efficient-debug-loop-strategies.md:79 |
| unverified | NIST AI 600-1 defines 12 GenAI risk categories and places red teaming under Measure as a recurring activity. | resources/good-adversarial-review.md:33 |
| unverified | Crescendomation achieves 29-61% higher performance on GPT-4 and 49-71% on Gemini-Pro, 98% binary success on GPT-4. | resources/good-adversarial-review.md:50 |
| unverified | Constitutional Classifiers cut jailbreak success from 86% to 4.4% at 23.7% compute overhead and 0.38% refusal rise. | resources/good-adversarial-review.md:56 |
| unverified | Constitutional Classifiers++ released January 9, 2026 at ~1% additional compute with no universal jailbreak found. | resources/good-adversarial-review.md:56 |
| unverified | Skill cites NIST, OWASP, and Microsoft's 100-product retrospective as converging on discipline over cleverness. | skills/adversarial-review-2/SKILL.md:26-28 |
| unverified | Skill supersedes the diagnose skill; when both match, run debug-loop only. | skills/debug-loop/SKILL.md:18 |
| unverified | references/tactics.md contains sections on building a check, git bisect, hooks, and overfitting. | skills/debug-loop/SKILL.md:252 |
| unverified | /rewind checkpoints track only file-editing tool edits, not shell command changes. | skills/debug-loop/SKILL.md:247 |
| unverified | Traceback query embeds escaped newlines and quotes; JSON remains valid. | skills/debug-loop/evals/eval_queries.json:25 |
| unverified | Fixtures expired-sessions, pricing-regression, slug-typo, slow-enrichment exist with the behavior the expectations describe. | skills/debug-loop/evals/evals.json:13,59,82,105 |
| unverified | test_half_cent_rounds_up expects line_total(0.70,3,5)==2.00; float 1.995 rounds to 1.99 in Python, so this test fails. | tests/test_pricing.py:128 |
| unverified | Claude Code overrides a Stop hook after 8 consecutive blocks. | skills/debug-loop/references/tactics.md:63 |
| unverified | A subagent run costs about three times the tokens of the same work inline. | skills/debug-loop/references/tactics.md:81 |
| unverified | Auto-compaction fires exactly when reliability is already lowest; compact at about 60% instead. | skills/debug-loop/references/tactics.md:100 |
| unverified | Description claims this is cheaper than debate-review, adversarial-review, adversarial-review-2, which exist as skills. | skills/p-review/SKILL.md:17-19 |
| verified | Plan splits reading by size: under 4 chunks sequential, 4+ chunks one subagent per chunk. | docs/plans/brief-artifact-plan.md:17 |
| verified | Plan says chunk summary limit is 120 words. | docs/plans/brief-artifact-plan.md:43 |
| verified | Feffer et al. (AIES 2024) found red-teaming purposes often vague and warned unstructured red teaming verges on security theater. | resources/good-adversarial-review.md:31 |
| verified | OpenAI white paper arXiv 2503.16431 lays out four campaign design steps and cohort diversity axes. | resources/good-adversarial-review.md:38 |
| verified | Adversaries receive only the brief, artifact, and charter; conversation history is never pasted. | skills/adversarial-review-2/SKILL.md:80-82 |
| verified | Each adversary returns at most 4 findings in a fixed format with category, scenario, root cause, fix. | skills/adversarial-review-2/SKILL.md:95-104 |
| verified | Severity rubric grades outcomes: Critical includes failing the artifact's own stated goal from day one. | skills/adversarial-review-2/SKILL.md:138 |
| verified | Charter written next to the artifact, falling back to scratchpad if directory rejects new files. | skills/adversarial-review-2/SKILL.md:56-57 |
| verified | evals.json expects reports to flag 200k sessions x 40KB = 8GB equal to free cluster memory. | skills/adversarial-review-2/evals/evals.json:22 |
| verified | session-cache-design.md states ~40KB per hash, ~200k sessions, 8GB free, matching the eval expectation. | skills/adversarial-review-2/evals/files/session-cache-design.md:110 |
| verified | Invalidation uses KEYS session:*:pricing then DEL on a shared Redis cluster, the planted blocking flaw. | skills/adversarial-review-2/evals/files/session-cache-design.md:106 |
| verified | Eval expects timezone gap: Krakow 08:00-20:00 CET = 02:00-14:00 ET, leaving 20:00-02:00 ET uncovered. | skills/adversarial-review-2/evals/evals.json:41 |
| verified | On-call plan notes Krakow team joined 6 weeks ago, no prod ships, access still in progress. | skills/adversarial-review-2/evals/files/oncall-rotation-plan.md:78 |
| verified | adversarial-review SKILL.md now routes severity-graded findings or retest loops to adversarial-review-2. | skills/adversarial-review/SKILL.md:128 |
| verified | Step 2 commits the failing test before any fix, overriding the commit-only-when-asked default. | skills/debug-loop/SKILL.md:119 |
| verified | Fast path applies only when all three conditions hold: file/line named, line explains failure, single-place fix. | skills/debug-loop/SKILL.md:95 |
| verified | Reset trigger fires after two failed fixes on the same issue, then hand off via Debug Handoff block. | skills/debug-loop/SKILL.md:80 |
| verified | File is new; 82 lines added, none removed. | skills/debug-loop/evals/eval_queries.json:1 |
| verified | Array holds 20 entries: 11 should_trigger true, 9 false. | skills/debug-loop/evals/eval_queries.json:7 |
| verified | A trivial typo blowing up the suite is expected to trigger the skill. | skills/debug-loop/evals/eval_queries.json:33 |
| verified | Performance regressions and nightly queue backups are expected to trigger. | skills/debug-loop/evals/eval_queries.json:45 |
| verified | Lint violations and error-handling cleanup are expected not to trigger. | skills/debug-loop/evals/eval_queries.json:69 |
| verified | Five evals defined, ids 0-4, each naming a fixture directory under evals/fixtures/. | skills/debug-loop/evals/evals.json:10-124 |
| verified | sales-2026-08.csv header starts with a UTF-8 BOM before 'region'. | skills/debug-loop/evals/fixtures/csv-report/data/sales-2026-08.csv:1 |
| verified | report.py opens with encoding="utf-8" (not utf-8-sig), so BOM stays in first header key and row["region"] raises KeyError. | skills/debug-loop/evals/fixtures/csv-report/report.py:5-12 |
| verified | Test suite uses only BOM-free CSVs, so it stays green while the export crashes, matching the eval prompt. | skills/debug-loop/evals/fixtures/csv-report/tests/test_report.py:9-15 |
| verified | Eval 1 traceback cites report.py line 20 and line 12, which match the fixture's line numbers. | skills/debug-loop/evals/evals.json:37 |
| verified | get_session selects the row with the greatest created_at, ignoring version; created_at has one-second resolution per docstring. | sessions.py:37 |
| verified | refresh treats expires_at equal to now as expired (<=), returning status 401. | sessions.py:45 |
| verified | line_total computes round(unit_price*qty*(1-discount_pct/100), 2) with float arithmetic and Python round. | pricing.py:95 |
| verified | index_customers returns a list of dict copies; enrich_orders scans it linearly per order, giving O(orders*customers). | enrich.py:146 |
| verified | run_nightly builds 20000 customers and 20000 orders and prints elapsed seconds for enrich_orders. | run_nightly.py:177 |
| verified | slug.py calls text.lower().stip(), a misspelling of strip(); every test raises AttributeError. | skills/debug-loop/evals/fixtures/slug-typo/slug.py:7 |
| verified | Tests insert parent directory into sys.path to import slug directly. | skills/debug-loop/evals/fixtures/slug-typo/tests/test_slug.py:3 |
| verified | Git bisect finds the culprit in about 10 steps across 1,000 commits. | skills/debug-loop/references/tactics.md:19 |
| verified | --inline skips subagent dispatch and the Ruling step; conductor reviews directly using the brief. | skills/p-review/SKILL.md:24-25, 45-47 |
| verified | Baseline resolves via git merge-base HEAD @{u}, falls back to origin/HEAD, then asks the user. | skills/p-review/SKILL.md:32-36 |
| verified | Reviewer must not report issues that compiler, linter, type-checker, or tests would catch. | skills/p-review/SKILL.md:79-81 |
| verified | Ruling rejects only findings on false premises; all other findings are kept. | skills/p-review/SKILL.md:118-120 |
| verified | Minor findings are written verbatim to minor-findings.md beside the artifact or at repo root, never printed. | skills/p-review/SKILL.md:132-136 |

## Risks

- **duplicate-logic** [high] enrich.py:154: index_customers builds a list, not a dict; nested loop does 400M comparisons on nightly input.
- **missing-edge-case** [high] skills/adversarial-review-2/evals/evals.json:15: Files paths are relative (evals/files/...); resolution base directory not shown in chunk.
- **missing-edge-case** [high] skills/debug-loop/evals/fixtures/csv-report/report.py:12: Intentional fixture bug: no BOM-aware decoding; also float(row["amount"]) has no guard for blank or malformed amounts.
- **missing-edge-case** [high] skills/debug-loop/evals/evals.json:86: Fast-path expectation 'about three lines' is fuzzy; grader may score inconsistently on brief length.
- **missing-edge-case** [high] sessions.py:37: Two rows with same created_at (same-second refresh) tie; max returns first, not highest version.
- **missing-edge-case** [high] pricing.py:95: Float round on half-cent values (1.995) yields 1.99; test and order_total assertion likely fail.
- **uncited-number** [high] skills/adversarial-review-2/evals/evals.json:41: CET-to-ET 6-hour offset assumed; DST mismatch weeks make it 5 hours, shifting the stated gap.
- **unsupported-claim** [high] skills/adversarial-review/SKILL.md:129: References adversarial-review-2 skill; its SKILL.md is not in this chunk, so existence is unconfirmed.
- **missing-edge-case** [low] skills/adversarial-review-2/SKILL.md:65-76: Charter allows 3-5 harm categories but Stage 2 assigns exactly top three; merge/split guidance is vague.
- **missing-edge-case** [low] skills/debug-loop/evals/eval_queries.json:73: "broken by design" query marked false; contains word broken, likely false-positive trigger boundary worth checking.
- **missing-edge-case** [low] skills/debug-loop/evals/eval_queries.json:77: Linter "complaining" case marked false; ambiguous with fix-the-suite positives like line 33.
- **missing-edge-case** [low] skills/p-review/SKILL.md:32-36: Baseline procedure covers only diffs; plans get n/a but conductor steps do not say so explicitly.
- **missing-edge-case** [low] skills/p-review/SKILL.md:132-133: Writing minor-findings.md at repo root may overwrite an existing file; no collision guidance.
- **uncited-number** [low] resources/efficient-debug-loop-strategies.md:43: 60% compact threshold and ~80% auto-compact attributed only to unnamed practitioners.
- **uncited-number** [low] resources/efficient-debug-loop-strategies.md:46: Lost-in-the-middle 30+ point accuracy drop has no source named.
- **uncited-number** [low] resources/efficient-debug-loop-strategies.md:79: 2026 re-evaluation with 4.6-6.1% rates and 127 identical fake names has no author or venue.
- **uncited-number** [low] resources/good-adversarial-review.md:56: Bug-bounty figures (405 of ~800, 339 participants, 300,000 interactions, 8 levels) have no source link.
- **uncited-number** [low] skills/debug-loop/SKILL.md:246: Run flaky check five times: threshold given without justification.
- **uncited-number** [low] skills/debug-loop/references/tactics.md:63: The 8-consecutive-blocks Stop hook limit is stated without source.
- **uncited-number** [low] skills/debug-loop/references/tactics.md:81: 3x subagent token cost has no citation.
- **uncited-number** [low] skills/debug-loop/references/tactics.md:100: 60% compaction threshold and reliability claim unsupported.
- **unsupported-claim** [low] resources/efficient-debug-loop-strategies.md:61: Stop hook override after 8 consecutive blocks stated without source.
- **unsupported-claim** [low] resources/good-adversarial-review.md:53: 'One 2026 methodological paper warns' about ASR validity is unnamed and uncited.
- **unsupported-claim** [low] resources/good-adversarial-review.md:61: 'Most processes remain limited to English' attributed to no source.
- **unsupported-claim** [low] resources/good-adversarial-review.md:45: OWASP Top 10 for Agentic Applications dated 2026 with no citation; line 72 calls it 'ASI Top 10'.
- **unsupported-claim** [low] skills/adversarial-review-2/SKILL.md:26-28: Literature sources named but not cited; 'converges on one lesson' is asserted without references.
- **unsupported-claim** [low] skills/adversarial-review-2/SKILL.md:59-60: 'the literature's most-cited failure mode' has no source.
- **unsupported-claim** [low] skills/adversarial-review-2/SKILL.md:214: Example finding described as 'verbatim' from a run; no run or artifact is provided.
- **unsupported-claim** [low] skills/debug-loop/SKILL.md:247: Claim about /rewind checkpoint behavior stated without citation; product behavior may differ.
- **unsupported-claim** [low] skills/debug-loop/SKILL.md:252: references/tactics.md referenced four times but not in this chunk; sections may not exist.
- **unsupported-claim** [low] skills/debug-loop/SKILL.md:28: Assertion that accumulated dead ends bias re-trying ruled-out fixes given without evidence.
- **unsupported-claim** [low] skills/debug-loop/references/tactics.md:108: "Claude ignores a bloated file wholesale" asserted without evidence.
- **unsupported-claim** [low] skills/p-review/SKILL.md:37-38: Asserts craft-vs-fit review is weaker without evidence; stylistic, low stakes.

## Least confident

- chunk-01: I could not check any of the quoted Anthropic docs, Chroma, or USENIX figures; the playbook's many quotations are unsourced within the chunk.
- chunk-02: I could not check the many specific numbers and dates (Crescendo percentages, Constitutional Classifiers stats, the January 9, 2026 release) against their primary sources.
- chunk-03: Whether the referenced red-teaming literature (NIST, OWASP, Microsoft retrospective) actually supports the five-discipline framing, since the chunk provides no citations.
- chunk-04: Whether the adversarial-review-2 SKILL.md exists and whether the eval runner resolves the relative files paths, since neither appears in this chunk.
- chunk-05: Whether references/tactics.md exists with the named sections and whether the diagnose skill supersession interacts correctly with skill triggering.
- chunk-06: I cannot check whether the schema (query/should_trigger) matches what the eval runner expects, or whether the file parses.
- chunk-07: Whether the BOM byte in sales-2026-08.csv survives git and the diff rendering intact, since the chunk shows only the visible character at line 134.
- chunk-08: Whether the pricing rounding failure and session tie-break are intentional planted bugs for the debug-loop evals or accidental; the chunk gives no eval metadata.
- chunk-09: I cannot check whether the Stop-hook override after 8 blocks and the 3x subagent cost figure match current Claude Code behavior.
- chunk-10: I cannot verify that the referenced sibling skills (debate-review, adversarial-review, adversarial-review-2) exist or that git symbolic-ref fallback behaves as described.

_10 chunks, 60 claims (40 verified, 18 unverified, 2 contradicted), 33 risks._
