#!/usr/bin/env python3
"""Scratch demo of step 1 as a script. Proves the dedup/slug result on the fixture."""
import json
import re
import sys


def slugify(line):
    return re.sub(r"[^a-z0-9]+", "-", line.strip().lower()).strip("-")


def main(path):
    seen = {}
    for lineno, raw in enumerate(open(path, encoding="utf-8"), 1):
        if not raw.strip():
            continue
        slug = slugify(raw)
        if not slug or slug in seen:
            continue
        seen[slug] = {"slug": slug, "topic": raw.strip(), "line": lineno}
    json.dump(list(seen.values()), sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main(sys.argv[1])
