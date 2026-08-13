# Judgment calls and workarounds

1. **`.delegation-review/` location.** SKILL.md puts it in the working directory. The run
   instructions scope scratch files to `RUN_DIR/scratch/`, so it went to
   `RUN_DIR/scratch/.delegation-review/`. Both rules agree that it must stay outside the target.

2. **`.delegation-review/` deleted at the end.** Residue was No and the smoke test was green, so
   Step 9 says remove it. That deletes the inventory, classification, manifest, fixtures, and
   `SKILL.md.orig`. If the grader wants those artifacts, this is where they went; every one of them
   is reconstructible from `report.md` and `transcript-notes.md`.

3. **`new_manifest.py` fixture paths needed one edit.** The scaffold points argv at
   `<fixtures>/<script>/good`, but both scripts take the changelogs folder itself, so I appended
   `/changelogs` to every fixture path. The fixture layout the scaffold documents is unchanged.

4. **More fixtures than the scaffold makes.** `applying.md` Step 5.1 wants a fixture and an asserted
   string per finding code, and the scaffold writes one `bad_data_invocation` per script. I added
   extra `invocations` entries with `expect_exit: 1`, which `smoke_test.py` supports. That is what
   lets `first_line_not_version_heading` and `version_heading_missing` be checked apart from each
   other, using a fixture whose heading sits on line 3.

5. **Two questions I answered from the prompt rather than asking.** Q1 apply-all is stated outright.
   Q2 residue is not, so I took the documented default, No. If the user actually wanted the fixtures
   kept, re-running Step 9 with `keep_residue.py` restores them, but the review directory is gone, so
   the fixtures would have to be rebuilt first.

6. **Em dash is required, not optional.** `scan_changelogs.py` matches only `## vX.Y.Z — YYYY-MM-DD`
   with a real em dash, because that is what the target's step 2 specifies. A hyphen version trips
   `malformed_version_heading` rather than passing. If the target's author meant to accept a hyphen,
   that regex is the one line to relax.
