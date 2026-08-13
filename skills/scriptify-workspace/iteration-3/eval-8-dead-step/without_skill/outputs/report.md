# api-docs-checker: which steps should be scripts

I read `SKILL.md` and all three files under `endpoints/`. Verdict per step:

| # | Step | Verdict |
|---|------|---------|
| 1 | List every `.md` in `endpoints/`, sorted, with a count | **Script** |
| 2 | Check every file has `summary:` | **Delete** — step 3 already does this |
| 3 | Check every file has `summary:` and `description:`, record which is missing | **Script** (merge with step 1) |
| 4 | Append the endpoint list to `legacy/index.txt` | **Delete** — dead step |
| 5 | Judge whether each `description:` reads clearly for an external developer | **Keep as prose** |

## Why

**Steps 1 and 3 -> one script.** Both are pure file mechanics: walk `endpoints/*.md`, parse
the frontmatter, test for two keys, count. There is no judgment anywhere in them, and a model
re-deriving the answer by reading files can miscount or skip a file on a large docs tree. A
script returns the same table every run. Make it one script, not two — the walk that produces
the sorted list is the same walk that checks the fields, so splitting it means reading every
file twice.

Suggested contract: `scripts/check_frontmatter.py` prints the sorted file list, the total count,
and one line per file naming any missing field. Emit JSON so step 5 can consume the
`description:` values directly instead of re-reading the files.

**Step 2 is redundant.** Step 3 checks `summary:` *and* `description:`, so it is a strict
superset of step 2. Running both makes the skill read every file twice and report the same
missing-`summary:` finding twice. Fold step 2 into step 3 and drop it.

**Step 4 is dead — do not script it.** The Notes section of the skill says the legacy docs
portal was retired in v2 and the `legacy/` output directory went with it. I checked: there is
no `legacy/` directory in the skill folder. Scripting this step would make a permanent tool
out of a write to a path that does not exist and has no consumer. It should be deleted, along
with the Notes paragraph that explains its absence — once the step is gone the explanation has
nothing to attach to.

**Step 5 stays prose.** "Reads clearly for an external developer who has never seen this API"
is exactly the judgment a script cannot make. Keep it in `SKILL.md` and let it run on the
`description:` values the step 1/3 script already extracted.

## What the script would find today

Running the checks by hand against the current fixture:

- 3 endpoint files: `endpoints/create-widget.md`, `endpoints/delete-widget.md`,
  `endpoints/list-widgets.md`
- `list-widgets.md` — missing `summary:`
- `delete-widget.md` — missing `description:`
- `create-widget.md` — complete

And step 5's judgment call: `list-widgets.md`'s description, "Does the listing thing with the
standard params.", names neither the resource nor the params, so an external developer learns
nothing from it. Flag it.

## Net effect

The workflow drops from 5 steps to 3: one script call, then one judgment step, then the report.
`SKILL.md` loses steps 2 and 4 and the Notes paragraph.

I have not changed anything. Tell me which of these you want applied.
