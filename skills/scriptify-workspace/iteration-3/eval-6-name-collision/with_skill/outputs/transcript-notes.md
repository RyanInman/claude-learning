# What I did, in order

RUN_DIR = /Users/admin/claude-learning/skills/scriptify-workspace/iteration-3/eval-6-name-collision/with_skill
TARGET  = $RUN_DIR/workspace/docs-linter
REVIEW  = $RUN_DIR/scratch/.delegation-review   (printed at Step 0, per SKILL.md)

## Step 0 - locate and check eligibility

1. Read RUN_INSTRUCTIONS_with_skill.md, prompt.txt.
2. Read /Users/admin/claude-learning/skills/scriptify/SKILL.md.
3. `ls -ld` + `test -w` + `stat -f %Su` on TARGET -> writable, owner admin,
   outside every plugin cache path. Eligible. exit 0
4. `git status --porcelain -- $TARGET/SKILL.md` -> `??` (untracked eval
   workspace copy, no uncommitted tracked changes to warn about). exit 0
5. `mkdir -p $REVIEW $RUN_DIR/outputs` + `cp SKILL.md $REVIEW/SKILL.md.orig`.
   exit 0. CREATED: $REVIEW/SKILL.md.orig

## Step 1 - inventory

6. `python3 scriptify/scripts/inventory.py $TARGET --out $REVIEW/inventory.json`
   exit 0 -> 4 steps (s1-s4), 1 existing script, ~128 body tokens.
   Existing-script audit: check_headings.py mentioned=False argparse=False
   help_ok=False. CREATED: $REVIEW/inventory.json
7. `python3 scriptify/scripts/sample_target_data.py $TARGET` exit 0 ->
   3 md files; outlier first lines: tutorial.md "Some intro prose..." and
   api.md "## API Reference".
8. `cat -A` on the three docs -> exit 1, `cat: illegal option -- A` (BSD cat on
   macOS has no -A). Recovered by reading each file with Read instead.
9. Read docs/getting-started.md, docs/tutorial.md, docs/reference/api.md.
10. Interface audit probe on the one existing target script:
    `python3 scripts/check_headings.py --help` -> exit 2, "not a directory: --help"
    `python3 scripts/check_headings.py docs` -> exit 1, "missing alt text:
    docs/reference/api.md". Confirms it is an alt-text checker, not a heading
    checker, so s2 is NOT already delegated and the name is NOT free.

## Step 2 - classify

11. Read scriptify/references/delegation-rubric.md.
12. `head -60 scriptify/scripts/render_report.py` exit 0, for the exact schema.
13. CREATED: $REVIEW/classification.json
    s1 SCRIPT, s2 SCRIPT, s3 SCRIPT (all -> lint_docs.py), s4 CLAUDE.

## Step 3 - render

14. `python3 scriptify/scripts/render_report.py $REVIEW/classification.json
    $REVIEW/inventory.json --out $REVIEW/report-table.md` exit 0.
    CREATED: $REVIEW/report-table.md

## Step 4 - gate (non-interactive)

15. CREATED: outputs/gate.md - the two AskUserQuestion questions verbatim, plus
    the Step 6 name-collision question. prompt.txt says "apply all", so all
    three SCRIPT rows are selected; residue takes its recommended default (No);
    the collision takes its recommended default (new name, never overwrite).

## Step 5 - contract first

16. `python3 scriptify/scripts/new_manifest.py --help` exit 0 (read the help
    rather than the ~500 lines of new_manifest.py + smoke_test.py, per
    applying.md).
17. CREATED fixtures under $REVIEW/fixtures/lint_docs/ - exit 0:
      good/intro.md, good/guide.md               (clean; 1 fenced block total)
      bad/h1_not_first/tut.md                    (prose line 1, H1 line 3)
      bad/no_h1/api.md                           (## only, no H1 anywhere)
      bad/missing_blank/x.md                     (H1 then text on line 2)
      bad/empty/empty.md                         (zero bytes)
18. `python3 scriptify/scripts/new_manifest.py $REVIEW/classification.json
    --target $TARGET --out $REVIEW/manifest.json --fixtures $REVIEW/fixtures`
    exit 0 -> 1 script, kind=check, 2 TODOs.
19. REWROTE: $REVIEW/manifest.json - filled both TODOs and added one invocation
    per finding code, so each code has its own fixture and its own asserted
    string.

## Step 6 - implement

20. Read scriptify/references/script-conventions.md.
21. CREATED: $TARGET/scripts/lint_docs.py (argparse, --help, --out, exit 0/1/2,
    header docstring, stdlib only). Named lint_docs.py, NOT check_headings.py -
    that path is occupied by the alt-text checker the release pipeline calls.
    scripts/check_headings.py was never opened for writing; md5 unchanged
    (f39b9fc885e0c93eb84e34a3d3ae9aac).

## Step 7 - smoke test

22. `python3 scriptify/scripts/smoke_test.py $REVIEW/manifest.json` exit 0,
    11/11 checks passed. Green on the first run; no expectation was changed.
23. `python3 scripts/lint_docs.py docs/ --json` against the real target tree
    exit 1 -> api.md no_h1, tutorial.md h1_not_first, fenced_blocks_total 4.
24. A stray verification command mistyped a path toward the scriptify evals
    fixtures tree; python raised FileNotFoundError before opening anything, so
    nothing under evals/fixtures/ was read. Not retried.

## Step 8 - rewrite the target SKILL.md

25. REWROTE: $TARGET/SKILL.md - one Edit, atomic, after the green smoke test.
    Steps 1-3 collapse into the single exact invocation; step 4 keeps its
    judgment sentence and its "tutorial pages get the most traffic" rationale
    verbatim.
26. `diff -u $REVIEW/SKILL.md.orig $TARGET/SKILL.md` exit 1 (differs, as
    intended). Re-ran smoke_test.py after the rewrite: 11/11 passed.

## Step 9 - wrap up

27. Residue = No, so nothing was installed under $TARGET/scripts/tests/ and
    keep_residue.py was not run. $REVIEW/ is kept rather than deleted; see
    user_notes.md.
28. CREATED: outputs/report.md, outputs/transcript-notes.md,
    outputs/metrics.json, outputs/user_notes.md.

## Final state of the target

    docs-linter/SKILL.md                  rewritten (2 steps, was 4)
    docs-linter/scripts/lint_docs.py      new
    docs-linter/scripts/check_headings.py UNCHANGED
    docs-linter/docs/**                   UNCHANGED
