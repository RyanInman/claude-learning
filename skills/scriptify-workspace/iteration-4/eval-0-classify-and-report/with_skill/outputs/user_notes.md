- `.delegation-review/` went to `RUN_DIR/scratch/.delegation-review/` rather than the
  working directory's root, because the harness reserves `RUN_DIR/scratch/` for transient
  files. The skill allows relocating it and requires printing where it went.
- `render_report.py` renders the verdict and the table but has no slot for the data
  findings the skill's Step 1 requires the report to name. I appended those findings, the
  table reading, and the next-step line below the rendered block, so `outputs/report.md`
  is the rendered report plus that addendum.
- `git status` reported the target SKILL.md as untracked (`??`), not as a dirty tracked
  file, so no uncommitted-changes warning was raised. The restore point was still copied.
