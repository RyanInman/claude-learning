#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Extract commits, per-file stats, and truncated diffs for one branch.

Writes a JSON bundle to --out; prints a compact summary to stdout.

Exit codes:
  0 ok
  2 invalid arguments
  3 not a git repository
  4 ref not found
  5 no merge-base could be determined (pass --base explicitly)
"""
import argparse
import fnmatch
import json
import os
import subprocess
import sys
from collections import Counter

# Files that dominate line counts without carrying implementation signal.
DEFAULT_EXCLUDES = [
    "*.lock", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "Cargo.lock", "poetry.lock", "Gemfile.lock", "composer.lock",
    "*.min.js", "*.min.css", "*.map", "*.snap", "*.pb.go", "*_pb2.py",
    "node_modules/*", "vendor/*", "dist/*", "build/*", "out/*",
    ".idea/*", "*.generated.*",
    ".pattern-mining/*",  # this skill's own workspace must never count as change signal
]
# Per-file diff cap: enough to see structure and key hunks; full patches
# are fetched on demand with `git show`.
MAX_DIFF_LINES_DEFAULT = 120
# Overall diff-line budget so extract.json stays readable in one pass.
TOTAL_DIFF_LINE_BUDGET = 8000
BASE_CANDIDATES = ["origin/main", "main", "origin/master", "master",
                   "origin/develop", "develop"]


def die(code, msg):
    print(msg, file=sys.stderr)
    sys.exit(code)


def git(repo, *args, check=True):
    r = subprocess.run(["git", "-C", repo, *args],
                       capture_output=True, text=True)
    if check and r.returncode != 0:
        return None
    return r.stdout


def excluded(path, patterns):
    return any(fnmatch.fnmatch(path, p) or fnmatch.fnmatch("/" + path, "*/" + p)
               for p in patterns)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", help="path to the git repo (default: .)")
    ap.add_argument("--head", required=True,
                    help="branch name or commit to study")
    ap.add_argument("--base", default=None,
                    help="base ref; default: merge-base of --head with the "
                         "first existing ref among " + ", ".join(BASE_CANDIDATES))
    ap.add_argument("--out", required=True, help="path for the JSON bundle")
    ap.add_argument("--max-diff-lines", type=int, default=MAX_DIFF_LINES_DEFAULT,
                    help="per-file diff truncation (default %(default)s)")
    ap.add_argument("--include-generated", action="store_true",
                    help="keep lockfiles/vendored/generated files (excluded by default)")
    a = ap.parse_args()

    if git(a.repo, "rev-parse", "--git-dir") is None:
        die(3, f"'{a.repo}' is not a git repository (or git is unavailable). "
               "Pass --repo pointing at the repo root.")
    if git(a.repo, "rev-parse", "--verify", a.head + "^{commit}") is None:
        branches = (git(a.repo, "branch", "-a", "--format=%(refname:short)") or "")
        sample = ", ".join(branches.split()[:15])
        die(4, f"Ref '{a.head}' not found. Known refs include: {sample}. "
               "For a squash-merged branch pass the merge commit SHA as --head.")

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

    excludes = [] if a.include_generated else DEFAULT_EXCLUDES
    rng = f"{base}..{a.head}"

    # Commits with per-commit numstat.
    raw = git(a.repo, "log", "--no-merges", "--reverse",
              "--format=%x01%h%x02%an%x02%ad%x02%s", "--date=short",
              "--numstat", rng) or ""
    commits, cur = [], None
    for line in raw.splitlines():
        if line.startswith("\x01"):
            h, an, ad, s = line[1:].split("\x02", 3)
            cur = {"sha": h, "author": an, "date": ad, "subject": s, "files": []}
            commits.append(cur)
        elif line.strip() and cur is not None:
            parts = line.split("\t")
            if len(parts) == 3:
                add, rm, path = parts
                if excluded(path, excludes):
                    continue
                cur["files"].append({
                    "path": path,
                    "additions": None if add == "-" else int(add),
                    "deletions": None if rm == "-" else int(rm),
                })

    # Overall changed files (three-dot: changes introduced by the branch).
    ns = git(a.repo, "diff", "--numstat", f"{base}...{a.head}") or ""
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

    # Directory histogram (depth 2).
    dir_hist = Counter()
    for f in files:
        parts = f["path"].split("/")
        dir_hist["/".join(parts[:2]) if len(parts) > 2 else
                 (parts[0] if len(parts) > 1 else "(root)")] += 1

    # Truncated per-file diffs under a global budget, biggest files first.
    budget = TOTAL_DIFF_LINE_BUDGET
    diffs = {}
    ordered = sorted(files, key=lambda f: (f["additions"] or 0) + (f["deletions"] or 0),
                     reverse=True)
    for f in ordered:
        if budget <= 0:
            diffs[f["path"]] = "[omitted: total diff budget exhausted — use git show]"
            continue
        d = git(a.repo, "diff", f"{base}...{a.head}", "--", f["path"])
        if d is None:
            diffs[f["path"]] = (f"[error: git diff failed for this path — run: "
                                f"git diff {base}...{a.head} -- {f['path']}]")
            continue
        lines = d.splitlines()
        take = min(len(lines), a.max_diff_lines, budget)
        text = "\n".join(lines[:take])
        if take < len(lines):
            text += f"\n[truncated {len(lines) - take} lines — run: git show/diff -- {f['path']}]"
        diffs[f["path"]] = text
        budget -= take

    bundle = {
        "repo": os.path.abspath(a.repo),
        "head": a.head, "base": base,
        "excludes_applied": excludes, "excluded_file_count": skipped,
        "commit_count": len(commits), "file_count": len(files),
        "commits": commits, "files": files,
        "directory_histogram": dir_hist.most_common(),
        "diffs_truncated_per_file_lines": a.max_diff_lines,
        "diffs": diffs,
    }
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(bundle, fh, indent=1)

    print(json.dumps({
        "out": a.out, "head": a.head, "base": base,
        "commits": len(commits), "files": len(files),
        "excluded_files": skipped,
        "top_directories": dir_hist.most_common(8),
    }, indent=1))


if __name__ == "__main__":
    main()
