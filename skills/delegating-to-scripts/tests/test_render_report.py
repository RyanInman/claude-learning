import json
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SKILL_DIR / "scripts" / "render_report.py"

INVENTORY = {
    "target": "/tmp/fake-skill",
    "frontmatter": {"name": "fake-skill", "description_chars": 200, "unexpected_keys": []},
    "body": {"lines": 40, "approx_tokens": 400},
    "steps": [
        {"id": "s1", "origin": "numbered-list", "heading_path": ["Workflow"],
         "line_start": 10, "line_end": 12, "approx_tokens": 55,
         "snippet": "List every .md file", "code_blocks": [],
         "mechanical_verb_hints": ["list"], "agent_tool_mentions": [],
         "mentions_existing_script": []},
        {"id": "s2", "origin": "numbered-list", "heading_path": ["Workflow"],
         "line_start": 13, "line_end": 15, "approx_tokens": 80,
         "snippet": "Write a narrative", "code_blocks": [],
         "mechanical_verb_hints": [], "agent_tool_mentions": [],
         "mentions_existing_script": []},
    ],
    "orphan_code_blocks": [], "scripts": [], "references": [], "assets": [],
    "stats": {"n_steps": 2, "n_steps_with_hints": 1, "n_existing_scripts": 0},
}

GOOD_CLASSIFICATION = {
    "target": "/tmp/fake-skill",
    "steps": [
        {"id": "s1", "class": "SCRIPT", "why": "pure file discovery",
         "proposed_script": {"name": "list_files.py",
                             "interface": "python3 scripts/list_files.py docs/ --json",
                             "stdout": "file list JSON",
                             "exit": "0 ok / 2 usage"}},
        {"id": "s2", "class": "CLAUDE", "why": "prose synthesis",
         "proposed_script": None},
    ],
}


def run(tmp_path, classification, inventory=INVENTORY, extra=()):
    c = tmp_path / "classification.json"
    i = tmp_path / "inventory.json"
    c.write_text(json.dumps(classification))
    i.write_text(json.dumps(inventory))
    return subprocess.run([sys.executable, str(SCRIPT), str(c), str(i), *extra],
                          capture_output=True, text=True, timeout=30)


def test_renders_table(tmp_path):
    r = run(tmp_path, GOOD_CLASSIFICATION)
    assert r.returncode == 0, r.stderr
    assert "## Delegation review: fake-skill" in r.stdout
    assert "1 of 2 steps" in r.stdout
    assert "| s1 |" in r.stdout and "| SCRIPT |" in r.stdout
    assert "| s2 |" in r.stdout and "| CLAUDE |" in r.stdout
    assert "list_files.py" in r.stdout
    # CLAUDE rows carry no interface
    s2_row = [l for l in r.stdout.splitlines() if l.startswith("| s2 |")][0]
    assert "list_files.py" not in s2_row


def test_unknown_id_exits_1(tmp_path):
    bad = {"target": "/tmp/fake-skill",
           "steps": GOOD_CLASSIFICATION["steps"] +
                    [{"id": "s9", "class": "CLAUDE", "why": "x", "proposed_script": None}]}
    r = run(tmp_path, bad)
    assert r.returncode == 1
    assert "s9" in r.stderr


def test_script_class_requires_interface(tmp_path):
    bad = {"target": "/tmp/fake-skill",
           "steps": [{"id": "s1", "class": "SCRIPT", "why": "x", "proposed_script": None},
                     {"id": "s2", "class": "CLAUDE", "why": "y", "proposed_script": None}]}
    r = run(tmp_path, bad)
    assert r.returncode == 1
    assert "proposed_script" in r.stderr


def test_unclassified_step_exits_1(tmp_path):
    bad = {"target": "/tmp/fake-skill", "steps": [GOOD_CLASSIFICATION["steps"][0]]}
    r = run(tmp_path, bad)
    assert r.returncode == 1
    assert "s2" in r.stderr


def test_missing_file_exits_2(tmp_path):
    r = subprocess.run([sys.executable, str(SCRIPT), "/nope.json", "/nope2.json"],
                       capture_output=True, text=True)
    assert r.returncode == 2
