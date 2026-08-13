# Choice point

I would have stopped here and asked:

> I found two anchors worth converting to scripts (`Collect the link inventory`,
> `Resolve each target`), one that should stay with Claude (`Decide what to fix now`), and one
> gotcha that belongs inside the collector. How do you want to proceed?
>
> 1. Apply all — write `scripts/collect_links.py` and `scripts/resolve_links.py`, and rewrite the
>    two anchors in `SKILL.md` to call them.
> 2. Apply the scripts only — add both files, leave `SKILL.md` untouched so you can review the
>    wording yourself.
> 3. Ship as one file — `scripts/check_links.py` with `collect` and `resolve` subcommands instead
>    of two scripts, same interfaces.
> 4. Nothing — take the report as is.

Resolution: `prompt.txt` says "Don't change anything yet", which selects option 4. I stopped after
the report and wrote nothing into
`without_skill/workspace/prose-only-reviewer/`. That folder still contains only its original
`SKILL.md`, unmodified.
