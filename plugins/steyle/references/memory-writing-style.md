# Memory and Rules Writing Style Guide

House style for the always-loaded layer: `CLAUDE.md`, `MEMORY.md`, and `.claude/rules/*.md`. This guide builds on [universal-writing-style.md](../output-styles/universal-writing-style.md). Every universal rule applies. This guide adds what is specific to memory files — content selection, routing, and per-file rules.

The difference from other prose: these files load into every session. Each line is a recurring tax paid on every turn. Adherence degrades as the instruction count grows. The budget is roughly 150 to 200 instructions. The system prompt already spends about 50. A bloated memory file makes Claude worse, because it buries the rules that matter.

## Contents

- [The litmus test](#the-litmus-test)
- [Routing — where a fact belongs](#routing--where-a-fact-belongs)
- [Style deltas from the universal guide](#style-deltas-from-the-universal-guide)
- [Per-file rules](#per-file-rules)
- [Maintenance](#maintenance)
- [Worked before/after](#worked-beforeafter)
- [Checklist](#checklist)

---

## The litmus test

For every line ask: "If I removed this, would Claude make a mistake?" If not, remove it.

**Include:**
- Commands Claude cannot guess, with their exact flags.
- Conventions that differ from language or framework defaults.
- Architectural decisions specific to the project.
- Environment quirks: required env vars, version pins.
- Gotchas that Claude tripped on before. The second occurrence of the same correction is the signal to write the line.

**Exclude:**
- Anything Claude derives by reading the code, the git history, or the README.
- Standard conventions Claude already follows ("write clean code").
- Detailed API docs — link instead.
- Time-sensitive content: sprint tasks, running checklists, yesterday's bug.

## Routing — where a fact belongs

Ask in order. The first match wins.

| Question | Destination |
|---|---|
| Must it hold every time, with no judgment? | Hook, not prose — prose is advisory |
| Is it a multi-step procedure, or does it need scripts? | Skill |
| Is it relevant on almost every turn, project-wide? | Project root `CLAUDE.md` |
| Is it a personal preference across all projects? | `~/.claude/CLAUDE.md` |
| Is it relevant only in part of the tree? | `.claude/rules/*.md` with `paths:`, or a subdirectory `CLAUDE.md` |
| Is it personal and project-specific, not for the repo? | `CLAUDE.local.md`, gitignored |

The boundary that matters most: conventions go in memory files, procedures go in skills. A naming rule is a convention. A seven-step release process is a skill.

## Style deltas from the universal guide

- Write imperative and verifiable. "Use pnpm, not npm" beats "we generally prefer pnpm." "Run `npm test` before committing" beats "test your changes." A rule you cannot check compliance against is noise.
- Attach the reason to every non-obvious rule (universal D3). In memory files the reason also earns the line its slot. "Server components by default, because over-clienting took LCP to 8s" survives a prune. "Prefer server components" does not.
- One delta on emphasis: "IMPORTANT" or "YOU MUST" measurably improves adherence. The universal ban on ALL-CAPS relaxes here, for at most two rules per file. If everything shouts, nothing does.
- Include "avoid" rules — deprecated patterns, forbidden dependencies — because what not to do is as valuable as what to do.
- Structure with headers, bullets, and tables, not dense prose. Put critical rules first, because earlier instructions are followed more reliably than later ones.
- Do not paste code. Reference the file that holds the pattern.
- Convert relative dates to absolute ("since 2026-08") because "recently" rots.

## Per-file rules

### CLAUDE.md

- Keep each file under 200 lines. Past that, adherence degrades and the fix is migration, not louder wording: procedures to skills, guarantees to hooks, area-specific conventions to `.claude/rules/`.
- Keep the project file self-contained, because teammates do not have your global `~/.claude/` files.
- Do not duplicate the README or package.json — reference them, because repetition invites drift.
- `@` imports organize content but load at launch and save no tokens. For content not needed every session, write a pointer instead: "read `docs/deploy.md` before a deploy."

### .claude/rules/*.md

- Scope each file with `paths:` frontmatter. One topic per file. Keep each under about 100 lines, because a matched rule injects into every interaction with matching files.
- Quote globs that start with `*` or `{` — unquoted, YAML parses them as indicators and the rule silently fails.
- Do not rely on a path-scoped rule at file creation. Rules load when Claude reads a matching file, not when it writes a new one. Put creation-time essentials in CLAUDE.md or a hook.

### MEMORY.md and memory files

- Keep MEMORY.md an index only: one line per memory, `- [Title](file.md) — hook`. Content lives in the individual files, because only the first 200 lines of the index load each session.
- Hold one fact per memory file, with frontmatter (`name`, `description`, `type`). The description alone drives recall, so write it like a trigger, not a summary.
- Link related memories with `[[name]]`. A link to a memory that does not exist yet marks something worth writing, not an error.
- Update the existing file instead of writing a near-duplicate. Delete a memory that turns out wrong, because a stale memory misleads with the authority of a note-to-self.

## Maintenance

- Test in a fresh session after every change. Treat the file like code. Review edits in PRs and assign an owner.
- Read the ignore signal correctly: when Claude starts ignoring a rule, the file is too long. Prune before rewording and before adding emphasis.
- Prune model-compensation rules after every major model release. Comment out one piece at a time. Keep only what is still load-bearing, because rules written for an older model's limits become pure friction.
- When you type the same correction twice in chat, move it into the file while the gap is fresh.

## Worked before/after

**Before:**

> We generally try to keep things consistent with our existing patterns. Testing is important, so make sure things are tested appropriately before you commit. Note that we recently switched package managers, so various commands may be different than you expect.

**After:**

> Use pnpm, not npm — the repo switched in 2026-06 and npm lockfiles break CI. Run `pnpm test` before every commit.

Faults fixed: no verifiable action ("consistent," "appropriately"), no actor, relative date ("recently"), and three sentences of filler that would tax every future session.

## Checklist

Run against the finished file. Fix faults. Never annotate them.

- [ ] Universal checklist passes ([universal-writing-style.md](../output-styles/universal-writing-style.md#checklist))
- [ ] Every line passes the litmus test: removal would cause a mistake
- [ ] No procedures, no guarantees, no area-specific content — each routed out per the table
- [ ] Every rule is verifiable, with zero "appropriately / properly / as needed"
- [ ] At most two emphasized rules per file
- [ ] Critical rules first
- [ ] All dates absolute
- [ ] CLAUDE.md under 200 lines
- [ ] Each rules file under ~100 lines
- [ ] Globs quoted in `paths:` frontmatter
- [ ] MEMORY.md is an index only
- [ ] One fact per memory file
- [ ] No content duplicated from README, docs, or code
