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

## steyle

The house writing guides and the prose grader. The name blends STE (Simplified Technical English) with "style". The same two-copy rule applies:

- **Canonical:** `plugins/steyle/`. Edit here.
- **Installed:** `~/.claude-personal/skills/steyle/`.

```bash
rsync -a --delete --delete-excluded \
  --exclude '__pycache__/' --exclude '.pytest_cache/' \
  --exclude '.DS_Store' --exclude '*-workspace/' \
  ~/claude-learning/plugins/steyle/ ~/.claude-personal/skills/steyle/
```

Delete the older standalone install before the first sync, or Claude Code loads the same skill twice:

```bash
rm -rf ~/.claude-personal/skills/grading-markdown-style
```

The plugin ships one grader. `grading-markdown-style` grades one markdown file, or a whole skill folder in one pass, against `references/universal-writing-style.md` plus at most one of the skill or memory guide. Step 0 of its workflow picks file scope or folder scope. The former `style-guide` skill merged into it on 2026-08-05; its `scripts/scan.py` moved along and now reports universal rule IDs (C1, D2, D3) instead of the retired Rule 3/6/9 numbering.

The steyle copy of `writing-style-guide.md` went with that merge. `plugins/skillit/references/writing-style-guide.md` survives as the only copy, and skillit:create reads it. Do not restore the steyle copy: a plugin cannot resolve a path into another plugin, so two copies drift.

Its eval workspace stays at `skills/grading-markdown-style-workspace/` in the repo root, outside the plugin, per the rule above.
