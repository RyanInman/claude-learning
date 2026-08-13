## Delegation review: changelog-checker

**Verdict:** 4 of 7 steps become pure script invocations, plus 1 HYBRID step(s) that keep their judgment prose. Replacing the 4 SCRIPT step(s) removes ~105 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "List every `.md` file in `changelogs/`, sorted by version, and note the total co" (L12-12) | numbered-list | 21 | SCRIPT | listing .md files, sorting by semver, and counting them is a pure function of the folder contents; two runs must not differ | `python3 scripts/list_changelogs.py changelogs/ --json` -> JSON {count, files:[{file,version}]} sorted by version ascending, exit 0 files found / 1 no .md files / 2 usage |
| s2 | "Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`." (L13-13) | numbered-list | 29 | SCRIPT | fixed regex check of the first line against '## vX.Y.Z — YYYY-MM-DD'; the correct answer is decidable from the file alone | `python3 scripts/check_headings.py changelogs/ --json` -> JSON {violations:[{file,first_line,reason}]}, exit 0 clean / 1 violations found / 2 usage |
| s3 | "Count the entries in each file per category (`Added`, `Fixed`, `Changed`, `Remov" (L14-14) | numbered-list | 29 | SCRIPT | per-category tallies and cross-file totals are arithmetic over parsed headings; no judgment enters | `python3 scripts/count_entries.py changelogs/ --json` -> JSON {per_file:{file:{category:n}}, totals:{category:n}}, exit 0 counted / 1 no entries found / 2 usage |
| s4 | "Write a one-paragraph release narrative summarizing the overall direction of the" (L15-15) | numbered-list | 29 | CLAUDE | the output is a narrative for a non-technical reader; the framing, emphasis, and wording should differ between reasonable runs, and a script would encode one arbitrary phrasing | - |
| s5 | "Render a summary table of versions, dates, and per-category entry counts, sorted" (L16-16) | numbered-list | 26 | SCRIPT | a fixed markdown table sorted by version descending, rendered from the counts; report rendering from structured data is the canonical SCRIPT category | `python3 scripts/render_summary.py changelogs/` -> markdown table of version, date, per-category counts, version-descending, exit 0 rendered / 1 no parseable files / 2 usage |
| s6 | "Check every entry's category tag against the allowed list (`Added`, `Fixed`, `Ch" (L17-17) | numbered-list | 54 | HYBRID | membership in the allowed tag list is mechanical, but deciding whether a Misc entry really belongs under Fixed is contextual re-triage; the script produces the fact (which tags are illegal, and the text of every Misc entry) that the judgment consumes, so Claude reads only the residue instead of every entry | `python3 scripts/check_categories.py changelogs/ --json` -> JSON {illegal:[{file,tag}], misc:[{file,text}]}, exit 0 all tags allowed and no Misc / 1 illegal tags or Misc entries present / 2 usage |
| s7 | "Verify the entries are clearly written and flag any that a reader would find con" (L18-18) | numbered-list | 22 | CLAUDE | clarity is a reader judgment with no decidable rule, and a script could only list the entries Claude must read in full anyway, so it would change no decision | - |

**Working files:** `.delegation-review/` lives in `<run-dir>/scratch/`, outside the target, so the review never pollutes the skill it reviews.

**Target eligibility:** `changelog-checker/` is user-owned, writable, and outside every plugin cache path, so it is eligible to write to. `git status` reports SKILL.md as untracked (`?? .../changelog-checker/SKILL.md`) rather than modified, so there are no uncommitted edits to lose. Restore point saved to `.delegation-review/SKILL.md.orig`.

## What the target's own data already produces

`changelogs/` holds 3 files. The digest names `v1.2.0.md` as the first-line outlier, and it is a real defect, not a fixture I invented:

- `v1.2.0.md` opens with `### Added`. It carries no `## v1.2.0 — YYYY-MM-DD` heading at all, so step 2's check fails on it today, and step 5 has no date to put in the table row for v1.2.0.
- `v1.1.0.md` tags "Corrected typo in settings page label" as `Misc`. That is the one entry step 6's judgment half exists for, and it plausibly belongs under `Fixed`.
- Counted across the folder: Added 4, Fixed 2, Changed 1, Misc 1 — 8 entries in 3 files.

The `Misc` tag is why `count_entries.py` reports every category it finds instead of only the four step 3 names: a counter that silently dropped `Misc` would hide the entry step 6 is supposed to triage.

## Applied: steps 1 and 3 only

You asked for the delegations on steps 1 and 3 and nothing else. Rows s2, s5, and s6 stay reported-only, and steps 2, 4, 5, 6, 7 in the target are byte-identical to before.

**Scripts written into `changelog-checker/scripts/`:**

| Script | Backs | Interface | Exit codes |
|---|---|---|---|
| `list_changelogs.py` | step 1 | `python3 scripts/list_changelogs.py changelogs/ --json` | 0 files found / 1 `no_markdown_files` / 2 usage |
| `count_entries.py` | step 3 | `python3 scripts/count_entries.py changelogs/ --json` | 0 counted / 1 `no_entries_found` / 2 usage |

Both are stdlib-only, argv-only, support `--help` and `--out`, and print JSON to stdout with diagnostics on stderr.

**Smoke test:** 10/10 checks passed (exit 0).

    PASS  scripts/list_changelogs.py  exists
    PASS  scripts/list_changelogs.py  help
    PASS  scripts/list_changelogs.py  fixture-run[0]
    PASS  scripts/list_changelogs.py  fixture-run[1]
    PASS  scripts/list_changelogs.py  bad-args
    PASS  scripts/count_entries.py  exists
    PASS  scripts/count_entries.py  help
    PASS  scripts/count_entries.py  fixture-run[0]
    PASS  scripts/count_entries.py  fixture-run[1]
    PASS  scripts/count_entries.py  bad-args

    10/10 checks passed

Each script has a passing fixture and a failing fixture. `list_changelogs.py` must sort `v10.1.0.md` after `v2.0.0.md`, which pins semver ordering rather than lexical ordering, and it must trip `no_markdown_files` on a folder holding only a `.txt`. `count_entries.py` must total `Added 2, Fixed 1` on the good fixture and trip `no_entries_found` on a file with no `###` sections.

**Live run against your data:**

    $ python3 scripts/list_changelogs.py changelogs/ --json
    {"count": 3, "files": [{"file": "v1.0.0.md", "version": "1.0.0"}, {"file": "v1.1.0.md", "version": "1.1.0"}, {"file": "v1.2.0.md", "version": "1.2.0"}], "findings": [], "sorted_versions": ["1.0.0", "1.1.0", "1.2.0"], "unversioned": []}

    $ python3 scripts/count_entries.py changelogs/ --json
    {"entry_count": 8, "findings": [], "per_file": {"v1.0.0.md": {"Added": 2, "Fixed": 1}, "v1.1.0.md": {"Added": 1, "Changed": 1, "Misc": 1}, "v1.2.0.md": {"Added": 1, "Fixed": 1}}, "totals": {"Added": 4, "Changed": 1, "Fixed": 2, "Misc": 1}}

## SKILL.md diff

```diff
--- <run-dir>/scratch/.delegation-review/SKILL.md.orig	2026-08-12 11:31:22
+++ <run-dir>/workspace/changelog-checker/SKILL.md	2026-08-12 11:34:23
@@ -9,9 +9,11 @@
 
 ## Workflow
 
-1. List every `.md` file in `changelogs/`, sorted by version, and note the total count.
+1. Run exactly: `python3 scripts/list_changelogs.py changelogs/ --json`
+   Exit 0 files found, 1 the folder holds no `.md` file (`findings: ["no_markdown_files"]`), 2 usage error. `files` is version-sorted and `count` is the total; names carrying no version land in `unversioned`.
 2. Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`. Record every file that does not.
-3. Count the entries in each file per category (`Added`, `Fixed`, `Changed`, `Removed`) and total them across files.
+3. Run exactly: `python3 scripts/count_entries.py changelogs/ --json`
+   Exit 0 entries counted, 1 no entry in any file (`findings: ["no_entries_found"]`), 2 usage error. `per_file` holds the per-category counts and `totals` the cross-file totals; every tag found is reported, including ones outside the expected list, so step 6 can triage them.
 4. Write a one-paragraph release narrative summarizing the overall direction of the changes for a non-technical reader.
 5. Render a summary table of versions, dates, and per-category entry counts, sorted by version descending.
 6. Check every entry's category tag against the allowed list (`Added`, `Fixed`, `Changed`, `Removed`, `Misc`); for entries tagged `Misc`, judge whether they actually fit one of the other categories and suggest the move.
```

## Left on the table

Three delegable rows are unapplied, exactly as you asked:

- **s2 → `check_headings.py`** — the fixed-regex heading check. This is the row that catches `v1.2.0.md` today; step 2 still re-derives that check in prose on every run.
- **s5 → `render_summary.py`** — the version-descending markdown table.
- **s6 → `check_categories.py`** (HYBRID) — mechanical tag validation plus the `Misc` entries, leaving only the re-triage judgment to Claude.

Steps 4 (release narrative) and 7 (clarity check) stay CLAUDE by classification, not by your selection. A script for either would encode one arbitrary answer to a question that should vary, and for step 7 a script could only list the entries Claude must read in full anyway.

No DEAD steps found. Residue was not kept, so `.delegation-review/` is removed and nothing extra ships in the target. Run `skillit:review` on `changelog-checker` as a final check.
