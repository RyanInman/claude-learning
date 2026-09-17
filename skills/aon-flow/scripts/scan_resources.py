#!/usr/bin/env python3
"""List candidate requirement resources in a repo: specs, tickets, mockups, screenshots.

Usage: python3 scripts/scan_resources.py [repo_root] [--limit N]

Prints one candidate per line as "<group>\t<path>\t<size>\t<modified>", newest first
within each group. Groups: spec, image, plan. Exit 1 when nothing is found.
"""

import argparse
import os
import sys
import time

DIRS = ("resources", "mockups", "docs", "design", "designs", "specs", "spec",
        "requirements", "tickets", "plans")
SPEC_EXT = (".md", ".mdx", ".txt", ".rst")
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif", ".svg")
SKIP_DIRS = {".git", "node_modules", "dist", "build", ".next", "venv", ".venv",
             "__pycache__", "target", "vendor", "coverage"}
SKIP_NAMES = {"CHANGELOG.md", "LICENSE.md", "CODE_OF_CONDUCT.md"}
RECENT_DAYS = 30


def group_of(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in IMAGE_EXT:
        return "image"
    if "plan" in os.path.basename(path).lower() or "plans" in path.lower().split(os.sep):
        return "plan"
    return "spec"


def walk(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            yield os.path.join(dirpath, name)


def collect(root, limit):
    cutoff = time.time() - RECENT_DAYS * 86400
    hits = {}
    for path in walk(root):
        name = os.path.basename(path)
        ext = os.path.splitext(name)[1].lower()
        if name in SKIP_NAMES or ext not in SPEC_EXT + IMAGE_EXT:
            continue
        rel = os.path.relpath(path, root)
        top = rel.split(os.sep)[0]
        try:
            stat = os.stat(path)
        except OSError:
            continue
        in_dir = top in DIRS
        recent = stat.st_mtime >= cutoff
        if not in_dir and not recent:
            continue
        hits[rel] = (group_of(rel), rel, stat.st_size, stat.st_mtime)
    # Round-robin across groups so a folder of images cannot crowd out the specs.
    by_group = {}
    for hit in sorted(hits.values(), key=lambda h: -h[3]):
        by_group.setdefault(hit[0], []).append(hit)
    picked = []
    while len(picked) < limit and any(by_group.values()):
        for group in sorted(by_group):
            if by_group[group] and len(picked) < limit:
                picked.append(by_group[group].pop(0))
    return sorted(picked, key=lambda h: (h[0], -h[3]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--limit", type=int, default=20)
    args = ap.parse_args()

    rows = collect(os.path.abspath(args.root), args.limit)
    if not rows:
        print("no candidates found", file=sys.stderr)
        return 1
    for group, rel, size, mtime in rows:
        stamp = time.strftime("%Y-%m-%d", time.localtime(mtime))
        print(f"{group}\t{rel}\t{size}\t{stamp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
