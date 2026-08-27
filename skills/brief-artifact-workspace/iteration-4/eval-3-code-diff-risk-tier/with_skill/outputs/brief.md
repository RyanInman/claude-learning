# Brief: diff 5e3c12b~3

## TL;DR
- The diff adds four new skills (adversarial-review-2, debug-loop, p-review, and a brief-artifact plan), two research notes, and planted-bug eval fixtures; it edits one existing file, adversarial-review/SKILL.md, to route severity-graded requests.
- Nothing runtime-facing changes: every added .py file is a debug-loop eval fixture with a deliberate bug (BOM header, .stip() typo, banker's rounding, O(n*m) scan, same-second session tie).
- Subagent token cost disagrees across files: tactics.md:82 says ~3x, efficient-debug-loop-strategies.md:67 says 15x and ~4x; neither cites a source.
- Highest reader-flagged risk: adversarial-review-2 overkill check says four subagents while Stage 2 spawns three; p-review overwrites minor-findings.md silently on rerun.
- The research notes carry many dated figures, arXiv ids, and percentages with no links; readers marked nearly all of them unverified.

## Structure map

| id | type | risk | size | anchor |
|---|---|---|---|---|
| chunk-01 | diff | low | 188 lines | docs/plans/brief-artifact-plan.md:1+ +1 more |
| chunk-02 | diff | low | 80 lines | resources/good-adversarial-review.md:1+ (diff) |
| chunk-03 | diff | low | 229 lines | skills/adversarial-review-2/SKILL.md:1+ (diff) |
| chunk-04 | diff | high | 110 lines | skills/adversarial-review-2/evals/evals.json:1+ +3 more |
| chunk-05 | diff | low | 255 lines | skills/debug-loop/SKILL.md:1+ (diff) |
| chunk-06 | diff | low | 83 lines | skills/debug-loop/evals/eval_queries.json:1+ (diff) |
| chunk-07 | diff | high | 171 lines | skills/debug-loop/evals/evals.json:1+ +5 more |
| chunk-08 | diff | high | 196 lines | skills/debug-loop/evals/fixtures/expired-sessions/sessions.py:1+ +6 more |
| chunk-09 | diff | low | 136 lines | skills/debug-loop/evals/fixtures/slug-typo/slug.py:1+ +2 more |
| chunk-10 | diff | low | 131 lines | skills/p-review/SKILL.md:1+ (diff) |

## Chunk summaries

- **chunk-04** [high] skills/adversarial-review-2/evals/evals.json:1+ +3 more: Diff adds two eval cases for a new adversarial-review-2 skill: a Redis session-cache design and a follow-the-sun on-call plan, each with planted flaws and graded expectations (severity ranking, failure scenarios, retest checks, verdicts).
- **chunk-07** [high] skills/debug-loop/evals/evals.json:1+ +5 more: Adds five eval cases for the debug-loop skill (vague login failure, pasted traceback, red tests after merge, trivial typo fast path, perf regression), each with a fixture path, prompt, and five expectations.
- **chunk-08** [high] skills/debug-loop/evals/fixtures/expired-sessions/sessions.py:1+ +6 more: Adds three planted-bug eval fixtures for the debug-loop skill, each a small Python module plus pytest tests.
- **chunk-01** [low] docs/plans/brief-artifact-plan.md:1+ +1 more: Diff adds two new markdown files.
- **chunk-02** [low] resources/good-adversarial-review.md:1+ (diff): Adds a new 78-line research note arguing that a good adversarial review of an AI chatbot rests on discipline, not clever jailbreaks: explicit impact-first threat model, diverse and partly independent testers, taxonomy-anchored reproducible methodology, manual plus automated probing, severity grading, and a closed remediate-retest loop.
- **chunk-03** [low] skills/adversarial-review-2/SKILL.md:1+ (diff): Adds a new SKILL.md, adversarial-review-2, a systematic red-team review skill.
- **chunk-05** [low] skills/debug-loop/SKILL.md:1+ (diff): Adds a new skill file skills/debug-loop/SKILL.md.
- **chunk-06** [low] skills/debug-loop/evals/eval_queries.json:1+ (diff): Adds a new file skills/debug-loop/evals/eval_queries.json: a JSON array of 20 trigger-eval entries for the debug-loop skill.
- **chunk-09** [low] skills/debug-loop/evals/fixtures/slug-typo/slug.py:1+ +2 more: Diff adds three new files.
- **chunk-10** [low] skills/p-review/SKILL.md:1+ (diff): Adds a new skill file skills/p-review/SKILL.md.

## Claims

| status | claim | anchor |
|---|---|---|
| contradicted | Plan caps chunk summary at 120 words, but this reader prompt schema says 80 words; schema documents may disagree. | docs/plans/brief-artifact-plan.md:40 vs docs/plans/brief-artifact-plan.md:37 |
| contradicted | line_total uses Python round(), which is banker's rounding on floats; test expects 1.995 to bill as 2.00. | skills/debug-loop/evals/fixtures/pricing-regression/pricing.py:3 vs skills/debug-loop/evals/fixtures/pricing-regression/tests/test_pricing.py:17-18 |
| contradicted | A subagent run costs about three times the tokens of the same work inline. | skills/debug-loop/references/tactics.md:82 vs resources/efficient-debug-loop-strategies.md:67 |
| unverified | No existing skill in `skills/` re-presents artifacts as layered briefs; closest is `session-review`. | docs/plans/brief-artifact-plan.md:5 |
| unverified | Chroma Context Rot report (July 14, 2025) evaluated 18 frontier models and found performance degrades with input length. | resources/efficient-debug-loop-strategies.md:15 |
| unverified | Spracklen et al. USENIX Security 2025 found 19.7% of recommended packages across 576,000 samples were hallucinated. | resources/efficient-debug-loop-strategies.md:85 |
| unverified | Extended-thinking budgets: 'think' ~4,000, 'think hard' ~10,000, 'ultrathink' 31,999, per Simon Willison decompilation. | resources/efficient-debug-loop-strategies.md:64 |
| unverified | Feffer et al. (AIES 2024) found red-teaming purpose is often vague and warned of security theater without structure. | resources/good-adversarial-review.md:26 |
| unverified | NIST AI 600-1 defines 12 GenAI risk categories and places red teaming under Measure as recurring. | resources/good-adversarial-review.md:28 |
| unverified | OpenAI external red teaming white paper is arXiv 2503.16431 (Ahmad, Agarwal, Lampe, Mishkin, 2025) with four design steps. | resources/good-adversarial-review.md:33 |
| unverified | Crescendomation achieves 29-61% higher performance on GPT-4, 49-71% on Gemini-Pro, 98% binary success (arXiv:2404.01833). | resources/good-adversarial-review.md:43 |
| unverified | Constitutional Classifiers cut jailbreak success 86% to 4.4% at 23.7% compute increase, 0.38% refusal rise. | resources/good-adversarial-review.md:49 |
| unverified | Constitutional Classifiers++ released January 9, 2026 at ~1% additional compute with no universal jailbreak found. | resources/good-adversarial-review.md:49 |
| unverified | Claims NIST, OWASP, and Microsoft's 100-product retrospective converge on discipline-over-cleverness with five elements. | skills/adversarial-review-2/SKILL.md:20-24 |
| unverified | Skill supersedes the diagnose skill; when both match, run debug-loop only. | skills/debug-loop/SKILL.md:12 |
| unverified | /rewind checkpoints track only file-editing-tool edits, not shell command changes. | skills/debug-loop/SKILL.md:239 |
| unverified | references/tactics.md contains sections on building a check, git bisect, and overfitting. | skills/debug-loop/SKILL.md:47 |
| unverified | Fixtures expired-sessions, pricing-regression, slug-typo, slow-enrichment are referenced but not present in this chunk. | skills/debug-loop/evals/evals.json:7 |
| unverified | Claude Code overrides a Stop hook after 8 consecutive blocks. | skills/debug-loop/references/tactics.md:63 |
| unverified | Description claims this pass is cheaper than debate-review and adversarial-review skills. | skills/p-review/SKILL.md:12 |

40 verified claims omitted to keep the brief short; see chunk JSON for the full list.

## Risks

- **duplicate-logic** [high] skills/debug-loop/evals/fixtures/slow-enrichment/enrich.py:4-6: index_customers only copies dicts; name implies index but builds none. Intentional planted slowness.
- **missing-edge-case** [high] skills/adversarial-review/SKILL.md:12: Description references adversarial-review-2 skill; its SKILL.md is not in this chunk, so existence unverified.
- **missing-edge-case** [high] skills/debug-loop/evals/fixtures/csv-report/report.py:13: float(row['amount']) has no guard for blank or malformed amounts; intentional for fixture but untested.
- **missing-edge-case** [high] skills/debug-loop/evals/fixtures/expired-sessions/sessions.py:31: Docstring promises version ordering; max by created_at ignores version on same-second refresh. Tests never cover tie.
- **missing-edge-case** [high] skills/debug-loop/evals/fixtures/pricing-regression/tests/test_pricing.py:17-18: Float 0.70*3*0.95 may not equal exactly 1.995; round() result depends on float repr, test may fail.
- **unsupported-claim** [high] skills/adversarial-review-2/evals/evals.json:35: CET-to-ET offset is 6 hours only outside DST mismatch weeks; eval hardcodes it.
- **unsupported-claim** [high] skills/adversarial-review-2/evals/evals.json:45: evals.json lacks trailing newline; may matter for tooling or linting.
- **unsupported-claim** [high] skills/debug-loop/evals/evals.json:7: Four of five fixture directories are referenced without their contents in this chunk; existence cannot be checked here.

24 risks in low-risk chunks omitted; see chunk JSON.

## Least confident

- chunk-01: I could not check whether any of the quoted Anthropic doc passages, the Chroma report, or the USENIX study exist or say what the playbook attributes to them.
- chunk-04: Whether the file paths in evals.json ("evals/files/...") resolve correctly relative to how the eval runner locates fixtures, since the runner is not in this chunk.
- chunk-07: I could not confirm the BOM byte is actually present in sales-2026-08.csv beyond the visible marker, nor that the other four fixture directories exist.
- chunk-08: Whether round(0.70*3*0.95, 2) actually yields 2.00 or 1.99 in CPython, which decides if the pricing test is the intended planted failure.
- chunk-09: Whether the .stip() typo is intentional fixture design (the directory is named slug-typo, suggesting yes) rather than an accidental bug.

_10 chunks, 60 claims (40 verified, 17 unverified, 3 contradicted), 32 risks. Budget 1500 words, compaction level 4._
