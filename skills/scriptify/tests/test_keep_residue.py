import json
import shutil
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import keep_residue  # noqa: E402

from test_smoke_test import GOOD_SCRIPT  # noqa: E402


def test_rewrite_paths_converts_absolute_fixture_path(tmp_path):
    root = tmp_path / ".delegation-review" / "fixtures"
    (root / "x" / "good").mkdir(parents=True)
    manifest = {"scripts": [{"invocations": [
        {"argv": ["python3", "scripts/x.py", str(root / "x" / "good")]}]}]}
    n = keep_residue._rewrite_paths(manifest, {root})
    assert n == 1
    assert manifest["scripts"][0]["invocations"][0]["argv"][2] == \
        "{skill}/scripts/tests/fixtures/x/good"


def test_rewrite_paths_leaves_flag_tokens_alone(tmp_path):
    root = tmp_path / ".delegation-review" / "fixtures"
    root.mkdir(parents=True)
    manifest = {"scripts": [{"invocations": [
        {"argv": ["python3", "scripts/x.py", "--json"]}]}]}
    n = keep_residue._rewrite_paths(manifest, {root})
    assert n == 0
    assert manifest["scripts"][0]["invocations"][0]["argv"][2] == "--json"


def _make_review(tmp_path, target):
    """A target plus a review dir whose manifest points at real fixtures."""
    review = tmp_path / ".delegation-review"
    fixtures = review / "fixtures" / "toy_check"
    fixtures.mkdir(parents=True)
    (fixtures / "good.txt").write_text("all ok here")
    (fixtures / "bad.txt").write_text("nothing here")
    manifest = {
        "target_skill": str(target),
        "scripts": [{
            "path": "scripts/toy_check.py",
            "kind": "check",
            "invocations": [
                {"argv": [sys.executable, "scripts/toy_check.py",
                          str(fixtures / "good.txt")],
                 "expect_exit": 0}],
            "bad_data_invocation": {
                "argv": [sys.executable, "scripts/toy_check.py",
                         str(fixtures / "bad.txt")],
                "expect_exit_nonzero": True,
                "expect_stdout_contains": "missing_ok"},
            "bad_invocation": {
                "argv": [sys.executable, "scripts/toy_check.py"],
                "expect_exit_nonzero": True},
        }],
    }
    (review / "manifest.json").write_text(json.dumps(manifest))
    return review


def _make_target(tmp_path):
    target = tmp_path / "target"
    (target / "scripts").mkdir(parents=True)
    (target / "scripts" / "toy_check.py").write_text(GOOD_SCRIPT)
    (target / "SKILL.md").write_text("---\nname: t\ndescription: d\n---\n\n# T\n")
    return target


def test_install_green_in_place_and_relocated(tmp_path, capsys):
    target = _make_target(tmp_path)
    review = _make_review(tmp_path, target)
    code, err = keep_residue.install(target, review, 20.0)
    out = capsys.readouterr().out
    assert (code, err) == (0, None), out
    assert "in place:" in out and "from a relocated copy:" in out
    assert "FAIL" not in out
    assert (target / "scripts" / "tests" / "smoke_test.py").is_file()


def test_install_refuses_to_clobber_existing_fixtures(tmp_path):
    target = _make_target(tmp_path)
    review = _make_review(tmp_path, target)
    own = target / "scripts" / "tests" / "fixtures"
    own.mkdir(parents=True)
    (own / "mine.txt").write_text("do not delete me")

    code, err = keep_residue.install(target, review, 20.0)
    assert code == 2
    assert "--force" in err
    assert (own / "mine.txt").read_text() == "do not delete me"


def test_install_force_replaces_existing_fixtures(tmp_path):
    target = _make_target(tmp_path)
    review = _make_review(tmp_path, target)
    own = target / "scripts" / "tests" / "fixtures"
    own.mkdir(parents=True)
    (own / "mine.txt").write_text("do not delete me")

    code, err = keep_residue.install(target, review, 20.0, force=True)
    assert (code, err) == (0, None)
    assert not (own / "mine.txt").exists()


def test_relocated_residue_tests_the_copy_not_the_original(tmp_path):
    target = _make_target(tmp_path)
    review = _make_review(tmp_path, target)
    assert keep_residue.install(target, review, 20.0) == (0, None)

    copy = tmp_path / "moved"
    shutil.copytree(target, copy)
    # Break the ORIGINAL. A run that honoured the recorded absolute
    # target_skill would test the original and go red; rehoming keeps it green.
    (target / "scripts" / "toy_check.py").write_text("import sys; sys.exit(1)\n")
    code, tail = keep_residue._run_smoke(
        copy / "scripts" / "tests" / "manifest.json", 20.0)
    assert code == 0, tail
