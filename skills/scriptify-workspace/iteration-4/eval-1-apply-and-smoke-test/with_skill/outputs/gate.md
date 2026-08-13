# Step 4 gate — the questions I would have asked

I would have sent both questions below in one `AskUserQuestion` call.

## Question 1 — Which rows to apply?

header: "Apply"
question: "5 steps can be delegated (4 SCRIPT, 1 HYBRID), backed by 2 new scripts. Which rows should I apply to changelog-checker?"
multiSelect: true

| Option | Description |
|---|---|
| Apply all 5 (Recommended) | Write `scan_changelogs.py` (s1, s2, s3, s5) and `check_categories.py` (s6) into `changelog-checker/scripts/`, rewrite those steps to invoke them, and smoke-test both. |
| Apply a subset — list row ids in Other | e.g. "s1 s2 s3 s5" to take only the scan script and leave the Misc re-triage step as prose. |
| Report only, write nothing | Leave `changelog-checker/SKILL.md` untouched. |

(5 SCRIPT+HYBRID rows is more than 4, so this is the three-option form, not one option per row.)

## Question 2 — Keep verification residue?

header: "Residue"
question: "Keep the smoke-test fixtures and manifest in `changelog-checker/scripts/tests/` after the run?"

| Option | Description |
|---|---|
| No (Recommended) | Delete `.delegation-review/` once the run is green. The target keeps only the two scripts. |
| Yes | Install fixtures, manifest, and a vendored `smoke_test.py` under `scripts/tests/`, and prove the suite still passes from a relocated copy. |

## What the prompt already decided

The prompt says "apply all the delegations you find, and verify the generated scripts work."

- Question 1 → **Apply all 5** (s1, s2, s3, s5, s6).
- Question 2 → **No**, the default. The prompt asks me to verify the scripts work, which Step 7's
  smoke test does; it does not ask for the fixtures to be left behind in the target.

Target eligibility: `workspace/changelog-checker/` is user-owned, writable, and outside every plugin
cache path, so it is eligible to write to. `git status` reports it untracked rather than dirty, so
there were no uncommitted edits to warn about. The working directory is not under the target, but the
run instructions scope scratch files to `RUN_DIR/scratch/`, so `.delegation-review/` lives at
`RUN_DIR/scratch/.delegation-review/`.
