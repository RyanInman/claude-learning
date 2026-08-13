# changelog-checker: which workflow steps belong in a script

I read `workspace/changelog-checker/SKILL.md` and the three files in `changelogs/`
(`v1.0.0.md`, `v1.1.0.md`, `v1.2.0.md`). Nothing was changed.

## The test I applied

A step belongs in a script when the same input must always produce the same output — file
listing, regex matching, counting, sorting, table rendering. A step stays with the model when
it needs judgment about meaning — narrative, category fit, clarity. Deterministic work done by
re-derivation drifts between runs; the counts in one run's table will not match the next.

## Verdict per step

| # | Step | Verdict | Why |
|---|------|---------|-----|
| 1 | List `.md` files in `changelogs/`, sort by version, note count | Script | Directory listing plus a version sort is pure mechanics. Semantic version sort is also a known model error: `v1.10.0` sorts before `v1.2.0` under string comparison. |
| 2 | Check each file starts with `## vX.Y.Z — YYYY-MM-DD` | Script | A single regex over line 1. The model reading for a pattern misses cases; a regex does not, and it catches the em dash vs hyphen difference that eyeballing skips. |
| 3 | Count entries per category and total across files | Script | Counting is the classic re-derivation failure. Totals must reconcile across 4 categories and N files, and hand-counted totals will not match the per-file numbers. |
| 4 | Write the one-paragraph release narrative | Model | Summarizing direction for a non-technical reader is the judgment this skill exists to supply. No script can write it. |
| 5 | Render the summary table, sorted by version descending | Script | Rendering rows from the step 3 data is formatting. Emit it from the same script that counts, so the table cannot disagree with the totals. |
| 6 | Check tags against the allowed list, then judge whether `Misc` entries fit another category | Split | Membership in `{Added, Fixed, Changed, Removed, Misc}` is a set lookup — script. Deciding that `Misc: "Corrected typo in settings page label"` is really a `Fixed` is judgment — model. The script should emit the offending entries; the model rules on them. |
| 7 | Flag entries a reader would find confusing | Model | Clarity has no mechanical definition. Leave it with the model. |

Summary: steps 1, 2, 3, 5 and the first half of 6 move to a script. Steps 4, 7 and the second
half of 6 stay with the model.

## What the script should look like

One script, not five. `scripts/scan_changelogs.py <changelogs_dir>` walks the folder once and
prints JSON:

```json
{
  "file_count": 3,
  "files": [
    {"version": "1.2.0", "path": "changelogs/v1.2.0.md", "date": null,
     "heading_ok": false,
     "counts": {"Added": 1, "Fixed": 1, "Changed": 0, "Removed": 0, "Misc": 0}}
  ],
  "totals": {"Added": 4, "Fixed": 2, "Changed": 1, "Removed": 0, "Misc": 1},
  "heading_violations": ["changelogs/v1.2.0.md"],
  "unknown_tags": [],
  "misc_entries": [
    {"file": "changelogs/v1.1.0.md", "text": "Corrected typo in settings page label"}
  ],
  "markdown_table": "| Version | Date | Added | Fixed | Changed | Removed | Misc |\n|...|"
}
```

Why one script: steps 1, 2, 3, 5 and 6a all need the same parse of the same files. Splitting
them means parsing three times and inviting the three results to disagree.

Why it also emits `markdown_table`: step 5 is presentation of step 3's numbers. If the model
retypes the table from the JSON, it can typo a count and silently contradict `totals`.

Why it emits `misc_entries` rather than deciding them: it hands the model exactly the entries
that need a judgment call, so the model reads one short list instead of re-reading every file.

The rewritten workflow then reads: run the script, then use its JSON for the narrative (4), the
`Misc` re-classification (6b), and the clarity pass (7).

## What the script would have caught here

Running that logic over the current fixture finds two real defects that the prose workflow
leaves to chance:

- `changelogs/v1.2.0.md` has no `## vX.Y.Z — YYYY-MM-DD` heading at all. It opens directly with
  `### Added`, so its version and date are unrecoverable from the file body.
- `changelogs/v1.1.0.md` carries a `Misc` entry, "Corrected typo in settings page label", which
  reads as `Fixed`. That is the exact case step 6 hands to the model.

## Two things I would fix while I was in there

Neither is a scripting question, so I am flagging rather than folding them in:

- Step 3 counts four categories but step 6 allows five. `Misc` entries are counted by no step.
  The script's schema above closes that gap by counting all five.
- The workflow never says what to do when the heading is missing, as in `v1.2.0.md`. Sorting by
  version in step 1 then depends on the filename, not the heading. Worth stating explicitly.

Nothing has been modified. Tell me to apply and I will add `scripts/scan_changelogs.py` and
rewrite the workflow section around it.
