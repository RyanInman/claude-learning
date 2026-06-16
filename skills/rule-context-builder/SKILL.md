---
name: rule-context-builder
description: >-
  Use when the user wants to turn a prompt, notes, a spec, a style guide, or a markdown file
  into Claude Code path-scoped rules under `.claude/rules/`. Converts loose context into lean,
  correctly-scoped rule files with `paths:` frontmatter, and routes anything that doesn't belong
  in a rule (deterministic guarantees → hooks, multi-step procedures → skills, project-wide
  conventions → CLAUDE.md) to its proper home. Trigger whenever someone says "make this a rule",
  "turn these conventions into .claude/rules", "set up path-scoped rules", "convert my coding
  standards into rules for Claude", or hands over a doc of conventions and asks where it should
  live — even if they don't name a file path explicitly.
---

# Context to Rules

Takes a chunk of context (a prompt, pasted notes, a style guide, an md file) and converts it
into well-formed Claude Code rules under `.claude/rules/`. The value isn't dumping text into a
file — it's *routing*: deciding which instructions are path-scoped conventions (rules), which
are project-wide (CLAUDE.md), which are deterministic guarantees (hooks), and which are
procedures (skills), then writing each to the right place with correct scoping.

The full routing logic, rule syntax, glob quoting rules, and the creation-time gotcha live in
`references/decision-framework.md`. **Read it before classifying** — it's the brain of this skill.

---

## Step 1: Gather the input

Get the context to convert. It arrives as either:
- a **file** the user names → read it fully;
- **pasted text / a prompt** → use it directly.

Then orient on the target repo so you can ground glob proposals in the real layout:

```bash
pwd
ls -la
ls .claude/rules/ 2>/dev/null   # existing rules — extend, don't clobber
```

Read any existing `CLAUDE.md` and **every** `.claude/rules/*.md`, and build an inventory of
what's already there — for each rule file, its `paths:` glob(s) and the topics it covers. New
units merge into this inventory rather than landing in fresh files (Step 5); reading it now is
also how you avoid duplicating or contradicting a rule that already exists.

## Step 2: Decompose into discrete instructions

Break the input into atomic instruction units — one rule per idea. A wall of prose like
"we use pnpm, components in packages/ui use compound components, never push to main, and here's
how to cut a release" is **four** units bound for four different destinations. Splitting first
is what makes correct routing possible.

## Step 3: Classify each unit

Route every unit using the decision tree in `references/decision-framework.md` (enforce-every-time
→ hook; procedure → skill; every-turn project-wide → CLAUDE.md; personal → global; area-specific
convention → path-scoped rule; uncommittable note → CLAUDE.local.md). Build a routing table:

| # | Instruction (short) | Destination | Why | Proposed `paths:` glob |
|---|---|---|---|---|
| 1 | "Use pnpm not npm" | root CLAUDE.md | every turn, project-wide | — |
| 2 | "packages/ui uses compound components" | rule | area-specific convention | `"packages/ui/**"` |
| 3 | "Never push to main" | hook (PreToolUse) | must be enforced deterministically | — |
| 4 | "How to cut a release (7 steps)" | skill | multi-step procedure | — |

Ground glob proposals in the actual tree (e.g. confirm the real test-file pattern with a quick
`find`), and quote any glob starting with `*` or `{`.

## Step 4: Choose the routing scope (ask the user)

Before writing anything, show the routing table and ask how aggressive to be:

1. **Rules only** — write `.claude/rules/` for the rule-bound units; just list the rest.
2. **Route + flag misfits** *(default)* — write the rules, and report each non-rule unit with
   its recommended destination and a one-line why, so the user can place it.
3. **Route + write everywhere** — also write the CLAUDE.md edits, hook stubs in
   `.claude/settings.json`, and skill scaffolds. Largest blast radius — only on explicit yes.

Default to option 2 if the user doesn't care. Respect the choice for the rest of the run.

## Step 5: Place each unit, confirm globs, then write

Before creating any file, reconcile each rule-bound unit against the existing-rules inventory
from Step 1:

- **An existing rule file already covers this scope** (its glob matches the unit's target) →
  the unit belongs *in that file*. Append to it; don't spawn a parallel `api2.md`.
- **No existing file fits** → group same-scope new units into a new file (`api.md`,
  `testing.md`, `ui.md` — as few files as read cleanly).
- **Already covered** — an existing bullet says the same thing → drop the unit and note it as
  already-present. Don't restate.
- **Contradicts an existing rule** (e.g. existing "prefer type aliases", new "use interfaces")
  → do NOT silently append the opposite; contradictory rules across files make Claude behave
  inconsistently. Surface the clash, ask which wins, and replace the old line if they pick the new.

Then, for each file you'll create or touch, present its `paths:` glob(s) and the exact bullets
being added, and **confirm with the user before writing** — a wrong glob means the rule silently
never loads. For a file that already exists, show a **diff** (current → merged) and get approval;
never overwrite blindly. Preserve the content you're merging into. Let them edit globs/lines inline.

Write each `.claude/rules/<domain>.md` using the template below. Keep each file under
~100 lines; split by sub-domain if it grows past that.

If any rule is **creation-critical** (it must hold when a *new* file is written, not just
edited), flag the read-only Write gotcha from the reference and offer the workarounds
(drop `paths:`, or move the at-creation bit to CLAUDE.md, or a PreToolUse hook).

## Step 6: Handle the non-rule units

Per the scope chosen in Step 4:
- **Option 1:** list them under "Not converted — belongs elsewhere".
- **Option 2:** for each, give destination + why + the exact line(s) to add, so the user can
  paste it in.
- **Option 3:** apply CLAUDE.md edits, write hook entries into `.claude/settings.json`, and
  scaffold skill folders — showing each diff before applying.

## Step 7: Report and verify

Tell the user:
1. Which rule files were written and the glob each is scoped to.
2. Any units routed elsewhere (with destinations), and anything you couldn't confidently place.
3. The creation-time caveat for any creation-critical rule.
4. To run `/memory` in a fresh session to confirm the rules load, and to open a file matching
   each glob to verify the right rule actually triggers.

---

## Rule file template

ALWAYS use this shape for files written to `.claude/rules/`:

```markdown
---
paths:
  - "<quoted glob>"
---
# <Domain> Rules

- <Imperative, verifiable rule>. <Why, if non-obvious.>
- Avoid <deprecated pattern> — <reason / what to do instead>.
- See `path/to/example.ts:NN` for the canonical pattern.
```

**Example**

Input prose:
> "All our API route handlers need input validation and should return errors in the standard
> envelope. We keep getting raw throws that leak stack traces to clients."

Output — `.claude/rules/api.md`:
```markdown
---
paths:
  - "src/api/**/*.ts"
---
# API Handler Rules

- Validate every handler's input with the shared schemas in `src/api/schemas/` before use.
- Return errors via the standard envelope in `src/api/errors.ts` — never raw `throw`.
  Raw throws leak stack traces to clients.
```

---

## Evaluation Phase

Use this section when testing or improving the rule-context-builder skill itself — not during normal use. Run it when you want to verify the skill is routing correctly, generating quality globs, and merging cleanly.

### Test case format

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

### Step 1: Spawn with-skill and baseline runs in the same turn

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

### Step 2: Draft assertions while runs are in progress

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

### Step 3: Capture timing data as runs complete

When each subagent completes, save timing immediately to `timing.json` in its run directory:
```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

### Step 4: Grade, aggregate, and launch the viewer

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

### Step 5: Iterate

Read `feedback.json` when user finishes. Empty feedback = looks good. Improve the skill based on complaints, rerun into `iteration-<N+1>/`, repeat until feedback is empty or you're not making progress.

**Common failure modes to watch for:**
- Routing too broad (dumping everything into rules instead of classifying)
- Globs matching non-existent paths (not grounded in real tree)
- Silently overwriting existing files instead of merging
- Missing the routing table confirm step before writing

---

## Quality rules

- **Route, don't dump.** A rule that should've been a hook (a deterministic guarantee) or a
  skill (a procedure) is a defect, even if it's syntactically valid. The reference's decision
  tree is the spec.
- **Narrowest accurate glob.** Over-broad globs load rules where they don't apply, burning
  attention; over-narrow ones miss files. Match the real tree.
- **Lean files win.** Path-scoped rules inject into every matching interaction — every padding
  line is a recurring tax. Cut anything Claude already knows or can read from the code.
- **Merge, never clobber.** When a `.claude/rules/` file already exists, append into it and show
  the diff (Step 5) — silently overwriting and losing a teammate's committed rule is a worse
  failure than a misrouted line. Dedup against what's there; flag contradictions instead of
  stacking opposite rules.
- **Quote your globs.** Patterns starting with `*` or `{` must be quoted or they silently fail.
