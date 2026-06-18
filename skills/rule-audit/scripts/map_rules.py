#!/usr/bin/env python3
"""Map .claude/rules/*.md to the source files each rule applies to.

This is the deterministic core of the rule-adherence-review skill. It discovers
rule files, classifies them as global (empty frontmatter) or path-scoped
(`paths:` glob list), resolves which files each rule covers, and emits JSON the
skill uses to fan out one review subagent per batch of files sharing an
identical applicable rule-set.

Usage:
    python3 map_rules.py --mode audit            [--path SUBDIR] [--root DIR]
    python3 map_rules.py --mode staged                          [--root DIR]

Globs follow Claude Code / gitignore semantics (** spans path segments, * stays
within one, {a,b} brace expansion). Paths are relative to --root, which defaults
to the git toplevel. --root lets you point the tool at a self-contained tree
(e.g. the eval fixtures) that carries its own .claude/rules.
"""

import argparse
import json
import os
import re
import subprocess
import sys

# Files that are never worth sending to a review subagent.
SKIP_NAMES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
              "Cargo.lock", "composer.lock", ".DS_Store"}
SKIP_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".pdf",
             ".woff", ".woff2", ".ttf", ".eot", ".zip", ".gz", ".tar", ".lock",
             ".min.js", ".min.css", ".map", ".snap"}
LARGE_UNIVERSE = 150  # warn above this many files in audit mode


def run_git(root, args):
    try:
        out = subprocess.run(["git", "-C", root, *args], capture_output=True,
                             text=True, check=True)
        return out.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def repo_top(root):
    out = run_git(root, ["rev-parse", "--show-toplevel"])
    return out.strip() if out else None


# --- frontmatter parsing -----------------------------------------------------

def parse_paths(text):
    """Return (is_path_scoped, globs). Empty/absent frontmatter -> global.

    Tries PyYAML; falls back to a minimal parser covering the documented forms:
        paths:
          - "glob"
        paths: ["glob", "glob"]
    """
    if not text.startswith("---"):
        return False, []
    end = text.find("\n---", 3)
    if end == -1:
        return False, []
    block = text[3:end].strip()
    if not block:
        return False, []
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(block) or {}
        paths = data.get("paths")
        if paths is None:
            return False, []
        if isinstance(paths, str):
            paths = [paths]
        return True, [str(p) for p in paths]
    except Exception:
        pass
    return _parse_paths_minimal(block)


def _parse_paths_minimal(block):
    lines = block.splitlines()
    globs, in_paths = [], False
    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            continue
        m = re.match(r"^paths:\s*(.*)$", line)
        if m:
            inline = m.group(1).strip()
            if inline.startswith("[") and inline.endswith("]"):
                for part in inline[1:-1].split(","):
                    g = part.strip().strip("\"'")
                    if g:
                        globs.append(g)
                return True, globs
            in_paths = True
            continue
        if in_paths:
            item = re.match(r"^\s*-\s*(.+)$", line)
            if item:
                globs.append(item.group(1).strip().strip("\"'"))
            elif not line.startswith((" ", "\t")):
                in_paths = False  # next top-level key ends the list
    return (True, globs) if (in_paths or globs) else (False, [])


# --- glob matching (gitignore-style) -----------------------------------------

def expand_braces(pattern):
    m = re.search(r"\{([^{}]*)\}", pattern)
    if not m:
        return [pattern]
    pre, post = pattern[:m.start()], pattern[m.end():]
    out = []
    for opt in m.group(1).split(","):
        out.extend(expand_braces(pre + opt + post))
    return out


def glob_to_regex(pattern):
    """Translate one (brace-free) glob to an anchored regex string."""
    pattern = pattern.lstrip("/")
    i, n, out = 0, len(pattern), []
    while i < n:
        c = pattern[i]
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")  # zero or more dirs (the preceding "/" is emitted on its own)
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")        # trailing globstar: everything below, slashes included
            i += 2
        elif c == "*":
            out.append("[^/]*")
            i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    return "^" + "".join(out) + "$"


def compile_globs(globs):
    try:
        import pathspec  # type: ignore
        return ("pathspec", pathspec.PathSpec.from_lines("gitwildmatch", globs))
    except Exception:
        pass
    regexes = []
    for g in globs:
        for ex in expand_braces(g):
            regexes.append(re.compile(glob_to_regex(ex)))
    return ("regex", regexes)


def matches(compiled, path):
    kind, value = compiled
    if kind == "pathspec":
        return value.match_file(path)
    return any(r.match(path) for r in value)


# --- file universe -----------------------------------------------------------

def is_skippable(path):
    if path.startswith(".claude/"):  # config/rules are not review targets
        return True
    base = os.path.basename(path)
    if base in SKIP_NAMES:
        return True
    lower = base.lower()
    return any(lower.endswith(ext) for ext in SKIP_EXTS)


WALK_SKIP_DIRS = {".git", "node_modules", "dist", "build", ".next", "coverage",
                  "__pycache__", ".venv", "venv", ".claude"}


def universe_audit(root, sub):
    git_args = ["ls-files", "--cached", "--others", "--exclude-standard"]
    if sub:
        git_args += ["--", sub]
    out = run_git(root, git_args)
    if out is not None:
        files = [f for f in out.splitlines() if f and not is_skippable(f)]
        return sorted(set(files))
    return _walk_audit(root, sub)  # not a git repo: fall back to a filesystem walk


def _walk_audit(root, sub):
    base = os.path.join(root, sub) if sub else root
    files = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in WALK_SKIP_DIRS]
        for name in filenames:
            rel = os.path.relpath(os.path.join(dirpath, name), root)
            if not is_skippable(rel):
                files.append(rel)
    return sorted(set(files))


def universe_staged(root):
    out = run_git(root, ["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    if out is None:
        return None, "git unavailable"
    top = repo_top(root)
    files = [f for f in out.splitlines() if f]
    # staged paths are repo-top-relative; rebase onto root so globs (root-relative) match.
    if top and os.path.abspath(top) != os.path.abspath(root):
        rel = os.path.relpath(root, top)
        prefix = rel + "/"
        files = [f[len(prefix):] for f in files if f.startswith(prefix)]
    files = [f for f in files if not is_skippable(f)]
    return sorted(set(files)), None


# --- main --------------------------------------------------------------------

def emit(result, out_path):
    """No --out: full JSON to stdout (back-compat). With --out: full JSON to the
    file (render_report.py reads it), compact summary to stdout. The agent only
    needs root/batches/notes to fan out; assignments never enters its context."""
    full = json.dumps(result, indent=2)
    if not out_path:
        print(full)
        return
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(full)
    print(json.dumps({
        "mode": result["mode"],
        "root": result["root"],
        "counts": {
            "rules": len(result["global_rules"]) + len(result["path_scoped_rules"]),
            "files": len(result["assignments"]),
            "unmatched": len(result["unmatched_files"]),
            "batches": len(result["batches"]),
        },
        "batches": result["batches"],
        "notes": result["notes"],
    }, indent=2))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", required=True, choices=["audit", "staged"])
    ap.add_argument("--path", default=None,
                    help="audit mode: narrow the universe to this subdir (relative to root)")
    ap.add_argument("--root", default=None,
                    help="dir containing .claude/rules (default: git toplevel, else cwd)")
    ap.add_argument("--out", default=None,
                    help="write full JSON here and print a compact summary to stdout "
                         "(keeps the per-file assignments array out of the agent's context)")
    args = ap.parse_args()

    root = args.root or repo_top(".") or os.getcwd()
    root = os.path.abspath(root)
    notes = []

    rules_dir = os.path.join(root, ".claude", "rules")
    if not os.path.isdir(rules_dir):
        result = {"mode": args.mode, "root": root, "global_rules": [],
                  "path_scoped_rules": [], "assignments": [], "batches": [],
                  "unmatched_files": [],
                  "notes": [f"No .claude/rules/ found under {root}; nothing to check."]}
        emit(result, args.out)
        return

    global_rules, scoped = [], []  # scoped: [(rule_path, compiled, globs)]
    for name in sorted(os.listdir(rules_dir)):
        if not name.endswith(".md"):
            continue
        rule_path = os.path.join(".claude", "rules", name)
        with open(os.path.join(rules_dir, name), encoding="utf-8") as fh:
            scoped_flag, globs = parse_paths(fh.read())
        if scoped_flag and globs:
            scoped.append((rule_path, compile_globs(globs), globs))
        else:
            global_rules.append(rule_path)
            if scoped_flag and not globs:
                notes.append(f"{rule_path} has an empty paths: list; treating as global.")

    if not global_rules and not scoped:
        notes.append("Rules dir exists but contains no rule files.")

    if args.mode == "staged":
        files, err = universe_staged(root)
        if err:
            notes.append(err)
            files = []
        elif not files:
            notes.append("No staged files (git diff --cached is empty). "
                         "Stage changes or run --mode audit.")
    else:
        files = universe_audit(root, args.path)
        if files is None:
            notes.append("git unavailable; cannot list files.")
            files = []
        elif len(files) > LARGE_UNIVERSE:
            notes.append(f"Audit universe is {len(files)} files; consider --path to narrow "
                         "and cut subagent count.")

    assignments, unmatched = [], []
    matched_scoped = set()
    for f in files:
        rules = list(global_rules)
        for (rp, compiled, _) in scoped:
            if matches(compiled, f):
                rules.append(rp)
                matched_scoped.add(rp)
        if rules:
            assignments.append({"file": f, "rules": rules})
        else:
            unmatched.append(f)

    # A path-scoped rule that matched nothing is a dead rule (or a wrong glob) worth flagging.
    for (rp, _, g) in scoped:
        if rp not in matched_scoped:
            notes.append(f"{rp} (globs {g}) matched no files in scope — dead rule or wrong glob.")

    # Batch files that share an identical applicable rule-set -> one subagent each.
    by_ruleset = {}
    for a in assignments:
        key = tuple(a["rules"])
        by_ruleset.setdefault(key, []).append(a["file"])
    batches = [{"rules": list(k), "files": sorted(v)}
               for k, v in sorted(by_ruleset.items(), key=lambda kv: kv[1])]

    result = {
        "mode": args.mode,
        "root": root,
        "global_rules": global_rules,
        "path_scoped_rules": [{"file": rp, "globs": g} for (rp, _, g) in scoped],
        "assignments": assignments,
        "batches": batches,
        "unmatched_files": unmatched,
        "notes": notes,
    }
    emit(result, args.out)


if __name__ == "__main__":
    main()
