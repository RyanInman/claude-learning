# Skill Anatomy, Frontmatter, and Loading

How a skill is laid out, what goes in the frontmatter, how to name and split files, and how the three-stage loading model affects token cost. Read this when scaffolding a new skill or deciding what belongs in `SKILL.md` versus a bundled file.

## Contents

- [Folder layout](#folder-layout)
- [Frontmatter fields](#frontmatter-fields)
- [Naming conventions](#naming-conventions)
- [When to split vs. keep inline](#when-to-split-vs-keep-inline)
- [Progressive disclosure and token budgets](#progressive-disclosure-and-token-budgets)

## Folder layout

A skill is a folder, not just a file. The canonical layout works across Claude.ai, the API, and Claude Code:

```
my-skill/
├── SKILL.md            # Required: YAML frontmatter + instructions
├── references/         # Docs Claude READS into context as needed
├── scripts/            # Executable code Claude RUNS (not loaded into context)
├── assets/             # Files used in OUTPUT (templates, boilerplate, fonts, icons)
└── evals/              # Recommended: evaluation tests
```

The three bundled-resource directories serve distinct purposes:

- **`scripts/`** — executable code for deterministic, repetitive operations. May be executed _without_ loading source into context (only stdout/stderr costs tokens), but can still be read by Claude when it needs to patch the script.
- **`references/`** — documentation loaded into context to inform reasoning (API references, schemas, comprehensive guides). This is where you offload anything that would otherwise bloat `SKILL.md`.
- **`assets/`** — files used _within the output_ Claude produces (document templates, boilerplate code, images). Not loaded into context.

## Frontmatter fields

**Required:**

- `name` — max 64 chars; lowercase letters, numbers, hyphens only; no XML tags; cannot contain the reserved words "anthropic" or "claude". In Claude Code, the _directory name_ (not this field) becomes the `/command`.
- `description` — max 1024 chars; non-empty; third person; states _what the skill does_ AND _when to use it_. This is the single highest-leverage line you write — see [Progressive disclosure and token budgets](#progressive-disclosure-and-token-budgets) for why, and the "Description Optimization" section of `SKILL.md` for how to tune it.

**Claude Code optional fields** (use only when needed — most skills need none of these):

- `when_to_use` — supplementary triggering hint.
- `argument-hint`, `arguments` — declare expected arguments for `/command` invocation.
- `disable-model-invocation: true` — only the user can invoke (`/deploy`); removes the description from Claude's context. Use for side-effecting actions you don't want Claude triggering autonomously.
- `user-invocable: false` — only Claude can invoke; hides the skill from the `/` menu. Use for passive background knowledge (e.g., `legacy-system-context`).
- `allowed-tools` / `disallowed-tools` — pre-approve or block tools while the skill is active (e.g., `Bash(git add *) Bash(git commit *)`), avoiding per-use prompts. For project skills this takes effect after the workspace trust dialog is accepted — review project skills before trusting a repo, since a skill can grant itself broad tool access.
- `model`, `effort` — pin the model/effort for the skill.
- `context: fork`, `agent` — run the skill's work in an isolated subagent (see `references/bundling-scripts.md`).
- `hooks`, `paths`, `shell` — advanced integration points.

See `references/claude-code-specifics.md` for how these fields interact with precedence, discovery, and the `/` menu.

## Naming conventions

Prefer **gerund form** (verb + -ing): `processing-pdfs`, `analyzing-spreadsheets`, `testing-code`, `writing-documentation`. Acceptable alternatives: noun phrases (`pdf-processing`) or action-oriented (`process-pdfs`).

Avoid vague names (`helper`, `utils`, `tools`) and overly generic ones (`documents`, `data`), and keep the pattern consistent within a collection. Name bundled files descriptively (`form_validation_rules.md`, not `doc2.md`) and organize by domain (`references/finance.md`, `references/sales.md`) — Claude navigates the folder like a filesystem, so good names are how it finds the right file.

## When to split vs. keep inline

Keep in `SKILL.md`: the overview, quick-start, core workflow, and pointers to other files — think of it as the table of contents for an onboarding guide.

Split content out when:

- The body approaches ~500 lines (one community guide suggests splitting past ~300).
- Contexts are mutually exclusive or rarely used together — splitting means a given query loads only what it needs.
- Content is domain-specific — organize by domain so a finance query only ever loads `finance.md`.

Rules for split files:

- **Keep references one level deep.** Don't nest (`SKILL.md` → `advanced.md` → `details.md`). Claude may only partially read deeply-nested files (previewing with `head`), producing incomplete information. Link every reference directly from `SKILL.md`.
- **Add a table of contents** to any reference file longer than ~100 lines, so Claude sees the full scope even when it previews with a partial read.
- **Forward slashes only** in paths (`scripts/helper.py`), even on Windows.
- **`@` imports work only in CLAUDE.md, not SKILL.md.** In a skill, write an instruction telling Claude to use the Read tool: "Read `references/api.md` for the full requirements."

## Progressive disclosure and token budgets

Skills load context in three stages, and this is the core architecture that makes bundled content effectively unbounded:

1. **Metadata** (`name` + `description`) — preloaded at startup for _every_ skill, roughly ~100 tokens each. With 10 skills you pay ~1,000 tokens at startup, not the 50,000+ you'd pay if bodies loaded eagerly.
2. **`SKILL.md` body** — read via the filesystem only when a task matches. Keep it lean anyway: once loaded, every token competes with conversation history, and in Claude Code an invoked skill stays in context for the rest of the session.
3. **Bundled resources** — references are read, and scripts executed, only when needed. A reference costs zero tokens until read; a 50-line script that prints "Validation passed: 3 pages, 2 tables" costs ~15 tokens (just its output), never its source.

Because the description is the _only_ body-level signal available at startup, it alone decides whether a skill fires. A vague description wastes the metadata budget (the skill never triggers); a trigger-rich one fires reliably. Front-load the key use case.

**Claude Code listing budget.** All skill _names_ are always included, but descriptions are shortened to fit a character budget that scales at ~1% of the model's context window, with each entry capped (1,536 chars in recent versions). When the budget overflows, the least-used skills' descriptions are dropped first and those skills silently stop triggering. Run `/doctor` to detect overflow; raise it with `skillListingBudgetFraction` or free budget by setting low-priority skills to name-only in `skillOverrides`.

**Lifecycle under compaction.** Once invoked, the rendered `SKILL.md` enters the conversation as one message and stays for the session (it is not re-read each turn) — so write standing instructions, not one-time steps. Under auto-compaction, Claude Code re-attaches the most recent invocation of each skill after the summary, keeping the first ~5,000 tokens of each (shared ~25,000-token budget). Re-invoke a large skill after compaction if its later sections were dropped.

**Caveat:** progressive disclosure isn't always perfectly realized — some plugin/skill configurations have loaded full bodies at startup. Token figures above are approximate and vary by model and Claude Code version. Audit real startup context with `/context` and prune unused skills.
