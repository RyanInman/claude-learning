---
paths:
  - "src/api/**"
---
# API rules

- Validate every handler's request body against a schema before use.
- Never build SQL by string interpolation; use parameterized queries.
