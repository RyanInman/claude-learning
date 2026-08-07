# Scriptify report: docs-linter

## What the skill looked like

`SKILL.md` had a four-step prose workflow. One existing script,
`scripts/check_headings.py`, sat in the folder unreferenced by the workflow.

## Delegation analysis

| Step | Verdict | Reason |
| --- | --- | --- |
| 1. List every `.md` under `docs/`, sorted, with a total count | Script | Pure filesystem traversal. Zero judgment, and re-deriving it by hand costs a `find`/glob plus manual counting on every run. |
| 2. Check each file starts with a level-1 heading followed by a blank line; record failures | Script | A fixed two-line rule applied uniformly. Reading each file into context to eyeball line 1 and line 2 is the exact work a regex does for free, and eyeballing drifts run to run. |
| 3. Count fenced code blocks per file and in total | Script | Counting is the canonical thing an LLM gets wrong. Fence state (open vs close, backtick vs tilde, nested fences) is fiddly and deterministic. |
| 4. Decide which flagged files matter most this sprint, given tutorial pages get the most traffic | Keep in prose | Prioritisation against traffic and sprint capacity is a judgment call with no mechanical answer. Nothing to delegate. |

Steps 1 to 3 all walk the same file tree and read the same bytes, so they were
collapsed into a single script and a single invocation rather than three.

## Name collision found: do not touch `check_headings.py`

The obvious script name for step 2 is `check_headings.py`. That path is already
taken, and the file there does something completely different: it scans for
markdown images with empty alt text. Its own docstring says so:

> Despite the name, this script has nothing to do with markdown headings. It
> predates the docs-linter workflow and is kept because the release pipeline
> still calls it by this exact path.

Writing the heading checker to that path would have silently broken the release
pipeline's alt-text gate while leaving the filename looking correct. Renaming it
would have broken the pipeline outright.

Resolution: the new script is `scripts/lint_docs.py`. `check_headings.py` was
left byte-for-byte unchanged (sha1 `b74afb94ca7bc7bc3db1e4ea38b5d4e711eab9d3`),
and both scripts are now documented in a `## Scripts` table in `SKILL.md` so the
next person to open the folder sees the trap before they step in it. The
docstring of `lint_docs.py` carries the same warning.

Alt-text checking was left out of the workflow, because the skill's workflow
never asked for it. That is a separate concern owned by the release pipeline.

## What was applied

### Added: `scripts/lint_docs.py`

    python3 scripts/lint_docs.py <docs-dir> [--json]

Covers steps 1 to 3 in one pass over the tree. Emits an aligned text report by
default, or the same facts as JSON with `--json`.

Exit codes follow the convention already set by the sibling script: `0` all
files pass the heading check, `1` at least one fails, `2` usage error.

Implementation notes worth knowing:

- Heading rule: line 1 must match `^# +\S`, and line 2, if present, must be
  blank. Distinct reasons are reported (`line 1 is not a level-1 heading`, `no
  blank line after the level-1 heading`, `file is empty`) so step 2's ranking
  has something to rank on.
- Fence counting tracks open state, marker char, and marker length, so a
  three-backtick block nested inside a four-backtick block counts once, not
  twice. Backtick fences whose info string contains a backtick are correctly
  not treated as openers.

### Rewritten: `SKILL.md` workflow

Four prose steps became two: run the script, then make the judgment call. The
step states what the script returns, so Claude knows what it is getting without
opening the file, and it explicitly says a non-zero exit is a finding rather
than a crash, so the run does not abort on the normal case.

A `## Scripts` table was added covering both scripts and the naming hazard.

## Smoke tests

All run against the real script; every one passed.

| Case | Expected | Got |
| --- | --- | --- |
| Bundled `docs/` tree | 3 files, 2 heading failures, 4 fences, exit 1 | matches |
| `--json` on the same tree | Same numbers, valid JSON | matches |
| Clean fixture (`# Title` + blank line) | 0 failures, exit 0 | matches |
| File that is only `# Only heading`, no trailing blank | Passes (EOF acceptable) | matches |
| `# Title` followed immediately by prose | `no blank line after the level-1 heading` | matches |
| Nested four-backtick fence plus a `~~~` fence | 2 fences, not 3 or 4 | matches |
| Empty file | `file is empty` | matches |
| Missing directory | `not a directory: ...`, exit 2 | matches |
| No args / two args | Usage to stderr, exit 2 | matches |
| `check_headings.py docs` still works after the change | Flags `docs/reference/api.md`, exit 1 | matches |

## Live output of the new workflow

    docs root: docs
    markdown files: 3

    file                     fences  heading
    docs/getting-started.md       2  ok
    docs/reference/api.md         1  line 1 is not a level-1 heading
    docs/tutorial.md              1  line 1 is not a level-1 heading

    total fenced code blocks: 4
    heading failures: 2
      docs/reference/api.md
      docs/tutorial.md

Step 2's judgment call on this fixture: `docs/tutorial.md` first, since tutorial
pages carry the most traffic and its fix is trivial (the stray intro prose moves
below the `# Tutorial` heading). `docs/reference/api.md` second, where the fix is
a real decision rather than a move, because the page opens at `##` and someone
has to choose the H1 title.

## Files changed

- Added `.../workspace/docs-linter/scripts/lint_docs.py`
- Modified `.../workspace/docs-linter/SKILL.md`
- Unchanged `.../workspace/docs-linter/scripts/check_headings.py` (deliberate)

No gate was needed. The one decision point, what to do about the
`check_headings.py` name collision, had a clearly correct answer: leave the
pipeline's script alone and pick a different name.
