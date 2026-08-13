# Script-delegation review: release-note-advisor

**Verdict: no new scripts needed.** The one deterministic step in this skill is already
delegated to `scripts/check.py`. The two remaining steps are judgment calls that a script
cannot make correctly, so they stay with Claude.

## Step-by-step classification

| # | Workflow step | Nature | Classification |
|---|---------------|--------|----------------|
| 1 | `python3 scripts/check.py notes/ --json` — lint structure (title heading present) | Deterministic: same input, same findings, every run | **SCRIPT — already delegated.** No change. |
| 2 | Decide which flagged items actually matter for this release's audience | Contextual judgment: depends on who reads the note, whether it is internal, what the release contains | **CLAUDE.** No rule set produces this answer. |
| 3 | Write a plainly-worded explanation for each item worth fixing, in the project's voice | Natural-language generation matched to an unwritten house voice | **CLAUDE.** |

## Why `scripts/check.py` counts as properly delegated

I verified the script rather than assuming it works:

- **Invoked from the body, exactly.** SKILL.md line 10 gives the literal command
  `python3 scripts/check.py notes/ --json`, with the exit-code contract (0 clean, 1 findings,
  2 usage error) stated inline. Claude does not have to guess the interface.
- **Real CLI.** It uses `argparse`, so `--help` works:

  ```
  $ python3 scripts/check.py --help
  usage: check.py [-h] [--json] notes_dir

  Lint release-note structure.

  positional arguments:
    notes_dir

  options:
    -h, --help  show this help message and exit
    --json
  ```
- **Runs clean on the bundled fixture.**

  ```
  $ python3 scripts/check.py notes/ --json
  []
  $ echo $?
  0
  ```
  `notes/welcome.md` starts with `# Welcome improvements`, so there are no findings and the
  exit code is 0, matching the documented contract.
- **Error path matches the docstring.**

  ```
  $ python3 scripts/check.py nope/
  error: not a directory: nope
  $ echo $?
  2
  ```
- **Machine-readable output.** `--json` emits a findings list that step 2 reads directly, so
  the script hands structured data to the judgment step instead of prose Claude must re-parse.
- **Docstring documents usage and every exit code**, so the file is self-describing when read
  on its own.

## What I considered scripting and rejected

- **Scripting the audience-fit decision (step 2).** A script would need a rule like "skip
  internal notes." The skill deliberately says the opposite — "a missing heading on an
  internal note *may* be fine" — which is a per-release call. Encoding it would turn a
  judgment into a wrong constant.
- **Scripting the explanations (step 3).** Templated explanations would defeat the stated
  requirement to write "in the project's usual voice." Template output reads as template
  output.
- **Adding more lint rules to `check.py`** (link checks, version-string format, changelog
  ordering). These would be genuine script work, but the skill never asks for them. Adding
  them is scope the skill does not have, not delegation of work it already does.

## Recommendation

Change nothing. This skill is at the right split already: one deterministic check in a
script with a documented CLI contract, and two judgment steps left to Claude. The next
delegation opportunity would only appear if you add new deterministic checks to the
workflow.
