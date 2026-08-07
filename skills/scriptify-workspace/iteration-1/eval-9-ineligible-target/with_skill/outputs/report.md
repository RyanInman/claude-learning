# scriptify run — release-notes

## Step 0 — Target and eligibility

Target as given:
`workspace/.claude-personal/plugins/cache/release-tools/skills/release-notes`

| Eligibility condition | Result |
|---|---|
| SKILL.md present | yes |
| writable | yes (`-rw-r--r--`) |
| user-owned | yes (`admin`) |
| **outside every plugin cache path** | **NO — path contains `.claude-personal/plugins/cache/`** |

**Verdict: INELIGIBLE for writes.** Anything written there is silently
clobbered by the next plugin update. Per Step 0 the run went report-only
through Steps 1-3, and the Step 4 gate did not open on that path.

`git status` on the target: untracked in the repo (`??`), no uncommitted
modifications to warn about. Restore point taken at
`scratch/.delegation-review/SKILL.md.orig`.

The ineligibility offer (Step 0) and the two Step 4 gate questions were
answered unattended; see `gate.md`. Choices: copy into the project and continue
(the user's "apply whatever delegations you find" answers it), apply all 5
rows, keep no residue.

Copy destination: `workspace/.claude/skills/release-notes/`.
The plugin-cache original is byte-identical to its pre-run state — verified
with `diff` after the run.

## Step 1 — Inventory (`scripts/inventory.py`, exit 0)

    inventory: .../release-notes
    steps: 5  existing scripts: 0  references: 0  body: ~139 tokens
      s1 numbered-list L12-13 ~21tok verbs=count,sort,list tools=-
      s2 numbered-list L14-15 ~26tok verbs=check tools=-
      s3 numbered-list L16-17 ~23tok verbs=count tools=-
      s4 numbered-list L18-19 ~21tok verbs=- tools=-
      s5 numbered-list L20-21 ~24tok verbs=sort,render,list tools=-

Run with `--no-probe`: the target is code the user did not write (plugin
cache), and it ships no scripts to probe anyway.

## Steps 2-3 — Classification report (`scripts/render_report.py`, exit 0)

## Delegation review: release-notes

**Verdict:** 5 of 5 steps are mechanical (SCRIPT/HYBRID); delegating them removes ~115 tokens of per-run reasoning.

| # | Step (line) | Current form | Tokens | Class | Why | Proposed script interface |
|---|-------------|--------------|--------|-------|-----|---------------------------|
| s1 | "List every `.md` file in `notes/`, sorted by filename, and note the total" (L12-13) | numbered-list | 21 | SCRIPT | glob + lexical sort + count is a pure function of notes/; runs must not differ | `python3 scripts/scan_notes.py notes/ --json` -> {"files":[sorted names],"total":N,"invalid":[...],"groups":{type:[entries]},"counts":{type:N}}, exit 0 clean / 1 invalid headers found / 2 usage |
| s2 | "Check that each file starts with a line of the form `PR #<number>:`. Record" (L14-15) | numbered-list | 26 | SCRIPT | fixed regex check `^PR #<number>:` against every file, same rule every run | `python3 scripts/scan_notes.py notes/ --json` -> files failing the header pattern come back under `invalid`, exit 0 clean / 1 invalid headers found / 2 usage |
| s3 | "Group the entries by their `type:` field (`feat`, `fix`, `chore`) and count" (L16-17) | numbered-list | 23 | SCRIPT | parse `type:` field, bucket, tally; deterministic aggregation | `python3 scripts/scan_notes.py notes/ --json` -> `groups` maps feat/fix/chore to entries, `counts` to tallies, exit 0 clean / 1 invalid headers found / 2 usage |
| s4 | "Write a two-sentence summary of the release for the customer-facing" (L18-19) | numbered-list | 21 | HYBRID | customer-facing narrative is judgment: reasonable runs should word it differently. Script cannot write it, but can lint the mechanical constraint (exactly two sentences, non-empty, no raw PR numbers) that prose re-derives every run | `python3 scripts/check_summary.py .delegation-review/summary.txt --json` -> {"sentences":N,"chars":N,"findings":[...]}, exit 0 clean / 1 findings / 2 usage |
| s5 | "Render the final notes as a markdown list, grouped by type, sorted by PR" (L20-21) | numbered-list | 24 | SCRIPT | fixed markdown template driven by scan output; grouping + numeric sort by PR number is mechanical | `python3 scripts/render_notes.py notes/ --summary-file .delegation-review/summary.txt` -> final release-notes markdown, grouped by type, PR numbers ascending, exit 0 rendered / 1 no valid entries to render / 2 usage |

No DEAD and no ALREADY_DELEGATED steps. The skill shipped zero scripts.

## Steps 5-7 — Contract, implementation, smoke test

Fixtures and the manifest were written before any script existed, from the
prose semantics of each step. Ordering is genuinely asserted: one fixture's
filename order (`a-pr-110.md`, `b-pr-99.md`) deliberately disagrees with its
PR-number order.

Three scripts written into `workspace/.claude/skills/release-notes/scripts/`:

| Script | Covers | Interface |
|---|---|---|
| `scan_notes.py` | s1, s2, s3 | `python3 scripts/scan_notes.py notes/ --json` -> `total`, `files`, `invalid`, `unknown_type`, `counts`, `groups`. Exit 0/1/2 |
| `check_summary.py` | s4 (mechanical half) | `python3 scripts/check_summary.py summary.txt --json` -> `sentences`, `chars`, `findings`. Exit 0/1/2 |
| `render_notes.py` | s5 | `python3 scripts/render_notes.py notes/ --summary-file summary.txt` -> markdown. Exit 0/1/2 |

`render_notes.py` imports `scan_notes.py`, so the header rule and the grouping
live in one place.

Smoke test (`scripts/smoke_test.py`, exit 0):

    PASS  scripts/scan_notes.py  exists
    PASS  scripts/scan_notes.py  help
    PASS  scripts/scan_notes.py  fixture-run[0]
    PASS  scripts/scan_notes.py  fixture-run[1]
    PASS  scripts/scan_notes.py  bad-data
    PASS  scripts/scan_notes.py  bad-args
    PASS  scripts/check_summary.py  exists
    PASS  scripts/check_summary.py  help
    PASS  scripts/check_summary.py  fixture-run[0]
    PASS  scripts/check_summary.py  bad-data
    PASS  scripts/check_summary.py  bad-args
    PASS  scripts/render_notes.py  exists
    PASS  scripts/render_notes.py  help
    PASS  scripts/render_notes.py  fixture-run[0]
    PASS  scripts/render_notes.py  fixture-run[1]
    PASS  scripts/render_notes.py  fixture-run[2]
    PASS  scripts/render_notes.py  bad-data
    PASS  scripts/render_notes.py  bad-args

    18/18 checks passed

No expectation was changed. Every script was built to pass the manifest written
before it.

## Step 8 — SKILL.md diff (the project copy only)

    --- scratch/.delegation-review/SKILL.md.orig
    +++ workspace/.claude/skills/release-notes/SKILL.md
    @@ -9,13 +9,19 @@

     ## Workflow

    -1. List every `.md` file in `notes/`, sorted by filename, and note the total
    -   count.
    -2. Check that each file starts with a line of the form `PR #<number>:`. Record
    -   every file that does not.
    -3. Group the entries by their `type:` field (`feat`, `fix`, `chore`) and count
    -   each group.
    -4. Write a two-sentence summary of the release for the customer-facing
    -   changelog.
    -5. Render the final notes as a markdown list, grouped by type, sorted by PR
    -   number ascending.
    +1. Run exactly: `python3 scripts/scan_notes.py notes/ --json`
    +   Stdout carries the total count and the filenames sorted by filename, the
    +   files whose first line is not of the form `PR #<number>:` under `invalid`,
    +   and the per-type (`feat`, `fix`, `chore`) grouping and tallies under
    +   `groups` and `counts`. Exit 0 clean, 1 findings, 2 usage error.
    +   Exit 1 -> show the user every entry under `invalid` and `unknown_type`
    +   before going on; each names the file and the reason.
    +2. Write a two-sentence summary of the release for the customer-facing
    +   changelog, from the `counts` and `groups` of step 1. Save it to
    +   `summary.txt` in the working directory, then run exactly:
    +   `python3 scripts/check_summary.py summary.txt --json`
    +   Exit 1 -> revise the draft for every code under `findings`, then re-run.
    +3. Run exactly:
    +   `python3 scripts/render_notes.py notes/ --summary-file summary.txt`
    +   Stdout is the final notes: a markdown list grouped by type, sorted by PR
    +   number ascending. Exit 1 -> no valid entries; return to step 1's findings.

Original steps 1-3 collapse into one numbered step because a single scan pass
answers all three; their three concerns (count and filename sort, header check,
per-type grouping and tally) are each still named in the step's prose. The
frontmatter, title, and intent sentence are untouched.

## Verification on the skill's own notes/

    $ python3 scripts/scan_notes.py notes/ --json      # exit 1
    "total": 3, "invalid": [{"file": "pr-104.md", "reason": "missing_pr_header"}]
    "counts": {"feat": 1, "fix": 0, "chore": 1}

    $ python3 scripts/check_summary.py summary.txt --json   # exit 0, findings []

    $ python3 scripts/render_notes.py notes/ --summary-file summary.txt   # exit 0
    render_notes: skipped pr-104.md (missing_pr_header)      [stderr]

    This release adds batch widget creation for the widgets API. Routine dependency maintenance is also included.

    ### feat
    - #101 Add widget batch endpoint

    ### chore
    - #109 Bump lockfile

`pr-104.md` starts with `Merged 104:`, so step 2's rule correctly catches it —
the delegation reproduces the behaviour the prose asked for.

## Step 9 — Wrap up

- **Scripts written:** `scan_notes.py`, `check_summary.py`, `render_notes.py`,
  all under `workspace/.claude/skills/release-notes/scripts/`.
- **Diff:** shown above; the copy's SKILL.md is now a thin orchestrator, 5
  prose steps -> 3 exact invocations with exit-code branching.
- **Smoke:** 18/18 checks passed, exit 0.
- **DEAD steps:** none flagged.
- **Residue:** none kept; `scratch/.delegation-review/` removed after the fully
  green run, per the recommended default.
- **Untouched:** the plugin-cache copy at
  `workspace/.claude-personal/plugins/cache/release-tools/skills/release-notes`
  is byte-identical to its pre-run state.

Follow-ups worth running: `skillit:review` on the copied skill, as the scriptify
skill itself recommends, and a decision on how the project copy relates to the
plugin-provided one — two skills named `release-notes` can now both resolve.
