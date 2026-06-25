---
paths:
  - "src/api/**"
---
# API handler rules

Validate every handler's request body against a schema before using it. Never pass
`req.body` straight into a database call.
