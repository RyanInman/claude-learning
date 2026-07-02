---
name: log-formatter-ok
description: Log formatter for structured logging pipelines that also documents the formatting rules used by downstream consumers and dashboards. Use this whenever the user wants to test that a long opening sentence does not trigger the name-redundancy finding even though it mentions the name tokens.
---

# Log Formatter Ok

Fixture skill whose description opening mentions the name tokens but is long
enough (>= 60 chars) that it adds real information beyond the name.

## Workflow

1. Read the log lines.
2. Apply the configured format.
