"""Tests for ``scripts/mock_deploy.py`` — the dry-run-only mock deploy CLI.

The contract (``standards/build-orchestration.md`` section 5's deploy
deny-list, section 1's "validate-only command the human may run") is that this
script can never trigger a real deploy, so the failure mode that matters most
is a test that would let ``--dry-run`` disappear from the invoked command.
``subprocess.run`` is mocked everywhere in this file: the suite never invokes
the real ``sf`` CLI.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts import mock_deploy  # noqa: E402


# --------------------------------------------------------------------------
# Fixture helpers
# --------------------------------------------------------------------------

PACKAGE_XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>{members}</members>
        <name>{type_name}</name>
    </types>
    <version>{version}</version>
</Package>
"""


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_build(tmp_path: Path) -> Path:
    """A minimal two-step build: M1-S01 (object-model) and M1-S02 (ui),
    mirroring the shape of examples/builds/case-onboarding.
    """
    build_dir = tmp_path / "build"
    artefacts = build_dir / "artefacts"

    # M1-S01: a field under objects/Case/fields/, plus its own package.xml.
    _write(
        artefacts / "M1-S01" / "objects" / "Case" / "fields" / "Severity__c.field-meta.xml",
        "<CustomField><fullName>Severity__c</fullName></CustomField>",
    )
    _write(
        artefacts / "M1-S01" / "package.xml",
        PACKAGE_XML_TEMPLATE.format(members="Case.Severity__c", type_name="CustomField", version="61.0"),
    )

    # M1-S02: a layout under layouts/, plus its own package.xml (no version
    # element deliberately absent from S01 order matters only if S01 lacked one).
    _write(
        artefacts / "M1-S02" / "layouts" / "Case-Case Support Layout.layout-meta.xml",
        "<Layout><fullName>Case-Case Support Layout</fullName></Layout>",
    )
    _write(
        artefacts / "M1-S02" / "package.xml",
        PACKAGE_XML_TEMPLATE.format(members="Case-Case Support Layout", type_name="Layout", version="62.0"),
    )

    plan = {
        "artefacts_root": "artefacts",
        "steps": [
            {"id": "M1-S01", "milestone": "M1", "status": "documented"},
            {"id": "M1-S02", "milestone": "M1", "status": "built"},
            {"id": "M2-S01", "milestone": "M2", "status": "pending"},
        ],
    }
    _write(build_dir / "plan.json", json.dumps(plan, indent=2))
    return build_dir


# --------------------------------------------------------------------------
# select_steps
# --------------------------------------------------------------------------

def test_select_steps_default_uses_status_allowlist(tmp_path):
    build_dir = make_build(tmp_path)
    plan = mock_deploy.load_plan(build_dir / "plan.json")
    selected = mock_deploy.select_steps(plan, [], [])
    assert [s["id"] for s in selected] == ["M1-S01", "M1-S02"]  # M2-S01 is pending


def test_select_steps_by_milestone_ignores_status(tmp_path):
    build_dir = make_build(tmp_path)
    plan = mock_deploy.load_plan(build_dir / "plan.json")
    selected = mock_deploy.select_steps(plan, ["M2"], [])
    assert [s["id"] for s in selected] == ["M2-S01"]  # pending, but explicitly named


def test_select_steps_by_step_id(tmp_path):
    build_dir = make_build(tmp_path)
    plan = mock_deploy.load_plan(build_dir / "plan.json")
    selected = mock_deploy.select_steps(plan, [], ["M1-S01"])
    assert [s["id"] for s in selected] == ["M1-S01"]


# --------------------------------------------------------------------------
# Artefact tree assembly
# --------------------------------------------------------------------------

def test_copy_artefacts_preserves_paths_and_excludes_package_xml(tmp_path):
    build_dir = make_build(tmp_path)
    dest = tmp_path / "force-app" / "main" / "default"
    result = mock_deploy.copy_artefacts(build_dir, "artefacts", ["M1-S01", "M1-S02"], dest)
    copied = result.copied

    copied_str = {str(p) for p in copied}
    assert copied_str == {
        str(Path("objects/Case/fields/Severity__c.field-meta.xml")),
        str(Path("layouts/Case-Case Support Layout.layout-meta.xml")),
    }
    # package.xml must never be copied into the source tree.
    assert not any(p.name == "package.xml" for p in copied)
    assert not (dest / "package.xml").exists()
    # M1-S01 and M1-S02 each contribute exactly one skipped package.xml.
    assert result.skipped == 2

    # Subfolders are preserved exactly.
    assert (dest / "objects" / "Case" / "fields" / "Severity__c.field-meta.xml").is_file()
    assert (dest / "layouts" / "Case-Case Support Layout.layout-meta.xml").is_file()


def test_copy_artefacts_skips_missing_step_dir(tmp_path):
    build_dir = make_build(tmp_path)
    dest = tmp_path / "out"
    # M2-S01 has no artefacts directory on disk; must not raise.
    result = mock_deploy.copy_artefacts(build_dir, "artefacts", ["M2-S01"], dest)
    assert result.copied == []
    assert result.skipped == 0


def test_copy_artefacts_copies_non_xml_body_beside_meta_xml(tmp_path):
    build_dir = make_build(tmp_path)
    dest = tmp_path / "out"
    _write(
        build_dir / "artefacts" / "M1-S01" / "email" / "case_intake" / "Case_Acknowledgement.email",
        "<messaging/plain_text>Hi</messaging/plain_text>",
    )
    _write(
        build_dir / "artefacts" / "M1-S01" / "email" / "case_intake" / "Case_Acknowledgement.email-meta.xml",
        "<EmailTemplate><fullName>Case_Acknowledgement</fullName></EmailTemplate>",
    )
    result = mock_deploy.copy_artefacts(build_dir, "artefacts", ["M1-S01"], dest)

    copied_str = {str(p) for p in result.copied}
    assert str(Path("email/case_intake/Case_Acknowledgement.email")) in copied_str
    assert str(Path("email/case_intake/Case_Acknowledgement.email-meta.xml")) in copied_str
    assert (dest / "email" / "case_intake" / "Case_Acknowledgement.email").is_file()


def test_copy_artefacts_copies_cls_and_its_meta_xml(tmp_path):
    build_dir = make_build(tmp_path)
    dest = tmp_path / "out"
    _write(build_dir / "artefacts" / "M1-S01" / "classes" / "CaseService.cls", "public class CaseService {}")
    _write(
        build_dir / "artefacts" / "M1-S01" / "classes" / "CaseService.cls-meta.xml",
        "<ApexClass><apiVersion>62.0</apiVersion></ApexClass>",
    )
    result = mock_deploy.copy_artefacts(build_dir, "artefacts", ["M1-S01"], dest)

    copied_str = {str(p) for p in result.copied}
    assert str(Path("classes/CaseService.cls")) in copied_str
    assert str(Path("classes/CaseService.cls-meta.xml")) in copied_str


def test_copy_artefacts_excludes_markdown_build_notes(tmp_path):
    build_dir = make_build(tmp_path)
    dest = tmp_path / "out"
    _write(build_dir / "artefacts" / "M1-S01" / "deploy-order.md", "# Deploy order\n")
    _write(
        build_dir / "artefacts" / "M1-S01" / "queue-retirement-runbook.md",
        "# Queue retirement runbook\n",
    )
    result = mock_deploy.copy_artefacts(build_dir, "artefacts", ["M1-S01"], dest)

    copied_names = {p.name for p in result.copied}
    assert "deploy-order.md" not in copied_names
    assert "queue-retirement-runbook.md" not in copied_names
    assert not (dest / "deploy-order.md").exists()
    assert not (dest / "queue-retirement-runbook.md").exists()


def test_copy_artefacts_copies_nested_lwc_bundle_whole(tmp_path):
    build_dir = make_build(tmp_path)
    dest = tmp_path / "out"
    _write(build_dir / "artefacts" / "M1-S01" / "lwc" / "foo" / "foo.js", "export default class {}")
    _write(build_dir / "artefacts" / "M1-S01" / "lwc" / "foo" / "foo.html", "<template></template>")
    _write(
        build_dir / "artefacts" / "M1-S01" / "lwc" / "foo" / "foo.js-meta.xml",
        "<LightningComponentBundle/>",
    )
    result = mock_deploy.copy_artefacts(build_dir, "artefacts", ["M1-S01"], dest)

    copied_str = {str(p) for p in result.copied}
    assert str(Path("lwc/foo/foo.js")) in copied_str
    assert str(Path("lwc/foo/foo.html")) in copied_str
    assert str(Path("lwc/foo/foo.js-meta.xml")) in copied_str
    assert (dest / "lwc" / "foo" / "foo.js").is_file()
    assert (dest / "lwc" / "foo" / "foo.html").is_file()
    assert (dest / "lwc" / "foo" / "foo.js-meta.xml").is_file()


# --------------------------------------------------------------------------
# sfdx-project.json version pick
# --------------------------------------------------------------------------

def test_pick_api_version_uses_highest_not_first(tmp_path):
    build_dir = make_build(tmp_path)
    # M1-S01's package.xml declares 61.0, M1-S02's declares 62.0; the higher
    # of the two wins even though M1-S01 comes first in step order.
    resolution = mock_deploy.pick_api_version(build_dir, "artefacts", ["M1-S01", "M1-S02"])
    assert resolution.version == "62.0"
    assert resolution.source == "highest of: M1-S01=61.0, M1-S02=62.0"


def test_pick_api_version_uses_highest_regardless_of_argument_order(tmp_path):
    build_dir = make_build(tmp_path)
    # Same two steps, reversed order: the higher version (62.0, from M1-S02)
    # still wins even though it is now listed first.
    resolution = mock_deploy.pick_api_version(build_dir, "artefacts", ["M1-S02", "M1-S01"])
    assert resolution.version == "62.0"


def test_pick_api_version_skips_missing_and_uses_remaining(tmp_path):
    build_dir = make_build(tmp_path)
    # M2-S01 has no package.xml at all (missing file, skipped); M1-S02 is the
    # only one left with a usable <version>.
    resolution = mock_deploy.pick_api_version(build_dir, "artefacts", ["M2-S01", "M1-S02"])
    assert resolution.version == "62.0"
    assert resolution.source == "highest of: M1-S02=62.0"


def test_pick_api_version_falls_back_when_none_found(tmp_path):
    build_dir = make_build(tmp_path)
    resolution = mock_deploy.pick_api_version(build_dir, "artefacts", ["M2-S01"])
    assert resolution.version == mock_deploy.DEFAULT_API_VERSION
    assert resolution.version == "62.0"
    assert resolution.source.startswith("fallback")


def test_pick_api_version_max_across_more_than_two_mixed_versions(tmp_path):
    # M3-S03 needs >= 64.0 for a property the org rejects at 62.0; M4-S01
    # targets 67.0 Apex; M1-S01 (built earliest) still says 61.0. The highest
    # across all three — 67.0 — must win regardless of step order.
    build_dir = make_build(tmp_path)
    _write(
        build_dir / "artefacts" / "M3-S03" / "package.xml",
        PACKAGE_XML_TEMPLATE.format(members="Case.Foo__c", type_name="CustomField", version="64.0"),
    )
    _write(
        build_dir / "artefacts" / "M4-S01" / "package.xml",
        PACKAGE_XML_TEMPLATE.format(members="MyClass", type_name="ApexClass", version="67.0"),
    )
    resolution = mock_deploy.pick_api_version(
        build_dir, "artefacts", ["M1-S01", "M3-S03", "M4-S01"]
    )
    assert resolution.version == "67.0"
    assert resolution.source == "highest of: M1-S01=61.0, M3-S03=64.0, M4-S01=67.0"


def test_write_sfdx_project_content(tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    path = mock_deploy.write_sfdx_project(out_dir, "61.0")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["sourceApiVersion"] == "61.0"
    assert payload["packageDirectories"] == [{"path": "force-app", "default": True}]


# --------------------------------------------------------------------------
# Manifest merge
# --------------------------------------------------------------------------

def test_merge_package_xml_unions_and_sorts_members_and_types(tmp_path):
    p1 = tmp_path / "a.xml"
    p2 = tmp_path / "b.xml"
    _write(
        p1,
        """<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case.Severity__c</members>
        <members>Case.Origin</members>
        <name>CustomField</name>
    </types>
    <version>62.0</version>
</Package>
""",
    )
    _write(
        p2,
        """<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case-Case Support Layout</members>
        <name>Layout</name>
    </types>
    <types>
        <members>Case.Severity__c</members>
        <name>CustomField</name>
    </types>
    <version>62.0</version>
</Package>
""",
    )
    merged = mock_deploy.merge_package_xml([p1, p2], "62.0")

    # Types sorted alphabetically: CustomField before Layout.
    custom_field_idx = merged.index("<name>CustomField</name>")
    layout_idx = merged.index("<name>Layout</name>")
    assert custom_field_idx < layout_idx

    # Members deduplicated (Case.Severity__c appeared in both files) and sorted.
    field_members_block = merged.split("<name>CustomField</name>")[0]
    assert field_members_block.count("Case.Severity__c") == 1
    origin_idx = merged.index("Case.Origin")
    severity_idx = merged.index("Case.Severity__c")
    assert origin_idx < severity_idx  # "Origin" < "Severity__c" alphabetically

    assert "<version>62.0</version>" in merged
    assert merged.startswith('<?xml version="1.0" encoding="UTF-8"?>')


def test_merge_package_xml_ignores_missing_files(tmp_path):
    missing = tmp_path / "does-not-exist.xml"
    merged = mock_deploy.merge_package_xml([missing], "62.0")
    assert "<types>" not in merged
    assert "<version>62.0</version>" in merged


def test_resolve_manifest_always_uses_steps_merge_when_report_matches(tmp_path):
    # F-18 fix: the manifest is always the fresh steps' merge. When a
    # single-milestone report exists and agrees with it, that merge is what
    # gets used (the report's identical text would do just as well) and no
    # warning is raised.
    build_dir = make_build(tmp_path)
    report_xml = mock_deploy.merge_package_xml(
        [build_dir / "artefacts" / "M1-S01" / "package.xml",
         build_dir / "artefacts" / "M1-S02" / "package.xml"],
        "62.0",
    )
    _write(build_dir / "reports" / "MILESTONE-M1-package.xml", report_xml)

    resolution = mock_deploy.resolve_manifest_text(
        build_dir, "artefacts", ["M1"], [], ["M1-S01", "M1-S02"], "62.0"
    )
    assert resolution.source.startswith("merged:")
    assert resolution.warning is None
    assert "matches" in resolution.drift_note
    assert "CustomField" in resolution.xml_text
    assert "Layout" in resolution.xml_text


def test_resolve_manifest_merges_when_report_missing(tmp_path):
    build_dir = make_build(tmp_path)
    # No MILESTONE-M1-package.xml on disk -> merge is used silently.
    resolution = mock_deploy.resolve_manifest_text(
        build_dir, "artefacts", ["M1"], [], ["M1-S01", "M1-S02"], "62.0"
    )
    assert resolution.source.startswith("merged:")
    assert resolution.warning is None
    assert resolution.drift_note == ""
    assert "CustomField" in resolution.xml_text
    assert "Layout" in resolution.xml_text


def test_resolve_manifest_merges_when_step_filter_used(tmp_path):
    build_dir = make_build(tmp_path)
    _write(
        build_dir / "reports" / "MILESTONE-M1-package.xml",
        PACKAGE_XML_TEMPLATE.format(members="Case", type_name="CustomObject", version="62.0"),
    )
    # --step was used alongside --milestone -> the report is not even
    # consulted (the single-milestone shortcut requires no --step).
    resolution = mock_deploy.resolve_manifest_text(
        build_dir, "artefacts", ["M1"], ["M1-S01"], ["M1-S01"], "62.0"
    )
    assert resolution.source.startswith("merged:")
    assert resolution.warning is None
    assert resolution.drift_note == ""


# --------------------------------------------------------------------------
# F-18: stale milestone-report manifest drift
# --------------------------------------------------------------------------

def test_diff_manifest_types_identical_is_empty():
    types = {"CustomField": {"Case.Severity__c"}}
    assert mock_deploy.diff_manifest_types(types, dict(types)) == []


def test_diff_manifest_types_reports_both_sides():
    report_types = {"CompactLayout": {"Case_Intake"}}
    merged_types = {"CustomField": {"Case.Case_Intake"}}
    diff = mock_deploy.diff_manifest_types(report_types, merged_types)
    assert ("CompactLayout", "Case_Intake", "report-only") in diff
    assert ("CustomField", "Case.Case_Intake", "steps-only") in diff


def test_resolve_manifest_drift_warns_and_uses_steps_merge(tmp_path):
    build_dir = make_build(tmp_path)
    # Stale report: still names the old CompactLayout member that step
    # M1-S01's own package.xml no longer has (it now has CustomField
    # Case.Case_Intake instead) — the exact F-18 scenario.
    stale_report = PACKAGE_XML_TEMPLATE.format(
        members="Case_Intake", type_name="CompactLayout", version="62.0"
    )
    _write(build_dir / "reports" / "MILESTONE-M1-package.xml", stale_report)

    resolution = mock_deploy.resolve_manifest_text(
        build_dir, "artefacts", ["M1"], [], ["M1-S01", "M1-S02"], "62.0"
    )

    # Merge is used, not the stale report.
    assert resolution.source.startswith("merged:")
    assert "CompactLayout" not in resolution.xml_text
    assert "Case.Severity__c" in resolution.xml_text  # from the steps' merge

    assert resolution.warning is not None
    assert resolution.warning.startswith("WARN:")
    assert "MILESTONE-M1-package.xml" in resolution.warning
    assert "Case_Intake" in resolution.warning
    assert "using the steps' merge" in resolution.warning
    assert "milestone-verifier M1" in resolution.warning

    assert "CompactLayout:Case_Intake (report-only)" in resolution.drift_note
    assert "steps-only" in resolution.drift_note


def test_resolve_manifest_prefer_report_manifest_uses_report_but_still_warns(tmp_path):
    build_dir = make_build(tmp_path)
    stale_report = PACKAGE_XML_TEMPLATE.format(
        members="Case_Intake", type_name="CompactLayout", version="62.0"
    )
    _write(build_dir / "reports" / "MILESTONE-M1-package.xml", stale_report)

    resolution = mock_deploy.resolve_manifest_text(
        build_dir, "artefacts", ["M1"], [], ["M1-S01", "M1-S02"], "62.0",
        prefer_report_manifest=True,
    )

    # The report's own (stale) text is what gets used this time.
    assert resolution.xml_text == stale_report
    assert resolution.source.endswith("MILESTONE-M1-package.xml")

    assert resolution.warning is not None
    assert resolution.warning.startswith("WARN:")
    assert "Case_Intake" in resolution.warning
    assert "--prefer-report-manifest" in resolution.warning


# --------------------------------------------------------------------------
# JSON-prefix stripping
# --------------------------------------------------------------------------

def test_strip_json_prefix_removes_warning_lines():
    text = (
        "Warning: sf update available from 2.1.0 to 2.2.0.\n"
        '{\n  "status": 0,\n  "result": {"status": "Succeeded"}\n}\n'
    )
    stripped = mock_deploy.strip_json_prefix(text)
    parsed = json.loads(stripped)
    assert parsed["result"]["status"] == "Succeeded"


def test_strip_json_prefix_no_prefix_needed():
    text = '{"status": 0, "result": {"status": "Failed"}}'
    stripped = mock_deploy.strip_json_prefix(text)
    assert json.loads(stripped)["result"]["status"] == "Failed"


def test_strip_json_prefix_raises_when_no_json_present():
    with pytest.raises(ValueError):
        mock_deploy.strip_json_prefix("nothing but noise here\nmore noise\n")


# --------------------------------------------------------------------------
# Exit-code mapping
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "status,expected",
    [
        ("Succeeded", 0),
        ("Failed", 1),
        ("SucceededPartial", 2),
        (None, 2),
        ("SomethingUnexpected", 2),
    ],
)
def test_exit_code_for_status(status, expected):
    assert mock_deploy.exit_code_for_status(status) == expected


# --------------------------------------------------------------------------
# build_sf_command never omits --dry-run, never exposes a deploy path
# --------------------------------------------------------------------------

def test_build_sf_command_source_mode_always_has_dry_run():
    cmd = mock_deploy.build_sf_command("source", "sfskills-dev")
    assert "--dry-run" in cmd
    assert "--source-dir" in cmd
    assert "force-app" in cmd
    assert "--target-org" in cmd and "sfskills-dev" in cmd


def test_build_sf_command_manifest_mode_always_has_dry_run():
    cmd = mock_deploy.build_sf_command("manifest", "sfskills-dev", "package.xml")
    assert "--dry-run" in cmd
    assert "--manifest" in cmd
    assert "package.xml" in cmd


def test_cli_has_no_deploy_flag():
    parser = mock_deploy.build_arg_parser()
    dest_names = {action.dest for action in parser._actions}
    assert "deploy" not in dest_names
    assert "dry_run" not in dest_names  # not exposed; it is hard-coded, not a flag


# --------------------------------------------------------------------------
# main() end-to-end with subprocess.run mocked
# --------------------------------------------------------------------------

def _fake_completed_process(payload: dict, prefix: str = "") -> MagicMock:
    proc = MagicMock()
    proc.stdout = prefix + json.dumps(payload)
    proc.stderr = ""
    proc.returncode = 0
    return proc


def test_main_succeeded_writes_outputs_and_returns_zero(tmp_path, monkeypatch):
    build_dir = make_build(tmp_path)
    out_dir = tmp_path / "mock-out"

    payload = {
        "status": 0,
        "result": {
            "status": "Succeeded",
            "checkOnly": True,
            "numberComponentsTotal": 2,
            "numberComponentErrors": 0,
            "details": {
                "componentSuccesses": [
                    {"componentType": "CustomField", "fullName": "Case.Severity__c"},
                    {"componentType": "Layout", "fullName": "Case-Case Support Layout"},
                ],
                "componentFailures": [],
            },
        },
    }

    captured_cmd = {}

    def fake_run(cmd, cwd, capture_output, text):
        captured_cmd["cmd"] = cmd
        captured_cmd["cwd"] = cwd
        return _fake_completed_process(payload, prefix="Warning: update available\n")

    monkeypatch.setattr(mock_deploy.subprocess, "run", fake_run)

    rc = mock_deploy.main(
        [
            str(build_dir / "plan.json"),
            "--org-alias", "sfskills-dev",
            "--milestone", "M1",
            "--out", str(out_dir),
        ]
    )

    assert rc == 0
    assert "--dry-run" in captured_cmd["cmd"]
    assert captured_cmd["cwd"] == str(out_dir)

    result_json = json.loads((out_dir / "result.json").read_text(encoding="utf-8"))
    assert result_json["result"]["status"] == "Succeeded"

    summary = (out_dir / "summary.md").read_text(encoding="utf-8")
    assert "Succeeded" in summary
    assert "Case.Severity__c" in summary

    assert (out_dir / "sfdx-project.json").is_file()
    assert (out_dir / "force-app" / "main" / "default" / "objects" / "Case" / "fields"
            / "Severity__c.field-meta.xml").is_file()
    assert not (out_dir / "force-app" / "main" / "default" / "package.xml").exists()


def test_main_failed_returns_one(tmp_path, monkeypatch):
    build_dir = make_build(tmp_path)
    payload = {
        "result": {
            "status": "Failed",
            "checkOnly": True,
            "details": {
                "componentSuccesses": [],
                "componentFailures": [
                    {"componentType": "Layout", "fullName": "Case-Case Support Layout",
                     "problem": "Layout must contain an item for required layout field: ContactId"},
                ],
            },
        }
    }

    monkeypatch.setattr(
        mock_deploy.subprocess, "run",
        lambda cmd, cwd, capture_output, text: _fake_completed_process(payload),
    )

    rc = mock_deploy.main(
        [str(build_dir / "plan.json"), "--org-alias", "sfskills-dev", "--milestone", "M1",
         "--out", str(tmp_path / "out2")]
    )
    assert rc == 1
    summary = (tmp_path / "out2" / "summary.md").read_text(encoding="utf-8")
    assert "FAIL" in summary
    assert "ContactId" in summary


def test_main_parse_error_returns_two(tmp_path, monkeypatch):
    build_dir = make_build(tmp_path)

    def fake_run(cmd, cwd, capture_output, text):
        proc = MagicMock()
        proc.stdout = "not json at all"
        proc.stderr = "some cli error"
        proc.returncode = 1
        return proc

    monkeypatch.setattr(mock_deploy.subprocess, "run", fake_run)

    rc = mock_deploy.main(
        [str(build_dir / "plan.json"), "--org-alias", "sfskills-dev", "--milestone", "M1",
         "--out", str(tmp_path / "out3")]
    )
    assert rc == 2


def test_main_no_steps_selected_returns_two(tmp_path, monkeypatch):
    build_dir = make_build(tmp_path)
    monkeypatch.setattr(
        mock_deploy.subprocess, "run",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("sf must not be invoked")),
    )
    rc = mock_deploy.main(
        [str(build_dir / "plan.json"), "--org-alias", "sfskills-dev", "--milestone", "NO-SUCH-MILESTONE"]
    )
    assert rc == 2


def test_main_plan_only_never_invokes_subprocess(tmp_path, monkeypatch):
    build_dir = make_build(tmp_path)
    monkeypatch.setattr(
        mock_deploy.subprocess, "run",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("sf must not be invoked with --plan-only")),
    )

    out_dir = tmp_path / "plan-only-out"
    rc = mock_deploy.main(
        [str(build_dir / "plan.json"), "--org-alias", "sfskills-dev", "--milestone", "M1",
         "--plan-only", "--out", str(out_dir)]
    )
    assert rc == 0
    assert not (out_dir / "result.json").exists()
    summary = (out_dir / "summary.md").read_text(encoding="utf-8")
    assert "status: **not run (--plan-only)**" in summary
    # Source-mode tree assembly still happens.
    assert (out_dir / "force-app" / "main" / "default" / "objects" / "Case" / "fields"
            / "Severity__c.field-meta.xml").is_file()


def test_main_plan_only_manifest_mode_shows_drift_without_org(tmp_path, monkeypatch):
    build_dir = make_build(tmp_path)
    stale_report = PACKAGE_XML_TEMPLATE.format(
        members="Case_Intake", type_name="CompactLayout", version="62.0"
    )
    _write(build_dir / "reports" / "MILESTONE-M1-package.xml", stale_report)

    monkeypatch.setattr(
        mock_deploy.subprocess, "run",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("sf must not be invoked with --plan-only")),
    )

    out_dir = tmp_path / "plan-only-drift-out"
    printed = []
    monkeypatch.setattr("builtins.print", lambda *a, **k: printed.append(" ".join(str(x) for x in a)))

    rc = mock_deploy.main(
        [str(build_dir / "plan.json"), "--org-alias", "none", "--milestone", "M1",
         "--mode", "manifest", "--plan-only", "--out", str(out_dir)]
    )
    assert rc == 0

    manifest_text = (out_dir / "package.xml").read_text(encoding="utf-8")
    assert "CompactLayout" not in manifest_text  # steps' merge used, not the stale report

    summary = (out_dir / "summary.md").read_text(encoding="utf-8")
    assert "not run (--plan-only)" in summary
    assert "## Manifest drift" in summary
    assert "Case_Intake" in summary

    warn_lines = [line for line in printed if line.startswith("WARN:")]
    assert warn_lines, "expected a WARN line naming the manifest drift"
    assert "Case_Intake" in warn_lines[0]


def test_main_manifest_mode_writes_manifest_file(tmp_path, monkeypatch):
    build_dir = make_build(tmp_path)
    payload = {"result": {"status": "Succeeded", "checkOnly": True,
                           "details": {"componentSuccesses": [], "componentFailures": []}}}

    captured_cmd = {}

    def fake_run(cmd, cwd, capture_output, text):
        captured_cmd["cmd"] = cmd
        return _fake_completed_process(payload)

    monkeypatch.setattr(mock_deploy.subprocess, "run", fake_run)

    out_dir = tmp_path / "manifest-out"
    rc = mock_deploy.main(
        [str(build_dir / "plan.json"), "--org-alias", "sfskills-dev", "--milestone", "M1",
         "--mode", "manifest", "--out", str(out_dir)]
    )
    assert rc == 0
    assert "--manifest" in captured_cmd["cmd"]
    assert (out_dir / "package.xml").is_file()
    manifest_text = (out_dir / "package.xml").read_text(encoding="utf-8")
    assert "CustomField" in manifest_text
    assert "Layout" in manifest_text


# --------------------------------------------------------------------------
# --api-version override + summary/result.json recording
# --------------------------------------------------------------------------

def test_main_api_version_scanned_highest_recorded_in_summary_and_result(tmp_path, monkeypatch):
    build_dir = make_build(tmp_path)
    payload = {"result": {"status": "Succeeded", "checkOnly": True,
                           "details": {"componentSuccesses": [], "componentFailures": []}}}
    monkeypatch.setattr(
        mock_deploy.subprocess, "run",
        lambda cmd, cwd, capture_output, text: _fake_completed_process(payload),
    )

    out_dir = tmp_path / "api-version-scan-out"
    rc = mock_deploy.main(
        [str(build_dir / "plan.json"), "--org-alias", "sfskills-dev", "--milestone", "M1",
         "--out", str(out_dir)]
    )
    assert rc == 0

    # M1-S01=61.0, M1-S02=62.0 -> the higher (62.0) is chosen and used for
    # sfdx-project.json too.
    summary = (out_dir / "summary.md").read_text(encoding="utf-8")
    assert "- api version: `62.0` (highest of: M1-S01=61.0, M1-S02=62.0)" in summary

    sfdx_project = json.loads((out_dir / "sfdx-project.json").read_text(encoding="utf-8"))
    assert sfdx_project["sourceApiVersion"] == "62.0"

    result_json = json.loads((out_dir / "result.json").read_text(encoding="utf-8"))
    assert result_json["api_version"]["value"] == "62.0"
    assert result_json["api_version"]["source"] == "highest of: M1-S01=61.0, M1-S02=62.0"
    # Adding api_version must not disturb the existing sf CLI keys.
    assert result_json["result"]["status"] == "Succeeded"


def test_main_api_version_override_wins_over_scan(tmp_path, monkeypatch):
    build_dir = make_build(tmp_path)
    payload = {"result": {"status": "Succeeded", "checkOnly": True,
                           "details": {"componentSuccesses": [], "componentFailures": []}}}
    monkeypatch.setattr(
        mock_deploy.subprocess, "run",
        lambda cmd, cwd, capture_output, text: _fake_completed_process(payload),
    )

    out_dir = tmp_path / "api-version-override-out"
    rc = mock_deploy.main(
        [str(build_dir / "plan.json"), "--org-alias", "sfskills-dev", "--milestone", "M1",
         "--api-version", "67.0", "--out", str(out_dir)]
    )
    assert rc == 0

    summary = (out_dir / "summary.md").read_text(encoding="utf-8")
    assert "- api version: `67.0` (override)" in summary

    sfdx_project = json.loads((out_dir / "sfdx-project.json").read_text(encoding="utf-8"))
    assert sfdx_project["sourceApiVersion"] == "67.0"

    result_json = json.loads((out_dir / "result.json").read_text(encoding="utf-8"))
    assert result_json["api_version"] == {"value": "67.0", "source": "override"}


def test_main_api_version_override_wins_in_manifest_mode(tmp_path, monkeypatch):
    # The merged package.xml's <version> must reflect the override too, not
    # just sfdx-project.json.
    build_dir = make_build(tmp_path)
    payload = {"result": {"status": "Succeeded", "checkOnly": True,
                           "details": {"componentSuccesses": [], "componentFailures": []}}}
    monkeypatch.setattr(
        mock_deploy.subprocess, "run",
        lambda cmd, cwd, capture_output, text: _fake_completed_process(payload),
    )

    out_dir = tmp_path / "api-version-override-manifest-out"
    rc = mock_deploy.main(
        [str(build_dir / "plan.json"), "--org-alias", "sfskills-dev", "--milestone", "M1",
         "--mode", "manifest", "--api-version", "67.0", "--out", str(out_dir)]
    )
    assert rc == 0

    manifest_text = (out_dir / "package.xml").read_text(encoding="utf-8")
    assert "<version>67.0</version>" in manifest_text


def test_main_api_version_fallback_recorded_when_no_step_declares_one(tmp_path, monkeypatch):
    build_dir = make_build(tmp_path)
    payload = {"result": {"status": "Succeeded", "checkOnly": True,
                           "details": {"componentSuccesses": [], "componentFailures": []}}}
    monkeypatch.setattr(
        mock_deploy.subprocess, "run",
        lambda cmd, cwd, capture_output, text: _fake_completed_process(payload),
    )

    out_dir = tmp_path / "api-version-fallback-out"
    # M2-S01 has no package.xml at all -> nothing to scan -> fallback.
    rc = mock_deploy.main(
        [str(build_dir / "plan.json"), "--org-alias", "sfskills-dev", "--milestone", "M2",
         "--out", str(out_dir)]
    )
    assert rc == 0

    summary = (out_dir / "summary.md").read_text(encoding="utf-8")
    assert f"- api version: `{mock_deploy.DEFAULT_API_VERSION}` (fallback" in summary


def test_main_api_version_recorded_in_plan_only_summary(tmp_path, monkeypatch):
    build_dir = make_build(tmp_path)
    monkeypatch.setattr(
        mock_deploy.subprocess, "run",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("sf must not be invoked with --plan-only")),
    )

    out_dir = tmp_path / "api-version-plan-only-out"
    rc = mock_deploy.main(
        [str(build_dir / "plan.json"), "--org-alias", "sfskills-dev", "--milestone", "M1",
         "--plan-only", "--out", str(out_dir)]
    )
    assert rc == 0
    assert not (out_dir / "result.json").exists()

    summary = (out_dir / "summary.md").read_text(encoding="utf-8")
    assert "- api version: `62.0` (highest of: M1-S01=61.0, M1-S02=62.0)" in summary


# --------------------------------------------------------------------------
# S2-F-06: Apex test execution (--test-level / --tests)
# --------------------------------------------------------------------------

def test_build_sf_command_no_test_run_leaves_command_unchanged():
    # NoTestRun is the default and must add no flags at all — the built
    # command is byte-for-byte what it was before --test-level existed, even
    # if a stray `tests` list is passed in (it must be silently ignored).
    baseline = mock_deploy.build_sf_command("source", "sfskills-dev")
    with_no_test_run = mock_deploy.build_sf_command(
        "source", "sfskills-dev", "package.xml",
        test_level="NoTestRun", tests=["Whatever"],
    )
    assert baseline == with_no_test_run
    assert "--test-level" not in baseline
    assert "--tests" not in baseline


def test_build_sf_command_run_specified_tests_adds_repeated_tests_flag():
    cmd = mock_deploy.build_sf_command(
        "source", "sfskills-dev", test_level="RunSpecifiedTests",
        tests=["FooTest", "BarTest"],
    )
    assert cmd[cmd.index("--test-level") + 1] == "RunSpecifiedTests"
    assert cmd.count("--tests") == 2
    tests_passed = [cmd[i + 1] for i, v in enumerate(cmd) if v == "--tests"]
    assert tests_passed == ["FooTest", "BarTest"]


def test_build_sf_command_run_local_tests_has_no_tests_flag():
    cmd = mock_deploy.build_sf_command("source", "sfskills-dev", test_level="RunLocalTests")
    assert cmd[cmd.index("--test-level") + 1] == "RunLocalTests"
    assert "--tests" not in cmd


def test_find_test_classes_scans_at_istest_class_and_ignores_non_test(tmp_path):
    root = tmp_path / "force-app"
    _write(
        root / "classes" / "CaseServiceTest.cls",
        "@isTest\nprivate class CaseServiceTest {\n"
        "    @isTest static void itWorks() {}\n"
        "}\n",
    )
    _write(
        root / "classes" / "AnotherTest.cls",
        "@IsTest\npublic class AnotherTest {\n}\n",
    )
    _write(
        root / "classes" / "CaseService.cls",
        "public class CaseService {\n    public void doWork() {}\n}\n",
    )
    assert mock_deploy.find_test_classes(root) == ["AnotherTest", "CaseServiceTest"]


def test_find_test_classes_missing_root_returns_empty(tmp_path):
    assert mock_deploy.find_test_classes(tmp_path / "does-not-exist") == []


def test_extract_test_summary_all_zero_when_no_test_data():
    summary = mock_deploy.extract_test_summary({"result": {}}, "NoTestRun", None)
    assert summary.level == "NoTestRun"
    assert summary.run == 0
    assert summary.passed == 0
    assert summary.failed == 0
    assert summary.coverage_pct is None
    assert summary.failures == []


def test_extract_test_summary_computes_coverage_and_failures():
    parsed = {
        "result": {
            "numberTestsCompleted": 3,
            "numberTestErrors": 1,
            "details": {
                "runTestResult": {
                    "codeCoverage": [
                        {"numLocations": 10, "numLocationsNotCovered": 5},
                        {"numLocations": 10, "numLocationsNotCovered": 1},
                    ],
                    "failures": [
                        {
                            "name": "FooTest",
                            "methodName": "itFails",
                            "message": "boom",
                            "stackTrace": "Class.FooTest.itFails: line 5, column 1\nmore",
                        },
                    ],
                }
            },
        }
    }
    summary = mock_deploy.extract_test_summary(parsed, "RunSpecifiedTests", ["FooTest"])
    assert summary.run == 3
    assert summary.passed == 2
    assert summary.failed == 1
    assert summary.coverage_pct == 70.0  # (20 - 6) / 20 * 100
    assert summary.failures == [
        ("FooTest", "itFails", "boom", "Class.FooTest.itFails: line 5, column 1")
    ]


def test_render_summary_without_tests_omits_tests_line():
    parsed = {
        "result": {
            "status": "Succeeded", "checkOnly": True,
            "details": {"componentSuccesses": [], "componentFailures": []},
        }
    }
    summary = mock_deploy.render_summary(parsed, "source", "sfskills-dev")
    assert "- tests:" not in summary


def test_render_summary_with_tests_shows_line_and_failures_table():
    parsed = {
        "result": {
            "status": "Failed", "checkOnly": True,
            "details": {"componentSuccesses": [], "componentFailures": []},
        }
    }
    tests = mock_deploy.TestSummary(
        level="RunSpecifiedTests",
        requested_tests=["CaseServiceTest"],
        run=2, passed=1, failed=1, coverage_pct=75.0,
        failures=[
            ("CaseServiceTest", "itFails", "System.AssertException: Assertion Failed",
             "Class.CaseServiceTest.itFails: line 10, column 1"),
        ],
    )
    summary = mock_deploy.render_summary(parsed, "source", "sfskills-dev", tests=tests)
    assert (
        "- tests: level RunSpecifiedTests · run 2 · passed 1 · failed 1 · coverage 75.0%"
        in summary
    )
    assert "## Test failures" in summary
    assert "CaseServiceTest" in summary
    assert "itFails" in summary
    assert "System.AssertException: Assertion Failed" in summary


def test_main_default_no_test_run_shows_all_zero_tests_line(tmp_path, monkeypatch):
    # The whole point of S2-F-06: NoTestRun's silence becomes visible, not
    # hidden, once this line is always rendered.
    build_dir = make_build(tmp_path)
    payload = {"result": {"status": "Succeeded", "checkOnly": True,
                           "details": {"componentSuccesses": [], "componentFailures": []}}}
    monkeypatch.setattr(
        mock_deploy.subprocess, "run",
        lambda cmd, cwd, capture_output, text: _fake_completed_process(payload),
    )
    out_dir = tmp_path / "no-test-run-out"
    rc = mock_deploy.main(
        [str(build_dir / "plan.json"), "--org-alias", "sfskills-dev", "--milestone", "M1",
         "--out", str(out_dir)]
    )
    assert rc == 0
    summary = (out_dir / "summary.md").read_text(encoding="utf-8")
    assert "- tests: level NoTestRun · run 0 · passed 0 · failed 0 · coverage n/a" in summary

    result_json = json.loads((out_dir / "result.json").read_text(encoding="utf-8"))
    assert result_json["tests"]["level"] == "NoTestRun"
    assert result_json["tests"]["run"] == 0
    assert result_json["tests"]["coverage_pct"] is None


def test_main_run_specified_tests_auto_discovers_and_reports(tmp_path, monkeypatch):
    build_dir = make_build(tmp_path)
    _write(
        build_dir / "artefacts" / "M1-S01" / "classes" / "CaseServiceTest.cls",
        "@isTest\nprivate class CaseServiceTest {\n}\n",
    )
    _write(
        build_dir / "artefacts" / "M1-S01" / "classes" / "CaseService.cls",
        "public class CaseService {\n}\n",
    )

    payload = {
        "result": {
            "status": "Succeeded",
            "checkOnly": True,
            "runTestsEnabled": True,
            "numberTestsCompleted": 1,
            "numberTestErrors": 0,
            "details": {
                "componentSuccesses": [],
                "componentFailures": [],
                "runTestResult": {
                    "numTestsRun": 1,
                    "numFailures": 0,
                    "codeCoverage": [{"numLocations": 10, "numLocationsNotCovered": 2}],
                    "failures": [],
                },
            },
        }
    }

    captured_cmd = {}

    def fake_run(cmd, cwd, capture_output, text):
        captured_cmd["cmd"] = cmd
        return _fake_completed_process(payload)

    monkeypatch.setattr(mock_deploy.subprocess, "run", fake_run)

    out_dir = tmp_path / "run-specified-out"
    rc = mock_deploy.main(
        [str(build_dir / "plan.json"), "--org-alias", "sfskills-dev", "--milestone", "M1",
         "--test-level", "RunSpecifiedTests", "--out", str(out_dir)]
    )
    assert rc == 0

    cmd = captured_cmd["cmd"]
    assert "--tests" in cmd
    idx = cmd.index("--tests")
    assert cmd[idx + 1] == "CaseServiceTest"
    assert cmd.count("--tests") == 1  # CaseService (non-test) is not auto-included

    summary = (out_dir / "summary.md").read_text(encoding="utf-8")
    assert (
        "- tests: level RunSpecifiedTests · run 1 · passed 1 · failed 0 · coverage 80.0%"
        in summary
    )

    result_json = json.loads((out_dir / "result.json").read_text(encoding="utf-8"))
    assert result_json["tests"]["level"] == "RunSpecifiedTests"
    assert result_json["tests"]["requested_tests"] == ["CaseServiceTest"]
    assert result_json["tests"]["passed"] == 1
    assert result_json["tests"]["coverage_pct"] == 80.0


def test_main_tests_override_wins_over_auto_scan(tmp_path, monkeypatch):
    build_dir = make_build(tmp_path)
    _write(
        build_dir / "artefacts" / "M1-S01" / "classes" / "CaseServiceTest.cls",
        "@isTest\nprivate class CaseServiceTest {\n}\n",
    )

    payload = {"result": {"status": "Succeeded", "checkOnly": True,
                           "details": {"componentSuccesses": [], "componentFailures": []}}}
    captured_cmd = {}

    def fake_run(cmd, cwd, capture_output, text):
        captured_cmd["cmd"] = cmd
        return _fake_completed_process(payload)

    monkeypatch.setattr(mock_deploy.subprocess, "run", fake_run)

    out_dir = tmp_path / "tests-override-out"
    rc = mock_deploy.main(
        [str(build_dir / "plan.json"), "--org-alias", "sfskills-dev", "--milestone", "M1",
         "--test-level", "RunSpecifiedTests", "--tests", "ExplicitTest,OtherTest",
         "--out", str(out_dir)]
    )
    assert rc == 0

    cmd = captured_cmd["cmd"]
    tests_passed = [cmd[i + 1] for i, v in enumerate(cmd) if v == "--tests"]
    assert tests_passed == ["ExplicitTest", "OtherTest"]
    assert "CaseServiceTest" not in tests_passed  # override wins over auto-scan

    result_json = json.loads((out_dir / "result.json").read_text(encoding="utf-8"))
    assert result_json["tests"]["requested_tests"] == ["ExplicitTest", "OtherTest"]


def test_main_run_specified_tests_errors_when_none_found(tmp_path, monkeypatch):
    build_dir = make_build(tmp_path)  # no .cls files anywhere in this fixture
    monkeypatch.setattr(
        mock_deploy.subprocess, "run",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("sf must not be invoked")),
    )
    rc = mock_deploy.main(
        [str(build_dir / "plan.json"), "--org-alias", "sfskills-dev", "--milestone", "M1",
         "--test-level", "RunSpecifiedTests"]
    )
    assert rc == 2


def test_main_tests_ignored_with_warn_when_not_run_specified(tmp_path, monkeypatch, capsys):
    build_dir = make_build(tmp_path)
    payload = {"result": {"status": "Succeeded", "checkOnly": True,
                           "details": {"componentSuccesses": [], "componentFailures": []}}}
    monkeypatch.setattr(
        mock_deploy.subprocess, "run",
        lambda cmd, cwd, capture_output, text: _fake_completed_process(payload),
    )
    out_dir = tmp_path / "tests-ignored-out"
    rc = mock_deploy.main(
        [str(build_dir / "plan.json"), "--org-alias", "sfskills-dev", "--milestone", "M1",
         "--tests", "SomeTest", "--out", str(out_dir)]
    )
    assert rc == 0
    captured = capsys.readouterr()
    assert "WARN" in captured.err
    assert "--tests" in captured.err


def test_main_plan_only_shows_planned_tests_without_contacting_org(tmp_path, monkeypatch):
    build_dir = make_build(tmp_path)
    _write(
        build_dir / "artefacts" / "M1-S01" / "classes" / "CaseServiceTest.cls",
        "@isTest\nprivate class CaseServiceTest {\n}\n",
    )
    monkeypatch.setattr(
        mock_deploy.subprocess, "run",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("sf must not be invoked with --plan-only")),
    )
    out_dir = tmp_path / "plan-only-tests-out"
    rc = mock_deploy.main(
        [str(build_dir / "plan.json"), "--org-alias", "sfskills-dev", "--milestone", "M1",
         "--test-level", "RunSpecifiedTests", "--plan-only", "--out", str(out_dir)]
    )
    assert rc == 0
    assert not (out_dir / "result.json").exists()
    summary = (out_dir / "summary.md").read_text(encoding="utf-8")
    assert "not run (--plan-only)" in summary
    assert "level RunSpecifiedTests" in summary
    assert "CaseServiceTest" in summary


def test_main_plan_only_no_test_run_shows_not_run_line(tmp_path, monkeypatch):
    build_dir = make_build(tmp_path)
    monkeypatch.setattr(
        mock_deploy.subprocess, "run",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("sf must not be invoked with --plan-only")),
    )
    out_dir = tmp_path / "plan-only-no-test-run-out"
    rc = mock_deploy.main(
        [str(build_dir / "plan.json"), "--org-alias", "sfskills-dev", "--milestone", "M1",
         "--plan-only", "--out", str(out_dir)]
    )
    assert rc == 0
    summary = (out_dir / "summary.md").read_text(encoding="utf-8")
    assert "- tests: level NoTestRun (not run — --plan-only)" in summary


def test_cli_test_level_choices_exclude_run_all_tests_in_org():
    parser = mock_deploy.build_arg_parser()
    test_level_action = next(a for a in parser._actions if a.dest == "test_level")
    assert set(test_level_action.choices) == {"NoTestRun", "RunSpecifiedTests", "RunLocalTests"}
    assert test_level_action.default == "NoTestRun"
