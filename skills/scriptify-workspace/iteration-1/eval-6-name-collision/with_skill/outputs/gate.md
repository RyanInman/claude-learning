# Gate (Step 4 + Step 6 collision) — answered unattended

No live user. Each question below is recorded with its options, the option taken,
and why.

## Question 1 — which delegations to apply

4 SCRIPT/HYBRID rows, so one option per row, all recommended (multiSelect).

- [x] s1 — SCRIPT — `docs_stats.py` (Recommended)
- [x] s2 — SCRIPT — heading check (Recommended)
- [x] s3 — SCRIPT — `docs_stats.py` (Recommended)
- [x] s4 — HYBRID — script enumerates flagged files, Claude ranks (Recommended)

**Taken: all four.** The user's request already answers this — "find the steps
worth delegating and apply all of them".

## Question 2 — keep verification residue in the target's `scripts/tests/`?

- No (Recommended)
- Yes

**Taken: No (Recommended).** Not answered by the request, so the recommended
option stands. `.delegation-review/` is removed after a green run; nothing extra
lands in the target.

## Question 3 — name collision on `scripts/check_headings.py`

Raised by Step 6's rule "name collision with an existing file -> ask the user.
Never overwrite silently". Asked here rather than mid-implementation because
Step 5 keys its fixture folders by script name, and the run is unattended.

The collision: the target already ships `scripts/check_headings.py`. Despite the
name, it checks that every markdown image carries alt text — nothing to do with
headings. Its own docstring says "the release pipeline still calls it by this
exact path", so the path is load-bearing outside this skill. It is not mentioned
anywhere in the target SKILL.md (inventory: `mentioned=False`), so no workflow
step is already delegated to it.

- **Rename the new heading checker to `check_h1.py`, leave the existing file
  byte-for-byte untouched (Recommended).** Nothing the release pipeline calls
  changes. Cost: two files whose names read as near-neighbours.
- Overwrite `check_headings.py` with the new heading checker. Breaks the release
  pipeline silently — the path still resolves, the behaviour is gone.
- Rename the existing script to `check_alt_text.py` and take the good name.
  Honest naming, but it moves the exact path the pipeline calls, so it breaks the
  pipeline just as hard.
- Report only, write nothing.

**Taken: rename the new script to `check_h1.py` (Recommended).** The user asked
to apply all delegations, and this is the only option that applies them without
touching a file the release pipeline depends on.

Follow-up worth raising with the user later (not acted on here — this skill never
edits another skill's unrelated files): `check_headings.py` is misnamed for what
it does, and nothing in the SKILL.md references it.
