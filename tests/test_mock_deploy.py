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
    copied = mock_deploy.copy_artefacts(build_dir, "artefacts", ["M1-S01", "M1-S02"], dest)

    copied_str = {str(p) for p in copied}
    assert copied_str == {
        str(Path("objects/Case/fields/Severity__c.field-meta.xml")),
        str(Path("layouts/Case-Case Support Layout.layout-meta.xml")),
    }
    # package.xml must never be copied into the source tree.
    assert not any(p.name == "package.xml" for p in copied)
    assert not (dest / "package.xml").exists()

    # Subfolders are preserved exactly.
    assert (dest / "objects" / "Case" / "fields" / "Severity__c.field-meta.xml").is_file()
    assert (dest / "layouts" / "Case-Case Support Layout.layout-meta.xml").is_file()


def test_copy_artefacts_skips_missing_step_dir(tmp_path):
    build_dir = make_build(tmp_path)
    dest = tmp_path / "out"
    # M2-S01 has no artefacts directory on disk; must not raise.
    copied = mock_deploy.copy_artefacts(build_dir, "artefacts", ["M2-S01"], dest)
    assert copied == []


# --------------------------------------------------------------------------
# sfdx-project.json version pick
# --------------------------------------------------------------------------

def test_pick_api_version_uses_first_step_in_order(tmp_path):
    build_dir = make_build(tmp_path)
    # M1-S01's package.xml declares 61.0, M1-S02's declares 62.0; step order wins.
    version = mock_deploy.pick_api_version(build_dir, "artefacts", ["M1-S01", "M1-S02"])
    assert version == "61.0"


def test_pick_api_version_skips_missing_and_uses_next(tmp_path):
    build_dir = make_build(tmp_path)
    version = mock_deploy.pick_api_version(build_dir, "artefacts", ["M2-S01", "M1-S02"])
    assert version == "62.0"


def test_pick_api_version_falls_back_when_none_found(tmp_path):
    build_dir = make_build(tmp_path)
    version = mock_deploy.pick_api_version(build_dir, "artefacts", ["M2-S01"])
    assert version == mock_deploy.DEFAULT_API_VERSION
    assert version == "62.0"


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


def test_resolve_manifest_uses_milestone_report_when_single_milestone(tmp_path):
    build_dir = make_build(tmp_path)
    report_xml = PACKAGE_XML_TEMPLATE.format(members="Case", type_name="CustomObject", version="62.0")
    _write(build_dir / "reports" / "MILESTONE-M1-package.xml", report_xml)

    source, xml_text = mock_deploy.resolve_manifest_text(
        build_dir, "artefacts", ["M1"], [], ["M1-S01", "M1-S02"], "62.0"
    )
    assert source.endswith("MILESTONE-M1-package.xml")
    assert xml_text == report_xml


def test_resolve_manifest_merges_when_report_missing(tmp_path):
    build_dir = make_build(tmp_path)
    # No MILESTONE-M1-package.xml on disk -> falls back to merging step manifests.
    source, xml_text = mock_deploy.resolve_manifest_text(
        build_dir, "artefacts", ["M1"], [], ["M1-S01", "M1-S02"], "62.0"
    )
    assert source.startswith("merged:")
    assert "CustomField" in xml_text
    assert "Layout" in xml_text


def test_resolve_manifest_merges_when_step_filter_used(tmp_path):
    build_dir = make_build(tmp_path)
    _write(
        build_dir / "reports" / "MILESTONE-M1-package.xml",
        PACKAGE_XML_TEMPLATE.format(members="Case", type_name="CustomObject", version="62.0"),
    )
    # --step was used alongside --milestone -> report shortcut does not apply.
    source, _xml_text = mock_deploy.resolve_manifest_text(
        build_dir, "artefacts", ["M1"], ["M1-S01"], ["M1-S01"], "62.0"
    )
    assert source.startswith("merged:")


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
