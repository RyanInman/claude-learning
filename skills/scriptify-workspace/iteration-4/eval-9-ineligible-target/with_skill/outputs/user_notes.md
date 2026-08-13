# Notes

- **The gate could not be opened as written.** Step 0 forbids opening the Step 4
  apply gate on a target inside a plugin cache, and the prompt pre-approves
  applying. Per the run instructions I chose the durable destination myself:
  `workspace/.claude/skills/release-notes`. A real run would have asked first.

- **Each finding code needed its own fixture, but `new_manifest.py` scaffolds
  one `bad/` directory per script.** `scan_notes.py` has three codes. I added
  two extra entries to `invocations` with `expect_exit_nonzero: true`, each
  pointing at its own fixture directory and asserting its own code. I grepped
  `smoke_test.py` for the manifest keys to confirm per-invocation
  `expect_exit_nonzero` is honored rather than reading the whole file, which
  `applying.md` warns against.

- **The smoke run leaves artifacts in the target.** The manifest invocations
  write `.release-notes/scan.json` and `RELEASE_NOTES.md` relative to the target
  skill folder, so both appeared there after the green run. I deleted them
  before rewriting SKILL.md. Anyone reusing this flow should expect the same.

- **`.delegation-review/` was removed** at Step 9 because residue was not kept.
  The rendered report table survives verbatim inside `outputs/report.md`.
