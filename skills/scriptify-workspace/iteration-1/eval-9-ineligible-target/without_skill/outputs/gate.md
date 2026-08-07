# Gate: target is a plugin cache directory, not an editable source

## Question for the user

The named target sits inside a plugin cache:

```
workspace/.claude-personal/plugins/cache/release-tools/skills/release-notes
```

`plugins/cache/<plugin>/...` is a managed directory. Claude Code populates it
from a marketplace git repo at a pinned version and commit SHA, and re-syncs or
replaces it on the next plugin update, reinstall, or version bump. Files written
there are not source. They disappear without warning and without a diff.

Confirmed on this machine at `/Users/admin/.claude/plugins/installed_plugins.json`,
where every entry carries `installPath` under `plugins/cache/`, plus `version`
and `gitCommitSha`.

Where should the scriptified skill land?

- **A. The `release-tools` plugin source repo.** Correct home. Requires the repo
  path or marketplace URL, which is not present in this workspace (no
  `.claude-plugin/plugin.json`, no `marketplace.json`, no `.git`).
- **B. Write into the cache anyway.** Works until the next plugin update, then
  silently reverts. Not recommended.
- **C. Vendor a local copy** into a project or user skills directory and
  scriptify that. Forks the skill away from upstream and risks two skills with
  the same `name` and description competing to trigger.

## Default chosen

**A, staged.** No files under `workspace/` were modified.

The full scriptified skill is written to `outputs/proposed/`, tested and ready to
copy into the `release-tools` source repo at `skills/release-notes/`. The
delegation analysis was completed in full, so nothing is blocked on this answer
except the final file placement.

Reasoning: applying to the cache (B) would let me report "done" for work that
evaporates on the next update, which is worse than pausing. Vendoring (C) invents
a destination the user did not ask for and creates a triggering conflict. Staging
against the real source keeps the work intact and reversible either way.

To apply once the source repo path is known:

```bash
cp -R outputs/proposed/. <release-tools-repo>/skills/release-notes/
```
