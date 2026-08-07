# Complexity Report: `validate(user)` snippet

## Summary

| Unit | Cyclomatic | Cognitive | Assessment |
|------|-----------|-----------|------------|
| validate | 4 | 3 | ✅ |

## validate

**Cyclomatic: 4** — base 1 + 2 if + 1 &&
**Cognitive: 3** — 2 if + 1 && (no nesting penalties)

Both scores are low and close together, which means the function reads about as easily as it tests. The `if (!user)` guard clause with early return is exactly the pattern that keeps cognitive complexity down: it adds a path but no nesting, so the reader never has to hold an "else" branch in mind. Both `if` statements sit at top level, so no nesting penalties apply, and the `.map(t => t.toLowerCase())` lambda contains no branching, so it adds nothing.

**Verdict: fine to leave as is.** Thresholds for concern are cyclomatic > 10 or cognitive > 15; this function is at 4/3. Refactoring it for complexity would gain nothing.

One note unrelated to complexity: if `user.age > 18 && user.consent` passes but `user.tags` is missing, `.map` throws. That's a robustness gap, not a complexity one — the metrics stay the same either way.
