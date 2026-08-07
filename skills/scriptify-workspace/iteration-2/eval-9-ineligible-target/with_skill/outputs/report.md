# Scriptify report — release-notes (report-only)

## Eligibility (Step 0)

Target:
`/Users/admin/claude-learning/skills/scriptify-workspace/iteration-2/eval-9-ineligible-target/with_skill/workspace/.claude-personal/plugins/cache/release-tools/skills/release-notes`

**INELIGIBLE for writes.** The path sits under `.claude-personal/plugins/cache/`,
a plugin cache path SKILL.md Step 0 names explicitly. The next plugin update
silently clobbers any script written there, so nothing was written into the
target. Per Step 0, Steps 1-3 ran report-only and the Step 4 gate stayed shut.

The file is chmod-writable (`-rw-r--r--`, owned by the current user) and
untracked in git, so no uncommitted-changes warning applied. Writability is not
the disqualifier here — cache-path residence is.

## Step 1 — Inventory

    python3 <scriptify>/scripts/inventory.py <target> --out .delegation-review/inventory.json --no-probe

    steps: 5   existing scripts: 0   references: 0   body: ~139 tokens

`--no-probe` was used because the target is plugin code the user did not write;
probing would execute it. It made no difference in practice — the target ships
zero scripts.

## Step 3 — Rendered report

## Delegation review: release-notes

**Verdict:** 5 of 5 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~115 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "List every `.md` file in `notes/`, sorted by filename, and note the total" (L12-13) | numbered-list | 21 | SCRIPT | glob + sort + count; identical output for identical notes/ dir | `python3 scripts/parse_notes.py notes/ --json` -> {files:[...sorted], count:N, invalid:[...], groups:{feat:N,fix:N,chore:N}}, exit 0 all headers valid / 1 invalid headers found / 2 usage |
| s2 | "Check that each file starts with a line of the form `PR #<number>:`. Record" (L14-15) | numbered-list | 26 | SCRIPT | fixed regex check `^PR #<number>:` on line 1; no judgment | `python3 scripts/parse_notes.py notes/ --json` -> invalid[] lists every file whose first line misses `PR #<n>:`, exit 0 all headers valid / 1 invalid headers found / 2 usage |
| s3 | "Group the entries by their `type:` field (`feat`, `fix`, `chore`) and count" (L16-17) | numbered-list | 23 | SCRIPT | group by literal type: field and tally; pure aggregation | `python3 scripts/parse_notes.py notes/ --json` -> groups{} maps feat/fix/chore to counts, unknown types under groups.other, exit 0 all headers valid / 1 invalid headers found / 2 usage |
| s4 | "Write a two-sentence summary of the release for the customer-facing" (L18-19) | numbered-list | 21 | HYBRID | customer-facing narrative varies with what shipped; Claude writes it, script lints the fixed constraint (exactly two sentences, non-empty) | `python3 scripts/lint_summary.py SUMMARY_FILE --json` -> {sentences:N, findings:[...]}, exit 0 clean / 1 findings / 2 usage |
| s5 | "Render the final notes as a markdown list, grouped by type, sorted by PR" (L20-21) | numbered-list | 24 | SCRIPT | fixed markdown template, grouped by type, sorted by PR number; a unit test can pin the exact output | `python3 scripts/render_notes.py notes/ --summary SUMMARY_FILE --out RELEASE_NOTES.md` -> path written + per-group counts, exit 0 rendered / 1 unparseable note / 2 usage |

## Step 2 — Reasoning behind each class

**s1 — SCRIPT.** "List every `.md` file in `notes/`, sorted by filename, and
note the total count." File discovery plus a count. Two runs must not differ.
The unit test writes itself: given three fixture files, assert the sorted list
and `count: 3`. Nothing here resists scripting.

**s2 — SCRIPT.** "Check that each file starts with a line of the form
`PR #<number>:`." Fixed-rule validation against a literal pattern. The rubric's
"every heading matches the version pattern" example verbatim. No contextual
call about what counts as valid — the prose states the form.

**s3 — SCRIPT.** "Group the entries by their `type:` field and count each
group." Aggregation over a literal field with an enumerated value set
(`feat`, `fix`, `chore`). Types outside that set land in `groups.other` so the
script surfaces them rather than silently dropping them; noticing an unexpected
type is Claude's job, tallying is not.

s1, s2 and s3 share `parse_notes.py`. All three read the same directory and the
same per-file structure, so three scripts would parse `notes/` three times. One
script emits `files`, `count`, `invalid`, and `groups` in a single pass; each
step consumes its own field. Exit 1 signals invalid headers, which gates s3-s5
on a clean parse.

**s4 — HYBRID, not CLAUDE.** "Write a two-sentence summary of the release for
the customer-facing changelog." The narrative genuinely varies — a release of
three fixes reads differently from a release of one feature — and reasonable
runs *should* differ, which is the CLAUDE test. But the step is not judgment
all the way through. Per the rubric's prose-writing entry, the script-strippable
shell stays scripted: `parse_notes.py` already gathers the source facts
(counts per type, PR numbers), and `lint_summary.py` enforces the one hard
constraint the prose states — exactly two sentences, non-empty. Claude writes,
the script checks. That leaves the minimal judgment core.

**s5 — SCRIPT.** "Render the final notes as a markdown list, grouped by type,
sorted by PR number ascending." Report rendering from structured data with a
fixed template and a fully specified sort. Every degree of freedom is pinned
by the prose. `--out` rather than stdout because the rendered notes grow with
the release, and dumping them into context spends the tokens the script saves.

**Zero DEAD steps.** All five steps are live and non-duplicative. No
`skillit:review` follow-up is owed on that account.

**Zero ALREADY_DELEGATED steps.** The target ships no `scripts/` directory.

## Not done, and why

Steps 4-9 (gate, contract, implementation, smoke test, SKILL.md rewrite) did
not run. Writing scripts into a plugin cache is the exact failure Step 0 exists
to prevent. See `gate.md` for the offer that would have been put to the user.
