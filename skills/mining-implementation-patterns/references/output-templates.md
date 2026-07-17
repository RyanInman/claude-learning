# Compile Deliverables: Templates and Promotion Rules

## Contents
1. Promotion rules (what goes where)
2. overview.md template
3. Generated skill template
4. Path-scoped rule file template

---

## 1. Promotion rules (what goes where)

Apply these mechanically; they are the contract that keeps the generated
skill trustworthy as the corpus grows.

| Signal | Destination |
|---|---|
| Pattern with `confidence: high/medium` recurring in **≥2 branches** | Generated skill (workflow step, checklist item, or gotcha) **and** overview.md |
| Pattern seen in **1 branch**, any confidence | overview.md only, marked *observed once* |
| Any pattern with `confidence: low` | overview.md only, regardless of recurrence |
| Pattern with `scope:` narrower than `repo`, recurring in ≥2 branches | Also emitted as a path-scoped rule file |
| Contradicting observations (an ID plus its `-violated` counterpart) | overview.md → Open questions; excluded from generated skill and rules |
| Rework signals recurring in ≥2 branches | Generated skill → Gotchas |
| Rework signals seen once | overview.md → Findings |

When the corpus is a single branch, say so plainly in the outputs: the
generated skill will be thin and every pattern is provisional. Recommend
studying 3–5 branches before treating the generated skill as reliable.

## 2. overview.md template

```markdown
# Implementation Patterns: <repo name>

## Summary
(5–10 sentences: what kind of codebase, how features flow through it, the
3–5 strongest patterns, current corpus size and confidence level.)

## Corpus
| Branch | Ticket | Studied | Requirements | Commits |
|---|---|---|---|---|

## Architecture map
(How the studied changes reveal the system's layering: directories, their
roles, and how a feature typically flows across them. Derived from
index.json directory histograms + change-anatomy sections.)

## Confirmed patterns
| ID | Scope | Claim | Seen in | Evidence |
|---|---|---|---|---|
(≥2 branches, medium+ confidence. Evidence = branch:sha references.)

## Observed once (unconfirmed)
(same table shape)

## Standard steps
(the every-time checklist, with recurrence counts)

## Rework findings
(mistake → lesson bullets, with citations)

## Open questions
(contradictions, low-confidence claims, things to confirm with the team)

## Compile log
- <date>: compiled from N branches; <what changed since last compile>
```

## 3. Generated skill template

Write to `output/skills/implementing-<repo>-features/SKILL.md`. The
generated skill is forward-looking: concrete file paths and real examples
from the corpus stay in; commit SHAs stay out (meaningless to its future
reader). Its description needs its own triggers — model them on:

```markdown
---
name: implementing-<repo>-features
description: >
  How to implement features in <repo> the way this team does, learned from
  <N> completed branches. Use this skill whenever the user asks to build,
  implement, add, or change functionality in <repo> from a requirement,
  ticket, or feature description — even for small changes — including
  phrases like "implement this ticket", "add an endpoint", "build this
  feature". Do NOT use for studying past branches (use
  mining-implementation-patterns instead).
---

# Implementing Features in <repo>

(2–4 sentences: the repo's shape and the standard flow of a change.)

## Where things live
(table: concern → directory → naming convention. From confirmed
scope-local patterns and the architecture map.)

## Workflow
1. Parse the requirement into atomic items (R1..Rn).
2. For each item, locate the layers to touch using "Where things live".
3. Implement in the order this team uses: <confirmed ordering pattern>.
4. Apply the standard steps checklist below before considering any item done.

## Standard steps checklist
(confirmed every-time actions, one per line, checkbox format)

## Examples
(2–3 real requirement → files-changed pairs lifted from the corpus, e.g.:
**"Users can sign in with Okta"** →
`src/api/auth/OktaController.cs`, `src/api/auth/OktaValidator.cs`,
`src/core/identity/OktaProvider.cs`, `tests/api/auth/Okta.spec.ts`,
migration `20260412_AddIdentityProvider`.)

## Gotchas
(promoted rework findings: mistake + why + correct approach)
```

## 4. Path-scoped rule file template

Emit each qualifying pattern group into
`output/rules/<scope-slug>.md` (`src/api/**` → `src-api.md`) in the
generic format below, then install into the user's chosen consumer format
per `references/rule-formats.md`.

```markdown
---
paths: ["src/api/**"]
derived_from: mining-implementation-patterns (<date>, N branches)
---

# Rules: src/api

- Every new endpoint ships with a FluentValidation validator and a
  matching `*.spec.ts` under `tests/api`, in the same change — endpoints
  without validators were flagged in review in 3 of 4 studied branches.
- Error responses use ProblemDetails; ad-hoc error shapes were reworked
  in `feature/sso-login` and `feature/billing-export`.
```

Rule-writing style: each bullet states the rule **and** the observed
reason, so a future agent can judge edge cases instead of pattern-matching
blindly. 3–10 bullets per file; a scope with fewer than 2 confirmed rules
does not get a file.
