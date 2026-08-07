#!/usr/bin/env python3
"""
render_notes.py - Render the final release notes: a markdown list grouped by
type, PR numbers ascending, optionally preceded by the drafted summary.

Covers workflow step 5. Reuses scan_notes.py so the grouping and the header
rules stay defined in exactly one place.

STDOUT
    The release-notes markdown. Files that fail the header check are named on
    stderr and skipped, so a partial notes/ still renders.

USAGE
    python3 scripts/render_notes.py <notes-dir> [--summary-file FILE] [--out FILE]

EXIT CODES
    0  Notes rendered.
    1  No valid entries to render.
    2  Usage error, or an input file is missing or unreadable.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_notes import KNOWN_TYPES, scan  # noqa: E402


def render(result, summary=None):
    """Return the release-notes markdown for a scan_notes result."""
    blocks = []
    if summary:
        blocks.append(" ".join(summary.split()))
    for type_name in KNOWN_TYPES:
        entries = result["groups"][type_name]
        if not entries:
            continue
        lines = [f"### {type_name}"]
        lines += [f"- #{e['pr']} {e['title']}" for e in entries]
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Render release notes grouped by type, PR numbers ascending.")
    ap.add_argument("notes_dir", help="directory holding the per-PR .md notes")
    ap.add_argument("--summary-file", help="file holding the drafted summary")
    ap.add_argument("--out", help="write the markdown here instead of stdout")
    args = ap.parse_args(argv)

    d = Path(args.notes_dir)
    if not d.is_dir():
        print(f"render_notes: not a directory: {args.notes_dir}", file=sys.stderr)
        return 2
    summary = None
    if args.summary_file:
        try:
            summary = Path(args.summary_file).read_text(encoding="utf-8")
        except OSError as e:
            print(f"render_notes: cannot read summary: {e}", file=sys.stderr)
            return 2
    try:
        result = scan(d)
    except OSError as e:
        print(f"render_notes: cannot read notes: {e}", file=sys.stderr)
        return 2

    for bad in result["invalid"] + result["unknown_type"]:
        print(f"render_notes: skipped {bad['file']} "
              f"({bad.get('reason') or 'unknown type ' + bad.get('type', '')})",
              file=sys.stderr)
    if not any(result["groups"][t] for t in KNOWN_TYPES):
        print(f"render_notes: no valid entries in {args.notes_dir}", file=sys.stderr)
        return 1

    markdown = render(result, summary)
    if args.out:
        try:
            Path(args.out).write_text(markdown + "\n", encoding="utf-8")
        except OSError as e:
            print(f"render_notes: cannot write --out: {e}", file=sys.stderr)
            return 2
        print(f"render_notes: wrote {args.out}")
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
