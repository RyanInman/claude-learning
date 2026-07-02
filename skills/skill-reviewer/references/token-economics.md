# Token Economics for Skills — The High-Impact Moves

Read this when writing up findings about token cost. It is deliberately scoped to
the few moves that matter most for a *skill* — not an exhaustive list. The whole
frame: you are not buying a context window, you are buying an **attention
budget**, and it is smaller than the window. Every token a skill forces Claude to
carry competes with the live task. Minimizing tokens is not austerity; it is how
you buy back intelligence.

## Contents
- [1. Recurring vs one-time tokens](#1-recurring-vs-one-time-tokens-the-core-distinction)
- [2. Load the address, not the knowledge](#2-load-the-address-not-the-knowledge)
- [3. The description is the whole game](#3-the-description-is-the-whole-game)
- [4. Compile cognition into scripts](#4-compile-cognition-into-scripts)
- [5. One skill, one job](#5-one-skill-one-job)
- [6. Lost in the middle](#6-lost-in-the-middle)
- [7. The triage questions](#7-the-triage-questions)
- [8. Listing-budget overflow](#8-listing-budget-overflow)
- [9. Compaction behavior](#9-compaction-behavior)

---

## 1. Recurring vs one-time tokens (the core distinction)

Two kinds of tokens, constantly confused:
- **One-time:** loaded once when a task triggers, then gone.
- **Recurring:** loaded on every turn of every session.

For a skill, the body becomes recurring *for the rest of the session* once the
skill triggers — it is not re-read each turn, but it stays. A 200-line section in
the body across a 30-turn session is ~6,000 line-turns of attention spent
re-carrying the same text. The highest-impact token finding is almost always:
**this content is loaded more often than it is needed.** The fix is to move it
down the tier (body → reference) so it loads only when actually used.

Spec recommends the body stay under 5,000 tokens alongside the 500-line
guideline — a recommendation, not a hard limit. audit.py flags bodies over that
at MED, worded "recommended" rather than a cap.

Litmus test for any body line: *"If I deleted this, would the skill work worse?"*
If not, it is not documentation — it is noise hiding the rules that matter.

## 2. Load the address, not the knowledge

Progressive disclosure is the biggest architectural lever. Three tiers:
1. **Startup:** only name + description (~100 tokens) per skill.
2. **On match:** the body loads.
3. **On demand:** references are read and scripts are run only when needed.

Consequence: **a bundled reference costs zero tokens until read; a script costs
zero until run.** You can attach effectively unbounded knowledge to a skill as
long as it stays *addressable* (a pointer) rather than *resident* (inlined).

The beginner trap: **`@imports` are not free** — and in SKILL.md they don't even
work. A "read references/schema.md when relevant" pointer costs nothing until the
moment of need; the same content pasted into the body costs full tokens every
session it is loaded. Prefer pointers to inlined content.

When you see a long body, the question is not "is this useful?" (it usually is) —
it's "does this need to be resident, or can it be addressable?"

## 3. The description is the whole game

You write ~100 tokens (the description) that decide whether the ~hundreds-to-
thousands in the body ever load. A vague description means the skill never fires
and its entire budget is wasted; a trigger-rich one fires reliably. This is both
a triggering issue and a token issue — see best-practices.md §1 for the rewrite
criteria. In a token review, the framing is: a description that under-triggers is
the most expensive failure in the whole skill, because everything else you
optimized never runs.

## 4. Compile cognition into scripts

LLMs are expensive, slow, and non-deterministic at mechanical work. So don't ask
Claude to *think through* deterministic steps every run — compile that thinking
into code once. A 50-line validation script that prints `"Validation passed: 3
pages, 2 tables"` costs ~15 tokens (just its output); the 50 lines never enter
context. Community framing of an ideal skill: **~10% LLM steering, ~90%
deterministic execution.**

So when reviewing, look for instructions that ask the model to do the same
mechanical procedure every time (parsing, validating, formatting, counting,
posting comments). Each is a candidate to move into `scripts/`. The payoff is
triple: fewer tokens, more reliability, less latency.

Also on the output side: prefer **structured output to a file** over verbose
in-context reasoning. The plan-validate-execute pattern (write `changes.json`,
validate with a script, then execute) keeps the reasoning on disk, not in the
token stream — and catches errors before they apply. "Cap the volume" (e.g.
"report at most five findings") is a real token lever too.

## 5. One skill, one job

Overlapping skills create a false-positive tax: the wrong skill keeps loading its
body when its keywords brush a query. The fix is sharp scoping plus **negative
triggers** ("Do NOT use for X — use the Y skill"). A skill doing several jobs both
confuses triggering and bloats the body. When two skills overlap, recommend
distinct trigger keywords or merging them.

## 6. Lost in the middle

Attention forms a U-curve: content in the *center* of a long context can lose
>30% accuracy, and there is a confirmed primacy bias (earlier instructions are
followed more reliably). This gives length a second hidden cost: a long body
doesn't just cost more tokens, it **relocates important rules into the attention
dead-zone.** So front-load what matters in both the body and the description, and
reserve one or two genuine "IMPORTANT" markers for rules that truly can't slip —
if everything shouts, nothing is heard.

## 7. The triage questions

For any instruction or section in a skill, ask in order:
- **Can a machine do this deterministically?** → move it to a script (free
  cognition).
- **Is this needed on every invocation, or only sometimes?** → if sometimes, move
  it to a reference (addressable, not resident).
- **Would one example teach it faster than a paragraph?** → show, don't tell.
- **Is this resident content earning its permanent seat?** → if not, cut it.
- **Must this hold every time, no exceptions?** → hook, not prose.
  Guarantee-shaped rules in a skill body are wishes; flag them.

The closing discipline: don't fill the context, curate it. Keep the working set
small enough that every token left in the room is fighting for the task in front
of it.

## 8. Listing-budget overflow

Descriptions tax the shared listing budget (1% of context window, configurable
via `skillListingBudgetFraction`) before any triggering; `when_to_use` counts
toward the combined 1,536-char per-entry cap (configurable via
`skillListingMaxDescChars`); overflow drops least-invoked skills' descriptions
first; symptom is skills silently not triggering; `/doctor` diagnoses.
Companion deterministic check: audit.py flags combined length > 1,536 (INFO).

Source: code.claude.com/docs/en/skills.md

## 9. Compaction behavior

Invoked skill bodies re-injected capped at 5,000 tokens per skill, 25,000
tokens total, oldest dropped first (code.claude.com/docs/en/context-window.md)
— front-load the body; rules past ~5k tokens vanish after compaction. Review
criterion: does the body front-load what matters?
