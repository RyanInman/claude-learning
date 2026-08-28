#!/usr/bin/env python3
"""
resolve_target.py - Resolve a style-review target: scope, file list, guide class, guide paths.

READS   the target file or folder, its frontmatter, and the guide directories it searches
WRITES  nothing

USAGE
    python3 scripts/resolve_target.py <target> [--plugin-root DIR] [--json]

    <target>        one .md file, or a folder that holds SKILL.md
    --plugin-root   where the guides live; default is the steyle root two levels
                    above this skill folder. Fallback search: output-styles/,
                    style-guides/, rules/ under the current directory and the
                    git root. Guides match on their H1 title, not on filename.

STDOUT (JSON)
    scope           "file" | "folder"
    files           files the grade covers, relative to target_dir
    target_class    "skill" | "memory" | "other"
    class_reason    one sentence; ambiguous cases say so and name the closer match
    ambiguous       true when Claude must confirm the class (a rules/ path outside .claude/)
    guides          {"universal": path|null, "extra": path|null, "extra_name": "skill"|"memory"|null}
    missing         finding codes: guide_missing_universal, guide_missing_extra

EXIT CODES
    0  Resolved; every needed guide found.
    1  A needed guide is missing (codes under "missing"); ask the user where the guides live.
    2  Usage error, target does not exist, or folder holds no SKILL.md.
    3  Unexpected failure.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TITLES = {
    "universal": "Universal Claude Writing Style Guide",
    "skill": "Skill Writing Style Guide",
    "memory": "Memory and Rules Writing Style Guide",
}
MEMORY_NAMES = {"CLAUDE.md", "CLAUDE.local.md", "AGENTS.md", "MEMORY.md"}
FALLBACK_DIRS = ("output-styles", "style-guides", "rules", "references")
FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
H1 = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def frontmatter_keys(path):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return set()
    m = FRONTMATTER.match(text)
    if not m:
        return set()
    return {ln.split(":", 1)[0].strip() for ln in m.group(1).splitlines() if ":" in ln and not ln.startswith(" ")}


def in_skill_folder(path):
    if path.name == "SKILL.md":
        return True
    if (path.parent / "SKILL.md").is_file():
        return True
    return path.parent.name == "references" and (path.parent.parent / "SKILL.md").is_file()


def classify(target, scope):
    if scope == "folder":
        return "skill", "folder holds SKILL.md, so the skill guide applies", False
    parts = target.parts
    if in_skill_folder(target):
        return "skill", "file is a SKILL.md or sits inside a skill folder", False
    if target.name in MEMORY_NAMES:
        return "memory", f"{target.name} is a memory file", False
    if any(parts[i] == ".claude" and parts[i + 1] == "rules" for i in range(len(parts) - 1)):
        return "memory", "file sits under .claude/rules/, which makes the memory guide mandatory", False
    keys = frontmatter_keys(target)
    if {"name", "description", "type"} <= keys:
        return "memory", "frontmatter carries name, description, and type, the memory-file shape", False
    if "rules" in parts:
        return ("other", "path holds a rules/ directory outside .claude/, so the memory guide is not mandatory; "
                "closer match is 'other' unless the content reads as a rules file", True)
    return "other", "not a skill file and not a memory file", False


def title_of(path):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = H1.search(text)
    return m.group(1) if m else None


def search_dirs(plugin_root):
    dirs = [plugin_root / "output-styles", plugin_root / "references"]
    roots = [Path.cwd()]
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True,
                             text=True, timeout=5)
        if top.returncode == 0:
            roots.append(Path(top.stdout.strip()))
    except (OSError, subprocess.SubprocessError):
        pass
    for r in roots:
        dirs += [r / d for d in FALLBACK_DIRS]
    seen, out = set(), []
    for d in dirs:
        if d.is_dir() and d.resolve() not in seen:
            seen.add(d.resolve())
            out.append(d)
    return out


def find_guides(plugin_root, wanted):
    found = {k: None for k in wanted}
    for d in search_dirs(plugin_root):
        for md in sorted(d.glob("*.md")):
            t = title_of(md)
            for k in wanted:
                if found[k] is None and t == TITLES[k]:
                    found[k] = str(md.resolve())
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("target", help="one .md file, or a folder that holds SKILL.md")
    parser.add_argument("--plugin-root", help="steyle root that holds output-styles/ and references/")
    parser.add_argument("--json", action="store_true", help="accepted for symmetry; output is always JSON")
    args = parser.parse_args(argv)

    target = Path(args.target).expanduser().resolve()
    if target.is_dir():
        if not (target / "SKILL.md").is_file():
            print(f"error: no SKILL.md in {target}", file=sys.stderr)
            return 2
        scope, target_dir = "folder", target
        files = ["SKILL.md"] + [str(p.relative_to(target)) for p in sorted((target / "references").rglob("*.md"))
                                if (target / "references").is_dir()]
    elif target.is_file():
        if target.suffix.lower() != ".md":
            print(f"error: not a markdown file: {target}", file=sys.stderr)
            return 2
        scope, target_dir, files = "file", target.parent, [target.name]
    else:
        print(f"error: no such file or folder: {target}", file=sys.stderr)
        return 2

    klass, reason, ambiguous = classify(target, scope)
    plugin_root = Path(args.plugin_root).expanduser().resolve() if args.plugin_root \
        else Path(__file__).resolve().parent.parent.parent.parent
    extra_name = {"skill": "skill", "memory": "memory"}.get(klass)
    wanted = ["universal"] + ([extra_name] if extra_name else [])
    found = find_guides(plugin_root, wanted)

    missing = []
    if found["universal"] is None:
        missing.append("guide_missing_universal")
    if extra_name and found[extra_name] is None:
        missing.append("guide_missing_extra")

    result = {
        "target": str(target), "target_dir": str(target_dir), "scope": scope, "files": files,
        "target_class": klass, "class_reason": reason, "ambiguous": ambiguous,
        "plugin_root": str(plugin_root),
        "guides": {"universal": found["universal"],
                   "extra": found.get(extra_name) if extra_name else None,
                   "extra_name": extra_name},
        "missing": missing,
    }
    print(json.dumps(result, indent=2))
    return 1 if missing else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # predictable errors already returned 2 above
        print(f"unexpected failure: {e}", file=sys.stderr)
        sys.exit(3)
