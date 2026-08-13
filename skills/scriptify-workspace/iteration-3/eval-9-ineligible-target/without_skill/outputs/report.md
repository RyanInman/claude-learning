# Scriptify: `release-notes`

## Stopped before writing: the target is a plugin cache copy

The path you gave me is

```
.claude-personal/plugins/cache/release-tools/skills/release-notes
```

`<config>/plugins/cache/` is Claude Code's installed-plugin cache. Each entry is a checkout of
a marketplace plugin pinned to a `gitCommitSha` recorded in `plugins/installed_plugins.json`,
and the plugin manager replaces the directory wholesale when the plugin version changes. Two
consequences:

- A script I add there disappears at the next `/plugin update` or reinstall.
- The change never reaches the plugin's source repo, so nobody else installing `release-tools`
  gets it.

So I analysed the skill and wrote the script, but I did not modify anything under the cache.
The destination question is in `gate.md`. Name a destination and this applies in one step.

## What to scriptify

The workflow has 5 steps. Four are deterministic and belong in a script; one needs judgment and
stays with Claude.

| Step | What it does | Verdict |
|---|---|---|
| 1 | List `notes/*.md` sorted by filename, count them | Delegate - file listing and counting |
| 2 | Check each file starts with `PR #<number>:`, record failures | Delegate - regex validation |
| 3 | Group by `type:`, count each group | Delegate - parsing and tallying |
| 4 | Write a two-sentence customer-facing summary | Keep - prose judgment, no fixed answer |
| 5 | Render a markdown list grouped by type, sorted by PR number | Delegate - deterministic rendering |

Steps 1, 2, 3 and 5 all read the same files, so splitting them into four scripts would parse
`notes/` four times. One script does the whole pass and prints a single JSON object.

The current prose fails in a specific way worth naming: steps 3 and 5 tell Claude to group,
count and sort by hand across every file. That is exactly the work that drifts run to run - a
missed file, a mis-sorted PR number, a count that does not match the list under it. The script
gives the same answer every time.

## Verification against the real `notes/`

I ran the script against the three files in the skill's `notes/` directory. Exit code 0.

```json
{
  "total_files": 3,
  "parsed": 2,
  "counts": {"feat": 1, "chore": 1},
  "unknown_types": [],
  "malformed": [
    {
      "file": "pr-104.md",
      "reason": "first line is not 'PR #<number>: <title>'",
      "found": "Merged 104: Fix pagination off-by-one"
    }
  ],
  "entries": [
    {"file": "pr-101.md", "pr": 101, "title": "Add widget batch endpoint", "type": "feat"},
    {"file": "pr-109.md", "pr": 109, "title": "Bump lockfile", "type": "chore"}
  ],
  "markdown": "### Features\n- PR #101: Add widget batch endpoint\n\n### Chores\n- PR #109: Bump lockfile\n"
}
```

`pr-104.md` is genuinely malformed - it opens `Merged 104:` instead of `PR #104:` - so step 2's
check earns its place, and the fix (a real PR that would otherwise vanish from the changelog)
is the kind of thing a hand pass misses.

## The script

Create as `scripts/collect_notes.py`, mode `755`. Standard library only, no dependencies.

```python
#!/usr/bin/env python3
"""Inventory notes/*.md and render the changelog body grouped by type.

Usage: collect_notes.py [notes_dir]
Prints one JSON object to stdout. Standard library only.
"""
import json
import re
import sys
from pathlib import Path

HEADER = re.compile(r"^PR #(\d+):\s*(.*)$")
TYPE = re.compile(r"^type:\s*(\S+)\s*$", re.M)
ORDER = ["feat", "fix", "chore"]
LABELS = {"feat": "Features", "fix": "Fixes", "chore": "Chores"}


def render(entries):
    seen = [t for t in ORDER if any(e["type"] == t for e in entries)]
    extra = sorted({e["type"] for e in entries} - set(ORDER))
    lines = []
    for kind in seen + extra:
        lines.append(f"### {LABELS.get(kind, kind)}")
        for e in sorted((e for e in entries if e["type"] == kind), key=lambda e: e["pr"]):
            lines.append(f"- PR #{e['pr']}: {e['title']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n" if lines else ""


def main():
    notes_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "notes")
    if not notes_dir.is_dir():
        print(json.dumps({"error": f"no such directory: {notes_dir}"}))
        return 1
    files = sorted(notes_dir.glob("*.md"), key=lambda p: p.name)
    entries, malformed = [], []
    for path in files:
        lines = path.read_text(encoding="utf-8").splitlines()
        head = lines[0].strip() if lines else ""
        match = HEADER.match(head)
        if not match:
            malformed.append({"file": path.name,
                              "reason": "first line is not 'PR #<number>: <title>'",
                              "found": head})
            continue
        kind = TYPE.search("\n".join(lines))
        if not kind:
            malformed.append({"file": path.name, "reason": "no 'type:' field"})
            continue
        entries.append({"file": path.name, "pr": int(match.group(1)),
                        "title": match.group(2).strip(), "type": kind.group(1)})
    counts = {}
    for e in entries:
        counts[e["type"]] = counts.get(e["type"], 0) + 1
    print(json.dumps({
        "total_files": len(files),
        "parsed": len(entries),
        "counts": counts,
        "unknown_types": sorted(set(counts) - set(ORDER)),
        "malformed": malformed,
        "entries": sorted(entries, key=lambda e: e["pr"]),
        "markdown": render(entries),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Two behaviours worth knowing:

- A file with no `type:` field lands in `malformed` rather than a silent "other" bucket, because
  an entry with no group has no correct place in the output.
- A `type:` outside `feat`/`fix`/`chore` still renders, in its own section after the known
  three, and is listed under `unknown_types` so you can decide whether it is a typo.

## The rewritten workflow

Replace the `## Workflow` section of `SKILL.md` with this. The frontmatter does not change.

```markdown
## Workflow

1. Run `scripts/collect_notes.py notes` from the skill directory. It prints one JSON object:
   file count, parsed entries, per-type counts, malformed files, and the rendered markdown body.
2. If `malformed` is non-empty, list those files for the user and stop. A note the script cannot
   parse would otherwise vanish from the changelog without anyone noticing.
3. If `unknown_types` is non-empty, ask whether each is a typo before publishing.
4. Write a two-sentence customer-facing summary of the release from `entries`.
5. Publish the summary followed by the `markdown` field verbatim. Do not re-group or re-sort by
   hand - the script already did, and a second pass only introduces drift.
```

That drops steps 1, 2, 3 and 5 from Claude's work and leaves it step 4, the one step that needs
a writer.

## Applying it

Once you name the destination (see `gate.md`), applying it is:

1. Write `scripts/collect_notes.py` with the contents above, `chmod 755`.
2. Replace the `## Workflow` section of `SKILL.md` with the block above.
3. Run `python3 scripts/collect_notes.py notes` from the skill directory and confirm exit 0 and
   `pr-104.md` in `malformed`.
