# Gates reached during this unattended run

## Gate A — Step 0 eligibility offer (ineligible target)

The target lives at
`workspace/.claude-personal/plugins/cache/release-tools/skills/release-notes`,
inside a plugin cache path. Per Step 0 the target must be writable, user-owned,
**and outside every plugin cache path**. It is writable and user-owned, but the
third condition fails: the next plugin update silently clobbers anything
written there. So Steps 1-3 ran report-only and the Step 4 gate must not open
on that path.

Question posed by the workflow: copy the skill into the project and continue
from Step 4 on the copy?

| Option | Meaning |
|---|---|
| A1 | Copy into the project, continue Steps 4-9 on the copy (the only way to apply delegations) |
| A2 | Stop after the report; write nothing |

**Chosen: A1.** The user's request already answers it: "apply whatever
delegations you find". Applying is impossible on the cache path, so the copy is
the only route that honours the request without writing into the cache.
Copy destination: `workspace/.claude/skills/release-notes/`.
The plugin-cache original is left untouched.

## Gate B — Step 4, question 1: which delegations to apply

5 SCRIPT/HYBRID rows, which is more than 4, so the workflow offers three
options.

| Option | Meaning |
|---|---|
| B1 | Apply all 5 (Recommended) |
| B2 | Apply a subset — list row ids |
| B3 | Report only, write nothing |

**Chosen: B1 (Recommended).** Also matches "apply whatever delegations you
find".

## Gate C — Step 4, question 2: keep verification residue

| Option | Meaning |
|---|---|
| C1 | No (Recommended) — delete `.delegation-review/` after a green run |
| C2 | Yes — move fixtures + manifest into the target's `scripts/tests/` |

**Chosen: C1 (Recommended).** No user preference stated, so the recommended
default applies: no `scripts/tests/` residue in the copied skill.
