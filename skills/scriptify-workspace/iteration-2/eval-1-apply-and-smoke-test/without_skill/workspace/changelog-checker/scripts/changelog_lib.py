"""Shared parsing helpers for the changelog-checker scripts.

Not a CLI. Import from the sibling scripts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

ALLOWED_CATEGORIES = ["Added", "Fixed", "Changed", "Removed", "Misc"]
CORE_CATEGORIES = ["Added", "Fixed", "Changed", "Removed"]

# Required file heading, e.g. "## v1.2.0 — 2026-03-02" (em dash separator).
HEADER_RE = re.compile(r"^##\s+v(\d+)\.(\d+)\.(\d+)\s+—\s+(\d{4}-\d{2}-\d{2})\s*$")
CATEGORY_RE = re.compile(r"^###\s+(.+?)\s*$")
ENTRY_RE = re.compile(r"^[-*]\s+(.*\S)\s*$")
FILENAME_VERSION_RE = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")


@dataclass
class Entry:
    text: str
    category: str
    line_no: int


@dataclass
class Changelog:
    path: Path
    name: str
    version: str | None = None
    version_key: tuple[int, int, int] = (0, 0, 0)
    date: str | None = None
    header_ok: bool = False
    header_problem: str | None = None
    entries: list[Entry] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        out = {c: 0 for c in ALLOWED_CATEGORIES}
        for e in self.entries:
            out[e.category] = out.get(e.category, 0) + 1
        return out


def version_key_from_name(name: str) -> tuple[int, int, int]:
    m = FILENAME_VERSION_RE.search(name)
    if not m:
        return (0, 0, 0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def parse_file(path: Path) -> Changelog:
    cl = Changelog(path=path, name=path.name)
    lines = path.read_text(encoding="utf-8").splitlines()

    first = next((ln for ln in lines if ln.strip()), "")
    m = HEADER_RE.match(first)
    if m:
        cl.header_ok = True
        cl.version = f"v{m.group(1)}.{m.group(2)}.{m.group(3)}"
        cl.version_key = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        cl.date = m.group(4)
    else:
        cl.header_ok = False
        cl.header_problem = (
            "no non-empty first line"
            if not first
            else f"first line is {first!r}, expected '## vX.Y.Z — YYYY-MM-DD'"
        )
        cl.version_key = version_key_from_name(path.name)
        if cl.version_key != (0, 0, 0):
            cl.version = "v{}.{}.{}".format(*cl.version_key)

    current = None
    for i, raw in enumerate(lines, start=1):
        cm = CATEGORY_RE.match(raw)
        if cm:
            current = cm.group(1)
            continue
        em = ENTRY_RE.match(raw)
        if em and current is not None:
            cl.entries.append(Entry(text=em.group(1), category=current, line_no=i))
    return cl


def load_dir(changelog_dir: Path) -> list[Changelog]:
    if not changelog_dir.is_dir():
        raise SystemExit(f"error: not a directory: {changelog_dir}")
    files = sorted(changelog_dir.glob("*.md"), key=lambda p: p.name)
    logs = [parse_file(p) for p in files]
    logs.sort(key=lambda c: (c.version_key, c.name))
    return logs


def add_dir_arg(parser, help_text: str = "Directory holding the changelog .md files.") -> None:
    parser.add_argument("changelog_dir", type=Path, help=help_text)


def add_json_arg(parser) -> None:
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
