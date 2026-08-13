# User notes

**Possible contamination.** I read `eval-3-partial-selection/eval_metadata.json` early, in the same
batch as `SKILL.md`, before realizing it holds `expected_output` and the grader assertions. The run
instructions only forbade reading `/Users/admin/claude-learning/skills/scriptify/`, so this was not a
rule violation, but it does mean this baseline arm saw the grading criteria. Discount the run
accordingly, or re-run with that file moved out of the tree.

For what it is worth, my plan — two scripts for steps 1 and 3, a smoke test, and a two-line SKILL.md
diff — was already formed from `prompt.txt` and `SKILL.md`. The metadata did not change the approach.

**Judgment call on step 6.** Step 6 is half deterministic (tag allow-list check) and half judgment
(does a `Misc` entry belong elsewhere). Splitting it would be the right delegation, but it would edit
step 6's prose, which "leave everything else untouched" forbids. I reported the split in `report.md`
and applied nothing.

**Fixture note.** `changelogs/v1.2.0.md` has no version heading. That is a real defect the skill's
step 2 would catch. I left it in place because the run instructions scope me to reviewing the skill,
not repairing its fixtures.
