import json
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SKILL_DIR / "scripts" / "inventory.py"
FIXTURE_A = SKILL_DIR / "evals" / "fixtures" / "changelog-checker"
FIXTURE_WELL_DELEGATED = SKILL_DIR / "evals" / "fixtures" / "well-delegated"


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


def _write_skill(tmp_path, body, frontmatter="name: t\ndescription: d"):
    d = tmp_path / "t"
    d.mkdir()
    (d / "SKILL.md").write_text(f"---\n{frontmatter}\n---\n\n{body}", encoding="utf-8")
    return d


def test_numbered_headings_anchor(tmp_path):
    # "### 1. Foo" matches neither the Step-N heading nor the numbered-list
    # pattern; before this it silently produced zero steps.
    d = _write_skill(tmp_path, "# T\n\n## Workflow\n\n### 1. Extract the metrics\n\n"
                               "Run the analyzer.\n\n### 2. Interpret them\n\nJudge.\n")
    inv = json.loads(run(str(d)).stdout)
    assert [s["origin"] for s in inv["steps"]] == ["numbered-heading"] * 2
    assert inv["steps"][0]["snippet"] == "1. Extract the metrics"


def test_prose_only_falls_back_to_headings(tmp_path):
    d = _write_skill(tmp_path, "# T\n\n## Workflow\n\n### Locate the config\n\n"
                               "Read it.\n\n### Validate\n\nCheck the fields.\n\n"
                               "### Output the report\n\nPrint it.\n\n"
                               "## Output format\n\nA table.\n\n"
                               "## Gotchas\n\nWatch out.\n")
    inv = json.loads(run(str(d)).stdout)
    snippets = [s["snippet"] for s in inv["steps"]]
    assert {s["origin"] for s in inv["steps"]} == {"heading-fallback"}
    # dropped: the empty "Workflow" container, "Output format", "Gotchas".
    # kept: "Output the report", which only a prefix match would have eaten.
    assert snippets == ["Locate the config", "Validate", "Output the report"]


def test_fallback_only_when_nothing_else_matched(tmp_path):
    d = _write_skill(tmp_path, "# T\n\n## Workflow\n\n1. Do the thing.\n\n"
                               "## Other section\n\nProse here.\n")
    inv = json.loads(run(str(d)).stdout)
    assert [s["origin"] for s in inv["steps"]] == ["numbered-list"]


def test_bare_stem_is_not_a_mention(tmp_path):
    d = _write_skill(tmp_path, "# T\n\n## Workflow\n\n1. Check the data carefully.\n")
    (d / "scripts").mkdir()
    (d / "scripts" / "check.py").write_text("import argparse\n", encoding="utf-8")
    inv = json.loads(run(str(d), "--no-probe").stdout)
    # body says "Check", never "check.py": a stem match here would wrongly
    # route the step to ALREADY_DELEGATED
    assert inv["scripts"][0]["mentioned_in_body"] is False
    assert inv["steps"][0]["mentions_existing_script"] == []


def test_claude_code_frontmatter_is_expected(tmp_path):
    d = _write_skill(tmp_path, "# T\n\n1. Do it.\n",
                     frontmatter="name: t\ndescription: d\n"
                                 "disable-model-invocation: true\nuser-invocable: true")
    inv = json.loads(run(str(d)).stdout)
    assert inv["frontmatter"]["unexpected_keys"] == []


def test_well_delegated_fixture_signals():
    r = run(str(FIXTURE_WELL_DELEGATED))
    assert r.returncode == 0, r.stderr
    inv = json.loads(r.stdout)
    assert len(inv["scripts"]) == 1
    sc = inv["scripts"][0]
    assert sc["mentioned_in_body"] is True
    assert sc["has_argparse"] is True
    assert sc["has_docstring"] is True
    assert sc["help_ok"] is True
