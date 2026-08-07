# Complexity Assessment

## Snippet

```js
function validate(user) {
  if (!user) return null;
  if (user.age > 18 && user.consent) {
    return user.tags.map(t => t.toLowerCase());
  }
  return null;
}
```

## Complexity: low

- Cyclomatic complexity ~4 (guard, compound condition, implicit fallthrough)
- Nesting depth 1, 5 lines, single responsibility per branch
- No metric flags this fn. Structure needs no refactor.

## Fine to leave as is? Not quite

Issues are correctness/clarity, not complexity:

1. **Bug: `user.tags.map` can throw.** `user` guarded, `user.tags` not. Adult user with consent but missing `tags` -> `TypeError: Cannot read properties of undefined (reading 'map')`.
2. **Misleading name.** `validate` implies boolean/error result; fn transforms data (returns lowercased tags). Callers can't distinguish "invalid user" from "valid user, empty result" -- both return `null`.
3. **Boundary: `age > 18` excludes exactly 18.** If intent is "18 and over", use `>= 18`. Confirm requirement.

## Minimal fix (complexity unchanged)

```js
function getNormalizedTags(user) {
  if (!user || user.age < 18 || !user.consent) return null;
  return (user.tags ?? []).map(t => t.toLowerCase());
}
```

## Verdict

Complexity fine. Fix `tags` guard (real bug), confirm age boundary, rename if call sites cheap to update.
