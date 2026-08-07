## Delegation review: changelog-checker

**Verdict:** 6 of 7 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~181 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "List every `.md` file in `changelogs/`, sorted by version, and note the total co" (L12-12) | numbered-list | 21 | SCRIPT | file discovery plus a semver sort plus a count; a function of the folder contents, same answer every run | `python3 scripts/list_changelogs.py changelogs/ --json` -> {"files": [{"path", "version"}], "count": N} sorted by version, exit 0 files found / 1 no .md files or unparseable version / 2 usage |
| s2 | "Check that each file starts with a heading of the form `## vX.Y.Z — YYYY-MM-DD`." (L13-13) | numbered-list | 29 | SCRIPT | fixed-rule regex validation of one heading pattern; unit-testable now, runs should never differ | `python3 scripts/check_headings.py changelogs/ --json` -> {"findings": [{"file", "first_line", "reason"}]}, exit 0 clean / 1 findings / 2 usage |
| s3 | "Count the entries in each file per category (`Added`, `Fixed`, `Changed`, `Remov" (L14-14) | numbered-list | 29 | SCRIPT | per-category tally and totals; pure aggregation over parsed entries | `python3 scripts/count_entries.py changelogs/ --json` -> {"per_file": {file: {category: n}}, "totals": {category: n}}, exit 0 counted / 1 no parseable entries / 2 usage |
| s4 | "Write a one-paragraph release narrative summarizing the overall direction of the" (L15-15) | numbered-list | 29 | CLAUDE | the narrative must read the meaning of the changes and pitch it at a non-technical audience; two reasonable runs should word and frame it differently. Its only mechanical inputs, the counts and the table, already come from count_entries.py and render_summary.py, so no mechanical shell is left to strip | - |
| s5 | "Render a summary table of versions, dates, and per-category entry counts, sorted" (L16-16) | numbered-list | 26 | SCRIPT | report rendering from structured data: fixed columns, fixed sort, fixed markdown template | `python3 scripts/render_summary.py .changelog-check/counts.json` -> markdown table of version, date, per-category counts, sorted by version descending, exit 0 rendered / 1 counts JSON invalid / 2 usage |
| s6 | "Check every entry's category tag against the allowed list (`Added`, `Fixed`, `Ch" (L17-17) | numbered-list | 54 | HYBRID | the allowed-list check is mechanical and the Misc re-categorization is contextual; script validates every tag and isolates the Misc residue, Claude judges only that residue | `python3 scripts/check_tags.py changelogs/ --json` -> {"invalid": [{"file", "line", "tag"}], "misc": [{"file", "line", "text"}]}, exit 0 all tags valid and no misc / 1 invalid tags or misc entries present / 2 usage |
| s7 | "Verify the entries are clearly written and flag any that a reader would find con" (L18-18) | numbered-list | 22 | HYBRID | clarity is a reader judgment no script can settle, but the enumeration and the measurable smells are mechanical; script lists every entry with length, vague-word hits, and missing-verb flags, Claude decides which are actually confusing | `python3 scripts/lint_entries.py changelogs/ --json` -> {"entries": [{"file", "line", "text", "words", "vague_terms", "starts_with_verb"}]}, exit 0 no smells flagged / 1 candidates flagged / 2 usage |

---

## Reasoning behind each class

Rubric applied: `references/delegation-rubric.md`. Core test — every step is
SCRIPT until a named judgment, conversation input, or user interaction proves
otherwise. Tie-breaks: SCRIPT over HYBRID, HYBRID over CLAUDE.

**s1 — list files sorted by version, note count → SCRIPT.**
File discovery and inventory, one of the rubric's named SCRIPT categories. The
sort is semver, not lexicographic (`v1.10.0` after `v1.2.0`), so it is more
than one moving part and earns a bundled script rather than a pinned `ls`
one-liner. Unit-testable today: given the folder, the file list and the count
are fixed.

**s2 — heading format check → SCRIPT.**
Fixed-rule validation of a single regex (`## vX.Y.Z — YYYY-MM-DD`). Two runs
should never disagree about whether a line matches. The rubric names this exact
shape as a SCRIPT example.

**s3 — per-category entry counts and totals → SCRIPT.**
Aggregation and counting. A function of the file contents with no contextual
input. Prose re-derivation here also risks arithmetic drift between runs, which
is the variance cost the skill exists to remove.

**s4 — one-paragraph release narrative → CLAUDE.**
The only pure-CLAUDE step. Its whole point is output that varies: it reads what
the changes mean and pitches them at a non-technical reader, and two reasonable
runs should word and frame it differently. HYBRID decomposition was attempted
and rejected — the script-strippable shell around a narrative is gathering the
source material and rendering the result, and both are already covered by the
s3 counts script and the s5 table script. Nothing mechanical is left to strip,
so a script here would only fake determinism over genuinely varying prose.

**s5 — summary table, sorted by version descending → SCRIPT.**
Report rendering from structured data: fixed columns, fixed sort, fixed
markdown template. Consumes s3's counts JSON so the numbers in the table and
the numbers in the tally cannot diverge.

**s6 — tag validation plus Misc re-categorization → HYBRID.**
Two halves with different natures. Checking each tag against a closed allowed
list is fixed-rule validation. Deciding whether a `Misc` entry actually belongs
under `Fixed` is contextual classification, which the rubric names verbatim as
Claude-needed. Extract-then-judge shape: the script validates every tag and
isolates the Misc residue; Claude judges only that residue and suggests moves.
Per the rubric, a step mixing mechanical and judgment work is HYBRID, never
CLAUDE.

**s7 — flag confusingly-written entries → HYBRID.**
Whether a reader finds an entry confusing is a judgment no script can settle,
so the step is not SCRIPT. But the mechanical shell is real: enumerating every
entry, and measuring the smells that correlate with confusion (entry length,
vague-term hits, whether the entry starts with a verb). Script produces that
table of candidates and facts; Claude decides which entries are actually
confusing. Script output is advisory metrics, never a verdict, so it does not
hide variance behind false authority.

## Delegation impact

- 4 SCRIPT, 2 HYBRID, 1 CLAUDE, 0 DEAD, 0 ALREADY_DELEGATED.
- 6 of 7 steps carry mechanical work; ~181 of ~242 body tokens stop being
  re-derived per run.
- The rewritten SKILL.md would read as a thin orchestrator: five exact script
  invocations, one judgment step (s4), and two run-then-judge steps (s6, s7).
- Suggested new scripts: `list_changelogs.py`, `check_headings.py`,
  `count_entries.py`, `render_summary.py`, `check_tags.py`, `lint_entries.py`.
  The target currently has no `scripts/` folder, so there are no name
  collisions and no existing interfaces to preserve.
- Output size: all six scripts emit compact JSON or one markdown table, well
  under the threshold that would need `--out`.

## Status

Report only. Nothing was written into
`workspace/changelog-checker/` — the user asked for the classification with
"Don't change anything yet". Applying the delegations (Steps 5-9 of scriptify:
fixtures and manifest, script implementation, smoke test, atomic SKILL.md
rewrite) is the follow-up, and needs an explicit pick of which rows to apply.
