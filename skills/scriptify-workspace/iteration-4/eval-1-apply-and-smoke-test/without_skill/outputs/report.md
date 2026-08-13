# Changelog Checker: script delegation

I reviewed `workspace/changelog-checker/SKILL.md`, split its seven workflow steps into
deterministic work and judgment work, moved all the deterministic work into one script, and
smoke-tested that script against the bundled changelogs plus synthetic edge cases.

## What I delegated, and what I left in prose

| Original step | Verdict | Where it lives now |
|---|---|---|
| 1. List `.md` files sorted by version, note the count | Delegate — pure enumeration | `scripts/check_changelogs.py` |
| 2. Check each file's `## vX.Y.Z — YYYY-MM-DD` heading | Delegate — a regex match | `scripts/check_changelogs.py` |
| 3. Count entries per category and total them | Delegate — counting | `scripts/check_changelogs.py` |
| 4. Write a release narrative for a non-technical reader | Keep — writing judgment | SKILL.md step 2 |
| 5. Render the summary table sorted by version descending | Delegate — formatting a computed table | `scripts/check_changelogs.py` |
| 6. Validate category tags, then judge whether `Misc` entries fit elsewhere | Split | Tag validation → script; the `Misc` judgment → SKILL.md step 3 |
| 7. Flag entries a reader would find confusing | Keep — reading comprehension | SKILL.md step 4 |

Step 6 was the only step that needed splitting. Checking a tag against a fixed allowed list is a
set membership test, so the script does it. Deciding that "Corrected typo in settings page label"
is really a `Fixed` entry depends on what the words mean, so that stays with the model. The script
prints every `Misc` entry under a "needing a judgment call" heading to hand the model exactly the
lines it must rule on.

## The script

`scripts/check_changelogs.py` — one file, no dependencies beyond the standard library.

```
usage: check_changelogs.py [-h] [folder]
```

The folder argument defaults to `changelogs`. The script prints five sections:

- **Files found** — count and names.
- **Heading format** — every file whose first non-blank line is not `## vX.Y.Z — YYYY-MM-DD`,
  with the line it found instead.
- **Summary table** — version, date, per-category counts, row total, and a totals row, sorted by
  version descending.
- **Category tags** — every `###` section whose name is outside
  `Added, Fixed, Changed, Removed, Misc`, plus the `Misc` entries the model must reclassify.
- **All entries** — every entry with its category, grouped by version, so the model can do the
  clarity pass without re-reading the files.

Implementation notes worth knowing:

- Versions sort as integer triples, not as text, so `v10.0.1` ranks above `v2.0.0`.
- A file with no valid heading still appears in the table. The script recovers the version from
  the filename and prints `missing` for the date, so a malformed file is never silently dropped.
- The heading regex accepts `-`, `–`, or `—` as the separator, because the em dash in the original
  spec is easy to type as a hyphen and rejecting the hyphen would produce noise, not signal.
- A missing folder or a folder with no `.md` files exits 1 with a message on stderr.

## Verification

Every command below was run and its exit code recorded.

**1. Bundled fixtures (`changelogs/`), exit 0.** The script found all 3 files and reported:

```
### Heading format
- v1.2.0.md: expected `## vX.Y.Z - YYYY-MM-DD`, found `### Added`

### Summary table
| Version | Date | Added | Fixed | Changed | Removed | Misc | Total |
|---|---|---|---|---|---|---|---|
| v1.2.0 | missing | 1 | 1 | 0 | 0 | 0 | 2 |
| v1.1.0 | 2026-03-02 | 1 | 0 | 1 | 0 | 1 | 3 |
| v1.0.0 | 2026-01-15 | 2 | 1 | 0 | 0 | 0 | 3 |
| **Total** | | 4 | 2 | 1 | 0 | 1 | 8 |

### Category tags
- Every section tag is in the allowed list.

Misc entries needing a judgment call:
- v1.1.0.md: Corrected typo in settings page label
```

I checked these numbers against the three files by hand: v1.0.0 has 2 Added and 1 Fixed, v1.1.0
has 1 Added, 1 Changed, and 1 Misc, and v1.2.0 has 1 Added and 1 Fixed with no heading line. The
script agrees on all of it, including catching v1.2.0.md's missing heading and surfacing the
`Misc` typo entry for reclassification.

**2. Edge cases in `scratch/edge/`, exit 0.** Two synthetic files covering the cases the fixtures
do not reach:

- `Security` as a section name → reported as outside the allowed list.
- `v10.0.1` and `v2.0.0` together → `v10.0.1` sorted first, confirming numeric rather than
  lexicographic ordering.
- An ASCII hyphen in `## v10.0.1 - 2026-07-04` → accepted, no false violation.

**3. Failure paths.** Missing folder → `error: ... is not a directory`, exit 1. Empty folder →
`error: no .md files in ...`, exit 1.

**4. Invocation forms.** Running `python3 scripts/check_changelogs.py` with no argument from the
skill root picked up `changelogs/` and produced the same output, exit 0. `--help` printed usage,
exit 0.

## Files changed

- `scripts/check_changelogs.py` — new, 147 lines.
- `SKILL.md` — the seven-step workflow became five steps: run the script, then three judgment
  steps that consume its output, then report. Added a gotchas section covering the numeric sort,
  the recovered-version behavior, and why the count must not be done by hand.

The frontmatter is unchanged. The description already covers the same triggers, and the workflow
rewrite does not change what the skill is for.

## What I did not delegate

Steps 4 and 7 are the reason this skill exists as a skill rather than as a script. Writing a
release narrative for a non-technical reader and judging whether an entry reads clearly are both
language tasks with no correct mechanical answer. Pushing them into a script would produce a
template, not a judgment. I left them in prose and pointed them at the script's output so the
model does not re-read the source files to do them.
