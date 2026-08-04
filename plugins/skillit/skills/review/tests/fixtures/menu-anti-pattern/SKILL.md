---
name: menu-anti-pattern
description: Use this whenever the user wants to test that a repeated 'or' option chain in the body is flagged as a menu anti-pattern, instead of recommending one default path with an escape hatch.
---

# Menu Anti Pattern

Fixture skill whose body deliberately reads as a menu of options.

## Workflow

1. Search with ripgrep or grep, or ag for the pattern across the repo.
2. Report the matches found.
