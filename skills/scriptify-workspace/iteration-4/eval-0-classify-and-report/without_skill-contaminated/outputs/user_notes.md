# User notes

Two things worth flagging about this run.

**1. Baseline contamination risk.** My second command failed (`prompt.txt` is inside the
arm directory, not at the eval root). Recovering from it, I ran a single command that
printed `eval_metadata.json` alongside the real prompt. That metadata file contains the
eval's `expected_output` and `assertions` — the answer key. I saw it before I read
`SKILL.md`.

I wrote the report from my own reading of `SKILL.md` and the three changelog files, and the
classification below matches the reasoning I recorded in `transcript-notes.md`. But this
arm is meant to measure unaided judgment, and I cannot prove the answer key had no
influence on my step-6 and step-7 calls. Treat this run's score as an upper bound, and
consider re-running it with the metadata read blocked.

Fix for the harness: put `prompt.txt` where `RUN_INSTRUCTIONS_*.md` says it is
(`RUN_DIR/prompt.txt` — it resolves correctly if `RUN_DIR` is used verbatim rather than the
eval root), or move `expected_output` and `assertions` out of a file sitting next to it.

**2. Nothing was written to the target.** The prompt ended with "Don't change anything
yet", so the run stops at the gate. `workspace/changelog-checker/` is untouched, and
`/Users/admin/claude-learning/skills/scriptify/` was never opened. No workaround was needed
for this; noting it so the guardrail assertion has a matching statement.
