# Gate record

One decision point would normally go to the user; the request already answered it,
so the run proceeded without stopping.

## Question 1 — which delegations to apply?

Options that would have been offered:
- A: apply all script and hybrid delegations (steps 1, 2, 3, 5, 6)
- B: apply only the fully deterministic ones (1, 2, 3, 5), leave 6 prose
- C: pick individually

Proceeded with: **A**.
Why: the request says "apply all of them", which selects every delegation the
review identified. No user input needed.

## Question 2 — keep or delete the fixtures and manifest after the smoke test?

Options that would have been offered:
- A: keep `scripts/tests/` (fixtures + manifest) inside the skill
- B: delete them after the smoke test passes, leaving only the scripts

Proceeded with: **A**.
Why: the request says "Keep the test fixtures and the manifest inside the skill
afterward so I can re-run the checks myself later." Fixtures were therefore
authored directly at their final location, `scripts/tests/fixtures/`, and the
manifest at `scripts/tests/manifest.json` with absolute paths pointing there —
no temporary review directory was ever used, so no path rewrite was needed and no
stale path can survive. A runner, `scripts/tests/run_smoke.py`, ships alongside so
the user can re-run the checks with one command, and that command is recorded in
SKILL.md.

## Questions 4 and 7 — script or prose?

Not a user gate. Steps 4 (release narrative) and 7 (clarity judgment) have no
deterministic output; classifying them as prose is the review's own call, recorded
with reasoning in report.md.

No other point in the run required a user choice.
