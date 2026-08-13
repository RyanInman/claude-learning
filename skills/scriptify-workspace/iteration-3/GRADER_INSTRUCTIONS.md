# Grader instructions

You grade ONE eval, both arms, for the scriptify skill benchmark.

You are given `EVAL_DIR`. It contains `eval_metadata.json` (the prompt and the pre-registered
`assertions`) and two run directories: `with_skill/` and `without_skill/`.

## Inputs per arm

- `outputs/report.md` — what the run would have shown the user
- `outputs/gate.md` — the choice point it would have presented
- `outputs/transcript-notes.md` — commands run and files written
- `facts.json` — mechanical ground truth already collected: `target_tree_diff` (added/removed/
  modified vs the pristine fixture), `scripts` (every .py with its `--help` exit status and
  whether it pre-existed), `new_script_count`, `skill_md_diff`, and for eval 6 `collision`,
  for eval 7 `residue`.
- `workspace/` — the run's own copy of the target skill, as the run left it

## Rules

Grade each assertion in `assertions` for each arm independently.

- Prefer `facts.json` over any claim in `report.md`. A run asserting it wrote three scripts
  loses to a `new_script_count` of one, because the run can be wrong about itself.
- Run commands yourself when an assertion is checkable. Do not eyeball an exit code you can
  reproduce.
- Grade the assertion as written. Do not soften wording that a run failed on, and do not
  invent a stricter reading that a run passed on, because the assertions were fixed before
  the runs and re-reading them after the fact destroys the comparison.
- Never grade the ORDER in which a run did things. Ordering is only visible in
  `transcript-notes.md`, which the run writes about itself, and no independent tool-call log is
  kept. Assertions now state the end state instead; grade that.
- Each assertion carries a `tier`. Grade `signal` assertions here. A `guardrail` assertion is
  decided by `collect_facts.py`, so copy its mechanical result into your evidence rather than
  re-deciding it by eye.
- When an assertion cannot be satisfied by one arm by construction (it names a scriptify
  artifact or a scriptify path convention the baseline had no reason to produce), still grade
  it as written, and say so in `evidence` with the words `DEFINITIONAL`.
- When both arms pass or both fail, say so in `evidence` with the word `NON-DISCRIMINATING`.

## Calibration — do this first

Grade these two fixed items before you touch the eval. They anchor borderline vocabulary so ten
independent graders return comparable verdicts, because nothing else in this brief tells you how
strict to be.

**C1 — expect PASS.** Assertion: "a verification result is reported for each generated script."
Run output: a table with a Result column reading `exit 1, flagged v1.2.0.md` and
`exit 2, usage error`, and no line containing the word PASS.
Correct verdict: **passed**. A per-check outcome in any form satisfies this; the literal token
PASS is not required.

**C2 — expect FAIL.** Assertion: "every generated script exits 0 on `--help`."
Run output: the report states "all scripts support --help"; `facts.json` shows
`help.exit: 2` for one script.
Correct verdict: **failed**. `facts.json` beats the run's claim about itself.

Put your two verdicts in `grading.json` under `"calibration": {"C1": true, "C2": false}`. If your
verdicts disagree with the above, re-read this brief before grading — a grader that misses the
anchors is discarded.

## Output

Write `grading.json` into EACH arm directory, using exactly these field names:

```json
{"expectations": [{"text": "<assertion text verbatim>", "passed": true, "evidence": "<what you checked and what you found, incl. the command and its exit code>"}]}
```

`passed` must be a JSON boolean. The viewer and `aggregate_benchmark.py` depend on the field
names `text`, `passed`, and `evidence`.

Write the files with a Bash heredoc or `python3`, not the Write tool — the harness blocks
subagents from writing report-shaped files, and grading.json trips that guard.

## Final message

Return at most 12 lines: per arm, the pass count out of total, and every assertion where the
two arms differ.
