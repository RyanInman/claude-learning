# JSON Schemas

This document defines the JSON schemas used by this skill.

The three agent-produced files (`grading.json`, `comparison.json`, `analysis.json`) are specified in their agent prompts, which are the source of truth — this document only points to them, because two hand-maintained copies of a schema drift apart.

## Contents

- [evals.json](#evalsjson)
- [eval_metadata.json](#eval_metadatajson)
- [grading.json](#gradingjson)
- [metrics.json](#metricsjson)
- [timing.json](#timingjson)
- [benchmark.json](#benchmarkjson)
- [comparison.json](#comparisonjson)
- [analysis.json](#analysisjson)
- [feedback.json](#feedbackjson)

---

## evals.json

Defines the evals for a skill. Located at `evals/evals.json` within the skill directory.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "eval_name": "descriptive-name-here",
      "prompt": "User's example prompt",
      "expected_output": "Description of expected result",
      "files": ["evals/files/sample1.pdf"],
      "expectations": [
        "The output includes X",
        "The skill used script Y"
      ]
    }
  ]
}
```

**Fields:**
- `skill_name`: Name matching the skill's frontmatter
- `evals[].id`: Unique integer identifier
- `evals[].eval_name`: Optional descriptive name; reused as the `eval-<ID>-<name>` directory name
- `evals[].prompt`: The task to execute
- `evals[].expected_output`: Human-readable description of success
- `evals[].files`: Optional list of input file paths (relative to skill root)
- `evals[].expectations`: List of verifiable statements

---

## eval_metadata.json

Per-test-case metadata for a run. Located at `<workspace>/iteration-<N>/eval-<ID>-<name>/eval_metadata.json`. The worked example lives in `references/running-evals.md` (Step 1) — read it there. Fields: `eval_id`, `eval_name`, `prompt`, `expectations` (empty until Step 2 fills it).

---

## grading.json

Output from the grader agent. Located at `<run-dir>/grading.json`. The full schema with a worked example lives in `agents/grader.md` (Output Format section) — read it there.

Viewer constraint worth restating: the `expectations` array must use the exact field names `text`, `passed`, and `evidence` (not `name`/`met`/`details` or other variants) — the viewer reads them literally.

---

## metrics.json

Written by the test-run subagent — the run template in `references/running-evals.md` requests it. Located at `<run-dir>/outputs/metrics.json`. Optional: the grader and `aggregate_benchmark.py` read it when present and report zeros when absent.

```json
{
  "tool_calls": {
    "Read": 5,
    "Write": 2,
    "Bash": 8,
    "Edit": 1,
    "Glob": 2,
    "Grep": 0
  },
  "total_tool_calls": 18,
  "total_steps": 6,
  "files_created": ["filled_form.pdf", "field_values.json"],
  "errors_encountered": 0,
  "output_chars": 12450,
  "transcript_chars": 3200
}
```

**Fields:**
- `tool_calls`: Count per tool type
- `total_tool_calls`: Sum of all tool calls
- `total_steps`: Number of major execution steps
- `files_created`: List of output files created
- `errors_encountered`: Number of errors during execution
- `output_chars`: Total character count of output files
- `transcript_chars`: Character count of transcript

---

## timing.json

Wall clock timing for a run. Located at `<run-dir>/timing.json`.

**How to capture:** When a subagent task completes, the task notification includes `total_tokens` and `duration_ms`. Save these immediately — the harness does not persist them anywhere else; you cannot recover them after the fact.

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

These three fields are all this file holds. The grader records executor and grader durations separately, in the `timing` block of `grading.json`.

---

## benchmark.json

Written by `scripts/aggregate_benchmark.py`. Located at `<workspace>/iteration-<N>/benchmark.json`.

```json
{
  "metadata": {
    "skill_name": "pdf",
    "skill_path": "/path/to/pdf",
    "executor_model": "claude-sonnet-4-20250514",
    "analyzer_model": "most-capable-model",
    "timestamp": "2026-01-15T10:30:00Z",
    "evals_run": [1, 2, 3],
    "runs_per_configuration": 3
  },

  "runs": [
    {
      "eval_id": 1,
      "eval_name": "Ocean",
      "configuration": "with_skill",
      "run_number": 1,
      "result": {
        "pass_rate": 0.85,
        "passed": 6,
        "failed": 1,
        "total": 7,
        "time_seconds": 42.5,
        "tokens": 3800,
        "tool_calls": 18,
        "errors": 0
      },
      "expectations": [
        {"text": "...", "passed": true, "evidence": "..."}
      ],
      "notes": [
        "Used 2023 data, may be stale",
        "Fell back to text overlay for non-fillable fields"
      ]
    }
  ],

  "run_summary": {
    "with_skill": {
      "pass_rate": {"mean": 0.85, "stddev": 0.05, "min": 0.80, "max": 0.90},
      "time_seconds": {"mean": 45.0, "stddev": 12.0, "min": 32.0, "max": 58.0},
      "tokens": {"mean": 3800, "stddev": 400, "min": 3200, "max": 4100}
    },
    "without_skill": {
      "pass_rate": {"mean": 0.35, "stddev": 0.08, "min": 0.28, "max": 0.45},
      "time_seconds": {"mean": 32.0, "stddev": 8.0, "min": 24.0, "max": 42.0},
      "tokens": {"mean": 2100, "stddev": 300, "min": 1800, "max": 2500}
    },
    "delta": {
      "pass_rate": "+0.50",
      "time_seconds": "+13.0",
      "tokens": "+1700"
    }
  },

  "notes": [
    "Expectation 'Output is a PDF file' passes 100% in both configurations - may not differentiate skill value",
    "Eval 3 shows high variance (50% ± 40%) - may be flaky or model-dependent",
    "Without-skill runs consistently fail on table extraction expectations",
    "Skill adds 13s average execution time but improves pass rate by 50%"
  ]
}
```

**Fields:**
- `metadata`: Information about the benchmark run
  - `skill_name`: Name of the skill
  - `timestamp`: When the benchmark was run
  - `evals_run`: List of eval names or IDs
  - `runs_per_configuration`: Number of runs per config (e.g. 3)
- `runs[]`: Individual run results
  - `eval_id`: Numeric eval identifier
  - `eval_name`: Human-readable eval name (used as section header in the viewer)
  - `configuration`: One of `"with_skill"`, `"without_skill"`, `"new_skill"`, `"old_skill"` — the viewer matches these exact strings for grouping and color coding, and treats `"without_skill"` and `"old_skill"` as the baseline group
  - `run_number`: Integer run number (1, 2, 3...)
  - `result`: Nested object with `pass_rate`, `passed`, `total`, `time_seconds`, `tokens`, `errors`
- `run_summary`: Statistical aggregates per configuration
  - `with_skill` / `without_skill`: Each contains `pass_rate`, `time_seconds`, `tokens` objects with `mean` and `stddev` fields
  - `delta`: Difference strings like `"+0.50"`, `"+13.0"`, `"+1700"`
- `notes`: Freeform observations from the analyzer

**Important:** The viewer reads these field names exactly. Using `config` instead of `configuration`, or putting `pass_rate` at the top level of a run instead of nested under `result`, will cause the viewer to show empty/zero values. Always reference this schema when generating benchmark.json manually.

---

## comparison.json

Output from blind comparator. Located at `<grading-dir>/comparison-N.json`. The full schema with a worked example lives in `agents/comparator.md` (Output Format section) — read it there.

---

## analysis.json

Output from post-hoc analyzer. Located at `<grading-dir>/analysis.json`. The full schema with a worked example lives in `agents/analyzer.md` (Output Format section) — read it there.

---

## feedback.json

Written by the eval viewer when the user clicks "Submit All Reviews". The server flow saves it into the iteration directory; the static/Cowork flow downloads it, and you copy it into the workspace. The worked example lives in `references/running-evals.md` (Step 5) — read it there. Fields: `reviews[]` (`run_id`, `feedback`, `timestamp`) and `status`.
