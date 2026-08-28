---
name: create
description: Author, improve, and benchmark Claude Code skills - write the trigger description before the body, keep only the instructions that fix an observed failure, compile mechanical steps into scripts, and verify with human review, then loop skillit:review and steyle:grading-markdown subagents until clean. Evals stay off unless asked. Use whenever the user wants to create a skill, turn a workflow or repeated task into a reusable skill, rewrite or optimize an existing SKILL.md, benchmark a skill against a no-skill baseline, or fix a skill that isn't triggering - even if they never say "skill" and instead describe wanting a repeatable task done the same way every time. Do NOT use when the user wants the task itself performed rather than packaged. Do NOT use for a read-only audit with no edits requested (use skillit:review). Do NOT use when a lighter container fits - an always-true convention belongs in CLAUDE.md, a per-path rule in .claude/rules, and a guarantee that must hold every run in a hook.
---

# create: skill authoring

Build skills that earn their tokens. Every line a skill loads competes with the live task for a finite attention budget, so the job is not to document the task - it is to write the minimum that measurably beats Claude working without the skill.

Four beliefs drive the workflow. Each phase below applies one.

1. **The description is a router, not documentation.** It alone decides whether the body ever loads, and Claude under-triggers by default.
2. **Only an observed failure earns an instruction.** Watch Claude attempt the task, from the conversation history or from a baseline run, and write lines that close the gaps you saw. Instructions that fix no observed failure are noise.
3. **Deterministic work belongs in scripts.** A script's source never enters context; only its output does. Prose re-spends attention on every run.
4. **The user reviews re-presentations, not raw drafts.** A summary, an assumptions list, and a least-confident section direct scarce reviewer attention to the highest-risk spots.

## Workflow

Run the phases in order. Skip a phase only when its output already exists (for example, the user arrives with a finished draft - start at Phase 4).

### Phase 1 - Fit check

Confirm a skill is the right container before writing one, because a misfiled instruction taxes every session it loads into.

- Always-true convention (naming rule, code style) → CLAUDE.md.
- Rule scoped to certain paths → `.claude/rules/*.md` with a `paths:` glob.
- Guarantee that must hold on every run ("never push to main") → a hook. A rule in prose is a request; a hook is enforcement.
- Multi-step procedure, bundled scripts, or domain knowledge used on demand → a skill.

If the request fails the fit check, say so, name the right container, and offer to build that instead.

### Phase 2 - Intake

Collect four facts from the user or the conversation history. Draft answers from context first, then confirm, because the conversation often already contains the workflow being packaged.

1. What the skill enables Claude to do.
2. The verbatim phrases a user would type to trigger it, casual phrasing included.
3. The expected output and its format.
4. What "done and correct" looks like - the check a grader could run.

### Phase 3 - Failure inventory

List the failures the skill must fix. Draw them from what the user reports and from Claude attempts already in the conversation. Each failure becomes an instruction; a behavior Claude already gets right becomes nothing, because restating defaults spends tokens without changing output.

Skip evals unless the user asks for them. Formal evals and a no-skill baseline are off by default, because a full baseline loop costs several subagent runs and most skills ship from reported failures alone. Run Phase 3b only when the user says "eval", "baseline", "benchmark", "measure", or "compare against no skill", or when they ask whether an existing skill still earns its tokens.

### Phase 3b - Evals and baseline (optional)

Write 3 eval prompts into `evals/evals.json` before touching the skill (see `references/evals.md` for the schema). Run each prompt in a subagent with no skill. Save the outputs and add their failures to the Phase 3 inventory. If the baseline fails nowhere, tell the user a skill is not needed and stop.

### Phase 4 - Description first

Write the frontmatter description before the body. Read `references/description.md` for the rules. In short: third person, what-plus-when, verbatim trigger phrases, negative triggers for near-miss cases, deliberately pushy because under-triggering is the default failure.

Test it before writing the body: ask a fresh subagent "When would you use this skill?" with only the description visible. Missing keywords show up immediately, and fixing the router costs less before the body exists.

### Phase 5 - Body

Write the minimum body that fixes the Phase 3 failures. Read `references/structure.md` for folder anatomy and splitting rules. While drafting:

- Open every instruction with a command verb. Attach a reason to every non-obvious rule, because a reason lets Claude generalize to inputs the rule never anticipated.
- Include at least one verbatim input→output example, untouched by style editing, because one real example teaches more than fifty lines of abstract rules.
- Move every deterministic step into `scripts/` and tell the body to run it, not re-derive it. Read `references/structure.md` (Scripts section) for the interface rules.
- Move cold knowledge into `references/`, one level deep, pointed to with "read X when Y" lines. A pointer costs nothing until followed; inlined content costs on every load.
- End with a Gotchas section - the observed failure points with their reasons. This is the highest-signal content in the file.
- Keep the body under 200 lines. Split to references from 150. Put the rules that matter most first, because attention follows a U-curve and the middle of a long file is a dead zone.

### Phase 6 - Validate and style-pass

Run the validator, then fix what it reports:

```
python3 scripts/validate_skill.py <path-to-skill-folder>
```

It checks frontmatter constraints, line budgets, vague-verb instructions, ALL-CAPS directives, `@` imports, and reference nesting. Then do one manual style pass against the checklist in `references/style.md`, because the validator catches patterns, not prose quality.

### Phase 7 - Re-present for review

Never hand the user a raw draft. Present, in this order:

1. A three-sentence summary of what the skill does and how.
2. The assumptions made during drafting.
3. A **least-confident** section: the two or three choices most likely to be wrong, and what was not tested. This is the AI analogue of author annotation, which measurably cuts defect density by directing the reviewer to risk.
4. The description and body, last.

When Phase 3b ran, run the with-skill evals too and show both outputs side by side, then ask for feedback on the comparison rather than the prose. Without evals, ask the user to check the draft against the Phase 3 failure list.

### Phase 8 - Iterate

Generalize from feedback rather than patching the literal example, because the skill will run on prompts nobody previewed. When a fix wants to be an ALL-CAPS rule, reframe it as rule-plus-reason instead. Re-run Phases 6-7 after each revision. Stop when every Phase 3 failure is fixed and the user signs off. When Phase 3b ran and with-skill only ties baseline, recommend retiring the skill - the model has outgrown it.

### Phase 9 - Review loop

Run this phase from the main orchestrator after the user signs off in Phase 8. The orchestrator applies every fix itself; subagents only report. A subagent that edits the skill loses the Phase 3 failure list and the user's decisions, so its fixes drift from the design.

1. Deploy a fresh subagent. Tell it to invoke `skillit:review` on the skill folder and return the prioritized finding list, each finding with file, line, and proposed fix. Tell it not to edit any file.
2. Apply the findings in the orchestrator. Reject a finding that reverses a Phase 8 user decision, and record the rejection so the next reviewer does not repeat it.
3. Deploy a new subagent for another review pass. Include the rejected findings in its prompt, because a fresh reviewer has no memory of the last round.
4. Repeat steps 2-3 until a pass returns no findings beyond the recorded rejections.

Use a fresh subagent each pass, not a continued one, because a reviewer that already saw the draft anchors on its own prior findings.

### Phase 10 - Grading loop

Run this phase after Phase 9 reaches no findings, because a style pass on a structure that still changes wastes a grade.

1. Deploy a fresh subagent. Tell it to invoke `steyle:grading-markdown` on the skill folder and return the grade plus the complete line-by-line fix list that lifts the target to an A. Tell it not to edit any file.
2. Apply the fix list in the orchestrator. Keep verbatim examples, code blocks, and quoted text untouched, because the style guides exclude them and a "fix" there breaks the example.
3. Deploy a new subagent to grade again.
4. Repeat steps 2-3 until the grade is A.

Re-run `scripts/validate_skill.py` once after the loop ends, because prose fixes can push a line budget over its limit.

## Example

Input (user): "every time I ask for release notes claude formats them differently, can you make it consistent"

Output (Phase 1-2 response): "That's a skill - it's a repeatable procedure with a fixed output format. Two questions before I draft it: 1) Which sections must release notes always contain? 2) Show me one past release note you considered good - I'll use it as the verbatim example."

## Gotchas

- A skill that never fires is indistinguishable from a skill that does not exist. When a finished skill misbehaves, check triggering before checking the body - ask a fresh session "When would you use X?" and compare its answer to the description.
- `@` imports do not work in SKILL.md and inline the file at full token cost where they do work. Write "Read `references/x.md` when Y" instead.
- The body stays in context for the whole session once invoked. Write standing instructions, not one-time setup steps.
- Do not offer tool menus ("use pypdf, or pdfplumber, or..."). Pick one default and give an escape hatch, because a menu forces a re-decision on every run.
- Time-sensitive lines ("before the August API change") rot silently. Keep them out; a skill is not a log.
