# Evals, baselines, and re-presented review

Read this file only when the user asks for evals, a baseline, or a benchmark. Evals are off by default in the create-2 workflow, because a baseline loop costs several subagent runs. The re-presented-review section applies to every skill.

## Why a baseline helps

Instructions written before observing failures document the author's guesses. Instructions written after watching Claude fail fix real failures. A baseline run is the most rigorous way to watch, and reported failures from the user are the cheap way. Build the eval, run it without the skill, and keep only the lines that close an observed gap. A skill that only ties its baseline should be retired, because the model has outgrown it and its tokens now buy nothing.

## evals.json schema

Store in `evals/evals.json` inside the skill folder:

```json
{
  "skill_name": "my-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "verbatim realistic user prompt",
      "expected_output": "what a correct result looks like",
      "assertions": ["objectively checkable statement", "..."],
      "files": []
    }
  ]
}
```

Write the prompts the way real users type: concrete file names, backstory, casual phrasing, typos. Abstract prompts ("format this data") test nothing.

Write assertions only for objectively checkable facts (a file exists, a section is present, a number matches). Leave subjective quality (tone, design) to human review, because a forced assertion on a judgment call produces noise, not signal.

## Running a comparison

1. Spawn the with-skill run and the no-skill baseline in the same turn, one subagent each, so both finish together.
2. Save each run's outputs to its own folder (`eval-1/with_skill/`, `eval-1/without_skill/`).
3. Grade each assertion against the outputs. Prefer a checking script over eyeballing, because a script grades the same way on every iteration.
4. Read the transcripts, not only the outputs. Repeated work across runs (every subagent wrote the same helper) is the signal to bundle that helper as a script. Wasted detours are the signal to cut the body lines that caused them.

Keep the grader isolated from the author where subagents allow it, because an agent grading its own output inherits its own biases.

## Re-presenting results for human review

Reviewer attention is the scarcest resource in the loop: working memory holds about four chunks, and plausible-looking output invites rubber-stamping. Re-present instead of dumping:

1. Lead with a three-sentence summary of what changed and why.
2. List assumptions made while drafting.
3. Add a least-confident section - the two or three spots most likely to be wrong and what went untested. Author annotation measurably cuts defect density by pointing the reviewer at risk.
4. Show with-skill and baseline outputs side by side per eval, so the reviewer judges the delta, not the prose.
5. Keep each review unit small and cap sessions near an hour, because defect detection collapses past roughly 400 lines or 90 minutes.

For a high-stakes skill, add an adversarial pass: a fresh subagent told to attack the draft - "find the three instructions most likely to misfire, the missing edge cases, and any claim the body makes that the scripts do not back". A fresh attacker catches what the author's context hides.

## Iterating on feedback

- Generalize the fix. The user iterates on three examples, but the skill will run on thousands of prompts; a patch that hard-codes the example overfits. Change the rule or its reason, not the instance.
- Cut lines that caused detours in transcripts. Lean bodies outperform thorough ones.
- Re-run the same evals after every revision so scores compare across iterations.
- Stop when with-skill beats baseline on the assertions and the user signs off.
