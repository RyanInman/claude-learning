#!/usr/bin/env python3
"""Score each finding's refactor effort into low / medium / high.

Effort drives model choice: low -> haiku, medium -> sonnet, high -> opus (after
asking the user, because Opus costs more). Estimating before any edit lets the
skill spend the cheapest model that can plausibly do each job.

Signals (all deterministic, computed from the finding plus a git grep):
  - has_fix_example   a local corrected snippet is provided -> cheaper
  - snippet_lines     lines in code_snippet; long snippets are riskier
  - blast_radius      git grep count of the touched symbol across the repo
  - exported          snippet declares an exported/public symbol or signature
  - cross_file        issue/fix wording implies a shared/extracted change
  - has_nearby_test   a test file references the target file -> safer to verify

Rules (see references/effort-rubric.md for the why):
  high   if cross_file OR blast_radius >= 10 OR (exported AND no fix_example)
  low    if has_fix_example AND snippet_lines <= 3 AND blast_radius <= 1
         AND not cross_file AND not exported
  medium otherwise

Input:  canonical findings.json (from load_findings.py)
Output: same JSON with per-finding "effort", "model", "signals" added.
"""

import argparse
import json
import os
import re
import subprocess
import sys

MODEL = {"low": "haiku", "medium": "sonnet", "high": "opus"}
# Phrases that genuinely imply a multi-file / repo-wide change. Matched with word
# boundaries so "fall through" doesn't trip "all" and "shared across calls"
# (a within-function description) doesn't trip a bare "shared".
CROSS_PAT = re.compile(
    r"\b(across all|across the codebase|across the repo|across modules|"
    r"every (public|handler|function|module)|all (handlers|modules|public|callers)|"
    r"throughout|introduce a shared|consolidate|each handler)\b")
# explicit public surface only; a bare `def` isn't necessarily public and
# blast_radius already captures how widely the symbol is used.
EXPORT_PAT = re.compile(r"\b(export|public)\b")
# data/report files mention symbols but aren't code call sites — keep them out
# of the blast-radius count.
BLAST_EXCLUDE = [":!*test*", ":!*spec*", ":!*/tests/*", ":!*.json", ":!*.md",
                 ":!*.txt", ":!*.lock", ":!*.yaml", ":!*.yml", ":!.refactor/*",
                 ":!reports/*"]
# plausible code identifier, longest one wins as the "touched symbol"
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")


def pick_symbol(snippet):
    idents = IDENT.findall(snippet or "")
    skip = {"const", "return", "await", "this", "self", "import", "from", "function",
            "class", "public", "private", "export", "default", "null", "None", "True", "False"}
    cands = [w for w in idents if w not in skip]
    return max(cands, key=len) if cands else None


def blast_radius(symbol, root):
    """Production call sites of the symbol. Test/spec references are excluded:
    a test naming the symbol verifies the fix, it doesn't widen the change's
    risk, so counting it would wrongly inflate effort."""
    if not symbol:
        return 0
    try:
        out = subprocess.run(["git", "grep", "-w", "-I", "--count", symbol, "--", *BLAST_EXCLUDE],
                             cwd=root, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return 0
    return sum(int(line.rsplit(":", 1)[1]) for line in out.stdout.splitlines() if ":" in line)


def has_nearby_test(file, root):
    base = os.path.splitext(os.path.basename(file or ""))[0]
    if not base:
        return False
    try:
        out = subprocess.run(["git", "grep", "-l", "-I", base, "--", "*test*", "*spec*"],
                             cwd=root, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return False
    return bool(out.stdout.strip())


def score(f, root):
    snippet = f.get("code_snippet") or ""
    text = f"{f.get('issue', '')} {f.get('suggested_fix', '')}".lower()
    sig = {
        "has_fix_example": bool(f.get("fix_example")),
        "snippet_lines": len([l for l in snippet.splitlines() if l.strip()]),
        "blast_radius": blast_radius(pick_symbol(snippet), root),
        "exported": bool(EXPORT_PAT.search(snippet)),
        "cross_file": bool(CROSS_PAT.search(text)),
        "has_nearby_test": has_nearby_test(f.get("file"), root),
    }
    if sig["cross_file"] or sig["blast_radius"] >= 10 or (sig["exported"] and not sig["has_fix_example"]):
        effort = "high"
    elif (sig["has_fix_example"] and sig["snippet_lines"] <= 3 and sig["blast_radius"] <= 2
          and not sig["cross_file"] and not sig["exported"]):
        effort = "low"
    else:
        effort = "medium"
    return effort, sig


def main():
    ap = argparse.ArgumentParser(description="Estimate refactor effort per finding.")
    ap.add_argument("findings", help="canonical findings.json from load_findings.py")
    ap.add_argument("--root", default=None, help="repo root (default: findings.json root or cwd)")
    ap.add_argument("--out", default=None, help="output path (default: overwrite input)")
    args = ap.parse_args()

    with open(args.findings, encoding="utf-8") as fh:
        data = json.load(fh)
    root = args.root or data.get("root") or os.getcwd()

    counts = {"low": 0, "medium": 0, "high": 0}
    for f in data["findings"]:
        effort, sig = score(f, root)
        f["effort"] = effort
        f["model"] = MODEL[effort]
        f["signals"] = sig
        counts[effort] += 1

    out_path = args.out or args.findings
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)

    print(json.dumps({"n_findings": len(data["findings"]), "by_effort": counts,
                      "out": out_path}, indent=2))


if __name__ == "__main__":
    main()
