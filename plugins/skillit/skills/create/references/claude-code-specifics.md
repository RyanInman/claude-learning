# Claude Code Specifics

Behavior that applies only when a skill runs inside Claude Code: where skills live, how they're discovered and invoked, how they relate to slash commands and subagents, and the categories of skill that have proven most valuable in practice. Read this when authoring a skill targeted at Claude Code or debugging why one isn't firing.

## Contents

- [Locations and precedence](#locations-and-precedence)
- [Discovery](#discovery)
- [Skills vs. slash commands vs. subagents](#skills-vs-slash-commands-vs-subagents)
- [Invocation control](#invocation-control)
- [Interaction with CLAUDE.md](#interaction-with-claudemd)
- [Arguments and substitutions](#arguments-and-substitutions)
- [Bundled skills](#bundled-skills)
- [Software-development skill categories](#software-development-skill-categories)
- [Code-review experience reports](#code-review-experience-reports)

## Locations and precedence

Resolution order is **Enterprise > Personal (`~/.claude/skills/`) > Project (`.claude/skills/`)**. Plugin skills use a `plugin-name:skill-name` namespace. If a skill and a `.claude/commands/` file share a name, the skill wins. Commit project skills to git so the team shares them.

## Discovery

Project skills load from `.claude/skills/` in the start directory and every parent up to the repo root; nested package skills (e.g., `packages/frontend/.claude/skills/`) load on demand for monorepos. **Live change detection** picks up edits to an existing `SKILL.md` within the session, but creating a brand-new top-level skills directory requires a restart. A skill that doesn't appear in the available-skills list effectively doesn't exist — verify it after install.

## Skills vs. slash commands vs. subagents

Custom commands have been **merged into skills**: `.claude/commands/deploy.md` and `.claude/skills/deploy/SKILL.md` both create `/deploy`. Skills are the recommended path because they support bundled files, frontmatter invocation control, auto-invocation, and subagent execution. The key difference from a plain command: Claude can **auto-invoke** a skill based on description matching, and skills can bundle scripts. Subagents are for parallel or isolated heavy work.

## Invocation control

The field syntax and semantics (`disable-model-invocation`, `user-invocable`, `allowed-tools`) live in `references/skill-anatomy.md` under Frontmatter fields; when a missing field counts as a defect is covered in `../../../references/best-practices.md` §9.

## Interaction with CLAUDE.md

CLAUDE.md loads at session start and stays in context even for unrelated work; skills load on demand. Move specialized procedures (PR reviews, migrations, deploys) out of CLAUDE.md into skills, keeping CLAUDE.md under ~200 lines. A skill body is subject to the same conciseness test as CLAUDE.md.

## Arguments and substitutions

`$ARGUMENTS`, `$ARGUMENTS[N]` / `$N`, and named `$name` arguments are substituted into the body, plus `${CLAUDE_SKILL_DIR}` (reference bundled scripts regardless of cwd), `${CLAUDE_SESSION_ID}`, and `${CLAUDE_PLUGIN_DATA}` (a stable dir for persistent skill memory, like an append-only log).

## Bundled skills

Claude Code ships skills including `/code-review`, `/batch`, `/debug`, `/loop`, `/claude-api`, `/run`, `/verify`, and `/run-skill-generator`. Check what already exists before building something adjacent.

## Software-development skill categories

Anthropic's Claude Code team (which runs hundreds of internal skills) catalogs them into nine categories. The best skills fit cleanly into one; skills straddling several confuse the agent:

1. **Library/API reference** (`billing-lib`, `internal-platform-cli`) — reference snippets + gotchas.
2. **Product verification** (`signup-flow-driver`, `checkout-verifier`, `tmux-cli-driver`) — paired with Playwright/tmux. Singled out as the most valuable category, worth a full engineer-week to get excellent.
3. **Data fetching/analysis** (`funnel-query`, `grafana`, `datadog`).
4. **Business process / team automation** (`standup-post`, `create-ticket`, `weekly-recap`).
5. **Code scaffolding / templates** (`new-<framework>-workflow`, `new-migration`, `create-app`).
6. **Code quality / review** (`adversarial-review`, `code-style`, `testing-practices`) — can run via hooks or GitHub Actions.
7. **CI/CD and deployment** (`babysit-pr`, `deploy-<service>` with auto-rollback, `cherry-pick-prod`).
8. **Runbooks** (`<service>-debugging`, `oncall-runner`, `log-correlator`).
9. **Infrastructure operations** (`<resource>-orphans`, `dependency-management`, `cost-investigation`) — destructive actions benefit from guardrails like on-demand hooks that block `rm -rf`, `DROP TABLE`, force-push.

## Code-review experience reports

Real-world code-review skills converge on: encapsulate the comment-posting logic in a **Python script, not markdown instructions**; cap nit volume ("report at most five nits"); define a clear severity taxonomy (blocking / important / nit); list skip rules (generated code, lockfiles, anything CI already enforces); and keep approval messages terse ("LGTM").
