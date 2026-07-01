---
name: totally-different-skill
description: Use this whenever the user wants to test that a frontmatter 'name' not matching its parent folder is flagged as a medium finding, per the packaging spec requirement.
---

# Name Dir Mismatch

Fixture skill whose frontmatter `name` deliberately does not match its folder
name (`name-dir-mismatch`).

## Workflow

1. Read the frontmatter `name`.
2. Compare it against the parent directory name.
3. Confirm a medium finding fires on mismatch.
