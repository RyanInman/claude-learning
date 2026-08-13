# Iteration-4: outstanding work

Session limit reached (resets 1:20pm America/Chicago). Two runs still need execution.

## Re-runs still required

| run | why | state |
|-----|-----|-------|
| eval-3-partial-selection/without_skill | original read the answer key; re-run died mid-work | reset to clean staged state |
| eval-8-dead-step/with_skill | original read the answer key; re-run died at start | reset to clean staged state |

Contaminated originals kept at `<run>-contaminated/` as evidence.

eval-0-classify-and-report/without_skill was successfully re-run clean: report.md, gate.md and
transcript-notes.md are complete and the target is pristine. Only metrics.json is missing, which
feeds the tool-call and error columns already discounted as unreliable.

## Command to resume

Spawn both with the standard arm instructions, adding the answer-key ban:

    RUN_DIR=<path>
    Read iteration-4/RUN_INSTRUCTIONS_<arm>.md and follow it end to end. Write output files with a
    Bash heredoc or python3, not the Write tool. Do not read any eval_metadata.json or anything
    under _answer_keys.

## Then

1. `python3 collect_facts.py .` (deterministic; decides the 12 guardrail assertions)
2. Grade the 10 evals against `_answer_keys/<eval>.json`
3. `cd <skillit create dir> && python3 -m scripts.aggregate_benchmark <iteration-4> --skill-name scriptify --skill-path <scriptify> --executor-model claude-opus-5`
4. `python3 report_by_property.py`
