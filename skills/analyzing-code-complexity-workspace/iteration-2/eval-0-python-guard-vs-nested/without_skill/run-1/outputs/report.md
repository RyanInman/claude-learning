# Complexity Analysis: `order_utils.py`

File: `/Users/admin/claude-learning/skills/analyzing-code-complexity/evals/files/order_utils.py` (4 functions, 27 lines)

## Metrics Summary

| Function | Cyclomatic Complexity | Cognitive Complexity | Max Nesting Depth | Verdict |
|---|---|---|---|---|
| `can_ship` | 4 | 3 | 1 | Easy |
| `can_ship_nested` | 4 | 6 | 3 | **Hardest to follow** |
| `first_error` | 4 | 3 | 2 | Easy-moderate |
| `total` | 2 | 1 | 1 | Trivial |

Notes on method: cyclomatic complexity counts branch points + 1 (each `if`, loop, and boolean operator). Cognitive complexity (Sonar-style) additionally penalizes each level of nesting, which is what makes it a better proxy for "hard to follow."

## Function-by-Function

### `can_ship` (lines 1-8) — easy
Three guard clauses, each at depth 1: `order is None`, empty `items`, unpaid. Cyclomatic 4, but cognitive only 3 because nothing nests. Each condition is independently readable as "reject if X"; a reader never carries more than one condition in their head at a time. Early returns mean the happy path is the last line.

### `can_ship_nested` (lines 11-16) — hardest to follow
Logically identical to `can_ship` (same cyclomatic complexity, 4), but structured as three nested `if`s reaching depth 3. Cognitive complexity doubles to 6: each `if` costs 1 plus its nesting depth (1 + 2 + 3). Why it is harder:

- The reader must mentally accumulate the conjunction `order is not None AND order.items AND order.paid` across three indentation levels before reaching `return True`.
- The failure path is implicit: falling out of any `if` silently reaches the shared `return False` on line 16, so understanding "when does this return False" requires reasoning about all three ways of not entering a block.
- Adding a fourth condition deepens nesting further; the guard-clause version stays flat.

This pair is the file's clearest lesson: identical cyclomatic complexity can hide very different cognitive load. Nesting depth, not branch count, is what makes `can_ship_nested` harder.

### `first_error` (lines 19-23) — easy to moderate
Cyclomatic 4 (loop + `if` + `and`), nesting depth 2 (an `if` inside a `for`). This is idiomatic linear-search shape, so the pattern is instantly recognizable. The only cognitive costs are the compound condition (`status == "error" and severity > 3`) and the magic number `3`, which encodes an unexplained severity threshold. Naming the threshold (`SEVERITY_THRESHOLD = 3`) or extracting the predicate would remove the remaining friction. Could also be written as `next((r for r in rows if ...), None)`, though the explicit loop is arguably clearer.

### `total` (lines 26-27) — trivial
Single expression with a generator; cyclomatic 2 only because of the comprehension's implicit loop. Nothing to simplify.

## Recommendations

1. Replace `can_ship_nested` with the guard-clause form (`can_ship` already demonstrates it); if both exist as alternatives, delete the nested variant. This is the only meaningful complexity reduction available in the file.
2. In `first_error`, name the severity threshold to make the compound condition self-documenting.
3. `can_ship` could optionally compress to `return order is not None and bool(order.items) and order.paid`, but the guard-clause form is already at minimal cognitive load and arguably reads better; no change needed.

## Key Takeaway

The hardest function here, `can_ship_nested`, is not the one with the most branches; every non-trivial function ties at cyclomatic 4. It is hardest because of nesting: depth-3 indentation forces the reader to track accumulated state, and its single fall-through `return False` hides three distinct failure reasons. Guard clauses with early returns (`can_ship`) express the same logic at half the cognitive complexity.
