---
name: release-notes
description: Assembles release notes from the merged pull request titles in notes/ and writes a summary paragraph. Use when the user asks to build or draft release notes.
---

# Release Notes

Assemble the release notes for the current milestone.

## Workflow

1. Collect and validate the notes:

   ```bash
   python3 scripts/collect_notes.py > /tmp/release-notes-data.json
   ```

   Emits JSON with `file_count`, `files`, `entries` (PR number, title, type),
   `invalid`, `by_type` counts, and `unknown_types`.

2. If `invalid` is non-empty, stop. Report each malformed file and its reason to
   the user, and do not render notes until they are fixed. Also flag any
   `unknown_types` beyond `feat`, `fix`, and `chore`.

3. Read `entries` and `by_type`, then write a two-sentence summary of the release
   for the customer-facing changelog. Ground both sentences in the actual PR
   titles. Save it:

   ```bash
   cat > /tmp/release-summary.txt
   ```

4. Render the final notes:

   ```bash
   python3 scripts/render_notes.py \
     --data /tmp/release-notes-data.json \
     --summary /tmp/release-summary.txt
   ```

   Groups by type in `feat`, `fix`, `chore` order and sorts each group by PR
   number ascending.
