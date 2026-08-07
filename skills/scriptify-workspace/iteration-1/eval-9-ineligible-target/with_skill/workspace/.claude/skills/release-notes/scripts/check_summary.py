#!/usr/bin/env python3
"""
check_summary.py - Lint the customer-facing release summary Claude drafted:
exactly two sentences, non-empty, no internal PR references.

Covers the mechanical half of workflow step 4. The wording stays Claude's job;
this script only holds the draft to the constraints the step states.

STDOUT (JSON)
{"file": "summary.txt", "sentences": 2, "chars": 118, "findings": []}

Finding codes: empty_summary, not_two_sentences, raw_pr_reference, too_long.

USAGE
    python3 scripts/check_summary.py <summary-file> [--json]

EXIT CODES
    0  Clean: findings is empty.
    1  Findings present.
    2  Usage error, or the file is missing or unreadable.
"""

import argparse
import json
import re
import sys
from pathlib import Path

WANT_SENTENCES = 2      # step 4 says "a two-sentence summary"
MAX_CHARS = 400         # two sentences that run past this stop being a summary
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
PR_REFERENCE_RE = re.compile(r"(PR\s*#|#\d)", re.IGNORECASE)


def check(text):
    """Return the findings dict for a drafted summary."""
    body = " ".join(text.split())
    findings = []
    if not body:
        return {"sentences": 0, "chars": 0,
                "findings": [{"code": "empty_summary",
                              "detail": "the summary file is empty"}]}
    sentences = [s for s in SENTENCE_SPLIT_RE.split(body) if s.strip()]
    if len(sentences) != WANT_SENTENCES:
        findings.append({
            "code": "not_two_sentences",
            "detail": f"found {len(sentences)} sentence(s), want {WANT_SENTENCES}"})
    if PR_REFERENCE_RE.search(body):
        findings.append({
            "code": "raw_pr_reference",
            "detail": "customer-facing copy should not cite PR numbers"})
    if len(body) > MAX_CHARS:
        findings.append({
            "code": "too_long",
            "detail": f"{len(body)} chars, max {MAX_CHARS}"})
    return {"sentences": len(sentences), "chars": len(body), "findings": findings}


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Lint a drafted two-sentence release summary.")
    ap.add_argument("summary_file", help="file holding the drafted summary")
    ap.add_argument("--json", action="store_true",
                    help="accepted for explicitness; stdout is JSON either way")
    args = ap.parse_args(argv)

    p = Path(args.summary_file)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as e:
        print(f"check_summary: cannot read summary: {e}", file=sys.stderr)
        return 2

    result = check(text)
    result = {"file": str(p).replace("\\", "/"), **result}
    print(json.dumps(result, indent=2))
    return 1 if result["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())
