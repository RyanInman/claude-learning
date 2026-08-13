# Gate presented to the user

Asked after the analysis, before touching any file.

**Question:** I found four changes to `api-docs-checker`. Which should I apply?

**Options:**

1. Extract steps 1 and 3 into `scripts/check_frontmatter.py` and replace both steps in
   `SKILL.md` with a single call to it.
2. Delete step 2 — step 3 already checks `summary:`, so it is redundant.
3. Delete step 4 and the Notes paragraph — it writes to `legacy/index.txt`, and the skill's own
   Notes say the legacy portal was retired in v2. There is no `legacy/` directory.
4. Leave step 5 as prose — judging whether a description reads clearly needs a model, not a
   script.

**Reply with:** `all`, a subset (e.g. `1,3`), or `none`.

**Outcome:** The prompt said "Just tell me — don't write anything yet", so I stopped here and
wrote nothing into the skill folder.
