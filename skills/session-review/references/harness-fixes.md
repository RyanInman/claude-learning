# Harness Fixes — turning session findings into instructional changes

When the session review surfaces a recurring problem, the durable fix usually
isn't "tell the model harder next time" — it's a change to the *harness*: the
always-loaded memory, the skills, the tool definitions, or a deterministic
hook. This file maps common findings to where the fix belongs.

## Table of contents
1. The decision rule — where a fix belongs
2. CLAUDE.md / memory fixes
3. Skill fixes
4. Hook fixes (guarantees)
5. Tool-definition and MCP fixes
6. The token-tier mental model

---

## 1. The decision rule — where a fix belongs

Ask, in order:

1. **Must it hold every time, no exceptions?** → a **hook**, not prose. "Never
   push to main," "run the formatter after every edit." A rule in a memory
   file is a polite request re-issued every turn; a PreToolUse hook is
   enforced once and free thereafter.
2. **Is it a multi-step procedure, or does it need scripts/templates/reference
   files?** → a **skill**. Loads on demand, keeps tokens out of every session.
3. **Is it a convention that's always true across the whole project?** →
   **project-root CLAUDE.md** (committed).
4. **Is it a personal preference across all your projects?** → **global
   `~/.claude/CLAUDE.md`**.
5. **Does it only matter in one part of the tree?** → a **path-scoped rule**
   (`.claude/rules/*.md` with a `paths:` glob) or a subdirectory CLAUDE.md.

Shorthand: **conventions go in memory; procedures go in skills; guarantees go
in hooks.**

## 2. CLAUDE.md / memory fixes

Recommend these when the session shows the model ignoring known rules,
re-learning the same facts, or carrying a bloated always-loaded layer.

- **Keep it under ~200 lines** — now the official guidance ("Aim to keep
  CLAUDE.md under 200 lines"). It's loaded in full on every turn. The
  official per-line litmus test: *"Would removing this cause Claude to make
  mistakes? If not, cut it."* Bloated memory files actively cause the model
  to ignore the rules that matter.
- **Move conditional knowledge into skills.** Official cost guidance: skills
  load on demand, so anything that only applies to certain tasks (deploy
  steps, schema docs, style guides for one subsystem) belongs in a skill, not
  in CLAUDE.md.
- **Capture repeated mistakes.** The same error twice, or a correction the
  user typed more than once, is a one-line CLAUDE.md Gotcha, not a chat fix.
- **Front-load critical rules** (primacy bias) and reserve "IMPORTANT" for the
  one or two rules that truly can't slip — if everything shouts, nothing is
  heard.
- **State the why** for non-obvious rules so the model generalizes instead of
  dropping a bare command when context shifts.
- **Cut the anti-patterns:** the Kitchen Sink (documenting everything), the
  Fossil (stale time-sensitive lines), the Contradiction (two rules pulling
  opposite ways), the Menu ("use X or Y or Z" — one default + escape hatch),
  and the Obvious ("write clean code").
- **Prefer pointers to imports.** `@imports` are inlined at launch and cost
  full tokens; a "read `references/schema.md` when relevant" pointer costs
  nothing until needed.
- **Auto memory is capped:** only the first 200 lines / 25KB of MEMORY.md load
  at session start — keep it an index (one line per memory), not a document.

## 3. Skill fixes

Recommend a skill when the session shows the same multi-step procedure worked
out from scratch, or the same helper script written repeatedly.

- **Make it a skill the third time** the user pastes the same playbook or the
  model reinvents the same helper.
- **The description is the router.** It alone decides whether the skill fires;
  the common failure is *under*-triggering. Third person, pushy, concrete
  trigger phrases, and negative triggers ("do NOT use for X").
- **Mind the listing budget.** All skill descriptions share a budget of ~1% of
  the context window, with the combined description + `when_to_use` capped at
  1,536 chars per skill. Overflow drops the least-invoked skills'
  descriptions — the symptom is a skill silently not triggering. `/doctor`
  reports shortened/dropped entries. Knobs: `skillListingMaxDescChars`,
  `skillListingBudgetFraction`, `skillOverrides` (name-only), and
  `disable-model-invocation: true` to keep a user-only skill out of the
  listing entirely.
- **Progressive disclosure:** keep SKILL.md lean (<500 lines), push mechanical
  work into `scripts/` (run, not loaded), docs into `references/` (read on
  demand), templates into `assets/`.
- **Pin `model:` and `effort:` in frontmatter** for mechanical skills and
  subagents (`model: haiku`, `effort: low`) — the routing lever that makes
  cheap steps cheap without touching the main loop.
- **If the session shows tool sprawl or duplicated work,** a skill bundling
  the right script and a tight workflow often beats more prose.

## 4. Hook fixes (guarantees)

If the review found a rule that *must* hold but didn't (a write to a protected
path, a missing lint step, a push to a protected branch), the fix is a hook.
PreToolUse blocks an action before it happens; PostToolUse lints/formats
after. Prose is advisory and degrades as context grows; hooks are enforced.

- **Hooks run as code, not context** — only a hook's `additionalContext`
  output enters the window; the hook itself costs zero resident tokens.
- **Hooks are also a token fix:** a PostToolUse hook that condenses verbose
  tool output (test logs, build spew) before it enters context turns tens of
  thousands of tokens into hundreds, every time, deterministically.

## 5. Tool-definition and MCP fixes

When the session shows misselection, repeated wrong-tool calls, or unbounded
outputs:

- **Differentiate descriptions and names** so two tools aren't confusable.
- **Bound outputs** with default limits, pagination, and `--output`-to-file.
- **Make errors actionable** (what went wrong, what was expected, what to try)
  so the model self-corrects in one turn.
- **Stabilize tool ordering** (fixed/sorted) to protect the prompt cache.
- **Keep MCP schemas deferred.** Tool search is on by default — verify nobody
  set `ENABLE_TOOL_SEARCH=false` or forced upfront loading; disable unused
  servers via `/mcp`.
- **Prefer CLI tools over MCP servers** where both exist (`gh`, `aws`,
  `gcloud`, `sentry-cli`): a CLI adds zero per-tool listing cost and its
  output can be piped through filters before it reaches context.

## 6. The token-tier mental model

Map every piece of knowledge to a tier by how *hot* it is, and keep hot data
tiny:

| Tier | Holds | Loads | Keep it |
|---|---|---|---|
| L1 — always | CLAUDE.md: build commands, architecture-at-a-glance, a few gotchas | every turn | tiny (<200 lines) |
| L2 — locality | path-scoped rules (`paths:` globs) | when a matching file is touched | <100 lines |
| L3 — task | skill bodies | when the task matches the description | <500 lines |
| Deferred | MCP tool schemas (tool search) | when the model searches for/uses the tool | names only until used |
| Disk — on demand | references, scripts, assets | read/run only when needed | unbounded |

A finance query should never load the sales schema; a payments-deploy skill
should never wake while editing inventory. Organize references by domain so
only the needed file loads.
