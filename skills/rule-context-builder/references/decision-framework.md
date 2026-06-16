# Decision Framework: Where Should This Instruction Live?

Distilled from `memory-and-rules-best-practices.md`. Use this to route each piece of
input context to its correct home, and to author path-scoped rules correctly.

---

## The routing decision tree

Ask these questions **in order** for each discrete instruction. The first match wins.

1. **Must it be enforced every time, regardless of the model's judgment?**
   (secrets, branch protection, "never edit `migrations/`", "run eslint after every edit")
   → **Hook** (PreToolUse to block, PostToolUse to lint/format). Prose can't guarantee this.

2. **Is it a multi-step procedure or workflow, especially one needing scripts/templates?**
   ("how to run a DB migration", "our deploy checklist", "the 7-step endpoint process")
   → **Skill** (`.claude/skills/*/SKILL.md`). Loads on demand, carries helper files.

3. **Is it relevant on almost every turn, across the whole project?**
   (build/test commands, project-wide conventions, architecture-at-a-glance, common gotchas)
   → **Project root `CLAUDE.md`** (committed).

4.  **Is it relevant on almost every turn, across the whole project, but covers a specific set of conventions, standards, or style-guides?**
   (language style guide, project coding standards, team conventions)
   → **Global `~/.claude/rules/*.md`** named after its specific purpose

5. **Is it a personal preference that applies across all the user's projects?**
   (communication style, "explain root cause before fixing")
   → **Global `~/.claude/CLAUDE.md`**. Keep team/project specifics OUT.

6. **Is it a convention relevant only when working in a specific part of the codebase?**
   ("React components in `packages/ui` follow pattern X", "all `*.test.tsx`: no inline mocks")
   → **Path-scoped rule** (`.claude/rules/*.md` with `paths:`) — this skill's primary output.
   Use a rule when the convention spans scattered paths or you want rules centralized.
   Prefer a **subdirectory `CLAUDE.md`** instead if one package owns its conventions and
   wants them versioned next to the code.

7. **Is it a personal, project-specific note that shouldn't be committed?**
   → **`CLAUDE.local.md`** (gitignored) or `.claude/settings.local.json`.

## Quick lookup

| Information | Destination |
|---|---|
| "Use pnpm not npm", build/test commands | Project root CLAUDE.md |
| "I prefer concise responses" | Global ~/.claude/CLAUDE.md |
| "Components in `packages/ui` use compound-component pattern" | Path-scoped rule (`packages/ui/**`) |
| "All `*.test.tsx`: use `src/test/factories/*`, no inline mocks" | Path-scoped rule (`**/*.test.tsx`) |
| "How to run a DB migration (8 steps + script)" | Skill |
| "Never push directly to main" | Hook (PreToolUse) |
| "Always format with prettier after editing" | Hook (PostToolUse) |
| Company-wide security/compliance policy | Managed-policy CLAUDE.md |

**Distinguishing criteria:** every turn → CLAUDE.md; specific task type → skill; convention →
rule; multi-step procedure → skill; must hold deterministically → hook; needs scripts/files →
skill (it's a folder); whole project → root CLAUDE.md; one area → path-scoped rule.

---

## Path-scoped rule mechanics

A file in `.claude/rules/` with YAML frontmatter:

```markdown
---
paths:
  - "src/api/**/*.ts"
---
# API Development Rules

- All endpoints validate input with the shared zod schemas in `src/api/schemas/`.
- Return the standard error envelope from `src/api/errors.ts` — never raw throws.
```

- **`paths:` present** → rule loads only when Claude **reads** a file matching the glob.
- **`paths:` absent** → rule loads at launch, same priority as `.claude/CLAUDE.md`
  (use this for creation-time-critical conventions; see gotcha below).
- User-level rules live in `~/.claude/rules/` and load before project rules.
- Rules support recursive subdirectories (`frontend/`, `backend/`) and symlinks
  (share one rule set across repos).

## Glob rules (get these right)

- `**` = any nesting depth, `*` = one path segment. Paths are relative to project root.
- Brace expansion works: `"src/**/*.{ts,tsx}"`.
- **Quote any pattern starting with `*` or `{`.** YAML treats them as reserved indicators;
  unquoted patterns can silently fail to match. When in doubt, quote every glob.
- Prefer the **narrowest accurate** glob. `"**/*.test.tsx"` (scattered test files) vs
  `"packages/ui/**"` (one package) — match the real layout, not a guess.

## The creation-time gotcha (must warn the user)

Path-scoped rules load when Claude **reads** a matching file, **not** when it **creates** one
via Write. A rule like "all new API files must include header X" will NOT be present at the
moment a brand-new endpoint is written (the cold-start case). This is a documented, open
limitation (claude-code issues #23478, #38487).

Workarounds when a rule is creation-critical:
- (a) Drop `paths:` so the rule is unconditional (loads at launch) — costs always-on tokens.
- (b) Put the essential at-creation bit in root CLAUDE.md instead.
- (c) Nudge Claude to read an existing example before writing a new file.
- (d) Enforce truly non-negotiable creation rules with a PreToolUse hook.

Path scoping still covers the ~80–90% case (editing existing code, or creating after
exploring patterns) well — just flag the tradeoff when a rule is about new-file creation.

---

## Authoring style for rule files

- **Keep each rule file under ~100 lines** — tighter than CLAUDE.md, since it injects into
  every relevant interaction. Split a fat rule file by sub-domain.
- **Imperative and verifiable.** "Use 2-space indent" > "format properly". "API handlers
  live in `src/api/handlers/`" > "keep files organized".
- **State the why for non-obvious rules** — a rule with a reason generalizes to edge cases;
  a bare rule gets dropped when context shifts. ("Server components by default; add
  'use client' only when needed — we hit 8s LCP from over-clienting.")
- **Include "avoid" rules** — deprecated patterns and forbidden deps are as useful as do-rules.
- **Reference files/patterns, don't paste code** — snippets go stale, `file:line` refs don't.
- **Emphasis sparingly.** Reserve "IMPORTANT"/"YOU MUST" for the one or two genuinely critical
  lines. If everything shouts, nothing does.

## What does NOT belong in a rule

- Anything Claude can figure out by reading the code; standard language conventions.
- Self-evident practices ("write clean code").
- Multi-step procedures (→ skill) or deterministic guarantees (→ hook).
- Stale/time-sensitive content (current-sprint tasks, "yesterday's deploy bug").
- Secrets — reference an env var name instead.
