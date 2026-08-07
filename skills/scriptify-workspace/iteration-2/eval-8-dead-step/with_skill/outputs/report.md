# Delegation review: api-docs-checker

Target: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-2/eval-8-dead-step/with_skill/workspace/api-docs-checker/`

Report only. Nothing was written into the target skill.

## Rendered report (verbatim from `render_report.py`)

## Delegation review: api-docs-checker

**Verdict:** 3 of 5 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~96 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "List every `.md` file in `endpoints/`, sorted by path, and note the total" (L13-14) | numbered-list | 21 | SCRIPT | glob + sort + count is a pure function of the directory; runs must not differ | `python3 scripts/check_endpoints.py endpoints/ --json` -> JSON: {files: [sorted paths], count: N, missing: {file: [fields]}}, exit 0 clean / 1 missing fields / 2 usage |
| s2 | "Check that every endpoint file has a `summary:` field in its frontmatter." (L15-16) | numbered-list | 28 | DEAD | fully subsumed by s3, which checks summary: and description: together; checking summary: alone duplicates half of s3 and reports the same files twice | - |
| s3 | "Check that every endpoint file has both a `summary:` field and a" (L17-19) | numbered-list | 40 | SCRIPT | fixed-rule frontmatter validation: required keys present or not, same verdict every run | `python3 scripts/check_endpoints.py endpoints/ --json` -> JSON: {files: [sorted paths], count: N, missing: {file: [fields]}}, exit 0 clean / 1 missing fields / 2 usage |
| s4 | "Append the endpoint list to `legacy/index.txt` so the old docs portal can" (L20-21) | numbered-list | 22 | DEAD | writes to legacy/index.txt for the legacy docs portal that the target's own Notes say was retired in v2; the legacy/ directory does not exist in the skill folder | - |
| s5 | "Judge whether each `description:` reads clearly for an external developer" (L22-24) | numbered-list | 35 | HYBRID | clarity for an unfamiliar reader is genuine judgment and reasonable runs differ, but extracting each description and pre-computing the mechanical signals is deterministic | `python3 scripts/collect_descriptions.py endpoints/ --json` -> JSON per file: description text, word count, vague-phrase and placeholder hits (TODO/TBD/'the thing'), whether it only restates the endpoint name, exit 0 all extracted / 1 mechanical flags present / 2 usage |

## Reasoning per step

### s1 (L13-14) - SCRIPT

"List every `.md` file in `endpoints/`, sorted by path, and note the total count."
Glob, sort, count. File discovery and aggregation, both named SCRIPT categories
in the rubric. The output is a pure function of the directory contents; two runs
that differ here are two runs where one is wrong. Unit-testable today against a
fixture directory.

Shares `check_endpoints.py` with s3: the same walk over `endpoints/` that
validates frontmatter already produces the sorted file list and the count, so one
script covers both steps and one invocation replaces two prose steps.

### s2 (L15-16) - DEAD

"Check that every endpoint file has a `summary:` field in its frontmatter. Record
every file that does not."

Not a script candidate, because the step should not exist. s3 immediately after
it checks *both* `summary:` and `description:` and records which field is missing
from which file. s2 is a strict subset of s3. Every file s2 reports, s3 reports
again with the same finding, so the skill double-reports the same gaps on every
run and spends tokens twice on the same walk.

Per the rubric, DEAD steps are never auto-deleted - the user owns the target's
workflow. Flagged here for a `skillit:review` follow-up. The intended fix is to
delete s2 and keep s3; if instead the author wanted summary-only to be a distinct
severity, that intent belongs in s3's output, not in a duplicate step.

### s3 (L17-19) - SCRIPT

"Check that every endpoint file has both a `summary:` field and a `description:`
field in its frontmatter. Record which field is missing from which file."

Fixed-rule validation over parsed frontmatter - the canonical SCRIPT category.
Presence of a required key is not a judgment call. The expected output is fully
specifiable in advance, which is the rubric's secondary test for close calls. It
is not even close.

Grounding on the real fixtures: `create-widget.md` has both fields,
`delete-widget.md` is missing `description:`, `list-widgets.md` is missing
`summary:`. A script returns exactly that map every time; prose re-derives it and
can miscount.

### s4 (L20-21) - DEAD

"Append the endpoint list to `legacy/index.txt` so the old docs portal can pick it
up."

Superseded. The target's own Notes section states the legacy docs portal was
retired in v2 and the `legacy/` output directory went with it. Confirmed on disk:
the skill folder contains only `SKILL.md` and `endpoints/` - there is no
`legacy/`. Scripting this step would harden a write to a consumer that no longer
exists, and would either create a stray directory or fail hard on every run.

This is the rubric's exact warning against forcing a script onto a DEAD step.
Flagged for a `skillit:review` follow-up; not auto-deleted.

### s5 (L22-24) - HYBRID

"Judge whether each `description:` reads clearly for an external developer who has
never seen this API, and flag the ones that do not."

Not pure CLAUDE, because a mechanical shell surrounds the judgment. Not pure
SCRIPT, because "reads clearly to an unfamiliar reader" is contextual
classification where reasonable runs legitimately disagree - a script asserting a
clarity verdict would hide that variance behind false authority.

Decomposition (extract-then-judge, hybrid shape 1):

- Script side - enumerate every file that actually has a `description:`, extract
  the text, and pre-compute the mechanical signals: word count, placeholder hits
  (TODO, TBD, XXX), vague filler ("the thing", "standard params", "as expected"),
  and whether the description merely restates the endpoint name or path. Skipping
  files with no `description:` at all is s3's job, not a clarity judgment.
- Claude side - read the extracted descriptions plus the flags and decide which
  ones an external developer could not act on. Example from the fixtures:
  `list-widgets.md` reads "Does the listing thing with the standard params." The
  script flags "the thing" and "standard params" as vague and reports 8 words;
  Claude still makes the call that this fails an unfamiliar reader, and says what
  is missing (which params, what is returned).

Rewritten step becomes "run the script, then apply judgment to its output"; the
judgment prose stays verbatim.

## Summary

- Delegate to scripts: **s1, s3** (fully, one shared `check_endpoints.py`) and
  **s5** (partly, `collect_descriptions.py` feeding Claude's clarity call).
- Do not script: **s2** and **s4**. Both are DEAD - s2 is duplicative of s3, s4
  targets a retired output path. They need deletion by the skill's owner, not
  automation. Route to `skillit:review`.
- Two scripts cover the whole live workflow, leaving Claude one genuine judgment
  step.
