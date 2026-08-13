# Notes

- `sample_target_data.py` digested topics.txt but reported no outliers, because
  it inspects first lines across files and the target ships a single data file.
  The planted defects in that file (a blank line, an exact duplicate, and a
  case-variant duplicate) came from reading the file directly. A digest keyed
  on within-file repetition would have surfaced them.
- Step 0 says to copy the target SKILL.md to `.delegation-review/SKILL.md.orig`
  on an eligible target. This target is eligible, but the prompt forbids any
  write to it, so the restore point was skipped — it protects a rewrite this
  branch never performs.
- `.delegation-review/` went to `RUN_DIR/scratch/` per the run instructions
  rather than the working directory.
