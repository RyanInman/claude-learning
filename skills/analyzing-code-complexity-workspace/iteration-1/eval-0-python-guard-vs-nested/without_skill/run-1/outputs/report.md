# Complexity Analysis: order_utils.py

File: `/Users/admin/claude-learning/skills/analyzing-code-complexity/evals/files/order_utils.py` (4 functions, 27 lines)

## Summary Table

| Function | Cyclomatic | Cognitive | Max nesting | Verdict |
|---|---|---|---|---|
| `can_ship` | 4 | 3 | 1 | Easy |
| `can_ship_nested` | 4 | 6 | 3 | **Hardest** |
| `first_error` | 4 | 4 | 2 | Easy-moderate |
| `total` | 2 | 0 | 1 | Trivial |

Metric notes: cyclomatic = decision points + 1 (each `if`, `for`, boolean operator). Cognitive follows the SonarSource model: +1 per control structure, +1 extra per level of nesting, +1 per boolean-operator sequence.

## Ranking: hardest to easiest

### 1. `can_ship_nested` (lines 11-16) - hardest

```python
def can_ship_nested(order):
    if order is not None:
        if order.items:
            if order.paid:
                return True
    return False
```

- Cyclomatic 4, cognitive 6, nesting depth 3.
- Same decision count as `can_ship`, but nesting doubles cognitive load. This is the key finding: **cyclomatic complexity is identical (4 vs 4) yet the nested version is measurably harder** because each nested `if` forces the reader to hold the enclosing conditions in working memory.
- Single `return False` at line 16 serves three distinct failure paths (no order, no items, unpaid). To answer "why did this return False?" the reader must mentally invert all three conditions.
- The success path is buried at maximum depth; failure paths are implicit (fall-through), not explicit.

### 2. `first_error` (lines 19-23)

```python
for r in rows:
    if r.status == "error" and r.severity > 3:
        return r
return None
```

- Cyclomatic 4 (`for` + `if` + `and`), cognitive 4, nesting depth 2.
- Follows the standard find-first idiom (loop, test, early return, sentinel), so it reads easily despite the numbers. Complexity here comes from the compound predicate, not structure.
- Minor friction: single-letter names `r`/`rows` and magic number `3` (why severity > 3?) push understanding cost onto the reader.

### 3. `can_ship` (lines 1-8)

- Cyclomatic 4, cognitive 3, nesting depth 1.
- Guard-clause style: each precondition checked and exited flat. Every `return False` maps to exactly one named reason. Reads top-to-bottom with no state to carry.
- This is the readable twin of `can_ship_nested` and the shape the nested version should be refactored to.

### 4. `total` (lines 26-27)

- Cyclomatic 2 (generator expression), cognitive 0. One-line sum, nothing to follow.

## Why the hardest one is hard

`can_ship` and `can_ship_nested` implement identical logic and have identical cyclomatic complexity, so decision-count metrics alone rank them equal. What separates them:

1. **Nesting = working memory.** At line 14 the reader tracks two live assumptions (`order is not None`, `order.items` truthy). Guard clauses discharge each assumption immediately.
2. **Merged failure paths.** One `return False` for three causes destroys the 1:1 mapping between code path and business reason, which hurts debugging.
3. **Inverted happy path.** Success is the deepest, last-reached statement instead of the natural conclusion.

## Recommendation

Replace `can_ship_nested` with the guard-clause form (it is an exact duplicate of `can_ship`; keeping both invites drift). Optionally name `first_error`'s threshold: `SEVERITY_THRESHOLD = 3`.
