import json
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SKILL_DIR / "scripts" / "inventory.py"
FIXTURE_A = SKILL_DIR / "evals" / "fixtures" / "changelog-checker"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True, timeout=60)


def test_fixture_a_step_anchors():
    r = run(str(FIXTURE_A))
    assert r.returncode == 0, r.stderr
    inv = json.loads(r.stdout)
    assert inv["frontmatter"]["name"] == "changelog-checker"
    assert inv["stats"]["n_steps"] == 7
    ids = [s["id"] for s in inv["steps"]]
    assert ids == [f"s{i}" for i in range(1, 8)]
    assert all(s["origin"] == "numbered-list" for s in inv["steps"])
    assert all(s["approx_tokens"] >= 1 for s in inv["steps"])
    assert all(s["line_start"] >= 1 for s in inv["steps"])


def test_fixture_a_hints():
    inv = json.loads(run(str(FIXTURE_A)).stdout)
    steps = {s["id"]: s for s in inv["steps"]}
    assert "list" in steps["s1"]["mechanical_verb_hints"]
    assert "check" in steps["s2"]["mechanical_verb_hints"]
    assert "count" in steps["s3"]["mechanical_verb_hints"]
    assert "render" in steps["s5"]["mechanical_verb_hints"]
    # trap step: 'verify' hint present even though the step is CLAUDE work
    assert "verify" in steps["s7"]["mechanical_verb_hints"]
    assert steps["s4"]["agent_tool_mentions"] == []
    assert inv["stats"]["n_existing_scripts"] == 0


def test_accepts_skill_md_path():
    r = run(str(FIXTURE_A / "SKILL.md"))
    assert r.returncode == 0
    assert json.loads(r.stdout)["stats"]["n_steps"] == 7


def test_non_skill_dir_exits_2(tmp_path):
    r = run(str(tmp_path))
    assert r.returncode == 2
    assert "SKILL.md" in r.stderr


def test_out_flag_summary_has_no_step_text(tmp_path):
    out = tmp_path / "inv.json"
    r = run(str(FIXTURE_A), "--out", str(out))
    assert r.returncode == 0
    inv = json.loads(out.read_text())
    assert inv["stats"]["n_steps"] == 7
    # stdout is counts + hints only, never step text
    assert "release narrative" not in r.stdout
    assert "verbs=" in r.stdout


def test_help():
    r = run("--help")
    assert r.returncode == 0
    assert "target-skill-dir" in r.stdout or "target_skill_dir" in r.stdout
