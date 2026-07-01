# Skill Reviewer Strengthening — Design

**Date:** 2026-07-01 (revised same day after adversarial review)
**Target:** `skills/skill-reviewer/` (SKILL.md, references/best-practices.md, references/token-economics.md, scripts/audit.py)
**Approach:** Additive. Extend existing references and audit.py; minimal SKILL.md body edits. No restructuring. Review stays static-analysis-only (no live trigger simulation).

## Goal

Strengthen the skill-reviewer's review quality by folding in (a) gaps between the two source resource docs and the current skill, and (b) fresh mid-2026 research: official Anthropic model-migration guidance, the agentskills.io spec and authoring/eval pages, Claude Code skill-listing mechanics, SkillsBench findings, and skill-security research.

**Revision note:** every check and claim below was validated before implementation: proposed regexes were run against a 428-skill corpus (deduped local plugin cache, includes official Anthropic plugins) to measure false-positive rates, and every external claim was traced to a primary source. Two originally proposed checks were cut for 30%/79% false-positive rates; several citations were corrected. FP rates cited per check below.

## Design principles

- Resident layer (SKILL.md body) stays lean; new knowledge goes to references (loaded on demand) or audit.py (never loaded).
- All new audit.py checks use conservative severity — the reviewing agent re-triages. Exception: reasoning-extraction (check 10) is HIGH because it is a documented runtime refusal risk with an official audit mandate.
- Model-generation awareness is scoped to what Anthropic documents: body over-prescriptiveness degrades Fable 5 output, and reasoning-echo instructions trigger refusals. There is NO documented claim that newer models over-trigger on pushy descriptions — official skill-creator guidance still recommends "a little bit pushy" descriptions. Do not gut pushiness guidance.
- Every new check ships with a fixture test pair and a corpus false-positive gate (see Verification).

## 1. audit.py — new deterministic checks

1. **Claude Code frontmatter awareness.** Second allowlist of Claude Code-only fields — all 13 verified against official docs (code.claude.com/docs/en/skills.md): `when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `disallowed-tools`, `model`, `effort`, `context`, `agent`, `hooks`, `paths`, `shell`. Report as INFO ("Claude Code-only field — fails upload to claude.ai/API") instead of HIGH. Portable-spec keys ({name, description, license, compatibility, metadata, allowed-tools}) stay as-is.
2. **Listing-cap check** (replaces the earlier "first-sentence trigger" idea, which hit 79% of the corpus and rested on a truncation claim no doc makes). Combined `description` + `when_to_use` length > 1,536 chars → INFO, suggest `/doctor`. Grounded in the documented per-entry cap (configurable via `skillListingMaxDescChars`); overflow drops least-invoked skills' descriptions whole. Corpus FP: 0%.
3. **Menu anti-pattern.** Repeated-or option chains only: regex shape `\bor\b[^.\n]{2,40},\s*or\b` (case-insensitive) → LOW, suggest one default plus escape hatch. Corpus FP: 1.6%, hits plausibly genuine. Do NOT broaden to comma-list form (`X, Y, or Z`) — that variant hits 22% of the corpus (ordinary English enumeration). Body-only scan; references quote menu examples deliberately.
4. **Time-sensitive content (fossils).** Dates paired with before/after/until/deprecated phrasing → LOW. Corpus FP: 0.7%. Body-only scan (best-practices.md quotes a fossil example).
5. **Trigger-phrase density metric.** Count quoted phrases / "mentions X" / trigger-verb patterns in description → emitted via the new `metrics` channel (see check 12), NOT as a finding.
6. **Name-redundancy check.** Description heavily token-overlapping the name → LOW. The "WHEN without WHAT" half of the original idea is NOT deterministically checkable (14% of corpus legitimately opens with "Use..."); it moves to best-practices.md as a judgment criterion, optionally surfaced as an INFO metric ("description opens with trigger phrasing").
7. **`allowed-tools` breadth.** Broad Bash grants → INFO security note.
8. **Name matches parent directory** (spec requirement, confirmed: "Must match the parent directory name") → MED. Requires the companion SKILL.md workflow fix in §4 (pasted skills currently copy to `/tmp/rev/SKILL.md`, which would false-positive every pasted review).
9. **Body token estimate > 5,000** (estimate already computed) → MED. Wording: the spec says "< 5000 tokens *recommended*", not a hard limit — the finding message must say "recommended". Corpus hit rate: 5.8%.
10. **Show-your-thinking detection** → **HIGH** (promoted from MED). Verified: `reasoning_extraction` is a documented refusal category ("The request asks the model to reproduce its internal reasoning in the response text", platform.claude.com/docs/en/build-with-claude/refusals-and-fallback), causes elevated fallbacks to Opus 4.8, and the Fable 5 prompting guide explicitly instructs auditing skills for these instructions. Regex mirrors the doc's verbs — echo/transcribe/reproduce/explain *internal* reasoning as response text — not generic "explain your reasoning". Finding message cites the doc URL. Corpus FP: 0.2%.
11. **Shouting scan extended to description** → LOW (downgraded from MED; over-trigger framing dropped — unverified). Justification: official skill-creator guidance discourages ALL-CAPS rigid language; state rule + reason instead. Must exclude "Do NOT"/"DO NOT" — 2.8% of corpus (including skill-reviewer itself) uses it as the recommended negative-trigger pattern. With exclusion, corpus FP: 0.7%.
12. **Metrics channel + exit-code fix.** Add a `metrics` object (trigger-phrase density, description chars, combined listing chars, body tokens) to JSON output and the report header — INFO metrics need a home that isn't the findings list. Fix `main()` exit code to match the docstring: info-only findings return 0 (currently `return 1 if findings else 0` at audit.py:364 returns 1 for info-only; the design adds ~6 INFO-class outputs, so unfixed, nearly every audit would exit 1).
13. **Script security scan.** Env-var read combined with network call, URL parameter interpolation in scripts or SKILL.md → MED. Extended with concrete injection markers from the Snyk ToxicSkills taxonomy: base64 blobs, "ignore previous instructions" patterns, Unicode smuggling.

**Cut from the original design (empirically disproven):**
- ~~Second person in body~~ — 30% corpus FP, including 8 hits in skill-reviewer's own body; no official guidance against second-person bodies (third-person convention is description-only and already checked). Imperative-voice preference stays as a judgment note in best-practices.md.
- ~~First-sentence trigger check~~ — 79% corpus FP; flagged the canonical good example in best-practices.md §1 and skill-reviewer's own description; truncation rationale unsupported by any doc. Replaced by check 2.

## 2. references/best-practices.md — revisions and additions

- **§1 (description) — keep the pushiness guidance.** Official skill-creator still documents under-triggering and recommends "a little bit 'pushy'" descriptions; no Anthropic source documents an over-triggering reversal on newer models. Adjust only: imperative phrasing ("Use this skill when...") acceptable alongside third person; include conceptual synonyms and rephrasings (activation layer keyword-matches, not semantic); carve-out — trivial one-step tasks intentionally skip skills, so failure to trigger on "read this PDF" is not a description bug. Drop the planned "front-load trigger phrases in first sentence" advice (unsupported; contradicts §1's own WHAT-first example).
- **New § Eval-driven review — split into the two real specs** (the original draft conflated them):
  - *Trigger testing* (agentskills.io/skill-creation/optimizing-descriptions): ~20 queries in `eval_queries.json`, 8-10 should-trigger and 8-10 should-not (near-misses most valuable), 3 runs per query, 0.5 trigger-rate threshold.
  - *Output evals* (agentskills.io/skill-creation/evaluating-skills): `evals/evals.json`, start with 2-3 test cases, with-skill vs without-skill comparison; outgrowth detection (base model passes without the skill → recommend retiring — supported by SkillsBench finding that self-generated skills provide no benefit on average); regression detection on model updates.
  - Reviewer recommends this testing to the author — does not perform it.
- **New § Model-generation sensitivity** — scoped to documented claims, date-stamped "as of mid-2026", principle stated generation-independently ("newer models need less prescription; verify against the current migration guide") so it passes its own fossil check next generation. Contents: "Skills developed for prior models are often too prescriptive for Claude Fable 5 and can degrade output quality" (Fable 5 prompting guide, verbatim); reasoning-based instructions ("Do X because Y causes Z") over rigid directives (agentskills.io + skill-creator); flag echo/transcribe-internal-reasoning instructions (refusal risk, see check 10).
- **New § Claude Code invocation control.** When to recommend `disable-model-invocation: true` (side-effecting skills), `user-invocable: false` (background knowledge), scoped `allowed-tools`. Side-effecting skill without invocation control = real finding.
- **New § Security surface.** Concrete checks: env-var reads plus network calls in bundled scripts, URL parameter appending/exfiltration, angle brackets in frontmatter, broad tool grants, base64 blobs, "ignore previous instructions" strings. Context stat, corrected to what Snyk actually found (ToxicSkills, 3,984 skills scanned from ClawHub/skills.sh): 36.82% had at least one security flaw of any kind (hardcoded keys, insecure credential handling, third-party content exposure — not all prompt injection); 13.4% (534) had a critical-severity issue; 76 human-confirmed malicious payloads; 91% of confirmed-malicious skills combined prompt injection with conventional malware.
- **§ One-job test strengthened with corrected SkillsBench citation** (arXiv:2602.12670): curated skills +16.6pp average pass rate; 2-3 skill modules +18.6pp vs +5.9pp for 4+; comprehensive skills score **-2.9pp — worse than no skill at all** (lead with this number); paper's own terms are "comprehensive/exhaustive bundles" (it never says "monolithic" — quote its terms).
- TOC updated; file stays one level deep.

## 3. references/token-economics.md — additions

All numbers verified verbatim against code.claude.com docs; cite doc URLs inline.

- **New § Listing-budget overflow.** Descriptions tax the shared listing budget (1% of context window, configurable via `skillListingBudgetFraction`) before any triggering; `when_to_use` counts toward the combined 1,536-char per-entry cap (configurable via `skillListingMaxDescChars`); overflow drops least-invoked skills' descriptions first; symptom is skills silently not triggering; `/doctor` diagnoses. Companion deterministic check: audit.py check 2.
- **New § Compaction behavior.** Invoked skill bodies re-injected capped at 5,000 tokens per skill, 25,000 tokens total, oldest dropped first (code.claude.com/docs/en/context-window.md) — front-load the body; rules past ~5k tokens vanish after compaction. Review criterion: does the body front-load what matters?
- **§7 triage questions gains hooks row.** "Must this hold every time, no exceptions? → hook, not prose." Guarantee-shaped rules in a skill body are wishes; flag them.
- **Body limit note.** Spec recommends <5,000 tokens alongside the 500-line guideline (recommendation, not hard limit).
- TOC updated.

## 4. SKILL.md body — minimal edits

1. Step 1 workflow fix (required by audit check 8): pasted skills save to a folder named after the skill — `mkdir -p /tmp/rev/<skill-name>` — not `/tmp/rev/SKILL.md`, so the name-matches-directory check doesn't false-positive on every pasted review.
2. Step 3 reference-pointer bullets updated to name the new content areas so the reviewer knows when to read each file:
   - best-practices.md: "...anti-pattern catalog, eval-readiness, model-generation sensitivity, invocation control, and security surface."
   - token-economics.md: "...lost-in-the-middle, listing-budget overflow, and compaction front-loading."
3. New line in step 3: "Determine the skill's target platform first (Claude Code vs claude.ai/API upload) — frontmatter validity and several criteria differ; audit.py flags platform-specific fields as INFO."

Output format, confidence scoring, and scope sections unchanged.

## Out of scope

- Live trigger simulation during review (rejected — static analysis only).
- Restructuring references by review dimension.
- Reviewing CLAUDE.md/rules files (existing scope boundary stands).

## Verification

- **Fixture tests for every new check:** one fixture that must trip the check, one that must not, run by a small test script alongside audit.py. Regex checks with no tests are how 30%/79% FP-rate checks reach production; the corpus harness caught both pre-implementation and the fixtures prevent regression post-implementation.
- **Self-audit gate, precisely defined:** `python scripts/audit.py skills/skill-reviewer` emits nothing above INFO and (post exit-code fix) exits 0. "Runs clean" means this, not zero output.
- **Corpus false-positive gate:** sweep the local plugin cache (~430 deduped skills, already on disk, free) — each new check's hit rate stays within its measured budget above (menu ≤ ~2%, fossils ≤ ~1%, desc-shouting ≤ ~1%, show-thinking ≤ ~0.5%); a check that exceeds its budget is mis-specified, not the corpus.
- Run audit.py against 2-3 other skills in `skills/` — new checks produce sane findings, no crashes.
- Both reference files retain TOCs and stay under ~200 lines each.
- SKILL.md body stays under 150 lines.

## Sources (verified 2026-07-01)

- Claude Code skills + listing mechanics: code.claude.com/docs/en/skills.md
- Compaction re-injection caps: code.claude.com/docs/en/context-window.md
- Fable 5 prompting / migration: platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5
- Refusal categories (`reasoning_extraction`): platform.claude.com/docs/en/build-with-claude/refusals-and-fallback
- Agent Skills spec: agentskills.io/specification
- Trigger testing: agentskills.io/skill-creation/optimizing-descriptions
- Output evals: agentskills.io/skill-creation/evaluating-skills
- SkillsBench: arXiv:2602.12670
- Snyk ToxicSkills: snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/
