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
- [7. Quick scoring rubric](#7-quick-scoring-rubric)

---

## 1. The description (highest leverage)

The `description` is the only part of a skill (with the name) that is always in
context, and it alone decides whether the body ever loads. Claude's dominant
failure mode is **under-triggering** — not reaching for a skill that would help.
So a good description is deliberately, almost embarrassingly "pushy."

A strong description has all of:
- **Third person.** "Reviews a SKILL.md and..." not "You review...".
- **Both what AND when.** State what the skill does *and* the contexts/phrases
  that should fire it. All "when to use" info lives here, not in the body.
- **Concrete trigger phrases.** Quote the kinds of things a real user types —
  "use this whenever the user mentions dashboards, metrics, or company data, even
  if they don't say 'dashboard'." Vague descriptions never fire.
- **Negative triggers when domains overlap.** "Do NOT use for simple data
  exploration — use the data-viz skill instead." This is the single most
  effective fix for false-positive firing between sibling skills.

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
  agent. One skill = one job; split or scope it.

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

## 7. Quick scoring rubric

Use to set the verdict line:
- **Triggering:** does the description state what + when with concrete phrases?
  (If no → likely the #1 fix.)
- **Cost:** is the always-loaded/on-trigger content as small as it can be?
- **Determinism:** is mechanical work in scripts, or re-derived by the model
  every run?
- **Clarity:** examples present, terms consistent, freedom matched to fragility?
- **Focus:** one job, with negative triggers if it overlaps a sibling?
