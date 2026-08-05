---
name: style-guide
description: Grades the prose of an existing skill (SKILL.md body plus its references/) against the skillit house writing style guide, returning an A-F adherence grade and, below an A, a complete rule-by-rule checklist of edits that reaches an A. Use whenever the user wants a style pass, prose grade, or writing-consistency check on a skill they wrote or pasted -- requests like "style check my skill", "grade the writing in this SKILL.md", "does my skill follow the house style", "clean up the prose in my skill", "style pass on this skill", or after a skill draft is finished and its prose needs the dedicated editing pass. Do NOT use for a full skill audit covering triggering, structure, anti-patterns, and token cost (use skillit:review for that), do NOT use to author a brand-new skill (use skillit:create), and do NOT use on prose that is not a skill folder -- blog posts, docs, or CLAUDE.md are out of scope.
---

# Skill Style Grader

Grade a skill's prose against the house writing style guide. Return the A–F
grade plus the complete list of edits that reaches an A. Style is a measure of
adherence, so grade by how closely the prose follows the guide's principles —
never by the likelihood or payoff of any single correction.

## Workflow

1. **Locate the skill.** Find the folder containing `SKILL.md`. If the user
   pasted a SKILL.md inline, save it to a temp folder first (e.g.
   `mkdir -p /tmp/style/<skill-name>` and write the file there). Note every
   file under `references/` — the guide governs those too.

2. **Run the deterministic scan.** Run `python ${CLAUDE_SKILL_DIR}/scripts/scan.py
   <path-to-skill-folder>`. It flags literal Rule 3, 6, and 9 hits across
   SKILL.md and every reference file. Those are the "and then" phrase, the
   closed vague-word list, and ALL-CAPS MUST/NEVER/ALWAYS. It already skips
   the frontmatter description and any Example section. Confirm each hit sits
   inside real instructional prose before you count it, because the script
   finds candidates, not final violations.

3. **Read the guide.** Read `${CLAUDE_SKILL_DIR}/../../references/writing-style-guide.md`
   in full. It defines the Part A sentence rules (1–10), the two exempt zones
   (Rules 11–12), the conflict-resolution order, the pre-ship checklist, and
   the adherence grading table. Grade from the guide as written, not from
   memory, because the guide evolves and a stale rule misgrades the skill.

4. **Walk the Part A checklist** over the SKILL.md body and each reference
   file. Start from the scan's hits for Rules 3, 6, and 9. Read the prose
   yourself for Rules 2, 5, and 8. Passive voice, synonym drift, and stacked
   clauses need judgment a pattern match cannot supply. Respect the
   two exempt zones — the frontmatter description (Rule 11) and verbatim
   input→output examples (Rule 12). Never flag style inside them; they carry
   their own rules and an "edited" example teaches the wrong distribution.

5. **Assign the grade** from the guide's adherence table. Count which rules
   are violated and how often; the pattern of violations, not the severity of
   any one line, sets the grade.

6. **Write the report** in the format below. When the grade is below A, list
   **every** change needed to reach an A, not just the worst offenders. A
   partial list means the author can apply all of it and still grade below A
   on the next pass.

## Output format

Respond in chat (this is feedback to read, not a file to ship):

```
## Style grade: <skill-name>

**Grade:** <A–F> — <the two or three rules that cost it the most>

<One quoted offending line per costly rule, because a quoted line lets the
author find the whole pattern.>

### Checklist to reach an A
<Omit this section entirely at grade A.>
1. **Rule <n> (<rule name>)** — "<offending line>" → "<fixed line>"
2. ...
```

### Example

A body line reads: "Results are written to out.json and then the report gets
generated as needed."

The report item:

> **Rule 2 (keep the actor visible) + Rule 3 (one instruction per sentence) +
> Rule 6 (name the specific action)** — "Results are written to out.json and
> then the report gets generated as needed." → "The script writes results to
> `out.json`. Then render the report with `scripts/render.py`."

## Gotchas

- **Do not grade the description.** Rule 11 exempts it from Part A, so its
  colloquial phrasings can target triggering instead of prose style. Flagging
  it as "informal prose" is the most common false positive.
- **Grade references, not just the body.** Authors polish SKILL.md and forget
  `references/`; the guide applies to both.
- **The guide path assumes the skillit plugin layout.** When
  `${CLAUDE_SKILL_DIR}/../../references/writing-style-guide.md` does not
  resolve (e.g. the skill was copied out of the plugin), ask the user for the
  guide's location instead of grading from memory.

## Scope

This skill grades prose style only. For triggering, structure, token cost, and
anti-pattern review, use skillit:review — it reports style as out of scope and
points here. For authoring or editing a skill, use skillit:create.
