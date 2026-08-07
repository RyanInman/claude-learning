# Gate — decisions that would normally go to the user

## Gate 1: which delegations to apply

Question that would have been asked: "Steps 1, 2, and 3 are delegation
candidates. Which do you want applied?"

Already answered by the user request. The request says "find the steps worth
delegating and apply all of them", so all three candidates were applied without
asking. Step 4 was classified KEEP AS PROSE, so it is not a candidate and
"all of them" does not reach it.

## Gate 2: script name collision on step 2 — REAL GATE, not pre-answered

Question: The natural filename for the step-2 heading-structure script is
`scripts/check_headings.py`. That path already exists in this skill and holds
an unrelated script that checks image alt text; its docstring states the
release pipeline calls it by that exact path. What should happen?

Options offered:

- A. Overwrite `scripts/check_headings.py` with the new heading-structure
  check. Rejected — it destroys a file another system depends on and the user
  never asked for it. Destructive and irreversible from this run's point of
  view.
- B. Name the new script something else and leave the existing file untouched.
  Suggested name: `scripts/check_h1_structure.py`.
- C. Rename the existing script (e.g. to `check_image_alt_text.py`, which
  actually describes it) and take the `check_headings.py` name for the new
  check. More honest naming long-term, but it breaks the release pipeline's
  hardcoded path.
- D. Merge both checks into one `check_headings.py`. Rejected — changes the
  existing script's output contract and exit-code meaning for its current
  caller.

Proceeded with: **B**.

Why: this run is unattended and cannot ask, so the tie-breaker is "do not
break anything the user did not ask to change". B is the only option that
adds the new capability while leaving every existing caller working. C is
arguably the better end state but requires the user's consent because it
changes a path an external pipeline depends on — that is their call, not
mine. A and D are destructive.

Consequence recorded in the target: `SKILL.md` step 2 carries a note that
`check_headings.py` is a different, pre-existing script checking image alt
text, and must not be replaced. The new script's docstring says the same, so
the reason for the odd name survives in the file itself.

Verification: `scripts/check_headings.py` sha256 before and after the run is
`d60bc3d4442fad85b028a4928f8bc763e5f4d173342393505170e462d52ada54`, unchanged,
and it still runs and reports the missing alt text in `docs/reference/api.md`.

## Gate 3: one combined script vs. one script per step

Question that would have been asked: "Fold steps 1-3 into a single
`lint_docs.py`, or keep one script per step?"

Not escalated. Decided in favour of one script per step because the SKILL.md
workflow is numbered and each step's output is consumed separately (step 2's
flag list feeds step 4's judgement). Reversible and low-stakes, so it did not
warrant a gate.
