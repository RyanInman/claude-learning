# Guard calibration — 2026-08-05

Purpose: prove the three always-pass expectations can actually fail. Observed passes cannot
distinguish genuine checking from confabulation. Only a case whose correct verdict is *fail* can
(debate-review, Objection 5).

Method: two doctored reports, graded blind by a fresh grader subagent that was not told they were
doctored.

- `doctored-report-scriptify.md` carries two probes against `../fixtures/scriptify/SKILL.md`:
  a violation cited at frontmatter line 4, and a fabricated quote attributed to line 24 that
  appears nowhere in the target.
- `doctored-report-tutorial.md` carries one probe against `../fixtures/output-styles-tutorial.md`:
  a violation cited at line 66, inside the fenced code block (lines 59-68). Its quote is verbatim
  on purpose, so only the code-block guard is under test.

Verdict (`grading.json`): all three probes failed their guard, each for the planted reason.

- The verbatim-quote guard caught the fabricated quote.
- The frontmatter-exemption guard caught the line-4 citation.
- The code-block-exemption guard caught the line-66 citation.

3/3 guards verified able to fire.

Re-run this calibration after any change to the expectations' wording or to the grading procedure.
A stale calibration decays back into the article of faith it replaced.
