---
name: desc-do-not-ok
description: Use this whenever the user wants to validate a config file before deployment, checking required fields and format constraints. Do NOT use this for handling legacy XML configs; use the legacy-validator skill for that instead of this one.
---

# Desc Do Not Ok

Fixture skill whose description uses 'Do NOT' as the recommended
negative-trigger idiom, which must not be flagged as shouting.

## Workflow

1. Read the config file.
2. Check required fields are present.
