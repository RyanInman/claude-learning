# changelog-checker: delegable-step review

Reviewed `workspace/changelog-checker/SKILL.md` (7 workflow steps). Per your instruction I applied
the delegations for **steps 1 and 3 only**; every other step is untouched.

## Review of all seven steps

| Step | What it does | Delegable? | Why |
|---|---|---|---|
| 1 | List `.md` files sorted by version, note count | **Yes - applied** | Pure file enumeration and version sort. Same input always gives the same list; no judgment. |
| 2 | Check each file's `## vX.Y.Z — YYYY-MM-DD` heading | Yes - not applied | A regex match per file. Deterministic, but out of scope for this run. |
| 3 | Count entries per category, total across files | **Yes - applied** | Counting bullets under `###` headings. Arithmetic, and a model re-deriving it by eye miscounts. |
| 4 | Write a one-paragraph release narrative | No | Requires reading meaning and audience. A script cannot write prose for a non-technical reader. |
| 5 | Render the summary table | Partly | The rendering is mechanical, but it needs the dates from step 2 and the counts from step 3. Worth folding into a single report script only after step 2 is delegated too. |
| 6 | Check tags against the allowed list; judge `Misc` entries | Partly | The membership check is deterministic; deciding whether "Corrected typo in settings page label" is really `Changed` is judgment. Split, don't delegate whole. |
| 7 | Flag confusingly written entries | No | Pure language judgment. |

## What I created

`scripts/list_changelogs.py` - step 1.

- Usage: `python3 scripts/list_changelogs.py changelogs`
- Sorts by parsed `vX.Y.Z` numerically, so `v1.10.0` sorts after `v1.9.0` - a plain alphabetical
  sort gets that wrong. Files without a version sort last, alphabetically.
- Prints `{"files": [{"file", "version"}], "count"}`.
- Exits 1 with a message on stderr if the directory is missing.

`scripts/count_categories.py` - step 3.

- Usage: `python3 scripts/count_categories.py changelogs`
- Counts `- ` bullets under each `### Category` heading.
- Reports **every** category it finds, not only the four named in step 3. That is deliberate:
  step 6 needs to see the raw tags, and `v1.1.0.md` has a `Misc` section that a hardcoded
  four-category filter would have silently dropped.
- Prints `{"per_file", "totals", "categories", "grand_total"}`.

## Smoke tests (run before the SKILL.md rewrite)

Both scripts ran against the real `changelogs/` fixture and exited 0.

`list_changelogs.py` output:

```json
{"files": [{"file": "v1.0.0.md", "version": [1,0,0]},
           {"file": "v1.1.0.md", "version": [1,1,0]},
           {"file": "v1.2.0.md", "version": [1,2,0]}],
 "count": 3}
```

`count_categories.py` output:

```json
{"per_file": {"v1.0.0.md": {"Added": 2, "Fixed": 1},
              "v1.1.0.md": {"Added": 1, "Changed": 1, "Misc": 1},
              "v1.2.0.md": {"Added": 1, "Fixed": 1}},
 "totals": {"Added": 4, "Fixed": 2, "Changed": 1, "Misc": 1},
 "categories": ["Added", "Changed", "Fixed", "Misc"],
 "grand_total": 8}
```

I checked both outputs by hand against the three changelog files. They match.

## SKILL.md diff

```diff
-1. List every `.md` file in `changelogs/`, sorted by version, and note the total count.
+1. Run `python3 scripts/list_changelogs.py changelogs` to list every `.md` file sorted by version with the total count. It prints JSON as `{"files": [{"file", "version"}], "count"}`.
 2. Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`. Record every file that does not.
-3. Count the entries in each file per category (`Added`, `Fixed`, `Changed`, `Removed`) and total them across files.
+3. Run `python3 scripts/count_categories.py changelogs` to count entries per category per file and across files. It prints JSON as `{"per_file", "totals", "categories", "grand_total"}` and reports every category it finds, including unexpected tags such as `Misc`, so step 6 has the raw tags to judge.
```

Steps 2 and 4 through 7 are byte-identical to before. The frontmatter and the intro are unchanged.

## One thing worth knowing

The fixture already exposes two problems the workflow is meant to catch, and neither is a script
bug: `v1.2.0.md` has no `## vX.Y.Z — YYYY-MM-DD` heading, which step 2 will flag, and `v1.1.0.md`
uses a `Misc` tag, which step 6 will judge. I left both in place - they are the skill's test data,
not defects.

## Not done, on your instruction

Step 2 is the strongest remaining candidate: a `check_headings.py` would be about 20 lines and
would remove a per-file regex the model currently runs by eye. Say the word and I will add it.
