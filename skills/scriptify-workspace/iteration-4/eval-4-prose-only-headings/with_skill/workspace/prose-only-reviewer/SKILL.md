---
name: link-checker
description: Checks a docs folder for broken relative links and recommends which ones to fix. Use when the user asks to check or audit documentation links.
---

# Link Checker

Find broken relative links in `docs/` and recommend a fix order.

## Collect the link inventory

Walk every `.md` file under `docs/` and record each relative link target with
its source file and line number.

## Resolve each target

Mark a link broken when its target path does not exist on disk. Report the
count of broken links alongside the total number of links.

## Decide what to fix now

Weigh each broken link against the docs owner's release deadline and pick the
ones worth fixing in this pass.

## Gotchas

Anchor-only links (`#section`) point inside a page, not at a file. Skip them.
