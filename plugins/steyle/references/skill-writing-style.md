# Skill Writing Style Guide

House style for SKILL.md files and their `references/`. This guide builds on [universal-writing-style.md](../output-styles/universal-writing-style.md). Every universal rule applies to the SKILL.md body and to all reference files. This guide adds what is specific to skills — two exempt zones, a token budget, and skill hygiene.

The goal: skills that trigger reliably, read unambiguously, and stay token-lean.

## Contents

- [Base rules](#base-rules)
- [Zone 1 — The frontmatter description](#zone-1--the-frontmatter-description)
- [Zone 2 — Examples](#zone-2--examples)
- [Structure and token budget](#structure-and-token-budget)
- [Skill hygiene](#skill-hygiene)
- [Conflict resolution order](#conflict-resolution-order)
- [Pre-ship checklist](#pre-ship-checklist)
- [Adherence grading](#adherence-grading)

---

## Base rules

Apply the full universal guide to the body and every reference file. These rules matter most in skills, because a model executes the text under load:

- Start every instruction with a command verb (D1).
- Keep the actor visible — Claude, the user, or a script (B1).
- Give one instruction per sentence. Treat 20 words as the rewrite tripwire (C1, C2).
- One term per concept. Build a terminology table in your drafting notes the moment you reach for a synonym. Keep the table out of the shipped skill (A1).
- Name the specific action and amount. Never write "handle" or "as needed" (D2).
- Attach the reason to every non-obvious rule. Write no ALL-CAPS directives (D3).
- Cut filler after the rules hold, never past clarity (F).

One skill-specific relaxation: where splitting a sentence would triple the line count with no clarity gain, keep the denser sentence. The 500-line ceiling on SKILL.md outranks the one-instruction rule.

## Zone 1 — The frontmatter description

The description is the only text loaded at startup, and it alone decides whether the skill fires. Every universal rule is suspended here.

**Do:**
- Write third person: "Transforms a funny idea into 3 satirical headlines…"
- Pack in verbatim trigger phrasings, casual included: "turn this into a skill", "is this still good to eat", "what's wrong with my deck".
- Cover implicit asks: "even if they don't explicitly say 'dashboard'."
- Add negative triggers for near-miss cases: "Do NOT use for X (use [other-skill] instead)."
- Err pushy. Under-triggering is the default failure mode.

**Don't:**
- Apply the terminology table, sentence caps, or imperative mood to the description.
- Sanitize colloquial trigger phrases into formal prose. Their value is that they match what users type.
- Put "when to use" information anywhere in the body. Claude never reads the body until after it makes the trigger decision.

## Zone 2 — Examples

Every skill includes at least one concrete input→output example, because Claude generalizes from one real example better than from fifty lines of abstract rules.

**Do:**
- Reproduce real user phrasing and real output exactly, typos and informality included.

**Don't:**
- Rewrite example text to conform to the style rules. An edited example teaches the wrong distribution.
- Substitute a description of the output for the output itself.

## Structure and token budget

- Keep the SKILL.md body under 500 lines. Start moving detail to `references/` at about 300 lines.
- Keep references one level deep. Add a table of contents to any reference over about 100 lines.
- Use forward-slash paths. Do not use `@` imports in SKILL.md, because they load eagerly and defeat progressive disclosure.
- Delegate deterministic work to bundled scripts: parsing, validation, counting, report rendering. A script gives the same output every run. Prose re-derivation does not.

## Skill hygiene

- Include a gotchas section. Give each entry its reason.
- Name one default tool per job. Do not offer option menus, because a menu delegates a choice the skill exists to make.
- Ship at least 2 realistic eval prompts in `evals/evals.json`. Test them against the no-skill baseline, because a skill that does not beat the baseline is pure token cost.

## Conflict resolution order

When two rules collide, the earlier item wins:

1. Triggering reliability (Zone 1)
2. Example fidelity (Zone 2)
3. Token budget — body under 500 lines, splitting to `references/` from ~300
4. Reasons attached to rules (D3)
5. All other universal rules

## Pre-ship checklist

Run against the finished skill. Fix faults. Never annotate them.

**Universal conformance (body + references):**
- [ ] Full universal checklist passes ([universal-writing-style.md](../output-styles/universal-writing-style.md#checklist))
- [ ] Terminology table applied throughout
- [ ] Terminology table itself not shipped

**Zone conformance:**
- [ ] Description: third person, verbatim user phrasings, implicit cases, negative triggers
- [ ] All "when to use" content lives in the description, none in the body
- [ ] ≥1 verbatim input→output example, untouched by style editing

**Structure and hygiene:**
- [ ] Body under 500 lines
- [ ] References split out from ~300 lines
- [ ] References one level deep
- [ ] TOC on any reference over ~100 lines
- [ ] Forward-slash paths throughout
- [ ] No `@` imports in SKILL.md
- [ ] Gotchas section present, each entry with its reason
- [ ] One default tool per job, with no option menus
- [ ] ≥2 realistic eval prompts in `evals/evals.json`, tested against the no-skill baseline

## Adherence grading

Grade style by how closely the prose follows the rules — never by the likelihood or payoff of any single correction. Walk the checklist over the body and each reference. Count which rules are violated and how often. Then assign the grade.

| Grade | Adherence level |
|---|---|
| A | Full adherence — the checklist passes; at most an isolated borderline sentence |
| B | Minor drift — a few violations of one or two rules; meaning never at risk |
| C | Patterned drift — one rule broken repeatedly, or several rules broken occasionally |
| D | Widespread violations — several rules broken throughout; the prose needs a full editing pass |
| F | Guide not applied — pervasive passive voice, vague terms, or synonym drift |

Report the grade with the two or three rules that cost it the most. Quote one offending line per rule, because a quoted line lets the author find the whole pattern. Exempt zones never count against the grade.

## Workflow tip

Draft naturally first. Apply this guide as a dedicated editing pass, checklist in hand. A blank-page draft written to the rules is slower and stiffer than one edited toward them.
