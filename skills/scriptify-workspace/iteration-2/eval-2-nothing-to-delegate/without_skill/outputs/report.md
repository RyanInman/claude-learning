# Script delegation review: `release-note-advisor`

Target: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-2/eval-2-nothing-to-delegate/without_skill/workspace/well-delegated/`

Files inspected:
- `SKILL.md` (3-step workflow)
- `scripts/check.py`
- `notes/welcome.md` (fixture input)

## Verdict

**No new scripts recommended.** The skill's one mechanical step is already delegated to `scripts/check.py`. The two remaining steps require judgment and must stay with Claude.

## Per-step classification

| # | Step | Class | Reason |
|---|------|-------|--------|
| 1 | Run `python3 scripts/check.py notes/ --json` to lint structure (title heading present) | ALREADY SCRIPT | Deterministic parse/validation, already extracted to `scripts/check.py`, invoked by exact command in SKILL.md, documented exit codes 0/1/2 |
| 2 | Read findings JSON and decide which flagged items actually matter for this release's audience | CLAUDE | Audience-fit judgment. "A missing heading on an internal note may be fine" is context-dependent and cannot be encoded as a rule |
| 3 | Write a short, plainly-worded explanation for each item worth fixing, in the project's usual voice | CLAUDE | Natural-language generation matched to project voice. No deterministic output |

## Reasoning

### Step 1 - already delegated, verified working

`scripts/check.py` is a proper delegation, not a stub:

- Uses `argparse` with a positional `notes_dir` and a `--json` flag.
- Has a module docstring covering USAGE and EXIT CODES.
- Returns documented exit codes: `0` clean, `1` findings, `2` usage error / missing directory.
- Emits machine-readable JSON for step 2 to consume, plus a human-readable fallback.
- SKILL.md invokes it with an exact command line and states what the exit codes mean, so Claude does not have to re-derive the invocation.

Verified live (commands and output in `transcript-notes.md`):

- `python3 scripts/check.py --help` prints usage, exit 0.
- `python3 scripts/check.py notes/ --json` prints `[]`, exit 0 (the one fixture note starts with `# `, so it is clean).

Nothing to add here. Re-scripting it would be duplicate work.

### Step 2 - must stay CLAUDE

The step explicitly asks for a relevance filter over the linter's findings, gated on audience ("internal note may be fine"). The inputs that would drive such a decision - who the release is for, whether a note is internal or customer-facing, how much the omission actually costs - are not present in the file tree and are not derivable from the note text. A script could only re-implement the linter's own rule or hard-code a guess. Forcing this into code would make the skill less correct, not more deterministic.

### Step 3 - must stay CLAUDE

Prose written "in the project's usual voice" is generative and unverifiable by exit code. A script cannot produce it, and a template would flatten exactly the quality the step asks for.

## What was considered and rejected

- **A wrapper that runs the linter and pretty-prints the report.** Rejected: the workflow has one script call and three steps; a wrapper adds a file and an indirection without removing any re-derived reasoning. The `--json` output is already the structured hand-off.
- **A severity/priority rules table for step 2.** Rejected: any rule set would be a guess at audience, which is the exact thing the step defers to Claude on. It would produce confident wrong filtering.
- **A report renderer for step 3.** Rejected: the output is short free prose per item, not a fixed table or fixed sections. There is no stable shape to render.
- **Extending `check.py` with more lint rules.** Rejected: out of scope. SKILL.md asks only for the title-heading check; adding rules changes the skill's behavior rather than making the existing behavior deterministic.

## Recommendation

Leave the skill as is. It is already correctly split: the deterministic structural check is in a script with a documented CLI and exit codes; the judgment and writing stay with Claude. No files were added or modified in the target skill folder.
