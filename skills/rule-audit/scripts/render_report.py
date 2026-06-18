#!/usr/bin/env python3
"""Aggregate review-subagent JSON into the ranked rule-adherence report.

Back-end counterpart to map_rules.py: that script fans work out, this one fans
it back in. Each review subagent writes its findings as JSON (the Finding schema
in references/rubric-and-schema.md) into a directory; this script validates every
file against that schema, sorts findings by impact then risk deterministically,
writes the full Markdown report to disk, and prints the title block + ranked
Summary table to stdout for the main agent to relay.

Keeping the sort + render here (not in the model) means the report never streams
through the conversation token-by-token, the ordering is always correct, and a
malformed subagent response is caught as a hard error instead of a silent gap.

Usage:
    python3 render_report.py --findings .rule-review --map .rule-review/map.json
                             [--out rule-adherence-report.md] [--expect N]

Exit codes: 0 ok · 2 validation error (bad/malformed/short findings) · 1 usage/IO.
"""

import argparse
import glob
import json
import os
import sys

RANK = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
LEVELS = set(RANK)
REQUIRED = ("title", "rule_file", "rule_text", "issue", "impact", "risk",
            "code_snippet", "suggested_fix")

LANG_BY_EXT = {
    ".ts": "ts", ".tsx": "tsx", ".js": "js", ".jsx": "jsx", ".py": "python",
    ".go": "go", ".rb": "ruby", ".java": "java", ".rs": "rust", ".php": "php",
    ".c": "c", ".h": "c", ".cpp": "cpp", ".cs": "csharp", ".kt": "kotlin",
    ".swift": "swift", ".sh": "bash", ".sql": "sql", ".css": "css",
    ".scss": "scss", ".html": "html", ".json": "json", ".yml": "yaml",
    ".yaml": "yaml",
}


def fail(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def lang_for(path):
    return LANG_BY_EXT.get(os.path.splitext(path)[1].lower(), "")


# --- load + validate ---------------------------------------------------------

def validate_finding(src, file, i, fnd):
    where = f"{src}: finding #{i + 1} for {file}"
    if not isinstance(fnd, dict):
        return [f"{where}: not a JSON object"]
    errs = [f"{where}: missing '{k}'" for k in REQUIRED if not fnd.get(k)]
    for axis in ("impact", "risk"):
        v = fnd.get(axis)
        if v is not None and v not in LEVELS:
            errs.append(f"{where}: {axis}={v!r} not one of HIGH|MEDIUM|LOW")
    return errs


def collect(findings_dir, expect):
    paths = sorted(p for p in glob.glob(os.path.join(findings_dir, "*.json"))
                   if os.path.basename(p) != "map.json")
    if not paths:
        fail(f"No findings JSON in {findings_dir} (expected one per batch). "
             "Did the review subagents write their files?", 2)
    if expect is not None and len(paths) != expect:
        fail(f"Expected {expect} batch files, found {len(paths)} in {findings_dir}. "
             "A subagent likely failed to write its findings — re-run the missing batch.", 2)

    file_findings, meta, errors = [], [], []
    for p in paths:
        try:
            with open(p, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError) as e:
            errors.append(f"{p}: cannot parse JSON ({e})")
            continue
        if not isinstance(data, dict):
            errors.append(f"{p}: top level must be a JSON object")
            continue
        ffs = data.get("file_findings")
        if not isinstance(ffs, list):
            errors.append(f"{p}: missing or non-list 'file_findings'")
            continue
        for entry in ffs:
            if not isinstance(entry, dict) or "file" not in entry:
                errors.append(f"{p}: each file_findings entry needs a 'file' key")
                continue
            fnds = entry.get("findings", [])
            if not isinstance(fnds, list):
                errors.append(f"{p}: 'findings' for {entry.get('file')} must be a list")
                continue
            for i, fnd in enumerate(fnds):
                errors.extend(validate_finding(p, entry["file"], i, fnd))
            file_findings.append(entry)
        for m in data.get("meta") or []:
            meta.append(m)
    return file_findings, meta, errors


# --- render ------------------------------------------------------------------

def title_block(mode, rules_n, files_reviewed, findings_n):
    return ("# Rule Adherence Report\n"
            f"Mode: {mode} · Rules: {rules_n} · Files reviewed: {files_reviewed} "
            f"· Findings: {findings_n}")


def summary_table(flat):
    lines = ["## Summary (ranked by impact, then risk)",
             "| # | File | Rule | Impact | Risk | Issue |",
             "|---|------|------|--------|------|-------|"]
    if not flat:
        lines.append("| – | – | – | – | – | No violations found |")
        return "\n".join(lines)
    for i, (file, f) in enumerate(flat, 1):
        rule = os.path.basename(f.get("rule_file", ""))
        issue = (f.get("title", "") or "").replace("|", "\\|")
        lines.append(f"| {i} | {file} | {rule} | {f.get('impact', '')} "
                     f"| {f.get('risk', '')} | {issue} |")
    return "\n".join(lines)


def fenced(lines_out, label, text, lang):
    lines_out.append(f"  {label}")
    lines_out.append(f"  ```{lang}")
    for ln in (text or "").splitlines():
        lines_out.append(f"  {ln}")
    lines_out.append("  ```")


def render(mode, rules_n, files_reviewed, findings_n, flat, file_findings,
           unmatched, meta):
    out = [title_block(mode, rules_n, files_reviewed, findings_n), "",
           summary_table(flat), "", "## Findings by file"]

    by_file = {}
    for file, f in flat:
        by_file.setdefault(file, []).append(f)

    for file in sorted(by_file):
        out.append(f"### {file}")
        lang = lang_for(file)
        for f in by_file[file]:
            loc = f"{file}:{f['line']}" if f.get("line") else file
            out.append(f"#### [{f.get('impact')} impact / {f.get('risk')} risk] "
                       f"{f.get('title', '')}")
            out.append(f"- Rule: `{f.get('rule_file', '')}` → \"{f.get('rule_text', '')}\"")
            out.append(f"- Issue: {f.get('issue', '')}")
            out.append("")
            fenced(out, f"Current (`{loc}`):", f.get("code_snippet"), lang)
            fix = f.get("fix_example")
            if fix:
                fenced(out, "Suggested fix:", fix, lang)
            else:
                out.append(f"  Suggested fix: {f.get('suggested_fix', '')}")
            out.append("")

    clean = sorted({e["file"] for e in file_findings} - set(by_file))
    if clean:
        out.append("## Clean files (no violations)")
        out.extend(f"- {c}" for c in clean)
        out.append("")

    if unmatched:
        out.append("## Files with no applicable rules")
        out.extend(f"- {u}" for u in unmatched)
        out.append("")

    if meta:
        out.append("## Meta-findings")
        for m in meta:
            out.append(f"- [{m.get('type', 'note')}] `{m.get('rule_file', '')}` "
                       f"— {m.get('note', '')}")
        out.append("")

    return "\n".join(out).rstrip() + "\n"


# --- main --------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--findings", required=True,
                    help="dir holding one batch-<N>.json per review subagent")
    ap.add_argument("--map", dest="map_path", required=True,
                    help="map_rules.py JSON output (gives mode, rule count, unmatched_files)")
    ap.add_argument("--out", default="rule-adherence-report.md",
                    help="report path (default: rule-adherence-report.md in cwd)")
    ap.add_argument("--expect", type=int, default=None,
                    help="expected batch count; error if the dir holds a different number")
    args = ap.parse_args()

    if not os.path.isdir(args.findings):
        fail(f"--findings dir not found: {args.findings}")
    try:
        with open(args.map_path, encoding="utf-8") as fh:
            mp = json.load(fh)
    except (OSError, json.JSONDecodeError) as e:
        fail(f"cannot read --map {args.map_path}: {e}")

    file_findings, meta, errors = collect(args.findings, args.expect)
    if errors:
        fail("Findings JSON failed validation; report NOT written:\n  - "
             + "\n  - ".join(errors), 2)

    mode = mp.get("mode", "?")
    rules_n = len(mp.get("global_rules", [])) + len(mp.get("path_scoped_rules", []))
    unmatched = mp.get("unmatched_files", [])

    flat = []
    for entry in file_findings:
        for fnd in entry.get("findings", []):
            flat.append((entry["file"], fnd))
    flat.sort(key=lambda t: (RANK.get(t[1].get("impact"), 3),
                             RANK.get(t[1].get("risk"), 3),
                             t[0], t[1].get("title", "")))

    files_reviewed = len({e["file"] for e in file_findings})
    report = render(mode, rules_n, files_reviewed, len(flat), flat,
                    file_findings, unmatched, meta)
    try:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
    except OSError as e:
        fail(f"cannot write {args.out}: {e}")

    print(title_block(mode, rules_n, files_reviewed, len(flat)))
    print()
    print(summary_table(flat))
    print(f"\nFull report written to {args.out}")


if __name__ == "__main__":
    main()
