"""The report-only sf commands need a project root even in a pip install (no resources/ dir)."""
from sfskills_mcp import deploy


def test_fallback_creates_a_minimal_project_when_packaged_dir_is_absent(monkeypatch, tmp_path):
    monkeypatch.setattr(deploy, "_EMPTY_SF_PROJECT", tmp_path / "does-not-exist")
    monkeypatch.setattr(deploy, "_EMPTY_SF_PROJECT_FALLBACK", None)
    root = deploy._ensure_empty_sf_project()
    assert (root / "sfdx-project.json").is_file()
    assert (root / "force-app").is_dir()
    assert deploy._ensure_empty_sf_project() == root


def test_checkout_dir_is_used_when_present():
    if (deploy._EMPTY_SF_PROJECT / "sfdx-project.json").is_file():
        assert deploy._ensure_empty_sf_project() == deploy._EMPTY_SF_PROJECT
