---
name: grading-markdown
description: Grades the prose of one markdown file, or of a whole skill folder in one pass, against the steyle writing guides — the universal guide (the plugin's output-styles/universal-writing-style.md) always, plus the plugin's references/skill-writing-style.md when the target is a SKILL.md, a file inside a skill folder, or a skill folder itself, or references/memory-writing-style.md when the file is a CLAUDE.md, MEMORY.md, memory file, or .claude/rules file. Returns an A-F adherence grade and the complete line-by-line fix list that lifts the target to an A. Use whenever the user says "style check", "style pass", "grade the writing", "review the prose", "does this follow the style guide", "check this against our writing style", "does my skill follow the house style", "clean up the prose in my skill", or points at any .md file or skill folder and asks how well it is written, even if they never say the word "style". Also use after a skill draft is finished and its prose needs the dedicated editing pass. Do NOT use for a structural or triggering audit — description quality, progressive disclosure, folder layout, token cost all belong to skillit:review. Do NOT use to author a brand-new skill (use skillit:create), and do NOT edit the target file — this skill reports fixes; the user decides which to apply.
---

# Grading markdown style

Grade one markdown file, or one skill folder, against the steyle writing guides. Report an A-F grade and every fix needed to reach an A. Do not edit the target.

Scripts live in `scripts/`. Run them. Do not reimplement them.

## Workflow

### Step 0: Resolve the target

Confirm the target before you read any guide, because a wrong target wastes the whole pass. The user names one file or one folder. Grade one target per run. When the user names several separate files, run the workflow once per file. Report each file separately.

- Take folder scope when the user names a skill or a directory, as in "style check my scriptify skill". Pass the folder that holds `SKILL.md`.
- Take file scope when the user names one `.md` path, a lone `SKILL.md` included.

Extract the path from the conversation. Ask only when no path is stated. Then run exactly:

`python3 ${CLAUDE_SKILL_DIR}/scripts/resolve_target.py <target> --json`

It prints JSON: `scope`, `files` (what the grade covers), `target_class` (`skill`, `memory`, or `other`), `class_reason`, `ambiguous`, and `guides` (resolved paths). It matches guides on their titles, so filenames can differ between copies.

- Exit 2 → the path is wrong or the folder holds no `SKILL.md`. Ask the user for the target.
- Exit 1 → a guide is missing (`missing` lists which). Ask the user where the guides live. Re-run with `--plugin-root <dir>`.
- `ambiguous: true` → the class is a judgment call, such as a `rules/` path outside `.claude/`. Pick the closer match. State the reason in the report, because the reader must be able to challenge the choice.

### Step 1: Read the guides

Read `guides.universal` on every run. It carries Claude Code output-style frontmatter above the guide text. Read `guides.extra` when it is not null: the skill guide for a `skill` target, the memory guide for a `memory` target. Read no other guide.

### Step 2: Run the scan

Run exactly: `python3 ${CLAUDE_SKILL_DIR}/scripts/scan.py <target>`. The script flags literal C1, D2, and D3 hits across every file in the target. It matches the "and then" phrase, the closed vague-word list, and ALL-CAPS MUST/NEVER/ALWAYS. It skips code fences and frontmatter, and in a skill target it skips Example sections too.

Confirm each hit sits inside real instructional prose before you count it, because the script finds candidates, not final violations. Treat a zero-hit scan as a start, not an A. Rules A1, B1, and B4 — synonym drift, passive voice, stacked clauses — need the read in Step 3, which no pattern match supplies.

### Step 3: Collect and verify violations

Read each file in `files` with line numbers, in the listed order. Walk the universal checklist, then the extra guide's checklist when one applies. Write every violation to a `findings.json` in your scratch directory, in this shape:

```json
{"target": "<target path>", "scope": "<scope>", "target_class": "<target_class>",
 "findings": [
  {"file": "SKILL.md", "line": 21, "rule": "B1", "quote": "<offending text, verbatim>", "fix": "<concrete rewrite>"},
  {"file": "SKILL.md", "line": null, "rule": "<rule ID or checklist item>", "quote": "<finding>", "fix": "<fix>"}
 ]}
```

Use `"line": null` for a violation without a line, such as a missing frontmatter field, a missing section, or a file over its line budget. List several rule IDs in one `rule` string, as in `"B1, D1, D2"`.

Exempt zones never produce violations, because the guides exempt them:

- Code blocks, identifiers, file paths, commands, and flags.
- Text quoted from a file, a log, a tool result, or a user.
- In a `SKILL.md`: the frontmatter description and verbatim input→output examples (skill guide, Zones 1 and 2).
- In a memory file: up to two emphasized rules ("IMPORTANT", "YOU MUST"), because the memory guide permits them.

Then run exactly: `python3 ${CLAUDE_SKILL_DIR}/scripts/verify_findings.py findings.json`

It checks every quote verbatim at its line and flags lines inside frontmatter, code blocks, blockquotes, and skill Example sections. Exit 1 → fix or drop each listed finding, because a fabricated quote sends the author hunting for a line that does not exist. Re-run until exit 0. It does not count the memory guide's two-rule allowance. Count that by hand.

### Step 4: Grade

Run exactly: `python3 ${CLAUDE_SKILL_DIR}/scripts/render_review.py findings.json --counts`

It prints the total, per-rule and per-file counts, and the three costliest rules. Apply this table to every target type. It comes from the skill guide's Adherence grading section and extends unchanged to folders, universal-only files, and memory files, because grades must compare across targets:

| Grade | Adherence level |
|---|---|
| A | Full adherence — the checklist passes; at most an isolated borderline sentence |
| B | Minor drift — a few violations of one or two rules; meaning never at risk |
| C | Patterned drift — one rule broken repeatedly, or several rules broken occasionally |
| D | Widespread violations — several rules broken throughout; the prose needs a full editing pass |
| F | Guide not applied — pervasive passive voice, vague terms, or synonym drift |

Give one grade per run. A folder takes a single grade for the whole folder, because the author ships the skill as one deliverable. Grade how closely the prose follows the rules. Never grade the payoff of any single fix.

### Step 5: Report

Run exactly:

`python3 ${CLAUDE_SKILL_DIR}/scripts/render_review.py findings.json --grade <A-F> --grade-note "<one sentence tying the grade to the adherence table>" --guides-reason "<one sentence>"`

It renders the fixed template: the guides line, the grade, the costliest rules, and the numbered fix list. File scope gives one flat list. Folder scope gives one bold heading per file with continuous numbering, because the last number is the size of the job. Zero findings renders "No fixes required." Paste the output to the user verbatim.

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
