# Harness Fixes — turning session findings into instructional changes

When the session review surfaces a recurring problem, the durable fix usually isn't
"tell the model harder next time" — it's a change to the *harness*: the always-loaded
memory, the skills, the tool definitions, or a deterministic hook. This file maps
common findings to where the fix belongs.

## Table of contents
1. The decision rule — where a fix belongs
2. CLAUDE.md / memory fixes
3. Skill fixes
4. Hook fixes (guarantees)
5. Tool-definition fixes
6. The token-tier mental model

---

## 1. The decision rule — where a fix belongs

Ask, in order:

1. **Must it hold every time, no exceptions?** → a **hook**, not prose. "Never push to
   main," "block writes to `migrations/`," "run the formatter after every edit." A rule
   in a memory file is a polite request re-issued every turn; a PreToolUse hook is
   enforced once and free thereafter.
2. **Is it a multi-step procedure, or does it need scripts/templates/reference files?**
   → a **skill**. Loads on demand, keeps tokens out of every session.
3. **Is it a convention that's always true across the whole project?** → **project-root
   CLAUDE.md** (committed).
4. **Is it a personal preference across all your projects?** → **global
   `~/.claude/CLAUDE.md`**.
5. **Does it only matter in one part of the tree?** → a **path-scoped rule**
   (`.claude/rules/*.md` with a `paths:` glob) or a subdirectory CLAUDE.md.

Shorthand: **conventions go in memory; procedures go in skills; guarantees go in hooks.**

## 2. CLAUDE.md / memory fixes

Recommend these when the session shows the model ignoring known rules, re-learning the
same facts, or carrying a bloated always-loaded layer.

- **Keep it under ~200 lines.** It's loaded in full on every turn of every session —
  the most expensive kind of token. The litmus test for each line: *"If I deleted this,
  would Claude make a mistake?"* If not, cut it. Bloated memory files actively *cause*
  the model to ignore the rules that matter.
- **Capture repeated mistakes.** If the session shows Claude making the same error twice,
  or a correction the user had to type more than once, that's a one-line CLAUDE.md
  addition (a Gotcha), not a one-off chat fix.
- **Front-load critical rules** (primacy bias) and reserve one or two "IMPORTANT"
  markers for the rules that truly can't slip — if everything shouts, nothing is heard.
- **State the why** for non-obvious rules ("use constructor injection — field injection
  breaks testability") so the model generalizes to edge cases instead of dropping a bare
  command when context shifts.
- **Cut the anti-patterns:** the Kitchen Sink (documenting everything), the Fossil
  (stale/time-sensitive lines like "yesterday's deploy bug"), the Contradiction (two
  rules pulling opposite ways — the model may pick one arbitrarily), the Menu ("use X or
  Y or Z" — give one default + an escape hatch), and the Obvious ("write clean code").
- **Prefer pointers to imports.** `@imports` are inlined at launch and cost full tokens;
  a "read `references/schema.md` when relevant" pointer costs nothing until needed.

## 3. Skill fixes

Recommend a skill when the session shows the same multi-step procedure being worked out
from scratch, or the same helper script written repeatedly.

- **Make it a skill the third time** the user pastes the same playbook into chat, or the
  third time the model reinvents the same helper.
- **The description is the router.** It alone decides whether the skill fires, and the
  failure mode is *under*-triggering. Write it third person, pushy, with concrete trigger
  phrases ("use whenever the user mentions X, Y, or Z, even if they don't say 'Z'") and
  negative triggers ("do NOT use for …, use the other skill instead").
- **Progressive disclosure:** keep SKILL.md lean (<500 lines), push mechanical work into
  `scripts/` (run, not loaded — only stdout costs tokens), put docs in `references/`
  (read on demand), templates in `assets/`. Ten skills cost ~1,000 startup tokens, not
  50,000, because only name+description preload.
- **If the session shows tool sprawl or duplicated work,** a skill that bundles the right
  script and a tight workflow often fixes it better than more prose.

## 4. Hook fixes (guarantees)

If the review found a rule that *must* hold but didn't (a write to a protected path, a
missing format/lint step, a push to a protected branch), the fix is a hook, not a
stronger sentence in CLAUDE.md. PreToolUse blocks an action before it happens; PostToolUse
lints/formats after. This is the only way to get a deterministic guarantee — prose is
advisory and degrades as context grows.

## 5. Tool-definition fixes

When the session shows misselection, repeated wrong-tool calls, or unbounded outputs:

- **Differentiate descriptions and names** so two tools aren't confusable.
- **Bound outputs** with default limits, pagination, and an `--output`-to-file option.
- **Make errors actionable** (what went wrong, what was expected, what to try) so the
  model self-corrects in one turn instead of retrying blindly.
- **Stabilize tool ordering** (fixed/sorted) to protect the prompt cache.

## 6. The token-tier mental model

Map every piece of knowledge to a tier by how *hot* it is, and keep hot data tiny:

| Tier | Holds | Loads | Keep it |
|---|---|---|---|
| L1 — always | CLAUDE.md: build commands, architecture-at-a-glance, a few gotchas | every turn | tiny (<200 lines) |
| L2 — locality | path-scoped rules (`paths:` globs) | when a matching file is touched | <100 lines |
| L3 — task | skill bodies | when the task matches the description | <500 lines |
| Disk — on demand | references, scripts, assets | read/run only when needed | unbounded |

A finance query should never load the sales schema; a payments-deploy skill should never
wake while editing inventory. Organize references by domain so only the needed file loads.
