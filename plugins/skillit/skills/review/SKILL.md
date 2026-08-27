---
name: review
description: Reviews an existing SKILL.md (and its bundled scripts/references) and produces a prioritized, high-impact-first list of improvement suggestions covering Claude skill best practices (description quality and triggering, progressive disclosure, folder structure, anti-patterns) and token optimization. Use this whenever the user wants to audit, review, critique, improve, optimize, or get feedback on a skill they have written or pasted -- including requests like "review my skill", "is this SKILL.md any good", "why isn't my skill triggering", "make my skill more token-efficient", "what's wrong with this skill", or whenever the user shares a SKILL.md / skill folder and asks what could be better. Do NOT use this to author a brand-new skill from scratch (use skillit:create for that), and do NOT use it to review CLAUDE.md, rules files, or prompts -- this skill is scoped to SKILL.md skill folders.
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
   (e.g. `mkdir -p /tmp/rev/<skill-name> && cp <file> /tmp/rev/<skill-name>/SKILL.md`
   — audit checks that the folder name matches the skill's frontmatter name).
   Note any `scripts/`, `references/`, `assets/` alongside it.

2. **Run the deterministic audit first.** Everything measurable is already coded
   — do not eyeball line counts or frontmatter rules by hand:

   ```
   python ${CLAUDE_SKILL_DIR}/scripts/audit.py <path-to-skill-folder>
   ```

   It reports description length, body size, frontmatter validity, anti-pattern
   counts, and reference/script structure as a list of findings with a
   mechanical severity guess. Add `--json` if you want to parse it. The script
   handles its own errors and exits non-interactively.

3. **Classify the skill, then apply judgment the script can't.** First decide
   which of the four types it is — discipline, technique, pattern, or reference
   — because the type decides which criteria apply. Flagging a reference skill
   for a missing Gotchas section wastes the finding slot that should have gone
   to a real problem. `${CLAUDE_SKILL_DIR}/../../references/form-fit.md` has the type table.

   Then read `${CLAUDE_SKILL_DIR}/../../references/form-fit.md` in full whenever the skill contains rules.
   It covers the question the rest of this review does not ask: whether each
   rule's *shape* matches the failure it prevents. A rule can be correctly
   scoped and sized and still be the form that invites the behavior it forbids —
   a prohibition where the failure is wrong-shaped output, a count where the
   model can pad to pass, a hedge that reopens the negotiation. This is a
   different axis from best-practices §4's freedom-to-fragility, which asks how
   much latitude to grant; say which one a finding answers, because an author
   who conflates them will tighten latitude and change nothing.

   The audit catches the countable things; you catch the rest. Determine the skill's target platform first (Claude Code
   vs claude.ai/API upload) — frontmatter validity and several criteria differ;
   audit.py flags platform-specific fields as INFO. Read the two reference files
   for the full criteria and the *why* behind each, so your suggestions explain
   reasoning rather than assert rules:
   - `${CLAUDE_SKILL_DIR}/../../references/best-practices.md` — description/triggering quality, structure,
     splitting, naming, examples-over-rules, anti-pattern catalog, eval-readiness,
     model-generation sensitivity, invocation control, and security surface.
   - `${CLAUDE_SKILL_DIR}/../../references/token-economics.md` — the high-impact token moves: progressive
     disclosure, recurring vs one-time cost, compile-to-script, one-job +
     negative triggers, lost-in-the-middle, listing-budget overflow, and
     compaction front-loading.

   Prose style is out of scope here — the steyle:grading-markdown-style skill
   grades it against the house writing guides. When a skill's prose is the
   problem, point the user there instead of folding style fixes into this
   review.

   Read the actual files and scripts before reporting on them. Report only what
   you confirmed in the content — no guessing at what a script "probably" does.

4. **Review the evals, if the skill has any.** When `evals/evals.json` exists,
   read the expectations and ask of each one: *would a run without this skill
   also pass it?* An expectation the baseline passes anyway inflates the
   measured delta while testing nothing, and it hides real losses — a skill can
   post a healthy pass-rate gain while losing the case a user actually cares
   about. Flag presence checks ("the plan includes a requirements section")
   and recommend substance checks ("every build step names the files it
   touches"). This is a high-value finding because it corrupts the evidence the
   author will use for every future decision about the skill.

5. **Score each suggestion by confidence (1–10).** The script's severity is a
   mechanical starting guess; replace it with a confidence score that answers two
   questions at once:
   - **Will the fix actually do what it claims?** Will applying it work as
     described, with no hidden breakage or guesswork? A confident rewrite of a
     weak description scores high; a "maybe restructuring helps" hunch scores low.
   - **Will it actually optimize the skill?** How much does it move the things
     that matter — triggering, token cost, output quality? A change that stops a
     dead skill from never firing is a 10; a cosmetic reword is a 3.

   Multiply the two intuitions together: a suggestion only earns a high score if
   you are *both* sure it works *and* sure it helps. High-likelihood-but-trivial
   and high-impact-but-speculative both land mid-band, not top.

   | Score | Meaning |
   |-------|---------|
   | 10    | Near-certain fix, large impact (e.g. fixes a non-triggering description) |
   | 8–9   | High confidence, clear material gain |
   | 6–7   | Plausible fix, moderate or uncertain payoff |
   | ≤5    | Speculative, or correct-but-trivial — cut unless user asked for an exhaustive pass |

   An individual prose-style fix enters this rubric only when it costs real
   clarity or tokens on its own; otherwise style belongs to
   steyle:grading-markdown-style.

6. **Write the review** in the format below.

## Output format

Respond in chat (this is feedback to read, not a file to ship). Surface only the
high-confidence suggestions and tag each with its score. Use this shape:

```
## Skill review: <name>

**Verdict:** <one line — overall health + the single most important fix>

### Surfaced (confidence 8–10)
1. **[9] <short title>** — <what's wrong and the concrete cost (triggering /
   tokens / quality)>. <Why it matters in one clause.>
   *Fix:* <specific, copy-pasteable change — show before -> after when useful.>
```

**Which scores to surface:**
- **Any suggestions scored 8–10:** show them, highest score first. These are the
  changes you are confident will both work and meaningfully help.
- **Nothing scored 8 or above:** the skill is already in good shape — say so
  plainly in the verdict ("No high-confidence wins; the skill is already solid"),
  then show the 6–7 band under a `### Lower-confidence polish (6–7)` heading so
  the user still has options. Don't manufacture an 8 to fill the slot.
- **Below 6:** cut, unless the user asked for an exhaustive pass.

Each item leads with its score in brackets so the user can triage at a glance.

Rules for the write-up:
- **Lead with the highest score.** If the description under-triggers, that fix is
  almost always a 9–10 and goes first.
- **Show, don't just tell.** For description and anti-pattern fixes, give the
  rewritten line, not a description of it.
- **Explain the why, briefly.** "State the rule and the reason" applies to your
  own suggestions too — a fix with a reason generalizes.
- **Quantify token impact** when you can ("this 200-line section loads every
  turn; as a reference it would cost zero until read").
- **Don't railroad.** Offer the change and the reason; let the author decide.
- **Give every 6–7 finding its test.** End the item with the one check that
  would settle it: a micro-test of the wording against a no-guidance control,
  five or more runs, and what to look for in the output. Reason: a
  lower-confidence finding is a hypothesis, and handing the author a way to
  resolve it beats handing them a hunch. `skillit:create` runs the test.

## Scope

This skill reviews **skills** (SKILL.md folders). For authoring a new skill from
scratch, use skillit:create. For a prose-style grade against the house writing
guides, use steyle:grading-markdown-style, which takes one file or a whole skill
folder. For CLAUDE.md / rules-file review, the token
principles transfer but the structure rules differ — say so rather than applying
SKILL.md rules to a memory file.
