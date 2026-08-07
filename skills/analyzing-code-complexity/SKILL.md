---
name: analyzing-code-complexity
description: Scores code for cyclomatic complexity and cognitive complexity, producing a per-method report with both scores and explanations. Use whenever the user asks about code complexity, complexity scores or metrics, "how complex is this code", readability/maintainability measurement, nesting depth concerns, or wants to know which functions are hardest to follow — even if they don't name a specific metric. Do NOT use for general code review, refactoring without metrics, or performance profiling.
---

# Analyzing Code Complexity

Score every named unit (method, function, property with logic) in the given code with two metrics, then report. **Cyclomatic** counts independent execution paths (how hard to test); **cognitive** measures effort to follow the flow (how hard to read). They answer different questions and often diverge — that divergence is the most useful finding, so never report one without the other.

## Scoring rules

Score each unit independently, walking the code line by line rather than estimating — one miscounted score undermines trust in the whole report.

**Cyclomatic complexity** — start at 1, then +1 for each:
- `if`, `else if` (NOT `else`)
- each loop (`for`, `while`, `do`, `foreach`)
- each `case` in a switch (NOT `default`)
- each `&&`, `||`
- each ternary `?:`
- each `catch`

Nothing for: `else`, `finally`, `return`/`break`/`continue`, method calls, assignments.

**Cognitive complexity** — start at 0:
- +1 for each flow-break: `if`, `else if`, `else`, ternary, switch (the switch itself, not each case), each loop, `catch`, `goto`/labeled break
- +1 for each `&&`, `||`
- **Nesting penalty**: each flow-break structure nested inside another gets an extra +N, where N = nesting depth (1st level +1, 2nd level +2, ...). Boolean operators and `else` take no nesting penalty.

Nothing for: early `return` (guard clauses), linear code, method calls. This is why guard clauses score lower than nested equivalents — same paths, less nesting.

For worked examples, edge cases (lambdas, recursion, switch expressions, comprehensions), and threshold rationale, read `references/scoring-rules.md`. Read it whenever nesting exceeds 2 levels, a lambda or closure branches, or a construct is unclear. Tool conventions vary across linters. This reference pins the convention this skill uses.

## Report structure

Use this exact template:

```markdown
# Complexity Report: <file or code description>

## Summary

| Unit | Cyclomatic | Cognitive | Assessment |
|------|-----------|-----------|------------|
| ClassName.methodName | 4 | 7 | ⚠️ Refactor candidate |

## <ClassName.methodName>

**Cyclomatic: N** — <one-line breakdown, e.g. "base 1 + 2 if + 1 && ">
**Cognitive: N** — <one-line breakdown, e.g. "2 if + 1 && + nesting penalties (+1, +2)">

<annotated code block — see "Code examples in per-unit sections">

<2-4 sentence explainer: why this score, what makes it hard/easy to follow, and — if the two scores diverge — why.>
```

The summary table lists **every** named unit, trivial ones included — a getter's 1/0 row is what lets the reader trust the table is complete. Per-unit sections cover only units that score cyclomatic > 2 or cognitive > 1. List these sections by cognitive score, highest first. A trivial unit gets no section — its table row says everything.

Assessment column: ✅ (cyclomatic ≤ 10 and cognitive ≤ 15), ⚠️ Refactor candidate (either above), 🔴 High risk (cyclomatic > 20 or cognitive > 30).

## Code examples in per-unit sections

Each per-unit section shows the code it scored, annotated with per-line increments (`// CC +1 | Cog +1, nesting +2`). The annotated code is the evidence — it lets the reader verify every increment instead of trusting the breakdown.

- **Unit fits in ~15 lines**: show it whole, annotated.
- **Larger**: show a condensed fragment preserving what drives the score (the nesting skeleton, the compound conditions), eliding straight-line bodies with `...`. The reader needs the shape, not every statement.
- **A cheap rewrite exists** (guard clause, extraction): also show the rewrite (≤ 10 lines) with its new scores, proving the improvement.

## Gotchas

- `else` counts for cognitive (+1) but never for cyclomatic — the most common miscount.
- Switch: cyclomatic charges per `case`; cognitive charges +1 for the whole switch. A big flat switch is many-test-paths but low reading cost — say so rather than flagging it for refactor.
- Nesting depth counts *enclosing structures*, not braces — a method body is depth 0, so a top-level `if` takes no penalty.
- Lambda and local-function contents count toward the enclosing method, unless `references/scoring-rules.md` says otherwise for that construct.
- If the input has no named units (a loose script), treat the whole script as one unit named after the file.
