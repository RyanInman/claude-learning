---
name: guarded-publisher
description: Publishes a draft post from drafts/ to the site. Use when the user asks to publish a draft.
---

# Guarded Publisher

## Workflow

1. Confirm the draft in `drafts/` has a `title:` and a `date:` frontmatter
   field and that the body is under 800 words.
2. NEVER publish while `git status` shows uncommitted changes. ALWAYS run
   `npm test` before every publish, because a red build ships a broken page.
3. Decide whether the post's tone fits the current audience. Ask the user
   when the draft reads as internal-only.
4. Run `npm run publish -- drafts/<file>`.
