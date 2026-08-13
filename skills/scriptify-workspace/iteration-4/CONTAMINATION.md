# Answer-key exposure, iteration-4

Two baseline runs read `eval_metadata.json` — which carries `expected_output` and the grader
assertions — before the keys were relocated to `_answer_keys/`. Both runs disclosed it themselves,
unprompted, in `user_notes.md`.

| run | exposure | assessment |
|-----|----------|------------|
| eval-0 without_skill | printed the file while recovering from a wrong-directory `cat`, before reading SKILL.md | plausibly benign; classification matches its iteration-3 result |
| eval-3 without_skill | read it before realising what it was | likely material: it shipped `--help`, exit-2 handling and a smoke test, which is exactly what eval 3's remaining assertion grades and exactly where the iteration-3 baseline failed |
| eval-8 with_skill | first Bash call also cat'd the file, before classifying | the leak hit both arms, not only baselines. Its verdicts match its iteration-3 verdicts, so probably benign, but it is not a blind sample |

Cause: `eval_metadata.json` sat at the eval root, one level above each arm's `prompt.txt`. A run
that mistyped the path found the answer key instead of an error.

Fix applied mid-fleet: all 10 keys moved to `iteration-4/_answer_keys/<eval>.json`, outside every
run directory. Graders read them from there.

The three affected runs are being re-run against the relocated keys. The contaminated runs are preserved as
`without_skill-contaminated/` rather than deleted, because discarding the evidence would hide the
defect from anyone reading these results later.
