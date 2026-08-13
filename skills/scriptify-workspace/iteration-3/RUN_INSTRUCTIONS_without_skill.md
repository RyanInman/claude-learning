# Eval run instructions (without_skill / baseline arm)

You are executing one skill-evaluation run. You have a `RUN_DIR` given in your task message.

## 1. Read your task

Read `RUN_DIR/prompt.txt`. That text is the user's request. Treat it as if a real user typed it.

## 2. No skill

Complete the task with your own judgment and your normal tools. Do not read
`/Users/admin/claude-learning/skills/scriptify/` — this arm measures what you do unaided, so
consulting it invalidates the comparison.

## 3. Non-interactive rule

You cannot ask the user anything. When you reach a point where you would present choices and wait,
write the exact question and options you would have asked into `RUN_DIR/outputs/gate.md`, then obey
what `prompt.txt` already decided:

- The prompt says "don't change anything" / "just tell me" → stop after the gate. Write nothing
  into the target skill.
- The prompt says "apply all" → treat every change you proposed as approved and continue.
- The prompt names specific steps → do exactly those.
- The target is ineligible to write to and the prompt pre-approves applying → pick a durable
  destination yourself, record it in `gate.md`, and apply there.

## 4. Boundaries

- Work only inside `RUN_DIR/workspace/`. That copy is yours.
- Never read from or write to `/Users/admin/claude-learning/skills/scriptify/evals/fixtures/`.
  That is the pristine baseline the grader diffs against, so touching it destroys the run.
- Put scratch files in `RUN_DIR/scratch/`, not in the target skill folder, unless the task itself
  calls for placing them in the target.

## 5. Outputs

Write these into `RUN_DIR/outputs/`:

- `report.md` — the complete report you would have shown the user, verbatim. Not a summary of it.
- `gate.md` — the choice point you would have presented, or the single word `none`.
- `transcript-notes.md` — what you did in order: each command you ran, its exit code, and each
  file you created or rewrote.
- `metrics.json`:
  ```json
  {"tool_calls": {"<tool>": 0}, "total_tool_calls": 0, "total_steps": 0,
   "files_created": [], "errors_encountered": 0, "output_chars": 0, "transcript_chars": 0}
  ```
- `user_notes.md` — only if something was uncertain or needed a workaround.

## 6. Final message

Your final text is data, not a chat reply. Return at most 10 lines: what you did, what you wrote,
and any failure you hit.
