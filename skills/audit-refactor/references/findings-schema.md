# Findings schema

`load_findings.py` normalizes any supported report into this canonical shape,
written to `.refactor/findings.json`. The rest of the skill reads only this.

```json
{
  "source": "rule-audit-json | findings-json | markdown",
  "root": "/abs/repo/root",
  "findings": [
    {
      "id": "f1",
      "file": "src/api/handler.ts",
      "title": "Unvalidated request body written to DB",
      "rule_file": ".claude/rules/api.md",
      "rule_text": "Validate every handler's input against a shared schema before use.",
      "line": 6,
      "issue": "req.body passed straight to db.user.create without validation.",
      "impact": "HIGH",
      "risk": "HIGH",
      "confidence": 95,
      "code_snippet": "const body = req.body;\nreturn res.json(...);",
      "suggested_fix": "Validate req.body with the shared schema first.",
      "fix_example": "const parsed = userSchema.safeParse(req.body); ..."
    }
  ]
}
```

After `estimate_effort.py` runs, each finding also carries `effort`
(low|medium|high), `model` (haiku|sonnet|opus), and a `signals` object.

## Field meaning

| Field | Notes |
|-------|-------|
| `id` | Assigned by load order (`f1`, `f2`, ...). Stable handle through the run. |
| `file` | Path the change targets, relative to `root`. |
| `impact` / `risk` | Severity / likelihood, each HIGH\|MEDIUM\|LOW. Used to rank and to pick the small scope. |
| `confidence` | 0–100. Findings below `--min-confidence` (default 90) are dropped at load — same bar rule-audit uses to surface a finding. |
| `code_snippet` | The offending lines, verbatim. The executor edits exactly here. |
| `fix_example` | A local corrected snippet when the fix is self-contained. Its presence is a strong "this is cheap" signal. |

## Supported inputs

1. **rule-audit working dir** — a directory of `batch-*.json` files. The reliable
   path: every field is present and typed. This is the default expectation.
2. **single JSON file** — the rule-audit wrapper (`{"file_findings": [...]}`), a
   bare list of finding objects, or `{"findings": [...]}`.
3. **markdown report** — best-effort. Only the summary table is parsed, so
   `code_snippet`, `rule_text`, and `fix_example` come back empty. Those findings
   then look expensive to `estimate_effort.py` (no fix_example, unknown blast
   radius) and tend to route to a stronger model — which is the safe direction.
   Prefer feeding the JSON when you have it.

## Scoping to a target (`--files`)

Pass `--files <path...>` (files and/or directories) to keep only findings whose `file` is a
target or sits under a target directory. Targets are normalized repo-relative against `root`,
so absolute and relative paths behave identically. The filter runs *before* the confidence
filter and `f1..fN` id assignment, so ids stay contiguous for the target. An empty scoped set
exits 3 — the same "no findings" signal — which the skill's "no audit info for the target"
branch keys on.

If `load_findings.py` exits 3 (zero findings after scoping/confidence filtering) or no report
exists at all, do not invent work — notify the developer and offer the Phase 1 options
(provide a report, or run rule-audit scoped to the target).
