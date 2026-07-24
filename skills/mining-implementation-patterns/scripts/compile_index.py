#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Aggregate all studied branches into index.json for the compile step.

Reads every branches/*/extract.json and the frontmatter of every
branches/*/analysis.md. Computes directory touch frequency, files touched
in multiple branches, source<->test pairing rate, and pattern-ID
recurrence across branches.

Exit codes:
  0 ok
  3 workspace directory missing
  4 no studied branches found under <workspace>/branches
"""
import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

TEST_MARKERS = re.compile(
    r"(\.spec\.|\.test\.|_test\.|Tests?\.|/tests?/|/__tests__/)", re.I)


def die(code, msg):
    print(msg, file=sys.stderr)
    sys.exit(code)


def parse_frontmatter(path):
    """Minimal reader for the constrained frontmatter defined in
    references/analysis-guide.md. Two-space indents, one value per line."""
    meta = {"patterns": []}
    try:
        text = open(path).read()
    except OSError:
        return meta
    text = text.lstrip("\ufeff\r\n")  # tolerate BOM / leading blank lines
    m = re.match(r"---\r?\n(.*?)\r?\n---", text, re.S)
    if not m:
        return meta
    cur = None
    for line in m.group(1).splitlines():
        pm = re.match(r"\s*-\s+id:\s*(.+)", line)
        if pm:
            cur = {"id": pm.group(1).strip()}
            meta["patterns"].append(cur)
            continue
        kv = re.match(r"(\s*)([A-Za-z_]+):\s*(.*)", line)
        if not kv:
            continue
        indent, key, val = kv.groups()
        val = val.strip()
        if indent and cur is not None:
            if key == "evidence":
                cur[key] = [s.strip() for s in val.strip("[]").split(",") if s.strip()]
            else:
                cur[key] = val
        elif not indent and key != "patterns":
            meta[key] = val
    return meta


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", default=".pattern-mining",
                    help="workspace dir (default: .pattern-mining)")
    ap.add_argument("--out", default=None,
                    help="output path (default: <workspace>/index.json)")
    a = ap.parse_args()

    if not os.path.isdir(a.workspace):
        die(3, f"Workspace '{a.workspace}' does not exist. Run a learn pass "
               "first (see SKILL.md, Learn mode).")
    bdir = os.path.join(a.workspace, "branches")
    slugs = sorted(d for d in (os.listdir(bdir) if os.path.isdir(bdir) else [])
                   if os.path.isdir(os.path.join(bdir, d)))
    if not slugs:
        die(4, f"No studied branches under {bdir}. Each learn pass creates "
               "branches/<slug>/ with extract.json and analysis.md.")

    dir_branch_counts = Counter()      # directory -> number of branches touching it
    file_branch_counts = Counter()     # file -> number of branches touching it
    branches, warnings = [], []
    patterns = defaultdict(lambda: {"branches": [], "claims": [], "scopes": set(),
                                    "confidences": []})
    pair_hits = pair_total = 0

    for slug in slugs:
        ex_path = os.path.join(bdir, slug, "extract.json")
        an_path = os.path.join(bdir, slug, "analysis.md")
        entry = {"slug": slug, "has_extract": os.path.exists(ex_path),
                 "has_analysis": os.path.exists(an_path)}
        if entry["has_extract"]:
            ex = json.load(open(ex_path))
            entry.update(head=ex.get("head"), commits=ex.get("commit_count"),
                         files=ex.get("file_count"))
            for d, _n in ex.get("directory_histogram", []):
                dir_branch_counts[d] += 1
            paths = [f["path"] for f in ex.get("files", [])]
            for p in paths:
                file_branch_counts[p] += 1
            src = [p for p in paths if not TEST_MARKERS.search(p)]
            tst = [p for p in paths if TEST_MARKERS.search(p)]
            stems = {re.sub(r"\.[^.]+$", "", os.path.basename(t)).lower()
                     .replace(".spec", "").replace(".test", "").replace("_test", "")
                     for t in tst}
            for s in src:
                pair_total += 1
                if re.sub(r"\.[^.]+$", "", os.path.basename(s)).lower() in stems:
                    pair_hits += 1
        else:
            warnings.append(f"{slug}: extract.json missing — rerun extract_branch.py")
        if entry["has_analysis"]:
            meta = parse_frontmatter(an_path)
            entry["ticket"] = meta.get("ticket")
            if not meta["patterns"]:
                warnings.append(f"{slug}: analysis.md present but zero patterns "
                                "parsed — check frontmatter against "
                                "references/analysis-guide.md §3")
            for p in meta["patterns"]:
                pid = p.get("id", "(missing-id)")
                rec = patterns[pid]
                rec["branches"].append(slug)
                if p.get("claim"):
                    rec["claims"].append(p["claim"])
                if p.get("scope"):
                    rec["scopes"].add(p["scope"])
                rec["confidences"].append(p.get("confidence", "medium"))
        else:
            warnings.append(f"{slug}: analysis.md missing — learn pass incomplete")
        branches.append(entry)

    pattern_rows = []
    for pid, rec in sorted(patterns.items(),
                           key=lambda kv: -len(kv[1]["branches"])):
        n = len(set(rec["branches"]))
        # Promotion contract (references/output-templates.md §1): high/medium
        # recurrence in >=2 branches promotes; low sightings don't count but
        # don't veto either.
        non_low = {b for b, c in zip(rec["branches"], rec["confidences"])
                   if c != "low"}
        eligible = len(non_low) >= 2
        contradicted = pid.endswith("-violated") or (pid + "-violated") in patterns
        pattern_rows.append({
            "id": pid, "branch_count": n,
            "branches": sorted(set(rec["branches"])),
            "scopes": sorted(rec["scopes"]),
            "confidences": rec["confidences"],
            "claims": rec["claims"][:3],
            "promotion_eligible": eligible and not contradicted,
            "contradicted": contradicted,
        })

    index = {
        "branch_count": len(branches),
        "branches": branches,
        "directories_by_branch_count": dir_branch_counts.most_common(),
        "files_in_multiple_branches": sorted(
            [f for f, c in file_branch_counts.items() if c >= 2],
            key=lambda f: -file_branch_counts[f])[:50],
        "source_test_pairing_rate": round(pair_hits / pair_total, 2) if pair_total else None,
        "patterns": pattern_rows,
        "warnings": warnings,
    }
    out = a.out or os.path.join(a.workspace, "index.json")
    with open(out, "w") as fh:
        json.dump(index, fh, indent=1)

    print(json.dumps({
        "out": out, "branches": len(branches),
        "patterns_total": len(pattern_rows),
        "patterns_promotion_eligible": sum(1 for p in pattern_rows
                                           if p["promotion_eligible"]),
        "warnings": warnings,
    }, indent=1))


if __name__ == "__main__":
    main()
