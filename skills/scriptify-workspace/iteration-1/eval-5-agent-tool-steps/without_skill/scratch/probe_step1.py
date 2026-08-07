"""Scratch probe: does step 1 (parse/dedupe/slugify) have a single deterministic answer?

Two readings of "drop duplicates, and normalize each remaining topic to a lowercase
slug": dedupe-then-normalize vs normalize-then-dedupe. Show they disagree.
"""
import re
import sys

path = sys.argv[1]
raw = [ln.strip() for ln in open(path, encoding="utf-8")]
lines = [ln for ln in raw if ln]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def dedupe(seq):
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


a = [slug(t) for t in dedupe(lines)]          # dedupe raw, then slugify
b = dedupe([slug(t) for t in lines])          # slugify, then dedupe

print("raw lines      :", len(raw))
print("non-blank      :", len(lines))
print("A dedupe->slug :", len(a), a)
print("B slug->dedupe :", len(b), b)
print("agree          :", a == b)
