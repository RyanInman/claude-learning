# Complexity Report: order_utils.py

## Summary

| Unit | Cyclomatic | Cognitive | Assessment |
|------|-----------|-----------|------------|
| can_ship | 4 | 3 | ✅ |
| can_ship_nested | 4 | 6 | ✅ |
| first_error | 4 | 4 | ✅ |
| total | 1 | 0 | ✅ |

All units are within safe thresholds (cyclomatic ≤ 10, cognitive ≤ 15). The interesting finding is the `can_ship` vs `can_ship_nested` pair: identical behavior and identical cyclomatic (4), but the nested version costs twice the cognitive effort (6 vs 3). Nesting, not decision count, is what makes `can_ship_nested` the hardest unit to follow here.

## can_ship_nested

**Cyclomatic: 4** — base 1 + 3 if
**Cognitive: 6** — 3 if + nesting penalties (+1, +2)

```python
def can_ship_nested(order):
    if order is not None:        # CC +1 | Cog +1
        if order.items:          # CC +1 | Cog +1, nesting +1
            if order.paid:       # CC +1 | Cog +1, nesting +2
                return True
    return False
```

Hardest unit in the file to follow. Each nested `if` forces the reader to hold the enclosing conditions in mind, and the final `return False` sits three structural levels away from the checks it answers — you must mentally unwind the whole pyramid to see which failures land there. The cyclomatic score (4) is identical to `can_ship` because both have the same four execution paths; the cognitive gap (6 vs 3) is pure nesting cost. A cheap rewrite already exists in this same file:

```python
def can_ship(order):                 # identical behavior
    if order is None: return False   # CC +1 | Cog +1
    if not order.items: return False # CC +1 | Cog +1
    if not order.paid: return False  # CC +1 | Cog +1
    return True
# Cyclomatic: 4    Cognitive: 3 — same paths, half the reading cost
```

## first_error

**Cyclomatic: 4** — base 1 + 1 for + 1 if + 1 `and`
**Cognitive: 4** — 1 for + 1 if + 1 `and` + nesting penalty (+1)

```python
def first_error(rows):
    for r in rows:                                    # CC +1 | Cog +1
        if r.status == "error" and r.severity > 3:    # CC +1 if, +1 and | Cog +1 if, +1 and, nesting +1
            return r
    return None
```

A loop with one nested compound condition — the standard search-and-early-return shape, easy to follow despite the scores matching `can_ship`'s cyclomatic. The `if` takes a +1 nesting penalty for sitting inside the loop, and the `and` adds +1 to both metrics (note: SonarQube would count a run of like operators as +1 total, so its cognitive score here would be the same 4, but longer chains would diverge). No refactor needed.

## can_ship

**Cyclomatic: 4** — base 1 + 3 if
**Cognitive: 3** — 3 if, no nesting penalties

```python
def can_ship(order):
    if order is None:      # CC +1 | Cog +1
        return False
    if not order.items:    # CC +1 | Cog +1
        return False
    if not order.paid:     # CC +1 | Cog +1
        return False
    return True
```

Guard-clause style: each check is read once, discharged by an early `return`, and forgotten — no condition context carries forward, so no nesting penalties accrue. Same four test paths as `can_ship_nested` (both need the same test cases), but the flat shape halves the reading cost. This is the canonical guard-vs-nesting divergence: cyclomatic measures paths and cannot tell the two apart; only cognitive captures why this version is easier.

## total

Cyclomatic 1, cognitive 0 — a single `sum` over a generator expression (comprehensions score 0 for both metrics; it contains no filter or boolean logic). Trivial, no explanation needed.
