---
name: allowed-tools-broad
description: Use this whenever the user wants to test that an unscoped 'Bash' entry in allowed-tools is flagged as a broad tool grant, not for testing a command-scoped grant like Bash(git:*); use the allowed-tools-scoped-ok fixture for that instead.
allowed-tools: Bash
---

# Allowed Tools Broad

Fixture skill whose frontmatter grants unrestricted Bash.

## Workflow

1. Run any shell command needed.
