#!/usr/bin/env python3
"""Normalize an audit report into a canonical findings list for refactoring.

Accepts three input shapes and emits one stable schema so the rest of the skill
never has to care where the report came from:

  1. A rule-audit working dir holding `batch-*.json` files
     ({"file_findings": [{"file", "findings": [...]}], "meta": [...]}).
  2. A single JSON file: either that same wrapper, a bare list of findings, or
     {"findings": [...]}.
  3. A rendered markdown report (best-effort: parses the summary table only;
     code snippets and fix examples are usually absent, so those findings get
     bumped a tier later by estimate_effort.py).

Canonical output (written to --out, default .refactor/findings.json):
  {
    "source": "rule-audit-json|findings-json|markdown",
    "root": "/abs/repo/root",
    "findings": [
      {"id": "f1", "file", "title", "rule_file", "rule_text", "line",
       "issue", "impact", "risk", "confidence", "code_snippet",
       "suggested_fix", "fix_example"}
    ]
  }

Pass --files <path...> to scope findings to specific files and/or directories
(matched repo-relative against root); the confidence filter and f1..fN id
assignment then run over the scoped set, so ids stay contiguous for the target.

Findings a prior refactor run marked resolved are filtered out on load — JSON
`status` in {addressed, cleared}, or a markdown Issue cell prefixed with
`[ADDRESSED]`/`[CLEARED]` — so a continuation run reading a `.updated.md` report
sees only open work.

Exit: 0 found >=1 finding · 3 input parsed/scoped to zero findings · 1 usage/IO.
"""

import argparse
import glob
import json
import os
import re
import sys

LEVELS = {"HIGH", "MEDIUM", "LOW"}
RESOLVED_STATUSES = {"addressed", "cleared"}
CANON_KEYS = ("file", "title", "rule_file", "rule_text", "line", "issue",
              "impact", "risk", "confidence", "code_snippet", "suggested_fix",
              "fix_example")


def _norm_one(raw):
    """Coerce a single raw finding dict into the canonical key set.

    Sets a private `_resolved` flag (from a `status` of addressed/cleared) that
    main() filters on and the canonical output omits."""
    out = {k: raw.get(k) for k in CANON_KEYS}
    for axis in ("impact", "risk"):
        v = out.get(axis)
        out[axis] = v if v in LEVELS else (v.upper() if isinstance(v, str) and v.upper() in LEVELS else "MEDIUM")
    if not isinstance(out.get("confidence"), (int, float)) or isinstance(out.get("confidence"), bool):
        out["confidence"] = 0
    out["_resolved"] = str(raw.get("status") or "").strip().lower() in RESOLVED_STATUSES
    return out


def _from_wrapper(data):
    """{"file_findings": [{"file", "findings": [...]}]} -> flat list."""
    findings = []
    for entry in data.get("file_findings", []):
        f = entry.get("file")
        for fnd in entry.get("findings", []):
            n = _norm_one(fnd)
            n["file"] = n.get("file") or f
            findings.append(n)
    return findings


def load_json_source(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict) and "file_findings" in data:
        return _from_wrapper(data)
    if isinstance(data, dict) and isinstance(data.get("findings"), list):
        return [_norm_one(x) for x in data["findings"]]
    if isinstance(data, list):
        return [_norm_one(x) for x in data]
    raise ValueError(f"{path}: unrecognized JSON shape (need file_findings, findings, or a list)")


def load_dir_source(path):
    findings = []
    batches = sorted(glob.glob(os.path.join(path, "batch-*.json")))
    if not batches:
        raise ValueError(f"{path}: no batch-*.json files found in directory")
    for b in batches:
        with open(b, encoding="utf-8") as fh:
            findings.extend(_from_wrapper(json.load(fh)))
    return findings


# Summary table row from render_report.py:
# | # | File | Rule | Impact | Risk | Conf | Issue |
_ROW = re.compile(r"^\|\s*\d+\s*\|(.+)\|(.+)\|(.+)\|(.+)\|(.+)\|(.+)\|\s*$")


def load_markdown_source(path):
    findings = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = _ROW.match(line.rstrip())
            if not m:
                continue
            file, rule, impact, risk, conf, issue = (c.strip() for c in m.groups())
            if file.lower() == "file" or set(file) <= {"-", " "}:
                continue  # header / separator row
            conf_n = int(re.sub(r"[^0-9]", "", conf) or 0)
            tag = re.match(r"\[(addressed|cleared)\]", issue, re.I)  # prior-run marker
            findings.append(_norm_one({
                "file": file, "title": issue, "rule_file": rule, "rule_text": "",
                "issue": issue, "impact": impact, "risk": risk,
                "confidence": conf_n, "code_snippet": "", "suggested_fix": "",
                "status": tag.group(1).lower() if tag else None,
            }))
    return findings


def main():
    ap = argparse.ArgumentParser(description="Normalize an audit report to canonical findings.")
    ap.add_argument("input", help="rule-audit dir, findings JSON, or markdown report")
    ap.add_argument("--root", default=None, help="repo root (default: git toplevel or cwd)")
    ap.add_argument("--out", default=".refactor/findings.json", help="output path")
    ap.add_argument("--files", nargs="+", default=None,
                    help="scope findings to these files/dirs (repo-relative match against root)")
    ap.add_argument("--min-confidence", type=int, default=90,
                    help="drop findings below this confidence (default 90, matches rule-audit)")
    args = ap.parse_args()

    root = args.root or os.popen("git rev-parse --show-toplevel 2>/dev/null").read().strip() or os.getcwd()

    try:
        if os.path.isdir(args.input):
            source, findings = "rule-audit-json", load_dir_source(args.input)
        elif args.input.endswith(".md"):
            source, findings = "markdown", load_markdown_source(args.input)
        else:
            source, findings = "findings-json", load_json_source(args.input)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    # Drop findings a prior run marked addressed/cleared, so a continuation run
    # that loads a `.updated.md` report sees only open work.
    resolved = sum(1 for f in findings if f.get("_resolved"))
    findings = [f for f in findings if not f.get("_resolved")]

    if args.files:
        # Normalize each target to repo-relative against root; finding `file`
        # values are already repo-relative. A target that resolves to root
        # itself (".") means "no narrowing" and matches everything.
        targets = {os.path.normpath(os.path.relpath(os.path.abspath(t), root))
                   for t in args.files}
        def _in_scope(finding):
            nf = os.path.normpath(finding.get("file") or "")
            for t in targets:
                if t in (".", "") or nf == t or nf.startswith(t + os.sep):
                    return True
            return False
        findings = [f for f in findings if _in_scope(f)]

    kept = [f for f in findings if f["confidence"] >= args.min_confidence]
    for i, f in enumerate(kept, 1):
        f["id"] = f"f{i}"
    # stable key order: id first
    kept = [{"id": f["id"], **{k: f[k] for k in CANON_KEYS}} for f in kept]

    out = {"source": source, "root": root, "findings": kept}
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)

    dropped = len(findings) - len(kept)
    print(json.dumps({"source": source, "root": root, "n_findings": len(kept),
                      "dropped_low_confidence": dropped, "dropped_addressed": resolved,
                      "out": args.out}))
    sys.exit(0 if kept else 3)


if __name__ == "__main__":
    main()
