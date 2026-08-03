---
name: script-security
description: Use this whenever the user wants to test that a bundled script combining an env-var read with a network call, and one that interpolates a variable into a URL, are flagged as security findings -- while a script that only reads an env var with no network call is not.
---

# Script Security

Fixture skill with two bundled scripts.

## Workflow

1. Run scripts/evil.py or scripts/fine.py as needed.
