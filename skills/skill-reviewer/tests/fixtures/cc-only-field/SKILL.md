---
name: cc-only-field
description: Use this whenever the user wants to test that Claude Code-only frontmatter fields are reported as INFO instead of a HIGH unexpected-key finding, not for testing portable-spec keys.
when_to_use: Use this when testing the Claude Code-only frontmatter allowlist.
---

# CC Only Field

Fixture skill whose frontmatter includes `when_to_use`, a Claude Code-only field.

## Workflow

1. Read the frontmatter.
2. Confirm `when_to_use` is flagged INFO, not HIGH.
