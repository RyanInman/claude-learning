---
name: menu-comma-list-ok
description: Use this whenever the user wants to test that an ordinary comma-list enumeration ('X, Y, or Z') in the body does not trigger the menu anti-pattern finding, unlike a repeated 'or' chain.
---

# Menu Comma List Ok

Fixture skill whose body uses a plain comma-list enumeration, not a repeated
'or' chain.

## Workflow

1. Search with ripgrep, grep, or ag for the pattern across the repo.
2. Report the matches found.
