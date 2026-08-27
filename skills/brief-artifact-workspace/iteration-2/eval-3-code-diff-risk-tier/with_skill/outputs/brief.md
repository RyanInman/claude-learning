# Brief: diff 5e3c12b~3

## TL;DR
- The diff is additive: it introduces three new skills (debug-loop with a tactics reference and five bug fixtures, adversarial-review-2 with two red-team evals, p-review as a cheap single-reviewer pass), two research notes (efficient-debug-loop-strategies, good-adversarial-review), and a plan doc for brief-artifact. The only edit to an existing file is a one-line routing note in skills/adversarial-review/SKILL.md sending severity-graded reviews to adversarial-review-2.
- The three "high" risk chunks are eval fixtures, not production code: each carries a planted bug (BOM header vs encoding="utf-8" in csv-report, max-by-created_at tie in expired-sessions, banker's rounding on 1.995 in pricing-regression, O(n*m) list scan in slow-enrichment, .stip() typo in slug-typo). Treat them as intentional.
- One internal contradiction in resources/efficient-debug-loop-strategies.md: L140 orders extended-thinking budgets think < think hard < think harder < ultrathink, while L193 cites Willison mapping think harder and ultrathink to the same 31,999.
- Most prose claims are unverified numbers and citations (NIST/OWASP/Microsoft, 19.7% hallucinated packages, 8-block Stop hook override, 3x subagent token cost); the research notes admit some figures come from vendor blogs. Cross-chunk references (tactics.md sections, fixture dirs, adversarial-review-2) all resolve within the diff.

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

This diff adds three new eval files for a new skill, adversarial-review-2, and edits the description of the existing adversarial-review skill. evals.json defines two evals: a red-team of a Redis session-cache design for a checkout service, and a red-team of a follow-the-sun on-call rotation plan. Each eval lists a prompt, an expected output, and a checklist of expectations (severity grades, strict rank order, concrete failure scenarios, planted flaws caught, falsifiable retest checks, a verdict plus minimum-changes list). The two fixture markdown files contain the planted flaws. The SKILL.md edit shortens one phrase and adds a routing rule: send severity-graded findings or retest loops to adversarial-review-2.

### chunk-07 [high] skills/debug-loop/evals/evals.json:1+, skills/debug-loop/evals/fixtures/csv-report/data/sales-2026-08.csv:1+, skills/debug-loop/evals/fixtures/csv-report/report.py:1+, skills/debug-loop/evals/fixtures/csv-report/tests/data/clean.csv:1+, skills/debug-loop/evals/fixtures/csv-report/tests/data/header_only.csv:1+, skills/debug-loop/evals/fixtures/csv-report/tests/test_report.py:1+ (diff)

This chunk adds new eval files for the debug-loop skill. evals.json defines five evals (vague login failure, pasted traceback, red tests after merge, trivial typo fast path, perf regression), each with a fixture path, a prompt, and five graded expectations. It then adds the csv-report fixture: a sales CSV whose header starts with a UTF-8 BOM, a report.py that opens files with encoding="utf-8" and sums amounts by region via csv.DictReader, two clean test CSVs (one header-only), and a two-test pytest file asserting totals on the clean file and an empty dict on the header-only file. The fixture is built so the suite is green while the BOM file crashes with KeyError: 'region'.

### chunk-08 [high] skills/debug-loop/evals/fixtures/expired-sessions/sessions.py:1+, skills/debug-loop/evals/fixtures/expired-sessions/tests/test_sessions.py:1+, skills/debug-loop/evals/fixtures/pricing-regression/pricing.py:1+, skills/debug-loop/evals/fixtures/pricing-regression/tests/test_pricing.py:1+, skills/debug-loop/evals/fixtures/slow-enrichment/enrich.py:1+, skills/debug-loop/evals/fixtures/slow-enrichment/run_nightly.py:1+, skills/debug-loop/evals/fixtures/slow-enrichment/tests/test_enrich.py:1+ (diff)

Adds three new eval fixtures for the debug-loop skill, each a small Python module plus pytest tests. expired-sessions: an append-only in-memory session store where get_session picks the newest row by created_at and refresh returns 404/401/200. pricing-regression: line_total rounds unit_price*qty*(1-discount) to cents; order_total sums rounded lines. slow-enrichment: enrich_orders does a linear scan over a copied customer list per order (O(n*m)); run_nightly.py drives it with 20000 orders and 20000 customers and prints elapsed time. Each fixture appears designed to carry a planted bug or performance flaw for the eval to diagnose. Tests insert the parent dir on sys.path and import the module directly.

### chunk-01 [low] docs/plans/brief-artifact-plan.md:1+, resources/efficient-debug-loop-strategies.md:1+ (diff)

This diff adds two new markdown files. The first, docs/plans/brief-artifact-plan.md, is an implementation plan for a `brief-artifact` skill that chunks a prose doc, code tree, or git diff, has readers write per-chunk JSON (summary, anchored claims with verified/unverified/contradicted status, typed risks, least-confident line), and renders a layered brief with TL;DR, structure map, claims table, and ranked risks. It lists scripts, references, workflow steps, triggers, and six verifiable implementation steps. The second, resources/efficient-debug-loop-strategies.md, is a research playbook on debugging with Claude Code: verification-gated loops, context management (/clear after two failed corrections, compact at ~60%), subagents, hooks, git bisect, a failure-mode table, staged recommendations, and caveats about secondary-sourced numbers.

### chunk-02 [low] resources/good-adversarial-review.md:1+ (diff)

This diff adds a new 78-line markdown document, resources/good-adversarial-review.md, a research brief on what makes a good adversarial review (red team) of AI chatbots. It argues that quality comes from discipline rather than clever jailbreaks: explicit impact-first threat model, diverse and partly independent testers, taxonomy-anchored reproducible methodology, manual plus automated probing, end-to-end system coverage, severity grading, and a closed remediate-retest loop. It cites NIST, OWASP, MITRE ATLAS, Microsoft, OpenAI, Anthropic, DeepMind, and academic papers, lists pitfalls of weak reviews, gives a four-stage recommendation process, and closes with caveats about field immaturity, metric fragility, imperfect independence, and vendor-sourced figures.

### chunk-03 [low] skills/adversarial-review-2/SKILL.md:1+ (diff)

This chunk adds a new skill file, adversarial-review-2/SKILL.md. The skill defines a five-stage red-team review: intake and an overkill check, a one-page charter naming ranked harm categories, three parallel fresh-eyes adversary subagents each assigned one lens from the charter and given only the artifact and charter, a verify-dedupe-seam-sweep-grade pass by the main agent with an outcome-based Critical/High/Medium/Low rubric and strict total ranking, a fixed-format report written to adversarial-review-2/report.md, and a retest stage that reruns each confirmed finding's failing scenario after fixes. It justifies the design by citing red-teaming literature (NIST, OWASP, Microsoft), lists gotchas, and closes with one example finding from a queue-migration review.

### chunk-05 [low] skills/debug-loop/SKILL.md:1+ (diff)

Adds a new 254-line skills/debug-loop/SKILL.md. Frontmatter declares the skill, its trigger phrases, and states it supersedes the diagnose skill. The body prescribes a debugging procedure: Step 0 gathers symptom, repro, check, and scope; Step 1 emits a fixed Debug Brief template with 2-4 ranked hypotheses; Step 1a is a fast path for small bugs meeting three conditions; Step 2 reproduces and commits a failing test before any fix; Step 3 instruments (profiler for latency, subagent for wide search); Step 4 makes one change and runs the check; Step 5 verifies via full check, revert, and conditional subagent review; Step 6 hands off with a template after two failed fixes. Ends with a worked example, gotchas, and pointers to references/tactics.md.

### chunk-06 [low] skills/debug-loop/evals/eval_queries.json:1+ (diff)

New file adds a JSON array of 20 trigger-eval queries for the debug-loop skill. Each entry pairs a natural-language user request with a should_trigger boolean. Eleven positives cover build failures, red tests, pasted tracebacks, regressions, CI failures, a trivial typo, a restart after failed fixes, intermittent login bounces, a latency regression, and a nightly queue backup. Nine negatives cover feature work, PR review, refactoring, TDD, error-handling cleanup, code walkthroughs, lint noise, brainstorming, and theory questions. No harness or scoring logic appears in the chunk; the file is data only.

### chunk-09 [low] skills/debug-loop/evals/fixtures/slug-typo/slug.py:1+, skills/debug-loop/evals/fixtures/slug-typo/tests/test_slug.py:1+, skills/debug-loop/references/tactics.md:1+ (diff)

Three new files. slug.py adds a slugify() that lowercases, strips, replaces non-alphanumerics with dashes, and trims dashes, but calls .stip() instead of .strip(), a deliberate typo fixture named slug-typo. test_slug.py adds three tests (basic, whitespace trim, punctuation collapse) that all hit the typo and raise AttributeError. tactics.md is a prose reference for a debug-loop skill: git bisect for regressions, building a check when none exists (test, repro script, exit-code command, timed threshold), PostToolUse/Stop hooks as gates, delegating disposable investigation to subagents, detecting fixes that overfit tests, and context hygiene (compact at 60%, /clear between bugs, handoff block, lean CLAUDE.md).

### chunk-10 [low] skills/p-review/SKILL.md:1+ (diff)

This chunk adds a new skill file, skills/p-review/SKILL.md (130 lines). It defines a fast single-reviewer adversarial review of a plan, spec, or diff. The conductor first establishes three facts (artifact, baseline ref for diffs, intent), then dispatches one fresh subagent with a verbatim reviewer brief, rules on its findings (rejecting only false premises), and presents them as Concerns, Noted-not-recommended, Rejected, and a Minor list written to minor-findings.md. An --inline flag skips the subagent and the Ruling step. The baseline is resolved via git merge-base against the upstream, falling back to origin/HEAD, then asking the user. The description frontmatter positions it as the cheap alternative to debate-review and adversarial-review skills.

## Claims

| status | claim | anchor |
|---|---|---|
| contradicted | Extended-thinking budgets: blog implies think < think hard < think harder < ultrathink, but Willison's decompilation maps think harder and ultrathink both to 31,999. | resources/efficient-debug-loop-strategies.md:140 vs resources/efficient-debug-loop-strategies.md:193 |
| unverified | resources/human-level-ai-review.md argues comprehension is the bottleneck and recommends layered summaries, ~200 LOC chunks, risk tiering, and claim extraction. | docs/plans/brief-artifact-plan.md:11 |
| unverified | No existing skill in skills/ performs layered briefing; closest is session-review. | docs/plans/brief-artifact-plan.md:11 |
| unverified | Chroma's Context Rot report (July 14, 2025) evaluated 18 frontier models and found performance grows unreliable as input length grows. | resources/efficient-debug-loop-strategies.md:91 |
| unverified | Spracklen et al. USENIX Security 2025 found 19.7% of recommended packages across 576,000 samples from 16 LLMs were hallucinated. | resources/efficient-debug-loop-strategies.md:156 |
| unverified | Feffer et al. (AIES 2024) found red-teaming purposes are often vague and that unstructured red teaming verges on security theater. | resources/good-adversarial-review.md:25 |
| unverified | NIST AI 600-1 defines 12 GenAI risk categories and places red teaming under Measure as a recurring activity. | resources/good-adversarial-review.md:27 |
| unverified | OpenAI's external red teaming paper is arXiv 2503.16431 by Ahmad, Agarwal, Lampe, Mishkin (2025) and lists four campaign design steps. | resources/good-adversarial-review.md:32 |
| unverified | Crescendomation achieves 29-61% higher performance on GPT-4 and 49-71% on Gemini-Pro on the AdvBench subset, with 98% binary success on GPT-4 (arXiv:2404.01833). | resources/good-adversarial-review.md:44 |
| unverified | Constitutional Classifiers cut jailbreak success from 86% to 4.4% on 10,000 synthetic prompts at 23.7% compute increase and 0.38% refusal rise; Classifiers++ released January 9, 2026 at ~1% additional compute. | resources/good-adversarial-review.md:50 |
| unverified | Bug bounty invited 405 participants from ~800 applicants; February 2025 public challenge drew 339 participants and over 300,000 interactions across 8 CBRN difficulty levels. | resources/good-adversarial-review.md:50 |
| unverified | Published red-teaming literature (NIST, OWASP, Microsoft 100-product retrospective) converges on discipline over cleverness and on the five listed properties. | skills/adversarial-review-2/SKILL.md:26-30 |
| unverified | Attacking without a threat model is the literature's most-cited failure mode; a review without retest is the literature's most common weak-review pattern. | skills/adversarial-review-2/SKILL.md:59-60 vs 201-202 |
| unverified | The example finding is a verbatim excerpt from a real run's report. | skills/adversarial-review-2/SKILL.md:214 |
| unverified | Eval file paths are relative ('evals/files/...') and resolve against the skill directory. | evals.json:16 |
| unverified | Skill supersedes the diagnose skill; when both match, run debug-loop only. | skills/debug-loop/SKILL.md:18 |
| unverified | references/tactics.md contains sections 'Building a check when none exists', 'Locating a regression with git bisect', and 'Catching a fix that overfits the test'. | skills/debug-loop/SKILL.md:52-55 |
| unverified | /rewind checkpoints track only file-editing-tool edits, not shell-command changes. | skills/debug-loop/SKILL.md:247 |
| unverified | Fixtures referenced by evals 0, 2, 3, 4 (expired-sessions, pricing-regression, slug-typo, slow-enrichment) exist. | skills/debug-loop/evals/evals.json:13 |
| unverified | test_half_cent_rounds_up expects line_total(0.70,3,5) == 2.00, but round() uses banker's rounding on a float near 1.995, so this test likely fails (intended regression). | tests/test_pricing.py:126-128 |
| unverified | Claude Code overrides a Stop hook after 8 consecutive blocks. | tactics.md:63-64 |
| unverified | A subagent run costs about three times the tokens of the same work inline. | tactics.md:81-82 |
| unverified | If the fix commit also modified the test, the fix overfits the test. | tactics.md:95-96 |
| unverified | The skill is distinct from debate-review, adversarial-review, and adversarial-review-2 as the cheap one-reviewer pass. | skills/p-review/SKILL.md:17-19 |
| verified | risk_tier is high only for code chunks touching auth, DB, IO, or dependency files; prose is always low. | docs/plans/brief-artifact-plan.md:40 |
| verified | Adversaries receive only the brief, artifact, and charter; conversation history is never pasted. | skills/adversarial-review-2/SKILL.md:80-82 |
| verified | Severity is graded from worst plausible outcome using the four-row rubric, then ranked in a strict total order with certainty weighing in. | skills/adversarial-review-2/SKILL.md:131-146 |
| verified | The report has exactly six sections: Verdict, Summary table, Findings, Killed findings, Verification items, Retest list. | skills/adversarial-review-2/SKILL.md:154-171 |
| verified | Eval 1 expects the report to flag KEYS-based invalidation blocking the shared Redis cluster; the fixture shows KEYS session:*:pricing then DEL on a shared cluster. | evals.json:21 and session-cache-design.md:106-107 |
| verified | Eval 1 expects sizing math 200k x 40KB = 8GB equal to free memory; fixture states ~40KB/session, ~200k sessions, 8GB free. | evals.json:22 and session-cache-design.md:110 |
| verified | Eval 2 expects a timezone gap: Krakow 08:00-20:00 CET = 02:00-14:00 ET, leaving 20:00-02:00 ET uncovered; fixture gives the two windows. | evals.json:41 and oncall-rotation-plan.md:68 |
| verified | Eval 2 expects the readiness risk (6-week-old team, no prod shipments, access in progress); fixture Notes state exactly this. | evals.json:42 and oncall-rotation-plan.md:78-79 |
| verified | adversarial-review SKILL.md now routes severity-graded findings or a retest loop to adversarial-review-2. | skills/adversarial-review/SKILL.md:128-129 |
| verified | Fast path applies only when all three conditions hold: error names file and line, line explains failure, fix touches one place. | skills/debug-loop/SKILL.md:95-99 |
| verified | Committing the failing test before the fix overrides the usual commit-only-when-asked default. | skills/debug-loop/SKILL.md:119 |
| verified | Reset trigger fires after 2 failed fixes on the same issue. | skills/debug-loop/SKILL.md:80 |
| verified | File is new (created from /dev/null) with 82 added lines. | skills/debug-loop/evals/eval_queries.json:1 |
| verified | Array holds 20 entries, each with exactly the keys query and should_trigger. | skills/debug-loop/evals/eval_queries.json:7 |
| verified | 11 entries set should_trigger true, 9 set false. | skills/debug-loop/evals/eval_queries.json:8 |
| verified | A trivial typo fix is expected to trigger the skill (positive case). | skills/debug-loop/evals/eval_queries.json:33 |
| verified | A 'broken by design' walkthrough request is expected not to trigger despite the word 'broken'. | skills/debug-loop/evals/eval_queries.json:73 |
| verified | The traceback query embeds escaped newlines and quotes and is valid JSON. | skills/debug-loop/evals/eval_queries.json:25 |
| verified | evals.json defines five evals with ids 0 through 4, each carrying five expectations. | skills/debug-loop/evals/evals.json:7-126 |
| verified | The sales-2026-08.csv fixture header begins with a UTF-8 BOM before 'region'. | skills/debug-loop/evals/fixtures/csv-report/data/sales-2026-08.csv:1 |
| verified | report.py opens files with encoding="utf-8" (not utf-8-sig), so the BOM stays in the first header key and row["region"] raises KeyError. | skills/debug-loop/evals/fixtures/csv-report/report.py:5-12 |
| verified | test_report.py only exercises clean.csv and header_only.csv, so the suite passes despite the BOM bug, matching the prompt's 'test suite is green' claim. | skills/debug-loop/evals/fixtures/csv-report/tests/test_report.py:9-15 |
| verified | The eval 1 prompt traceback lines (report.py line 20 and line 12) match the added report.py source line numbers. | skills/debug-loop/evals/evals.json:37 |
| verified | get_session returns the row with the max created_at, not the max version, despite the docstring saying created_at has one-second resolution (ties between refresh rows are unresolved). | sessions.py:37 vs sessions.py:9-11 |
| verified | refresh returns 401 when expires_at <= now, 404 when no row exists, else 200 with the token. | sessions.py:43-47 |
| verified | enrich_orders performs a nested linear scan over the customer list for every order. | enrich.py:154-161 |
| verified | run_nightly builds 20000 customers and 20000 orders and prints row count and elapsed seconds. | run_nightly.py:177-198 |
| verified | test_refreshed_session_uses_new_row expects the version-2 row with later created_at to win. | tests/test_sessions.py:80-85 |
| verified | slugify calls text.lower().stip(), a misspelling of strip(); every call raises AttributeError. | slug.py:7 |
| verified | The three tests import slugify via sys.path insertion of the parent dir and assert hello-world, release-notes, v2-0-final. | tests/test_slug.py:3-17 |
| verified | Bisect finds the culprit in about 10 steps across 1,000 commits. | tactics.md:19 |
| verified | The skill always dispatches a fresh subagent as Reviewer unless --inline is passed. | skills/p-review/SKILL.md:40-47 |
| verified | Baseline resolution: `git merge-base HEAD @{u}`, fallback to origin/HEAD via symbolic-ref, then ask the user. | skills/p-review/SKILL.md:32-36 |
| verified | Reviewer reads the change with `git diff {BASELINE}...HEAD` plus untracked files. | skills/p-review/SKILL.md:64-65 |
| verified | Ruling may reject a finding only when it rests on a false premise; all other findings are kept. | skills/p-review/SKILL.md:118-120 |
| verified | Minor findings are written verbatim to minor-findings.md beside the artifact (or repo root), never printed to the user. | skills/p-review/SKILL.md:132-136 |

## Risks

- **duplicate-logic** [high] enrich.py:146: index_customers returns a list copy, not a dict index; name implies indexing but scan is O(n*m). Likely the planted perf flaw.
- **missing-edge-case** [high] evals.json:41: CET-to-ET offset is 6 hours only outside DST-drift weeks; the expectation hardcodes 02:00-14:00 ET, which a correct report using CEST/EDT could phrase differently.
- **missing-edge-case** [high] skills/debug-loop/evals/fixtures/csv-report/tests/test_report.py:9-11: Tests compare floats with exact equality; passes for these values but brittle if fixture amounts change.
- **missing-edge-case** [high] skills/debug-loop/evals/evals.json:46: Expectation text names the BOM cause; grader must confirm the fixture's BOM survives git/editor checkouts, otherwise the eval cannot reproduce.
- **missing-edge-case** [high] sessions.py:37: Two rows with equal created_at (one-second resolution) are ordered by max() insertion tie-break, not by version; stale row can win. Likely the planted bug.
- **missing-edge-case** [high] pricing.py:95: round() on binary float 1.995 does not reliably round half up; test at test_pricing.py:128 may fail. Likely the planted regression.
- **unsupported-claim** [high] evals.json:14: Expected output asserts the stale-price window is a planted flaw, but the fixture only implies it via the 30-minute TTL; graders may disagree on what counts as catching it.
- **unsupported-claim** [high] skills/adversarial-review/SKILL.md:129: Description references adversarial-review-2 but the chunk does not show that skill's SKILL.md exists.
- **missing-edge-case** [low] skills/debug-loop/evals/eval_queries.json:77: Lint failures marked non-triggering; if the linter blocks CI this overlaps with the positive CI-failure case at line 29, so the boundary is judgment-based and may flake.
- **missing-edge-case** [low] skills/debug-loop/evals/eval_queries.json:73: Negative case relies on subtle intent ('before I touch it'); a classifier keyed on 'broken' will likely misfire.
- **missing-edge-case** [low] slug.py:7: Intentional typo fixture; if it is meant as a working fixture the .stip() call breaks all tests. Also no handling of non-str input, likely fine for a fixture.
- **missing-edge-case** [low] skills/p-review/SKILL.md:64: `git diff {BASELINE}...HEAD` ignores uncommitted working-tree changes; the brief mentions untracked files but not modified-unstaged or staged edits, which a 'review my changes' request often includes.
- **missing-edge-case** [low] skills/p-review/SKILL.md:132-134: Writing minor-findings.md into the repo root or beside the artifact can overwrite a prior run's file or land in a tracked directory with no mention of overwrite or cleanup.
- **uncited-number** [low] resources/efficient-debug-loop-strategies.md:123: 'accuracy can drop 30+ points' for lost-in-the-middle has no named source.
- **uncited-number** [low] resources/efficient-debug-loop-strategies.md:120: 60% compact threshold and ~80% auto-compact threshold attributed only to unnamed 'practitioners'.
- **uncited-number** [low] resources/efficient-debug-loop-strategies.md:156: '2026 re-evaluation' giving 4.6-6.1% rates and 127 identical fake names names no author or venue.
- **uncited-number** [low] resources/good-adversarial-review.md:50: Dense cluster of specific figures (405/800, 339, 300,000, 86%, 4.4%, 23.7%, 0.38%, ~1%) with no per-figure citation; the Caveats section admits some figures come from vendor blogs.
- **uncited-number** [low] skills/adversarial-review-2/SKILL.md:233: Example fix specifies 'publish-success-ratio >= 99.99% over 24h' with no basis stated.
- **uncited-number** [low] skills/debug-loop/SKILL.md:246: 'Run a flaky check five times' is a bare number with no rationale.
- **uncited-number** [low] tactics.md:63-64: The 8-consecutive-blocks Stop hook override limit is stated without a source.
- **uncited-number** [low] tactics.md:81-82: The 3x token cost of subagents is stated without a source.
- **unsupported-claim** [low] docs/plans/brief-artifact-plan.md:67: Grader threshold 'brief <=1/5 source length' is asserted with no rationale; 'Decisions (approved in brainstorm)' cites no record of that approval.
- **unsupported-claim** [low] resources/good-adversarial-review.md:47: Claims about Intigriti outcome-based severity, an Anthropic CVSS-modeled jailbreak scoring framework, and an unnamed '2026 methodological paper' on ASR have no citations.
- **unsupported-claim** [low] resources/good-adversarial-review.md:39: OWASP Top 10 for Agentic Applications (2026) and its content are asserted without a source; Caveats flag 2026 items as needing reverification.
- **unsupported-claim** [low] resources/good-adversarial-review.md:36: Stanford HAI 'In-House Evaluation Is Not Enough' (2025) and UK AISI claims, including critics' views, lack citations.
- **unsupported-claim** [low] skills/adversarial-review-2/SKILL.md:26-28: Cites NIST, OWASP, and a Microsoft 100-product retrospective without document names or links; the specific five-property convergence is not sourced.
- **unsupported-claim** [low] skills/adversarial-review-2/SKILL.md:59-60: 'the literature's most-cited failure mode' is asserted with no citation.
- **unsupported-claim** [low] skills/adversarial-review-2/SKILL.md:214: Example labeled 'verbatim' from a run, but no run artifact is referenced; may be fabricated illustration.
- **unsupported-claim** [low] skills/debug-loop/SKILL.md:52-55: References sections of references/tactics.md that are not in this chunk; existence and names cannot be confirmed here.
- **unsupported-claim** [low] skills/debug-loop/SKILL.md:18: Supersession of diagnose relies on a description-level instruction; no mechanism in the chunk enforces that only one skill runs.
- **unsupported-claim** [low] skills/debug-loop/SKILL.md:247: Claim about /rewind checkpoint behavior is stated without a source.
- **unsupported-claim** [low] tactics.md:95-96: A fix commit that touches the test does not always mean overfitting (e.g. fixing a wrong assertion); stated as absolute.
- **unsupported-claim** [low] skills/p-review/SKILL.md:18: References sibling skills adversarial-review and adversarial-review-2 whose existence is not shown in this chunk.

## Least confident

- chunk-01: I could not check whether the quoted Anthropic docs passages (lines 87, 93, 116, 138) are verbatim or whether the plan's claim that no existing skill covers layered briefing is accurate.
- chunk-02: I could not check any of the cited statistics or 2026-dated items (Constitutional Classifiers++ release date, OWASP Agentic Top 10, the unnamed ASR methodology paper) against their sources.
- chunk-03: I cannot check whether the cited NIST/OWASP/Microsoft red-teaming sources exist or say what the chunk attributes to them, nor whether the example finding came from an actual run.
- chunk-04: Whether the evals.json schema (skill_name, evals, expectations) matches what the eval runner expects, since no runner or schema appears in the chunk.
- chunk-05: Whether references/tactics.md exists with the section titles cited, and whether the /rewind checkpoint claim is accurate, since neither is visible in this chunk.
- chunk-06: Whether the expected should_trigger labels match the skill's actual trigger description, since the SKILL.md is not in this chunk.
- chunk-07: Whether the other four fixture directories referenced in evals.json exist elsewhere in the diff, since only csv-report appears in this chunk.
- chunk-08: Whether the pricing test and sessions tie-case are intended to fail as fixture bugs, since the chunk does not include the eval prompts or expected outcomes.
- chunk-09: Whether the .stip() typo in slug.py is the intended fixture bug (the directory name slug-typo suggests yes) and whether the hook override count of 8 matches actual Claude Code behavior.
- chunk-10: I could not check whether the referenced sibling skills (debate-review, adversarial-review, adversarial-review-2) exist or whether the frontmatter description length is acceptable to the skill loader.

_10 chunks, 60 claims (36 verified, 23 unverified, 1 contradicted), 33 risks._
