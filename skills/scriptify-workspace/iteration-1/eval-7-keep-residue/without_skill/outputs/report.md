# changelog-checker: script delegation review + applied changes

Reviewed all 7 workflow steps, delegated every mechanical one to a script, and left the
three that need judgement in prose. Fixtures and a re-runnable check manifest stay inside
the skill, as requested.

## Delegation review

| Old step | What it did | Verdict | Now |
|---|---|---|---|
| 1 | List `.md` files sorted by version, note count | **Script** - deterministic enumeration + semver sort | `scripts/scan_changelogs.py` |
| 2 | Validate `## vX.Y.Z - YYYY-MM-DD` heading | **Script** - a regex match, and prose re-derives it differently each run | `scripts/scan_changelogs.py` |
| 3 | Count entries per category, total across files | **Script** - counting is where an LLM silently drifts | `scripts/scan_changelogs.py` |
| 4 | One-paragraph release narrative | **Keep in prose** - needs judgement about what the release *means* | SKILL.md step 3 |
| 5 | Render summary table, version descending | **Script** - pure formatting of data already computed | `scripts/render_summary.py` |
| 6a | Check tags against the allowed list | **Script** - set membership | `scripts/scan_changelogs.py` |
| 6b | Judge whether `Misc` entries fit another category | **Keep in prose** - semantic call the script cannot make | SKILL.md step 4 |
| 7 | Flag confusing entries | **Keep in prose** - subjective readability judgement | SKILL.md step 5 |

Step 6 was split: the script now surfaces every `Misc` entry with its text, so the model
only does the part that actually needs a model. The scan JSON also carries the full text
of every entry, so steps 3-5 are answered from one JSON read instead of reopening each
changelog file.

## What was added

```
changelog-checker/
  SKILL.md                      # rewritten: steps invoke scripts, judgement steps remain
  scripts/scan_changelogs.py    # enumerate, validate headings, count, flag tags -> JSON
  scripts/render_summary.py     # scan JSON -> markdown table + problem sections
  tests/manifest.json           # 8 check definitions (KEPT, as requested)
  tests/run_smoke_tests.py      # manifest runner (KEPT)
  tests/fixtures/clean/         # 2 well-formed files (KEPT)
  tests/fixtures/problems/      # bad heading + non-allowed tag + Misc entry (KEPT)
  tests/fixtures/no-heading/    # regression fixture, see bug below (KEPT)
  tests/fixtures/empty/         # no .md files, exercises the exit-2 path (KEPT)
  changelogs/                   # untouched
```

Contracts:

- `scan_changelogs.py [DIR] [-o OUT.json]` - exit `0` scanned, `2` folder missing or has
  no `.md` files.
- `render_summary.py [REPORT.json]` - reads stdin if no path; exit `0` clean, `1`
  structural problems found (listed in the output), `2` input is not a scan report.

The non-zero-means-problems-found convention on `render_summary.py` is documented in
SKILL.md so a future run does not mistake it for a crash.

## Smoke tests

All 8 checks pass:

```
PASS  scan-clean          PASS  scan-problems      PASS  scan-no-heading
PASS  scan-empty          PASS  scan-missing-dir   PASS  render-clean
PASS  render-problems     PASS  render-bad-input
8 passed, 0 failed
```

Re-run them yourself from the skill folder:

```bash
python3 tests/run_smoke_tests.py            # all
python3 tests/run_smoke_tests.py -v         # with the reason for each check
python3 tests/run_smoke_tests.py --only scan-problems
```

`--only` still runs any upstream check whose stdout a selected check consumes, so
`--only render-problems` works without naming `scan-problems`.

## Bug found and fixed while testing

The first version of the scanner treated the first non-empty line as the version heading
and started category parsing after it. For `changelogs/v1.2.0.md`, whose first line is
`### Added` (the heading is missing entirely), that swallowed the `Added` section: the
report showed `Added: 0` and orphaned "Dark mode" as an untagged entry.

Fixed by scanning every line for category sections - a `## ` version heading can never
match the `### ` category pattern, so nothing is double-counted. `tests/fixtures/no-heading/`
and the `scan-no-heading` manifest check pin the regression.

This is exactly the class of error the delegation is meant to remove: the old prose steps
would have produced that same wrong count, silently and differently on each run.

## Live run against the skill's own `changelogs/`

```
## Changelog summary (3 files, 8 entries)

| Version | Date | Added | Fixed | Changed | Removed | Misc | Total |
|---|---|---|---|---|---|---|---|
| v1.2.0 * | - | 1 | 1 | 0 | 0 | 0 | 2 |
| v1.1.0 | 2026-03-02 | 1 | 0 | 1 | 0 | 1 | 3 |
| v1.0.0 | 2026-01-15 | 2 | 1 | 0 | 0 | 0 | 3 |
| **Total** | 3 files | **4** | **2** | **1** | **0** | **1** | **8** |

`*` = heading does not match the required format.

### Heading check (1 problem(s))
- `v1.2.0.md`: first content line '### Added' is not a '## ' version heading

### Category tags outside the allowed list (0 file(s))
- Every tag is one of `Added`, `Fixed`, `Changed`, `Removed`, `Misc`.

### `Misc` entries needing a judgement call (1)
- `v1.1.0.md`: Corrected typo in settings page label
```

The judgement steps applied to that output:

**Release narrative (step 3).** Across three releases the product moved from standing up
the basics to smoothing them out. v1.0.0 delivered the core - accounts and a working
sign-in. v1.1.0 turned to getting data out and making the app feel quicker, adding CSV
export and faster search. v1.2.0 continued the polish with dark mode and a fix for a crash
on empty profiles. The arc is a young product that shipped its foundation, then spent its
next two releases on convenience and stability rather than new territory.

**`Misc` judgement (step 4).** `v1.1.0` - "Corrected typo in settings page label" should
move to `Fixed`. It repairs incorrect shipped text; `Misc` implies it fits nowhere, which
is not true here.

**Confusing entries (step 5).**

- `v1.0.0` "Initial release" - says nothing about what was released. Suggest: "First
  public release of the app."
- `v1.1.0` "Faster search indexing" - "indexing" is internal vocabulary and the entry does
  not state the user-visible effect. Suggest: "Search results now appear faster after new
  content is added."
- `v1.2.0` "Crash on empty profile" - no subject or verb, so it reads as a bug title
  rather than a change. Suggest: "Fixed a crash when opening a profile with no details
  filled in."

## Note on the fixtures

`tests/fixtures/` and `tests/manifest.json` are permanent parts of the skill, not scratch.
Nothing under the skill folder was cleaned up. Transient files from this run went to
`<run>/scratch/`. See `outputs/gate.md` for the one open decision (manifest format) and
the default chosen.
