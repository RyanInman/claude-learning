import json
import subprocess
import sys
import textwrap
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SKILL_DIR / "scripts" / "smoke_test.py"

GOOD_SCRIPT = textwrap.dedent('''\
    #!/usr/bin/env python3
    """toy checker. Exits 0 if the file contains 'ok', else 1 with a finding."""
    import argparse, sys
    p = argparse.ArgumentParser(description="toy checker")
    p.add_argument("file")
    a = p.parse_args()
    text = open(a.file).read()
    if "ok" in text:
        print("[]")
        sys.exit(0)
    print("finding: missing_ok")
    sys.exit(1)
''')

INTERACTIVE_SCRIPT = textwrap.dedent('''\
    #!/usr/bin/env python3
    import argparse
    p = argparse.ArgumentParser()
    p.parse_args()
    answer = input("continue? ")
    print(answer)
''')


def make_target(tmp_path):
    target = tmp_path / "target"
    (target / "scripts").mkdir(parents=True)
    (target / "scripts" / "toy_check.py").write_text(GOOD_SCRIPT)
    (target / "good.txt").write_text("all ok here")
    (target / "bad.txt").write_text("nothing here")
    return target


def manifest_for(target, expect_exit_good=0):
    return {
        "target_skill": str(target),
        "scripts": [{
            "path": "scripts/toy_check.py",
            "kind": "check",
            "invocations": [
                {"argv": [sys.executable, "scripts/toy_check.py", "good.txt"],
                 "expect_exit": expect_exit_good,
                 "expect_stdout_json": True}],
            "bad_data_invocation": {
                "argv": [sys.executable, "scripts/toy_check.py", "bad.txt"],
                "expect_exit_nonzero": True,
                "expect_stdout_contains": "missing_ok"},
            "bad_invocation": {
                "argv": [sys.executable, "scripts/toy_check.py"],
                "expect_exit_nonzero": True},
        }],
    }


def run(manifest_path, *extra):
    return subprocess.run([sys.executable, str(SCRIPT), str(manifest_path), *extra],
                          capture_output=True, text=True, timeout=120)


def test_all_pass(tmp_path):
    target = make_target(tmp_path)
    mf = tmp_path / "manifest.json"
    mf.write_text(json.dumps(manifest_for(target)))
    r = run(mf)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "FAIL" not in r.stdout


def test_wrong_expect_exit_fails(tmp_path):
    target = make_target(tmp_path)
    mf = tmp_path / "manifest.json"
    mf.write_text(json.dumps(manifest_for(target, expect_exit_good=3)))
    r = run(mf)
    assert r.returncode == 1
    assert "FAIL" in r.stdout


def test_interactive_script_flagged(tmp_path):
    target = make_target(tmp_path)
    (target / "scripts" / "toy_check.py").write_text(INTERACTIVE_SCRIPT)
    mf = tmp_path / "manifest.json"
    m = manifest_for(target)
    m["scripts"][0]["invocations"][0]["argv"] = [sys.executable, "scripts/toy_check.py"]
    m["scripts"][0]["invocations"][0].pop("expect_stdout_json")
    mf.write_text(json.dumps(m))
    r = run(mf, "--timeout", "10")
    assert r.returncode == 1
    # input() with stdin=DEVNULL raises EOFError -> nonzero exit -> exit mismatch FAIL;
    # a /dev/tty reader would hit the timeout -> 'interactive-or-hung'
    assert "FAIL" in r.stdout


def test_check_without_bad_data_rejected(tmp_path):
    target = make_target(tmp_path)
    m = manifest_for(target)
    del m["scripts"][0]["bad_data_invocation"]
    mf = tmp_path / "manifest.json"
    mf.write_text(json.dumps(m))
    r = run(mf)
    assert r.returncode == 2
    assert "bad_data_invocation" in r.stderr


def test_garbage_manifest_exits_2(tmp_path):
    mf = tmp_path / "manifest.json"
    mf.write_text("{not json")
    r = run(mf)
    assert r.returncode == 2


def test_json_output(tmp_path):
    target = make_target(tmp_path)
    mf = tmp_path / "manifest.json"
    mf.write_text(json.dumps(manifest_for(target)))
    r = run(mf, "--json")
    assert r.returncode == 0
    results = json.loads(r.stdout)
    checks = {c["check"] for c in results}
    assert {"exists", "help", "fixture-run[0]", "bad-data", "bad-args"} <= checks
