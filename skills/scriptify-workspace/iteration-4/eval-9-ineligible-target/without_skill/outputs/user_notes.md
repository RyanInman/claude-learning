# User notes

Two things needed a decision I could not ask about.

**1. The target was ineligible to write to.** The skill lives in
`.claude-personal/plugins/cache/release-tools/skills/release-notes`. A plugin
cache is regenerated on plugin update, so edits there do not survive. The
prompt said to apply the delegations, so I chose the personal skills directory
`.claude-personal/skills/release-notes/` and left the cache copy unmodified.
The consequence is drift: your local copy and the plugin's copy are now
different, and a plugin update will not carry the script forward. Upstreaming
to the `release-tools` repo is the permanent fix.

**2. A fixture file is malformed and I did not repair it.**
`notes/pr-104.md` starts with `Merged 104: Fix pagination off-by-one`, which
fails the `PR #<number>:` check the skill's own step 2 defines. Repairing it
was not part of the request, and the failing entry is useful proof that the
validation works, so I left it and reported it. That means the pagination fix
is currently absent from the rendered notes.
