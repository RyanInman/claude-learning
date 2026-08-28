#!/usr/bin/env python3
"""
render_review.py - Count violations per rule, or render the style-review report from findings.json.

READS   findings.json
WRITES  --out FILE only, when given

USAGE
    python3 scripts/render_review.py <findings.json> --counts
        Prints JSON: total, per_rule, per_file, top (the three costliest rules with
        one example each). Claude reads this to assign the grade.

    python3 scripts/render_review.py <findings.json> --grade B \\
        --grade-note "<one sentence tying the grade to the adherence table>" \\
        --guides-reason "<one sentence on the guide choice>" [--out FILE]
        Prints the report markdown in the fixed template. Numbering is one flat
        list in file scope and continuous across bold file headings in folder scope.
        Zero findings renders "No fixes required."

findings.json shape: see verify_findings.py. "rule" can list several ids, as in
"B1, D1, D2". "guides_applied" is optional; without it the script derives the
guide line from "target_class".

EXIT CODES
    0  Rendered.
    1  findings.json invalid (code invalid_findings on stdout).
    2  Usage error or unreadable file.
    3  Unexpected failure.
"""

import argparse
import json
import sys
from collections import Counter, OrderedDict
from pathlib import Path

RULE_NAMES = {
    "A1": "One term per concept", "A2": "Use the standard term of art", "A3": "Prefer the simple word",
    "A4": "Limit noun clusters to three nouns", "A5": "Use must and can only",
    "A6": "Introduce abbreviations once",
    "B1": "Keep the actor visible", "B2": "Use simple verb forms", "B3": "Prefer the verb to its noun",
    "B4": "Keep grammar flat",
    "C1": "One instruction per sentence", "C2": "Treat 20 words as a rewrite tripwire",
    "C3": "Put the condition or purpose first", "C4": "Keep paragraphs short and single-topic",
    "C5": "Use simple punctuation",
    "D1": "Start every instruction with a command verb", "D2": "Name the specific action and amount",
    "D3": "Attach the reason to every non-obvious rule",
    "E": "Warnings", "F": "Compression",
}
GUIDE_LABEL = {"skill": "skill guide", "memory": "memory guide"}
TOP_N = 3  # the template asks for two or three entries


def load(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"error: cannot load {path}: {e}", file=sys.stderr)
        return None, 2
    if not isinstance(data, dict) or not isinstance(data.get("findings"), list) or "target" not in data:
        print(json.dumps({"code": "invalid_findings",
                          "message": "findings.json needs 'target' and a 'findings' list"}))
        return None, 1
    for i, f in enumerate(data["findings"]):
        if not isinstance(f, dict) or not f.get("file") or not f.get("rule") or not f.get("fix"):
            print(json.dumps({"code": "invalid_findings", "index": i,
                              "message": "each finding needs file, rule, and fix"}))
            return None, 1
    return data, 0


def rule_ids(rule):
    return [r.strip() for r in str(rule).split(",") if r.strip()]


def counts(data):
    per_rule, example, per_file = Counter(), {}, Counter()
    for f in data["findings"]:
        per_file[f["file"]] += 1
        for r in rule_ids(f["rule"]):
            per_rule[r] += 1
            example.setdefault(r, {"file": f["file"], "line": f.get("line"), "quote": f.get("quote")})
    top = [{"rule": r, "name": RULE_NAMES.get(r, r), "count": n, "example": example[r]}
           for r, n in per_rule.most_common(TOP_N)]
    return {"total": len(data["findings"]), "per_rule": dict(per_rule.most_common()),
            "per_file": dict(per_file), "top": top}


def entry(n, f):
    rule = f["rule"]
    if f.get("line") is None:
        return f'{n}. File-wide ({rule}): {f.get("quote", "")} → {f["fix"]}'
    return f'{n}. Line {f["line"]} ({rule}): "{f.get("quote", "")}" → "{f["fix"]}"'


def render(data, grade, grade_note, guides_reason):
    scope = data.get("scope") or "file"
    extra = data.get("guides_applied") or GUIDE_LABEL.get(data.get("target_class"), "none")
    c = counts(data)
    out = [f"## Style review: {data['target']}", "",
           f"Guides applied: universal + {extra}. Reason: {guides_reason}", "",
           f"### Grade: {grade}", "", grade_note, "",
           "### Rules that cost the grade most", ""]
    if c["top"]:
        for t in c["top"]:
            ex = t["example"]
            where = f'{ex["file"]}:{ex["line"]}' if ex["line"] is not None else f'{ex["file"]}:file-wide'
            out.append(f'- **{t["rule"]} — {t["name"]}**: {t["count"]} violations. '
                       f'Example ({where}): "{ex["quote"]}"')
    else:
        out.append("- None.")
    out += ["", "### Fixes to reach A", ""]
    if not data["findings"]:
        out.append("No fixes required.")
        return "\n".join(out) + "\n"
    n = 0
    if scope == "folder":
        groups = OrderedDict()
        for f in data["findings"]:
            groups.setdefault(f["file"], []).append(f)
        for file, items in groups.items():
            out.append(f"**{file}**")
            for f in items:
                n += 1
                out.append(entry(n, f))
            out.append("")
    else:
        for f in data["findings"]:
            n += 1
            out.append(entry(n, f))
    return "\n".join(out).rstrip("\n") + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("findings", help="findings.json")
    parser.add_argument("--counts", action="store_true", help="print per-rule counts JSON and stop")
    parser.add_argument("--grade", choices=list("ABCDF"), help="letter grade Claude assigned")
    parser.add_argument("--grade-note", default="", help="one sentence tying the grade to the table")
    parser.add_argument("--guides-reason", default="", help="one sentence on the guide choice")
    parser.add_argument("--out", help="write the report here; print a one-line summary to stdout")
    args = parser.parse_args(argv)

    data, rc = load(args.findings)
    if data is None:
        return rc
    if args.counts:
        print(json.dumps(counts(data), indent=2))
        return 0
    if not args.grade:
        parser.error("--grade is required unless --counts is given")
    report = render(data, args.grade, args.grade_note, args.guides_reason)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"{len(data['findings'])} fixes, grade {args.grade} -> {args.out}")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # predictable errors already returned 2 above
        print(f"unexpected failure: {e}", file=sys.stderr)
        sys.exit(3)
