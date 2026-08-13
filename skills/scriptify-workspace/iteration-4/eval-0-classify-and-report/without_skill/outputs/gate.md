Question I would have asked the user, verbatim:

> I have the classification. Five of the seven steps (1, 2, 3, 5, and the tag-validation half of
> 6) are deterministic and belong in one script; steps 4, 7, and the `Misc` judgment in 6 stay
> with the model. Want me to apply it?
>
> 1. Apply — add `scripts/scan_changelogs.py` emitting the JSON above and rewrite the workflow
>    section to call it.
> 2. Report only — leave `SKILL.md` untouched (what I did).
> 3. Apply plus fix the two defects I flagged — the uncounted `Misc` category in step 3 and the
>    undefined behavior when a version heading is missing.

Resolution: `prompt.txt` says "Don't change anything yet", which selects option 2. I wrote the
report and made no edit to `workspace/changelog-checker/SKILL.md` or any file under it.
