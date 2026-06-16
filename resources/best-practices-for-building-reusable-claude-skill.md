# Best Practices for Building Reusable Claude Skills (Agent Skills / SKILL.md)
 
## TL;DR
- A great skill is a **folder, not just a file**: a concise `SKILL.md` (official guidance: keep the body under 500 lines, and the spec recommends instructions under ~5,000 tokens) plus `scripts/`, `references/`, and `assets/` loaded only when needed. The single highest-leverage decision is the frontmatter `description` — it alone determines whether the skill fires, because at startup Claude loads only name + description (~100 tokens each per the Agent Skills Specification), not the body.
- For consistent, fast output, push deterministic work into **pre-written, self-documenting scripts** (they run without entering context, so only their output costs tokens), use **templates and input/output examples**, and add **validation loops** (run → validate → fix → repeat). Avoid railroading Claude with rigid ALL-CAPS rules — state the rule and the "why."
- For Claude Code specifically: skills live in `~/.claude/skills/` (personal) or `.claude/skills/` (project, commit to git); they unify with slash commands (`/skill-name`); control invocation with `disable-model-invocation`, `user-invocable`, `allowed-tools`, and `context: fork`; and build evals first, testing trigger accuracy with real prompts.
## Key Findings
 
**Progressive disclosure is the core architecture.** Skills load context in three stages: (1) at startup, only the YAML `name` + `description` from every skill is preloaded into the system prompt; (2) when a task matches, Claude reads the full `SKILL.md` body via the filesystem; (3) referenced files and scripts are read/executed only when needed. Reference files and bundled data cost **zero context tokens until actually read**, and scripts can be executed without loading their source — only stdout/stderr consumes tokens. This is what makes a skill's bundled content effectively unbounded. The Agent Skills Specification states the metadata layer is "~100 tokens — the name and description fields are loaded at startup for all skills," while instructions are recommended to stay "< 5000 tokens."
 
**The description is the most important line you write.** Claude tends to *under*-trigger; it won't use a skill unless the match is obvious. Write descriptions in third person, state both *what the skill does* and *when to use it*, and include concrete trigger phrases. The Anthropic skill-creator `SKILL.md` is explicit: "currently Claude has a tendency to 'undertrigger' skills — to not use them when they'd be useful. To combat this, please make the skill descriptions a little bit 'pushy.'" Its worked example expands "How to build a simple fast dashboard to display internal Anthropic data" into "…Make sure to use this skill whenever the user mentions dashboards, data visualization, internal metrics, or wants to display any kind of company data, even if they don't explicitly ask for a 'dashboard.'"
 
**Keep `SKILL.md` lean.** Anthropic's Skill authoring best practices: "Keep SKILL.md body under 500 lines for optimal performance. If your content exceeds this, split it into separate files using the progressive disclosure patterns." Conciseness still matters even though the body isn't preloaded — once loaded, every token competes with conversation history, and in Claude Code an invoked skill stays in context for the rest of the session.
 
**Code provides determinism and speed.** LLMs are expensive and non-deterministic at mechanical work; pre-written scripts are more reliable, save tokens, save time, and ensure consistency. A common community framing of an ideal skill is roughly 10% LLM steering and 90% deterministic code execution.
 
## Details
 
### 1. Efficient Structure — folder layout, naming, and when to split
 
**Canonical folder layout** (works across Claude.ai, API, and Claude Code):
 
```
my-skill/
├── SKILL.md            # Required: YAML frontmatter + instructions
├── references/         # Docs Claude READS into context as needed
│   ├── api.md
│   └── schema.md
├── scripts/            # Executable code Claude RUNS (not loaded into context)
│   ├── validate.py
│   └── scaffold.sh
├── assets/             # Files used in OUTPUT (templates, boilerplate, fonts, icons)
│   └── component.template.tsx
└── evals/              # Recommended: evaluation tests
    └── evals.json
```
 
The three bundled-resource directories serve distinct purposes (per Anthropic's skill-creator):
- **`scripts/`** — executable code for deterministic/repetitive operations. May be executed *without* loading into context, but can still be read by Claude for patching.
- **`references/`** — documentation loaded into context to inform Claude's reasoning (API references, schemas, comprehensive guides). For Claude Code these are also where you offload anything that would otherwise bloat `SKILL.md`.
- **`assets/`** — files used *within the output* Claude produces (document templates, boilerplate code, images), not loaded into context.
**Frontmatter (required + optional fields):**
- `name`: max 64 chars; lowercase letters, numbers, hyphens only; no XML tags; cannot contain reserved words "anthropic" or "claude". In Claude Code, the directory name (not the `name` field) becomes the `/command`.
- `description`: max 1024 chars (the spec limit); non-empty; third person; what + when.
- Claude Code adds optional fields: `when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `disallowed-tools`, `model`, `effort`, `context: fork`, `agent`, `hooks`, `paths`, `shell`.
**Naming conventions:** Anthropic recommends **gerund form** (verb + -ing): `processing-pdfs`, `analyzing-spreadsheets`, `testing-code`, `writing-documentation`. Acceptable alternatives: noun phrases (`pdf-processing`) or action-oriented (`process-pdfs`). **Avoid** vague names (`helper`, `utils`, `tools`), overly generic names (`documents`, `data`), and inconsistent patterns within a collection. Name files descriptively (`form_validation_rules.md`, not `doc2.md`) and organize by domain (`reference/finance.md`, `reference/sales.md`) — Claude navigates the directory like a filesystem.
 
**When to split vs. keep in `SKILL.md`:**
- Keep in `SKILL.md`: the overview, quick-start, core workflow, and pointers to other files. Think of it as a table of contents for an onboarding guide.
- Split out when: the body approaches 500 lines (one community guide suggests splitting past ~300 lines); when contexts are mutually exclusive or rarely used together (splitting reduces token usage); when content is domain-specific (organize by domain so Claude only reads `finance.md` for a finance query).
- **Keep references one level deep.** Don't nest references (SKILL.md → advanced.md → details.md). Claude may only partially read deeply-nested files (using `head -100` previews), producing incomplete information. All reference files should link directly from `SKILL.md`.
- For reference files longer than 100 lines, **add a table of contents** at the top so Claude sees the full scope even when previewing with partial reads.
- **Forward slashes only** in paths (`scripts/helper.py`), even on Windows.
- **`@` imports only work in CLAUDE.md, not SKILL.md.** In a skill, write an instruction telling Claude to use the Read tool: "Read `references/agent-prompt.md` for the full requirements."
**Use `init_skill.py` to scaffold.** Anthropic's skill-creator bundles an `init_skill.py` that generates a valid template directory (with example `scripts/`, `references/`, `assets/` files to customize or delete) and a `package_skill.py` that validates and zips the skill into a `.skill` file for distribution.
 
### 2. Consistent Output — determinism techniques
 
- **Write imperative, third-person instructions.** Use imperative/infinitive voice ("Read the file," "Extract the fields"), not second person ("you should"). Use one consistent term throughout — don't mix "extract/pull/get/retrieve" or "field/box/element."
- **Set appropriate degrees of freedom (the single most important calibration).** Match specificity to task fragility:
  - *High freedom* (text instructions) when many approaches are valid and decisions depend on context — e.g., code review.
  - *Medium freedom* (pseudocode/parameterized scripts) when a preferred pattern exists.
  - *Low freedom* (exact scripts, no parameters) when operations are fragile and consistency is critical — e.g., "Run exactly this script: `python scripts/migrate.py --verify --backup`. Do not modify the command." The analogy: a narrow bridge with cliffs (one safe path → exact instructions) vs. an open field (many paths → general direction).
- **Provide templates,** matching strictness to need. Use "ALWAYS use this exact template structure" for strict formats (API responses, reports); use "here is a sensible default, but use your judgment" for flexible guidance.
- **Provide input/output examples.** Anthropic's own example: a commit-message skill showing 3 concrete input→output pairs. "A single concrete example showing actual input and expected output is worth more than 50 lines of abstract description." Claude generalizes from concrete examples better than from abstract rule lists.
- **Use scripts for deterministic operations** instead of asking Claude to generate code each time. "Write `validate_form.py` rather than asking Claude to generate validation code."
- **Use validation/checklist loops.** The "run validator → fix errors → repeat" pattern greatly improves quality. Provide copyable checklists for multi-step workflows. Use the **plan-validate-execute** pattern for batch/destructive/high-stakes operations: have Claude write a plan to a structured file (e.g., `changes.json`), validate it with a script, then execute — catching errors before they're applied.
- **Make verification scripts verbose** with specific error messages: `"Field 'signature_date' not found. Available fields: customer_name, order_total, signature_date_signed"` helps Claude self-correct.
- **For code review specifically** (real-world report): instruct Claude to "Read actual code with Read/Grep tools before reporting. No guessing. Only report what you confirmed in the file" — without this, Claude generates plausible-sounding fabricated findings.
**Anti-patterns to avoid:**
- ALL-CAPS `MUST`/`ALWAYS`/`NEVER` strings with no reasoning. Anthropic's skill-creator flags these as a "yellow flag." Instead, state the rule *and the why*: "Use constructor injection. Field injection breaks testability because we cannot mock the field without Spring context" beats "MUST use constructor injection." LLMs respond better to reasoning than rote rules, and can then generalize to edge cases.
- **Railroading.** Over-specific instructions fail when the skill is reused across varied inputs — give Claude information plus flexibility to adapt.
- **Stating the obvious.** Claude already knows how to code and can read the codebase. Restating defaults adds tokens without value. Focus on what pushes Claude *out* of its default behavior, plus a **Gotchas section** (the highest-signal content) capturing real failure points — e.g., "The `subscriptions` table is append-only; take the row with the highest version, not the most recent `created_at`."
- **Offering too many options** ("use pypdf, or pdfplumber, or PyMuPDF, or..."). Provide one default with an escape hatch.
- **Time-sensitive information** ("before August 2025, use the old API"). Put deprecated content in a collapsed "Old patterns" section instead.
### 3. Fast Execution — minimizing latency
 
- **Pre-written scripts beat on-the-fly code generation.** Benefits per Anthropic: more reliable, save tokens (no code in context), save time (no generation), ensure consistency.
- **Make execution intent explicit.** State clearly whether Claude should *execute* ("Run `analyze_form.py` to extract fields") or *read* ("See `analyze_form.py` for the extraction algorithm"). For most utility scripts, execution is preferred.
- **Design script interfaces for agents** (per official `agentskills.io` guidance):
  - **Avoid interactive prompts** — a hard requirement. Agents run in non-interactive shells and cannot answer TTY/password/confirmation prompts; a blocking script hangs indefinitely. Accept all input via flags, env vars, or stdin.
  - **Meaningful exit codes** for different failure types (not found, invalid args, auth failure), documented in `--help`.
  - **Predictable output size.** Many agent harnesses truncate tool output beyond a threshold (e.g., 10–30K characters), losing critical info. Default to a summary or limit, and support `--offset`; for large output, require an `--output` flag (file or `-` for stdout).
  - **Safe defaults / dry-run / idempotency.** Destructive operations should require `--confirm`/`--force`; offer `--dry-run`; prefer "create if not exists" since agents may retry.
  - **Structured output** (JSON/CSV/TSV) to stdout, diagnostics to stderr.
  - **Helpful error messages** that say what went wrong, what was expected, and what to try — an opaque "Error: invalid input" wastes an agent turn.
  - **Document usage with `--help`** — it's the primary way an agent learns the interface; keep it concise since it enters the context window.
- **Solve, don't punt.** Scripts should handle error conditions (FileNotFoundError, PermissionError) rather than failing and leaving Claude to figure it out. Avoid "voodoo constants" — document why `TIMEOUT = 30` not `TIMEOUT = 47`.
- **Avoid unnecessary tool calls.** In Claude Code, dynamic context injection — `` !`git diff HEAD` `` in the skill body — runs a shell command *before* Claude sees the content and inlines the result, grounding the response without a separate tool round-trip.
- **Use `context: fork`** to run heavy/exploratory work in an isolated subagent (e.g., `agent: Explore`), keeping the main conversation's context clean and enabling parallel setup.
### 4. Token-Efficient Reading/Loading
 
- **Startup cost is just metadata.** The Agent Skills Specification states metadata is "~100 tokens" per skill (the name and description, loaded at startup for all skills); some community measurements report ~70–150. With 10 skills you pay roughly 1,000 tokens at startup, not the 50,000+ you'd pay if bodies loaded eagerly — a near-total reduction when skills are present but not activated.
- **Description quality directly affects both cost and triggering.** A vague description means the skill never fires (wasting its metadata budget); a trigger-rich one activates reliably. Front-load the key use case.
- **Claude Code's skill-listing budget.** All skill *names* are always included, but descriptions are shortened to fit a character budget. Per the official Claude Code docs: "The budget scales at 1% of the model's context window. When it overflows, descriptions for the skills you invoke least are dropped first… each entry's combined text is capped at 1,536 characters regardless." Per Claude Code config references, the per-entry listing cap was raised from 250 to 1,536 characters in v2.1.105, and v2.1.129 exposed `skillListingBudgetFraction` (default `0.01` = 1%) and `skillListingMaxDescChars` (default `1536`). Symptoms of overflow: skills silently stop triggering. **Run `/doctor`** to see if the budget is overflowing. Raise it with `skillListingBudgetFraction` (e.g., `0.02`) or the `SLASH_COMMAND_TOOL_CHAR_BUDGET` env var; free budget by setting low-priority skills to `"name-only"` in `skillOverrides`.
- **Scripts cost nothing until run; references cost nothing until read.** A 50-line Python script that returns "Validation passed: 3 pages, 2 tables" costs ~15 tokens (just the output). Domain-organized references mean a sales query never loads finance schemas.
- **Caveat — preloading behavior with plugins.** Community bug reports (anthropics/claude-code #14882; obra/superpowers #190) show that some plugins/skills have appeared *fully loaded* at startup rather than metadata-only, consuming 22k+ tokens (~11% of a 200k window). This indicates progressive disclosure isn't always perfectly realized in every harness/plugin configuration — audit your real startup context with `/context` and prune unused skills/plugins.
- **Skill content lifecycle in Claude Code:** once invoked, the rendered `SKILL.md` enters the conversation as a single message and stays for the session (it is not re-read each turn). Write standing instructions, not one-time steps. Per the official docs, under auto-compaction Claude Code "re-attaches the most recent invocation of each skill after the summary, keeping the first 5,000 tokens of each. Re-attached skills share a combined budget of 25,000 tokens." Older skills may be dropped — re-invoke a large skill after compaction if needed.
### Claude Code specifics
 
- **Where skills live & precedence:** Enterprise > Personal (`~/.claude/skills/`) > Project (`.claude/skills/`). Plugin skills use a `plugin-name:skill-name` namespace. If a skill and a `.claude/commands/` file share a name, the skill wins.
- **Discovery:** Project skills load from `.claude/skills/` in the start directory and every parent up to repo root; nested package skills (e.g., `packages/frontend/.claude/skills/`) load on demand for monorepos. **Live change detection** picks up edits to `SKILL.md` within the session; creating a brand-new top-level skills directory requires a restart.
- **Skills vs. slash commands vs. subagents:** Custom commands have been **merged into skills** — `.claude/commands/deploy.md` and `.claude/skills/deploy/SKILL.md` both create `/deploy`. Skills are the recommended path because they support supporting files, frontmatter invocation control, auto-invocation, and subagent execution. Key difference from plain commands: Claude can **auto-invoke** a skill based on description matching (like a subagent), and skills can bundle scripts. Subagents are for parallel/isolated heavy work.
- **Invocation control:**
  - `disable-model-invocation: true` → only the user can invoke (`/deploy`); removes the description from Claude's context. Use for side-effecting actions (`/commit`, `/deploy`) you don't want Claude triggering autonomously.
  - `user-invocable: false` → only Claude can invoke; hide from `/` menu. Use for passive background knowledge (e.g., `legacy-system-context`).
  - `allowed-tools` → pre-approves listed tools while the skill is active (e.g., `Bash(git add *) Bash(git commit *)`), no per-use prompt. For project skills, takes effect after accepting the workspace trust dialog — review project skills before trusting a repo, since a skill can grant itself broad tool access.
- **Interaction with CLAUDE.md:** CLAUDE.md is loaded at session start and stays in context even for unrelated work; skills load on demand. Anthropic's guidance: move specialized procedures (PR reviews, migrations) out of CLAUDE.md into skills, keeping CLAUDE.md under ~200 lines. A skill body is subject to the same conciseness test as CLAUDE.md.
- **Arguments & substitutions:** `$ARGUMENTS`, `$ARGUMENTS[N]`/`$N`, named `$name` args, plus `${CLAUDE_SKILL_DIR}` (reference bundled scripts regardless of cwd), `${CLAUDE_SESSION_ID}`, `${CLAUDE_PLUGIN_DATA}` (stable dir for persistent skill memory like an append-only log).
- **Bundled skills** shipped with Claude Code include `/code-review`, `/batch`, `/debug`, `/loop`, `/claude-api`, plus `/run`, `/verify`, and `/run-skill-generator` (which records a per-project launch recipe into `.claude/skills/run-<name>/`).
### Software-development skill categories (from Anthropic's Claude Code team)
 
In "Lessons from Building Claude Code: How We Use Skills" (Thariq Shihipar, member of technical staff on the Claude Code team, published June 3, 2026 on the Claude blog), the team — which runs hundreds of skills internally with engineers adding new ones every week — cataloged its internal skills into nine categories. The best skills fit cleanly into one; skills straddling several confuse the agent:
1. **Library/API reference** (e.g., `billing-lib`, `internal-platform-cli`) — reference snippets + gotchas.
2. **Product verification** (e.g., `signup-flow-driver`, `checkout-verifier`, `tmux-cli-driver`) — paired with Playwright/tmux. Shihipar singles this category out as the most valuable, saying it has had the most measurable impact on output quality and that "it can be worth having an engineer spend a full week making verification Skills excellent."
3. **Data fetching/analysis** (e.g., `funnel-query`, `grafana`, `datadog`).
4. **Business process/team automation** (e.g., `standup-post`, `create-ticket`, `weekly-recap`).
5. **Code scaffolding/templates** (e.g., `new-<framework>-workflow`, `new-migration`, `create-app`).
6. **Code quality/review** (e.g., `adversarial-review` — spawns a fresh-eyes subagent to critique and iterate until findings degrade to nitpicks; `code-style`; `testing-practices`). Can run via hooks or GitHub Actions.
7. **CI/CD and deployment** (e.g., `babysit-pr`, `deploy-<service>` with auto-rollback, `cherry-pick-prod`).
8. **Runbooks** (e.g., `<service>-debugging`, `oncall-runner`, `log-correlator`).
9. **Infrastructure operations** (e.g., `<resource>-orphans`, `dependency-management`, `cost-investigation`) — destructive actions benefit from guardrails like on-demand hooks (`/careful` blocks `rm -rf`, `DROP TABLE`, force-push).
Real-world code-review experience reports converge on: encapsulate the comment-posting logic in a **Python script, not markdown instructions**; cap nit volume ("report at most five nits"); define a clear severity taxonomy (blocking/important/nit); list skip rules (generated code, lockfiles, anything CI already enforces); and keep approval messages terse (a simple "LGTM").
 
### Bundling executable scripts — dependency management
 
Per official `agentskills.io` guidance, prefer **self-contained scripts that declare their own inline dependencies**, so the agent runs them with one command and no separate install step:
- **Python (PEP 723):** declare dependencies in a TOML block inside `# /// script ... # ///` markers; run with `uv run scripts/extract.py` (recommended; creates an isolated env, installs deps, runs) or `pipx run`. Pin with PEP 508 specifiers (`"beautifulsoup4>=4.12,<5"`), constrain with `requires-python`, and use `uv lock --script` for a reproducibility lockfile.
- **Deno:** `npm:`/`jsr:` import specifiers make scripts self-contained by default; semver pinning (`@1.0.0` exact, `@^1.0.0` compatible); deps cached globally.
- **Bun:** auto-installs missing packages at runtime when no `node_modules` exists; pin in the import path (`"cheerio@1.0.0"`).
- **One-off vs. script:** reference an existing package directly in `SKILL.md` (via `uvx`, `pipx run`, `npx`, etc., with pinned versions) when invoking a tool with a few flags; **move to a tested `scripts/` file when a command grows complex enough that it's hard to get right on the first try.**
- **Platform dependency limits:** Claude.ai/Claude Code can install packages from PyPI/npm (and GitHub) at runtime; the **Claude API container has no network access and no runtime install** — all deps must be pre-installed. State prerequisites in `SKILL.md` and don't assume packages are installed. For untrusted scripts, run in a sandbox (e.g., Docker) to keep the host clean.
### Versioning, testing, and iterating
 
- **Build evaluations first (evaluation-driven development).** Before writing extensive docs: (1) run Claude on representative tasks *without* the skill and document failures; (2) build at least three eval scenarios; (3) establish a baseline; (4) write minimal instructions to pass; (5) iterate. Evals are your source of truth. (Note: there's no built-in eval runner in the base product; you build your own, though the skill-creator and community tools like "Skills 2.0" / `pulser` provide eval, benchmark, and blind A/B comparison modes.)
- **The Claude A / Claude B loop:** work with one Claude instance ("A") to author/refine the skill; test with a fresh instance ("B") on real tasks; bring observed gaps back to A. Claude understands the skill format natively — just ask it to create a skill.
- **Test trigger accuracy explicitly.** The most common failure is the skill not firing due to a weak description. Debugging technique: ask Claude directly "When would you use the [skill-name] skill?" — it quotes the description verbatim, revealing missing keywords. Track trigger rate (aim >80–90% on relevant queries) and false-positive rate (>10% means the description is too broad).
- **Fix over-triggering with negative triggers.** Add explicit exclusions: "Do NOT use for simple data exploration (use the data-viz skill instead)." Negative triggers measurably reduce false positives in skills with domain overlap; give each skill distinct trigger keywords or merge overlapping ones.
- **Test across models** (Haiku/Sonnet/Opus) if you'll use multiple — what works for Opus may need more detail for Haiku.
- **Observe how Claude navigates the skill:** unexpected file-read order (structure isn't intuitive), missed references (links not prominent), overused files (move that content into `SKILL.md`), ignored files (unnecessary or poorly signaled).
- **Versioning & distribution:** commit project skills to git for small teams; for scale, build a **plugin** + Claude Code **marketplace** (`marketplace.json` listing plugins). Pin to a Git tag (e.g., `v1.0.0`) rather than `main` so library updates don't silently change older projects. A `compatibility` frontmatter field can declare runtime requirements. A skill that isn't registered/discovered "is a skill that doesn't exist" — always verify it appears in the available-skills list after install. Anthropic's internal model is organic: upload to a sandbox, gain traction, then PR into the marketplace; usage is measured via a PreToolUse hook that logs skill invocations.
## Recommendations
 
**Stage 1 — Build your first dev skill (today).** Pick one high-frequency, repeatable task (code review, scaffolding, or a verification/test-runner). Run `init_skill.py` (or ask Claude to scaffold). Write a lean `SKILL.md`: a third-person, trigger-rich `description`; a concise overview; one worked input/output example; and a clear workflow. Put it in `.claude/skills/<name>/` and commit it. **Benchmark to change course:** if `/doctor` shows description-budget overflow, or the skill doesn't fire on 8/10 natural phrasings, rewrite the description (add trigger phrases + negative triggers).
 
**Stage 2 — Add determinism (week 1).** Move any mechanical step (parsing, validation, posting PR comments, formatting) into a `scripts/` file. Make it non-interactive, give it meaningful exit codes, structured stdout + stderr diagnostics, a `--help`, and self-documenting constants. Add a validation loop. **Threshold:** if outputs still vary run-to-run, tighten degrees of freedom (move from text guidance to a fixed script command) and add a strict template.
 
**Stage 3 — Manage context (week 2).** Split anything past ~300–500 lines into `references/` (one level deep, with a TOC if >100 lines) organized by domain. Offload specialized procedures from CLAUDE.md into skills. Audit startup context with `/context`; prune or set rarely-used skills to `"name-only"`. **Threshold:** if baseline context exceeds ~10% of the window before work begins, consolidate to one skill per capability and disable unused plugins.
 
**Stage 4 — Test, version, distribute (ongoing).** Write ≥3 evals per important skill and establish a no-skill baseline; only keep a skill if it measurably beats baseline (fewer tool calls/tokens, higher pass rate). Test across the models you use. Version in git, pin marketplace installs to tags, and capture every new edge case as a one-line addition to a **Gotchas** section. **Threshold:** if a skill's pass rate equals baseline, either strengthen the test cases or retire the skill (the model may have outgrown it).
 
**General principles that apply across all surfaces (Claude.ai, API, Cowork, Code):** progressive disclosure (metadata always visible, body on trigger, files on demand); third-person trigger-rich descriptions; conciseness; one skill = one job; examples over rules; scripts for determinism; evals before docs. Surface-specific deltas: Claude Code adds invocation control, subagent forking, dynamic `!` injection, and personal/project/plugin scoping; the API has no network/runtime-install and no subagents; Claude.ai/Cowork manage skills via Settings/directory and adapt output to the surface (e.g., Excel vs. Word).
 
## Caveats
- **Progressive disclosure is not always perfectly realized.** Independent bug reports show some plugin/skill configurations loading full bodies at startup. Treat the ~100-tokens-per-skill figure as the *designed* behavior (per the Agent Skills Specification) and verify your actual context with `/context` and `/doctor`.
- **Token figures are approximations.** "~100 tokens per skill," "under 500 lines / <5,000 tokens," the 1%/1,536-char budgets, and the 5,000/25,000-token compaction budgets come from official docs and community measurement; exact values vary by model context-window size and Claude Code version (e.g., the 1,536-char per-entry cap and the `skillListingBudgetFraction` setting are version-specific).
- **Some sources are community blogs**, not Anthropic. Where this guide cites real-world reports (code-review skills, token-cleanup audits, the "98% savings" framing), treat them as illustrative experience rather than official specification. Official guidance is from docs.claude.com / platform.claude.com, code.claude.com, agentskills.io, the anthropic.com / claude.com engineering blog, and the anthropics/skills repo.
- **Skills are a security surface.** Install only from trusted sources; audit all bundled files (SKILL.md, scripts, references) for unexpected network calls or operations; a malicious skill can direct Claude to exfiltrate data or misuse tools. Frontmatter is injected into the system prompt, so it's also an injection vector.
- **Evaluation tooling is evolving.** There is no single built-in eval runner in the base product; the skill-creator, "Skills 2.0," and third-party tools (MLflow harnesses, promptfoo, Braintrust, Langfuse, pulser) fill this gap with varying maturity.