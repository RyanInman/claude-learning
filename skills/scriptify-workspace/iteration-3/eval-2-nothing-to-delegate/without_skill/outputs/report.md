# Scripting review: `well-delegated`

**Verdict: nothing new should become a script. The one deterministic step is already delegated to `scripts/check.py`, and the two remaining steps are judgment work that belongs to Claude.**

## What the skill contains

```
well-delegated/
├── SKILL.md          3-step workflow
├── notes/welcome.md  sample input
└── scripts/check.py  structure linter (argparse, --json, documented exit codes)
```

## Step-by-step classification

| # | Workflow step | Classification | Why |
|---|---|---|---|
| 1 | `python3 scripts/check.py notes/ --json` — lint structure (title heading present) | **SCRIPT — already done** | Fixed rule, same answer every run. Already extracted; no work left. |
| 2 | Decide which flagged items actually matter for this release's audience | **CLAUDE** | The decision depends on who reads the note and what shipped. A script has no way to know an internal note may skip its heading. |
| 3 | Write a plain-worded explanation per item, in the project's usual voice | **CLAUDE** | Prose in a house voice is generative. A template generator would produce identical text for every finding, which is worse than the current instruction. |

Score: 1 of 1 deterministic steps delegated. 0 gaps.

## Why `scripts/check.py` counts as properly delegated

I checked the four things that usually separate a real delegation from a script that exists but is never used:

1. **The body calls it by exact command.** SKILL.md line 10 reads ``Run exactly: `python3 scripts/check.py notes/ --json` `` — Claude does not have to guess the invocation.
2. **It parses arguments properly.** `argparse` with a positional `notes_dir` and a `--json` flag, so `--help` works. Verified:

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

3. **Its exit codes match its docstring, and the body documents them.** Verified all three:

   | Command | Output | Exit |
   |---|---|---|
   | `python3 scripts/check.py notes/ --json` | `[]` | 0 (clean) |
   | `python3 scripts/check.py <dir-with-bad-note> --json` | `[{"file": "bad.md", "problem": "missing title heading"}]` | 1 (findings) |
   | `python3 scripts/check.py nope/` | `error: not a directory: nope` | 2 (usage error) |

4. **Its output feeds the next step.** `--json` emits a machine-readable finding list, which is exactly what step 2 reads. The handoff is real, not decorative.

## What I deliberately did not recommend

Two changes look tempting and are wrong here:

- **Scripting the audience-fit call (step 2).** You could encode "internal notes are exempt" as a flag. That hard-codes today's single exception into a rule that will be wrong for the next release, and it moves a judgment the skill exists to make into a place where nobody will revisit it. Leave it with Claude.
- **Templating the explanations (step 3).** Fill-in-the-blank strings would make every explanation read the same, defeating "in the project's usual voice."

## Changes made

None. This was a read-only review, and the review found no work to do.
