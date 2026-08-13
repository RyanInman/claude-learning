---
name: release-notes
description: Assembles release notes from the merged pull request titles in notes/ and writes a summary paragraph. Use when the user asks to build or draft release notes.
---

# Release Notes

Assemble the release notes for the current milestone.

## Workflow

1. Run the builder from the skill directory:

   ```bash
   python3 scripts/build_notes.py
   ```

   It scans `notes/`, validates each file's `PR #<number>:` header, groups the
   entries by `type:`, and renders the markdown list sorted by PR number
   ascending. Pass a directory path as the first argument to scan a different
   notes folder.

2. Read the `FACTS` lines the script prints — `FILES`, `VALID`, `MALFORMED`,
   `COUNTS` — and quote those numbers verbatim. Do not recount the files
   yourself, because a second count can disagree with the rendered list.

3. Report every filename under `MALFORMED` to the user. Those files lack a
   `PR #<number>:` first line or a `type:` line, so the script leaves them out
   of the rendered notes.

4. Write a two-sentence summary of the release for the customer-facing
   changelog. This is the judgment step: read the entry titles and say what the
   release delivers, not how many entries it has.

5. Deliver the summary followed by the `--- NOTES ---` block from the script
   output, pasted unchanged.

## Gotchas

- The script excludes malformed files rather than guessing their PR number,
  because a wrong number in a changelog is worse than a missing entry. Fix the
  file's first line and rerun.
- Unknown `type:` values are kept and rendered under their raw name after
  `feat`, `fix`, and `chore`, so a typo like `fixes` shows up as its own group
  instead of vanishing.
- The script exits 1 when the notes directory does not exist. Check the path
  before assuming the milestone is empty.
