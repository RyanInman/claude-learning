# Rule Adherence Report
Mode: audit · Rules: 4 · Files reviewed: 6 · Findings: 7 · Suppressed (<90% conf): 0 · Min impact: MEDIUM (excluded 1)

## Summary (ranked by impact, then risk)
| # | File | Rule | Impact | Risk | Conf | Issue |
|---|------|------|--------|------|------|-------|
| 1 | src/api/users.ts | api.md | HIGH | HIGH | 92% | Query parameter used without validation |
| 2 | src/api/users.ts | api.md | HIGH | HIGH | 100% | SQL built with string interpolation |
| 3 | src/api/users.ts | global.md | MEDIUM | HIGH | 95% | Function parameters implicitly typed as any |
| 4 | src/components/Card.tsx | global.md | MEDIUM | HIGH | 98% | Function parameter typed as 'any' |
| 5 | src/utils/math.ts | global.md | MEDIUM | HIGH | 98% | Variable declared with var instead of const/let |
| 6 | src/utils/math.ts | utils.md | MEDIUM | HIGH | 99% | console.log used in utility function |
| 7 | src/components/Card.tsx | components.md | MEDIUM | MEDIUM | 95% | Inline hex color literal in style |

## Findings by file
### src/api/users.ts
#### [HIGH impact / HIGH risk · 92% conf] Query parameter used without validation
- Rule: `.claude/rules/api.md` → "Validate every handler's request body against a schema before use."
- Issue: req.query.name is used directly without schema validation, allowing potentially malformed input into the query.

  Current (`src/api/users.ts:5`):
  ```ts
  const rows = await db.query(`SELECT * FROM users WHERE name = '${req.query.name}'`);
  ```
  Suggested fix:
  ```ts
  const parsed = userQuerySchema.safeParse(req.query);
  if (!parsed.success) return res.status(400).json({ error: "invalid" });
  const rows = await db.query("SELECT * FROM users WHERE name = $1", [parsed.data.name]);
  ```

#### [HIGH impact / HIGH risk · 100% conf] SQL built with string interpolation
- Rule: `.claude/rules/api.md` → "Never build SQL by string interpolation; use parameterized queries."
- Issue: req.query.name is interpolated directly into a SQL string, creating a SQL injection vulnerability.

  Current (`src/api/users.ts:5`):
  ```ts
  const rows = await db.query(`SELECT * FROM users WHERE name = '${req.query.name}'`);
  ```
  Suggested fix:
  ```ts
  const rows = await db.query("SELECT * FROM users WHERE name = $1", [req.query.name]);
  ```

#### [MEDIUM impact / HIGH risk · 95% conf] Function parameters implicitly typed as any
- Rule: `.claude/rules/global.md` → "No `any` type; give every value a concrete type."
- Issue: Parameters req and res are not explicitly typed, falling back to implicit any.

  Current (`src/api/users.ts:3`):
  ```ts
  export async function findUser(req, res) {
  ```
  Suggested fix:
  ```ts
  export async function findUser(req: Request, res: Response) {
  ```

### src/components/Card.tsx
#### [MEDIUM impact / HIGH risk · 98% conf] Function parameter typed as 'any'
- Rule: `.claude/rules/global.md` → "No `any` type; give every value a concrete type."
- Issue: props parameter is typed as 'any' instead of a concrete type.

  Current (`src/components/Card.tsx:1`):
  ```tsx
  export function Card(props: any) {
  ```
  Suggested fix:
  ```tsx
  export function Card(props: { children: React.ReactNode }) {
  ```

#### [MEDIUM impact / MEDIUM risk · 95% conf] Inline hex color literal in style
- Rule: `.claude/rules/components.md` → "No inline hex color literals; use theme tokens."
- Issue: Hex color literal '#e5e7eb' is hardcoded in the style prop instead of using a theme token.

  Current (`src/components/Card.tsx:2`):
  ```tsx
  return <div style={{ border: "1px solid #e5e7eb" }}>{props.children}</div>;
  ```
  Suggested fix:
  ```tsx
  return <div style={{ border: `1px solid ${theme.border}` }}>{props.children}</div>;
  ```

### src/utils/math.ts
#### [MEDIUM impact / HIGH risk · 98% conf] Variable declared with var instead of const/let
- Rule: `.claude/rules/global.md` → "Use `const`/`let`, never `var`."
- Issue: Variable 'total' is declared with var on line 2.

  Current (`src/utils/math.ts:2`):
  ```ts
  var total = 0;
  ```
  Suggested fix:
  ```ts
  const total = 0;
  ```

#### [MEDIUM impact / HIGH risk · 99% conf] console.log used in utility function
- Rule: `.claude/rules/utils.md` → "Utility functions must be pure: no side effects, no I/O, no logging."
- Issue: Utility function calls console.log on line 4, violating purity requirement and no-logging constraint.

  Current (`src/utils/math.ts:4`):
  ```ts
  console.log("computed average over", xs.length, "items");
  ```
  Suggested fix: Remove the console.log call to maintain function purity.

## Clean files (no violations)
- src/api/orders.ts
- src/components/Modal.tsx
- src/utils/strings.ts
