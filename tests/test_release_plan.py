"""scripts/release_plan.py: the deterministic CLI over RELEASES.yaml."""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import release_plan as rp  # noqa: E402

HEADER = "# test plan header\n# second line, kept verbatim\n\n"
PLAN = HEADER + """\
version: 1
baseline:
  measured_on: 2026-10-01
releases:
  - version: 1.4.0
    mcp_version: 0.5.1
    branch: release/1.4.0
    ships: 2026-10-30
    freeze: 2026-10-28
    items:
      - {id: R1-01, title: "Done thing", size: S, owner_model: sonnet, status: done, evidence: "sha abc"}
      - {id: R1-02, title: "Depth wave", size: L, owner_model: opus, status: todo, target: 10, domains: [data]}
      - {id: R1-03, title: "Top-up wave", size: M, owner_model: opus, status: todo, target: 10, domains: [data]}
      - {id: R1-04, title: "Fix the gate", size: S, owner_model: sonnet, status: todo, notes: "a gate fix"}
      - {id: R1-05, title: "Release 1.4.0", size: S, owner_model: fable, status: todo}
    measured: {}
  - version: 1.5.0
    mcp_version: 0.5.2
    branch: release/1.5.0
    ships: 2026-11-13
    freeze: 2026-11-11
    items:
      - {id: R2-01, title: "Later", size: S, owner_model: sonnet, status: todo}
    measured: {}
inbox: []
"""

FM = '---\nname: {n}\nsalesforce-version: "{v}"\n---\n{body}\n'


@pytest.fixture
def plan(tmp_path):
    p = tmp_path / "RELEASES.yaml"
    p.write_text(PLAN, encoding="utf-8")
    return p


@pytest.fixture
def skills(tmp_path, monkeypatch):
    root = tmp_path / "skills"
    scores = {}
    for dom, slug, score, ver, body in [
        ("data", "low", 2, "Spring '25+", "UNVERIFIED x\n"),
        ("data", "mid", 6, "Summer '26", "## Questions to Ask Before Configuring\n"),
        ("data", "high", 11, "Spring '25+", "no table\n"),
        ("data", "high2", 12, "Spring '25+", "## Questions to Ask Before Configuring\n"),
        ("apex", "other", 0, "Spring '25+", ""),
    ]:
        d = root / dom / slug
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(FM.format(n=slug, v=ver, body=body), encoding="utf-8")
        scores[slug] = score
    ref = root / "data" / "low" / "references"
    ref.mkdir()
    (ref / "gotchas.md").write_text("UNVERIFIED y\n", encoding="utf-8")
    monkeypatch.setattr(rp, "score_skill", lambda d: {"score": scores[d.name], **{s: False for s in rp.SIGNALS}})
    return root


def run(plan, *args, skills=None):
    argv = [args[0], "--plan", str(plan)]
    if skills is not None:
        argv += ["--skills", str(skills)]
    return rp.main(argv + list(args[1:]))


def load(plan):
    return yaml.safe_load(plan.read_text(encoding="utf-8"))


def test_status(plan, capsys):
    assert run(plan, "status", "--today", "2026-10-19") == 0
    out = capsys.readouterr().out
    assert "1.4.0" in out and "9 days to freeze" in out
    assert "R1-02" in out and "todo" in out and "opus" in out
    assert "R2-01" not in out


def test_next_picks_first_todo(plan, capsys):
    assert run(plan, "next", "--today", "2026-10-19") == 0
    assert "R1-02" in capsys.readouterr().out


def test_next_after_freeze_only_release_or_gate_fix(plan, capsys):
    assert run(plan, "next", "--today", "2026-10-29") == 0
    assert "R1-04" in capsys.readouterr().out
    run(plan, "set-status", "R1-04", "done", "--evidence", "e")
    capsys.readouterr()
    run(plan, "next", "--today", "2026-10-29")
    assert "R1-05" in capsys.readouterr().out


def test_next_nothing_actionable(plan, capsys):
    for i in ("R1-02", "R1-03", "R1-04", "R1-05"):
        run(plan, "set-status", i, "dropped")
    run(plan, "set-status", "R2-01", "dropped")
    capsys.readouterr()
    assert run(plan, "next", "--today", "2026-10-19") == 2
    assert "nothing actionable" in capsys.readouterr().out


def test_next_target_worklist_lowest_first_skips_done(plan, skills, capsys):
    assert run(plan, "next", "--today", "2026-10-19", "--batch", "2", skills=skills) == 0
    out = capsys.readouterr().out
    assert out.index("data/low") < out.index("data/mid")
    assert "data/high" not in out and "apex" not in out
    run(plan, "set-status", "R1-02", "running", "--done-skills", "data/low,data/low")
    assert load(plan)["releases"][0]["items"][1]["done_skills"] == ["data/low"]
    capsys.readouterr()
    run(plan, "next", "--today", "2026-10-19", skills=skills)
    # running item is not "todo"; move to R1-03 topup instead
    out = capsys.readouterr().out
    assert "R1-03" in out


def test_next_json(plan, skills, capsys):
    run(plan, "next", "--today", "2026-10-19", "--json", skills=skills)
    d = json.loads(capsys.readouterr().out)
    assert d["item"]["id"] == "R1-02"
    assert [w["skill"] for w in d["work"]] == ["data/low", "data/mid", "data/high", "data/high2"]


def test_next_topup_list(plan, skills, capsys):
    run(plan, "set-status", "R1-02", "done", "--evidence", "e")
    capsys.readouterr()
    run(plan, "next", "--today", "2026-10-19", skills=skills)
    out = capsys.readouterr().out
    assert "data/high" in out and "data/high2" not in out and "data/mid" not in out


def test_done_requires_evidence(plan, capsys):
    before = plan.read_text()
    assert run(plan, "set-status", "R1-02", "done") == 1
    assert plan.read_text() == before
    assert run(plan, "set-status", "R1-02", "done", "--evidence", "sha 1") == 0
    item = load(plan)["releases"][0]["items"][1]
    assert item["status"] == "done" and item["evidence"] == "sha 1"


def test_set_status_unknown_id(plan):
    assert run(plan, "set-status", "R9-99", "todo") == 1


def slotted(plan):
    return load(plan)["inbox"][-1]["slotted_into"]


def test_add_s_before_and_after_freeze(plan, capsys):
    assert run(plan, "add", "tiny ask", "--size", "S", "--today", "2026-10-19") == 0
    assert slotted(plan) == "1.4.0"
    assert "R1-06" in capsys.readouterr().out
    run(plan, "add", "tiny later", "--size", "S", "--today", "2026-10-28")
    assert slotted(plan) == "1.5.0"
    new = load(plan)["releases"][1]["items"][-1]
    assert new["id"] == "R2-02" and new["owner_model"] == "sonnet" and new["status"] == "todo"
    assert new["title"] == "tiny later"


def test_add_m_close_to_freeze_goes_next(plan):
    run(plan, "add", "medium", "--size", "M", "--today", "2026-10-27")
    assert slotted(plan) == "1.5.0"


def test_add_m_with_capacity_goes_current(plan):
    run(plan, "add", "medium", "--size", "M", "--today", "2026-10-19", "--owner-model", "fable")
    assert slotted(plan) == "1.4.0"
    assert load(plan)["releases"][0]["items"][-1]["owner_model"] == "fable"


def test_add_m_without_capacity_goes_next(plan):
    for t in ("a", "b"):
        run(plan, "add", t, "--size", "M", "--today", "2026-10-10")
    # R1-02 (L) + R1-03 (M) + a + b = 4 open M/L already; capacity gone
    run(plan, "add", "c", "--size", "M", "--today", "2026-10-10")
    assert slotted(plan) == "1.5.0"


def test_add_l_next_with_prefix(plan):
    run(plan, "add", "huge", "--size", "L", "--today", "2026-10-19", "--title", "Big")
    assert slotted(plan) == "1.5.0"
    assert load(plan)["releases"][1]["items"][-1]["title"] == "[split before scheduling] Big"


def test_add_without_target_release_fails(plan, capsys):
    run(plan, "set-status", "R2-01", "dropped")
    for i in ("R1-02", "R1-03", "R1-04", "R1-05"):
        run(plan, "set-status", i, "dropped")
    assert run(plan, "add", "x", "--size", "S", "--today", "2026-10-19") == 1


def test_measure_writes_five_keys(plan, skills, capsys):
    assert run(plan, "measure", "--today", "2026-10-20", skills=skills) == 0
    m = load(plan)["releases"][0]["measured"]
    assert m == {
        "skills": 5, "at_bar": 2, "questions_tables": 2, "unverified_markers": 2,
        "default_version_skills": 4, "measured_on": date(2026, 10, 20),
    }
    assert "at_bar" in capsys.readouterr().out


def test_header_survives_write_byte_for_byte(plan):
    run(plan, "set-status", "R1-02", "running")
    assert plan.read_text(encoding="utf-8").startswith(HEADER + "version: 1\n")
    assert load(plan)["releases"][0]["items"][1]["status"] == "running"


def test_real_file_round_trips_through_write(tmp_path):
    real = Path(__file__).resolve().parents[1] / "RELEASES.yaml"
    copy = tmp_path / "RELEASES.yaml"
    copy.write_text(real.read_text(encoding="utf-8"), encoding="utf-8")
    orig = yaml.safe_load(real.read_text(encoding="utf-8"))
    item = orig["releases"][0]["items"][3]
    assert run(copy, "set-status", item["id"], "running") == 0
    d = load(copy)
    d["releases"][0]["items"][3]["status"] = item["status"]
    assert d == orig
