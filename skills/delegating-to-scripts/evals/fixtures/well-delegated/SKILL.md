---
name: release-note-advisor
description: Reviews release notes for tone and audience fit before publishing. Use when the user asks to review or polish release notes.
---

# Release Note Advisor

## Workflow

1. Run exactly: `python3 scripts/check.py notes/ --json` to lint structure
   (title heading present). Exit 0 clean, 1 findings, 2 usage error.
2. Read the findings JSON and decide which flagged items actually matter for
   this release's audience — a missing heading on an internal note may be fine.
3. Write a short, plainly-worded explanation for each item worth fixing, in
   the project's usual voice.
