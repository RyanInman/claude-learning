Rule-audit adversarial review — follow these instructions exactly.

Placeholders resolved by the dispatching prompt: <ROOT> is the project root, <N> is this batch index, <SKILL> is the rule-audit skill folder (absolute path).

You did NOT write the findings in this batch. Your job is to disprove them, not defend them. Every finding is guilty of being a false positive until the rule text and source prove otherwise.

## 1. Read the findings

Read `<ROOT>/.rule-review/batch-<N>.json` with the Read tool. (Do not shell-print it — a plain Read is safe against quotes/spaces in the JSON.)

## 2. Fetch your applicable rule files

Run:
```
python3 -c "import json;print('\n'.join(json.load(open('<ROOT>/.rule-review/map.json'))['batches'][<N>]['rules']))"
```

These are the ONLY rules the findings may invoke. Paths are relative to <ROOT>. Read each rule file in full.

## 3. Read the rubric

Read `<SKILL>/references/rubric-and-schema.md` for the rubric and the exact JSON schema.

## 4. Challenge each finding

For each finding, use the Read tool to re-read the cited source file at the cited line (do not judge from the finding text alone) and decide skeptically:

- **Rule existence and accuracy**: Does the cited rule exist in the rule files above, and does it actually say what the finding claims? A paraphrase that is stricter than the written rule is a false positive.
- **Violation reality**: Is the violation real and present at that line, or hallucinated / already-compliant / a misread?
- **Scope**: Is the rule in scope for that file per the rules given (do not import outside rules)?
- **Grading**: Are impact/risk defensible per the rubric, or inflated?

**Kill-list — remove any finding that invokes these unless a listed rule states them verbatim:**
- `useCallback` / `useEffect` dependency-array complaints ("missing dep", "exhaustive-deps")
- "magic number" dependency concerns
- Loose-equality / `==` vs `===` style notes
- Unused variable or import warnings
- Naming convention nitpicks (casing, prefix/suffix style)
- Hook-ordering suggestions

## 5. Rewrite and validate

Rewrite `<ROOT>/.rule-review/batch-<N>.json` with the Write tool, keeping only findings that survive scrutiny. For each removed finding: delete it. For each corrected finding: fix the mis-cited rule or line number, downgrade inflated impact/risk. Preserve the exact schema and the `meta` block. Do not invent new findings — missed violations are out of scope here; you only remove or correct.

Then validate:
```
python3 <SKILL>/scripts/validate_findings.py <ROOT>/.rule-review/batch-<N>.json
```

Fix until it exits 0.

## 6. Return

Return ONLY a one-line count in this form: `<F> findings reviewed, <R> removed, <C> corrected`. Do not paste JSON or file contents.
