# Scriptify: release-notes

## Step 0 — eligibility: the target is INELIGIBLE

The skill you named lives at

    workspace/.claude-personal/plugins/cache/release-tools/skills/release-notes

That path is a plugin cache. Anything I write there is silently clobbered by the
next update of the `release-tools` plugin, so I did not write into it, and I did
not open the apply gate on it. Steps 1-3 ran report-only against it.

I skipped the `git status` check and the `.delegation-review/SKILL.md.orig`
restore point for the same reason: the restore point protects a rewrite that
this branch never performs on the original.

Transient files went to `scratch/.delegation-review/`, outside the target.

## Steps 1-2 — inventory and data

`inventory.py` found 5 numbered steps, 0 existing scripts, ~139 tokens of body.

`sample_target_data.py` digested the skill's own `notes/` directory and named
the outlier:

    notes/  3 files
      pr-101.md   PR #101: Add widget batch endpoint
      pr-104.md   Merged 104: Fix pagination off-by-one
      pr-109.md   PR #109: Bump lockfile
      shape: PR ##:
      OUTLIERS: pr-104.md

**Real finding from the target's own data:** `pr-104.md` opens with
`Merged 104:` instead of `PR #104:`, so it is exactly the file step 2 exists to
catch. Its PR number is unparseable from the header, which also means the
sorting in step 5 has to decide what to do with it. The generated scripts flag
it as `bad_header` and list it under "Needs attention" rather than dropping it.

## Step 3 — report

## Delegation review: release-notes

**Verdict:** 4 of 5 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~94 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "List every `.md` file in `notes/`, sorted by filename, and note the total" (L12-13) | numbered-list | 21 | SCRIPT | globbing notes/ and counting is a function of the directory; two runs must not differ | `python3 scripts/scan_notes.py notes/ --json` -> JSON: files sorted by name, total, entries with pr number and type, malformed list, per-type counts, exit 0 all headers valid / 1 malformed header found / 2 usage |
| s2 | "Check that each file starts with a line of the form `PR #<number>:`. Record" (L14-15) | numbered-list | 26 | SCRIPT | fixed regex check ^PR #<number>: run identically every time; pr-104.md already fails it | `python3 scripts/scan_notes.py notes/ --json` -> JSON: files sorted by name, total, entries with pr number and type, malformed list, per-type counts, exit 0 all headers valid / 1 malformed header found / 2 usage |
| s3 | "Group the entries by their `type:` field (`feat`, `fix`, `chore`) and count" (L16-17) | numbered-list | 23 | SCRIPT | grouping by a literal type: field and tallying is aggregation, no judgment | `python3 scripts/scan_notes.py notes/ --json` -> JSON: files sorted by name, total, entries with pr number and type, malformed list, per-type counts, exit 0 all headers valid / 1 malformed header found / 2 usage |
| s4 | "Write a two-sentence summary of the release for the customer-facing" (L18-19) | numbered-list | 21 | CLAUDE | customer-facing narrative; reasonable runs should word the release differently, and a script would encode one arbitrary summary | - |
| s5 | "Render the final notes as a markdown list, grouped by type, sorted by PR" (L20-21) | numbered-list | 24 | SCRIPT | fixed markdown template, grouped and sorted by rules with one right answer | `python3 scripts/render_notes.py notes/` -> markdown list grouped by type, sorted by PR number ascending, malformed files listed under Needs attention, exit 0 rendered / 1 malformed entries present / 2 usage |

No DEAD and no ALREADY_DELEGATED steps.

## The copy

You asked me to apply the delegations, and the original is unwritable in
practice, so I copied the skill into the project and applied everything to the
copy:

    workspace/.claude/skills/release-notes/

The plugin-cache original is byte-for-byte untouched. A project skill of the
same name shadows the plugin copy, so the delegated version is the one that
runs. If `release-tools` later ships its own update to this skill, reconcile the
two by hand.

## Steps 5-6 — contract and scripts

Two scripts, both in `workspace/.claude/skills/release-notes/scripts/`:

- `scan_notes.py <notes-dir> [--json] [--out FILE]` — covers s1, s2, s3. Prints
  `files`, `total`, `entries`, `counts`, and `findings`. Exit 0 clean, 1
  findings, 2 usage or unreadable input.
- `render_notes.py <notes-dir> [--out FILE]` — covers s5. Imports
  `scan_notes.scan`, so the two cannot disagree about what a valid note is.
  Exit 0 rendered clean, 1 rendered with flagged files, 2 usage.

Two finding codes, one per condition actually tested, each with its own fixture:
`bad_header` (first line is not `PR #<number>: <title>`) and `missing_type` (no
`type:` line anywhere). They are separate because a file can have a perfect
header and still be ungroupable, and one collapsed code would mislabel it.

## Step 7 — smoke test: green

    PASS  scripts/scan_notes.py  exists
    PASS  scripts/scan_notes.py  help
    PASS  scripts/scan_notes.py  fixture-run[0]
    PASS  scripts/scan_notes.py  fixture-run[1]
    PASS  scripts/scan_notes.py  bad-data
    PASS  scripts/scan_notes.py  bad-args
    PASS  scripts/scan_notes.py  codes-distinct
    PASS  scripts/render_notes.py  exists
    PASS  scripts/render_notes.py  help
    PASS  scripts/render_notes.py  fixture-run[0]
    PASS  scripts/render_notes.py  bad-data
    PASS  scripts/render_notes.py  bad-args
    PASS  scripts/render_notes.py  codes-distinct

    13/13 checks passed

Against the skill's real `notes/`, `scan_notes.py` exits 1 with one finding
(`pr-104.md`, `bad_header`) and `render_notes.py` exits 1 and prints:

    # Release notes

    ### feat
    - #101 Add widget batch endpoint

    ### chore
    - #109 Bump lockfile

    ## Needs attention
    - pr-104.md: bad_header (first line is 'Merged 104: Fix pagination off-by-one')

## Step 8 — SKILL.md diff (on the copy)

    --- workspace/.claude-personal/plugins/cache/release-tools/skills/release-notes/SKILL.md
    +++ workspace/.claude/skills/release-notes/SKILL.md
    @@ -9,13 +9,17 @@

     ## Workflow

    -1. List every `.md` file in `notes/`, sorted by filename, and note the total
    -   count.
    -2. Check that each file starts with a line of the form `PR #<number>:`. Record
    -   every file that does not.
    -3. Group the entries by their `type:` field (`feat`, `fix`, `chore`) and count
    -   each group.
    -4. Write a two-sentence summary of the release for the customer-facing
    -   changelog.
    -5. Render the final notes as a markdown list, grouped by type, sorted by PR
    -   number ascending.
    +1. Run exactly: `python3 scripts/scan_notes.py notes/ --json`
    +   One run covers steps 1 to 3: `files` and `total` are the sorted listing and
    +   the count, `findings` holds every header and `type:` problem, and `counts`
    +   holds the per-type tallies. Exit 0 clean, 1 findings, 2 usage error.
    +2. Findings present (exit 1) → report each one by file and code before going
    +   on. `bad_header` means the first line is not `PR #<number>: <title>`;
    +   `missing_type` means the file carries no `type:` line. A flagged file is
    +   left out of the grouped list in step 4.
    +3. Write a two-sentence summary of the release for the customer-facing
    +   changelog, using the `counts` and `entries` from step 1.
    +4. Run exactly: `python3 scripts/render_notes.py notes/`
    +   It prints the markdown list, grouped by type and sorted by PR number
    +   ascending, with flagged files under "Needs attention". Same exit codes as
    +   step 1.

Five prose steps became four: two exact invocations, one exit-code branch, and
the one step that stays Claude's — the customer-facing summary.

## Step 9 — wrap up

- Scripts written: `scan_notes.py`, `render_notes.py`, both under the copy's
  `scripts/`.
- Diff: shown above. Smoke: 13/13 PASS.
- DEAD steps: none.
- Residue: not kept (the default), so `scratch/.delegation-review/` is removed.
- Untouched: the plugin-cache original.

Next: run `skillit:review` on `workspace/.claude/skills/release-notes` as a
final check.
