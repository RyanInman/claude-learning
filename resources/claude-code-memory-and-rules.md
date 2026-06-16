# The Complete Guide to Claude Code Memory & Rules Files: Authoring, Token Economics, and Where Information Should Live
 
## TL;DR
- **Keep the always-loaded layer tiny and push everything situational behind on-demand loading.** Anthropic's official rule of thumb is a CLAUDE.md under 200 lines per file containing only "facts Claude should hold in every session"; multi-step procedures move to skills, and conventions relevant only to part of the tree move to path-scoped rules in `.claude/rules/` (with `paths:` glob frontmatter) or per-directory CLAUDE.md files.
- **The decision rule is frequency × locality × type.** Always-relevant knowledge → CLAUDE.md (global `~/.claude` for personal, project root for team). Location-specific knowledge → path-scoped rule or subdirectory CLAUDE.md. On-demand procedures/workflows that need scripts → skills. Non-negotiable guarantees → hooks, not prose.
- **CLAUDE.md is advisory context, not enforced config** — delivered as a user message after the system prompt with no compliance guarantee. Empirical research (IFScale; Chroma "Context Rot") shows instruction adherence degrades non-linearly as instruction count and total context grow, so a bloated memory file actively makes Claude *worse* by burying the rules that matter.
## Key Findings
 
### How loading actually works (official mechanics)
1. **CLAUDE.md files load in full at session start** for the working directory and every ancestor directory, walking up the tree to the filesystem root. Subdirectory CLAUDE.md files load **on demand** when Claude reads a file in that directory. All discovered files are **concatenated, not overridden** — content is ordered root→working-dir, so more-specific files are read last.
2. **Five scope levels exist, in load order (broadest→narrowest):** Managed policy (org-wide, cannot be excluded) → User (`~/.claude/CLAUDE.md`) → Project (`./CLAUDE.md` or `./.claude/CLAUDE.md`) → Local (`./CLAUDE.local.md`, gitignored) → subdirectory CLAUDE.md. When instructions conflict, "Claude uses judgment to reconcile them, with more specific instructions typically taking precedence" — but the docs also warn that if two rules contradict, "Claude may pick one arbitrarily."
3. **Path-scoped rules** (`.claude/rules/*.md` with `paths:` YAML frontmatter) are a newer, real, documented system. Rules **without** `paths` load at launch with the same priority as `.claude/CLAUDE.md`. Rules **with** `paths` load only when Claude reads a file matching the glob. User-level rules live in `~/.claude/rules/` and load before project rules.
4. **Imports (`@path/to/file`)** are expanded and loaded into context at launch — they help organization but **do not reduce tokens**. Recursive imports are allowed (the official docs state a maximum depth of four hops; some community sources cite five). Relative paths resolve relative to the importing file.
5. **Compaction behavior:** project-root CLAUDE.md survives `/compact` (re-read from disk and re-injected). Nested/subdirectory CLAUDE.md and path-scoped rules are **not** re-injected automatically — they reload next time Claude reads a matching file. Conversation-only instructions are lost entirely. You can add `"When compacting, always preserve…"` instructions to CLAUDE.md to protect critical context.
6. **Auto memory** (v2.1.59+, on by default): Claude writes its own notes to `~/.claude/projects/<project>/memory/MEMORY.md`. The first 200 lines / 25KB of MEMORY.md load every session; topic files load on demand. It is machine-local, shared across worktrees of the same repo, but not shared via git.
7. **The `#` inline-memory shortcut was discontinued/deprecated.** Use `/memory` to edit files directly, or ask Claude conversationally ("add this to CLAUDE.md" / "remember that…"). HTML comments `<!-- … -->` in CLAUDE.md are stripped before injection (free maintainer notes that don't cost tokens).
### The accuracy-vs-overhead evidence
- Anthropic states it plainly in the official memory docs: *"For every line, ask yourself, 'If I removed this, would Claude make a mistake?' If not, remove it. Bloated CLAUDE.md files cause Claude to ignore actual instructions!"*
- **IFScale benchmark (Jaroslawicz et al., Distyl AI, arXiv:2507.11538, July 15 2025):** *"We evaluate 20 state-of-the-art models across seven major providers and find that even the best frontier models only achieve 68% accuracy at the max density of 500 instructions."* The best models stay near-perfect through ~100–250 instructions; the top two (gemini-2.5-pro 68.9%, o3-high 62.8%) hold near-perfect through 150+. Three degradation patterns emerge: **threshold decay** (reasoning models — o3, gemini-2.5-pro), **linear decay** (gpt-4.1, claude-sonnet-4), and **exponential decay** (gpt-4o, claude-3.5-haiku — rapid early collapse to a 7–15% floor). **Primacy bias** is confirmed — earlier instructions are followed more reliably than later ones, peaking around 150–200 instructions — so putting critical rules first helps (but stops helping at extreme densities). Claude Sonnet 4 scored 42.9% and Claude Opus 4 44.6% at 500 instructions; notably *"claude-3.7-sonnet outperforms the newer claude-opus-4 and claude-sonnet-4 at max density (52.7% vs. 44.6% and 42.9% respectively)."*
- **An actionable budget figure:** Builder.io's widely-circulated "50 Claude Code Tips" (drawn from Anthropic docs and input from Claude Code creator Boris Cherny) frames it as *"roughly a 150-200 instruction budget before compliance drops off, and the system prompt already uses about 50 of those"* — consistent with IFScale's degradation onset.
- **Chroma "Context Rot" (Kelly Hong, Anton Troynikov, and Jeff Huber; Chroma technical report, July 2025):** *"we evaluate 18 LLMs, including the state-of-the-art GPT-4.1, Claude 4, Gemini 2.5, and Qwen3 models. Our results reveal that models do not use their context uniformly; instead, their performance grows increasingly unreliable as input length grows."* Critically, *"a model with a 200K token window can exhibit significant degradation at 50K tokens. The decline is continuous, not a cliff."* The "lost in the middle" effect (Liu et al., Stanford, TACL 2024 — the U-shaped attention curve) compounds this: content in the center of long context receives the least attention, with documented accuracy drops exceeding 30% when key information sits in the middle.
- **Community measurement:** HumanLayer's context-engineering work targets **40–60% context utilization**, observing quality drops above ~80% and treating the ~170K usable window as something to spend as little of as possible.
- **Net implication:** every always-loaded line is a recurring tax paid on *every* turn of *every* session, competing for the same finite attention as the live task. This is the core reason to ruthlessly minimize the always-loaded layer.
### Rules vs skills boundary (the crux)
Anthropic's framing across the docs and the "Lessons from building Claude Code: How we use skills" blog: **"Conventions go in CLAUDE.md, procedures go in skills."** Conventions are things that are always true (a naming rule); workflows are repeatable multi-step processes for specific task types (a seven-step API-endpoint creation process). The official memory doc is explicit: *"If an entry is a multi-step procedure or only matters for one part of the codebase, move it to a skill or a path-scoped rule instead."* Skills are folders (not just markdown) that can carry scripts, templates, and reference files, loading via progressive disclosure (description visible always, body loads on match). Skills can also be path-scoped via `paths:` frontmatter.
 
## Details
 
### 1. Authoring best practices for rule/memory files
 
**Size and conciseness.** Target **under 200 lines per CLAUDE.md file** (official). Community experience reports converge on 20–80 lines for small repos/libraries, with degradation and contradiction risk rising past ~200 lines. The litmus test from Anthropic's best-practices doc: *for each line, ask "Would removing this cause Claude to make mistakes?" If not, cut it.*
 
**The official include/exclude table:**
 
| ✅ Include | ❌ Exclude |
|---|---|
| Bash commands Claude can't guess | Anything Claude can figure out by reading code |
| Code style rules that differ from defaults | Standard language conventions Claude already knows |
| Testing instructions and preferred test runners | Detailed API docs (link instead) |
| Repo etiquette (branch naming, PR conventions) | Information that changes frequently |
| Architectural decisions specific to your project | Long explanations or tutorials |
| Dev environment quirks (required env vars) | File-by-file descriptions of the codebase |
| Common gotchas / non-obvious behaviors | Self-evident practices like "write clean code" |
 
**Writing style.**
- **Imperative, not aspirational.** "Use pnpm, not npm or yarn" beats "we generally prefer pnpm." "Server components by default; add 'use client' only when needed" is testable; "write clean code" is noise.
- **Specific enough to verify.** "Use 2-space indentation" > "format code properly." "Run `npm test` before committing" > "test your changes." "API handlers live in `src/api/handlers/`" > "keep files organized."
- **State the "why" for non-obvious rules.** A rule with a reason ("we hit 8s LCP from over-clienting") generalizes to edge cases; a bare rule gets dropped when context shifts.
- **Emphasis sparingly.** Anthropic confirms adding "IMPORTANT" or "YOU MUST" improves adherence — reserve it for the one or two genuinely critical rules; if everything shouts, nothing does. (Anthropic notes it occasionally runs CLAUDE.md files through prompt optimizers internally.)
- **Structure with headers and bullets**, not dense prose; use tables and short code blocks. Don't paste code — reference files/patterns instead.
- **Include "avoid" rules** (deprecated patterns, forbidden deps, known anti-patterns) — what not to do is as valuable as what to do.
**Anti-patterns to avoid.**
- **The over-specified/bloated file** ("the kitchen sink"): the diligent dev who documents everything and dilutes the rules that matter. The worst CLAUDE.md files are the thorough ones, not the empty ones — an empty file costs nothing, a bloated one actively makes Claude worse.
- **Restating model defaults / obvious practices.** Claude already wants to write clean code.
- **Stale / time-sensitive content** (execution plans, running checklists, "yesterday's deploy bug," current-sprint tasks). Memory files should not become fossils; plans belong in plan docs, issues, or prompts.
- **Contradictory rules across hierarchy levels** — e.g., one dev adds "use interfaces for object types," another adds "prefer type aliases for unions," and six months later both sit in CLAUDE.md pulling opposite ways. Claude then behaves inconsistently.
- **Duplicating the README / package.json / docs.** Reference them with `@` imports or links; repetition wastes context and invites drift.
- **Over-constraining (railroading).** Rules written to compensate for an older model's limitations (e.g., "break every refactor into single-file changes") become friction once a newer model handles the case natively.
- **Using CLAUDE.md for guarantees.** "Never edit `.env`" in prose is a request, not enforcement — use a PreToolUse hook.
**Curating auto memory and the `/memory` command.** `/memory` lists every CLAUDE.md, CLAUDE.local.md, and rules file loaded in the session, toggles auto memory, and opens files in your editor. Auto memory is plain markdown you can audit, edit, or delete. Because Claude decides what to persist, review it periodically to prune stale or contradictory notes. The discontinued `#` shortcut is replaced by conversational requests ("remember that…") which route to auto memory, or "add this to CLAUDE.md" / `/memory` for the committed files.
 
**Verifying and debugging rule adherence.**
- Run **`/memory`** to confirm a file is actually loaded — if it's not listed, Claude can't see it (e.g., a nested file that hasn't loaded yet).
- Use the **`InstructionsLoaded` hook** to log exactly which instruction files load, when, and why — useful for intermittent path-scoped-rule issues.
- Make the instruction more specific; check for conflicts across files.
- **Test in a fresh session** after every change — observe whether behavior actually shifts. Treat CLAUDE.md like code.
- If a rule must hold every time, escalate it to a **hook** (deterministic) or `--append-system-prompt` (system-level, but must be passed each invocation).
### 2. Path-scoped rules — mechanics, gotchas, and a known limitation
 
**Syntax.** A file in `.claude/rules/` with YAML frontmatter:
```
---
paths:
  - "src/api/**/*.ts"
---
# API Development Rules
- All endpoints must include input validation
- Use the standard error response format
```
Globs follow standard rules: `**` = any nesting depth, `*` = one segment, paths relative to project root. Brace expansion works: `"src/**/*.{ts,tsx}"`. **Quote patterns starting with `*` or `{`** — YAML treats them as reserved indicators and unquoted patterns can silently fail. Rules support symlinks (for sharing a central rule set across repos) and recursive subdirectory discovery (organize into `frontend/`, `backend/`).
 
**Critical gotcha — read-only triggering.** Path-scoped rules load when Claude **reads** a matching file, **not when it creates one via Write**. A rule like "all new API files must include header X" won't be present at the exact moment Claude writes a brand-new endpoint (the cold-start case). This is a documented, community-confirmed limitation with open GitHub issues (#23478, #38487). Workarounds: (a) make creation-time essentials **unconditional** (no `paths`) or put them in CLAUDE.md; (b) nudge Claude to read existing examples before writing; (c) enforce truly non-negotiable creation rules with a PreToolUse hook. Path scoping covers the ~80–90% case (editing existing code, or creating after exploring patterns) well.
 
**Path-scoped rules vs subdirectory CLAUDE.md (official comparison):**
 
| | Per-directory CLAUDE.md | Path-scoped rule in `.claude/rules/` |
|---|---|---|
| File location | Inside the directory, alongside code | Central `.claude/` at repo root |
| Loads when | At launch if started there, or on demand when Claude reads a file there | When Claude works with a file matching the `paths:` glob |
| Best when | Directory owners maintain their own conventions; versioned with the code | All conventions in one place, or the same rule applies to many scattered paths (e.g., `**/*.test.tsx` across every package) |
 
Keep path-scoped rule files even tighter than CLAUDE.md — community practice suggests under ~100 lines, since they inject into every relevant interaction.
 
### 3. The decision framework — where should a given piece of information live?
 
Ask these questions in order:
 
**Q1: Does it need to be enforced every time, regardless of Claude's judgment?**
→ **Hook** (PreToolUse to block, PostToolUse to lint/format). Not CLAUDE.md. "Never push to main," "block writes to `migrations/`," "run eslint after every edit," "reject `rm -rf /`."
 
**Q2: Is it a multi-step procedure or workflow (especially one needing scripts/templates/reference files)?**
→ **Skill** (`.claude/skills/*/SKILL.md`). "How to run a database migration," "our deploy checklist," "the seven-step API-endpoint creation process," "how to cut a release." Loads on demand (description matched to task), keeps tokens out of every session. Can be path-scoped and can carry helper files. *(See your companion SKILL.md report for authoring depth; the boundary is: knowledge that's always true = rule; repeatable procedure = skill.)*
 
**Q3: Is it relevant on (almost) every turn, across the whole project?**
→ **Project root CLAUDE.md** (committed). Build/test commands, project layout, architecture-at-a-glance, project-wide conventions, common gotchas. Example: "Use pnpm, not npm. Run `pnpm typecheck` after TS changes. DB queries go through `/lib/supabase.ts`."
 
**Q4: Is it a personal preference that applies across all your projects?**
→ **Global `~/.claude/CLAUDE.md`** (not in any repo). Communication style, editor/terminal, "explain root cause before fixing," "prefer early returns." Keep team-specific and project-specific content OUT of here. (Or `~/.claude/rules/*.md` for personal path-scoped patterns.)
 
**Q5: Is it relevant only when working in a specific part of the codebase?**
→ **Path-scoped rule** (`.claude/rules/x.md` with `paths:`) if the convention spans scattered paths (all test files, all migrations) or you want all rules centralized; **OR subdirectory CLAUDE.md** if a package/subsystem owns its own conventions and you want them versioned next to the code. Example: "React components in `packages/ui` follow pattern X" → path-scoped to `packages/ui/**` or a `packages/ui/CLAUDE.md`.
 
**Q6: Is it a personal, project-specific note you don't want to commit?**
→ **`CLAUDE.local.md`** (project root, gitignored) or `.claude/settings.local.json`. Your sandbox URLs, preferred test data, personal overrides. Note: across worktrees a gitignored local file only exists where created — to share personal prefs across worktrees, import from home: `@~/.claude/my-project-instructions.md`.
 
**Concrete worked examples:**
 
| Information | Lives in |
|---|---|
| "Use pnpm not npm" | Project root CLAUDE.md |
| "I prefer concise responses, American English" | Global `~/.claude/CLAUDE.md` |
| "Components in `packages/ui` use the compound-component pattern" | Path-scoped rule (`packages/ui/**`) or `packages/ui/CLAUDE.md` |
| "All `*.test.tsx` files: no inline mocks, use `src/test/factories/*`" | Path-scoped rule (`**/*.test.tsx`) |
| "How to run a DB migration (8 steps + script)" | Skill |
| "Never push directly to main" | Hook (PreToolUse), reinforced in managed CLAUDE.md |
| "Our deploy checklist" | Skill (`/deploy`, often `disable-model-invocation: true`) |
| Company-wide security/compliance policy | Managed policy CLAUDE.md |
 
**Quick distinguishing criteria:**
- **Frequency:** every turn → CLAUDE.md; specific tasks → skill.
- **Knowledge vs procedure:** knowledge/convention → rule; multi-step procedure → skill.
- **Passive vs active:** passive context Claude should always hold → CLAUDE.md; active workflow you trigger → skill/command.
- **Locality:** whole project → root CLAUDE.md; one area → path-scoped rule or subdir CLAUDE.md.
- **Needs scripts/files?** → skill (it's a folder).
- **Must auto-trigger deterministically?** → hook.
- **Token tolerance:** if you can't afford it in every session, it doesn't belong in the always-loaded layer.
### 4. Team workflow, versioning, and maintenance
 
**What to commit vs gitignore:**
- **Commit:** `CLAUDE.md` (project root, team conventions), `.claude/CLAUDE.md`, `.claude/rules/*.md` (team rules), `.claude/settings.json` (team permissions/hooks), `.claude/skills/`.
- **Gitignore:** `CLAUDE.local.md` (personal project notes), `.claude/settings.local.json` (personal permissions/overrides). Claude Code auto-gitignores `.local.` files when it creates them. If you can't edit a shared `.gitignore`, use `$GIT_DIR/info/exclude` locally.
- **Never commit:** API keys, tokens, passwords. Reference env vars in rules instead ("use environment variable `XXX_API_KEY`").
- **Settings merge, they don't override:** a project-level `deny` cannot be undone by a local `allow`. CLAUDE.md content is additive across layers.
- **Self-containment rule:** the project CLAUDE.md must be self-contained — teammates don't have your global skills, agents, or `~/.claude/CLAUDE.md`. Global files are your personal toolkit; project files are the team playbook.
- **AGENTS.md interop:** Claude reads CLAUDE.md, not AGENTS.md. If your repo uses AGENTS.md, create a CLAUDE.md that does `@AGENTS.md` (then optionally add Claude-specific rules below), or symlink. `/init` reads existing AGENTS.md, `.cursorrules`, `.windsurfrules`, `.devin/rules/`.
**Monorepo organization (official patterns):**
- **Layer by directory ("Context Cascade"):** small root CLAUDE.md (repo structure, global rules, critical gotchas) + per-package CLAUDE.md (that package's build/test commands, local conventions). Start Claude *in the package directory* so it loads root + that package only, skipping siblings.
- **`claudeMdExcludes`** (settings, any layer): skip other teams' / legacy / vendored CLAUDE.md files by glob. Managed policy files can't be excluded.
- **Scope commands per directory** so Claude runs the right (fast) tests, not the 25-minute full suite.
- **Per-directory skills** for area-specific workflows; path-scope skills so a payments-deploy skill never loads while editing inventory.
- **When per-directory layering stops scaling:** centralize into **plugins** (versioned bundles a platform team owns) and/or expose code search via an **MCP server**; use a `SessionStart` hook to recommend the right plugin for the launch directory.
- The "orchestrator/index" pattern (a master root file linking out to relevance-loaded sub-files) consistently outperforms a monolithic file at equal total line counts.
**Maintaining and auditing over time:**
- **Treat it like code:** review CLAUDE.md/rules edits in PRs, give the file a single owner accountable for consistency, prune regularly.
- **Cadence:** community converges on a **quarterly review** (with dated entries); without a cadence, a prune is undone within two sprints. Anthropic's large-codebases guidance: do a meaningful harness review **every three to six months, and after every major model release**.
- **Prune model-compensation rules after model upgrades.** Anthropic's concrete examples: a rule forcing single-file refactors, or a hook imposing `p4 edit` in Perforce, became pure overhead once the model/tooling improved. After each release, "comment out harness pieces one at a time and see what's still load-bearing."
- **Capture new gotchas at the moment they surface:** when Claude makes the same mistake twice or a code review catches something it should have known, that's a CLAUDE.md edit (not a one-off chat correction). A `Stop` hook can review the session transcript and propose CLAUDE.md updates while the gap is fresh.
- **Signal you've hit bloat:** Claude starts ignoring specific rules. The fix is almost always *shorter*, not louder. Run `wc -l CLAUDE.md`; if over 200, move automation to hooks, workflows to skills, and area-specific rules to `.claude/rules/`.
**Migration path for a bloated CLAUDE.md (recommended sequence):**
1. Run `/memory` and `wc -l` to see current size and what's loaded.
2. Delete obvious-default and stale/time-sensitive lines outright.
3. Move multi-step procedures → skills; move deterministic guarantees → hooks.
4. Move area-specific conventions → path-scoped rules (`.claude/rules/`) or subdirectory CLAUDE.md.
5. Replace pasted docs/code with `@`-imports or links (remember imports still cost tokens — prefer "read X when relevant" pointers for things not needed every session).
6. Leave the root file as a lean index: project identity, build/test commands, architecture-at-a-glance, and a few critical gotchas.
7. Test in a fresh session and re-audit in two weeks.
## Recommendations
 
**Stage 1 — Establish the baseline (day one).**
- Run `/init` to generate a starter CLAUDE.md, then refine. Keep it under ~150 lines to leave headroom (recall the ~150–200 instruction budget, ~50 of which the system prompt already consumes).
- Commit `CLAUDE.md` and `.claude/settings.json`; add `.claude/settings.local.json` and `CLAUDE.local.md` to `.gitignore` immediately.
- Put personal preferences in `~/.claude/CLAUDE.md`, not the project file.
- **Benchmark to act on:** if the project file is already over 200 lines, do the migration sequence before adding anything new.
**Stage 2 — Split as the file grows.**
- When a section is area-specific, move it to a subdirectory CLAUDE.md (if a package owns it) or a path-scoped `.claude/rules/*.md` (if it spans scattered paths). Quote your globs.
- When you paste a multi-step playbook into chat for the third time, make it a skill.
- When you want something to happen every time without asking, write a hook.
- **Threshold that changes the plan:** if Claude starts ignoring a rule, treat it as evidence the file is too long — prune before rewording or adding "IMPORTANT."
**Stage 3 — Scale to teams/monorepos.**
- Adopt the Context Cascade (lean root + per-package files), scope commands per directory, and use `claudeMdExcludes` to mute irrelevant trees.
- Assign a CLAUDE.md owner; review changes in PRs; schedule a 30-minute biweekly or quarterly prune.
- Move shared conventions into plugins/MCP once per-directory files become hard to govern.
**Stage 4 — Verify and maintain.**
- Use `/memory` and the `InstructionsLoaded` hook to confirm what's loaded.
- After every major model release, comment out compensating rules and test what's still load-bearing; delete what the model now handles natively.
- For anything that *must* hold (secrets, branch protection, formatting), use hooks — never rely on prose.
**Thresholds summary that should change your behavior:**
- File > 200 lines → migrate to rules/skills.
- Claude ignores a rule → file too long, prune.
- Claude asks about something already in CLAUDE.md → phrasing ambiguous, rewrite more specifically.
- Same correction typed twice → add to CLAUDE.md.
- Context utilization > ~60–80% in long sessions → `/clear` or use subagents for exploration.
## Caveats
- **CLAUDE.md is advisory, not enforced.** It's injected as a user message after the system prompt; there is "no guarantee of strict compliance, especially for vague or conflicting instructions." For guarantees, use hooks or `--append-system-prompt`.
- **Some features are version- and date-specific (current date June 12, 2026).** Auto memory requires v2.1.59+; the `#` shortcut was discontinued; the `.claude/rules/` path-matching system and the per-directory monorepo settings are relatively recent. Loading behaviors and filenames change with releases — verify against current official docs before standardizing a team setup.
- **Path-scoped rules don't load on file creation (Write)** — a real, open limitation. Don't rely on them for creation-time guarantees.
- **The "200 lines" and "100 lines for rules" figures are guidelines, not hard limits.** There is no enforced cap on CLAUDE.md length (unlike MEMORY.md's 200-line/25KB *load* cap); the constraint is empirical adherence degradation, not a parser limit.
- **Conflict resolution is non-deterministic.** When rules contradict across layers, Claude "may pick one arbitrarily." Within-directory precedence (local appended after main) is reliable, but cross-layer conflicts are not. Eliminate contradictions rather than relying on precedence.
- **Empirical degradation numbers come from generic benchmarks** (IFScale's 500 keyword-inclusion task; Chroma's controlled retrieval/QA tasks; Liu et al.'s lost-in-the-middle study), not from Claude Code CLAUDE.md adherence specifically. They establish the *direction and shape* of degradation (non-linear, primacy-biased, worsens with length) rather than an exact "lines-to-accuracy" curve for memory files. Community figures like "adherence collapses past 500 words" and Builder.io's "150–200 instruction budget" are reasoned extrapolations, not measured CLAUDE.md benchmarks.
- **Source provenance.** Officially sourced here: the code.claude.com memory / best-practices / features-overview / large-codebases docs, claude.com engineering blogs ("Lessons from building Claude Code," "How Claude Code works in large codebases"), and the anthropics/claude-code GitHub. Community/experience reports (HumanLayer, Builder.io, and various Medium/DEV/Substack authors) are flagged as such — they corroborate but don't override official guidance.