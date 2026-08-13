# Delegation review: `changelog-checker`

Target: `workspace/changelog-checker/SKILL.md` (7 workflow steps, 3 changelog files).

I reviewed all 7 steps for delegable work, then applied only the delegations for steps 1 and 3, as
you asked. Steps 2, 4, 5, 6, and 7 are untouched.

## Full review of all 7 steps

| Step | Work | Verdict | Why |
|------|------|---------|-----|
| 1 | List `.md` files sorted by version, note count | **Delegable — applied** | Pure directory read plus a semver sort. No judgment. Re-deriving it in prose risks a miscount or a lexical sort that puts `v1.10.0` before `v1.2.0`. |
| 2 | Check each file's `## vX.Y.Z — YYYY-MM-DD` heading | **Delegable — not applied** | A single regex over line 1 of each file. Deterministic, but out of the scope you set. |
| 3 | Count entries per category, total across files | **Delegable — applied** | Counting is the classic case where a model drifts. A script gives the same eight-entry total every run. |
| 4 | Write a release narrative for a non-technical reader | **Not delegable** | Requires judgment about audience and tone. A script cannot write it. |
| 5 | Render the summary table sorted by version descending | **Delegable — not applied** | Formatting is deterministic once steps 1–3 supply versions, dates, and counts. Worth revisiting after step 2 is scripted, because the table needs the dates that a step-2 script would already parse. |
| 6 | Validate category tags; judge whether `Misc` entries belong elsewhere | **Split** | The first half — checking each tag against the allowed list — is deterministic and delegable. The second half — deciding whether "Corrected typo in settings page label" is really a `Fixed` — is judgment and stays with the model. Splitting this step is the right move but it changes step 6's prose, so I left it alone. |
| 7 | Flag confusing entries | **Not delegable** | Readability is a judgment call. |

Summary: 4 fully delegable steps (1, 2, 3, 5), 1 partially delegable (6), 2 that must stay prose (4, 7).

## What I applied

Two scripts, both new:

- `scripts/list_changelogs.py <changelog_dir>` — lists `*.md` sorted by numeric semver parsed from
  the filename, then prints `total: N`. Unparseable filenames sort last by name rather than crashing.
  `--descending` is there because step 5 sorts the other way.
- `scripts/count_entries.py <changelog_dir>` — counts `-`/`*` bullets under each `###` heading, prints
  one row per file plus an `ALL` row. It reports the four canonical categories, appends any extra
  category as its own column so the totals stay honest, and names non-standard categories on stderr.

Plus `scripts/smoke_test.sh`, which exercises both scripts.

The SKILL.md diff is two lines:

```diff
-1. List every `.md` file in `changelogs/`, sorted by version, and note the total count.
+1. Run `python3 scripts/list_changelogs.py changelogs/` to list every `.md` file in `changelogs/`, sorted by version, with the total count on the last line.
 2. Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`. Record every file that does not.
-3. Count the entries in each file per category (`Added`, `Fixed`, `Changed`, `Removed`) and total them across files.
+3. Run `python3 scripts/count_entries.py changelogs/` to count the entries in each file per category (`Added`, `Fixed`, `Changed`, `Removed`) and total them across files. The script prints one row per file and an `ALL` row; it names any non-standard category on stderr.
```

No other step gained a script invocation. Step 2's line is byte-identical to before.

## Verification

`scripts/smoke_test.sh` passes against the final on-disk state (exit 0). Per script it checks
`--help` exits 0, and that no args, an unknown flag, and a missing directory each exit nonzero:

```
ok   list_changelogs.py --help (exit 0)
ok   list_changelogs.py no args (exit 2)
ok   list_changelogs.py unknown flag (exit 2)
ok   list_changelogs.py missing dir (exit 2)
ok   list_changelogs.py happy path (exit 0)
ok   count_entries.py --help (exit 0)
ok   count_entries.py no args (exit 2)
ok   count_entries.py unknown flag (exit 2)
ok   count_entries.py missing dir (exit 2)
ok   count_entries.py happy path (exit 0)
all checks passed
```

Real output against `changelogs/`:

```
$ python3 scripts/list_changelogs.py changelogs/
v1.0.0.md
v1.1.0.md
v1.2.0.md
total: 3

$ python3 scripts/count_entries.py changelogs/
file          Added     Fixed   Changed   Removed      Misc     total
---------------------------------------------------------------------
v1.0.0.md         2         1         0         0         0         3
v1.1.0.md         1         0         1         0         1         3
v1.2.0.md         1         1         0         0         0         2
---------------------------------------------------------------------
ALL               4         2         1         0         1         8
non-standard categories seen: Misc      # stderr
```

## One thing worth knowing

`changelogs/v1.2.0.md` has no `## v1.2.0 — 2026-03-…` heading at all — it opens straight at
`### Added`. That is exactly the failure step 2 exists to catch, and the model still has to catch it
by hand because you scoped step 2 out. If you later apply the step 2 delegation, that file is the
regression case to test against.

## If you want the rest

Say the word and I will script step 2 (heading validation), step 5 (table rendering, reusing the
step 2 date parse), and the deterministic half of step 6 (tag allow-list check), leaving the `Misc`
judgment call and steps 4 and 7 in prose.
