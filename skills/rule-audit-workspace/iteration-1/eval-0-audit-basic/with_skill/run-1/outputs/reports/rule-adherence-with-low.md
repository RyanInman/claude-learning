# Rule Adherence Report
Mode: audit · Rules: 3 · Files reviewed: 4 · Findings: 5 · Suppressed (<90% conf): 0 · Min impact: LOW (excluded 0)

## Summary (ranked by impact, then risk)
| # | File | Rule | Impact | Risk | Conf | Issue |
|---|------|------|--------|------|------|-------|
| 1 | src/api/handler.ts | api.md | HIGH | HIGH | 100% | Unvalidated request body written to DB |
| 2 | src/utils/format.ts | global.md | MEDIUM | HIGH | 100% | Variable declared with `var` instead of `const`/`let` |
| 3 | src/ui/Button.tsx | ui.md | MEDIUM | MEDIUM | 95% | Inline hex color literals used instead of theme tokens |
| 4 | src/api/handler.ts | global.md | LOW | HIGH | 100% | console.log in committed code |
| 5 | src/utils/format.ts | global.md | LOW | HIGH | 100% | console.log in committed code |

## Findings by file
### src/api/handler.ts
#### [HIGH impact / HIGH risk · 100% conf] Unvalidated request body written to DB
- Rule: `.claude/rules/api.md` → "Validate every handler's request body against a schema before using it. Never pass `req.body` straight into a database call."
- Issue: req.body passed directly to db.user.create without schema validation.

  Current (`src/api/handler.ts:6`):
  ```ts
  const body = req.body;
  return res.json(await db.user.create({ data: body }));
  ```
  Suggested fix:
  ```ts
  const parsed = userSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: "invalid" });
  return res.json(await db.user.create({ data: parsed.data }));
  ```

#### [LOW impact / HIGH risk · 100% conf] console.log in committed code
- Rule: `.claude/rules/global.md` → "No `console.log` in committed code; use the project logger instead."
- Issue: console.log used instead of project logger.

  Current (`src/api/handler.ts:4`):
  ```ts
  console.log("creating user", req.body);
  ```
  Suggested fix:
  ```ts
  logger.info("creating user", req.body);
  ```

### src/ui/Button.tsx
#### [MEDIUM impact / MEDIUM risk · 95% conf] Inline hex color literals used instead of theme tokens
- Rule: `.claude/rules/ui.md` → "No inline hex color literals in components; use theme tokens from `theme.ts`."
- Issue: The button component uses hardcoded hex color values #3b82f6 and #ffffff directly in the style prop instead of referencing theme tokens.

  Current (`src/ui/Button.tsx:3`):
  ```tsx
  <button style={{ background: "#3b82f6", color: "#ffffff" }}>{label}</button>
  ```
  Suggested fix:
  ```tsx
  const buttonStyle = { background: theme.colors.primary, color: theme.colors.text };
  return <button style={buttonStyle}>{label}</button>;
  ```

### src/utils/format.ts
#### [MEDIUM impact / HIGH risk · 100% conf] Variable declared with `var` instead of `const`/`let`
- Rule: `.claude/rules/global.md` → "Use `const`/`let`, never `var`."
- Issue: Variable `out` is declared with `var` which is not allowed.

  Current (`src/utils/format.ts:2`):
  ```ts
  var out = n.toFixed(2);
  ```
  Suggested fix:
  ```ts
  const out = n.toFixed(2);
  ```

#### [LOW impact / HIGH risk · 100% conf] console.log in committed code
- Rule: `.claude/rules/global.md` → "No `console.log` in committed code; use the project logger instead."
- Issue: console.log is used directly instead of the project logger.

  Current (`src/utils/format.ts:3`):
  ```ts
  console.log("formatted", out);
  ```
  Suggested fix: Replace console.log with the project logger.

## Clean files (no violations)
- src/api/profile.ts
