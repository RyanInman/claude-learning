# Report Output Shape (main agent)

The report is rendered by `scripts/render_report.py`, not by hand. After every batch has written its
`.rule-review/batch-<N>.json`, run:

```bash
python3 <skill>/scripts/render_report.py --findings .rule-review --map .rule-review/map.json --expect <batch-count> [--reports-dir reports]
```

The script validates each findings file against the schema (exit 2 on a malformed or missing one),
**suppresses any finding scored below 90% confidence** (counted in the header), sorts the rest by impact
(HIGH→MEDIUM→LOW) then risk (HIGH→MEDIUM→LOW), and writes **two** reports to `reports/`:
`rule-adherence-high-medium.md` (HIGH+MEDIUM, the actionable set) and `rule-adherence-with-low.md` (adds
LOW/cosmetic findings, also counted in each header). It prints the HIGH+MEDIUM title block + ranked
Summary table plus both file paths to stdout. Relay that stdout; the files hold the detail. This is what
each rendered file looks like:

```markdown
# Rule Adherence Report
Mode: audit · Rules: 2 · Files reviewed: 4 · Findings: 1 · Suppressed (<90% conf): 1 · Min impact: MEDIUM (excluded 0)

## Summary (ranked by impact, then risk)
| # | File | Rule | Impact | Risk | Conf | Issue |
|---|------|------|--------|------|------|-------|
| 1 | src/api/handler.ts | api.md | HIGH | HIGH | 95% | Unvalidated request body written to DB |

## Findings by file
### src/api/handler.ts
#### [HIGH impact / HIGH risk · 95% conf] Unvalidated request body written to DB
- Rule: `.claude/rules/api.md` → "Validate every handler's input against a shared schema before use."
- Issue: req.body is passed straight to db.user.create without schema validation.

  Current (`src/api/handler.ts:6`):
  ```ts
  const body = req.body;
  return res.json(await db.user.create({ data: body }));
  ```
  Suggested fix:
  ```ts
  const parsed = userSchema.safeParse(req.body);
  if (!parsed.success) return errorResponse(res, 400, "invalid input");
  return res.json(await db.user.create({ data: parsed.data }));
  ```

## Clean files (no violations)
- src/api/profile.ts
- src/ui/Button.tsx

## Files with no applicable rules
- src/utils/format.ts

## Meta-findings
- [unverifiable_rule] `.claude/rules/global.md` — "write clean code" can't be checked mechanically.
```

Sections render only when they have content: no clean files → no "Clean files" section; no
`unmatched_files` in the map → no "Files with no applicable rules"; no meta entries → no
"Meta-findings". A run with zero findings still produces the report with an empty Summary row.
