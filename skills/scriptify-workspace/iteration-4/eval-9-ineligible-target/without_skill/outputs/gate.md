# Gate: the target is not a durable place to write

I would have stopped here and asked:

> The `release-notes` skill lives at
> `workspace/.claude-personal/plugins/cache/release-tools/skills/release-notes`.
> That path is a **plugin cache** — Claude Code rewrites it whenever the
> `release-tools` plugin updates or is reinstalled, so anything I add there is
> lost on the next update. Where should I apply the scriptified version?
>
> 1. **Personal skills directory** (recommended) —
>    `.claude-personal/skills/release-notes/`. Survives plugin updates, and a
>    user-level skill of the same name takes precedence over the plugin's copy.
> 2. **Project skills directory** — `.claude/skills/release-notes/` in a
>    specific repo. Durable and shareable with the team, but only active inside
>    that repo.
> 3. **Upstream the change** — send the script and the rewritten `SKILL.md` to
>    the `release-tools` plugin repository as a pull request. Durable for
>    everyone, but nothing works locally until it is merged and released.
> 4. **Write into the cache anyway** — works right now, disappears on the next
>    plugin update.

## What I did instead

`prompt.txt` pre-approves applying ("apply whatever delegations you find"), and
I cannot wait for an answer, so I picked option 1 and recorded it here.

**Destination applied:**
`/Users/admin/claude-learning/skills/scriptify-workspace/iteration-4/eval-9-ineligible-target/without_skill/workspace/.claude-personal/skills/release-notes/`

The plugin cache copy is left byte-for-byte unchanged.
