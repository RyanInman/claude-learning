# Gate

One decision point would normally be put to the user: **which of the identified
delegations to apply.**

Question that would have been asked: "Steps 1, 2, 3, 5 and the mechanical half of
6 are script candidates. Apply all of them, or a subset?"

Options that would have been offered:
- A. Apply all five (four full steps + split step 6).
- B. Apply only the four full-step delegations, leave step 6 entirely prose.
- C. Apply only the validation scripts (steps 2 and 6) and leave counting/rendering prose.

**Already answered by the user request.** The request says "apply all the
delegations you find", so option A was taken without asking. No user prompt was
issued; this run was unattended.

Second, smaller decision, resolved without asking because it is an
implementation detail rather than a scope choice: whether `check_headers.py`
should accept a plain hyphen as well as the em dash in `## vX.Y.Z — YYYY-MM-DD`.
Proceeded with **em dash only**, matching the skill's stated format literally.
A hyphen variant would silently widen the spec the skill defines. If the project
actually uses hyphens, that is a one-line regex change in
`scripts/changelog_lib.py`.
