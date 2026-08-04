#!/usr/bin/env python3
"""
test_audit.py - stdlib-only fixture test runner for audit.py.

Run: python skills/review/tests/test_audit.py
Exit 0 = all tests passed, 1 = at least one failed.

Each test runs audit.main() against a fixture folder in fixtures/ and checks
the exit code and/or that a finding category+severity is present or absent.
Tasks 2-4 add one fixture pair (must-trip / must-not-trip) per new check and
a matching test function here -- follow the pattern below.
"""
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
sys.path.insert(0, str(TESTS_DIR.parent / "scripts"))
import audit  # noqa: E402

FAILURES = []


def check(label, condition):
    print(f"[{'ok' if condition else 'FAIL'}] {label}")
    if not condition:
        FAILURES.append(label)


def run_audit(fixture_name):
    """Run audit.main() --json against a fixture dir. Returns (exit_code, parsed_json)."""
    fixture_dir = FIXTURES_DIR / fixture_name
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = audit.main([str(fixture_dir), "--json"])
    return code, json.loads(buf.getvalue())


def has_finding(findings, category, severity=None):
    return any(f["category"] == category and (severity is None or f["severity"] == severity)
               for f in findings)


def test_clean_fixture_is_clean_and_exits_zero():
    code, data = run_audit("clean")
    check("clean fixture: exit code 0", code == 0)
    check("clean fixture: no findings", data["findings"] == [])


def test_missing_description_is_high_and_exits_one():
    # Regression test: proves the harness catches breakage of an existing check.
    code, data = run_audit("missing-description")
    check("missing-description: exit code 1", code == 1)
    check("missing-description: high 'description' finding present",
          has_finding(data["findings"], "description", "high"))


def test_short_description_is_medium_and_exits_one():
    code, data = run_audit("short-description")
    check("short-description: exit code 1", code == 1)
    check("short-description: medium 'description' finding present",
          has_finding(data["findings"], "description", "medium"))


def test_metrics_object_present_and_correct():
    code, data = run_audit("clean")
    metrics = data.get("metrics")
    check("metrics object present in JSON output", metrics is not None)
    if metrics is None:
        return
    check("metrics.description_chars matches top-level description_chars",
          metrics["description_chars"] == data["description_chars"])
    check("metrics.body_tokens matches top-level approx_body_tokens",
          metrics["body_tokens"] == data["approx_body_tokens"])
    check("metrics.combined_listing_chars equals description_chars (no when_to_use in fixture)",
          metrics["combined_listing_chars"] == metrics["description_chars"])
    check("metrics.trigger_phrase_density is an int",
          isinstance(metrics["trigger_phrase_density"], int))


def test_cc_only_field_is_info_not_high():
    code, data = run_audit("cc-only-field")
    check("cc-only-field: exit code 0 (info-only)", code == 0)
    check("cc-only-field: info 'frontmatter' finding present",
          has_finding(data["findings"], "frontmatter", "info"))
    check("cc-only-field: message names the Claude Code-only phrase",
          any("Claude Code-only field — fails upload to claude.ai/API" in f["message"]
              for f in data["findings"]))
    check("cc-only-field: no high 'frontmatter' finding for when_to_use",
          not has_finding(data["findings"], "frontmatter", "high"))
    check("clean fixture: no CC-only-field finding",
          not has_finding(run_audit("clean")[1]["findings"], "frontmatter", "info"))


def test_listing_cap_overflow_is_info_and_exits_zero():
    code, data = run_audit("listing-cap-overflow")
    check("listing-cap-overflow: exit code 0 (info-only)", code == 0)
    check("listing-cap-overflow: info 'listing' finding present",
          has_finding(data["findings"], "listing", "info"))
    check("listing-cap-overflow: message names the 1,536 cap and /doctor",
          any("1,536" in f["message"] and "/doctor" in f["suggestion"]
              for f in data["findings"] if f["category"] == "listing"))
    check("clean fixture: no listing-cap finding",
          not has_finding(run_audit("clean")[1]["findings"], "listing", "info"))


def test_name_dir_mismatch_is_medium_and_exits_one():
    code, data = run_audit("name-dir-mismatch")
    check("name-dir-mismatch: exit code 1", code == 1)
    check("name-dir-mismatch: medium 'frontmatter' finding present",
          has_finding(data["findings"], "frontmatter", "medium"))
    check("clean fixture: name matches folder, no mismatch finding",
          not has_finding(run_audit("clean")[1]["findings"], "frontmatter", "medium"))


def test_large_body_token_estimate_is_medium_and_exits_one():
    code, data = run_audit("large-body")
    check("large-body: exit code 1", code == 1)
    check("large-body: medium 'size' finding present",
          has_finding(data["findings"], "size", "medium"))
    check("large-body: message says 'recommended'",
          any("recommended" in f["message"] for f in data["findings"]
              if f["category"] == "size"))
    check("clean fixture: body well under token ceiling, no size finding",
          not has_finding(run_audit("clean")[1]["findings"], "size", "medium"))


def test_menu_anti_pattern_is_low_and_exits_one():
    code, data = run_audit("menu-anti-pattern")
    check("menu-anti-pattern: exit code 1", code == 1)
    check("menu-anti-pattern: low 'anti-pattern' finding present",
          has_finding(data["findings"], "anti-pattern", "low"))
    check("menu-anti-pattern: message names the 'or' chain",
          any("'or' chain" in f["message"] for f in data["findings"]
              if f["category"] == "anti-pattern"))


def test_menu_comma_list_does_not_fire():
    code, data = run_audit("menu-comma-list-ok")
    check("menu-comma-list-ok: no 'anti-pattern' finding (ordinary 'X, Y, or Z' enumeration)",
          not has_finding(data["findings"], "anti-pattern", "low"))


def test_fossil_deprecated_is_low_and_exits_one():
    code, data = run_audit("fossil-deprecated")
    check("fossil-deprecated: exit code 1", code == 1)
    check("fossil-deprecated: low 'anti-pattern' finding present",
          has_finding(data["findings"], "anti-pattern", "low"))
    check("fossil-deprecated: message mentions before/after/until/deprecated",
          any("before/after/until/deprecated" in f["message"] for f in data["findings"]
              if f["category"] == "anti-pattern"))


def test_fossil_reversed_order_is_low_and_exits_one():
    code, data = run_audit("fossil-reversed")
    check("fossil-reversed: exit code 1", code == 1)
    check("fossil-reversed: low 'anti-pattern' finding present (date-then-keyword order)",
          has_finding(data["findings"], "anti-pattern", "low"))


def test_fossil_reversed_across_sentence_does_not_fire():
    code, data = run_audit("fossil-reversed-ok")
    check("fossil-reversed-ok: no 'anti-pattern' finding (year and keyword split by sentence boundary)",
          not has_finding(data["findings"], "anti-pattern", "low"))


def test_fossil_bare_year_does_not_fire():
    code, data = run_audit("fossil-bare-year-ok")
    check("fossil-bare-year-ok: no 'anti-pattern' finding (bare year, no fossil keyword)",
          not has_finding(data["findings"], "anti-pattern", "low"))


def test_fossil_config_value_near_miss_does_not_fire():
    # Corpus FPs: an ordinary numeric config default/table value that happens
    # to look like a year, sitting near a fossil keyword ("before"/"flush").
    pat = audit.FOSSIL_PATTERN
    check("fossil near-miss: 'before process exit (default: 2000)' does not fire "
          "(config value, not a year)",
          not pat.search("before process exit (default: 2000)"))
    check("fossil near-miss: '2000 | Milliseconds to flush events before' does not "
          "fire (SDK options table row)",
          not pat.search("`2000` | Milliseconds to flush events before"))
    check("fossil genuine: 'Before August 2025, use the old API.' still fires",
          bool(pat.search("Before August 2025, use the old API.")))
    check("fossil genuine: 'deprecated since 2024' still fires",
          bool(pat.search("deprecated since 2024")))
    check("fossil month-name word-boundary: 'dismay 2024' does not fire "
          "('May' must be a whole word, not a substring of 'dismay')",
          not pat.search("dismay 2024, the situation changed"))


def test_name_redundancy_is_low_and_exits_one():
    code, data = run_audit("csv-parser")
    check("csv-parser: exit code 1", code == 1)
    check("csv-parser: low 'description' finding present for name-redundancy",
          any(f["category"] == "description" and f["severity"] == "low"
              and "restates the name" in f["message"] for f in data["findings"]))


def test_name_redundancy_long_sentence_does_not_fire():
    code, data = run_audit("log-formatter-ok")
    check("log-formatter-ok: no name-redundancy finding (first sentence >= 60 chars)",
          not any(f["category"] == "description" and "restates the name" in f["message"]
                  for f in data["findings"]))


def test_desc_shouting_is_low_and_exits_one():
    code, data = run_audit("desc-shouting")
    check("desc-shouting: exit code 1", code == 1)
    check("desc-shouting: low 'description' finding present for ALL-CAPS directives",
          any(f["category"] == "description" and f["severity"] == "low"
              and "ALL-CAPS directive" in f["message"] for f in data["findings"]))


def test_desc_do_not_does_not_fire():
    code, data = run_audit("desc-do-not-ok")
    check("desc-do-not-ok: exit code 0 ('Do NOT' excluded, no other caps directives)", code == 0)
    check("desc-do-not-ok: no ALL-CAPS directive finding",
          not any("ALL-CAPS directive" in f["message"] for f in data["findings"]))


def test_trigger_phrase_density_known_count():
    code, data = run_audit("trigger-density")
    check("trigger-density: metric value is 6 (2 quoted phrases + mentions/asks/says/trigger)",
          data["metrics"]["trigger_phrase_density"] == 6)


def test_trigger_phrase_density_in_report_header():
    buf = io.StringIO()
    with redirect_stdout(buf):
        audit.main([str(FIXTURES_DIR / "trigger-density")])
    report = buf.getvalue()
    check("trigger-density: human report header shows the metric",
          "triggers    : 6" in report)


def test_allowed_tools_broad_bash_is_info_and_exits_zero():
    code, data = run_audit("allowed-tools-broad")
    check("allowed-tools-broad: exit code 0 (info-only)", code == 0)
    check("allowed-tools-broad: info 'security' finding present",
          has_finding(data["findings"], "security", "info"))
    check("allowed-tools-broad: message names broad Bash/wildcard grants",
          any("unrestricted Bash" in f["message"] for f in data["findings"]
              if f["category"] == "security"))


def test_allowed_tools_scoped_does_not_fire():
    code, data = run_audit("allowed-tools-scoped-ok")
    check("allowed-tools-scoped-ok: no 'security' finding for a scoped Bash(git:*) grant",
          not has_finding(data["findings"], "security", "info"))


def test_allowed_tools_bash_star_is_broad():
    # Bash(*) has the same risk shape as a bare Bash grant; exercised directly
    # against the check function (same style as the exit-code expression test).
    findings = []
    audit.check_allowed_tools({"allowed-tools": "Bash(*)"}, findings)
    check("allowed-tools: 'Bash(*)' treated as broad grant",
          has_finding(findings, "security", "info"))


def test_reasoning_extraction_is_high_and_exits_one():
    code, data = run_audit("reasoning-extraction")
    check("reasoning-extraction: exit code 1", code == 1)
    check("reasoning-extraction: high 'anti-pattern' finding present",
          has_finding(data["findings"], "anti-pattern", "high"))
    check("reasoning-extraction: message cites the refusals-and-fallback doc",
          any("refusals-and-fallback" in f["message"] for f in data["findings"]
              if f["category"] == "anti-pattern" and f["severity"] == "high"))


def test_reasoning_explain_generic_does_not_fire():
    code, data = run_audit("reasoning-explain-ok")
    check("reasoning-explain-ok: no high 'anti-pattern' finding for generic 'explain your reasoning'",
          not has_finding(data["findings"], "anti-pattern", "high"))


def test_reasoning_extraction_mirrored_direction():
    # Noun-first phrasings (active or passive verb) must fire too; a noun-first
    # sentence WITHOUT the internal/chain-of-thought qualifier must not.
    # Exercised directly against the pattern (same style as the exit-code test).
    pat = audit.REASONING_EXTRACTION_PATTERN
    check("reasoning mirrored: 'Your internal reasoning should be included in the "
          "final response.' fires",
          bool(pat.search("Your internal reasoning should be included in the final response.")))
    check("reasoning mirrored: 'The model's internal reasoning must be shown to the "
          "user.' fires",
          bool(pat.search("The model's internal reasoning must be shown to the user.")))
    check("reasoning mirrored near-miss: 'Your reasoning should be included in the "
          "summary.' does not fire (no internal/chain-of-thought qualifier)",
          not pat.search("Your reasoning should be included in the summary."))
    check("reasoning mirrored near-miss: frontend-design planning-in-thinking "
          "sentence does not fire (active verb 'show', no be-form + participle)",
          not pat.search(
              "Try to do a lot of this planning and iteration in your thinking, "
              "and only show ideas to the user when you have higher confidence "
              "it'll delight them."))
    check("reasoning mirrored near-miss: 'explain your reasoning for each "
          "finding' does not fire (no internal/chain-of-thought qualifier)",
          not pat.search("explain your reasoning for each finding"))


def test_script_security_evil_script_flagged_fine_script_not():
    code, data = run_audit("script-security")
    check("script-security: exit code 1", code == 1)
    security_findings = [f for f in data["findings"] if f["category"] == "security"]
    check("script-security: at least one medium 'security' finding for scripts/evil.py",
          any(f["severity"] == "medium" and f["location"] == "scripts/evil.py"
              for f in security_findings))
    check("script-security: env+network finding present for scripts/evil.py",
          any("credential exfiltration" in f["message"] for f in security_findings
              if f["location"] == "scripts/evil.py"))
    check("script-security: URL-interpolation finding present for scripts/evil.py",
          any("external endpoint" in f["message"] for f in security_findings
              if f["location"] == "scripts/evil.py"))
    check("script-security: no 'security' finding for scripts/fine.py (env read, no network)",
          not any(f["location"] == "scripts/fine.py" for f in security_findings))


def test_security_markers_base64_injection_unicode_flagged():
    # The three injection-marker sub-patterns live in the fixture's own
    # SKILL.md body (not under tests/fixtures/<name>/tests/), so the audit of
    # the fixture folder scans them fine.
    code, data = run_audit("security-markers")
    check("security-markers: exit code 1", code == 1)
    security_findings = [f for f in data["findings"] if f["category"] == "security"]
    check("security-markers: base64-blob finding present",
          any("base64" in f["message"] for f in security_findings))
    check("security-markers: prompt-injection finding present",
          any("prompt-injection" in f["message"] for f in security_findings))
    check("security-markers: Unicode-smuggling finding names U+200B",
          any("U+200B" in f["message"] for f in security_findings))


def test_security_markers_near_miss_does_not_fire():
    code, data = run_audit("security-markers-ok")
    check("security-markers-ok: no 'security' finding (short base64-ish string, "
          "ordinary 'ignore the previous section' wording, no control chars)",
          not any(f["category"] == "security" for f in data["findings"]))


def test_self_audit_clean():
    # Codifies the self-audit gate: audit.py run against the review skill itself
    # (the skill this tests/ dir belongs to) must emit nothing above INFO and
    # exit 0 -- so future regex edits can't silently break self-match avoidance.
    skill_dir = TESTS_DIR.parent
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = audit.main([str(skill_dir), "--json"])
    data = json.loads(buf.getvalue())
    above_info = [f for f in data["findings"] if f["severity"] != "info"]
    check("self-audit: no findings above INFO on skills/review",
          above_info == [])
    check("self-audit: exit code 0", code == 0)


def test_exit_code_expression_info_only_and_mixed():
    # No existing check emits an INFO finding yet (Task 3 adds the first ones),
    # so the info-only exit-code path is exercised directly against synthetic
    # finding lists rather than a fixture.
    def finding(severity):
        return {"severity": severity, "category": "x", "message": "m",
                "suggestion": "s", "location": "SKILL.md"}

    check("exit-code expr: no findings -> 0", audit._exit_code([]) == 0)
    check("exit-code expr: info-only findings -> 0",
          audit._exit_code([finding("info"), finding("info")]) == 0)
    check("exit-code expr: info + medium findings -> 1",
          audit._exit_code([finding("info"), finding("medium")]) == 1)


def main():
    test_clean_fixture_is_clean_and_exits_zero()
    test_missing_description_is_high_and_exits_one()
    test_short_description_is_medium_and_exits_one()
    test_cc_only_field_is_info_not_high()
    test_listing_cap_overflow_is_info_and_exits_zero()
    test_name_dir_mismatch_is_medium_and_exits_one()
    test_large_body_token_estimate_is_medium_and_exits_one()
    test_metrics_object_present_and_correct()
    test_menu_anti_pattern_is_low_and_exits_one()
    test_menu_comma_list_does_not_fire()
    test_fossil_deprecated_is_low_and_exits_one()
    test_fossil_reversed_order_is_low_and_exits_one()
    test_fossil_reversed_across_sentence_does_not_fire()
    test_fossil_bare_year_does_not_fire()
    test_fossil_config_value_near_miss_does_not_fire()
    test_name_redundancy_is_low_and_exits_one()
    test_name_redundancy_long_sentence_does_not_fire()
    test_desc_shouting_is_low_and_exits_one()
    test_desc_do_not_does_not_fire()
    test_trigger_phrase_density_known_count()
    test_trigger_phrase_density_in_report_header()
    test_allowed_tools_broad_bash_is_info_and_exits_zero()
    test_allowed_tools_scoped_does_not_fire()
    test_allowed_tools_bash_star_is_broad()
    test_reasoning_extraction_is_high_and_exits_one()
    test_reasoning_explain_generic_does_not_fire()
    test_reasoning_extraction_mirrored_direction()
    test_script_security_evil_script_flagged_fine_script_not()
    test_security_markers_base64_injection_unicode_flagged()
    test_security_markers_near_miss_does_not_fire()
    test_self_audit_clean()
    test_exit_code_expression_info_only_and_mixed()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for label in FAILURES:
            print(f"  - {label}")
        return 1
    print("all tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
