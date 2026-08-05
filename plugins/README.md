# Plugin development notes

Author-side notes for plugins in this repo. Nothing in this file ships with a plugin — installer-facing content belongs inside each plugin folder.

## skillit

Two copies exist on disk:

- **Canonical:** `plugins/skillit/` (this repo copy). Edit here.
- **Installed:** `~/.claude-personal/skills/skillit/`. Claude Code loads skills from here. Never edit this copy directly, because the repo copy would silently drift.

Sync repo → installed after each change:

```bash
rsync -a --delete --delete-excluded \
  --exclude '__pycache__/' --exclude '.pytest_cache/' \
  --exclude '.DS_Store' --exclude '*-workspace/' \
  ~/claude-learning/plugins/skillit/ ~/.claude-personal/skills/skillit/
```

Eval workspaces (`*-workspace/`) never belong inside a plugin's `skills/` folder, because the plugin loader treats every folder there as a skill and the workspace would ship to installers. Put them outside the plugin; `skills/create/references/running-evals.md` states the rule.
