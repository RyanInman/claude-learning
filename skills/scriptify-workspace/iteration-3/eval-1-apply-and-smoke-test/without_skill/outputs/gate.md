# Choice point I would have presented

After classifying the 7 workflow steps, I would have stopped here:

> I found 5 steps to delegate to a script and 3 to keep as judgment (step 6 splits
> in two). Here is the split:
>
> Delegate:
> 1. List `.md` files sorted by version + total count
> 2. Heading format check (`## vX.Y.Z — YYYY-MM-DD`)
> 3. Per-category entry counts and totals
> 5. Summary table rendering, versions descending
> 6a. Category tag membership check against the allowed list
>
> Keep as Claude judgment:
> 4. The non-technical release narrative
> 6b. Judging whether a `Misc` entry belongs in another category
> 7. Flagging entries a reader would find confusing
>
> Options:
> A. Apply all 5 delegations as one script with a JSON mode and a table mode.
> B. Apply all 5 as separate scripts, one per step.
> C. Apply only a subset — name the steps you want.
> D. Show me the proposed SKILL.md rewrite first, change nothing yet.

The prompt said "apply all the delegations you find", so I took option A and
continued: one script, both modes, SKILL.md rewritten, scripts smoke-tested.

I chose one script over B without asking because the delegated steps all read the
same parse of the same folder; separate scripts would parse it five times and could
report counts that disagree with the table.
