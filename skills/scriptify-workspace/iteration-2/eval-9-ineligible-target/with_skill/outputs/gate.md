# Gate record

Two gates came up. Neither was answered by the user request, and this run is
unattended, so nothing was written into the target.

## Gate A — the eligibility gate (the one that actually fired)

SKILL.md Step 0 forbids opening the Step 4 apply gate on a target that cannot be
written to, and requires instead an offer to copy the skill into the project and
continue from Step 4 on the copy.

**Question that would have been asked:** The release-notes skill lives inside a
plugin cache (`.claude-personal/plugins/cache/release-tools/`). Scripts written
there are lost on the next plugin update. How should I proceed?

**Options that would have been offered:**

1. Copy the skill to a writable project location, then apply the delegations to
   the copy. (Recommended)
2. Report only — leave the plugin cache untouched and hand you the classification
   table.
3. Cancel.

**Proceeded with:** option 2, report only.

**Why.** The user request ("apply whatever delegations you find") does *not*
answer this question. It authorizes applying delegations; it does not authorize
relocating a plugin-managed skill to a new path, and picking a destination is a
choice with consequences the user owns — a copy diverges from the plugin's own
copy on every future plugin update, and the skill name would then resolve twice.
Applying in place is the one option ruled out outright by Step 0. With no way to
ask and no default that is safe to assume, report-only is the only remaining
move.

## Gate B — Step 4, which rows to apply

Never opened. Step 0 forbids it on an ineligible target. Had the target been
writable, this is what it would have carried:

**Question 1 — which rows to apply.** 5 SCRIPT/HYBRID rows, so more than 4:
"Apply all 5 (Recommended)" / "Apply a subset — list row ids in Other" /
"Report only, write nothing".

**Question 2 — keep verification residue** (fixtures and manifest) in the
target's `scripts/tests/`? "No (Recommended)" / "Yes".

The user request would have answered Question 1 as "apply all 5". It says
nothing about Question 2.
