# Writing Effective Instructions

How to write skill instructions that produce consistent, high-quality output without railroading Claude. Read this when drafting or revising the prose body of a `SKILL.md`. The check-side versions of these rules — and the full anti-pattern catalog (shouting, railroading, stating the obvious, menus, time-sensitive content) — are canon in `../../../references/best-practices.md` §4–5; read that when you want the *why* behind a rule or the review criteria your draft will be graded against.

## Contents

- [Voice and terminology](#voice-and-terminology)
- [Degrees of freedom](#degrees-of-freedom)
- [Step 0: clarifying questions](#step-0-clarifying-questions)
- [Templates](#templates)
- [Examples beat rules](#examples-beat-rules)
- [Validation loops](#validation-loops)
- [The Gotchas section](#the-gotchas-section)

## Voice and terminology

Write in the **imperative / infinitive**, third person: "Read the file," "Extract the fields" — not "you should read the file." Use one consistent term throughout. Don't mix _extract / pull / get / retrieve_ or _field / box / element_; the inconsistency makes Claude wonder whether you mean different things.

## Degrees of freedom

This is the single most important calibration: match instruction specificity to how fragile the task is.

- **High freedom (text instructions)** when many approaches are valid and the right one depends on context — e.g., code review, design feedback. Give direction, not a script.
- **Medium freedom (pseudocode or parameterized scripts)** when a preferred pattern exists but inputs vary.
- **Low freedom (exact scripts, no parameters)** when an operation is fragile and consistency is critical — e.g., "Run exactly this: `python scripts/migrate.py --verify --backup`. Do not modify the command."

The analogy: a narrow bridge over a cliff has one safe path, so give exact steps; an open field has many paths, so give a direction and let Claude navigate. Over-specifying an open-field task is railroading; under-specifying a narrow-bridge task invites errors.

## Step 0: clarifying questions

Open every skill's workflow with a **Step 0** titled "Before starting". Its job is to resolve ambiguity before any work happens — a clarifying question asked after the output exists costs a full redo, so the questions belong at the front, not scattered through the steps.

Step 0 contains:

- **The specific facts the skill needs before it acts** — target file, environment, output format, scope, audience. Name them concretely. A bare "ask clarifying questions" is too vague to change behavior; a list of the three facts that actually gate the work is what gets asked.
- **Mine before asking.** Instruct the skill to extract answers from the conversation and provided inputs first, then ask the user only for what is missing. Re-asking something the user already said erodes trust in the skill.
- **A silent pass.** When every fact is already present, Step 0 passes without a pause — it is a gate, not a mandatory interview. This keeps the step from railroading fully-specified requests.

```markdown
## Workflow

### Step 0: Before starting

Confirm these before touching any file — a wrong answer here redoes the whole run:

1. Which environment is the target (staging or production)? Never assume production.
2. Is there an existing report to update, or is this a fresh run?
3. Who reads the output (engineers or executives)? This sets the report's depth.

Extract answers from the conversation first; ask the user only for what is missing. If all three are known, proceed without asking.
```

Step 0 and [validation loops](#validation-loops) are the two halves of the same guarantee: Step 0 catches ambiguity before the work, the validation loop catches errors after it.

## Templates

Provide templates, matching strictness to need. When the skill's job is a recurring deliverable (a report, a message, a file set), always include an exact output template with placeholder slots — a fixed template is what makes every run produce the same shape, which is usually why the user wanted a skill. State the exact structure with its reason ("use this exact template — readers rely on the same sections every time"). For flexible guidance, signal the latitude: "here is a sensible default, but use your judgment."

```markdown
## Report structure

Use this exact template — readers rely on the same sections every time, so the shape must not change:

# [Title]

## Executive summary

## Key findings

## Recommendations
```

## Examples beat rules

Show, don't describe — Anthropic's own commit-message skill gives input→output pairs rather than format rules:

```markdown
## Commit message format

**Example 1:**
Input: Added user authentication with JWT tokens
Output: feat(auth): implement JWT-based authentication
```

## Validation loops

The "run validator → fix errors → repeat" pattern greatly improves quality. For batch, destructive, or high-stakes work use **plan-validate-execute**: have Claude write a plan to a structured file (e.g., `changes.json`), validate it with a script, then execute — catching errors before they're applied.

Make verification scripts verbose, with specific, actionable error messages:

```
Field 'signature_date' not found. Available fields: customer_name, order_total, signature_date_signed
```

That lets Claude self-correct instead of guessing. For code review specifically, instruct Claude to "read actual code with Read/Grep before reporting — only report what you confirmed in the file." Without this, Claude generates plausible-sounding but fabricated findings.

## The Gotchas section

A **Gotchas** section is often the highest-signal content in a skill: the real failure points that aren't discoverable from the code or from Claude's defaults. Capture each one as a concrete, specific note — e.g., "The `subscriptions` table is append-only; take the row with the highest version, not the most recent `created_at`." Every edge case you hit while iterating belongs here as a one-line addition.
