# Step 4 gate (unattended run)

The skill's Step 4 opens an AskUserQuestion gate. No live user, so the questions
and options are recorded here.

## Question 1 — which delegations to apply

7 SCRIPT/HYBRID rows, so the >4-row form applies. Options offered by the skill:

1. Apply all 7 (Recommended)
2. Apply a subset — list row ids in Other
3. Report only, write nothing

**Chosen: option 3, "Report only, write nothing."** The user's request already
answers this question: "Report only for now, don't change anything." An explicit
user instruction outranks the skill's recommended default, and the skill's own
rule is "Never write into the target without an explicit pick."

## Question 2 — keep verification residue in the target's `scripts/tests/`?

1. No (Recommended)
2. Yes

**Not applicable.** Question 2 only matters once scripts get written. Report-only
run writes nothing, so no fixtures or manifest exist to keep. Moot.

## Consequence

Run stops after Step 3 (report). Steps 5-9 (contract, implement, smoke test,
SKILL.md rewrite, wrap-up) are not executed. The target skill folder is
untouched: `SKILL.md` and `topics.txt` are byte-identical to the baseline.
