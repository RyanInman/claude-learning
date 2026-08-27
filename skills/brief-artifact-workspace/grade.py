#!/usr/bin/env python3
"""Grade every run in one iteration of the brief-artifact workspace.

Usage: grade.py <iteration-dir>
Writes grading.json (viewer schema: expectations[{text,passed,evidence}] + summary)
into each <eval>/<config>/ and <eval>/<config>/run-1/.
"""
import glob
import json
import os
import re
import sys

LIMITS = {1: 1097, 2: 1500, 3: 1500}  # eval-1: 3292 source words // 3


def words(p):
    return len(open(p).read().split()) if os.path.exists(p) else 0


def grade(ev, run):
    d = f"{ev}/{run}"
    b = f"{d}/outputs/brief.md"
    t = open(b).read() if os.path.exists(b) else ""
    low = t.lower()
    meta = json.load(open(f"{ev}/eval_metadata.json"))
    eid = meta["eval_id"]
    exp = meta["expectations"]
    ex = []

    def add(text, passed, evidence):
        ex.append({"text": text, "passed": bool(passed), "evidence": evidence})

    secs = all(s in low for s in ["tl;dr", "claims", "risks", "least confident"])
    wc = words(b)
    if eid == 1:
        add(exp[0], secs, "sections present" if secs else "missing a section")
        rows = [r for r in t.splitlines() if r.startswith("| ") and "|---" not in r and "| status" not in r and "| id |" not in r]
        anch = bool(rows) and all(re.search(r"L\d+|:\d+|>", r) for r in rows)
        add(exp[1], anch, f"{len(rows)} table rows, anchored={anch}")
        st = len(re.findall(r"\| (verified|unverified|contradicted) \|", t))
        add(exp[2], st > 0, f"{st} status-marked claims")
        add(exp[3], wc <= LIMITS[1], f"{wc} words (limit {LIMITS[1]})")
        tl = re.search(r"## TL;DR\n(.*?)\n##", t, re.S)
        n = len([l for l in tl.group(1).splitlines() if l.strip().startswith("-")]) if tl else 0
        add(exp[4], 0 < n <= 5 and ("comprehension" in low or "bottleneck" in low), f"{n} bullets")
    if eid == 2:
        c = "contradict" in low and "30" in t and "90" in t
        add(exp[0], c, "contradiction with 30/90 present" if c else "not found")
        both = ("timeouts" in low or "retries" in low) and "operations" in low
        add(exp[1], both, "both section names present" if both else "one side missing")
        add(exp[2], secs, "sections present" if secs else "missing a section")
        add(exp[3], wc <= LIMITS[2], f"{wc} words (limit {LIMITS[2]})")
    if eid == 3:
        paths = len(re.findall(r"skills/[\w\-/.]+", t))
        add(exp[0], paths >= 5, f"{paths} path references")
        hi, lo = re.search(r"\[high\]", t), re.search(r"\[low\]", t)
        ordered = bool(hi and lo and hi.start() < lo.start())
        add(exp[1], ordered, "high before low" if ordered else "no explicit risk ordering")
        pl = re.search(r"[\w/.-]+\.\w+:\d+", t)
        add(exp[2], bool(pl), "path:line anchor found" if pl else "none")
        unc = "least confident" in low or "uncertain" in low
        add(exp[3], unc, "uncertainty statement present" if unc else "none")
        add(exp[4], wc <= LIMITS[3], f"{wc} words (limit {LIMITS[3]})")
    k = sum(e["passed"] for e in ex)
    g = {"expectations": ex, "summary": {"passed": k, "failed": len(ex) - k, "total": len(ex), "pass_rate": k / len(ex)}, "notes": f"brief words={wc}"}
    os.makedirs(f"{d}/run-1", exist_ok=True)
    for q in (f"{d}/grading.json", f"{d}/run-1/grading.json"):
        json.dump(g, open(q, "w"), indent=2)
    print(f"{os.path.basename(ev):45} {run:14} {k}/{len(ex)}  words={wc}")


if __name__ == "__main__":
    it = sys.argv[1].rstrip("/")
    for ev in sorted(glob.glob(f"{it}/eval-*")):
        for run in ("with_skill", "without_skill"):
            if os.path.isdir(f"{ev}/{run}"):
                grade(ev, run)
