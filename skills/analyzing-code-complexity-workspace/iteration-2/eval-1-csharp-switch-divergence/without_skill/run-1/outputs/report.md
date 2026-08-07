# Complexity Report: PaymentService.cs

File: `/Users/admin/claude-learning/skills/analyzing-code-complexity/evals/files/PaymentService.cs`

Metrics: cyclomatic complexity per McCabe (1 + decision points), cognitive complexity per SonarSource spec (increments for control-flow breaks, nesting penalties, boolean operator sequences; `switch` counts +1 regardless of case count).

## Summary Table

| Method | Cyclomatic | Cognitive | Notes |
|---|---:|---:|---|
| `StatusLabel(int)` | 6 | 1 | Flat switch: high cyclomatic, trivial to read |
| `Charge(Order)` | 3 | 2 | Two catch clauses |
| `Discount(Customer)` | 3 | 2 | Ternary + `&&` |
| `Process(List<Order>)` | 6 | 12 | Nesting drives cognitive score up |
| `Retry(Order)` | 1 | 0 | Straight-line |
| `Log(Exception)` | 1 | 0 | Straight-line |
| `Ship(Item)` | 1 | 0 | Straight-line |
| `Notify(Order, Item)` | 1 | 0 | Straight-line |
| **Total** | **22** | **17** | |

## Per-Method Breakdown

### StatusLabel(int code) — lines 8-19
- Cyclomatic: **6** = base 1 + 5 `case` labels (`default` adds nothing).
- Cognitive: **1** = `switch` counts +1 total, no nesting.
- Divergence: highest cyclomatic in file, lowest non-zero cognitive. Flat value-mapping switch; cyclomatic overstates difficulty. No refactor needed; a dictionary lookup would drop cyclomatic to 1 if a metric gate matters.

### Charge(Order o) — lines 21-36
- Cyclomatic: **3** = base 1 + 2 `catch` clauses.
- Cognitive: **2** = +1 per `catch` (nesting 0); `try` and `throw` add nothing.
- Assessment: simple error-handling shape, fine as is.

### Discount(Customer c) — lines 38-41
- Cyclomatic: **3** = base 1 + ternary `?:` + `&&`.
- Cognitive: **2** = +1 ternary (nesting 0) + 1 for the `&&` sequence.
- Assessment: single readable expression, fine as is.

### Process(List<Order> orders) — lines 43-62
- Cyclomatic: **6** = base 1 + outer `foreach` + `if (o.Paid)` + inner `foreach` + `if (...)` + `||` (`else` adds nothing).
- Cognitive: **12**
  - outer `foreach` (nesting 0): +1
  - `if (o.Paid)` (nesting 1): +2
  - inner `foreach` (nesting 2): +3
  - `if (i.InStock || i.Backorderable)` (nesting 3): +4
  - `||` sequence: +1
  - `else`: +1
- Divergence: same cyclomatic as `StatusLabel` (6) but 12x its cognitive score. Four nesting levels drive the cost. Refactor candidates: guard clause `if (!o.Paid) continue;` removes one level (cognitive 12 -> 8); extracting the inner item loop into a `ShipOrNotify` helper flattens further.

### Retry / Log / Ship / Notify — lines 64-67
- Cyclomatic: **1** each, Cognitive: **0** each. No branching.

## Key Finding

Cyclomatic and cognitive complexity disagree sharply here. `StatusLabel` and `Process` tie at cyclomatic 6, but cognitive complexity separates them: 1 vs 12. Cyclomatic counts paths, so a flat case-mapping switch looks as "complex" as deeply nested loops. Cognitive complexity penalizes nesting and discounts flat switches, matching human reading effort. Prioritize `Process` for refactoring; leave `StatusLabel` alone.
