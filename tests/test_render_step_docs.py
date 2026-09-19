"""render_step_docs.py — the deterministic half of the build-doc-keeper."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from test_build_plan import (advance, fixture_repo, open_gates, plan_dict,  # noqa: F401,E402
                             step, write_plan_file)

REPO = Path(__file__).resolve().parents[1]


def _builder_envelope(build_dir: Path, step_id: str, open_items) -> Path:
    env_dir = build_dir / "envelopes" / step_id
    env_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "agent": "metadata-builder", "mode": "single", "run_id": "2026-09-19T10-00-00Z",
        "summary": "built", "confidence": "MEDIUM", "process_observations": [], "citations": [],
        "report_path": "x.md", "envelope_path": "x.json",
        "extensions": {"artefacts": [f"artefacts/{step_id}/objects/Case.object-meta.xml",
                                     f"artefacts/{step_id}/package.xml", f"artefacts/{step_id}/deploy-order.md"],
                       "checker_results": [{"command": "python3 x.py --manifest-dir artefacts", "exit_code": 0}],
                       "open_items": open_items},
    }
    p = env_dir / "2026-09-19T10-00-00Z.json"
    p.write_text(json.dumps(payload))
    return p


def _render(build_dir: Path, repo: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO / "scripts/render_step_docs.py"), "M1-S01",
         "--build-dir", str(build_dir), "--repo-root", str(repo),
         "--req", "REQ-001", "--source", "Q1", "--requirement", "The thing exists",
         "--workbook", "01-objects-and-fields.md", "--row-prefix", "CWB-OBJ", "--row-start", "1", *extra],
        capture_output=True, text=True, cwd=str(REPO))


def test_renders_rows_req_open_items_and_flips_status(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)
    advance(path, fixture_repo, "M1-S01", upto="tested")
    build_dir = path.parent
    _builder_envelope(build_dir, "M1-S01", [{"id": "O-M1S01-01", "topic": "Something open", "what_to_do": "Decide it"},
                                            "A bare-string open item from an older envelope shape"])
    extra = tmp_path / "d.md"
    extra.write_text("## D-M1S01-01 — A decision\n\n- recorded by the operator\n")
    r = _render(build_dir, fixture_repo, "--extra-decisions", str(extra))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "OK" in r.stdout and "tested -> documented" in r.stdout
    after = json.loads(path.read_text())
    assert after["steps"][0]["status"] == "documented"
    wb = (build_dir / "workbook/01-objects-and-fields.md").read_text()
    assert "| CWB-OBJ-001 |" in wb and "| CWB-OBJ-003 |" in wb and "| CWB-OBJ-004 |" not in wb
    tr = (build_dir / "traceability.md").read_text()
    assert "| REQ-001 | Q1 | The thing exists | M1-S01 |" in tr
    dec = (build_dir / "decisions.md").read_text()
    assert "## O-M1S01-01 — Something open" in dec and "## D-M1S01-01 — A decision" in dec
    assert "## O-M1S01-02 — A bare-string open item" in dec
    envs = list((build_dir / "envelopes/M1-S01").glob("*.json"))
    assert len(envs) == 2, "builder envelope + renderer envelope"


def test_refuses_when_step_not_tested(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)
    advance(path, fixture_repo, "M1-S01", upto="built")
    _builder_envelope(path.parent, "M1-S01", [])
    before = path.read_bytes()
    r = _render(path.parent, fixture_repo)
    assert r.returncode != 0
    assert path.read_bytes() == before
