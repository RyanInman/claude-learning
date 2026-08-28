# Question themes — worked option sets

Read this when you know a theme applies but not what to ask inside it. Every set below is a starting point, not a script. Rewrite the options in the user's own domain words, because a generic option forces the user to translate before they can answer.

## Contents

- [Theme 1 — Scope and users](#theme-1--scope-and-users)
- [Theme 2 — Data and integrations](#theme-2--data-and-integrations)
- [Theme 3 — Edge cases and errors](#theme-3--edge-cases-and-errors)
- [Theme 4 — Non-functional requirements](#theme-4--non-functional-requirements)
- [Theme 5 — Success criteria](#theme-5--success-criteria)
- [Writing good options](#writing-good-options)

---

## Theme 1 — Scope and users

Ask here when you cannot tell who the change serves or where it ends.

**Who is this for?**
- The end user of the product
- Internal staff or admins
- Another system, through an API
- The developer working on this code

**Is this a new thing or a change to an existing one?**
- New surface, built alongside what exists
- Replaces the current behavior
- Extends the current behavior, old path still works

**What is explicitly not in this change?**
- Nothing, build it all
- Ship the read path now, the write path later
- Ship one entity type now, generalize later

## Theme 2 — Data and integrations

Ask here when the source, shape, or destination of the data is open.

**Where does the data come from?**
- The existing database tables
- A third-party API
- A file the user uploads
- Computed at request time from what we already have

**How fresh does it need to be?**
- Live, on every read
- Cached, refreshed on a schedule
- Snapshotted once, refreshed manually

**What happens to the existing schema?**
- Additive only, no migration
- New columns on existing tables
- New tables
- Backfill required for existing rows

## Theme 3 — Edge cases and errors

Ask here when a failure would be visible to someone. Skip when the operation is read-only and trivially retryable.

**What should happen when there is no data to show?**
- Empty state with a call to action
- Hide the whole section
- Show zeros

**When the operation fails partway, what does the user get?**
- All-or-nothing, roll back everything
- Keep what succeeded, report what failed
- Retry automatically, then report

**Who sees the error detail?**
- Full detail to the user
- Generic message to the user, detail to the logs
- Silent, logged only

## Theme 4 — Non-functional requirements

Ask here only when a constraint would change the design. Do not ask about performance on a screen three people open weekly.

**What scale does this need to hold?**
- Tens of records
- Thousands
- Millions, needs pagination and indexes

**Who is allowed to do this?**
- Anyone signed in
- A specific role
- The record's owner only
- No auth, it is public

**Does this need to work offline or on mobile?**
- Desktop web only
- Responsive, mobile browsers included
- Offline-capable

## Theme 5 — Success criteria

Ask here when you cannot state a test that would prove the change worked.

**How will you know this worked?**
- A specific number moves (name it)
- A manual flow completes end to end
- A test suite passes
- Users stop reporting a specific complaint

**What would make you call this a failure even if it shipped?**
- It is slower than what it replaced
- It breaks an existing workflow
- Nobody uses it
- It needs manual babysitting

---

## Writing good options

- **Name the outcome, not the technique.** "A CSV the user downloads from the table" beats "client-side export".
- **Make options mutually exclusive.** Overlapping options force the user to explain instead of choose. That defeats the format.
- **Two to four options.** More than four turns a choice into a reading task.
- **Put your recommendation first and mark it,** because a user with no strong view wants a default.
- **Let the user escape.** `AskUserQuestion` always offers a free-text "Other", so never pad the list with a weak catch-all option.
- **Set `multiSelect` when the options combine,** such as which user roles are in scope. Leave it off for real forks, because a multi-select fork returns "both" and resolves nothing.
