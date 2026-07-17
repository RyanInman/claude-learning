#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Scan a path's current code, or a diff/branch's changes, for reverse-
engineering a spec: inventories files, extracts language-agnostic signatures
(functions, classes, routes), flags validation/error-handling signals, and
pairs source files with their tests.

Modes (choose by which flags are set):
  Snapshot  --target <path>              inventories <path> at the working tree
  Diff      --head <ref> [--base <ref>]  inventories what --head changed vs --base
            (add --target to scope either mode to a subtree)

Writes a JSON bundle to --out; prints a compact summary to stdout.

Exit codes:
  0 ok
  2 invalid arguments (need --target and/or --head)
  3 not a git repository
  4 target path or ref not found
  5 no merge-base could be determined (pass --base explicitly, diff mode)
  6 nothing matched the target/filters -- nothing to scan
"""
import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys

# Files that dominate signature/line counts without carrying behavior signal.
DEFAULT_EXCLUDES = [
    "*.lock", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "Cargo.lock", "poetry.lock", "Gemfile.lock", "composer.lock",
    "*.min.js", "*.min.css", "*.map", "*.snap", "*.pb.go", "*_pb2.py",
    "node_modules/*", "vendor/*", "dist/*", "build/*", "out/*",
    ".idea/*", "*.generated.*",
]
TEST_MARKERS = re.compile(r"(\.spec\.|\.test\.|_test\.|Tests?\.|/tests?/|/__tests__/)", re.I)

# Keyword scan for validation/error-handling/edge-case signals. Heuristic,
# not a parser -- it points at lines worth reading, not a verified fact.
BEHAVIOR_KEYWORDS = [
    "raise ", "raise(", "throw ", "throw(", "Error(", "assert ", "assert(",
    "validate", "required", "must not", "if not ", "guard", "panic(",
    ".should", "expect(", "ValidationError", "PermissionError",
    "Unauthorized", "Forbidden", "NotFound",
]

# Per-language signature patterns: (kind, regex, name(match) -> str).
# Heuristic and regex-based by design -- fast and dependency-free across any
# language, at the cost of missing exotic syntax. SKILL.md tells Claude to
# verify by reading the file when a signature or excerpt looks incomplete.
_JS_PATTERNS = [
    ("function", re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+(\w+)"),
     lambda m: m.group(1)),
    ("class", re.compile(r"^\s*(?:export\s+)?class\s+(\w+)"), lambda m: m.group(1)),
    ("arrow-fn", re.compile(r"^\s*(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\("),
     lambda m: m.group(1)),
]
SIGNATURE_PATTERNS = {
    ".py": [("function", re.compile(r"^\s*(?:async\s+)?def\s+(\w+)"), lambda m: m.group(1)),
            ("class", re.compile(r"^\s*class\s+(\w+)"), lambda m: m.group(1))],
    ".rb": [("function", re.compile(r"^\s*def\s+(\w+)"), lambda m: m.group(1)),
            ("class", re.compile(r"^\s*class\s+(\w+)"), lambda m: m.group(1))],
    ".go": [("function", re.compile(r"^func\s+(?:\([^)]*\)\s*)?(\w+)"), lambda m: m.group(1))],
    ".java": [("method", re.compile(r"^\s*(?:public|private|protected)\s+[\w<>\[\],\s]+?\s(\w+)\s*\("),
              lambda m: m.group(1))],
    ".cs": [("method", re.compile(r"^\s*(?:public|private|protected|internal)\s+[\w<>\[\],\s]+?\s(\w+)\s*\("),
            lambda m: m.group(1))],
    ".js": _JS_PATTERNS, ".jsx": _JS_PATTERNS, ".ts": _JS_PATTERNS, ".tsx": _JS_PATTERNS,
}
# Route/endpoint calls, checked on every file regardless of extension --
# router.get(...)/app.post(...) style call routing looks the same across
# most web frameworks and languages. The path is required to start with
# "/" -- without it, this also matches the extremely common dict/config
# lookup idiom `app.get('timeout', 30)`, mislabeling it as an HTTP route.
ROUTE_CALL = re.compile(r"(?i)\b(?:router|app|api)\.(get|post|put|patch|delete)\(\s*['\"](/[^'\"]*)")
# Ruby/Sinatra-style block routing: get '/path' do
ROUTE_BLOCK = re.compile(r"(?i)^\s*(get|post|put|patch|delete)\s+['\"](/[^'\"]*)['\"]\s+do\b")
# Flask/classic-decorator style: @app.route('/path', methods=[...])
ROUTE_DECORATOR = re.compile(r"(?i)^\s*@(?:app|router|api)\.route\(\s*['\"](/[^'\"]*)")

MAX_EXCERPT_LINES_DEFAULT = 15
MAX_SIGNATURES_PER_FILE = 80  # generous for real files; excludes filter out the rest
MAX_SIGNAL_HITS_DEFAULT = 20
MAX_DIFF_LINES_PER_FILE = 120
TOTAL_DIFF_LINE_BUDGET = 8000
BASE_CANDIDATES = ["origin/main", "main", "origin/master", "master",
                   "origin/develop", "develop"]


def die(code, msg):
    print(msg, file=sys.stderr)
    sys.exit(code)


def git(repo, *args, check=True):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        return None
    return r.stdout


def excluded(path, patterns):
    return any(fnmatch.fnmatch(path, p) or fnmatch.fnmatch("/" + path, "*/" + p)
               for p in patterns)


def list_snapshot_files(repo, target, excludes):
    tracked = git(repo, "ls-files", "--", target) or ""
    untracked = git(repo, "ls-files", "--others", "--exclude-standard", "--", target) or ""
    paths = sorted(set(tracked.splitlines()) | set(untracked.splitlines()))
    return [p for p in paths if not excluded(p, excludes)]


def list_diff_files(repo, base, head, target, excludes):
    args = ["diff", "--numstat", f"{base}...{head}"]
    if target:
        args += ["--", target]
    ns = git(repo, *args) or ""
    files, skipped = [], 0
    for line in ns.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        add, rm, path = parts
        if excluded(path, excludes):
            skipped += 1
            continue
        files.append({"path": path,
                      "additions": None if add == "-" else int(add),
                      "deletions": None if rm == "-" else int(rm)})
    return files, skipped


def read_lines(repo, path, ref=None):
    if ref is None:
        try:
            with open(os.path.join(repo, path), encoding="utf-8", errors="replace") as fh:
                return fh.read().splitlines()
        except OSError:
            return None
    text = git(repo, "show", f"{ref}:{path}", check=False)
    return text.splitlines() if text is not None else None


def extract_signatures(lines, ext, max_excerpt):
    patterns = list(SIGNATURE_PATTERNS.get(ext, []))
    sigs = []
    truncated = False
    for i, line in enumerate(lines):
        if len(sigs) >= MAX_SIGNATURES_PER_FILE:
            truncated = True
            break
        found = None
        for kind, pat, name_fn in patterns:
            m = pat.search(line)
            if m:
                found = (kind, name_fn(m))
                break
        if not found:
            m = ROUTE_CALL.search(line) or ROUTE_BLOCK.search(line)
            if m:
                found = ("route", f"{m.group(1).upper()} {m.group(2)}")
            else:
                m = ROUTE_DECORATOR.search(line)
                if m:
                    found = ("route", f"ROUTE {m.group(1)}")
        if not found:
            continue
        kind, name = found
        excerpt_lines = lines[i:i + max_excerpt]
        excerpt = "\n".join(excerpt_lines)
        if len(lines) - i > max_excerpt:
            excerpt += f"\n[truncated {len(lines) - i - max_excerpt} lines]"
        sigs.append({"kind": kind, "name": name, "line": i + 1, "excerpt": excerpt})
    return sigs, truncated


def extract_signals(lines, max_hits):
    hits = []
    for i, line in enumerate(lines):
        if len(hits) >= max_hits:
            break
        low = line.lower()
        for kw in BEHAVIOR_KEYWORDS:
            if kw.lower() in low:
                hits.append({"keyword": kw.strip("( "), "line": i + 1, "text": line.strip()[:200]})
                break
    return hits


def pair_tests(repo, paths, ref=None):
    if ref is None:
        tracked = (git(repo, "ls-files") or "").splitlines()
        untracked = (git(repo, "ls-files", "--others", "--exclude-standard") or "").splitlines()
        all_files = tracked + untracked
    else:
        all_files = (git(repo, "ls-tree", "-r", "--name-only", ref) or "").splitlines()
    test_files = [p for p in all_files if TEST_MARKERS.search(p)]
    stem_index = {}
    for t in test_files:
        stem = re.sub(r"\.[^.]+$", "", os.path.basename(t)).lower()
        stem = re.sub(r"(\.spec|\.test|_test)$", "", stem)  # foo.test.ts, foo_test.go
        stem = re.sub(r"^test_", "", stem)                  # pytest's test_foo.py
        stem_index.setdefault(stem, []).append(t)
    pairs = {}
    for p in paths:
        if TEST_MARKERS.search(p):
            continue
        stem = re.sub(r"\.[^.]+$", "", os.path.basename(p)).lower()
        matches = stem_index.get(stem)
        pairs[p] = matches[0] if matches else None
    return pairs


def build_diffs(repo, base, head, diff_meta):
    ordered = sorted(diff_meta.values(),
                     key=lambda f: (f["additions"] or 0) + (f["deletions"] or 0), reverse=True)
    diffs = {}
    budget = TOTAL_DIFF_LINE_BUDGET
    for f in ordered:
        path = f["path"]
        if budget <= 0:
            diffs[path] = "[omitted: total diff budget exhausted -- use git show]"
            continue
        d = git(repo, "diff", f"{base}...{head}", "--", path)
        if d is None:
            diffs[path] = f"[error: git diff failed -- run: git diff {base}...{head} -- {path}]"
            continue
        lines = d.splitlines()
        take = min(len(lines), MAX_DIFF_LINES_PER_FILE, budget)
        text = "\n".join(lines[:take])
        if take < len(lines):
            text += f"\n[truncated {len(lines) - take} lines -- run: git show/diff -- {path}]"
        diffs[path] = text
        budget -= take
    return diffs


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", help="path to the git repo (default: .)")
    ap.add_argument("--target", default=None,
                    help="file or directory (relative to --repo) to scope to -- "
                         "required for snapshot mode, optional scope for diff mode")
    ap.add_argument("--head", default=None,
                    help="branch/commit to diff; presence of this selects diff mode")
    ap.add_argument("--base", default=None,
                    help="base ref for diff mode; default: merge-base with the first "
                         "existing ref among " + ", ".join(BASE_CANDIDATES))
    ap.add_argument("--out", required=True, help="path for the JSON bundle")
    ap.add_argument("--max-excerpt-lines", type=int, default=MAX_EXCERPT_LINES_DEFAULT,
                    help="lines of context kept per signature (default %(default)s)")
    ap.add_argument("--max-signal-hits", type=int, default=MAX_SIGNAL_HITS_DEFAULT,
                    help="behavior-signal hits kept per file (default %(default)s)")
    ap.add_argument("--include-generated", action="store_true",
                    help="keep lockfiles/vendored/generated files (excluded by default)")
    a = ap.parse_args()

    if not a.target and not a.head:
        die(2, "Provide --target for snapshot mode, or --head for diff mode "
               "(add --target too to scope the diff to a subtree).")

    if git(a.repo, "rev-parse", "--git-dir") is None:
        die(3, f"'{a.repo}' is not a git repository (or git is unavailable). "
               "Pass --repo pointing at the repo root.")

    excludes = [] if a.include_generated else DEFAULT_EXCLUDES
    mode = "diff" if a.head else "snapshot"
    base = head = None
    diff_meta = {}

    if mode == "snapshot":
        if not os.path.exists(os.path.join(a.repo, a.target)):
            die(4, f"Target '{a.target}' not found under '{a.repo}'.")
        paths = list_snapshot_files(a.repo, a.target, excludes)
    else:
        if git(a.repo, "rev-parse", "--verify", a.head + "^{commit}") is None:
            branches = (git(a.repo, "branch", "-a", "--format=%(refname:short)") or "")
            sample = ", ".join(branches.split()[:15])
            die(4, f"Ref '{a.head}' not found. Known refs include: {sample}.")
        base = a.base
        if base is None:
            for cand in BASE_CANDIDATES:
                if git(a.repo, "rev-parse", "--verify", cand + "^{commit}") is None:
                    continue
                mb = git(a.repo, "merge-base", cand, a.head)
                if mb:
                    base = mb.strip()
                    break
            if base is None:
                die(5, "Could not determine a merge-base against any of: "
                       + ", ".join(BASE_CANDIDATES)
                       + ". Pass --base <ref> explicitly (e.g. --base <merge-commit>^).")
        else:
            if git(a.repo, "rev-parse", "--verify", base + "^{commit}") is None:
                die(4, f"Base ref '{base}' not found.")
        head = a.head
        diff_files, _skipped = list_diff_files(a.repo, base, head, a.target, excludes)
        diff_meta = {f["path"]: f for f in diff_files}
        paths = list(diff_meta.keys())

    if not paths:
        die(6, "Nothing matched --target/filters -- nothing to scan. "
               "Check the path, ref, or widen --target.")

    ref_for_read = head if mode == "diff" else None
    test_pairs = pair_tests(a.repo, paths, ref=ref_for_read)

    files_out = []
    for p in sorted(paths):
        lines = read_lines(a.repo, p, ref_for_read)
        if lines is None:
            files_out.append({"path": p, "error": "could not read file content"})
            continue
        ext = os.path.splitext(p)[1]
        sigs, sigs_truncated = extract_signatures(lines, ext, a.max_excerpt_lines)
        files_out.append({
            "path": p,
            "is_test": bool(TEST_MARKERS.search(p)),
            "paired_test": test_pairs.get(p),
            "signatures": sigs,
            "signatures_truncated": sigs_truncated,
            "behavior_signals": extract_signals(lines, a.max_signal_hits),
        })

    bundle = {
        "repo": os.path.abspath(a.repo),
        "mode": mode,
        "target": a.target,
        "head": head, "base": base,
        "excludes_applied": excludes,
        "file_count": len(files_out),
        "files": files_out,
    }
    if mode == "diff":
        bundle["diffs_truncated_per_file_lines"] = MAX_DIFF_LINES_PER_FILE
        bundle["diffs"] = build_diffs(a.repo, base, head, diff_meta)

    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(bundle, fh, indent=1)

    print(json.dumps({
        "out": a.out, "mode": mode, "file_count": len(files_out),
        "signatures_found": sum(len(f.get("signatures", [])) for f in files_out),
        "behavior_signals_found": sum(len(f.get("behavior_signals", [])) for f in files_out),
        "tests_paired": sum(1 for v in test_pairs.values() if v),
    }, indent=1))


if __name__ == "__main__":
    main()
