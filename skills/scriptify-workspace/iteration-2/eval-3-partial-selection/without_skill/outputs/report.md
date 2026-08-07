# Delegation review — `changelog-checker`

Target: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-2/eval-3-partial-selection/without_skill/workspace/changelog-checker/`

Operating principle: a step goes to a script unless it needs Claude's judgment. Three classes used:

- **Script** — fully deterministic; same input always yields same output; no judgment.
- **Claude** — requires reading meaning, tone, or fit; no rule reproduces it.
- **Mixed** — a deterministic extraction/validation half plus a judgment half; the deterministic half is scriptable, the judgment half is not.

## Classification table

| # | Step | Class | Delegable | Applied | Script |
|---|------|-------|-----------|---------|--------|
| 1 | List every `.md` in `changelogs/`, sorted by version, note total count | Script | Yes | **Yes** | `scripts/list_changelogs.py` |
| 2 | Check each file starts with `## vX.Y.Z — YYYY-MM-DD`; record failures | Script | Yes | No (not selected) | — |
| 3 | Count entries per category per file and total across files | Script | Yes | **Yes** | `scripts/count_entries.py` |
| 4 | Write one-paragraph release narrative for a non-technical reader | Claude | No | No | — |
| 5 | Render summary table of versions, dates, per-category counts, desc | Script | Yes | No (not selected) | — |
| 6 | Validate category tags against allowed list; judge whether `Misc` entries belong elsewhere | Mixed | Partly | No (not selected) | — |
| 7 | Verify entries are clearly written; flag confusing ones | Claude | No | No | — |

## Reasoning per step

**Step 1 — Script.** Directory listing, semantic-version sort, and a count are pure mechanics. Prose leaves the sort ambiguous (`v1.10.0` vs `v1.2.0` sorts wrong lexically) and the count is a place Claude can miscount. Delegated.

**Step 2 — Script (not applied).** A single regex over the first line of each file: `^## v\d+\.\d+\.\d+ — \d{4}-\d{2}-\d{2}$`. Zero judgment, and the em-dash character is exactly the kind of detail a prose review misses. Genuinely delegable, but outside the requested selection, so its text is untouched.

**Step 3 — Script.** Counting list items under `###` category headings is parsing plus arithmetic. Run-to-run variance here is a known failure mode for counting in prose. Delegated.

**Step 4 — Claude.** Summarizing "the overall direction of the changes" for a non-technical reader is a writing task. No script can produce a narrative.

**Step 5 — Script (not applied).** Table rendering from data already computed in steps 1 and 3 (plus dates parsed from headings) is pure formatting; sort-descending is deterministic. Delegable, but not selected. It can consume the JSON that steps 1 and 3 now emit, so scripting it later needs no rework.

**Step 6 — Mixed (not applied).** Two halves. The membership check — is each tag in `{Added, Fixed, Changed, Removed, Misc}` — is a set lookup and belongs in a script. Deciding whether "Corrected typo in settings page label" is really a `Changed` needs semantic judgment and stays with Claude. If applied later, the split is: script emits the tag inventory and flags out-of-list tags plus every `Misc` entry; Claude reads only the flagged `Misc` entries and proposes moves.

**Step 7 — Claude.** "Would a reader find this confusing" is irreducibly a judgment call. Heuristics (length, jargon count) would be a worse proxy than reading it.

## What was applied

Only steps 1 and 3, as requested. Steps 2 and 5 are delegable and were deliberately left as prose.

### `scripts/list_changelogs.py`
`python3 scripts/list_changelogs.py [CHANGELOG_DIR] [--json]` (dir defaults to `changelogs`). Sorts by the numeric `vX.Y.Z` parsed from the filename, so `1.10.0` follows `1.9.0`. Unparseable names sort last rather than being dropped. Emits file name, path, version, and total count. Exits 1 with a message on a missing directory.

### `scripts/count_entries.py`
`python3 scripts/count_entries.py [CHANGELOG_DIR] [--json]` (dir defaults to `changelogs`). Counts top-level `-`/`*` list items under each `### Heading`. Categories `Added`, `Fixed`, `Changed`, `Removed` are counted by name; any other section rolls into `other` and is also itemized under `other_sections`, so a stray `Misc` section is surfaced rather than silently lost — that keeps step 6's judgment work possible without prejudging it. Emits per-file counts and grand totals. Exits 1 with a message on a missing directory.

## Smoke tests

All run before the SKILL.md rewrite.

| Check | Result |
|---|---|
| `list_changelogs.py changelogs` (text) | 3 files, correct version order, `total: 3` |
| `list_changelogs.py changelogs --json` | valid JSON, `count: 3` |
| `count_entries.py changelogs` (text) | table + `TOTAL 4 2 1 0 1` |
| `count_entries.py changelogs --json` | valid JSON; `v1.1.0.md` shows `other_sections: {"Misc": 1}` |
| Both scripts, empty directory | zero counts, exit 0, no crash |
| Both scripts, nonexistent directory | `error: not a directory: ...`, exit 1 |
| `--help` | renders |
| Both scripts with the relative paths as written in SKILL.md, cwd = skill root | correct output |

Counts verified by hand against the fixtures: v1.0.0 = Added 2 / Fixed 1; v1.1.0 = Added 1 / Changed 1 / Misc 1; v1.2.0 = Added 1 / Fixed 1. Totals Added 4, Fixed 2, Changed 1, Removed 0, other 1. Script output matches.

## SKILL.md diff

Two lines changed, both in place; no lines added or removed.

Line 12 (step 1), before:

    1. List every `.md` file in `changelogs/`, sorted by version, and note the total count.

after:

    1. Run `python3 scripts/list_changelogs.py changelogs --json` to get every `.md` file in `changelogs/`, sorted by version, plus the total count. Use its output as-is.

Line 14 (step 3), before:

    3. Count the entries in each file per category (`Added`, `Fixed`, `Changed`, `Removed`) and total them across files.

after:

    3. Run `python3 scripts/count_entries.py changelogs --json` to get per-file entry counts per category (`Added`, `Fixed`, `Changed`, `Removed`, plus `other`) and the totals across files. Use its output as-is.

Steps 2, 4, 5, 6, 7, the frontmatter, the title, and the intro line are byte-identical to before.
