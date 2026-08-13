---
name: api-docs-checker
description: Checks the endpoint documentation under endpoints/ for missing fields and unclear descriptions. Use when the user asks to check, validate, or review the API docs.
---

# API Docs Checker

Check the endpoint files for missing metadata, then report what needs a human
rewrite.

## Workflow

1. List every `.md` file in `endpoints/`, sorted by path, and note the total
   count.
2. Check that every endpoint file has a `summary:` field in its frontmatter.
   Record every file that does not.
3. Check that every endpoint file has both a `summary:` field and a
   `description:` field in its frontmatter. Record which field is missing from
   which file.
4. Append the endpoint list to `legacy/index.txt` so the old docs portal can
   pick it up.
5. Judge whether each `description:` reads clearly for an external developer
   who has never seen this API, and flag the ones that do not.

## Notes

The legacy docs portal was retired in v2, and the `legacy/` output directory
went with it.
