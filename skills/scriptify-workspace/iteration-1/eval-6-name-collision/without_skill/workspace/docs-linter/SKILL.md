---
name: docs-linter
description: Lints the markdown files under docs/ for structural problems and reports which ones to fix. Use when the user asks to lint, check, or tidy the docs folder.
---

# Docs Linter

Check the markdown under `docs/` for structural problems, then report what to
fix.

## Workflow

1. Run the scan. It lists every `.md` file under `docs/` sorted by path with a
   total count, flags each file that does not start with a level-1 heading
   followed by a blank line, and counts fenced code blocks per file and in
   total.

   ```bash
   python3 scripts/lint_docs.py docs
   ```

   Exit code `0` means every file passed the heading check, `1` means at least
   one failed, `2` means a usage error. A failing exit code is a finding, not a
   crash; read the report and carry on. Add `--json` if you need the same
   facts as structured data.

2. Report the scan output as-is, then decide which of the flagged files matter
   most to fix this sprint, given that the tutorial pages get the most traffic.
   This ranking is the judgment call the script cannot make.

## Scripts

| Script | What it does |
| --- | --- |
| `scripts/lint_docs.py` | Step 1 of the workflow: file inventory, level-1 heading check, fenced-code-block counts. |
| `scripts/check_headings.py` | **Checks image alt text, not headings.** Misnamed for historical reasons and called by this exact path from the release pipeline, so do not rename, repurpose, or overwrite it. It is not part of this workflow. |
