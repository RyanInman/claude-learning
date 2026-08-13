# What I did, in order

All paths below are relative to
`/Users/admin/claude-learning/skills/scriptify-workspace/iteration-4/eval-7-keep-residue/with_skill`.
`<skill>` = `/Users/admin/claude-learning/skills/scriptify`.
The review directory lives at `scratch/.delegation-review/`, not beside the target, because the
run's working directory sits above the target and Step 0 forbids polluting the skill under review.

1. Read `RUN_INSTRUCTIONS_with_skill.md`.
2. Read `prompt.txt`, listed the eval tree, read `eval_metadata.json`. exit 0.
3. Read `<skill>/SKILL.md`.
4. Read `workspace/changelog-checker/SKILL.md` (7 numbered steps).
5. **Step 0.** `git status --porcelain workspace/changelog-checker/SKILL.md` → exit 0, file untracked,
   no uncommitted-change warning needed. Target is writable, user-owned, outside every plugin cache.
   Created `scratch/.delegation-review/`, copied the restore point to `SKILL.md.orig`.
6. **Step 1.** `python3 <skill>/scripts/inventory.py workspace/changelog-checker --out scratch/.delegation-review/inventory.json`
   → exit 0. 7 steps, 0 existing scripts, ~242 body tokens.
7. `python3 <skill>/scripts/sample_target_data.py workspace/changelog-checker` → exit 0.
   3 changelog files, shape `## v#.#.#`, OUTLIERS: `v1.2.0.md`.
8. Read `<skill>/references/delegation-rubric.md`.
9. `cat -A *.md` in `changelogs/` → **exit 1, error**: `cat: illegal option -- A` (BSD cat on macOS
   has no `-A`). Re-ran as plain `cat` at step 11 and got what I needed.
10. Read `<skill>/references/applying.md`.
11. `cat` of the three changelog files → exit 0. Confirmed two real defects: `v1.2.0.md` has no
    version heading, `v1.1.0.md` carries a `### Misc` entry.
12. Read `<skill>/references/script-conventions.md`.
13. Read `render_report.py`'s schema header and ran `new_manifest.py --help` → exit 0.
14. **Step 2.** Wrote `scratch/.delegation-review/classification.json` with python3:
    s1 SCRIPT, s2 SCRIPT, s3 SCRIPT, s4 CLAUDE, s5 SCRIPT, s6 HYBRID, s7 CLAUDE.
15. **Step 3.** `python3 <skill>/scripts/render_report.py scratch/.delegation-review/classification.json scratch/.delegation-review/inventory.json --out scratch/.delegation-review/report-table.md`
    → exit 0, valid on the first try. Wrote `scratch/.delegation-review/report-table.md`.
16. **Step 4 gate.** Cannot ask. Wrote `outputs/gate.md` with both AskUserQuestion questions
    verbatim, then obeyed the prompt: apply all 5 rows, keep residue = Yes.
17. **Step 5.** Created fixtures under `scratch/.delegation-review/fixtures/`:
    `scan_changelogs/good/`, `render_summary/good/`, `check_headings/{good,bad}/`,
    `check_tags/{good,bad}/`. The bad fixtures reproduce the target's real defects — an H3 first
    line, a Misc entry — plus the two heading conditions the real data does not cover.
18. Flattened each fixture folder (moved the `.md` files up out of a `changelogs/` subfolder), because
    `new_manifest.py` points the invocation at `<fixture>/good` itself.
19. `python3 <skill>/scripts/new_manifest.py scratch/.delegation-review/classification.json --target workspace/changelog-checker --out scratch/.delegation-review/manifest.json --fixtures scratch/.delegation-review/fixtures`
    → exit 0. 4 scripts, 6 TODOs. Also ran `keep_residue.py --help` → exit 0.
20. Filled all 6 TODOs with python3, deriving each from what the step must catch:
    `scan_changelogs` → `"file_count": 3`; `check_headings` clean → `"findings": []`, bad →
    `no_h2_first_line`; `render_summary` → two consecutive table rows, which is what proves the
    descending sort; `check_tags` clean → `"invalid": []`, bad → `misc_needs_triage`.
    Also dropped `--out scan.json` from the scan invocation, because a smoke run would have written
    that file into the target folder.
21. **Step 6.** Wrote four scripts into `workspace/changelog-checker/scripts/`:
    `scan_changelogs.py`, `check_headings.py`, `check_tags.py`, `render_summary.py`. `chmod +x`. exit 0.
    The three consumers import `parse_file`/`sorted_files`/`scan` from `scan_changelogs.py` via a
    `sys.path` insert of the script's own directory, so the parser exists once.
22. **Step 7.** `python3 <skill>/scripts/smoke_test.py scratch/.delegation-review/manifest.json`
    → exit 0, 20/20 passed on the first run. No expectation was changed.
23. Ran all four scripts against the real `changelogs/` → `check_headings` exit 1
    (`no_h2_first_line` on v1.2.0.md), `check_tags` exit 1 (`misc_needs_triage` on v1.1.0.md),
    `render_summary` exit 0, `scan_changelogs --out` exit 0.
24. Renamed `render_summary.py`'s last column from `Total` to `All entries`, because it counts Misc
    entries too and so exceeds the four category columns. Rewrote
    `workspace/changelog-checker/SKILL.md` in one pass (**Step 8**), including the
    `python3 scripts/tests/smoke_test.py scripts/tests/manifest.json` line the residue makes true.
    Showed the unified diff. exit 0.
25. Re-ran the smoke test after the column rename → 20/20, exit 0.
26. **Step 9.** `python3 <skill>/scripts/keep_residue.py workspace/changelog-checker --review-dir scratch/.delegation-review`
    → exit 0. 6 fixture paths rewritten to `{skill}/…`; 20/20 in place and 20/20 from a relocated copy.
27. Verified independently: ran the documented command from the target folder → 20/20, exit 0; and
    checked every manifest argv path — 6 resolve, 0 still point into `.delegation-review/`.
28. Deleted `workspace/changelog-checker/scripts/__pycache__/`, which my own runs created.
    Kept `scratch/.delegation-review/` (inventory, classification, report table, restore point),
    because it sits in `scratch/`, not in the target.

# Files created or rewritten

Created:
- `workspace/changelog-checker/scripts/scan_changelogs.py`
- `workspace/changelog-checker/scripts/check_headings.py`
- `workspace/changelog-checker/scripts/check_tags.py`
- `workspace/changelog-checker/scripts/render_summary.py`
- `workspace/changelog-checker/scripts/tests/manifest.json`
- `workspace/changelog-checker/scripts/tests/smoke_test.py` (vendored by keep_residue.py)
- `workspace/changelog-checker/scripts/tests/fixtures/` (16 fixture files across 4 scripts)
- `scratch/.delegation-review/{SKILL.md.orig,inventory.json,classification.json,report-table.md,manifest.json,fixtures/}`
- `outputs/{report.md,gate.md,transcript-notes.md,metrics.json}`

Rewritten:
- `workspace/changelog-checker/SKILL.md`

Deleted:
- `workspace/changelog-checker/scripts/__pycache__/` (created by my own script runs)
