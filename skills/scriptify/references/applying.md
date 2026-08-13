# Applying the picks — Steps 5 to 9

**You are here:** Steps 0-4 live in `SKILL.md` — locate the target, inventory
it, classify every step, render the report, open the gate. This file picks up
at Step 5 and runs only after the user picks rows. If you arrived here without
a pick, go back, because nothing below is safe to run.

## Contents

- [Step 5 — Contract first](#step-5--contract-first-before-any-script-exists)
- [Step 6 — Implement the scripts](#step-6--implement-the-scripts)
- [Step 7 — Smoke test](#step-7--smoke-test)
- [Step 8 — Rewrite the target SKILL.md](#step-8--rewrite-the-target-skillmd-atomic-last)
- [Step 9 — Wrap up](#step-9--wrap-up)

The Gotchas in `references/delegation-rubric.md`, read at Step 2, stay binding
through every step below. Two of them bite at implementation time:

- Big output needs `--out`, because a step that dumps 40KB into context spends
  the tokens the script saves.
- Pin one-liners verbatim in the rewritten step. Never bundle them, because a
  single command costs less inline than in a file.

## Step 5 — Contract first (before any script exists)

For each picked row, derive the test expectations from the semantics of the
step — what the prose says the step must catch. Never derive them from script
output. Then write the contract:

1. Enumerate the distinct ways the step can fail. Give each one its own
   finding code. Name the code after the condition the script tests, not the
   cause you infer from it. "The first line is not an H1" and "the file has no
   H1 anywhere" are two conditions, so they need two codes.

   One shared `missing_h1` code labels a file that has an H1 lower down as
   having none. The rewritten step then publishes that wrong label to every
   reader of the findings. Give every code its own fixture and its own asserted
   string, because a code with no fixture is a claim nothing checks.
2. Create fixtures under `.delegation-review/fixtures/<script-stem>/good/`
   and `.delegation-review/fixtures/<script-stem>/bad/`. The stem is the
   script name without `.py`. new_manifest.py points every invocation at that
   path. Give every validation script at least one passing example and
   one failing example.
3. Scaffold the manifest. Run exactly:

       python3 <skill>/scripts/new_manifest.py .delegation-review/classification.json --target <target-dir>

   Exit 0 written, 1 nothing to scaffold, 2 usage error. It writes one entry
   per unique script name, infers `check` versus `transform` from the exit
   contract, and points each invocation at its fixture.

   Do not read `new_manifest.py` or `smoke_test.py`. Between them they are
   ~500 lines. One measured run read both and spent more tokens than
   re-deriving the schema by hand. Run
   `python3 <skill>/scripts/new_manifest.py --help` instead. It prints the
   fixture layout and what each `TODO:` must become. That is everything the
   scaffold leaves you to decide.
4. Fill every `TODO:` value the scaffold left. Derive each value from what the
   step must catch. smoke_test.py refuses a manifest that still holds a
   `TODO:`. A scaffold that passed a hollow contract would be worse than no
   scaffold.
   Fixture paths here are relative to the working directory. Step 9 rewrites
   them to the `{skill}` form only when the user keeps the residue.

Re-read `.delegation-review/classification.json` from disk here, because the
recorded decisions outrank chat memory.

## Step 6 — Implement the scripts

Write each script into `<target>/scripts/`. Build each one to pass the
manifest you already wrote. Follow `references/script-conventions.md`:
argv-only, exit codes 0, 1, 2, and 3, JSON to stdout, `--help`, header
docstring.
Name collision with an existing file → ask the user. Never overwrite silently.
Leave the target SKILL.md untouched in this step, because Step 8 rewrites it
in one atomic pass.

## Step 7 — Smoke test

    python3 <skill>/scripts/smoke_test.py .delegation-review/manifest.json

On FAIL, fix the script, not the expectation. Change an expectation only when
you misread the step's semantics. Name every expectation you changed. Re-run until
exit 0. Red run → stop here. The target SKILL.md stays pristine, and
`.delegation-review/` holds the state so a later run can resume. Never claim done
on red.

## Step 8 — Rewrite the target SKILL.md (atomic, last)

Rewrite only after a green smoke test. Rewrite all picked rows in one pass.
Keep every fact the original step carried. Move nothing out of the target.
Replace only the mechanical instruction with the
exact invocation, as in "Run exactly:
`python3 scripts/check_headings.py changelogs/ --json`".
Keep rationale, branching, and gotcha sentences verbatim. Turn each
HYBRID step into "run the script, then apply judgment to its output", because
the judgment prose stays.

Shape the result as an orchestrator. Open each rewritten step with its exact
invocation. Key the branching off script exit codes or stdout fields wherever
the script exposes them. Write each branch as "exit 1 → …" or as "if
`findings` is empty → …". Leave only the judgment, user interaction, and
routing that scripts cannot do. Cut the mechanical prose the scripts now cover.

A SCRIPT step and a HYBRID step, before → after:

    - 2. Check that each file starts with a heading of the form
    -    `## vX.Y.Z — YYYY-MM-DD`. Record every file that does not.
    + 2. Run exactly: `python3 scripts/check_headings.py changelogs/ --json`
    +    Exit 0 clean, 1 findings (JSON on stdout), 2 usage error.

    - 6. Check every entry's category tag against the allowed list; for
    -    entries tagged `Misc`, judge whether they fit another category.
    + 6. Run exactly: `python3 scripts/check_tags.py changelogs/ --json`
    +    Invalid tags come back under `invalid`. For each entry under `misc`,
    +    judge whether it actually fits another category and suggest the move.

If the user picked keep-residue at Step 4, add the smoke-test command to the
target's body in this same pass, because Step 9 moves files only and must not
reopen the body. Write it in the form Step 9 makes true:
`python3 scripts/tests/smoke_test.py scripts/tests/manifest.json`. Never write
`<skill>` or any other placeholder into the target, because the target's user
cannot resolve this skill's internal notation. Then show the user the unified
diff of the SKILL.md change.

## Step 9 — Wrap up

Summarize four things: the scripts written, the diff already shown, the smoke
PASS line, and any DEAD steps flagged for a `skillit:review` follow-up.

If the user picked keep-residue, run exactly:

    python3 <skill>/scripts/keep_residue.py <target-dir> --review-dir .delegation-review

Exit 0 the residue is installed and green, 1 a verification run failed, 2 the
inputs are missing or `scripts/tests/` already holds residue files. Exit 0
covers both runs: in place and from a relocated copy. On exit 2, pass `--force`
to replace them, but only after you confirm the target does not own them.

keep_residue.py moves the fixtures and manifest into `<target>/scripts/tests/`.
It vendors `smoke_test.py` beside them. It rewrites every fixture path to the
`{skill}` form.

It then re-runs the smoke test twice: once in place, once from a throwaway copy
of the whole skill. That second run is the point. It proves the residue
survives relocation, because a stale absolute path breaks relocation silently.

Exit 1 → do not claim the residue works. Report which of the two runs failed.

Otherwise remove `.delegation-review/`, but only after a fully green run.
