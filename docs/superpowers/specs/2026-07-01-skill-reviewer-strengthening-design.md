# Skill Reviewer Strengthening — Design

**Date:** 2026-07-01
**Target:** `skills/skill-reviewer/` (SKILL.md, references/best-practices.md, references/token-economics.md, scripts/audit.py)
**Approach:** Additive. Extend existing references and audit.py; minimal SKILL.md body edits. No restructuring. Review stays static-analysis-only (no live trigger simulation).

## Goal

Strengthen the skill-reviewer's review quality by folding in (a) gaps between the two source resource docs and the current skill, and (b) fresh mid-2026 research: official Anthropic model-migration guidance, the agentskills.io spec and authoring/eval pages, Claude Code skill-listing mechanics, SkillsBench findings, and skill-security research.

## Design principles

- Resident layer (SKILL.md body) stays lean; new knowledge goes to references (loaded on demand) or audit.py (never loaded).
- All new audit.py checks use conservative severity (INFO/LOW/MED) — the reviewing agent re-triages.
- Review criteria become model-generation-aware: guidance written for 2025-era under-triggering models is now an over-triggering risk on Opus 4.5+/Claude 5 family.

## 1. audit.py — new deterministic checks

1. **Claude Code frontmatter awareness.** Add a second allowlist of Claude Code-only fields (`when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `disallowed-tools`, `model`, `effort`, `context`, `agent`, `hooks`, `paths`, `shell`). Report these as INFO ("Claude Code-only field — fails upload to claude.ai/API") instead of HIGH. Spec-portable keys stay as-is.
2. **Menu anti-pattern.** Detect option chains ("or X, or Y, or Z" — 3+ alternatives in one clause) → LOW, suggest one default plus escape hatch.
3. **Time-sensitive content (fossils).** Dates paired with before/after/until/deprecated phrasing → LOW.
4. **Second person in body.** Extend existing description-only check to the body → LOW, suggest imperative voice.
5. **Trigger-phrase density.** Count quoted phrases / "mentions X" / trigger-verb patterns in description → INFO metric to ground the agent's judgment (not a finding).
6. **Description shape checks.** Description containing only trigger conditions with no capability statement (WHEN without WHAT — imperative "Use this skill when..." phrasing is fine as long as WHAT follows), or heavily redundant with the name → LOW.
7. **`allowed-tools` breadth.** Broad Bash grants → INFO security note.
8. **Name matches parent directory** (spec requirement) → MED.
9. **Body token estimate > 5,000** (spec formalized limit; estimate already computed) → MED.
10. **Shouting scan extended to description.** CRITICAL/MUST-style trigger language in the description → MED, framed as over-trigger risk on Opus 4.5+/Claude 5 models.
11. **Show-your-thinking detection.** Regex for "show your thinking / explain your reasoning / transcribe ... reasoning" instructions → MED (triggers `reasoning_extraction` refusals on Fable 5).
12. **Script security scan.** Env-var read combined with network call, URL parameter interpolation in scripts or SKILL.md → MED.
13. **First-sentence trigger check.** Trigger phrasing absent from the description's first sentence → INFO (listing truncation cuts the back half).

## 2. references/best-practices.md — revisions and additions

- **§1 (description) rewrite.** Replace "deliberately, almost embarrassingly pushy" with model-conditional guidance: moderately explicit trigger-context lists remain good; aggressive/shouting emphasis ("CRITICAL: You MUST use...") now causes over-triggering on Opus 4.5+/Claude 5. Add: imperative phrasing ("Use this skill when...") preferred over strict third person; include conceptual synonyms and rephrasings (activation layer keyword-matches, not semantic); front-load trigger phrases in the first sentence (truncation cuts the back half); carve-out — trivial one-step tasks intentionally skip skills, so failure to trigger on "read this PDF" is not a description bug.
- **New § Eval-driven review.** Official methodology: ~20 test queries including 8-10 near-miss should-NOT-trigger cases sharing keywords; 3 runs per query, per-query 0.5 threshold; `evals/evals.json` standard format; outgrowth detection (base model passes evals without the skill → recommend retiring); regression detection on model updates. Reviewer recommends this testing to the author — does not perform it.
- **New § Model-generation sensitivity.** Skills written for prior models are often too prescriptive for Fable 5 and can degrade output; reasoning-based instructions ("Do X because Y causes Z") over rigid directives; flag instructions telling the model to echo or explain internal reasoning (refusal risk).
- **New § Claude Code invocation control.** When to recommend `disable-model-invocation: true` (side-effecting skills), `user-invocable: false` (background knowledge), scoped `allowed-tools`. Side-effecting skill without invocation control = real finding.
- **New § Security surface.** Concrete checks: env-var reads plus network calls in bundled scripts, URL parameter appending/exfiltration, angle brackets in frontmatter (injection vector), broad tool grants. Context: 36% of tested public skills contained prompt injection (Snyk).
- **§ One-job test strengthened.** Nine-category taxonomy as diagnostic plus SkillsBench quantitative backing: focused skills (≤3 modules) outperform exhaustive bundles; monolithic skills measurably reduce performance.
- TOC updated; file stays one level deep.

## 3. references/token-economics.md — additions

- **New § Listing-budget overflow.** Descriptions tax the shared 1%-of-window listing budget before any triggering; `when_to_use` counts toward the combined 1,536-char per-entry cap (cap configurable via `skillListingMaxDescChars`); overflow drops least-invoked skills' descriptions first; symptom is skills silently not triggering; `/doctor` diagnoses.
- **New § Compaction behavior.** Re-attach keeps first 5,000 tokens per skill, 25,000 shared budget — front-load the body; rules past ~5k tokens vanish after compaction. Review criterion: does the body front-load what matters?
- **§7 triage questions gains hooks row.** "Must this hold every time, no exceptions? → hook, not prose." Guarantee-shaped rules in a skill body are wishes; flag them.
- **Body limit note.** Spec formalizes <5,000 tokens alongside 500 lines.
- TOC updated.

## 4. SKILL.md body — minimal edits

1. Step 3 reference-pointer bullets updated to name the new content areas so the reviewer knows when to read each file:
   - best-practices.md: "...anti-pattern catalog, eval-readiness, model-generation sensitivity, invocation control, and security surface."
   - token-economics.md: "...lost-in-the-middle, listing-budget overflow, and compaction front-loading."
2. New line in step 3: "Determine the skill's target platform first (Claude Code vs claude.ai/API upload) — frontmatter validity and several criteria differ; audit.py flags platform-specific fields as INFO."

Output format, confidence scoring, and scope sections unchanged.

## Out of scope

- Live trigger simulation during review (rejected — static analysis only).
- Restructuring references by review dimension.
- Reviewing CLAUDE.md/rules files (existing scope boundary stands).

## Verification

- `python scripts/audit.py skills/skill-reviewer` runs clean on the skill-reviewer itself (self-audit; new checks must not false-positive on their own skill).
- Run audit.py against 2-3 other skills in `skills/` — new checks produce sane findings, no crashes.
- Both reference files retain TOCs and stay under ~200 lines each.
- SKILL.md body stays under 150 lines.
