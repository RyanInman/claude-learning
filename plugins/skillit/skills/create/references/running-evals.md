# Running and evaluating test cases

## Contents

- [Step 1: Spawn all runs (with-skill AND baseline) in the same turn](#step-1-spawn-all-runs-with-skill-and-baseline-in-the-same-turn)
- [Step 2: While runs are in progress, draft expectations](#step-2-while-runs-are-in-progress-draft-expectations)
- [Step 3: As runs complete, capture timing data](#step-3-as-runs-complete-capture-timing-data)
- [Step 4: Grade, aggregate, and launch the viewer](#step-4-grade-aggregate-and-launch-the-viewer)
- [What the user sees in the viewer](#what-the-user-sees-in-the-viewer)
- [Step 5: Read the feedback](#step-5-read-the-feedback)

This is the full eval-running sequence, referenced from SKILL.md. It's one continuous sequence; don't stop partway through. Don't use `/skill-test` or any other testing skill: they skip the paired baseline and the feedback viewer this loop depends on.

The baseline matters as much as the skill. You're not just checking that the skill produces good output — you're checking that it *beats what Claude does without it*. Always run both, and judge the skill by the delta, not by whether the with-skill run looks fine on its own.

Put results in `<skill-name>-workspace/` as a sibling to the skill directory. When the skill lives inside a plugin's `skills/` folder, place the workspace outside the plugin instead. The plugin loader treats every folder under `skills/` as a skill, and the workspace would ship to installers. Within the workspace, organize results by iteration (`iteration-1/`, `iteration-2/`, etc.) and within that, each test case gets a directory (`eval-0-<name>/`, `eval-1-<name>/`, etc.). Don't create all of this upfront — just create directories as you go.

## Step 1: Spawn all runs (with-skill AND baseline) in the same turn

For each test case, spawn two subagents in the same turn — one with the skill, one without. This is important: don't run the with-skill runs first with baselines afterwards. Launch everything at once so it all finishes around the same time.

**With-skill run:**

```
Execute this task:
- Skill path: <path-to-skill>
- Task: <eval prompt>
- Input files: <eval files if any, or "none">
- Save outputs to: <workspace>/iteration-<N>/eval-<ID>/with_skill/outputs/
- Outputs to save: <what the user cares about — e.g., "the .docx file", "the final CSV">
- After finishing, also write metrics.json to the outputs directory:
  {"tool_calls": {"<tool>": <count>, ...}, "total_tool_calls": N,
   "total_steps": N, "files_created": [...], "errors_encountered": N,
   "output_chars": N, "transcript_chars": N}
- If anything was uncertain or needed a workaround, also write user_notes.md there
```

The grader and the benchmark read `metrics.json` and `user_notes.md` when present (schemas in `references/schemas.md`); without them, the tool-call and error columns in the benchmark show 0. Include the same two instructions in the baseline prompt.

**Baseline run** (same prompt, but the baseline depends on context):
- **Creating a new skill**: no skill at all. Same prompt, no skill path, save to `without_skill/outputs/`.
- **Improving an existing skill**: the old version. Before editing, snapshot the skill (`cp -r <skill-path> <workspace>/skill-snapshot/`), then point the baseline subagent at the snapshot. Save to `old_skill/outputs/`.

Write an `eval_metadata.json` for each test case (expectations can be empty for now). Give each eval a descriptive name based on what it's testing. Name the directory `eval-<ID>-<name>` (e.g. `eval-0-table-extraction`) — keep the `eval-` prefix, because `aggregate_benchmark.py` only discovers directories that start with `eval-`. If this iteration uses new or modified eval prompts, create these files for each new eval directory — don't assume they carry over from previous iterations.

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "The user's task prompt",
  "expectations": []
}
```

## Step 2: While runs are in progress, draft expectations

While the runs execute, draft quantitative expectations for each test case and explain them to the user. If expectations already exist in `evals/evals.json`, review them and explain what they check.

Good expectations are objectively verifiable and have descriptive names — they should read clearly in the benchmark viewer so someone glancing at the results immediately understands what each one checks. Subjective skills (writing style, design quality) are better evaluated qualitatively — don't force expectations onto things that need human judgment.

Update the `eval_metadata.json` files and `evals/evals.json` with the expectations once drafted. Also explain to the user what they'll see in the viewer — both the qualitative outputs and the quantitative benchmark.

## Step 3: As runs complete, capture timing data

When each subagent task completes, you receive a notification containing `total_tokens` and `duration_ms`. Save this data immediately to `timing.json` in the run directory:

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

This is the only opportunity to capture this data — it comes through the task notification and isn't persisted elsewhere. Process each notification as it arrives rather than trying to batch them.

## Step 4: Grade, aggregate, and launch the viewer

Once all runs are done:

1. **Grade each run** — spawn a grader subagent (or grade inline) that reads `agents/grader.md` and evaluates each expectation against the outputs. Save results to `grading.json` in each run directory. The grading.json expectations array must use the fields `text`, `passed`, and `evidence` (not `name`/`met`/`details` or other variants) — the viewer depends on these exact field names. For expectations that can be checked programmatically, write and run a script rather than eyeballing it — scripts are faster, more reliable, and can be reused across iterations.

2. **Aggregate into benchmark** — run the aggregation script from the skill directory, because `-m scripts.aggregate_benchmark` resolves the `scripts` package relative to the working directory:
   ```bash
   cd ${CLAUDE_SKILL_DIR} && python3 -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
   ```
   This produces `benchmark.json` and `benchmark.md` with pass_rate, time, and tokens for each configuration, with mean ± stddev and the delta. If generating benchmark.json manually, see `references/schemas.md` for the exact schema the viewer expects, and put each with_skill run before its baseline counterpart in the `runs` array.

3. **Do an analyst pass** — read the benchmark data and surface patterns the aggregate stats might hide. See `agents/analyzer.md` (the "Analyzing Benchmark Results" section) for what to look for — things like expectations that always pass regardless of skill (non-discriminating), high-variance evals (possibly flaky), and time/token tradeoffs.

4. **Launch the viewer** with both qualitative outputs and quantitative data:
   ```bash
   nohup python3 ${CLAUDE_SKILL_DIR}/scripts/generate_review.py \
     <workspace>/iteration-N \
     --skill-name "my-skill" \
     --benchmark <workspace>/iteration-N/benchmark.json \
     > /dev/null 2>&1 &
   VIEWER_PID=$!
   ```
   For iteration 2+, also pass `--previous-workspace <workspace>/iteration-<N-1>`.

   **Cowork / headless environments:** If `webbrowser.open()` is not available or the environment has no display, use `--static <output_path>` to write a standalone HTML file instead of starting a server. The viewer downloads feedback as a `feedback.json` file when the user clicks "Submit All Reviews". After download, copy `feedback.json` into the workspace directory for the next iteration to pick up.

Use generate_review.py for the viewer; don't write custom HTML.

5. **Tell the user** something like: "I've opened the results in your browser. There are two tabs — 'Outputs' lets you click through each test case and leave feedback, 'Benchmark' shows the quantitative comparison. When you're done, come back here and let me know."

## What the user sees in the viewer

The "Outputs" tab shows one test case at a time:
- **Prompt**: the task that was given
- **Output**: the files the skill produced, rendered inline where possible
- **Previous Output** (iteration 2+): collapsed section showing last iteration's output
- **Formal Grades** (if grading was run): collapsed section showing expectation pass/fail
- **Feedback**: a textbox that auto-saves as they type
- **Previous Feedback** (iteration 2+): their comments from last time, shown below the textbox

The "Benchmark" tab shows the stats summary: pass rates, timing, and token usage for each configuration, with per-eval breakdowns and analyst observations.

Navigation is via prev/next buttons or arrow keys. When done, they click "Submit All Reviews" which saves all feedback to `feedback.json`.

## Step 5: Read the feedback

When the user tells you they're done, read `feedback.json`:

```json
{
  "reviews": [
    {"run_id": "eval-0-with_skill", "feedback": "the chart is missing axis labels", "timestamp": "..."},
    {"run_id": "eval-1-with_skill", "feedback": "", "timestamp": "..."},
    {"run_id": "eval-2-with_skill", "feedback": "perfect, love this", "timestamp": "..."}
  ],
  "status": "complete"
}
```

Empty feedback means the user thought it was fine. Focus your improvements on the test cases where the user had specific complaints.

Kill the viewer server when you're done with it:

```bash
kill $VIEWER_PID 2>/dev/null
```

