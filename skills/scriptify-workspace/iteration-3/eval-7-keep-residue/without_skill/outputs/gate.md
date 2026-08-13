# Choice point

Asked after classifying the seven workflow steps, before editing the skill.

**Question:** I classified the seven workflow steps into deterministic work a script can do
exactly and judgment work that has to stay in prose. Step 6 splits across both. Which do you want
me to move into a bundled script?

**Options:**

- **A — Apply all.** Move steps 1, 2, 3, 5 and the validation half of step 6 into
  `scripts/check_changelogs.py`. Keep step 4 (narrative), step 7 (clarity flags), and the
  judgment half of step 6 (does this `Misc` entry belong elsewhere) as prose in `SKILL.md`.
- **B — Counting only.** Script steps 1, 2, 3 and leave table rendering and category validation
  in prose.
- **C — Tell me the classification and change nothing.**

**Resolution:** `prompt.txt` says "apply all of them", so I took option A and continued without
waiting. It also says to keep the test fixtures and the manifest inside the skill afterward, so
`tests/` stays in the skill folder rather than being deleted as scaffolding.
