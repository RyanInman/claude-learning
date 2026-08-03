# Writing a Per-Branch analysis.md

## Contents
1. The six lenses
2. Evidence discipline
3. Frontmatter format (machine-read — exact)
4. Body template
5. Pattern ID rules

---

## 1. The six lenses

Apply each lens to the branch; skip a lens only when it genuinely yields
nothing, and say so ("No rework signals observed").

1. **Traceability** — classify every normalized requirement (`R1`, `R2`,
   ...) as `fulfilled`, `partial`, or `not fulfilled` based on what the
   diffs actually do, then map only `fulfilled` requirements to the
   commits and files that implement them. For `partial`, cite what exists
   but note what's missing rather than presenting the requirement as
   done. For `not fulfilled`, cite no code — a ticket line with no
   evidence in the diff isn't a mapping problem to paper over, it's the
   finding. Changes that serve no requirement go in a separate `unmapped`
   row with a one-line guess at why they exist (drive-by fix, formatting,
   rebase noise).
2. **Change anatomy** — which layers/directories the feature touched and
   in what order the commit sequence approached them (e.g. "migration →
   domain model → service → endpoint → tests"). Order is a pattern in
   itself when it recurs.
3. **Conventions** — naming, file placement, and pairing rules visible in
   the diff: how new files are named, where they live relative to what
   they extend, which files always change together (registration files,
   route tables, barrel exports, DI modules).
4. **Standard steps** — mechanical actions performed for every unit of
   work regardless of the feature: adding a migration, updating an OpenAPI
   spec, bumping a changelog, wiring a feature flag, registering a
   handler. These become the Standard steps section of that branch's
   patterns-research doc.
5. **Rework signals** — later commits that fix, revert, or reshape earlier
   ones in the same branch (look for "fix", "address review", "revert",
   or repeated edits to one file). Each signal is a candidate gotcha: the
   mistake plus what the fix reveals about the correct approach.
6. **Scope-local rules** — statements true only within one directory
   subtree ("everything under `src/api/` returns ProblemDetails on
   error"). These become path-scoped rule files, so record the narrowest
   glob that covers the evidence.

## 2. Evidence discipline

- Every claim cites at least one commit SHA (short form) and, where
  useful, file paths. A claim with no citation gets deleted at compile
  time, so cite as you write.
- Verify before asserting: if a claim rests on a diff that was truncated
  in `extract.json`, run `git show <sha> -- <path>` and confirm.
- Mark shaky claims with `confidence: low` in the frontmatter pattern
  entry; the compile step keeps them out of overview.md's Confirmed
  patterns table even if they recur.
- Quantify where cheap: "4 of 5 new endpoints added a validator" carries
  more compile-time weight than "endpoints usually add validators".

## 3. Frontmatter format (machine-read — exact)

`scripts/compile_index.py` parses this with a minimal reader. Keep exactly
this shape: two-space indentation, one `- id:` block per pattern, values on
one line.

```yaml
---
branch: feature/sso-login
ticket: https://dev.azure.com/org/proj/_workitems/edit/1234
studied: 2026-07-16
requirements: 4
patterns:
  - id: endpoint-adds-validator-and-spec
    scope: src/api/**
    claim: Every new endpoint lands with a validator and a matching *.spec.ts in the same commit.
    confidence: high
    evidence: [a1b2c3d, e4f5a6b]
  - id: migration-first-commit-order
    scope: repo
    claim: Schema migrations land in the first commit, before any code that uses them.
    confidence: medium
    evidence: [9f8e7d6]
---
```

Field rules: `id` is kebab-case and shared across branches (see §5);
`scope` is a glob or the literal `repo`; `claim` is one sentence;
`confidence` ∈ high/medium/low; `evidence` is a bracketed list of short
SHAs.

## 4. Body template

```markdown
# Analysis: <branch>

## Requirements studied
(R1..Rn, one line each, from requirements.md)

## Traceability
| Req | Status | Commits | Files | Notes |
|-----|--------|---------|-------|-------|
| R1  | fulfilled | a1b2c3d, e4f5a6b | src/api/auth/... | |
| R2  | partial | e4f5a6b | src/api/auth/... | validates input but doesn't audit-log failures yet |
| R3  | not fulfilled | | | no evidence in diff — may be scoped to a later branch |
| unmapped | — | 9f8e7d6 | .editorconfig | drive-by formatting |

## Change anatomy
(layers touched, commit order, 3–8 sentences)

## Conventions observed
(bullets, each with SHA/path citation)

## Standard steps observed
(bullets — the mechanical every-time actions)

## Rework signals
(bullets: mistake → fix → lesson, each citing both commits; or "none")

## Scope-local rule candidates
(bullets: glob → rule → evidence)

## Open questions
(things a human should confirm before these harden into guidance)
```

## 5. Pattern ID rules

- Before writing, list existing IDs: use the Grep tool for `id:` across
  `.pattern-mining/branches/*/analysis.md` and dedupe the matches — this
  works the same on every platform, unlike a shell `grep | sort -u` pipe.
- Reuse an existing ID when the observed pattern matches its claim in
  substance, even if wording differs — recurrence counting keys on the ID.
- Mint a new ID only for a genuinely new pattern; name it
  `<subject>-<behavior>` (e.g. `handler-registered-in-di-module`).
- Never reuse an ID for a contradicting observation. Record the
  contradiction as a new ID (e.g. `...-violated`) plus a note in Open
  questions; the compile step surfaces contradictions in overview.md.
