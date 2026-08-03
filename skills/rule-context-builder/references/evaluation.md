# Evaluation Phase

Use this reference when testing or improving the rule-context-builder skill itself — not during normal use. Run it when you want to verify the skill is routing correctly, generating quality globs, and merging cleanly.

## Test case format

Save to `evals/evals.json` in the skill directory:

```json
{
  "skill_name": "rule-context-builder",
  "evals": [
    {
      "id": 1,
      "eval_name": "style-guide-routing",
      "prompt": "The user's input prompt (paste of notes, file path, etc.)",
      "input_context": "Any pasted prose or file contents the prompt references",
      "expected_routing": {
        "rules": ["<glob> → <topic>"],
        "claude_md": ["<instruction>"],
        "hooks": ["<enforcement>"],
        "skills": ["<procedure>"]
      },
      "assertions": []
    }
  ]
}
```

## Step 1: Spawn with-skill and baseline runs in the same turn

For each test case, launch two subagents simultaneously — one with the skill, one without. Don't run with-skill first and come back for baselines.

Put results in `rule-context-builder-workspace/iteration-<N>/` as a sibling to the skill directory. Each test case gets a directory named after its `eval_name`.

**With-skill run:**
```
Execute this task:
- Skill path: <path-to-skill>
- Task: <eval prompt>
- Input context: <paste of notes or file path>
- Save outputs to: <workspace>/iteration-<N>/<eval-name>/with_skill/outputs/
- Outputs to save: the routing table, all .claude/rules/*.md files written, any CLAUDE.md edits
```

**Baseline run** (no skill):
```
Execute this task — no skill:
- Task: <same eval prompt>
- Save outputs to: <workspace>/iteration-<N>/<eval-name>/without_skill/outputs/
- Outputs to save: same — routing table, rule files, CLAUDE.md edits
```

Write `eval_metadata.json` in each eval directory:
```json
{
  "eval_id": 1,
  "eval_name": "style-guide-routing",
  "prompt": "...",
  "assertions": []
}
```

## Step 2: Draft assertions while runs are in progress

Don't wait. While subagents run, draft assertions for each test case and explain them to the user. Add them to `eval_metadata.json` and `evals/evals.json` once drafted.

**Assertion types for rule-builder:**

| Assertion | What to check | How |
|---|---|---|
| `routing_correct` | Each unit landed at the right destination (rule/hook/CLAUDE.md/skill) | Compare routing table vs `expected_routing` |
| `glob_quoted` | Any glob starting with `*` or `{` is quoted in the written file | Grep rule files for unquoted glob patterns |
| `glob_narrowest` | Glob matches real tree — no `**/*.ts` when `src/api/**/*.ts` fits | Read actual tree, compare to proposed glob |
| `no_clobber` | Existing rule file content was preserved; new bullets appended, not overwritten | Diff before/after if existing rules present |
| `no_contradiction` | Contradictions with existing rules surfaced to user, not silently stacked | Check output for contradiction surface |
| `dedup_correct` | Already-covered rules noted as already-present, not restated | Compare new bullets against existing content |
| `template_compliance` | Written rule files follow the exact template (frontmatter + `paths:` + bullets) | Validate YAML frontmatter and structure |
| `file_lean` | Rule file under ~100 lines | `wc -l` on each written file |
| `creation_flag` | Creation-critical rules flagged with the workaround offer | Check output for creation-time caveat |

## Step 3: Capture timing data as runs complete

When each subagent completes, save timing immediately to `timing.json` in its run directory:
```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

## Step 4: Grade, aggregate, and launch the viewer

1. **Grade** — spawn a grader or grade inline. For each assertion, evaluate against the outputs. Save to `grading.json` in each run directory using fields `text`, `passed`, `evidence`.

2. **Aggregate** — run from the skill-creator directory:
   ```bash
   python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name rule-context-builder
   ```

3. **Analyst pass** — look for non-discriminating assertions (always-pass regardless of skill), high-variance evals, and time/token tradeoffs.

4. **Launch viewer:**
   ```bash
   nohup python <skill-creator-path>/eval-viewer/generate_review.py \
     <workspace>/iteration-N \
     --skill-name "rule-context-builder" \
     --benchmark <workspace>/iteration-N/benchmark.json \
     > /dev/null 2>&1 &
   ```
   For iteration 2+, add `--previous-workspace <workspace>/iteration-<N-1>`. In headless environments, use `--static <output_path>` instead.

5. Tell the user: "Results open in browser — 'Outputs' tab to review each test case and leave feedback, 'Benchmark' for quantitative comparison. Come back when done."

## Step 5: Iterate

Read `feedback.json` when user finishes. Empty feedback = looks good. Improve the skill based on complaints, rerun into `iteration-<N+1>/`, repeat until feedback is empty or you're not making progress.

**Common failure modes to watch for:**
- Routing too broad (dumping everything into rules instead of classifying)
- Globs matching non-existent paths (not grounded in real tree)
- Silently overwriting existing files instead of merging
- Missing the routing table confirm step before writing
