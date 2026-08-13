---
name: release-notes
description: Assembles release notes from the merged pull request titles in notes/ and writes a summary paragraph. Use when the user asks to build or draft release notes.
---

# Release Notes

Assemble the release notes for the current milestone.

## Workflow

1. List every `.md` file in `notes/`, sorted by filename, and note the total
   count.
2. Check that each file starts with a line of the form `PR #<number>:`. Record
   every file that does not.
3. Group the entries by their `type:` field (`feat`, `fix`, `chore`) and count
   each group.
4. Write a two-sentence summary of the release for the customer-facing
   changelog.
5. Render the final notes as a markdown list, grouped by type, sorted by PR
   number ascending.
