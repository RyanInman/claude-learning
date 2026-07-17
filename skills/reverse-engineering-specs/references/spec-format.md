# Writing spec.md

## Contents
1. Exact template
2. Field rules
3. Acceptance criteria style
4. Worked example

---

## 1. Exact template

Use this shape for every `spec.md`, in both Snapshot and Diff mode:

```markdown
# Spec: <target>

## Overview
(2-4 sentences: what this component does and why it exists, inferred from
its role in the codebase -- callers, directory placement, imports. Diff
mode: what the change adds, in the same 2-4 sentences.)

## Requirements
| ID | Requirement | Confidence | Evidence |
|----|-------------|------------|----------|
| R1 | ... | high | path:line |
| R2 | ... | medium | path:line, path:line |

## Acceptance criteria

### R1: <requirement, restated>
- Given ..., when ..., then ... (evidence: path:line or test name)
- Given ..., when ..., then ...

### R2: <requirement, restated>
- Given ..., when ..., then ...

## Out of scope / assumptions
(bullets: confident negative claims -- things the code observably does NOT
handle, e.g. "no rate limiting on this endpoint" -- distinct from Open
Questions below because these are asserted, not uncertain.)

## Open questions
(bullets: low-confidence inferences, contradictions between code and
tests, or intent a human should confirm before this spec is treated as
ground truth.)
```

## 2. Field rules

- `ID` — `R1`, `R2`, ... in the order the lenses surfaced them; stable
  within one spec, not shared across specs (unlike
  `mining-implementation-patterns`'s cross-branch pattern IDs — a spec
  describes one target, not a corpus).
- `Requirement` — one sentence, stated as an observable contract or
  behavior ("rejects a negative `amount`"), never an implementation detail
  ("uses a `for` loop"). A future reader should be able to test the
  sentence without reading the code.
- `Confidence` — `high` / `medium` / `low`, per
  `references/inference-guide.md` §3. Every requirement gets one; the
  compile-free nature of this skill means there's no second pass to catch
  a missing field, so set it as you write the row.
- `Evidence` — comma-separated `path:line` citations from `scan.json`, or a
  test name (e.g. `OktaValidator.spec.ts: "rejects expired tokens"`). Diff
  mode also cites the commit SHA in the Overview or a requirement's prose
  when it clarifies which change introduced the behavior.

## 3. Acceptance criteria style

- Given/When/Then, one behavior per bullet — not one bullet trying to cover
  every branch of a requirement. Split multi-branch requirements into
  multiple AC bullets under the same `### R#` heading.
- Every AC bullet is independently testable: a reader should be able to
  write a test from the sentence alone, without opening the code.
- Only write AC for `high`/`medium` confidence requirements. A `low`
  confidence row still appears in the Requirements table (per
  `inference-guide.md` §3) but its uncertainty belongs in Open Questions,
  not as a guessed AC that reads as more certain than it is.

## 4. Worked example

**Input:** Snapshot mode on `src/api/auth/OktaValidator.py`, which has a
`validate_token(token)` function that raises `ExpiredTokenError` when
`token.exp < now()`, raises `InvalidIssuerError` when the issuer doesn't
match config, and is covered by `OktaValidator.spec.ts`.

**Output (excerpt):**

```markdown
## Requirements
| ID | Requirement | Confidence | Evidence |
|----|-------------|------------|----------|
| R1 | Rejects an expired token | high | src/api/auth/OktaValidator.py:42, OktaValidator.spec.ts |
| R2 | Rejects a token from an unrecognized issuer | high | src/api/auth/OktaValidator.py:47 |

## Acceptance criteria

### R1: Rejects an expired token
- Given a token whose `exp` claim is in the past, when `validate_token` is
  called, then it raises `ExpiredTokenError` (evidence: OktaValidator.py:42,
  OktaValidator.spec.ts: "rejects expired tokens").

### R2: Rejects a token from an unrecognized issuer
- Given a token whose issuer does not match configured Okta issuer, when
  `validate_token` is called, then it raises `InvalidIssuerError` (evidence:
  OktaValidator.py:47).

## Open questions
- No test found for R2 (no `paired_test` for OktaValidator.py covering the
  issuer check) — confirm this is intentional before relying on it.
```
