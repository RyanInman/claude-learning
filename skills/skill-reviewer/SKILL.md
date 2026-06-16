---
name: skill-reviewer
description: Reviews an existing SKILL.md (and its bundled scripts/references) and produces a prioritized, high-impact-first list of improvement suggestions covering Claude skill best practices (description quality and triggering, progressive disclosure, folder structure, anti-patterns) and token optimization. Use this whenever the user wants to audit, review, critique, improve, optimize, or get feedback on a skill they have written or pasted -- including requests like "review my skill", "is this SKILL.md any good", "why isn't my skill triggering", "make my skill more token-efficient", "what's wrong with this skill", or whenever the user shares a SKILL.md / skill folder and asks what could be better. Do NOT use this to author a brand-new skill from scratch (use the skill-creator for that), and do NOT use it to review CLAUDE.md, rules files, or prompts -- this skill is scoped to SKILL.md skill folders.
---

# Skill Reviewer

Audit an existing skill and return a short, prioritized list of improvements. The
goal is **high-leverage suggestions only** — the one or two changes that move
triggering, output quality, or token cost the most — not an exhaustive nitpick
list. A long review that buries the important finding is itself the anti-pattern
this skill exists to catch.

## Why this matters (the lens)

Two failure modes dominate real skills, and both are about attention:

1. **The skill never fires.** The `description` is the router that decides
   whether the body ever loads. A weak description wastes the entire skill.
2. **The skill costs more than it earns.** Once a skill triggers, its whole body
   sits in context for the session, competing with the live task. Bloat, content
   that should be a script, and detail that should be an on-demand reference all
   tax every turn.

Everything below serves finding and fixing those.

## Workflow

1. **Locate the skill.** Find the folder containing `SKILL.md`. If the user
   pasted a SKILL.md inline, save it to a temp folder so the script can read it
   (e.g. `mkdir -p /tmp/rev && cp <file> /tmp/rev/SKILL.md`). Note any
   `scripts/`, `references/`, `assets/` alongside it.

2. **Run the deterministic audit first.** Everything measurable is already coded
   — do not eyeball line counts or frontmatter rules by hand:

   ```
   python scripts/audit.py <path-to-skill-folder>
   ```

   It reports description length, body size, frontmatter validity, anti-pattern
   counts, and reference/script structure as a list of findings with a
   mechanical severity guess. Add `--json` if you want to parse it. The script
   handles its own errors and exits non-interactively.

3. **Apply judgment the script can't.** The audit catches the countable things;
   you catch the rest. Read the two reference files for the full criteria and the
   *why* behind each, so your suggestions explain reasoning rather than assert
   rules:
   - `references/best-practices.md` — description/triggering quality, structure,
     splitting, naming, examples-over-rules, and the anti-pattern catalog.
   - `references/token-economics.md` — the high-impact token moves: progressive
     disclosure, recurring vs one-time cost, compile-to-script, one-job +
     negative triggers, lost-in-the-middle.

   Read the actual files and scripts before reporting on them. Report only what
   you confirmed in the content — no guessing at what a script "probably" does.

4. **Re-triage by real-world impact.** The script's severity is a starting
   guess. Promote/demote based on consequence: anything that stops the skill
   from triggering or that loads large content on every turn is HIGH regardless
   of what the script said; pure style is LOW. Then **cut the low-impact
   findings** unless the user asked for an exhaustive pass. Aim for the top 3–6
   suggestions, not everything.

5. **Write the review** in the format below.

## Output format

Respond in chat (this is feedback to read, not a file to ship). Use this shape:

```
## Skill review: <name>

**Verdict:** <one line — overall health + the single most important fix>

### High-impact
1. **<short title>** — <what's wrong and the concrete cost (triggering / tokens /
   quality)>. <Why it matters in one clause.>
   *Fix:* <specific, copy-pasteable change — show before -> after when useful.>

### Worth doing
- <medium-impact items, same shape, terser>

### Optional / nits
- <only if genuinely useful; otherwise omit this section entirely>
```

Rules for the write-up:
- **Lead with the highest-leverage fix.** If the description under-triggers,
  that is almost always #1.
- **Show, don't just tell.** For description and anti-pattern fixes, give the
  rewritten line, not a description of it.
- **Explain the why, briefly.** "State the rule and the reason" applies to your
  own suggestions too — a fix with a reason generalizes.
- **Quantify token impact** when you can ("this 200-line section loads every
  turn; as a reference it would cost zero until read").
- **Don't railroad.** Offer the change and the reason; let the author decide.

## Scope

This skill reviews **skills** (SKILL.md folders). For authoring a new skill from
scratch, use the skill-creator. For CLAUDE.md / rules-file review, the token
principles transfer but the structure rules differ — say so rather than applying
SKILL.md rules to a memory file.
