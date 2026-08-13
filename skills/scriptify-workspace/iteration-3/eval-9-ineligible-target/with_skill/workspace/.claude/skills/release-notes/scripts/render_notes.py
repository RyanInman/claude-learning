#!/usr/bin/env python3
"""
render_notes.py - Render the release notes as a markdown list, grouped by type
and sorted by PR number ascending.

Reuses scan_notes.scan for parsing, so the two scripts cannot disagree about
what a valid note looks like. Groups print in release order (feat, fix, chore),
then any other type alphabetically. Every entry the scan flagged is listed under
"## Needs attention" instead of being dropped silently.

USAGE
    python3 scripts/render_notes.py <notes-dir> [--out FILE]

    --out F  write the markdown to F and print a one-line summary instead

EXIT CODES
    0  Rendered; every note was well formed.
    1  Rendered, but flagged notes are listed under "## Needs attention".
    2  Usage error, missing directory, or an unreadable file.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_notes import scan  # noqa: E402

TYPE_ORDER = ["feat", "fix", "chore"]


def render(report):
    """Return the markdown document for a scan report."""
    flagged = {f["file"] for f in report["findings"]}
    good = [e for e in report["entries"] if e["file"] not in flagged]

    types = [t for t in TYPE_ORDER if any(e["type"] == t for e in good)]
    types += sorted({e["type"] for e in good if e["type"] not in TYPE_ORDER})

    lines = ["# Release notes", ""]
    for t in types:
        lines.append(f"### {t}")
        for e in sorted((e for e in good if e["type"] == t),
                        key=lambda e: e["pr"]):
            lines.append(f"- #{e['pr']} {e['title']}")
        lines.append("")

    if flagged:
        lines.append("## Needs attention")
        for f in report["findings"]:
            lines.append(f"- {f['file']}: {f['code']} ({f['detail']})")
        lines.append("")

    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Render the notes as markdown, grouped by type.")
    ap.add_argument("notes_dir", help="Directory holding the pr-*.md notes")
    ap.add_argument("--out", help="Write the markdown here; print a summary")
    args = ap.parse_args(argv)

    notes_dir = Path(args.notes_dir)
    if not notes_dir.is_dir():
        print(f"not a directory: {notes_dir}", file=sys.stderr)
        return 2

    report, err = scan(notes_dir)
    if err:
        print(err, file=sys.stderr)
        return 2

    text = render(report)
    if args.out:
        try:
            Path(args.out).write_text(text + "\n", encoding="utf-8")
        except OSError as e:
            print(f"cannot write {args.out}: {e}", file=sys.stderr)
            return 2
        print(f"{report['total']} notes rendered -> {args.out}")
    else:
        print(text)

    return 1 if report["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())
