# changelog-checker — script delegation report

Target: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-2/eval-1-apply-and-smoke-test/without_skill/workspace/changelog-checker/`

Operating principle applied: delegate a step to a script unless the step needs
Claude's judgment specifically. Deterministic parsing, counting, format checking,
sorting, and table rendering go to scripts. Semantic judgment stays prose.

## Classification table

| Step | What it does | Class | Script | Why |
| --- | --- | --- | --- | --- |
| 1 | List `.md` files sorted by version, note count | SCRIPT | `scripts/list_changelogs.py` | Directory glob + semver sort + count. Fully deterministic; Claude re-deriving it burns tokens and sorts `v1.10.0` wrong. |
| 2 | Check each file starts with `## vX.Y.Z — YYYY-MM-DD` | SCRIPT | `scripts/check_headers.py` | Exact-format check = one regex. Prose invites drift on em dash vs hyphen and on the date shape. Exits nonzero so failures cannot be glossed over. |
| 3 | Count entries per category, total across files | SCRIPT | `scripts/count_entries.py` | Pure counting. The most variance-prone thing to do by eye. |
| 4 | Write one-paragraph release narrative for a non-technical reader | PROSE | none | Open-ended writing with an audience constraint. No deterministic output exists. Kept as prose, plus one added sentence telling Claude not to restate counts. |
| 5 | Render summary table, version descending | SCRIPT | `scripts/render_table.py` | Fixed table shape over data step 3 already computes. Hand-rendered markdown tables drift run to run. |
| 6 | Check tags against the allowed list; judge whether `Misc` entries fit elsewhere | SPLIT | `scripts/check_categories.py` (mechanical half only) | Membership test against a fixed list is deterministic → script, exits nonzero on an unknown tag. Deciding that "Corrected typo in settings page label" is really `Fixed` is semantic → stays prose in SKILL.md; the script only surfaces the `MISC` candidates. |
| 7 | Flag entries a reader would find confusing | PROSE | none | "Confusing" has no mechanical definition. A script here would be a length heuristic, i.e. wrong. |

Result: 5 scripts (4 whole steps + the mechanical half of step 6); 2.5 steps stay prose.

## Reasoning per class

**Step 1 → script.** Input a directory, output a sorted list and an integer.
Version sort is a known failure mode (lexical sort puts `v1.10.0` before
`v1.2.0`). `changelog_lib.version_key_from_name` parses the numeric tuple.

**Step 2 → script.** The spec separator is an em dash (U+2014). Prose lets that
detail erode; the regex `^##\s+v(\d+)\.(\d+)\.(\d+)\s+—\s+(\d{4}-\d{2}-\d{2})\s*$`
does not. Nonzero exit makes it usable as a gate.

**Step 3 → script.** Entries are `- ` bullets under a `### Category` heading.
Counting is mechanical, and the totals must reconcile with step 5's table —
sharing one parser guarantees they do.

**Step 4 → prose.** The one genuinely generative step in the skill.

**Step 5 → script.** Columns, ordering, and divider row are fixed.
`--include-misc` covers the only real variant.

**Step 6 → split.** The step joins two different jobs with a semicolon.
"Check every entry's category tag against the allowed list" is set membership.
"Judge whether they actually fit one of the other categories" requires reading
the entry and understanding the change. The script does the first and documents
in its own docstring that it does not do the second; SKILL.md keeps the judgment
sentence, scoped to the `MISC` lines the script prints.

**Step 7 → prose.** Same reason as step 4.

## Generated files

| File | Role |
| --- | --- |
| `scripts/changelog_lib.py` | Shared parser (header regex, category/entry extraction, semver sort). Not a CLI. |
| `scripts/list_changelogs.py` | Step 1. `--json`. |
| `scripts/check_headers.py` | Step 2. `--json`. Exit 1 on any violation. |
| `scripts/count_entries.py` | Step 3. `--json`. |
| `scripts/render_table.py` | Step 5. `--include-misc`. |
| `scripts/check_categories.py` | Step 6 mechanical half. `--json`. Exit 1 on an unknown tag. |
| `scripts/manifest.json` | Step mapping, good invocations, `bad_data_invocations`, and the not-delegated steps with reasons. |

All five CLIs support `--help`.

## Smoke test — PASS

Run in full BEFORE the SKILL.md rewrite. Command log in `transcript-notes.md`.

| Check | Result |
| --- | --- |
| `--help` on all 5 CLIs | exit 0, usage printed |
| `list_changelogs.py changelogs/` | `total: 3`, versions ascending |
| `check_headers.py changelogs/` | flags `v1.2.0.md` ("first line is `### Added`"), exit 1 |
| `count_entries.py changelogs/` | Added=4 Fixed=2 Changed=1 Removed=0 Misc=1, grand total 8 |
| `render_table.py changelogs/` | 3 rows, v1.2.0 → v1.0.0, `(missing)` date on v1.2.0 |
| `check_categories.py changelogs/` | 0 unknown tags, 1 MISC (`v1.1.0.md:10`), exit 0 |
| bad data: nonexistent dir | exit 1, `error: not a directory` |
| bad data: empty `.md` | exit 1, `no non-empty first line` |
| bad data: headings with no bullets | exit 0, all counts 0 |
| bad data: `### Bogus` section | exit 1, `unknown category 'Bogus'` |

Zero failures. Rewrite proceeded on this result.

## Findings on the sample data

- `changelogs/v1.2.0.md` is missing its `## v1.2.0 — YYYY-MM-DD` heading; it
  opens with `### Added`. Real defect in the fixture, caught by the header check.
- `changelogs/v1.1.0.md:10` has one `Misc` entry, "Corrected typo in settings
  page label" — exactly the candidate step 6's prose half is meant to re-home
  (it reads as `Fixed`). The script surfaces it; it does not decide.

## SKILL.md rewrite

Steps 1, 2, 3, 5, 6 now carry an exact `python3 scripts/<name>.py changelogs/`
command line. Steps 4 and 7 remain prose with no script. Step 6 keeps its
judgment sentence. A preamble tells Claude to run the scripts rather than
re-derive their output; a `## Scripts` section points at the manifest.
