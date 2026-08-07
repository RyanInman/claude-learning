---
name: targeted-refactor
description: >-
  Refactor one specific function, method, or highlighted block of code: read and understand its
  current logic first, then write (or extend) a canonical test suite that pins down its existing
  behavior before any change is proposed, then simplify in small verified passes — one commit per
  pass, tests green after every single one — favoring readability over raw line-count reduction.
  Use whenever someone points at a single function/method/selection and says things like "simplify
  this function", "refactor UserService.validate", "this method is too complex, clean it up",
  "reduce the nesting in this", or highlights code and asks to make it more readable or
  maintainable. The non-negotiable Definition of Done: every original test plus the new
  characterization tests still passes — zero regressions, no exceptions. Do NOT use for broad
  "clean up my recent changes" sweeps across many files (use the simplify skill instead) or for
  applying an external audit or rule-review report's findings (use audit-refactor instead) — this
  skill is scoped to one named target at a time.
---

# Targeted Refactor

Refactor exactly one function, method, or highlighted block. The discipline that makes this safe:
**characterize the behavior with tests before changing anything, then change in small, individually
verified steps.** Skipping straight to "here's a cleaner version" is how refactors quietly become
rewrites — the model pattern-matches a nicer shape without confirming it preserves what the code
actually does today.

Scope check: one named target (a function, method, or a selection the user highlighted), not a
sweep across many files (that's the `simplify` skill) and not applying someone else's audit report
(that's `audit-refactor`).

## The workflow

### 0. Pin down the target
Get the exact file and line range or function/method name. If the name matches more than one
definition (overload, same name in multiple classes/files), ask which one before reading further.

### 1. Understand before touching anything
Read the whole function, not just the parts that look messy. Trace every branch, every caller,
every side effect (I/O, mutation, exceptions, globals). Write a short **Understanding** note and
share it before writing a single line of new code — this is the forcing function against jumping
straight to "cleaner code" without confirming what the current code does. If a caller always passes
a particular value in practice (a flag that's never false, an argument that's always the same
object), note it — it changes which simplifications are actually safe to make.

### 2. Characterize behavior with tests
Search for tests already covering this target before assuming there are none — grep the target's
name across common test locations (`test_*.py` / `*_test.py`, `*.test.ts` / `*.spec.ts`,
`__tests__/`, `*_test.go`, etc., adapted to the project's actual conventions).

- **Tests exist:** extend that same file/suite with cases for branches or edges it doesn't cover
  yet. Match its existing framework and style — don't introduce a second one.
- **No tests exist:** write a canonical suite from scratch — happy path, each branch, boundary
  values, error paths. Its job is to pin down what the code *actually does now*, not what it
  should do. If a correct-looking test would have to encode a bug to pass, write it that way anyway
  and flag the bug to the user as a separate finding — fixing it is a behavior change, not a
  simplification, and it's out of scope here.

Run the suite against the untouched original code. Every test must pass before any refactor begins.
If one doesn't, your understanding from step 1 is wrong somewhere — go back before proceeding.

### 3. Baseline signals (informational only)
Run the bundled script for an approximate complexity/nesting reading before you start:

```
python3 scripts/measure_complexity.py --file <path> --start <n> --end <n>
```

These numbers are heuristic — regex-based, not a real parser — so treat them as a directional
signal, never a gate. A lower number that reads worse is a worse outcome, full stop.

### 4. Plan the passes
Pick from these categories, in roughly this order since each tends to unlock the next. Skip any
that don't apply — this is a menu, not a checklist to exhaust:

1. **Reduce nesting** — guard clauses / early returns instead of nested if/else; flatten nested
   loops into helper functions.
2. **Extract functions** — pull out blocks that already have an implicit name (often marked by a
   comment explaining what they do) or that repeat elsewhere; one function, one job.
3. **Improve naming** — full words over abbreviations; boolean variables read as questions
   (`isValid`, `hasPermission`); boolean-returning functions start with `is`/`has`/`can`/`should`.
4. **Remove duplication** — parameterize near-duplicates; tolerate duplication across module
   boundaries if removing it would add worse coupling.
5. **Simplify conditionals** — named boolean variables for compound expressions; lookup tables
   instead of long if/else or switch chains.

### 5. Apply one pass at a time
For each planned pass:

1. Make only that one kind of change.
2. Run the full characterization suite plus any pre-existing tests touching this code. All green,
   or revert immediately — never carry a red pass forward into the next one.
3. Re-run `measure_complexity.py` and note the delta.
4. Re-read the result cold: would a senior engineer find this easier to follow than before? If a
   pass makes it shorter but harder to follow, revert it. Readability always outranks line count —
   that trade is never worth making.
5. Commit the pass by itself, with a message naming the specific kind of simplification (e.g.
   "extract validation logic from processOrder"). One pass per commit, so a regression introduced
   later is bisectable to exactly one change.

Stop when the remaining candidate passes would trade readability for line count, or when the
domain's inherent complexity is the floor (see Gotchas).

### 6. Definition of Done
Report this, don't just assert it:

- Every original test (pre-existing + new characterization tests) passes — state the count and
  include the actual run output/summary, not just a claim that it passed.
- Zero regressions — if anything went red at any point, name the pass that caused it and confirm it
  was reverted or fixed before moving on.
- The per-pass log described below.

## Report format

```
## Understanding
<what the code does, its inputs/outputs, side effects, callers>

## Characterization tests
<existing suite extended | new suite written> — <file> — <N> cases — all passing on original code

## Baseline
complexity ~<N> | max nesting <N> | lines <N>

## Passes
1. <pass> — <why> — complexity <a>→<b>, nesting <a>→<b> — tests: pass — <commit>
2. ...

## Definition of Done
- [x] <N>/<N> tests passing (pre-existing + characterization)
- [x] zero regressions
```

## Gotchas

- **A characterization test isn't a correctness test.** If the current code has a bug, the test
  should still capture what it does today, bug included. Flag the bug separately — don't fix it
  silently inside a "simplification," since that breaks the behavior-preserving guarantee this
  whole workflow depends on.
- **Don't over-decompose to chase a lower number.** Splitting one function into six two-line
  functions can lower a complexity score while making the logic harder to follow, because now the
  reader has to jump between six places to see one flow. If reading it end-to-end got harder, it's
  a regression no matter what the metric says.
- **If the target can't be tested without heavy mocking** — tightly coupled to a live database,
  network calls, global mutable state — say so up front and negotiate scope with the user rather
  than quietly skipping the characterization-test step. That step is the entire safety net the rest
  of the workflow leans on.
- **One kind of change per commit, always.** Resist folding a naming fix into the same commit as a
  nesting fix just because both are small. The granularity exists so any regression is bisectable
  to exactly one commit.
- **Some complexity belongs to the domain, not the code.** If a function is complex because the
  business rule it encodes is genuinely complex, don't force an artificially "simple" shape onto
  it — add a comment explaining the rule instead, and say so plainly in the report rather than
  claiming a simplification that didn't really happen.

## Scripts

- `scripts/measure_complexity.py --file <path> --start <N> --end <M>` — heuristic complexity
  estimate, max nesting depth, and line count for a file or line range. Stdlib-only Python, no
  dependencies. Used in step 3 (baseline) and step 5 (per-pass delta).
