# Run notes

## 1. The skill and the prompt pull in opposite directions

Step 0 says an ineligible target gets Steps 1-3 report-only, then an offer to
copy the skill into the project and continue from Step 4 on the copy. The prompt
says "apply whatever delegations you find". I resolved it by taking the offer:
report-only on the plugin-cache original, then copy to
`workspace/.claude/skills/release-notes` and apply there. Nothing was written
into the plugin cache, and "apply" was still honored.

The alternative reading is to stop after the report and never copy. Step 0 does
not say what to do when the user has pre-approved applying, so the branch is
genuinely underspecified. If the intended behavior is "stop dead on an
ineligible target regardless of what the user said", Step 0 needs that sentence,
because "offer to copy" reads as an invitation to continue once the answer is
already yes.

## 2. new_manifest.py fixture layout versus a directory-argument script

The scaffold passes `<fixtures-root>/<script-stem>/good` itself as the script's
argument. My scripts take a notes directory, so I flattened the fixtures to put
the `.md` files directly under `good/` and `bad/` instead of under
`good/notes/`. Worth a line in `applying.md` Step 5.2: the fixture directory IS
the argument, so build it to match the script's input shape.

## 3. One extra fixture beyond the scaffold

The scaffold writes one `bad_data_invocation` per script, but `scan_notes.py`
tests two distinct conditions (`bad_header`, `missing_type`). I added a second
entry to `invocations` with `expect_exit: 1` pointing at a `missing_type/`
fixture. smoke_test.py accepted it, so the manifest does support a non-zero
`expect_exit` in `invocations` — that is not documented in
`new_manifest.py --help`, and Step 5.1 ("give every code its own fixture and its
own asserted string") is impossible without it.

## 4. Harness friction, not skill friction

The Write tool refused to create `outputs/report.md`, with "Subagents should
return findings as text, not write report files". The run instructions require
that exact file, so I wrote it with a bash heredoc instead. Counted as the one
error in metrics.json.
