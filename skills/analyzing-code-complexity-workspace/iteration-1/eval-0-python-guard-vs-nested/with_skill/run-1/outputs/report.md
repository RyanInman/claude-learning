# Complexity Report: order_utils.py

## Summary

| Unit | Cyclomatic | Cognitive | Assessment |
|------|-----------|-----------|------------|
| can_ship | 4 | 3 | ✅ |
| can_ship_nested | 4 | 6 | ✅ |
| first_error | 4 | 4 | ✅ |
| total | 1 | 0 | ✅ |

All units fall within healthy thresholds (cyclomatic ≤ 10, cognitive ≤ 15). The most instructive finding is `can_ship` vs `can_ship_nested`: identical behavior and identical cyclomatic complexity, but the nested version costs twice the cognitive effort. `can_ship_nested` is the hardest unit to follow in the file.

Convention note: boolean operators are counted per operator for both metrics here; SonarQube's cognitive spec counts a sequence of like operators as +1 total, so its numbers may differ slightly.

## can_ship_nested

**Cyclomatic: 4** — base 1 + 3 `if`
**Cognitive: 6** — 3 `if` + nesting penalties (+1, +2)

Hardest function in the file to read, despite doing exactly what `can_ship` does. Each successive `if` sits one level deeper, so the reader must hold every enclosing condition in mind to know when `return True` is reachable — that accumulating context is what the nesting penalty measures. The scores diverge from `can_ship` purely because of structure, not logic:

```python
def can_ship_nested(order):
    if order is not None:        # +1
        if order.items:          # +1, nesting +1
            if order.paid:       # +1, nesting +2
                return True
    return False
# Cyclomatic: 4    Cognitive: 6
```

The cheap rewrite already exists in this file: `can_ship` is the guard-clause version of this exact function (cyclomatic 4, cognitive 3). Delete `can_ship_nested` or replace its body with the guard-clause form.

## first_error

**Cyclomatic: 4** — base 1 + 1 `for` + 1 `if` + 1 `and`
**Cognitive: 4** — 1 `for` + 1 `if` (+1 nesting) + 1 `and`

Easy to follow: a single loop with one compound condition and an early return on first match. The `if` picks up a +1 nesting penalty for sitting inside the loop, and the `and` adds one to each metric, but the flow is linear scan-and-exit. No action needed.

## can_ship

**Cyclomatic: 4** — base 1 + 3 `if`
**Cognitive: 3** — 3 `if`, no nesting penalties

Same decision count and same four execution paths as `can_ship_nested`, but flat. Each guard clause is read once, dismissed, and forgotten — early returns carry no cognitive charge and nothing nests, so the reader never tracks more than one condition at a time. This is the pattern to prefer.
