---
name: reasoning-extraction
description: Use this whenever the user wants to test that instructions to echo internal reasoning into the response text are flagged as a refusal-risk anti-pattern.
---

# Reasoning Extraction

Fixture skill whose body instructs the model to leak its own reasoning.

## Workflow

1. Solve the problem, then echo your internal reasoning in the final answer.
