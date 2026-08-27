#!/usr/bin/env python3
"""Validate chunk JSON files and render the layered brief.

Reads <work>/inventory.json and one <work>/chunk-NN.json per chunk. Exits 1 and
names every invalid chunk, so the caller re-runs those chunks instead of
shipping a brief with holes. On success writes the brief to --out and prints it.

Usage:
    render_brief.py --work DIR --tldr FILE --out BRIEF.md
"""

import argparse
import json
import os
import sys

STATUSES = {"verified", "unverified", "contradicted"}
KINDS = {"hallucinated-api", "duplicate-logic", "missing-edge-case", "uncited-number", "unsupported-claim"}
MAX_SUMMARY_WORDS = 80
MAX_CLAIM_WORDS = 25
MAX_NOTE_WORDS = 20
MAX_TLDR_WORDS = 35
MAX_CLAIMS = 6
MAX_RISKS = 4
COMPACT_AT = 12  # past this many chunks, summaries collapse to one line each
MAX_BRIEF_WORDS = 1500  # hard ceiling for code and diff targets
SOURCE_RATIO = 3  # prose briefs stay under source_words / SOURCE_RATIO


def validate(data, cid):
    errs = []
    if not isinstance(data, dict):
        return [f"{cid}: top level must be an object"]
    s = data.get("summary")
    if not isinstance(s, str) or not s.strip():
        errs.append(f"{cid}: summary missing")
    elif len(s.split()) > MAX_SUMMARY_WORDS:
        errs.append(f"{cid}: summary has {len(s.split())} words, max {MAX_SUMMARY_WORDS}")
    if len(data.get("claims", [])) > MAX_CLAIMS:
        errs.append(f"{cid}: {len(data['claims'])} claims, max {MAX_CLAIMS}; keep the ones a reviewer must check")
    if len(data.get("risks", [])) > MAX_RISKS:
        errs.append(f"{cid}: {len(data['risks'])} risks, max {MAX_RISKS}")
    for i, c in enumerate(data.get("claims", [])):
        for k in ("text", "anchor", "status"):
            if not isinstance(c.get(k), str) or not c[k].strip():
                errs.append(f"{cid}: claims[{i}].{k} missing")
        if len(c.get("text", "").split()) > MAX_CLAIM_WORDS:
            errs.append(f"{cid}: claims[{i}] has {len(c['text'].split())} words, max {MAX_CLAIM_WORDS}")
        if c.get("status") not in STATUSES:
            errs.append(f"{cid}: claims[{i}].status {c.get('status')!r} not in {sorted(STATUSES)}")
        if c.get("status") == "contradicted" and " vs " not in c.get("anchor", ""):
            errs.append(f"{cid}: claims[{i}] contradicted needs anchor 'A vs B'")
    for i, r in enumerate(data.get("risks", [])):
        for k in ("kind", "anchor", "note"):
            if not isinstance(r.get(k), str) or not r[k].strip():
                errs.append(f"{cid}: risks[{i}].{k} missing")
        if len(r.get("note", "").split()) > MAX_NOTE_WORDS:
            errs.append(f"{cid}: risks[{i}].note has {len(r['note'].split())} words, max {MAX_NOTE_WORDS}")
        if r.get("kind") not in KINDS:
            errs.append(f"{cid}: risks[{i}].kind {r.get('kind')!r} not in {sorted(KINDS)}")
    lc = data.get("least_confident")
    if not isinstance(lc, str) or not lc.strip():
        errs.append(f"{cid}: least_confident missing")
    return errs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work", required=True, help="dir holding inventory.json and chunk-NN.json")
    ap.add_argument("--tldr", required=True, help="file with 1-5 TL;DR bullets")
    ap.add_argument("--out", required=True, help="brief path to write")
    a = ap.parse_args()

    with open(os.path.join(a.work, "inventory.json")) as f:
        inv = json.load(f)
    with open(a.tldr) as f:
        tldr = [l.rstrip() for l in f if l.strip()]
    if not 1 <= len(tldr) <= 5:
        sys.exit(f"tldr must have 1-5 lines, got {len(tldr)}")
    long_bullets = [t for t in tldr if len(t.split()) > MAX_TLDR_WORDS]
    if long_bullets:
        sys.exit(f"{len(long_bullets)} TL;DR bullet(s) over {MAX_TLDR_WORDS} words; shorten them, because the TL;DR is the part every reader reads")

    chunks, errors = [], []
    for e in inv["chunks"]:
        p = os.path.join(a.work, f"{e['id']}.json")
        if not os.path.exists(p):
            errors.append(f"{e['id']}: {p} missing")
            continue
        try:
            with open(p) as f:
                data = json.load(f)
        except json.JSONDecodeError as ex:
            errors.append(f"{e['id']}: invalid JSON ({ex})")
            continue
        errs = validate(data, e["id"])
        if errs:
            errors += errs
        else:
            chunks.append({**e, **data})
    if errors:
        print("INVALID CHUNKS, re-run these:", file=sys.stderr)
        for err in errors:
            print("  " + err, file=sys.stderr)
        sys.exit(1)

    prose_words = sum(c["size"] for c in chunks if c["unit"] == "words")
    budget = min(MAX_BRIEF_WORDS, prose_words // SOURCE_RATIO) if prose_words and all(c["unit"] == "words" for c in chunks) else MAX_BRIEF_WORDS

    def render(level):
        """level 0: full. 1: one-line summaries. 2: verified claims collapsed to a count. 3: least-confident only for high-risk chunks. 4: risks only from high-risk chunks."""
        order = sorted(chunks, key=lambda c: (c["risk_tier"] != "high", c["id"]))
        compact = len(chunks) > COMPACT_AT or level >= 1

        def short(anchor):
            parts = [p.strip() for p in anchor.split(",")]
            return parts[0] if len(parts) == 1 else f"{parts[0]} +{len(parts) - 1} more"
        lines = [f"# Brief: {inv['target']}", ""]
        lines.append("## TL;DR")
        lines += [t if t.lstrip().startswith("-") else f"- {t}" for t in tldr]
        lines += ["", "## Structure map", "", "| id | type | risk | size | anchor |", "|---|---|---|---|---|"]
        for c in chunks:
            lines.append(f"| {c['id']} | {c['type']} | {c['risk_tier']} | {c['size']} {c['unit']} | {short(c['anchor']) if compact else c['anchor']} |")
        lines += ["", "## Chunk summaries", ""]
        for c in order:
            if compact:
                first = c["summary"].split(". ")[0].rstrip(".") + "."
                lines.append(f"- **{c['id']}** [{c['risk_tier']}] {short(c['anchor'])}: {first}")
            else:
                lines += [f"### {c['id']} [{c['risk_tier']}] {c['anchor']}", "", c["summary"], ""]
        if compact:
            lines.append("")
        lines += ["## Claims", "", "| status | claim | anchor |", "|---|---|---|"]
        all_claims = [(cl, c["id"]) for c in chunks for cl in c.get("claims", [])]
        rank = {"contradicted": 0, "unverified": 1, "verified": 2}
        shown = [x for x in all_claims if not (level >= 2 and x[0]["status"] == "verified")]
        for cl, cid in sorted(shown, key=lambda x: rank[x[0]["status"]]):
            lines.append(f"| {cl['status']} | {cl['text']} | {cl['anchor']} |")
        hidden = len(all_claims) - len(shown)
        if hidden:
            lines.append(f"\n{hidden} verified claims omitted to keep the brief short; see chunk JSON for the full list.")
        lines += ["", "## Risks", ""]
        all_risks = [(r, c) for c in chunks for r in c.get("risks", [])]
        all_risks.sort(key=lambda x: (x[1]["risk_tier"] != "high", x[0]["kind"]))
        if not all_risks:
            lines.append("None flagged.")
        shown_risks = [x for x in all_risks if not (level >= 4 and x[1]["risk_tier"] != "high")]
        for r, c in shown_risks:
            lines.append(f"- **{r['kind']}** [{c['risk_tier']}] {r['anchor']}: {r['note']}")
        if len(all_risks) - len(shown_risks):
            lines.append(f"\n{len(all_risks) - len(shown_risks)} risks in low-risk chunks omitted; see chunk JSON.")
        lines += ["", "## Least confident", ""]
        for c in chunks:
            if level >= 3 and c["risk_tier"] != "high" and c.get("claims") and not any(cl["status"] == "contradicted" for cl in c["claims"]):
                continue
            lines.append(f"- {c['id']}: {c['least_confident']}")
        counts = {s: sum(1 for cl, _ in all_claims if cl["status"] == s) for s in ("verified", "unverified", "contradicted")}
        lines += ["", f"_{len(chunks)} chunks, {len(all_claims)} claims ({counts['verified']} verified, {counts['unverified']} unverified, {counts['contradicted']} contradicted), {len(all_risks)} risks. Budget {budget} words, compaction level {level}._", ""]
        return lines

    level = 0
    lines = render(level)
    while len(" ".join(lines).split()) > budget and level < 4:
        level += 1
        lines = render(level)
    text = "\n".join(lines)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    print(f"\nwrote {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
