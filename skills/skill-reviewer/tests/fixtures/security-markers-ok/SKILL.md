---
name: security-markers-ok
description: Use this whenever the user wants to test that a short base64-like string under 80 chars and ordinary wording about ignoring a previous section do not raise security findings, not for testing the tripping markers; use the security-markers fixture for that instead.
---

# Security Markers Ok

Fixture skill whose body stays just under every injection-marker threshold.

## Workflow

1. Compare against this short token: QUJDREVGRw==
2. Readers can ignore the previous section if it does not apply.
