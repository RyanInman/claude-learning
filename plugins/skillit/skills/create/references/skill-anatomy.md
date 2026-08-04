# Skill Anatomy, Frontmatter, and Splitting

How a skill is laid out, what goes in the frontmatter, and when to split content out of `SKILL.md`. Read this when scaffolding a new skill or deciding what belongs in `SKILL.md` versus a bundled file. The rules this procedure must satisfy (naming, reference depth, token budgets) are canon in the plugin-level `references/` folder: `../../../references/best-practices.md` §2–3 and `../../../references/token-economics.md` §1–2, §8–9.

## Contents

- [Folder layout](#folder-layout)
- [Frontmatter fields](#frontmatter-fields)
- [When to split vs. keep inline](#when-to-split-vs-keep-inline)

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

Name bundled files descriptively (`form_validation_rules.md`, not `doc2.md`) — Claude navigates the folder like a filesystem, so good names are how it finds the right file. Skill-name rules (gerund form, vague-name traps, length limits) are in `../../../references/best-practices.md` §3.

## Frontmatter fields

**Required:**

- `name` — max 64 chars; lowercase letters, numbers, hyphens only; no XML tags; cannot contain the reserved words "anthropic" or "claude". In Claude Code, the _directory name_ (not this field) becomes the `/command`.
- `description` — max 1024 chars; non-empty; third person; states _what the skill does_ AND _when to use it_. This is the single highest-leverage line you write — the full criteria are in `../../../references/best-practices.md` §1, and the "Description Optimization" section of `SKILL.md` covers how to tune it.

**Claude Code optional fields** (use only when needed — most skills need none of these):

- `when_to_use` — supplementary triggering hint.
- `argument-hint`, `arguments` — declare expected arguments for `/command` invocation.
- `disable-model-invocation: true` — only the user can invoke (`/deploy`); removes the description from Claude's context. Use for side-effecting actions you don't want Claude triggering autonomously.
- `user-invocable: false` — only Claude can invoke; hides the skill from the `/` menu. Use for passive background knowledge (e.g., `legacy-system-context`).
- `allowed-tools` / `disallowed-tools` — pre-approve or block tools while the skill is active (e.g., `Bash(git add *) Bash(git commit *)`), avoiding per-use prompts. For project skills this takes effect after the workspace trust dialog is accepted — review project skills before trusting a repo, since a skill can grant itself broad tool access.
- `model`, `effort` — pin the model/effort for the skill.
- `context: fork`, `agent` — run the skill's work in an isolated subagent (see `references/bundling-scripts.md`).
- `hooks`, `paths`, `shell` — advanced integration points.

See `references/claude-code-specifics.md` for how these fields interact with precedence, discovery, and the `/` menu, and `../../../references/best-practices.md` §9 for when a missing invocation-control field is a defect.

## When to split vs. keep inline

Keep in `SKILL.md`: the overview, quick-start, core workflow, and pointers to other files — think of it as the table of contents for an onboarding guide.

Split content out when:

- The body approaches ~500 lines (one community guide suggests splitting past ~300).
- Contexts are mutually exclusive or rarely used together — splitting means a given query loads only what it needs.
- Content is domain-specific — organize by domain so a finance query only ever loads `finance.md`.

The structural rules split files must follow (one level deep, TOC over ~100 lines, forward slashes, why `@` imports fail in SKILL.md) are in `../../../references/best-practices.md` §2. The token model that motivates splitting — plus the Claude Code listing budget and compaction caps — is in `../../../references/token-economics.md` §1–2, §8–9.
