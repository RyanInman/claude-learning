# Writing Effective Instructions

How to write skill instructions that produce consistent, high-quality output without railroading Claude. Read this when drafting or revising the prose body of a `SKILL.md`.

## Contents

- [Voice and terminology](#voice-and-terminology)
- [Degrees of freedom](#degrees-of-freedom)
- [Templates](#templates)
- [Examples beat rules](#examples-beat-rules)
- [Validation loops](#validation-loops)
- [Anti-patterns](#anti-patterns)
- [The Gotchas section](#the-gotchas-section)

## Voice and terminology

Write in the **imperative / infinitive**, third person: "Read the file," "Extract the fields" — not "you should read the file." Use one consistent term throughout. Don't mix _extract / pull / get / retrieve_ or _field / box / element_; the inconsistency makes Claude wonder whether you mean different things.

## Degrees of freedom

This is the single most important calibration: match instruction specificity to how fragile the task is.

- **High freedom (text instructions)** when many approaches are valid and the right one depends on context — e.g., code review, design feedback. Give direction, not a script.
- **Medium freedom (pseudocode or parameterized scripts)** when a preferred pattern exists but inputs vary.
- **Low freedom (exact scripts, no parameters)** when an operation is fragile and consistency is critical — e.g., "Run exactly this: `python scripts/migrate.py --verify --backup`. Do not modify the command."

The analogy: a narrow bridge over a cliff has one safe path, so give exact steps; an open field has many paths, so give a direction and let Claude navigate. Over-specifying an open-field task is railroading; under-specifying a narrow-bridge task invites errors.

## Templates

Provide templates, matching strictness to need. For strict formats (API responses, reports), state the exact structure: "ALWAYS use this exact template." For flexible guidance, signal the latitude: "here is a sensible default, but use your judgment."

```markdown
## Report structure

ALWAYS use this exact template:

# [Title]

## Executive summary

## Key findings

## Recommendations
```

## Examples beat rules

A single concrete input→output example is worth more than 50 lines of abstract description — Claude generalizes from examples better than from rule lists. Anthropic's own commit-message skill shows three input→output pairs rather than describing the format:

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

## Anti-patterns

- **ALL-CAPS `MUST`/`ALWAYS`/`NEVER` with no reasoning.** State the rule _and the why_: "Use constructor injection — field injection breaks testability because we can't mock the field without a Spring context" beats "MUST use constructor injection." Today's models have good theory of mind; given the reason, they generalize correctly to edge cases the rule didn't name. Piling up caps locks is a yellow flag.
- **Railroading.** Over-specific instructions fail when the skill is reused across varied inputs. Give information plus the flexibility to adapt.
- **Stating the obvious.** Claude already knows how to code and can read the codebase. Restating defaults adds tokens without value. Spend words on what pushes Claude _out_ of its default behavior.
- **Offering too many options** ("use pypdf, or pdfplumber, or PyMuPDF, or…"). Provide one default with an escape hatch.
- **Time-sensitive information** ("before August 2025, use the old API"). Put deprecated content in a collapsed "Old patterns" section instead of inline caveats.

## The Gotchas section

A **Gotchas** section is often the highest-signal content in a skill: the real failure points that aren't discoverable from the code or from Claude's defaults. Capture each one as a concrete, specific note — e.g., "The `subscriptions` table is append-only; take the row with the highest version, not the most recent `created_at`." Every edge case you hit while iterating belongs here as a one-line addition.
