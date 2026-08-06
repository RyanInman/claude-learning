#!/usr/bin/env python3
"""Deterministic verbatim-quote checker for style-review reports.

Checks that every offending-text citation in a report's "Fixes to reach A"
section appears verbatim in the target file. A fix entry reads:

    N. Lines X-Y (RULE): "citation" → "rewrite"

Only the citation is checked. The rewrite (right of the arrow) is proposed
text and is expected NOT to be in the target. Reports without a "Fixes to
reach A" section fall back to whole-report quote extraction — noisier, but a
baseline report that skipped the contract still gets its quotes checked.

Normalization (ruled in the 2026-08-05 debate review):
- collapse whitespace runs to one space (joins hard-wrapped lines)
- fold typographic variants of the SAME mark: curly double quotes -> straight
  double, curly single/apostrophe -> straight apostrophe
- never fold one mark into a different mark: single-for-double or
  hyphen-for-em-dash substitution is a citation-fidelity failure and must miss

Usage: check_quotes.py <report.md> <target> [<target> ...] [--min-len N] [--json]
Exit 0 when every citation is found; exit 1 on any miss.

A target is a file or a folder. A folder expands to its SKILL.md plus every
markdown file under references/, which covers a folder-scope style review.
Several targets form one corpus, so a citation quoted from the right folder but
attributed to the wrong file inside it still passes. Per-file attribution is
out of scope here; a reader checks it against the report's file headings.
"""
import argparse
import json
import re
import sys
from pathlib import Path

SAME_MARK = str.maketrans({
    "“": '"', "”": '"', "„": '"', "«": '"', "»": '"',
    "‘": "'", "’": "'", "‚": "'",
})

# text right of these markers is proposed/illustrative, not a citation
ARROW = re.compile(r"\s(?:→|->)\s|\(for example:")
QUOTED = re.compile(r'"((?:[^"\\]|\\.)*)"')
FIXES_HEADING = re.compile(r"^#+\s.*fixes to reach a", re.IGNORECASE)
HEADING = re.compile(r"^#+\s")
ENTRY_START = re.compile(r"^\s*\d+\.\s")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.translate(SAME_MARK)).strip()


def unescape(span: str) -> str:
    return span.replace('\\"', '"').replace("\\\\", "\\")


def fixes_section(report: str) -> str | None:
    lines = report.splitlines()
    start = next((i for i, l in enumerate(lines) if FIXES_HEADING.match(l)), None)
    if start is None:
        return None
    end = next((i for i in range(start + 1, len(lines)) if HEADING.match(lines[i])),
               len(lines))
    return "\n".join(lines[start + 1:end])


def entries(section: str) -> list[str]:
    out, cur = [], None
    for line in section.splitlines():
        if ENTRY_START.match(line):
            if cur is not None:
                out.append(cur)
            cur = line
        elif cur is not None:
            cur += " " + line
    if cur is not None:
        out.append(cur)
    return out


def extract_citations(report: str, min_len: int) -> tuple[list[str], str]:
    """Returns (citations, mode). Mode is 'fixes' or 'fallback'."""
    section = fixes_section(report)
    if section is not None:
        spans = []
        for entry in entries(section):
            zone = ARROW.split(entry, maxsplit=1)[0]  # citation zone only
            spans += [unescape(m) for m in QUOTED.findall(zone)]
        mode = "fixes"
    else:
        flat = re.sub(r"\s+", " ", report)
        spans = [unescape(m) for m in QUOTED.findall(flat)]
        mode = "fallback"
    seen, citations = set(), []
    for s in spans:
        s = s.strip()
        if len(s) >= min_len and s not in seen:
            seen.add(s)
            citations.append(s)
    return citations, mode


ELLIPSIS = re.compile(r"…|\.\.\.")


def found_in(citation: str, corpus_norm: str, min_len: int) -> bool:
    """A citation matches when every elided fragment appears in the corpus.
    An ellipsis marks elision, not quoted text, so 'a … b' checks 'a' and 'b'
    separately; fragments below min_len are skipped as too short to anchor."""
    fragments = [f.strip() for f in ELLIPSIS.split(citation)]
    fragments = [f for f in fragments if len(f) >= min_len]
    if not fragments:
        return True
    return all(normalize(f) in corpus_norm for f in fragments)


def corpus_paths(targets: list[str]) -> list[Path]:
    """Expand each target to the files it covers. A folder yields its SKILL.md
    plus every markdown file under references/; a file yields itself."""
    paths = []
    for target in targets:
        p = Path(target)
        if not p.is_dir():
            paths.append(p)
            continue
        if (p / "SKILL.md").is_file():
            paths.append(p / "SKILL.md")
        if (p / "references").is_dir():
            paths += sorted((p / "references").rglob("*.md"))
    return paths


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("report")
    ap.add_argument("target", nargs="+",
                    help="one or more target files, or a skill folder")
    ap.add_argument("--min-len", type=int, default=15,
                    help="minimum citation length to check (default 15); "
                         "shorter spans are rule names or terms, not citations")
    ap.add_argument("--allow-from", action="append", default=[], metavar="FILE",
                    help="extra corpus (repeatable), e.g. the style guides: a "
                         "miss found here is a legitimate guide-rule quote, "
                         "reported separately and not a failure")
    ap.add_argument("--json", action="store_true", help="emit JSON result")
    args = ap.parse_args()

    report = open(args.report, encoding="utf-8").read()
    target_norm = normalize(" ".join(
        p.read_text(encoding="utf-8") for p in corpus_paths(args.target)))
    allow_norm = normalize(" ".join(
        open(p, encoding="utf-8").read() for p in args.allow_from)) if args.allow_from else ""

    citations, mode = extract_citations(report, args.min_len)
    misses, guide_quotes = [], []
    for c in citations:
        if found_in(c, target_norm, args.min_len):
            continue
        if allow_norm and found_in(c, allow_norm, args.min_len):
            guide_quotes.append(c)
        else:
            misses.append(c)

    result = {
        "mode": mode,
        "checked": len(citations),
        "found": len(citations) - len(misses) - len(guide_quotes),
        "guide_quotes": len(guide_quotes),
        "missing": len(misses),
        "misses": misses,
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"[{mode}] checked {result['checked']}, found {result['found']}, "
              f"guide-quotes {result['guide_quotes']}, missing {result['missing']}")
        for m in misses:
            print(f"  MISS: {m[:100]}")
    return 1 if misses else 0


if __name__ == "__main__":
    sys.exit(main())
