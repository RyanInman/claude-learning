# Claude Skill Best Practices — Review Criteria

Read this when writing up findings about triggering, structure, or anti-patterns.
Each item gives what to check, why it matters, and the shape of a good fix.

## Contents
- [1. The description (highest leverage)](#1-the-description-highest-leverage)
- [2. Folder structure & progressive disclosure](#2-folder-structure--progressive-disclosure)
- [3. Naming](#3-naming)
- [4. Instruction quality](#4-instruction-quality)
- [5. The anti-pattern catalog](#5-the-anti-pattern-catalog)
- [6. Scripts for agents](#6-scripts-for-agents)
- [7. Eval-driven review](#7-eval-driven-review)
- [8. Model-generation sensitivity](#8-model-generation-sensitivity)
- [9. Claude Code invocation control](#9-claude-code-invocation-control)
- [10. Security surface](#10-security-surface)
- [11. Quick scoring rubric](#11-quick-scoring-rubric)

---

## 1. The description (highest leverage)

The `description` is the only part of a skill (with the name) that is always in
context, and it alone decides whether the body ever loads. Claude's dominant
failure mode is **under-triggering** — not reaching for a skill that would help.
So a good description is deliberately, almost embarrassingly "pushy."

A strong description has all of:
- **Third person preferred, imperative acceptable.** "Reviews a SKILL.md and..."
  or "Use this skill when..." both work — skill-creator still documents
  under-triggering and recommends being "a little bit 'pushy'"; no Anthropic
  source documents an over-triggering reversal on newer models.
- **Both what AND when.** State what the skill does *and* the contexts/phrases
  that should fire it. All "when to use" info lives here, not in the body.
- **Concrete trigger phrases, including synonyms.** Quote real user phrasing —
  "use this whenever the user mentions dashboards, metrics, or company data,
  even if they don't say 'dashboard'" — plus conceptual synonyms/rephrasings:
  matching is keyword-based, not semantic. Vague descriptions never fire.
- **Negative triggers when domains overlap.** "Do NOT use for simple data
  exploration — use the data-viz skill instead." This is the single most
  effective fix for false-positive firing between sibling skills.

Carve-out: trivial one-step tasks skip skills intentionally — no trigger on
"read this PDF" isn't a description bug. Weak-opening test: an opening that
merely restates the name, or gives WHEN without WHAT, is weak. (Imperative
body text is fine — third person applies to the description, not the body.)
Limits: max 1024 chars, no angle brackets. Too short (under ~120 chars) almost
always under-triggers. A useful debugging move to suggest to the author: ask
Claude "When would you use the <skill> skill?" — it quotes the description back,
exposing missing keywords.

Fix shape: rewrite the description inline. Before: "Helps with PDFs." After:
"Extracts text and tables from PDF files and fills PDF forms. Use whenever the
user uploads a .pdf, mentions a PDF by name, or asks to read/merge/split/fill a
PDF. Do NOT use for creating Word or Excel files."

## 2. Folder structure & progressive disclosure

The architecture that makes skills cheap is three-tier loading: metadata always
in context, the SKILL.md body on trigger, and `references/`/`scripts/` only when
read or run. So:

- **Keep the body lean** (under ~500 lines; ~300 is where splitting starts to
  pay). Once triggered, the whole body stays in context for the session — every
  line competes with the live task. The body should read like a table of
  contents: overview, workflow, pointers.
- **Split by domain, not by chapter.** A finance query should never load the
  sales schema. Organize `references/finance.md`, `references/sales.md` so Claude
  reads only what the task needs.
- **Keep references one level deep.** SKILL.md → reference, not SKILL.md →
  reference → sub-reference. Deeply nested files get partially read (head
  previews) and yield incomplete information.
- **Add a TOC to any reference over ~100 lines** so the full scope is visible
  even on a partial read.
- **Three directories, three jobs:** `scripts/` = code Claude *runs* (not loaded
  into context); `references/` = docs Claude *reads* into context on demand;
  `assets/` = files used *in the output* (templates, boilerplate). Flag content
  filed under the wrong one.
- **`@imports` do not work in SKILL.md** (only in CLAUDE.md). An `@path` line in
  a skill loads nothing — replace with "Read references/x.md when...".
- **Forward slashes only** in bundled paths, even on Windows.
- **Every bundled file should be referenced** from SKILL.md. An unreferenced
  reference is one Claude never opens; an unmentioned script is one it never runs.

## 3. Naming

Gerund form is recommended (`processing-pdfs`, `reviewing-skills`). Noun phrases
(`pdf-processing`) and action forms (`process-pdfs`) are acceptable. Avoid vague
names (`helper`, `utils`, `tools`) and overly generic ones (`documents`, `data`).
Kebab-case, ≤64 chars, no "anthropic"/"claude". This is a low-impact finding on
its own — only raise it if the name is genuinely vague enough to hurt discovery.

## 4. Instruction quality

- **Imperative, third person, one consistent term.** "Extract the fields," not
  "you should pull out the boxes." Don't alternate extract/pull/get/retrieve.
- **Match freedom to fragility.** Many valid approaches → text guidance. A
  preferred pattern → pseudocode/parameters. Fragile, consistency-critical
  operation → an exact command ("Run exactly: `python scripts/migrate.py
  --verify`. Do not modify."). Over-constraining a flexible task ("railroading")
  fails when the skill meets varied inputs; under-constraining a fragile one
  breaks.
- **Examples beat rules.** One concrete input→output pair teaches more than 50
  lines of abstract description. If a skill has a fixed output format and no
  example, that's a real finding.
- **Templates with calibrated strictness.** "ALWAYS use this exact template" for
  strict formats; "sensible default, use judgment" for flexible ones.
- **Validation loops** (run validator → fix → repeat) and plan-validate-execute
  for batch/destructive work measurably raise quality. Their absence in a
  high-stakes skill is worth flagging.
- **Step 0 intake gate.** The workflow opens with a "Before starting" step that
  names the specific facts the skill must have before acting (target, scope,
  format, audience), tells the model to mine the conversation for answers first
  and ask the user only for what's missing, and passes silently when everything
  is known. Skills that act on underspecified input produce confident wrong
  output — a missing Step 0 in a skill whose inputs vary is a real finding.
  A bare "ask clarifying questions" line doesn't count; the gate must name its
  questions.

## 5. The anti-pattern catalog

- **The Shouting File.** ALL-CAPS MUST/ALWAYS/NEVER with no reasoning. State the
  rule *and the why* — "use constructor injection; field injection breaks
  testability" beats "MUST use constructor injection." Reasoning lets the model
  generalize to edge cases; bare commands get dropped when context shifts.
- **Stating the obvious.** Claude already knows how to write clean code and can
  read the repo. Spend tokens only on what pushes it *out* of its defaults. The
  highest-signal content is a **Gotchas** section ("the `subscriptions` table is
  append-only — take the highest version, not the newest `created_at`").
- **The Menu.** "use pypdf, or pdfplumber, or PyMuPDF, or..." Give one default
  with an escape hatch.
- **Time-sensitive content.** "Before August 2025, use the old API." Put
  deprecated patterns in a collapsed "Old patterns" note instead.
- **Railroading / over-specification** (see §4).
- **Doing many jobs.** A skill that straddles several purposes confuses the
  agent; one skill = one job. SkillsBench (arXiv:2602.12670): comprehensive
  skills score **-2.9pp — worse than no skill at all**; curated average
  +16.6pp; 2-3 modules +18.6pp vs +5.9pp for 4+. Paper's terms are
  "comprehensive/exhaustive bundles," not "monolithic."

## 6. Scripts for agents

When a script is bundled, check it is agent-friendly, because a script that hangs
or floods output wastes a whole agent turn:
- **Non-interactive** (no TTY/confirmation prompts) — a hard requirement.
- **Meaningful exit codes** and a concise `--help`.
- **Predictable, bounded output** (summary or `--output` file for large results)
  — harnesses truncate long tool output.
- **Structured output to stdout, diagnostics to stderr.**
- **Safe defaults** (`--dry-run`, `--confirm` for destructive ops, idempotency).
- **Helpful errors** that say what was expected and what to try.
- **Self-contained deps** where possible (PEP 723 / `uv run`), and note that the
  API container has no network/runtime install.

## 7. Eval-driven review

Two distinct specs, don't conflate: reviewer recommends this testing to the
author, doesn't run it.
- **Trigger testing** (agentskills.io/skill-creation/optimizing-descriptions):
  ~20 queries in `eval_queries.json`, 8-10 should-trigger, 8-10 should-not
  (near-misses most valuable). 3 runs/query, 0.5 trigger-rate threshold.
- **Output evals** (agentskills.io/skill-creation/evaluating-skills):
  `evals/evals.json`, 2-3 cases, with-skill vs without. Check **outgrowth**
  (base model passes without skill → recommend retiring; SkillsBench: no
  average benefit from self-generated skills) and **regression** on updates.

## 8. Model-generation sensitivity

As of mid-2026, per the Fable 5 prompting guide (verbatim): "Skills developed
for prior models are often too prescriptive for Claude Fable 5 and can degrade
output quality." Principle, stated generation-independently: newer models need
less prescription — verify against the current migration guide.
- Reasoning-based ("Do X because Y causes Z") instructions preferred over rigid
  directives (agentskills.io + skill-creator).
- Flag instructions telling the model to echo, transcribe, or reproduce its
  internal reasoning as response text — refusal risk (check 10;
  platform.claude.com/docs/en/build-with-claude/refusals-and-fallback).

## 9. Claude Code invocation control

Claude Code-only fields (fail upload to claude.ai/API; audit.py flags as INFO,
check 1) — determine target platform first.
- **`disable-model-invocation: true`** for side-effecting skills (writes,
  sends, deletes) run only on explicit invocation — missing on one is a finding.
- **`user-invocable: false`** for background-knowledge skills the model reaches
  for on its own but a user wouldn't type as a command.
- **Scoped `allowed-tools`** — narrow broad grants to what's actually needed.

## 10. Security surface

audit.py runs the deterministic side (script security scan, check 13); reviewer
judgment covers intent — is the network call the skill's actual job? Concrete
checks: env-var reads combined with network calls in bundled scripts, URL
parameter appending/exfiltration, angle brackets in frontmatter, broad tool
grants, base64 blobs, "ignore previous instructions" strings.
Context (Snyk ToxicSkills, 3,984 skills scanned from ClawHub/skills.sh,
snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/): 36.82% had at
least one security flaw of any kind (hardcoded keys, insecure credential
handling, third-party content exposure — not all prompt injection); 13.4%
(534) had a critical-severity issue; 76 human-confirmed malicious payloads; 91%
of confirmed-malicious skills combined prompt injection with conventional
malware.

## 11. Quick scoring rubric

Use to set the verdict line:
- **Triggering:** does the description state what + when with concrete phrases?
  (If no → likely the #1 fix.)
- **Cost:** is the always-loaded/on-trigger content as small as it can be?
- **Determinism:** is mechanical work in scripts, or re-derived by the model
  every run?
- **Clarity:** examples present, terms consistent, freedom matched to fragility?
- **Focus:** one job, with negative triggers if it overlaps a sibling?
