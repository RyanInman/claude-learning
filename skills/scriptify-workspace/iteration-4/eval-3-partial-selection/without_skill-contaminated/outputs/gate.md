# Choice point

I would have presented the delegation review below and waited for you to pick which steps to script.

**Question:** I found 4 fully delegable steps, 1 partially delegable step, and 2 that must stay
prose. Which delegations do you want me to apply?

**Options presented:**

1. Step 1 — list `.md` files sorted by version with a total count. Directory read plus a semver
   sort; no judgment. Script: `scripts/list_changelogs.py`.
2. Step 2 — validate each file's `## vX.Y.Z — YYYY-MM-DD` heading. One regex per file.
3. Step 3 — count entries per category and total across files. Counting is where a model drifts;
   a script is stable. Script: `scripts/count_entries.py`.
4. Step 5 — render the version/date/count table sorted descending. Deterministic once steps 1–3
   supply the data; best done together with step 2, which already parses the dates.
5. Step 6 (first half only) — check each entry's tag against the allowed list. The second half,
   judging whether a `Misc` entry belongs in another category, stays with the model.
6. Steps 4 and 7 — not offered. Writing a narrative and flagging confusing prose are judgment calls.

Answer with the step numbers to apply, or "all".

**Resolution:** the prompt already answered — "apply only the delegations for steps 1 and 3. Leave
everything else untouched." I applied options 1 and 3 and made no other edit.
