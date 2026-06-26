Rule-audit review batch — follow these instructions exactly.

Placeholders resolved by the dispatching prompt: <ROOT> is the project root, <N> is this batch index, <SKILL> is the rule-audit skill folder (absolute path).

## 1. Fetch your file list

Run:
```
python3 -c "import json;b=json.load(open('<ROOT>/.rule-review/map.json'))['batches'][<N>];print('\n'.join(b['files']))"
```

These are the source files you must review. Read each one in full under <ROOT> before judging.

## 2. Fetch your applicable rule files

Run:
```
python3 -c "import json;print('\n'.join(json.load(open('<ROOT>/.rule-review/map.json'))['batches'][<N>]['rules']))"
```

These paths are relative to <ROOT>. Read each rule file in full before judging.

## 3. Read the rubric and schema

Read `<SKILL>/references/rubric-and-schema.md` for the ranking rubric and the exact JSON output schema you must produce.

## 4. Review

Review each source file against ONLY the rules listed in step 2 — do not import or apply any rules not given to you. A file with no violations must still appear in the output with empty findings.

## 5. Write and validate

Write the JSON findings object to `<ROOT>/.rule-review/batch-<N>.json` using the Write tool. Then validate:

```
python3 <SKILL>/scripts/validate_findings.py <ROOT>/.rule-review/batch-<N>.json
```

If it exits non-zero, fix the reported problems and rewrite the file until it exits 0.

## 6. Return

Return ONLY a one-line count in this form: `<M> rule files read, <K> files reviewed, <F> findings`. Do not paste the JSON or any file contents.
