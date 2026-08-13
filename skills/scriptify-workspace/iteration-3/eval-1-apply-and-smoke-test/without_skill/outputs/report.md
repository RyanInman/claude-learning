# changelog-checker: script delegation applied

I reviewed the 7-step workflow, split it into deterministic work and judgment work,
moved the deterministic work into one script, rewrote `SKILL.md` to call it, and
smoke-tested the script against the bundled changelogs plus four edge cases.

## What I classified

| Step | Original instruction | Verdict | Where it lives now |
|---|---|---|---|
| 1 | List `.md` files sorted by version, note total count | Delegate - file listing and semver sort are mechanical | `scan_changelogs.py` -> `files[]`, `file_count` |
| 2 | Check heading `## vX.Y.Z — YYYY-MM-DD` | Delegate - it is a regex match | `scan_changelogs.py` -> `bad_headings`, `heading_problem` |
| 3 | Count entries per category and total them | Delegate - counting by hand drifts across a long file set | `scan_changelogs.py` -> `counts`, `totals`, `total_entries` |
| 4 | Write a release narrative for a non-technical reader | Keep - audience judgment, no correct output to compute | SKILL.md step 3 |
| 5 | Render summary table sorted by version descending | Delegate - deterministic rendering from the counts | `scan_changelogs.py --format table` |
| 6a | Check tags against the allowed list | Delegate - set membership | `scan_changelogs.py` -> `unknown_tags` |
| 6b | Judge whether a `Misc` entry fits another category | Keep - semantic call on the entry's meaning | SKILL.md step 4; the script only extracts the `Misc` text |
| 7 | Flag entries a reader would find confusing | Keep - reader-comprehension judgment | SKILL.md step 5 |

Step 6 was the only one that split. The script decides *which* tags are illegal;
Claude decides *where* a `Misc` entry should move.

## What I created

`scripts/scan_changelogs.py` - one script, two output modes:

- default: JSON with `file_count`, per-file `version`/`date`/`heading_ok`/`counts`/
  `misc_entries`, plus roll-ups `totals`, `total_entries`, `bad_headings`,
  `unknown_tags`, `misc_entries`.
- `--format table`: the markdown summary table, versions descending, with a totals row.

It takes the folder as an optional argument (default `changelogs`) and exits 2 if
that path is not a directory.

## Verification

All commands run from `workspace/changelog-checker/`.

| Check | Command | Result |
|---|---|---|
| JSON on the real fixtures | `python3 scripts/scan_changelogs.py changelogs` | exit 0; 3 files, 8 entries, `v1.2.0.md` flagged for its missing heading, the one `Misc` entry extracted |
| Table on the real fixtures | `python3 scripts/scan_changelogs.py changelogs --format table` | exit 0; rows descending v1.2.0 -> v1.0.0, totals row matches the JSON |
| Empty folder | `... scratch/edge/empty --format table` | exit 0; header plus a zero totals row, no crash |
| Hyphen heading, `*` bullets, unknown `### Security` tag, zero-byte file | `... scratch/edge/weird` | exit 0; both files in `bad_headings`, `Security` in `unknown_tags`, `* Legacy API` counted under `Removed` |
| Missing folder | `... scratch/edge/nope` | exit 2 with `error: not a directory: ...` |

The counts the script produced on the fixtures:

| Version | Date | Added | Fixed | Changed | Removed | Misc | Total |
|---|---|---|---|---|---|---|---|
| v1.2.0 | (missing) | 1 | 1 | 0 | 0 | 0 | 2 |
| v1.1.0 | 2026-03-02 | 1 | 0 | 1 | 0 | 1 | 3 |
| v1.0.0 | 2026-01-15 | 2 | 1 | 0 | 0 | 0 | 3 |
| **Total** | — | 4 | 2 | 1 | 0 | 1 | **8** |

I checked these against the three files by hand: v1.0.0 has 2 Added and 1 Fixed,
v1.1.0 has 1 Added, 1 Changed, 1 Misc, and v1.2.0 has 1 Added and 1 Fixed with no
version heading. The script agrees.

## Decisions worth knowing

- **One script, not five.** Every deterministic step reads the same parse of the
  same files. Five scripts would parse the folder five times and could disagree
  with each other.
- **The heading check requires the em dash** the original spec wrote. A hyphen is
  reported as a heading problem rather than silently accepted, so the check keeps
  the meaning step 2 had. `heading_problem` quotes the offending line, so the
  distinction between "wrong dash" and "no heading" survives into the report.
- **Entries under an unknown tag are counted nowhere.** They surface in
  `unknown_tags` instead. I documented this in the gotchas, because a row total
  can then be lower than the bullets you can see in the file.
- **`Misc` text is extracted, not judged.** The script hands Claude the entry
  strings; the recategorization call stays in the workflow.

## Residual risk

The script trusts the filename for a version when the heading is missing
(`v1.2.0.md` -> `v1.2.0`). If a file is named after something other than its
version, the table row will carry the filename's version. Nothing in the fixture
set trips this.
