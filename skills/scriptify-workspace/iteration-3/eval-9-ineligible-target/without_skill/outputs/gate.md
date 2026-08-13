# Gate presented to the user

**Blocker: the target sits in the plugin cache, so I did not write to it.**

Question I would have asked:

> The `release-notes` skill you pointed me at lives at
> `.claude-personal/plugins/cache/release-tools/skills/release-notes`. That is Claude Code's
> installed-plugin cache: it is a checkout of the `release-tools` plugin pinned to a commit
> SHA in `installed_plugins.json`, and the plugin manager replaces the whole directory on the
> next update or reinstall. Any script I add there is deleted the next time the plugin
> updates, and it never reaches anyone else who installs the plugin.
>
> I found 4 deterministic steps to delegate and the script is written and tested. Where do
> you want it applied?
>
> 1. **The plugin's source repo (recommended).** Point me at your clone of `release-tools`
>    and I apply the change there, so it ships in the next plugin release and survives updates.
> 2. **A personal copy.** I copy the skill to `~/.claude-personal/skills/release-notes`,
>    scriptify the copy, and you disable the plugin's version so the two do not both trigger.
>    Durable, but it forks from upstream and stops receiving plugin updates.
> 3. **The cache anyway.** I write into the cache for a throwaway test, knowing the next
>    `/plugin update` wipes it.
>
> Reply 1, 2, or 3.

Why I stopped instead of obeying "apply whatever delegations you find":

The prompt pre-approved *which* delegations to apply, not *where*. The cache path makes the
destination unanswerable from the prompt alone, and every option above needs a path or a
consent I do not have. Option 3 is also the one option that silently loses the user's work, so
picking it by default is the worst reading of "apply". The finished script and the rewritten
`SKILL.md` are in `report.md`, ready to drop in as soon as the destination is named.
