#!/usr/bin/env python3
"""Tests for collect_facts.py, the harness collector.

The guardrail tier trusts this collector to decide assertions without a grader, so a silent bug
here is worse than grader variance: nobody argues with it. These cover the two behaviours the
guardrail tier depends on — tree diffing and manifest path resolution.

Run: python3 -m pytest test_collect_facts.py -q
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import collect_facts as cf


def _skill(root: Path, name: str) -> Path:
    """Build a minimal skill folder with one script and one fixture."""
    d = root / name
    (d / "scripts" / "tests" / "fixtures").mkdir(parents=True)
    (d / "SKILL.md").write_text("# skill\n")
    (d / "scripts" / "scan.py").write_text("import sys\nsys.exit(0)\n")
    (d / "scripts" / "tests" / "fixtures" / "good.md").write_text("ok\n")
    return d


def test_tree_diff_clean(tmp_path):
    base = _skill(tmp_path / "base", "s")
    target = _skill(tmp_path / "run", "s")
    diff = cf.tree_diff(base, target)
    assert diff == {"added": [], "removed": [], "modified": []}


def test_tree_diff_detects_added_and_modified(tmp_path):
    base = _skill(tmp_path / "base", "s")
    target = _skill(tmp_path / "run", "s")
    (target / "scripts" / "new.py").write_text("x = 1\n")
    (target / "SKILL.md").write_text("# rewritten\n")
    diff = cf.tree_diff(base, target)
    assert diff["added"] == ["scripts/new.py"]
    assert diff["modified"] == ["SKILL.md"]
    assert diff["removed"] == []


def test_manifest_skill_placeholder_resolves(tmp_path):
    """A {skill} token must expand before resolution.

    This is the defect a grader found in iteration-3: unexpanded tokens were reported as
    unresolved paths, which under the guardrail tier would fail a sound run.
    """
    target = _skill(tmp_path, "s")
    manifest = target / "scripts" / "tests" / "manifest.json"
    manifest.write_text(json.dumps({
        "target_skill": str(target),
        "scripts": [{
            "path": "scripts/scan.py",
            "invocations": [{
                "cwd": str(target),
                "argv": ["python3", "scripts/scan.py",
                         "{skill}/scripts/tests/fixtures/good.md"],
            }],
        }],
    }))
    res = cf.residue_facts(target)
    assert res["unresolved_paths"] == [], res["unresolved_paths"]
    assert res["stale_delegation_review_paths"] == []


def test_manifest_reports_a_genuinely_missing_path(tmp_path):
    """The expansion fix must not mask a real missing fixture."""
    target = _skill(tmp_path, "s")
    manifest = target / "scripts" / "tests" / "manifest.json"
    manifest.write_text(json.dumps({
        "target_skill": str(target),
        "scripts": [{
            "path": "scripts/scan.py",
            "invocations": [{
                "cwd": str(target),
                "argv": ["python3", "scripts/scan.py",
                         "{skill}/scripts/tests/fixtures/absent.md"],
            }],
        }],
    }))
    res = cf.residue_facts(target)
    assert len(res["unresolved_paths"]) == 1
    assert res["unresolved_paths"][0].endswith("absent.md")


def test_stale_delegation_review_path_is_flagged(tmp_path):
    """A path still pointing into .delegation-review/ means the residue was never re-homed."""
    target = _skill(tmp_path, "s")
    manifest = target / "scripts" / "tests" / "manifest.json"
    manifest.write_text(json.dumps({
        "target_skill": str(target),
        "scripts": [{
            "path": "scripts/scan.py",
            "invocations": [{
                "cwd": str(target),
                "argv": ["python3", "scripts/scan.py",
                         str(target / ".delegation-review" / "fixtures" / "good.md")],
            }],
        }],
    }))
    res = cf.residue_facts(target)
    assert len(res["stale_delegation_review_paths"]) == 1
