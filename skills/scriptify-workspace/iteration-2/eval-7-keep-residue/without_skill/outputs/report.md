# Delegation review — changelog-checker

Target: `/Users/admin/claude-learning/skills/scriptify-workspace/iteration-2/eval-7-keep-residue/without_skill/workspace/changelog-checker/`

Operating principle applied: delegate to a script unless the step needs Claude's
judgment specifically. A step is scripted when its output is fully determined by
the input files (parsing, counting, sorting, formatting, checking against a fixed
list). A step stays prose when the answer depends on meaning, audience, or taste.

## Classification table

| # | Step | Class | Script | Why |
|---|---|---|---|---|
| 1 | List `.md` files sorted by version, note count | script | `scripts/list_changelogs.py` | Pure directory listing plus a semver sort. Prose gets `v1.10.0` before `v1.9.0` on a bad day; a script never does. |
| 2 | Check `## vX.Y.Z — YYYY-MM-DD` header | script | `scripts/check_headings.py` | A fixed regex over a fixed format. Zero judgment. |
| 3 | Count entries per category, total across files | script | `scripts/count_entries.py` | Arithmetic over parsed sections. The classic step where run-to-run counts drift. |
| 4 | Write release narrative for a non-technical reader | **prose** | none | Requires reading intent behind the entries and choosing a register for a non-technical audience. No deterministic output exists. Left as prose deliberately. |
| 5 | Render summary table, version descending | script | `scripts/render_table.py` | Deterministic formatting of already-computed numbers. Hand-rendered tables are a top source of column drift. |
| 6 | Validate tags; judge `Misc` entries | **hybrid** | `scripts/check_tags.py` + prose | Two halves. Membership in `{Added, Fixed, Changed, Removed, Misc}` is a set check → script. Deciding whether "Corrected typo in settings page label" is really a `Fixed` is semantic → Claude, using the script's `misc` list as its worklist. |
| 7 | Verify entries are clearly written, flag confusing ones | **prose** | none | "A reader would find this confusing" is a judgment about language. A word-count or readability heuristic would be a proxy, not the check asked for. Left as prose deliberately. |

Totals: 4 fully scripted, 1 hybrid, 2 prose.

## Per-step reasoning

### 1 — list and count → script
Input: a directory. Output: an ordered file list and an integer. Both are a
function of the directory contents. The only subtlety is version ordering, which
is exactly where prose fails (lexicographic `1.10.0 < 1.9.0`). `list_changelogs.py`
sorts on the parsed `(major, minor, patch)` tuple and emits JSON so later steps
consume structure rather than re-parsing prose.

### 2 — heading check → script
The spec names the exact format, so a regex encodes it once. The script also
catches a second, cheap-to-detect defect while it is already parsing: a header
version that disagrees with the filename (`version_mismatch`). Both findings carry
the file name and a one-line detail; the skill relays them unchanged.

### 3 — entry counts → script
Counting list items under `###` sections across N files is the archetypal step
that drifts between runs. The script returns per-file counts, cross-file totals in
a stable category order, and `total_entries`, so steps 4 and 5 never recount.

### 4 — release narrative → prose (no script)
The step asks for a one-paragraph story about the *direction* of a release, aimed
at a non-technical reader. That means inferring the theme behind the entries and
choosing wording. A script could at best template "3 additions, 2 fixes", which is
the table from step 5, not a narrative. Kept in SKILL.md as prose, with a pointer
to read the entries rather than the counts.

### 5 — summary table → script
The numbers already exist after step 3; what remains is layout — fixed columns,
version-descending order, a zero in every empty cell. `render_table.py` prints the
markdown directly and SKILL.md instructs Claude to paste stdout unedited, so the
table cannot drift between runs. It exits non-zero when a row cannot be resolved
to a version and date, surfacing the malformed `v1.2.0.md` instead of silently
rendering a blank row.

### 6 — tag validation → hybrid
Splitting the step is what makes it scriptable at all. `check_tags.py` returns:
- `invalid` — sections whose tag is outside the allowed list (e.g. `Security`),
- `misc` — every entry tagged `Misc`, each with the four candidate categories.

`invalid` is a finished finding and is reported as-is. `misc` is a worklist:
SKILL.md tells Claude to judge each entry against the candidates and suggest the
move with a reason. The script never guesses the category; Claude never has to
scan files for tags.

### 7 — clarity check → prose (no script)
The question is whether a human reader would stumble. That is semantic. Any
scripted proxy (entry length, word count, jargon lists) would answer a different
question and give false confidence. Kept fully prose; SKILL.md asks for the quoted
entry plus a clearer rewrite so the output stays concrete.

## What was written

```
changelog-checker/
  SKILL.md                      rewritten: steps 1,2,3,5,6 invoke scripts; 4 and 7 stay prose
  scripts/
    changelog_lib.py            shared parser (header/section/entry regexes, semver sort)
    list_changelogs.py          step 1
    check_headings.py           step 2
    count_entries.py            step 3
    render_table.py             step 5
    check_tags.py               step 6 (mechanical half)
    tests/
      manifest.json             18 smoke cases, absolute fixture paths
      run_smoke.py              manifest runner
      fixtures/                 good / bad-data fixtures per script
```

Exit-code contract, uniform across scripts: `0` clean, `1` findings or empty
input, `2` usage error.

## Smoke test

```
cd /Users/admin/claude-learning/skills/scriptify-workspace/iteration-2/eval-7-keep-residue/without_skill/workspace/changelog-checker
python3 scripts/tests/run_smoke.py
```

Result: `ran 18 cases from .../scripts/tests/manifest.json` then `all green`, exit 0.

Fixtures and `manifest.json` were kept inside the skill at `scripts/tests/`, as
requested, so the checks can be re-run later. Every fixture path in the manifest
is absolute and points at `scripts/tests/fixtures/...`; the runner also verifies
each of those paths exists before reporting green. No scratch or review directory
is referenced by the shipped skill.

## Findings from running the scripts on the real `changelogs/`

- `check_headings` — `v1.2.0.md` has no `## vX.Y.Z — YYYY-MM-DD` header (exit 1).
- `count_entries` — 8 entries: Added 4, Fixed 2, Changed 1, Misc 1.
- `render_table` — exit 1; the `v1.2.0.md` row renders as `unknown | unknown`
  because of the missing header above.
- `check_tags` — no invalid tags; one `Misc` entry for Claude to judge,
  "Corrected typo in settings page label" in `v1.1.0.md`.
