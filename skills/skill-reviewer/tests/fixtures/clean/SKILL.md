---
name: widget-validator
description: Use this whenever the user needs to validate a widget configuration file before deployment, including checking required fields and format constraints. Not for validating legacy XML configs; use the legacy-validator skill for that instead of this one.
---

# Widget Validator

Validates widget configuration files before deployment.

## Workflow

1. Read the config file.
2. Check required fields are present.
3. Report any validation errors found.
