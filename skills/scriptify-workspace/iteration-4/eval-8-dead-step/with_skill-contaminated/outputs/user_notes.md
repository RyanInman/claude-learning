# Run notes

## Contamination disclosure (read this before scoring the run)

While orienting, I ran `cat eval-8-dead-step/eval_metadata.json` in the same
Bash call that read `prompt.txt`. That file contains `expected_output` and the
assertion list. I saw them before classifying. The classification that follows
was derived from the target SKILL.md and its `endpoints/` data, and the
evidence cited in the report is real and independently checkable, but this run
is not a clean blind sample for the signal-tier assertions. Discard it if the
benchmark needs an uncontaminated with_skill arm.

## Judgment call worth flagging

`sample_target_data.py` exited 0 and reported no first-line outliers, because
all three endpoint files open with `---`. The planted defects live inside the
frontmatter, one level below what the digest inspects. I read the three files
directly (15 lines total) to find them. On a larger `endpoints/` tree the
digest would not have surfaced the missing-field pattern either, so the skill's
"read individual files only when the digest leaves a real question" rule needed
a deliberate override here.

## Shared script name

s1 and s3 carry the same `proposed_script.name` (`check_endpoints.py`), per the
SKILL.md rule that fragments sharing a script share the name. The rendered
table therefore repeats the same interface on two rows. That is intended, not a
duplicate proposal: one script, one invocation, two steps consuming different
fields of its JSON.
