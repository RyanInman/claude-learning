# Rule Adherence Report

## Rules

- `global.md` (global, applies to all src files): no `console.log`; no `var`.
- `api.md` (paths: `src/api/**`): validate request body against schema; never pass `req.body` straight into a DB call.
- `ui.md` (paths: `src/ui/**`): no inline hex color literals; use theme tokens from `theme.ts`.

## Violations

### src/ui/Button.tsx
Applicable rules: global, ui

- Rule (ui): No inline hex color literals in components.
  `<button style={{ background: "#3b82f6", color: "#ffffff" }}>{label}</button>`
  Two inline hex literals: `#3b82f6` and `#ffffff`.

### src/utils/format.ts
Applicable rules: global

- Rule (global): Use `const`/`let`, never `var`.
  `var out = n.toFixed(2);`
- Rule (global): No `console.log` in committed code.
  `console.log("formatted", out);`

### src/api/handler.ts
Applicable rules: global, api

- Rule (global): No `console.log` in committed code.
  `console.log("creating user", req.body);`
- Rule (api): Validate request body against a schema; never pass `req.body` straight into a DB call.
  `const body = req.body;` then `return res.json(await db.user.create({ data: body }));`
  `req.body` used directly in `db.user.create` with no schema validation.

## Clean files

### src/api/profile.ts
Applicable rules: global, api. No violations. Validates `req.body` via `profileSchema.safeParse`, uses `logger`, uses `const`.
