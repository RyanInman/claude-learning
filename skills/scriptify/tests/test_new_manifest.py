import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import new_manifest  # noqa: E402
import smoke_test  # noqa: E402


def test_kind_reads_the_exit_spec():
    assert new_manifest._kind("0 clean / 1 findings / 2 usage") == "check"
    assert new_manifest._kind("0 written / 2 usage") == "transform"


CLS = {"steps": [
    {"id": "s1", "class": "SCRIPT", "why": "same check every run",
     "proposed_script": {
         "name": "check_headings.py",
         "interface": "python3 scripts/check_headings.py changelogs/ --json",
         "stdout": "findings JSON",
         "exit": "0 clean / 1 findings / 2 usage"}},
    {"id": "s2", "class": "CLAUDE", "why": "reasonable runs should differ",
     "proposed_script": None},
]}


def test_scaffold_round_trips_with_only_todo_errors(tmp_path):
    fixtures = str(tmp_path / "fixtures")
    m, seen = new_manifest.scaffold(CLS, tmp_path, fixtures)
    assert seen == {"check_headings.py": ["s1"]}

    errs = smoke_test._schema_errors(m)
    # Every error must be a leftover TODO -- the scaffold's structure is
    # otherwise complete, so a run only has to fill in expectations.
    assert errs, "scaffold must not pass validation with TODOs still in it"
    assert all("is still 'TODO:" in e for e in errs), errs
    assert set(errs) == set(smoke_test._todo_errors(m))
