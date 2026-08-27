# Form-Fit — does each rule's shape match the failure it prevents?

Read this when a skill contains rules — when writing them, to pick the right form the first time, and when reviewing them, to judge whether they will hold. The rest of the review asks whether a skill is well-formed. This asks whether its guidance is the right *shape* for the failure it exists to prevent — a distinct question, because a rule can be correctly scoped, correctly sized, and still be the form that invites the behavior it forbids.

## Contents

- [Not the same as freedom-to-fragility](#not-the-same-as-freedom-to-fragility)
- [Classify the failure first](#classify-the-failure-first)
- [Why prohibitions backfire on shaping problems](#why-prohibitions-backfire-on-shaping-problems)
- [Two rules for whichever form you pick](#two-rules-for-whichever-form-you-pick)
- [Skill type selects the criteria](#skill-type-selects-the-criteria)
- [What audit.py already catches](#what-auditpy-already-catches)

---

## Not the same as freedom-to-fragility

`best-practices.md` §4 asks **how much latitude** a rule should grant: many valid approaches get text guidance, a fragile operation gets an exact command. That calibration can be right while the form is still wrong.

A skill can grant exactly the correct latitude and still express the rule as a prohibition where a recipe was needed. Judge both. When you report a form finding, say which question it answers, because an author who conflates the two will "fix" it by tightening latitude and change nothing.

## Classify the failure first

Name the failure the rule prevents, then check the form against this table. The form that bulletproofs one class measurably backfires on another.

| Baseline failure | Right form | Wrong form |
|---|---|---|
| Knows the rule, breaks it under pressure | Prohibition, plus a table of the excuses seen in testing and a red-flags list | Soft guidance — "prefer", "consider" |
| Complies, but the output has the wrong shape — bloated, buried, restated | A positive recipe: state what the output **is**, its parts, in order | A prohibition list — "don't restate", "never narrate" |
| Omits an element from something it already produces | Structural: a required slot in the template it fills in | Prose reminders near the template |
| Behavior should depend on context | A conditional keyed to something observable — "if the file has no tests, ..." | An unconditional rule with exemption clauses |

## Why prohibitions backfire on shaping problems

Under a competing incentive, a model negotiates with "don't X". In head-to-head wording tests on dispatch-prompt guidance, the prohibition arm produced clearly more of the unwanted content than the recipe arm, and trended worse than the no-guidance control. A recipe leaves nothing to negotiate: the output either matches the stated shape or it does not.

Treat that as a strong prior, not a law — the effect is measured on one family of prompts. When a finding turns on it, say what would settle the question rather than asserting the result.

## Two rules for whichever form you pick

**No nuance clauses.** "Don't X unless it matters" reopens the negotiation the rule closed. Appending one nuance clause to a winning recipe degraded it from consistent to noisy in the same tests. A real exception belongs in its own conditional on an observable predicate.

**Exemption clauses do not scope.** "This limit does not apply to code blocks" still suppresses code blocks. When part of the output must be exempt, restructure so the rule cannot reach it.

**A count is not a quality bar.** "One acceptance criterion per requirement" is satisfiable by restating each requirement, so the model pads to pass. Name the property that makes an item worth including — "only for requirements that could plausibly fail."

## Skill type selects the criteria

Applying one checklist to every skill generates findings the author cannot act on: a reference skill has no Gotchas to write, a discipline skill fails silently without rationalization coverage. Classify first, then judge only what applies.

| Type | What it is | Judge it on | Do not flag |
|---|---|---|---|
| **Discipline** | Enforces a rule under pressure (test-first, no force-push) | Are the specific loopholes closed? Is there a rationalization table drawn from real testing? | Missing worked example |
| **Technique** | A method with steps (debugging loop, migration) | One complete worked example; Step 0 intake gate; a Gotchas section | Missing rationalization table |
| **Pattern** | A way of thinking (when to reach for X) | Recognition cues, and counter-examples for when not to apply | Missing exact commands |
| **Reference** | API, schema, or command docs | Retrieval: is it findable, is it organized by domain, does it have a table of contents | Missing Gotchas, missing example |

A skill that will not classify is usually doing several jobs. That is its own finding, and it outranks anything in this file.

## What audit.py already catches

Do not re-derive these by reading. The script reports them as `form-fit` or `description` findings:

- A description that narrates the step sequence, which lets an agent act on the summary and skip the body.
- A count tied to an enumerable set, excluding work distribution and scoring formulas.
- An open-ended hedge appended to a rule.
- `@path` imports, which resolve in CLAUDE.md and load nothing in a SKILL.md.
- Evals defined with no benchmark showing the skill beat baseline.

What the script cannot see is the judgment: whether the rule's form matches the failure, and whether the skill's type makes a given criterion apply at all. When authoring, use the tables above to pick the form before writing; when reviewing, use them to name what is wrong with the form already there.
