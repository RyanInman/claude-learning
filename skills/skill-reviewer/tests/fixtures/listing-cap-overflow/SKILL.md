---
name: listing-cap-overflow
description: Use this whenever the user needs to validate, transform, and report on structured data files before deployment, including checking schema conformance and required fields. Not for validating legacy XML configs. Use this whenever the user needs to validate, transform, and report on structured data files before deployment, including checking schema conformance and required fields. Not for validating legacy XML configs.
when_to_use: Use this when the user explicitly wants deep listing-cap detail on demand, describing edge cases, historical context, migration notes, and long-form guidance that would otherwise be truncated from the always-on skill listing shown to the model at session start. Use this when the user explicitly wants deep listing-cap detail on demand, describing edge cases, historical context, migration notes, and long-form guidance that would otherwise be truncated from the always-on skill listing shown to the model at session start. Use this when the user explicitly wants deep listing-cap detail on demand, describing edge cases, historical context, migration notes, and long-form guidance that would otherwise be truncated from the always-on skill listing shown to the model at session start. Use this when the user explicitly wants deep listing-cap detail on demand, describing edge cases, historical context, migration notes, and long-form guidance that would otherwise be truncated from the always-on skill listing shown to the model at session start. Use this when the user explicitly wants deep listing-cap detail on demand, describing edge cases, historical context, migration notes, and long-form guidance that would otherwise be truncated from the always-on skill listing shown to the model at session start.
---

# Listing Cap Overflow

Fixture skill whose combined description + when_to_use exceeds the 1,536-char
per-entry listing cap.

## Workflow

1. Read the combined length.
2. Confirm the listing-cap check fires INFO.
