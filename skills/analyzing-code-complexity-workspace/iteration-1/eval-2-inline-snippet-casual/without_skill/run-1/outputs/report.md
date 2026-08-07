# Complexity assessment

Code is trivially complex, but has one latent bug worth noting.

**Complexity: low.**
- Cyclomatic complexity: 3 (two `if` branches + `&&`). Threshold for concern is usually ~10.
- 7 lines, single responsibility, no nesting beyond one level. No refactor needed.

**Not fine as-is, though — one real issue:**
- `user.tags.map(...)` throws if `tags` is missing/null. `user` is guarded, `tags` isn't. Fix: `(user.tags ?? []).map(...)` or add `Array.isArray(user.tags)` to the condition.

**Judgment calls to confirm, not bugs:**
- `age > 18` excludes exactly 18. If 18 counts as adult, use `>= 18`.
- Returns `null` on failure, array on success — callers must null-check. Returning `[]` instead often simplifies call sites. Fine either way if intentional.
- Fn named `validate` but it transforms (lowercases tags). Naming mismatch; `getNormalizedTags` or similar fits better. Cosmetic.

Verdict: complexity fine, leave structure alone. Add `tags` guard, confirm the 18 boundary.
