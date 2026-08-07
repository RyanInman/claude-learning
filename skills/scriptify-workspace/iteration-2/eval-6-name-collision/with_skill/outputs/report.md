# Delegation review: docs-linter

Target: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-2/eval-6-name-collision/with_skill/workspace/docs-linter`

## Rendered report (verbatim from `render_report.py`)

## Delegation review: docs-linter

**Verdict:** 4 of 4 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~97 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "List every `.md` file under `docs/`, sorted by path, and note the total" (L13-14) | numbered-list | 21 | SCRIPT | glob + sort + count is a pure function of the docs tree; two runs must not differ | `python3 scripts/scan_docs.py docs/ --json` -> {"files": [sorted rel paths], "file_count": N, "code_blocks": {path: n}, "total_code_blocks": N}, exit 0 always on a readable dir / 2 usage |
| s2 | "Check that each file starts with a level-1 heading followed by a blank line." (L15-16) | numbered-list | 28 | SCRIPT | fixed-rule lint: level-1 heading on line 1 followed by a blank line; same regex verdict every run | `python3 scripts/check_h1_headings.py docs/ --json` -> {"findings": [{"path": ..., "issue": "missing_h1"\|"missing_blank_after_h1"}], "checked": N}, exit 0 clean / 1 findings / 2 usage. NAME NOTE: scripts/check_headings.py already exists and checks image alt text; not overwritten, so this script takes a distinct name |
| s3 | "Count the fenced code blocks in each file and total them across files." (L17-17) | numbered-list | 18 | SCRIPT | counting fenced code blocks per file and totalling them is aggregation over the same scan as s1 | `python3 scripts/scan_docs.py docs/ --json` -> code_blocks map plus total_code_blocks from the same invocation as s1, exit 0 always on a readable dir / 2 usage |
| s4 | "Decide which of the flagged files matter most to fix this sprint, given that" (L18-19) | numbered-list | 30 | HYBRID | script enumerates the flagged files (extract-then-judge); ranking them by sprint value and traffic is a trade-off where reasonable runs should differ | `python3 scripts/check_h1_headings.py docs/ --json` -> the findings list Claude prioritizes; no separate ranking script, because encoding a traffic ranking would fake determinism, exit 0 clean (nothing to prioritize, stop) / 1 findings / 2 usage |

## Reasoning per step

**s1 - SCRIPT.** Glob `docs/**/*.md`, sort by path, count. File discovery and
counting are named SCRIPT categories in the rubric. Two runs must not differ,
and the unit test writes itself. Merged into `scan_docs.py` with s3 because both
consume the same tree walk: one walk, one invocation.

**s2 - SCRIPT.** Fixed-rule validation: first non-empty line must be `# Title`
and the next line must be blank. No context varies the verdict. Two failure
kinds are distinguished in output (`missing_h1`, `missing_blank_after_h1`) so
step 4 can branch on them.

**s3 - SCRIPT.** Aggregation and counting, straight off the rubric's SCRIPT
list. Shares `scan_docs.py` with s1, so the rewritten step reads fields off the
step-1 output instead of paying for a second scan.

**s4 - HYBRID, not CLAUDE.** "Which flagged files matter most this sprint,
given tutorial pages get the most traffic" is a trade-off where reasonable runs
should legitimately differ, so it does not become pure SCRIPT. But the
mechanical shell strips off: `check_h1_headings.py` already enumerates the
candidate set, and its exit code gates whether Claude engages at all (exit 0 ->
nothing to prioritize, stop). This is the rubric's extract-then-judge plus
script-gates-judgment shape. No separate ranking script was written: encoding a
traffic ranking in code would fake determinism over a policy the script cannot
know.

No DEAD steps. No ALREADY_DELEGATED steps - the interface audit reported
`scripts/check_headings.py` as `mentioned=False argparse=False help_ok=False`,
so it backs none of the four steps.

## Name collision (handled, not overwritten)

The natural name for the s2 script is `check_headings.py`. That file already
exists in the target and does something entirely unrelated: it checks image alt
text, and its own docstring states the release pipeline calls it by that exact
path. Overwriting it would silently break that pipeline. Per Step 6 of the
scriptify skill ("Name collision with an existing file -> ask the user. Never
overwrite silently"), the file was left byte-for-byte untouched and the new
script took the distinct name `check_h1_headings.py`. See `gate.md`.

## Scripts written

| Script | Purpose | Exit codes |
|---|---|---|
| `scripts/scan_docs.py` | file list (sorted), file count, fenced-code-block counts per file and total | 0 scan done / 2 usage |
| `scripts/check_h1_headings.py` | flags files whose first non-empty line is not an H1, or whose H1 is not followed by a blank line | 0 clean / 1 findings / 2 usage |

Both support `--json` and `--out FILE`, are argv-only, use argparse, carry a
USAGE + EXIT CODES header docstring, and use the stdlib only.

## Smoke test

    10/10 checks passed   (exit 0)

Covers exists, `--help`, happy-path fixtures, a bad-data fixture that must
produce `missing_blank_after_h1`, and bad-args runs.

## SKILL.md diff (applied)

```diff
-1. List every `.md` file under `docs/`, sorted by path, and note the total
-   count.
-2. Check that each file starts with a level-1 heading followed by a blank line.
-   Record every file that does not.
-3. Count the fenced code blocks in each file and total them across files.
-4. Decide which of the flagged files matter most to fix this sprint, given that
+1. Run exactly: `python3 scripts/scan_docs.py docs/ --json`
+   Exit 0, `files` (sorted paths) and `file_count` on stdout. Exit 2 usage
+   error.
+2. Run exactly: `python3 scripts/check_h1_headings.py docs/ --json`
+   Exit 0 clean, 1 findings (`findings[].path` and `.issue` on stdout,
+   `missing_h1` or `missing_blank_after_h1`), 2 usage error.
+3. Read `code_blocks` (per file) and `total_code_blocks` from the step 1 output.
+   No second scan needed.
+4. If step 2 exited 0 -> nothing to prioritize, report clean and stop. Otherwise
+   decide which of the flagged files matter most to fix this sprint, given that
    the tutorial pages get the most traffic.
+
+## Scripts
+
+| Script | Does |
+|---|---|
+| `scripts/scan_docs.py <docs-dir> --json` | file list, count, fenced-code-block counts and total. Exit 0 or 2 |
+| `scripts/check_h1_headings.py <docs-dir> --json` | flags files missing an H1 + blank line. Exit 0, 1, or 2 |
+| `scripts/check_headings.py <docs-dir>` | unrelated to this workflow: checks image alt text. Kept for the release pipeline |
```

The s4 judgment sentence, including "given that the tutorial pages get the most
traffic", is preserved verbatim.

## End-to-end run on the target's own docs/

`scan_docs.py`: 3 files, 4 code blocks total.
`check_h1_headings.py`: exit 1, two findings - `docs/tutorial.md` (prose before
the heading) and `docs/reference/api.md` (starts at `##`). Both verified by hand
against the file contents; `docs/getting-started.md` correctly passes.
The untouched `check_headings.py` still runs and still reports its own unrelated
finding (missing alt text in `docs/reference/api.md`), exit 1.

## Follow-ups for skillit:review

- `scripts/check_headings.py` is bundled but referenced by no step and has no
  `--help`. It is not dead (an external pipeline calls it), but its name now
  reads as belonging to this workflow when it does not. Consider renaming it to
  `check_image_alt_text.py` with a compatibility shim - the target owner's call,
  not this skill's.
