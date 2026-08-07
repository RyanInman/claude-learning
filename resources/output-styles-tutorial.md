# Output Styles in Claude Code

An output style modifies Claude Code's system prompt to change **how Claude
responds** — role, tone, and output format. Claude keeps all of its capabilities:
reading and writing files, running scripts, tracking TODOs.

Reference: https://code.claude.com/docs/en/output-styles

---

## Why use one

**Stop re-prompting for the same thing.** If you're regularly typing "be more
concise" or "give me the diagram first," you're spending tokens and attention
re-establishing a preference on every turn. A style makes it ambient.

**Repurpose Claude beyond software engineering.** Technical writing, data
analysis, incident response, drafting. Custom styles drop the built-in coding
guidance by default, so the prompt stops being tuned for shipping code while the
file and script access stays.

**Get consistency you can version-control.** A style lives in the repo at
`.claude/output-styles/`. Everyone on the team gets the same voice, the same
document structure, the same review format. Onboarding a new contributor to your
house style becomes a `git pull`.

**Adherence that survives long sessions.** Styles trigger periodic reminders for
Claude to stay on-style, which holds up better over a long conversation than an
instruction buried in a file or in your opening message.

**Cheap.** The instructions add input tokens once per session, then prompt caching
absorbs nearly all of the cost on subsequent turns.

## Zero-setup value

Three built-in styles beyond Default. Run `/config`, select **Output style**:

- **Proactive** — executes immediately and makes reasonable assumptions instead of
  pausing on routine decisions, without changing your permission mode.
- **Explanatory** — adds "Insights" about implementation choices and codebase
  patterns as it works.
- **Learning** — leaves `TODO(human)` markers for you to implement yourself.

## When something else fits better

Styles govern *how Claude sounds*. Two neighbours are easy to confuse:

- **CLAUDE.md** for what Claude should *know* — your conventions, your codebase.
- **Skills** for what Claude should *do* — a reusable workflow.

A style also can't carry reference data. Rules about form work well; lookup tables
and vocabulary lists belong in a file with a checker.

## Minimal setup

Save a Markdown file to `~/.claude/output-styles/` (all projects) or
`.claude/output-styles/` (this repo):

```markdown
---
name: Diagrams first
description: Lead every explanation with a diagram
keep-coding-instructions: true
---

When explaining code, architecture, or data flow, start with a Mermaid diagram
showing the structure, then explain in prose.
```

Set `keep-coding-instructions: true` when Claude still writes code and you're only
changing how it communicates. Omit it when Claude isn't doing engineering at all.

Select the style under `/config`, then `/clear` or restart — styles load at
session start.
