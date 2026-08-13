Short answer: none of them. `release-note-advisor` is already a thin orchestrator — step 1 is one exact command line over `scripts/check.py`, and steps 2 and 3 are the judgment and prose that command exists to feed.

## Delegation review: release-note-advisor

**Verdict:** 0 of 3 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~0 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "Run exactly: `python3 scripts/check.py notes/ --json` to lint structure" (L10-11) | numbered-list | 35 | ALREADY_DELEGATED | step is already one exact command line over scripts/check.py; interface audit shows mentioned in body, argparse present, --help works, exit codes 0/1/2 documented in the step itself | - |
| s2 | "Read the findings JSON and decide which flagged items actually matter for" (L12-13) | numbered-list | 39 | CLAUDE | decides which findings matter for this release's audience; the same missing heading is a defect on a public note and fine on an internal one, so reasonable runs should differ. check.py already applies every mechanical rule, so no mechanical shell is left to strip into a second script | - |
| s3 | "Write a short, plainly-worded explanation for each item worth fixing, in" (L14-15) | numbered-list | 26 | CLAUDE | writes prose the user reads, in the project's voice; a script would only re-gather the findings JSON Claude already holds from s1, adding a dependency without removing tokens or variance. The step names no checkable bound ("short" is not a number), so there is nothing to lint afterwards | - |

## What the target's own data says

`sample_target_data.py` found one data directory: `notes/`, holding a single file, `welcome.md` (3 lines, first line `# Welcome improvements`). No first-line outliers.

That file starts with `# `, so `python3 scripts/check.py notes/ --json` prints `[]` and exits 0. I ran it to confirm. The shipped data therefore never reaches steps 2 and 3 — the skill ships no note that trips the findings branch. This is a fixture gap, not a delegation gap: the workflow is correctly split, but nothing in the repo exercises the exit-1 path, so a regression in `check.py`'s findings branch would go unnoticed. Adding one `notes/` file whose first line is not a heading would cover it.

## Why nothing else converts

The script-first rule says every step is SCRIPT until something specific stops it. Here two things stop it.

Step 2 is contextual re-triage, the classic HYBRID shape — a script lists candidates, Claude judges them. But `check.py` already *is* that script. It enumerates every finding and applies the whole mechanical rule set. What remains is the audience call, and a script that answered it would encode one arbitrary policy ("internal notes are exempt") as if it were fact.

Step 3 is prose the user reads. Its script could only gather source material Claude must read in full anyway, so it adds a dependency without removing tokens or variance. A lint would be worth it if the step named a checkable bound — a word cap, a required section — but "short, plainly-worded" is not checkable.

## Nothing to apply

No SCRIPT or HYBRID rows means no gate and no writes. Your target SKILL.md is unchanged.

One optional follow-up, unrelated to scripting: run `skillit:review` on the skill for a triggering and structure pass. Its `description` covers "review or polish release notes" but not near-miss phrasings like "check my changelog" or "does this release note read okay", which is the usual reason a skill under-fires.
