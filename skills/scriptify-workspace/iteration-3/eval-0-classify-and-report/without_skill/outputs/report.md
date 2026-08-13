# changelog-checker: which workflow steps belong in a script

I read `workspace/changelog-checker/SKILL.md` (18 lines) and the three fixture files in
`changelogs/`. Nothing was changed.

## The test I applied

A step belongs in a script when the same input must always produce the same output — listing,
parsing, matching a fixed pattern, counting, sorting, rendering a table. A step stays in the skill
body when it needs judgment that no fixed rule captures — summarizing intent, deciding whether a
label is the right one, deciding whether a sentence reads clearly.

Steps 1, 2, 3, and 5 are fully deterministic. Step 6 is mixed. Steps 4 and 7 are judgment.

## Step-by-step

| # | Step | Verdict | Why |
|---|---|---|---|
| 1 | List every `.md` in `changelogs/`, sorted by version, note the count | **Script** | Directory listing plus a version sort. Prose sorting of semver is error-prone: `v1.10.0` sorts before `v1.2.0` under string comparison, and a model re-deriving the order each run will eventually get it wrong. |
| 2 | Check each file starts with `## vX.Y.Z — YYYY-MM-DD` | **Script** | A regex match with a yes/no answer. Note the separator is an em dash (—), not a hyphen; a script enforces that exactly, a reader skims past it. |
| 3 | Count entries per category and total across files | **Script** | Counting list items under headings. Model-counted totals drift, and nothing in the output signals when they have. |
| 4 | Write a one-paragraph release narrative for a non-technical reader | **Keep in the skill** | Requires reading intent across releases and choosing a register. No fixed rule produces this. |
| 5 | Render the summary table, sorted by version descending | **Script** | Pure formatting over data step 3 already computed. Have the script print the finished markdown table so the column set and sort order cannot drift between runs. |
| 6 | Check each entry's tag against the allowed list; for `Misc` entries, judge whether another category fits | **Split** | Two different jobs share one step. Membership in `{Added, Fixed, Changed, Removed, Misc}` is a set lookup → script. Deciding that "Corrected typo in settings page label" is really a `Fixed` is judgment → skill. The script should emit the list of `Misc` entries for the model to rule on. |
| 7 | Flag entries a reader would find confusing | **Keep in the skill** | Clarity has no mechanical definition. A script could only proxy it with length or word lists, which would flag the wrong lines. |

## The script I would add

One file, `scripts/check_changelogs.py`, run once at the start of the workflow. It takes the
changelogs directory and prints JSON:

```json
{
  "files": [{"file": "v1.2.0.md", "version": "1.2.0", "date": null, "heading_ok": false,
             "counts": {"Added": 1, "Fixed": 1}}],
  "total_files": 3,
  "totals": {"Added": 4, "Fixed": 3, "Changed": 1, "Misc": 1},
  "bad_headings": ["v1.2.0.md"],
  "unknown_categories": [],
  "misc_entries": [{"file": "v1.1.0.md", "text": "Corrected typo in settings page label"}],
  "summary_table": "| Version | Date | Added | Fixed | Changed | Removed | Misc |\n|..."
}
```

That one call covers steps 1, 2, 3, 5, and the mechanical half of 6. The rewritten workflow becomes:
run the script, then write the narrative (4), rule on the `misc_entries` it returned (6b), and read
the entries for clarity (7).

## What the fixtures already show

Running these checks by hand against the three fixture files finds:

- `v1.2.0.md` has no `## v1.2.0 — YYYY-MM-DD` heading at all — it opens with `### Added`. Step 2
  catches this, and it is exactly the kind of miss a skim overlooks.
- `v1.1.0.md` carries one `Misc` entry, "Corrected typo in settings page label", which belongs
  under `Fixed`. That is the judgment call step 6 must keep.
- No file uses a category outside the allowed list.

## One thing I'd raise separately

Step 3 says "count the entries per category" but the files use `###` subheadings, and `v1.2.0.md`
has no version heading — so a parser needs a stated rule for a file whose structure is broken:
report it and keep counting, or skip it. The skill does not say which. I would have the script
count what it can and mark the file `heading_ok: false` rather than skip it, so a malformed file
still appears in the table.

No files were modified. Say the word and I'll write the script and rewrite the workflow section.
