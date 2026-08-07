# Complexity Report: validate (inline snippet)

## Summary

| Unit | Cyclomatic | Cognitive | Assessment |
|------|-----------|-----------|------------|
| validate | 4 | 3 | ✅ |

## validate

**Cyclomatic: 4** — base 1 + 2 if + 1 &&
**Cognitive: 3** — 2 if + 1 && (no nesting penalties)

```javascript
function validate(user) {
  if (!user) return null;                        // CC +1 | Cog +1 (guard clause, early return itself free)
  if (user.age > 18 && user.consent) {           // CC +1 if, +1 && | Cog +1 if, +1 &&
    return user.tags.map(t => t.toLowerCase());  // lambda has no branching — 0
  }
  return null;
}
```

Both `if`s sit at top level of the function, so no nesting penalties apply — the guard-clause style keeps cognitive low. The lambda in `.map()` contains no branching and adds nothing. Scores barely diverge (4 vs 3): four independent paths to test, but the flow reads linearly.

**Verdict: fine to leave as is.** Well under thresholds (cyclomatic ≤ 10, cognitive ≤ 15). Refactoring for complexity would be over-engineering.

One non-complexity note: if `user.tags` can be undefined when age/consent pass, `.map` throws — a correctness gap, not a complexity one.
