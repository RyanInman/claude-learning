# Bundling Executable Scripts

How to push deterministic work into scripts, design their interfaces for agents, and manage their dependencies. Read this when a skill has a mechanical, repeated step worth turning into a `scripts/` file. A common framing of an ideal skill is roughly 10% LLM steering and 90% deterministic code execution.

## Contents

- [Why scripts](#why-scripts)
- [Make execution intent explicit](#make-execution-intent-explicit)
- [Design script interfaces for agents](#design-script-interfaces-for-agents)
- [Solve, don't punt](#solve-dont-punt)
- [Dependency management](#dependency-management)
- [Claude Code performance levers](#claude-code-performance-levers)

## Why scripts

LLMs are expensive and non-deterministic at mechanical work. Pre-written scripts are more reliable, save tokens (no code in context), save time (no generation step), and ensure consistency. Write `validate_form.py` rather than asking Claude to generate validation code each run.

A strong signal to bundle a script: while iterating on test cases, you notice every run independently writes a similar helper (a `create_docx.py`, a `build_chart.py`). Write it once, put it in `scripts/`, and point the skill at it — every future invocation skips reinventing the wheel.

## Make execution intent explicit

State clearly whether Claude should _execute_ or _read_ a script:

- Execute: "Run `analyze_form.py` to extract fields." (preferred for most utility scripts)
- Read: "See `analyze_form.py` for the extraction algorithm."

## Design script interfaces for agents

Agents call scripts in non-interactive shells, so the interface must be agent-friendly:

- **No interactive prompts** — a hard requirement. Agents can't answer TTY/password/confirmation prompts; a blocking script hangs indefinitely. Accept all input via flags, env vars, or stdin.
- **Meaningful exit codes** for different failure types (not found, invalid args, auth failure), documented in `--help`.
- **Predictable output size.** Many harnesses truncate tool output beyond a threshold (often 10–30K chars), losing critical info. Default to a summary or limit, support `--offset`, and for large output require an `--output` flag (file, or `-` for stdout).
- **Safe defaults / dry-run / idempotency.** Destructive operations should require `--confirm`/`--force` and offer `--dry-run`; prefer "create if not exists" since agents may retry.
- **Structured output** (JSON/CSV/TSV) to stdout; diagnostics to stderr.
- **Helpful error messages** that say what went wrong, what was expected, and what to try. An opaque "Error: invalid input" wastes an agent turn.
- **Document usage with `--help`** — it's the primary way an agent learns the interface, so keep it concise since it enters the context window.

## Solve, don't punt

Scripts should handle error conditions (FileNotFoundError, PermissionError) rather than failing and leaving Claude to figure it out. Avoid "voodoo constants" — document why `TIMEOUT = 30`, not a bare `TIMEOUT = 47`.

## Dependency management

Prefer **self-contained scripts that declare their own inline dependencies**, so the agent runs them with one command and no separate install step:

- **Python (PEP 723):** declare deps in a TOML block inside `# /// script ... # ///` markers; run with `uv run scripts/extract.py` (creates an isolated env, installs, runs) or `pipx run`. Pin with PEP 508 specifiers (`"beautifulsoup4>=4.12,<5"`), constrain with `requires-python`, and use `uv lock --script` for reproducibility.
- **Deno:** `npm:`/`jsr:` import specifiers are self-contained by default; pin with semver (`@1.0.0`); deps cached globally.
- **Bun:** auto-installs missing packages at runtime; pin in the import path (`"cheerio@1.0.0"`).
- **One-off vs. script:** for a tool invoked with a few flags, reference the package directly in `SKILL.md` via `uvx`/`pipx run`/`npx` with pinned versions. Move to a tested `scripts/` file once the command grows complex enough to be hard to get right first try.

**Platform limits:** Claude.ai and Claude Code can install from PyPI/npm (and GitHub) at runtime; the **Claude API container has no network access and no runtime install** — all deps must be pre-installed. State prerequisites in `SKILL.md`; don't assume packages are present. Run untrusted scripts in a sandbox (e.g., Docker).

## Claude Code performance levers

- **Dynamic `!` injection.** A `` !`git diff HEAD` `` in the skill body runs the shell command _before_ Claude sees the content and inlines the result, grounding the response without a separate tool round-trip.
- **`context: fork`.** Run heavy or exploratory setup in an isolated subagent (e.g., `agent: Explore`) to keep the main conversation's context clean and enable parallel work.
