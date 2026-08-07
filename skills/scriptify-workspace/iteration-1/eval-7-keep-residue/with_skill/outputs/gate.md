# Step 4 gate (unattended run)

The skill asks two questions with AskUserQuestion. No live user, so both are
recorded here and answered from the user's original request.

## Question 1 — which delegations to apply?

6 SCRIPT/HYBRID rows, more than 4, so the skill mandates the three-option form:

1. **Apply all 6 (Recommended)** — s1, s2, s3, s5, s6, s7.
2. Apply a subset — list row ids.
3. Report only, write nothing.

**Chosen: option 1, apply all 6.** It is both the recommended option and what
the request states: "apply all of them".

## Question 2 — keep verification residue (fixtures + manifest) in the target's `scripts/tests/`?

1. No (Recommended)
2. **Yes**

**Chosen: option 2, Yes.** The recommended default is No, but the request
overrides it: "Keep the test fixtures and the manifest inside the skill
afterward so I can re-run the checks myself later." An explicit user
instruction outranks the default.
