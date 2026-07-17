# Compile Deliverables: Templates and Promotion Rules

## Contents
1. Promotion rules (what goes where)
2. overview.md template
3. Patterns-research doc template
4. Path-scoped rule file template

---

## 1. Promotion rules (what goes where)

Apply these mechanically; they are the contract that keeps `overview.md`
trustworthy as the corpus grows. They do not gate the patterns-research
docs — each one is a full write-up of one branch's `analysis.md`,
findings and all, regardless of confidence or recurrence (see §3).

| Signal | Destination |
|---|---|
| Pattern with `confidence: high/medium` recurring in **≥2 branches** | overview.md → Confirmed patterns |
| Pattern seen in **1 branch**, any confidence | overview.md → Observed once (unconfirmed) |
| Any pattern with `confidence: low` | overview.md → Observed once (unconfirmed), regardless of recurrence |
| Pattern with `scope:` narrower than `repo`, recurring in ≥2 branches | Also emitted as a path-scoped rule file |
| Contradicting observations (an ID plus its `-violated` counterpart) | overview.md → Open questions; excluded from rule files |
| Rework signals recurring in ≥2 branches | overview.md → Rework findings |
| Rework signals seen once | overview.md → Findings |

When the corpus is a single branch, say so plainly in `overview.md`:
every pattern is provisional. Recommend studying 3–5 branches before
treating any pattern as confirmed.

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

## 3. Patterns-research doc template

Write to `patterns-research/<branch-slug>.md` — one file per branch in
the corpus, overwritten in full on every compile. This is plain prose for
an engineer about to work on similar code, not a skill: no frontmatter,
no "Use when" triggers, nothing loaded automatically. Pull the branch's
own findings straight from its `analysis.md`; pull recurrence context
(which other branches share a pattern) from `index.json`.

```markdown
# Patterns Research: <branch>

Studied <date>. Ticket: <ticket URL or "n/a">.

## Summary
(2–4 sentences: what this branch built and the strongest patterns it
demonstrates.)

## Standard steps
(this branch's "Standard steps observed" bullets from analysis.md, each
noting recurrence: "also seen in feature/x, feature/y" or "seen only
here so far.")

## Conventions
(this branch's "Conventions observed" bullets, same recurrence note.)

## Examples
(2–3 real requirement → files-changed pairs, pulled only from
Traceability rows marked `fulfilled` — a `partial` or `not fulfilled` row
has no code that actually satisfies it, so citing its files here would
teach the wrong shape.)

**"Users can sign in with Okta"** →
`src/api/auth/OktaController.cs`, `src/api/auth/OktaValidator.cs`,
`src/core/identity/OktaProvider.cs`, `tests/api/auth/Okta.spec.ts`,
migration `20260412_AddIdentityProvider`.

## Gotchas
(this branch's "Rework signals" bullets: mistake → why → correct
approach, noting if the same mistake recurred elsewhere in the corpus.)

## Open questions
(this branch's own Open questions, plus any contradiction with another
branch's patterns-research doc — link it by path.)
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
