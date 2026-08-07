# Scriptify report — docs-linter

Target: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-2/eval-6-name-collision/without_skill/workspace/docs-linter/`

Operating principle applied: delegate to a deterministic script unless the step
genuinely needs Claude's judgement.

## Classification table

| # | Step (original SKILL.md) | Class | Script | Why |
|---|---|---|---|---|
| 1 | List every `.md` file under `docs/`, sorted by path, note the total count | DELEGATE | `scripts/list_docs.py` | Pure filesystem traversal + sort + count. Zero judgement, and re-deriving it in prose invites missed nested files (`docs/reference/api.md`) and inconsistent ordering. |
| 2 | Check each file starts with an H1 followed by a blank line; record failures | DELEGATE | `scripts/check_h1_structure.py` | Mechanical predicate over the first two lines of each file. Deterministic pass/fail, exact reason string per file, stable exit code. |
| 3 | Count fenced code blocks per file and total them | DELEGATE | `scripts/count_code_blocks.py` | Counting is the canonical case where an LLM drifts run to run. Fence pairing is a small state machine. |
| 4 | Decide which flagged files matter most this sprint, given tutorial pages get the most traffic | KEEP AS PROSE | none | Prioritisation against unstated, changing context (sprint goals, traffic, what "matters" means). No stable input a script could read. Encoding "tutorial ranks first" as code would freeze a judgement meant to be re-made each run. |

## Reasoning per step

### Step 1 — DELEGATE

Inputs are fully determined by the filesystem. The output (sorted relative
paths, total) is a fixed function of the tree. Prose enumeration also tends to
skip subdirectories; the script's `rglob("*.md")` cannot.

Verified: reports 3 files — `getting-started.md`, `reference/api.md`,
`tutorial.md`.

### Step 2 — DELEGATE (with a naming conflict, see gate.md)

The rule "first line is `# ...`, second line blank" is a two-line predicate.
Making it a script also lets the skill return a reason per flagged file rather
than a bare list, and gives callers an exit code to branch on.

Verified: flags `tutorial.md` (prose before the H1) and `reference/api.md`
(starts at H2); passes `getting-started.md`. Exit code 1.

The natural filename, `check_headings.py`, is already taken by an unrelated
pre-existing script that checks image alt text and is called by the release
pipeline at that exact path. The generated script is named
`check_h1_structure.py` instead. `scripts/check_headings.py` was not edited,
moved, or overwritten — sha256 remains
`d60bc3d4442fad85b028a4928f8bc763e5f4d173342393505170e462d52ada54`.

### Step 3 — DELEGATE

Counting fenced blocks across files is exactly the class of arithmetic that
varies run to run when done by reading. The script tracks fence open/close
state so an indented or `~~~`-style fence is handled the same way every time.

Verified: `getting-started.md` 2, `reference/api.md` 1, `tutorial.md` 1,
total 4.

### Step 4 — KEEP AS PROSE

This is the one step whose answer depends on information not present in the
repository: which sprint, what the team is trying to ship, how heavily each
page is actually read. The SKILL.md hint ("tutorial pages get the most
traffic") is a heuristic to weigh, not a rule to execute. A script here would
either hardcode the current sprint's answer or reimplement a judgement it
cannot make. Left as prose, and the SKILL.md text now says explicitly that no
script decides it.

## Smoke test results — PASS (run before the SKILL.md rewrite)

| Check | Result |
|---|---|
| `list_docs.py --help` | PASS (rc 0) |
| `check_h1_structure.py --help` | PASS (rc 0) |
| `count_code_blocks.py --help` | PASS (rc 0) |
| `list_docs.py docs` | PASS — 3 files, total 3, rc 0 |
| `check_h1_structure.py docs` | PASS — flags `reference/api.md` and `tutorial.md`; rc 1 |
| `count_code_blocks.py docs` | PASS — 2/1/1, total 4, rc 0 |
| `check_h1_structure.py nope` (bad input) | PASS — `not a directory: nope`, rc 2 |
| pre-existing `check_headings.py docs` still runs | PASS — reports missing alt text in `reference/api.md`, rc 1 |
| pre-existing `check_headings.py` sha256 unchanged | PASS — `d60bc3d4…ada54` |

## Changes applied

Added:
- `scripts/list_docs.py`
- `scripts/check_h1_structure.py`
- `scripts/count_code_blocks.py`

Rewritten:
- `SKILL.md` — steps 1-3 invoke the scripts; step 4 stays prose and says so
  explicitly; a note warns that `check_headings.py` is unrelated and must not be
  replaced.

Untouched:
- `scripts/check_headings.py`
- everything under `docs/`
