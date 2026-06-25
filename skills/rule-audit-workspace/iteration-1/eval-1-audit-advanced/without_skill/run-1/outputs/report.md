# Rule-Adherence Report

Rules applied:
- global.md (global): no console.log; use const/let not var; no any type.
- api.md (src/api/**): validate request body against schema before use; no SQL via string interpolation, use parameterized queries.
- components.md (src/components/**): no inline hex color literals; function components only, no classes.
- utils.md (src/utils/**): utility functions must be pure (no side effects, I/O, or logging).

## src/api/orders.ts — CLEAN
Validates body with orderSchema.safeParse, uses parameterized query ($1). No violations.

## src/api/users.ts — 4 violations
1. Global: console.log in committed code.
   `console.log("query", req.query.name);`
2. Global: no any / concrete types — handler params untyped (implicit any).
   `export async function findUser(req, res) {`
3. API: request not validated against a schema before use.
   `const rows = await db.query(`SELECT * FROM users WHERE name = '${req.query.name}'`);`
4. API: SQL built by string interpolation instead of parameterized query.
   `const rows = await db.query(`SELECT * FROM users WHERE name = '${req.query.name}'`);`

## src/components/Card.tsx — 2 violations
1. Global: any type used.
   `export function Card(props: any) {`
2. Component: inline hex color literal.
   `<div style={{ border: "1px solid #e5e7eb" }}>{props.children}</div>`

## src/components/Modal.tsx — CLEAN
Function component, uses theme.surface token, no hex literal, no any.

## src/utils/math.ts — 3 violations
1. Global: var used instead of const/let.
   `var total = 0;`
2. Global: console.log in committed code.
   `console.log("computed average over", xs.length, "items");`
3. Utility: impure function — logging side effect.
   `console.log("computed average over", xs.length, "items");`

## src/utils/strings.ts — CLEAN
Pure function, concrete types, no violations.

## Summary
Total violations: 9 across 3 files (users.ts: 4, Card.tsx: 2, math.ts: 3). Clean: orders.ts, Modal.tsx, strings.ts.
