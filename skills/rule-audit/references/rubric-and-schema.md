# Rubric & Finding Schema (review subagent)

You are reviewing files against a fixed set of rule files named in your prompt. Use this for how to
grade a violation and the exact JSON shape to emit. The main agent renders the report from your JSON
with a script, so the schema must be followed exactly.

## Contents
- [What counts as a violation](#what-counts-as-a-violation)
- [Ranking rubric: impact x risk](#ranking-rubric-impact-x-risk)
- [Finding schema (your output)](#finding-schema-your-output)

## What counts as a violation

A finding is a place where the file **breaks or contradicts a specific rule** that applies to it.
Anchor every finding to an actual rule bullet — if you cannot quote the bullet it violates, it is not
a finding for this review (it may be a general code-quality issue, which is out of scope here).

- Review a file **only against the rules handed to you.** A path-scoped rule was already matched to
  this file by its glob; do not import rules that were not assigned (e.g. an API rule must not be
  applied to a UI component that fell outside its `paths:` glob).
- Judge **adherence**, not style you would prefer. The rule is the standard.
- Rules can be **vague or unverifiable** ("write clean code"). If a rule cannot be checked mechanically
  against this file, say so once as a meta-note rather than inventing a violation.
- If two assigned rules **contradict each other** (a file cannot satisfy both), report the conflict
  **once** as a meta-finding naming both rule files, and do **not** raise per-file violations for either
  side. Flagging a file for breaking one of two mutually exclusive rules is a false positive — the file
  is uncomplyable until the rules are reconciled (see `rule-context-builder`). The fix belongs in the
  rules, not the code, so don't add LOW-impact noise to the per-file findings for it.
- A file with no violations is a real, useful result. Report it as clean; do not manufacture findings.
- **Only high-confidence violations reach the report.** Score each finding's `confidence` (0–100) that
  the snippet genuinely breaks the quoted bullet; the renderer drops everything below 90. Report your
  honest number — do not inflate a borderline call to clear the bar, and do not pad with guesses.

## Ranking rubric: impact x risk

Two independent axes. Impact is *how bad the consequence is*; risk is *how likely it actually bites*.
Keep them separate — a near-certain cosmetic slip is LOW impact / HIGH risk; a catastrophic bug down a
path that almost never runs is HIGH impact / LOW risk.

**Impact** — severity if the violation stands:
- **HIGH**: breaks correctness, security, or data integrity, or violates a rule whose whole purpose is
  preventing a serious failure (unvalidated input to the DB, leaked secret, raw error to a client).
- **MEDIUM**: degrades maintainability, consistency, or readability; wrong pattern but it functions.
- **LOW**: cosmetic or stylistic deviation with no functional consequence.

**Risk** — likelihood the violation actually causes harm in practice:
- **HIGH**: on a hot or commonly hit code path, or the bad outcome is near-certain given the violation.
- **MEDIUM**: triggers only under some inputs or conditions.
- **LOW**: rarely-exercised edge case, defensive-only, or hard to reach.

Calibration examples:
- Handler uses `req.body` with no schema validation, then writes it to the DB on the main create path
  → **HIGH impact** (data integrity / injection), **HIGH risk** (every create request).
- `console.log` left in a shared util imported widely → **LOW impact** (log noise), **HIGH risk**
  (runs constantly).
- Raw `throw` in an error branch that only fires on a malformed internal call → **HIGH impact** (leaks
  a stack trace to the client), **LOW risk** (that branch is seldom reached).
- Variable named `x` instead of the convention's descriptive name in a rarely-touched script →
  **LOW impact**, **LOW risk**.

## Finding schema (your output)

Build a single JSON object with `file_findings` (one entry per file you reviewed) and optional `meta`.
**Write that object to the output path given in your prompt using the Write tool, then return only a
one-line count (files reviewed, findings).** Do not paste the JSON or any file contents into your reply
— the path keeps raw code out of the main conversation.

```json
{
  "file_findings": [
    {
      "file": "src/api/handler.ts",
      "findings": [
        {
          "title": "Unvalidated request body written to DB",
          "rule_file": ".claude/rules/api.md",
          "rule_text": "Validate every handler's input against a shared schema before use.",
          "line": 6,
          "issue": "req.body is passed straight to db.user.create without schema validation.",
          "impact": "HIGH",
          "risk": "HIGH",
          "confidence": 95,
          "code_snippet": "const body = req.body;\nreturn res.json(await db.user.create({ data: body }));",
          "suggested_fix": "Validate req.body with the shared schema before the DB call.",
          "fix_example": "const parsed = userSchema.safeParse(req.body);\nif (!parsed.success) return errorResponse(res, 400, \"invalid input\");\nreturn res.json(await db.user.create({ data: parsed.data }));"
        }
      ]
    },
    { "file": "src/api/profile.ts", "findings": [] }
  ],
  "meta": [
    { "type": "unverifiable_rule", "rule_file": ".claude/rules/global.md", "note": "..." }
  ]
}
```

Field rules (the renderer requires `title`, `rule_file`, `rule_text`, `issue`, `impact`, `risk`,
`confidence`, `code_snippet`, `suggested_fix` on every finding — a missing or malformed one is a hard
validation error):
- `rule_file` — the path the script reported (e.g. `.claude/rules/api.md`), so the report cites the source.
- `rule_text` — the **exact bullet** the file violates, quoted. This is what makes a finding auditable.
- `line` — best-effort line number in the reviewed file; omit or use `null` if not applicable.
- `impact` / `risk` — exactly `HIGH` | `MEDIUM` | `LOW`.
- `confidence` — integer 0–100: how sure you are the snippet **actually violates the quoted bullet**,
  not how severe it is (that is `impact`). 90–100 = the code plainly breaks the rule with little room
  for interpretation; below 90 = you are inferring intent, the rule is fuzzy, or you would need wider
  context to be sure. The renderer suppresses anything below 90, so a low score removes the finding.
- `issue` — one or two sentences: what in the file breaks the rule. Be concrete; no padding.
- `code_snippet` — the **minimal offending lines copied verbatim** from the file (a few lines, not the
  whole function or file), so the reader sees the problem without opening the source. Reviewers act on
  what they can see; a bare line number makes them go hunt.
- `suggested_fix` — one-line direction, always present.
- `fix_example` — a short corrected version of the snippet. Include it **only when the fix is local and
  straightforward**. When the right fix needs broader context or a judgment call, omit it and explain
  the direction in `suggested_fix` instead — a half-guessed fix is worse than none. Never invent APIs:
  ground fixes in patterns already visible in the codebase (e.g. a clean sibling file using the
  intended helper). A wrong example fix erodes trust in the whole report.
- Always include an entry (with empty `findings`) for every file you reviewed, so clean files are visible.
