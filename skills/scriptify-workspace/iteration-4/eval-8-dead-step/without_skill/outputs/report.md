# Which steps in `api-docs-checker` should be scripts

I read `SKILL.md` and all three files under `endpoints/`. Nothing was changed.

## Verdict per step

| Step | What it does | Verdict |
|------|--------------|---------|
| 1 | List every `.md` in `endpoints/` sorted by path, note the count | **Script** — pure file enumeration |
| 2 | Check every file has `summary:` | **Delete** — step 3 already checks `summary:`; this is a duplicate pass |
| 3 | Check every file has `summary:` and `description:`, record which is missing where | **Script** — deterministic frontmatter parse |
| 4 | Append the endpoint list to `legacy/index.txt` | **Delete — dead step.** Do not script it |
| 5 | Judge whether each `description:` reads clearly for an outside developer | **Keep in the model** — this is the judgment the skill exists for |

Net: steps 1, 2, and 3 collapse into **one** script. Step 4 goes away. Step 5 stays prose.

## Why each verdict

**Steps 1–3 are one script, not three.** They all walk the same directory and parse the
same frontmatter. Splitting them makes the model re-read the tree three times and re-derive
the same answer, and a re-derived answer varies run to run. One pass over `endpoints/` can
emit the sorted list, the count, and the per-file missing-field table together.

Step 2 is also strictly contained in step 3: any file step 2 flags, step 3 flags too, with
more detail. Keeping both produces a report that lists `list-widgets.md` twice for the same
defect. Drop step 2 and let step 3's script cover it.

**Step 4 is dead and should be deleted rather than scripted.** The skill's own Notes section
says the legacy docs portal was retired in v2 and the `legacy/` output directory went with
it. I confirmed there is no `legacy/` directory in the skill folder. As written the step
either fails on a missing directory or silently creates a file nobody reads. Scripting a
dead step just makes it fail faster and more reliably — it needs removing, and the now-stale
Notes paragraph explaining the retirement goes with it.

**Step 5 must not be a script.** "Reads clearly for an external developer who has never seen
this API" is a semantic judgment with no deterministic test. A script could only approximate
it with proxies like word count or a banned-word list, which would pass a short bad
description and fail a long good one. Leave it to the model, and feed it the script's output
so it only judges files that actually have a `description:`.

## Concrete shape of the one script

`scripts/check_endpoints.py` — no arguments, run from the skill directory:

- Walk `endpoints/*.md`, sort by path.
- Parse the YAML frontmatter of each file.
- Emit JSON: total count, the sorted file list, and per file which of `summary:` /
  `description:` is missing, plus the `description:` text when present.

Against the current fixture that script returns: 3 files;
`endpoints/create-widget.md` complete; `endpoints/delete-widget.md` missing `description:`;
`endpoints/list-widgets.md` missing `summary:`. The model then does step 5 on the one
`description:` worth judging — `list-widgets.md`'s "Does the listing thing with the standard
params." fails, because "the listing thing" and "the standard params" name nothing a new
reader can look up.

## Resulting workflow

1. Run `scripts/check_endpoints.py`. It emits the file count, the sorted list, and the
   missing-field table.
2. For each file that has a `description:`, judge whether it reads clearly for an external
   developer who has never seen this API, and flag the ones that do not.
3. Report the missing fields and the flagged descriptions together.

## One thing to double-check before deleting step 4

I am going on the skill's own Notes section for the claim that the legacy portal is gone.
If any consumer still reads `legacy/index.txt` outside this repo, deleting step 4 breaks it
silently. Confirm nothing polls that path, then delete.
