# Diff brief: 5e3c12b~3..HEAD (4 commits, 243 files, +10231 / -2)

Range: `8a56953` adversarial review skills → `1e058fa` debug-loop skill → `5e3c12b` debug-loop style/grading → `e9a0b2d` brief-artifact plan. Almost pure additions; only 2 lines deleted in the whole range.

## TL;DR

- Three new skills: `skills/debug-loop`, `skills/adversarial-review-2`, `skills/p-review`. Plus a one-line scope tweak to `skills/adversarial-review/SKILL.md`.
- Two new research docs in `resources/` (~200 lines) that the skills are derived from.
- One design doc: `docs/plans/brief-artifact-plan.md` (the plan for a fourth, not-yet-built skill).
- Everything else (~200 of 243 files, ~4300+ lines) is eval workspace output: benchmark results, grading JSON, metrics, timing, transcripts, and copied fixture projects under `skills/debug-loop-workspace/` and `skills/adversarial-review-2-workspace/`. Generated artifacts, not hand-written; safe to skim or ignore.

## What matters (hand-written, ~1000 lines)

| Path | Size | What it is |
|---|---|---|
| `skills/debug-loop/SKILL.md` | 254 | Debug Brief + verification-gated loop: reproduce, commit failing test, rank hypotheses, instrument, one change per run, prove fix, reset when stalled. Fast path for trivial bugs. Declares it supersedes `diagnose`. |
| `skills/debug-loop/references/tactics.md` | 108 | git bisect, building a check when none exists, hook-based gates, subagent delegation. |
| `skills/debug-loop/evals/` | ~200 + fixtures | 5 small Python fixtures (csv-report, expired-sessions, pricing-regression, slow-enrichment, slug-typo) each with tests; `evals.json`, `eval_queries.json`. |
| `skills/adversarial-review-2/SKILL.md` + evals | ~200 | Red-team review: charter → 3 parallel fresh-eyes adversaries → severity grading → report → retest. Two eval fixtures (oncall plan, session cache design). |
| `skills/p-review/SKILL.md` | 130 | Lightweight single-reviewer pass, findings ranked /10 into Concerns / noted / Minor. Positioned as cheaper alternative to debate-review and adversarial-review*. |
| `skills/adversarial-review/SKILL.md` | 2-line edit | Description now routes severity-graded / retest requests to adversarial-review-2. |
| `skills/debug-loop-workspace/grade.py` | script | Mechanical grader for debug-loop evals (checks patched source, tests, git history, response text). |
| `resources/good-adversarial-review.md`, `resources/efficient-debug-loop-strategies.md` | ~200 | Research summaries (NIST/OWASP/MITRE red-teaming; agentic debug-loop practices) that the skills implement. |
| `docs/plans/brief-artifact-plan.md` | 64 | Plan for a `brief-artifact` skill: chunker + renderer scripts, subagent per chunk, layered brief output. Not implemented in this range. |

## Benchmark results recorded in the workspace files

- debug-loop (iteration 2, 4 evals x 3 runs): pass rate 100% with skill vs 70% without; +44s time, +11k tokens.
- adversarial-review-2 (iteration 2, 2 evals x 1 run): 100% vs 67%; +84s, +27k tokens. Iteration 1 with-skill runs took ~1190s each.

## Risk / review notes

- No existing behavior changes except the `adversarial-review` description wording; nothing in this range is executed by users outside skill invocation.
- Overlap: `debug-loop` claims to supersede `diagnose`; `p-review`, `adversarial-review`, `adversarial-review-2`, `debate-review` now form four review skills with descriptions that cross-reference each other. Trigger confusion is the main risk.
- Workspace dirs commit `outputs/project` entries (1-line each) that look like submodule/gitlink pointers to copied fixtures; current working tree shows several as modified (`m`), which suggests they are nested repos and may not round-trip cleanly on clone.
- `debug-loop` benchmark.md files have `**Model**: <model-name>` unfilled.
