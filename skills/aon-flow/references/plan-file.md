# Plan file format

Read this at Step 7, when the interview ends. Follow the template exactly, because the user
reached for this skill to get a plan that looks the same on run 50 as on run 1.

## Contents

- [Template](#template)
- [Naming real things](#naming-real-things)
- [Test plan rules](#test-plan-rules)
- [UAT checklist rules](#uat-checklist-rules)
- [Build order rules](#build-order-rules)
- [Filled example](#filled-example)

---

## Template

Write to `plans/<slug>-plan.md`.

```
# <Change name>

## Outcome

[One paragraph, present tense, written as though the change shipped. State what a
user can now do that they could not do before. No implementation detail.]

## Requirements

- CONFIRMED — [what must be true, in the user's terms]
- ASSUMED — [what must be true]. [What changes if this is wrong.]

## Acceptance criteria

**[Requirement]**
- Given [starting state]
- When [action]
- Then [observable result]

## Test plan

Runner: `[command]` ([how you identified it])

**Already covered**
- `[file]` :: `[test name]` — proves [requirement]

**To write**
- `[file]` :: [test name] — [tier]. Given [state], when [action], then [result].
  Proves [requirement].

## UAT checklist

- [ ] [Manual step a person performs, and what they must see]

## Build order

1. [Step] — touches `[file]`, `[file]`. Verify: [the test or command that proves it]
2. [Step] — touches `[file]`. Verify: [check]

## Resources

- `[path]` — [what this resource decided]

## Assumptions and open questions

- CONFIRMED — [fact the user stated]
- ASSUMED — [fact you filled in]. [What changes if wrong.]
- OPEN — [question still unanswered]. [How the plan proceeds meanwhile.]

## Out of scope

- [Thing deliberately unbuilt, and why]
```

## Naming real things

Nobody can test or build from a requirement that names no file, table, endpoint, or symbol.
Read the schema and the routes, then use the real names. Where you cannot find one, write
your best guess and mark it ASSUMED. A named assumption is correctable. A generic noun is
not.

| Instead of | Write |
|---|---|
| the main transactional record | the `orders` table |
| the reporting endpoint | `GET /api/admin/reports/summary` |
| the relevant middleware | `src/middleware/rateLimit.ts` |

## Test plan rules

- Name the runner and how you identified it, so a reader can correct a wrong guess in one
  line.
- List the tests that already pass before the tests to write. The user needs to see the real
  gap, not a wish list that duplicates existing coverage.
- Give every test to write a file, a tier, a Given/When/Then, and the requirement it proves.
  A test line that names no requirement cannot be cut when its requirement is cut.
- Where the repo has no harness, name the runner to add and the single first failing test.
  One failing test is enough to start. A full suite designed up front is guesswork.

## UAT checklist rules

Write only the checks a runner cannot make: a visual match against the mockup, copy tone, a
flow crossing two systems, a permission a human must hold.

Write each item as an action plus what the person must see. "Check the export works" is not
checkable. "Click Export on a filtered table, then confirm the downloaded CSV holds only the
filtered rows" is.

## Build order rules

The user approves a plan to learn what it costs and where they can cut, so sequence the work
before you present it.

- Number the steps and name the files each one touches.
- Give every step a check, drawn from the test plan where one fits.
- Order so the user can stop early. Each step leaves something that runs.
- Put the riskiest unknown first unless a dependency blocks it, because a failed approach
  found in step 2 costs far less than one found in step 8.

## Filled example

From the CSV export request in the SKILL.md worked example.

```
# Orders CSV export

## Outcome

An ops user exports the orders they are looking at. The orders table toolbar carries
an Export button and a column picker. The download holds exactly the rows the current
filters select, with the columns the user ticked, in the order the table shows them.

## Requirements

- CONFIRMED — The export includes the column picker shown in `mockups/orders-export.png`.
- CONFIRMED — The export covers the filtered rows, not the whole table.
- ASSUMED — The export runs in the browser from rows already loaded. Above roughly
  50,000 rows this runs out of memory and the export moves server-side to a stream.

## Acceptance criteria

**Filtered rows only**
- Given an orders table filtered to status=failed, showing 12 of 400 rows
- When the user clicks Export
- Then the CSV holds 12 data rows and one header row

**Column picker**
- Given the user unticks Customer email in the column picker
- When the user clicks Export
- Then the CSV has no customer email column, and the remaining columns keep table order

## Test plan

Runner: `npx vitest run` (from the `test` script in `package.json`)

**Already covered**
- `tests/orders/table.test.ts` :: `applies status filter to visible rows` — proves the
  filter state the export reads.

**To write**
- `tests/orders/csvExport.test.ts` :: `serializes filtered rows` — unit. Given 12
  filtered rows, when the serializer runs, then the output holds 13 lines. Proves
  the filtered-rows requirement.
- `tests/orders/csvExport.test.ts` :: `escapes commas and quotes in values` — unit.
  Given a customer name `Smith, "Bo"`, when the serializer runs, then the field is
  quoted and the inner quotes doubled. Proves the malformed-data edge case.
- `tests/orders/columnPicker.test.ts` :: `omits unticked columns` — unit. Given
  Customer email unticked, when the serializer runs, then the header omits it.
  Proves the column-picker requirement.
- `tests/e2e/ordersExport.spec.ts` :: `downloads a CSV from the toolbar` — end-to-end.
  Given a filtered table, when the user clicks Export, then a `.csv` file downloads.
  Proves the button wiring.

## UAT checklist

- [ ] Compare the toolbar against `mockups/orders-export.png`. Button label, icon, and
      placement match.
- [ ] Open the downloaded CSV in Excel. The header row reads as text, and no order id
      renders in scientific notation.
- [ ] Export with a 10,000-row filter. The browser stays responsive.

## Build order

1. Serializer and escaping — touches `src/orders/csvExport.ts`. Verify:
   `npx vitest run tests/orders/csvExport.test.ts`
2. Column picker state — touches `src/orders/ColumnPicker.tsx`,
   `src/orders/useOrdersTable.ts`. Verify:
   `npx vitest run tests/orders/columnPicker.test.ts`
3. Toolbar button and download wiring — touches `src/orders/OrdersToolbar.tsx`.
   Verify: `npx playwright test tests/e2e/ordersExport.spec.ts`
4. UAT pass. Verify: the checklist above.

Steps 1 and 3 ship a working export. Step 2 can be cut, which drops the column picker
and leaves every column in the file.

## Resources

- `mockups/orders-export.png` — toolbar layout, button label, column picker placement.
- `docs/orders-api.md` — the order field list and their display names.

## Assumptions and open questions

- CONFIRMED — filtered rows only.
- CONFIRMED — the column picker ships this round.
- ASSUMED — browser-side export up to roughly 50,000 rows.
- OPEN — whether the CSV needs a UTF-8 byte order mark for Excel. Proceeding with the
  mark, because Excel mangles accented names without it.

## Out of scope

- Scheduled or emailed exports.
- Any format other than CSV.
```
