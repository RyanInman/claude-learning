# Scriptify: release-notes

## Headline

The delegation analysis is done and the scripts are written and tested. Nothing
was applied in place, because the target is a **plugin cache directory**, not an
editable source tree. Edits there are overwritten by the next plugin update.

Everything is staged in `outputs/proposed/`, ready to copy into the
`release-tools` plugin source. See `outputs/gate.md` for the decision.

## Why the target is ineligible for in-place edits

```
workspace/.claude-personal/plugins/cache/release-tools/skills/release-notes
                          ^^^^^^^^^^^^^
```

`plugins/cache/<plugin>/` is managed by Claude Code. It is populated from a
marketplace git repo and pinned to a version and commit SHA, then re-synced or
replaced on update, reinstall, or version bump. Anything written there is not
tracked by the user and vanishes silently.

Verified against the real layout on this machine,
`/Users/admin/.claude/plugins/installed_plugins.json`:

```json
"superpowers@claude-plugins-official": [
  {
    "scope": "user",
    "installPath": "/Users/admin/.claude/plugins/cache/claude-plugins-official/superpowers/6.2.0",
    "version": "6.2.0",
    "gitCommitSha": "c4bbe651cb1bc5e7bec6f7effae2b946571f3258"
  }
]
```

Two more signals that this checkout is not a source of truth:

- No `.claude-plugin/plugin.json`, no `marketplace.json`, no `.git` anywhere in
  the workspace. The cache holds the skill and nothing else.
- The version-pinned path shape means a version bump creates a *new* directory.
  Edits to the old one are not even overwritten, they are simply orphaned.

The skill content itself is fully eligible. The blocker is location only.

## Delegation analysis

The original workflow, five prose steps, re-derived on every run:

| # | Step | Verdict | Reason |
|---|------|---------|--------|
| 1 | List `.md` files sorted, count them | **Script** | Directory enumeration and sort. Zero judgment. |
| 2 | Validate each file starts with `PR #<number>:` | **Script** | Fixed regex. Prose validation drifts on edge cases. |
| 3 | Group by `type:`, count each group | **Script** | Parse and tally. Counting in prose is where models miscount. |
| 4 | Write a two-sentence customer summary | **Keep with Claude** | Genuine prose judgment. Not mechanical. |
| 5 | Render markdown, grouped by type, sorted by PR number asc | **Script** | Deterministic formatting and sort. |

Four of five steps are mechanical. Steps 1 to 3 are a single pass over the same
files, so they collapse into one script rather than three. Step 5 becomes a
second script. Claude's only remaining job is step 4, the part that actually
needs a model, plus deciding what to do when validation fails.

**Result: 2 scripts.**

- `scripts/collect_notes.py` (steps 1-3) enumerate, validate, extract, group.
  Emits JSON.
- `scripts/render_notes.py` (step 5) group, sort, emit markdown. Takes the JSON
  plus Claude's summary.

### What this buys

- **Correctness.** The fixture already contains a malformed note. `pr-104.md`
  starts with `Merged 104:` instead of `PR #104:`. A prose pass may or may not
  catch it on any given run. The script catches it every time, and
  `render_notes.py` refuses to render until it is fixed.
- **Determinism.** Grouping, counting, and sort order stop varying run to run.
- **Token cost.** Claude no longer reads every note file into context to count
  and sort them. It reads one JSON summary.

## Proposed files

All three are in `outputs/proposed/`, mirroring the skill folder layout.

### `SKILL.md` (rewritten)

Frontmatter `name` and `description` are unchanged, so triggering behavior is not
affected. The workflow becomes:

1. Run `collect_notes.py` into a JSON file.
2. If `invalid` is non-empty, stop and report. Do not render.
3. Write the two-sentence summary, grounded in the actual PR titles.
4. Run `render_notes.py` with the JSON and the summary.

### `scripts/collect_notes.py`

Scans the notes directory, defaults to `../notes` relative to the script, and
emits JSON:

```json
{
  "file_count": 3,
  "files": ["pr-101.md", "pr-104.md", "pr-109.md"],
  "entries": [{"file": "...", "number": 101, "title": "...", "type": "feat"}],
  "invalid": [{"file": "pr-104.md", "reason": "...", "first_line": "..."}],
  "by_type": {"feat": 1, "chore": 1},
  "unknown_types": []
}
```

Header regex is `^PR #(\d+):\s*(.+?)\s*$`. Type regex is `^type:\s*(\S+)\s*$`.
Malformed files land in `invalid` with a reason and are excluded from `entries`,
which matches the original step 2 instruction to *record* offenders rather than
abort. Exit 0 on success, 2 on a bad directory argument.

### `scripts/render_notes.py`

Takes `--data` (the JSON, or `-` for stdin) and `--summary` (a text file, or `-`).
Groups in fixed `feat`, `fix`, `chore` order with unknown types appended
alphabetically, sorts each group by PR number ascending. Refuses with exit 1 if
`invalid` is non-empty, so a malformed note cannot silently vanish from a
published changelog. The script never invents prose. The summary is passed in.

## Smoke tests run

Every script was executed against the real `notes/` fixture. All passed.

| Test | Result |
|------|--------|
| `collect_notes.py` on real fixture | Exit 0. 3 files, 2 valid entries, `pr-104.md` correctly flagged invalid. |
| `render_notes.py` with invalid present | Exit 1. `error: 1 malformed note(s): pr-104.md.` Refused to render. |
| `render_notes.py` happy path (corrected fixture) | Exit 0. Correct grouping and ascending PR sort. |
| JSON piped via stdin (`--data -`) | Exit 0. Identical output. |
| Empty notes directory | Exit 0. `file_count 0`, no crash. |
| Nonexistent directory | Exit 2. `error: not a directory: /nope` |
| Full proposed tree run from skill root | Exit 0. Default `../notes` path resolves correctly. |

Happy-path output on the corrected fixture:

```markdown
# Release Notes

This release adds batch widget creation and refreshes the dependency lockfile. No breaking changes.

## Features

- #101: Add widget batch endpoint

## Fixes

- #104: Fix pagination off-by-one

## Chores

- #109: Bump lockfile
```

## What you need to decide

Where the scriptified skill lands. Options and the default I picked are in
`outputs/gate.md`. Short version: give me the `release-tools` source repo path
and this becomes one copy command.

```bash
cp -R outputs/proposed/. <release-tools-repo>/skills/release-notes/
```

## Separate finding, not fixed

`notes/pr-104.md` is malformed. Its first line reads `Merged 104: Fix pagination
off-by-one` instead of `PR #104: Fix pagination off-by-one`. It sits in the
plugin cache alongside the skill, so it is subject to the same ineligibility and
was left untouched. If those notes are real release data rather than fixtures,
that PR is currently being dropped from the changelog.
