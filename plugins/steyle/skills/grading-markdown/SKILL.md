---
name: grading-markdown
description: Grades the prose of one markdown file, or of a whole skill folder in one pass, against the steyle writing guides — the universal guide (the plugin's output-styles/universal-writing-style.md) always, plus the plugin's references/skill-writing-style.md when the target is a SKILL.md, a file inside a skill folder, or a skill folder itself, or references/memory-writing-style.md when the file is a CLAUDE.md, MEMORY.md, memory file, or .claude/rules file. Returns an A-F adherence grade and the complete line-by-line fix list that lifts the target to an A. Use whenever the user says "style check", "style pass", "grade the writing", "review the prose", "does this follow the style guide", "check this against our writing style", "does my skill follow the house style", "clean up the prose in my skill", or points at any .md file or skill folder and asks how well it is written, even if they never say the word "style". Also use after a skill draft is finished and its prose needs the dedicated editing pass. Do NOT use for a structural or triggering audit — description quality, progressive disclosure, folder layout, token cost all belong to skillit:review. Do NOT use to author a brand-new skill (use skillit:create), and do NOT edit the target file — this skill reports fixes; the user decides which to apply.
---

# Grading markdown style

Grade one markdown file, or one skill folder, against the steyle writing guides. Report an A-F grade and every fix needed to reach an A. Do not edit the target.

## Workflow

### Step 0: Before starting

Confirm these two facts before you read any guide, because a wrong target wastes the whole pass:

1. What is the target, and is it one file or a folder? Grade one target per run. When the user names several separate files, run the workflow once per file. Report each file separately.
   - Take folder scope when the user names a skill or a directory, as in "style check my scriptify skill". The target is the folder that holds `SKILL.md`, and the grade covers that `SKILL.md` plus every file under `references/`.
   - Take file scope when the user names one `.md` path, a lone `SKILL.md` included.
2. Where do the guides live? Default: the steyle plugin root, `${CLAUDE_SKILL_DIR}/../..`. The universal guide is `output-styles/universal-writing-style.md` under that root. The skill and memory guides are `references/skill-writing-style.md` and `references/memory-writing-style.md` under that root. When those paths do not resolve, look in an `output-styles/`, `style-guides/`, or `rules/` directory at the repository root. Filenames differ between copies, so match each guide on its title, not on its filename. When no directory holds the guides, ask the user for the location.

Extract both answers from the conversation first. Ask only for what is missing. When both are known, proceed without a pause.

### Step 1: Pick the guides

The rest of this document writes `<plugin>/` for the root directory that Step 0 resolved.

Read `<plugin>/output-styles/universal-writing-style.md` on every run. That file holds the universal guide, and it carries Claude Code output-style frontmatter above the guide text. Then classify the target. Read at most one extra guide:

| Target | Extra guide |
|---|---|
| A skill folder, a `SKILL.md`, or any file inside a skill folder (a folder that contains a `SKILL.md`) | `<plugin>/references/skill-writing-style.md` |
| `CLAUDE.md`, `CLAUDE.local.md`, `AGENTS.md`, `MEMORY.md`, a file under `.claude/rules/`, or a memory file with `name`/`description`/`type` frontmatter | `<plugin>/references/memory-writing-style.md` |
| Anything else | none |

When the classification is ambiguous, pick the closer match. State the reason in the report, because the reader must be able to challenge the choice.

### Step 2: Run the scan

Run `python ${CLAUDE_SKILL_DIR}/scripts/scan.py <target>`. Pass the file for file scope, or the folder for folder scope. The script flags literal C1, D2, and D3 hits across every file in the target. It matches the "and then" phrase, the closed vague-word list, and ALL-CAPS MUST/NEVER/ALWAYS. It skips code fences and frontmatter, and in a skill target it skips Example sections too.

Confirm each hit sits inside real instructional prose before you count it, because the script finds candidates, not final violations. Treat a zero-hit scan as a start, not an A. Rules A1, B1, and B4 — synonym drift, passive voice, stacked clauses — need the read in Step 3, which no pattern match supplies.

### Step 3: Collect violations

Read each file in the target with line numbers. In folder scope that means `SKILL.md` first, then every file under `references/`. Walk the universal checklist, then the extra guide's checklist when one applies. For each violation, record five things:

- The file.
- The line number.
- The rule ID.
- The offending text, quoted verbatim.
- A concrete rewrite.

Exempt zones never produce violations, because the guides exempt them:

- Code blocks, identifiers, file paths, commands, and flags.
- Text quoted from a file, a log, a tool result, or a user.
- In a `SKILL.md`: the frontmatter description and verbatim input→output examples (skill guide, Zones 1 and 2).
- In a memory file: up to two emphasized rules ("IMPORTANT", "YOU MUST"), because the memory guide permits them.

Verify every quote against the file before you report it, because a fabricated quote sends the author hunting for a line that does not exist.

### Step 4: Grade

Apply this table to every target type. It comes from the skill guide's Adherence grading section and extends unchanged to folders, universal-only files, and memory files, because grades must compare across targets:

| Grade | Adherence level |
|---|---|
| A | Full adherence — the checklist passes; at most an isolated borderline sentence |
| B | Minor drift — a few violations of one or two rules; meaning never at risk |
| C | Patterned drift — one rule broken repeatedly, or several rules broken occasionally |
| D | Widespread violations — several rules broken throughout; the prose needs a full editing pass |
| F | Guide not applied — pervasive passive voice, vague terms, or synonym drift |

Give one grade per run. A folder takes a single grade for the whole folder, because the author ships the skill as one deliverable. Grade how closely the prose follows the rules. Never grade the payoff of any single fix.

### Step 5: Report

Use this exact template, because readers rely on the same sections every time:

```markdown
## Style review: <target path>

Guides applied: universal + <skill guide | memory guide | none>. Reason: <one sentence>.

### Grade: <A-F>

<One sentence tying the grade to the adherence table.>

### Rules that cost the grade most

- **<rule ID> — <rule name>**: <count> violations. Example (<file>:<line>): "<quoted text>"
<two or three entries>

### Fixes to reach A

**<file path>**
1. Line <n> (<rule ID>): "<original text>" → "<rewrite>"
2. File-wide (<rule ID or checklist item>): <finding> → <fix>
<one entry per violation — list every violation found, because a partial list leaves the target below A after the edits>
```

Drop the bold file headings in file scope. Number the fixes as one flat list. In folder scope, keep one bold heading per file. Number the fixes continuously across the headings, because the last number is the size of the job.

Use the "Line <n>" form for violations tied to one line. Use the "File-wide" form for violations without a line, such as a missing frontmatter field, a missing section, or a file over its line budget.

For a target already at A, keep the first three sections. Replace the fix list with one line: "No fixes required."

Report only violations and fixes. Do not add a strengths section or praise, because the reader acts on deficits and skips everything else.

## Example

Input (line 12 of a target file):

> You'll want to make sure the config gets updated appropriately before things are deployed.

Output (fix-list entry):

1. Line 12 (B1, D1, D2): "You'll want to make sure the config gets updated appropriately before things are deployed." → "Update `config.yaml` before you deploy."

The same entry in folder scope, under its file heading:

**references/deploy.md**

7. Line 12 (B1, D1, D2): "You'll want to make sure the config gets updated appropriately before things are deployed." → "Update `config.yaml` before you deploy."

## Gotchas

- The frontmatter description of a `SKILL.md` breaks universal rules on purpose — colloquial trigger phrases are its job. Never count it against the grade. This is the most common false positive.
- Grade the references, not just the body. Authors polish `SKILL.md` and forget `references/`, and the skill guide governs both.
- The memory guide relaxes the ALL-CAPS ban for at most two rules per file. Flag the third emphasized rule, not the first two.
- Line numbers shift when the user edits mid-review. Quote the text with each fix so the author can find it after the numbers rot.
- A guide file itself — in `<plugin>/output-styles/` or `<plugin>/references/` — classifies as "anything else". The guides are not skills or memory files, and the plugin's `references/` folder holds no `SKILL.md`, so it is not a skill folder. The `name` and `description` frontmatter of `universal-writing-style.md` does not make it a memory file, because the `type` field is absent.
