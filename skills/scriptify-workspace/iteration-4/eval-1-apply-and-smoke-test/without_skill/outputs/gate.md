# Choice point

I would have paused after the delegation review and before writing any files, to present the
split and confirm the scope.

**Question I would have asked:**

> I found 4 fully deterministic steps, 1 step that splits, and 2 that should stay as prose. Here
> is the split:
>
> - Delegate: step 1 (list and count files), step 2 (heading-format check), step 3 (per-category
>   entry counts), step 5 (render the version-sorted summary table).
> - Split: step 6 — validating tags against the allowed list is mechanical, but judging whether a
>   `Misc` entry belongs in another category is not.
> - Keep as prose: step 4 (the release narrative) and step 7 (flagging confusing entries).
>
> How would you like me to proceed?
>
> 1. Apply all of it — one script covering steps 1, 2, 3, 5 and the mechanical half of 6, plus the
>    SKILL.md rewrite that calls it.
> 2. Apply only the unambiguous four (1, 2, 3, 5) and leave step 6 entirely in prose.
> 3. Split into separate scripts per concern (a validator and a reporter) instead of one script.
> 4. Show me the script before I touch SKILL.md.
> 5. Stop here — just the review, no changes.

**How I resolved it without asking:** the prompt says "apply all the delegations you find", so I
took option 1. I chose one script over option 3 because the two concerns read the same files and
share the same parser; two scripts would parse every changelog twice and duplicate the entry
regex for no gain.
