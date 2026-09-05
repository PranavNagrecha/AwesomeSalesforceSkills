"""Tests for ``scripts/build_plan.py`` — the build-plan writer.

The contract (``standards/build-orchestration.md``) makes this script the only
writer of derived views and human gate records, so the failure modes that
matter are the ones where it *accepts* something it should reject: a step owned
by a deprecated agent, a dependency cycle, a step with no acceptance test, an
illegal status transition. Each of those gets a negative test here.

Everything runs against a synthetic repo root under ``tmp_path`` — fake
``agents/<id>/AGENT.md`` and ``skills/<domain>/<slug>/SKILL.md`` files — so the
suite does not move when the real roster does. One test deliberately does the
opposite and validates a plan against the real checkout, to catch the case
where the resolver logic drifts from how agents and skills are actually laid
out on disk.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts import build_plan  # noqa: E402


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def run(*argv: str) -> int:
    """Invoke the CLI, normalising the _die() SystemExit into an exit code."""
    try:
        return build_plan.main(list(argv))
    except SystemExit as exc:  # _die()
        return int(exc.code or 0)


AGENT_MD = """---
id: {id}
class: {cls}
version: 1.0.0
status: {status}
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-09-05
updated: 2026-09-05
---

# {id}
"""

SKILL_MD = """---
name: {slug}
category: {domain}
---

# {slug}
"""


@pytest.fixture()
def fixture_repo(tmp_path: Path) -> Path:
    """A tiny stand-in repo: 3 agents, 2 skills, 1 template, 1 decision tree."""
    root = tmp_path / "repo"
    for agent_id, cls, status in (
        ("alpha-designer", "runtime", "stable"),
        ("beta-flow-builder", "runtime", "beta"),
        ("gamma-legacy", "runtime", "deprecated"),
        ("delta-factory", "build", "stable"),
    ):
        target = root / "agents" / agent_id / "AGENT.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(AGENT_MD.format(id=agent_id, cls=cls, status=status), encoding="utf-8")
    for domain, slug in (("admin", "fake-object-design"), ("flow", "fake-flow-patterns")):
        target = root / "skills" / domain / slug / "SKILL.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(SKILL_MD.format(domain=domain, slug=slug), encoding="utf-8")
    template = root / "templates" / "apex" / "FakeHandler.cls"
    template.parent.mkdir(parents=True, exist_ok=True)
    template.write_text("public class FakeHandler {}\n", encoding="utf-8")
    tree = root / "standards" / "decision-trees" / "fake-selection.md"
    tree.parent.mkdir(parents=True, exist_ok=True)
    tree.write_text("# fake tree\n", encoding="utf-8")
    return root


@pytest.fixture()
def requirement(tmp_path: Path) -> Path:
    path = tmp_path / "requirement.md"
    path.write_text(
        "# Case intake\n\n"
        "Every inbound support email must become a Case owned by the right queue "
        "within five minutes, with an SLA clock running.\n",
        encoding="utf-8",
    )
    return path


def step(sid: str, milestone: str, *, agent="alpha-designer", stype="object-model",
         depends_on=None, skills=("admin/fake-object-design",), status="pending",
         tests=None, **extra) -> dict:
    out = {
        "id": sid,
        "milestone": milestone,
        "type": stype,
        "title": f"Step {sid}",
        "agent": agent,
        "skills": list(skills),
        "templates": ["templates/apex/FakeHandler.cls"],
        "decision_trees": ["standards/decision-trees/fake-selection.md"],
        "inputs": {"object": "Case"},
        "outputs": [f"artefacts/{sid}/Case.object-meta.xml"],
        "depends_on": list(depends_on or []),
        "acceptance_tests": tests if tests is not None else [
            {"type": "xml", "description": "every artefact parses"},
        ],
        "status": status,
        "runs": [],
        "human_gate": False,
    }
    out.update(extra)
    return out


def plan_dict(steps, milestones=None, **overrides) -> dict:
    ids = sorted({s["milestone"] for s in steps})
    milestones = milestones or [
        {
            "id": mid,
            "title": f"Milestone {mid}",
            "steps": [s["id"] for s in steps if s["milestone"] == mid],
            "acceptance_tests": [{"type": "manifest", "description": "package.xml consistent"}],
        }
        for mid in ids
    ]
    plan = {
        "build_id": "case-onboarding",
        "title": "Case intake onboarding",
        "version": 1,
        "status": "planned",
        "created": "2026-09-05T09:00:00Z",
        "requirement": {"source_path": "requirement.md", "summary": "Inbound email to Case."},
        "clarifications": [],
        "assumptions": [{"id": "A1", "text": "Service Cloud is licensed."}],
        "scope": {
            "in": ["Case object", "queues"],
            "out": ["CTI"],
            "fit_gap": [{"requirement": "SLA clock", "verdict": "fit", "note": "Entitlements"}],
        },
        "decisions": [{
            "id": "D1",
            "decision": "Record-triggered Flow, not Apex",
            "decision_tree": "standards/decision-trees/fake-selection.md",
            "branch": "Q3",
            "rationale": "No callout needed.",
        }],
        "milestones": milestones,
        "steps": steps,
        "human_gates": [{"name": "clarifications", "status": "pending"},
                        {"name": "plan", "status": "pending"}]
        + [{"name": f"milestone:{m['id']}", "status": "pending"} for m in milestones],
        "artefacts_root": "artefacts",
        "docs": {
            "plan": "PLAN.md",
            "clarifications": "CLARIFICATIONS.md",
            "decisions": "decisions.md",
            "traceability": "traceability.md",
        },
        "history": [],
    }
    plan.update(overrides)
    return plan


def write_plan_file(build_dir: Path, plan: dict) -> Path:
    build_dir.mkdir(parents=True, exist_ok=True)
    path = build_dir / "plan.json"
    path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    return path


def errors_for(plan: dict, repo_root: Path) -> list[str]:
    schema = build_plan.load_schema()
    return [msg for level, msg in build_plan.validate_plan(plan, repo_root, schema)
            if level == "ERROR"]


def set_answer(md_path: Path, qid: str, text: str) -> None:
    """Fill the `Answer:` line under `### <qid>` the way a human would."""
    lines = md_path.read_text(encoding="utf-8").splitlines()
    current = None
    done = False
    for i, line in enumerate(lines):
        header = build_plan._QUESTION_RE.match(line)
        if header:
            current = header.group("id")
            continue
        if not done and current == qid and line.startswith("Answer:"):
            lines[i] = f"Answer: {text}".rstrip()
            done = True
    assert done, f"no Answer: line found for {qid}"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------
# init / validate
# --------------------------------------------------------------------------

def test_init_creates_layout_and_validates(tmp_path, fixture_repo, requirement, capsys):
    build_dir = tmp_path / "case-onboarding"
    rc = run("init", "--build-dir", str(build_dir), "--title", "Case intake onboarding",
             "--requirement", str(requirement), "--repo-root", str(fixture_repo),
             "--now", "2026-09-05T09:00:00Z")
    assert rc == 0
    capsys.readouterr()

    for sub in ("workbook", "artefacts", "tests", "envelopes", "reports"):
        assert (build_dir / sub).is_dir(), f"missing § 2 directory {sub}"
    assert (build_dir / "requirement.md").read_text() == requirement.read_text()
    assert (build_dir / "PLAN.md").is_file()
    assert (build_dir / "CLARIFICATIONS.md").is_file()
    assert (build_dir / "decisions.md").is_file()
    assert (build_dir / "traceability.md").is_file()

    plan = json.loads((build_dir / "plan.json").read_text())
    assert plan["status"] == "intake"
    assert plan["version"] == 1
    assert plan["created"] == "2026-09-05T09:00:00Z"
    assert plan["build_id"] == "case-onboarding"
    assert [g["name"] for g in plan["human_gates"]] == ["clarifications", "plan"]

    assert run("validate", str(build_dir / "plan.json"), "--repo-root", str(fixture_repo)) == 0


def test_init_refuses_missing_requirement(tmp_path, fixture_repo):
    assert run("init", "--build-dir", str(tmp_path / "b"), "--title", "x",
               "--requirement", str(tmp_path / "nope.md"),
               "--repo-root", str(fixture_repo)) == 1


def test_valid_full_plan_passes(tmp_path, fixture_repo, capsys):
    plan = plan_dict([step("M1-S01", "M1"),
                      step("M1-S02", "M1", agent="beta-flow-builder", stype="automation",
                           skills=("flow/fake-flow-patterns",), depends_on=["M1-S01"])])
    path = write_plan_file(tmp_path / "b", plan)
    assert run("validate", str(path), "--repo-root", str(fixture_repo)) == 0
    assert "OK" in capsys.readouterr().out


@pytest.mark.parametrize("agent,fragment", [
    ("gamma-legacy", "deprecated"),
    ("no-such-agent", "has no agents/"),
    ("delta-factory", "not runtime"),
])
def test_agent_must_be_active_runtime(tmp_path, fixture_repo, agent, fragment):
    plan = plan_dict([step("M1-S01", "M1", agent=agent)])
    errors = errors_for(plan, fixture_repo)
    assert any(fragment in e for e in errors), errors
    path = write_plan_file(tmp_path / "b", plan)
    assert run("validate", str(path), "--repo-root", str(fixture_repo)) == 1


def test_unresolvable_skill_template_and_tree(fixture_repo):
    plan = plan_dict([step("M1-S01", "M1", skills=("admin/does-not-exist",),
                           templates=["templates/apex/Ghost.cls"],
                           decision_trees=["standards/decision-trees/ghost.md"])])
    errors = errors_for(plan, fixture_repo)
    assert any("does not resolve to skills/admin/does-not-exist/SKILL.md" in e for e in errors)
    assert any("template 'templates/apex/Ghost.cls' does not exist" in e for e in errors)
    assert any("decision tree" in e for e in errors)


def test_unknown_step_type_rejected(fixture_repo):
    plan = plan_dict([step("M1-S01", "M1", stype="sharing-model")])
    errors = errors_for(plan, fixture_repo)
    assert any("sharing-model" in e for e in errors), errors
    # The § 4 table is enforced twice on purpose: the schema enum, and a
    # hard-coded list in the script. Exercise the second one directly, since
    # validate_plan short-circuits on schema errors.
    semantic = [m for lvl, m in build_plan.semantic_issues(plan, fixture_repo) if lvl == "ERROR"]
    assert any("section 4 table" in m for m in semantic), semantic


def test_step_type_list_matches_the_schema_enum():
    schema = build_plan.load_schema()
    assert schema["$defs"]["step"]["properties"]["type"]["enum"] == build_plan.STEP_TYPES
    assert (schema["$defs"]["acceptanceTest"]["properties"]["type"]["enum"]
            == build_plan.TEST_TYPES)
    assert schema["properties"]["status"]["enum"] == build_plan.BUILD_STATUSES
    assert (sorted(schema["$defs"]["step"]["properties"]["status"]["enum"])
            == sorted(build_plan.ALLOWED_TRANSITIONS))


def test_dependency_cycle_detected(fixture_repo):
    plan = plan_dict([step("M1-S01", "M1", depends_on=["M1-S02"]),
                      step("M1-S02", "M1", depends_on=["M1-S01"])])
    errors = errors_for(plan, fixture_repo)
    assert any(e.startswith("depends_on cycle:") for e in errors), errors


def test_dangling_dependency_detected(fixture_repo):
    plan = plan_dict([step("M1-S01", "M1", depends_on=["M1-S99"])])
    assert any("does not exist" in e for e in errors_for(plan, fixture_repo))


def test_step_without_acceptance_test_fails(fixture_repo):
    plan = plan_dict([step("M1-S01", "M1", tests=[])])
    errors = errors_for(plan, fixture_repo)
    assert any("at least 1 item" in e or "acceptance test" in e for e in errors), errors


def test_milestone_without_acceptance_test_fails(fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    plan["milestones"][0]["acceptance_tests"] = []
    assert any("acceptance test" in e or "at least 1 item" in e
               for e in errors_for(plan, fixture_repo))


def test_milestone_steps_must_list_exactly_its_steps(fixture_repo):
    plan = plan_dict([step("M1-S01", "M1"), step("M1-S02", "M1")])
    plan["milestones"][0]["steps"] = ["M1-S01"]
    assert any("must list exactly its steps" in e for e in errors_for(plan, fixture_repo))


def test_milestone_ids_must_be_ordered(fixture_repo):
    plan = plan_dict([step("M2-S01", "M2")])
    assert any("out of order" in e for e in errors_for(plan, fixture_repo))


def test_step_in_unknown_milestone(fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    plan["steps"][0]["milestone"] = "M9"
    plan["steps"][0]["id"] = "M9-S01"
    plan["milestones"][0]["steps"] = []
    errors = errors_for(plan, fixture_repo)
    assert any("is not defined in milestones[]" in e for e in errors), errors


def test_missing_gates_reported_and_ensure_gates_adds_them(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    plan["human_gates"] = []
    path = write_plan_file(tmp_path / "b", plan)
    assert run("validate", str(path), "--repo-root", str(fixture_repo)) == 1
    assert run("ensure-gates", str(path), "--repo-root", str(fixture_repo)) == 0
    names = [g["name"] for g in json.loads(path.read_text())["human_gates"]]
    assert names == ["clarifications", "plan", "milestone:M1"]
    assert run("validate", str(path), "--repo-root", str(fixture_repo)) == 0


def test_deploy_command_in_acceptance_test_rejected(fixture_repo):
    plan = plan_dict([step("M1-S01", "M1", tests=[
        {"type": "command", "command": "sf project deploy start -x package.xml"}])])
    assert any("never deploy" in e for e in errors_for(plan, fixture_repo))


def test_step_without_skills_is_a_warning_not_an_error(tmp_path, fixture_repo, capsys):
    plan = plan_dict([step("M1-S01", "M1", skills=())])
    path = write_plan_file(tmp_path / "b", plan)
    assert run("validate", str(path), "--repo-root", str(fixture_repo)) == 0
    assert "WARN" in capsys.readouterr().out


# --------------------------------------------------------------------------
# render
# --------------------------------------------------------------------------

def test_render_is_deterministic(tmp_path, fixture_repo):
    plan = plan_dict([
        step("M1-S01", "M1"),
        step("M1-S02", "M1", agent="beta-flow-builder", stype="automation",
             skills=("flow/fake-flow-patterns",), depends_on=["M1-S01"]),
    ], clarifications=[{"id": "Q1", "question": "Which queue owns unrouted email?",
                        "kind": "blocking", "why": "Routing depends on it.",
                        "proposed_default": "Tier 1 Support", "status": "open"}])
    build_dir = tmp_path / "b"
    path = write_plan_file(build_dir, plan)

    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    first = {p.name: p.read_bytes() for p in (build_dir / "PLAN.md",
                                              build_dir / "CLARIFICATIONS.md")}
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    second = {p.name: p.read_bytes() for p in (build_dir / "PLAN.md",
                                               build_dir / "CLARIFICATIONS.md")}
    assert first == second, "render must be byte-identical across runs"

    plan_md = (build_dir / "PLAN.md").read_text()
    assert "Case intake onboarding" in plan_md
    assert "`M1-S02`" in plan_md and "beta-flow-builder" in plan_md
    assert "| Gate | Status | By | At | Notes |" in plan_md
    clar_md = (build_dir / "CLARIFICATIONS.md").read_text()
    assert "### Q1" in clar_md and "Answer:" in clar_md


def test_render_refuses_off_schema_plan(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    del plan["scope"]
    path = write_plan_file(tmp_path / "b", plan)
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 1
    assert not (tmp_path / "b" / "PLAN.md").exists()


# --------------------------------------------------------------------------
# ingest-answers
# --------------------------------------------------------------------------

def _plan_with_questions(tmp_path: Path, fixture_repo: Path) -> Path:
    plan = plan_dict([step("M1-S01", "M1")], clarifications=[
        {"id": "Q1", "question": "Which queue owns unrouted email?", "kind": "blocking",
         "proposed_default": "Tier 1 Support", "status": "open"},
        {"id": "Q2", "question": "Do we need a business-hours calendar?",
         "kind": "informational", "proposed_default": "9-5 Mon-Fri", "status": "open"},
    ])
    path = write_plan_file(tmp_path / "b", plan)
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    return path


def test_ingest_answers_round_trip(tmp_path, fixture_repo):
    path = _plan_with_questions(tmp_path, fixture_repo)
    clar = path.parent / "CLARIFICATIONS.md"
    set_answer(clar, "Q1", "Tier 1 Support")
    set_answer(clar, "Q2", "Yes — 9-5 Mon-Fri")

    assert run("ingest-answers", str(path), "--repo-root", str(fixture_repo)) == 0
    clarifications = {c["id"]: c for c in json.loads(path.read_text())["clarifications"]}
    assert clarifications["Q1"]["answer"] == "Tier 1 Support"
    assert clarifications["Q1"]["status"] == "answered"
    assert clarifications["Q2"]["status"] == "answered"

    # Re-render shows the stored answers, and re-ingesting is a no-op.
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    assert "Answer: Tier 1 Support" in clar.read_text()
    before = path.read_bytes()
    assert run("ingest-answers", str(path), "--repo-root", str(fixture_repo)) == 0
    assert path.read_bytes() == before


def test_ingest_refuses_empty_blocking_answer(tmp_path, fixture_repo):
    path = _plan_with_questions(tmp_path, fixture_repo)
    set_answer(path.parent / "CLARIFICATIONS.md", "Q2", "Yes")
    before = path.read_bytes()
    assert run("ingest-answers", str(path), "--repo-root", str(fixture_repo)) == 1
    assert path.read_bytes() == before, "a refused ingest must leave plan.json untouched"


def test_defer_requires_allow_deferred(tmp_path, fixture_repo):
    path = _plan_with_questions(tmp_path, fixture_repo)
    clar = path.parent / "CLARIFICATIONS.md"
    set_answer(clar, "Q1", "DEFER: legal has not signed off")
    set_answer(clar, "Q2", "Yes")

    assert run("ingest-answers", str(path), "--repo-root", str(fixture_repo)) == 1
    assert run("ingest-answers", str(path), "--repo-root", str(fixture_repo),
               "--allow-deferred") == 0
    q1 = json.loads(path.read_text())["clarifications"][0]
    assert q1["status"] == "deferred"
    assert q1["answer"] == "DEFER: legal has not signed off"


def test_defer_without_reason_refused(tmp_path, fixture_repo):
    path = _plan_with_questions(tmp_path, fixture_repo)
    clar = path.parent / "CLARIFICATIONS.md"
    set_answer(clar, "Q1", "DEFER:")
    set_answer(clar, "Q2", "Yes")
    assert run("ingest-answers", str(path), "--repo-root", str(fixture_repo),
               "--allow-deferred") == 1


# --------------------------------------------------------------------------
# state machine
# --------------------------------------------------------------------------

def test_state_machine_rejects_illegal_transition(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    before = path.read_bytes()
    assert run("set-status", str(path), "M1-S01", "documented",
               "--repo-root", str(fixture_repo)) == 1
    assert path.read_bytes() == before
    assert run("set-status", str(path), "M1-S01", "running",
               "--repo-root", str(fixture_repo)) == 0
    assert json.loads(path.read_text())["steps"][0]["status"] == "running"


def test_set_status_appends_runs_and_never_overwrites(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    for status, result in (("running", "started"), ("built", "artefacts written"),
                           ("tested", "checkers green"), ("documented", "workbook updated")):
        assert run("set-status", str(path), "M1-S01", status,
                   "--run-agent", "alpha-designer",
                   "--envelope", f"envelopes/M1-S01/{status}.json",
                   "--result", result, "--started", "2026-09-05T10:00:00Z",
                   "--repo-root", str(fixture_repo)) == 0
    runs = json.loads(path.read_text())["steps"][0]["runs"]
    assert len(runs) == 4
    assert [r["result"] for r in runs] == ["started", "artefacts written",
                                           "checkers green", "workbook updated"]
    # documented -> running re-runs a step (contract § 8) and appends again.
    assert run("set-status", str(path), "M1-S01", "running", "--run-agent", "alpha-designer",
               "--envelope", "envelopes/M1-S01/rerun.json",
               "--repo-root", str(fixture_repo)) == 0
    assert len(json.loads(path.read_text())["steps"][0]["runs"]) == 5


def test_blocked_requires_a_reason(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    assert run("set-status", str(path), "M1-S01", "blocked",
               "--repo-root", str(fixture_repo)) == 1
    assert run("set-status", str(path), "M1-S01", "blocked", "--blocked-reason", "skill-gap",
               "--repo-root", str(fixture_repo)) == 0
    assert json.loads(path.read_text())["steps"][0]["blocked_reason"] == "skill-gap"


# --------------------------------------------------------------------------
# gates and `next`
# --------------------------------------------------------------------------

def test_next_respects_gates_and_depends_on(tmp_path, fixture_repo, capsys):
    plan = plan_dict([
        step("M1-S01", "M1"),
        step("M1-S02", "M1", agent="beta-flow-builder", stype="automation",
             skills=("flow/fake-flow-patterns",), depends_on=["M1-S01"]),
    ])
    path = write_plan_file(tmp_path / "b", plan)

    assert run("next", str(path), "--repo-root", str(fixture_repo)) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == []
    assert "gate 'clarifications'" in captured.err

    for gate in ("clarifications", "plan"):
        assert run("gate", str(path), gate, "approve", "--by", "pranav",
                   "--at", "2026-09-05T11:00:00Z", "--repo-root", str(fixture_repo)) == 0
    capsys.readouterr()

    assert run("next", str(path), "--repo-root", str(fixture_repo)) == 0
    runnable = json.loads(capsys.readouterr().out)
    assert [s["id"] for s in runnable] == ["M1-S01"], "M1-S02 waits on its dependency"

    for status in ("running", "built", "tested", "documented"):
        assert run("set-status", str(path), "M1-S01", status,
                   "--repo-root", str(fixture_repo)) == 0
    capsys.readouterr()
    assert run("next", str(path), "--repo-root", str(fixture_repo)) == 0
    assert [s["id"] for s in json.loads(capsys.readouterr().out)] == ["M1-S02"]


def test_next_refuses_a_milestone_whose_predecessor_gate_is_open(tmp_path, fixture_repo, capsys):
    plan = plan_dict([step("M1-S01", "M1", status="documented"), step("M2-S01", "M2")])
    plan["human_gates"] = [
        {"name": "clarifications", "status": "approved", "by": "p", "at": "2026-09-05T09:00:00Z"},
        {"name": "plan", "status": "approved", "by": "p", "at": "2026-09-05T09:00:00Z"},
        {"name": "milestone:M1", "status": "pending"},
        {"name": "milestone:M2", "status": "pending"},
    ]
    path = write_plan_file(tmp_path / "b", plan)
    assert run("next", str(path), "--repo-root", str(fixture_repo)) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == []
    assert "milestone:M1" in captured.err and "M2" in captured.err

    assert run("gate", str(path), "milestone:M1", "approve", "--by", "pranav",
               "--at", "2026-09-05T12:00:00Z", "--repo-root", str(fixture_repo)) == 0
    capsys.readouterr()
    assert run("next", str(path), "--repo-root", str(fixture_repo)) == 0
    assert [s["id"] for s in json.loads(capsys.readouterr().out)] == ["M2-S01"]


def test_gate_flow_end_to_end(tmp_path, fixture_repo, capsys):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)

    assert run("gate", str(path), "clarifications", "approve", "--by", "pranav",
               "--notes", "defaults accepted", "--at", "2026-09-05T10:00:00Z",
               "--repo-root", str(fixture_repo)) == 0
    assert run("gate", str(path), "plan", "approve", "--by", "pranav",
               "--at", "2026-09-05T10:05:00Z", "--repo-root", str(fixture_repo)) == 0
    assert json.loads(path.read_text())["status"] == "approved"

    for status in ("running", "built", "tested", "documented"):
        assert run("set-status", str(path), "M1-S01", status,
                   "--repo-root", str(fixture_repo)) == 0

    assert run("gate", str(path), "milestone:M1", "approve", "--by", "pranav",
               "--at", "2026-09-05T13:00:00Z", "--repo-root", str(fixture_repo)) == 0
    final = json.loads(path.read_text())
    assert final["status"] == "done", "last milestone accepted -> done"
    assert final["milestones"][0]["status"] == "accepted"
    gate = [g for g in final["human_gates"] if g["name"] == "clarifications"][0]
    assert gate == {"name": "clarifications", "status": "approved", "by": "pranav",
                    "at": "2026-09-05T10:00:00Z", "notes": "defaults accepted"}
    capsys.readouterr()

    assert run("status", str(path), "--repo-root", str(fixture_repo)) == 0
    summary = capsys.readouterr().out
    assert "case-onboarding" in summary and "M1" in summary


def test_middle_milestone_gate_sets_building_not_done(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1", status="documented"), step("M2-S01", "M2")])
    path = write_plan_file(tmp_path / "b", plan)
    assert run("gate", str(path), "milestone:M1", "approve", "--by", "pranav",
               "--at", "2026-09-05T13:00:00Z", "--repo-root", str(fixture_repo)) == 0
    assert json.loads(path.read_text())["status"] == "building"


def test_plan_gate_rejection_bumps_version_and_archives(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    assert run("gate", str(path), "plan", "reject", "--by", "pranav",
               "--notes", "milestone 1 has no access step",
               "--at", "2026-09-05T10:30:00Z", "--repo-root", str(fixture_repo)) == 0
    after = json.loads(path.read_text())
    assert after["status"] == "plan-rejected"
    assert after["version"] == 2
    assert len(after["history"]) == 1
    archived = after["history"][0]
    assert archived["version"] == 1
    assert archived["plan"]["status"] == "planned"
    assert "history" not in archived["plan"], "snapshots must not nest history"


def test_milestone_gate_rejection_leaves_building(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1", status="documented")])
    path = write_plan_file(tmp_path / "b", plan)
    assert run("gate", str(path), "milestone:M1", "reject", "--by", "pranav",
               "--at", "2026-09-05T13:00:00Z", "--repo-root", str(fixture_repo)) == 0
    after = json.loads(path.read_text())
    assert after["status"] == "building"
    assert after["version"] == 1
    assert after["history"] == []


def test_unknown_gate_refused(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    before = path.read_bytes()
    assert run("gate", str(path), "milestone:M7", "approve", "--by", "pranav",
               "--repo-root", str(fixture_repo)) == 1
    assert path.read_bytes() == before


# --------------------------------------------------------------------------
# The real repo — catches resolver drift from the actual layout
# --------------------------------------------------------------------------

REAL_AGENTS = ("object-designer", "flow-builder")
REAL_SKILLS = ("admin/object-creation-and-design", "flow/flow-bulkification")
REAL_TEMPLATE = "templates/apex/TriggerHandler.cls"
REAL_TREE = "standards/decision-trees/automation-selection.md"


@pytest.mark.skipif(not (REPO_ROOT / "agents" / "object-designer" / "AGENT.md").is_file(),
                    reason="running outside the SfSkills checkout")
def test_validates_against_the_real_repo(tmp_path):
    steps = [
        step("M1-S01", "M1", agent=REAL_AGENTS[0], stype="object-model",
             skills=(REAL_SKILLS[0],), templates=[REAL_TEMPLATE], decision_trees=[REAL_TREE]),
        step("M1-S02", "M1", agent=REAL_AGENTS[1], stype="automation",
             skills=(REAL_SKILLS[1],), templates=[REAL_TEMPLATE], decision_trees=[REAL_TREE],
             depends_on=["M1-S01"],
             tests=[{"type": "xml", "description": "Flow XML parses"},
                    {"type": "manual", "description": "admin confirms the fault path emails"}]),
    ]
    plan = plan_dict(steps)
    plan["decisions"][0]["decision_tree"] = REAL_TREE
    path = write_plan_file(tmp_path / "real", plan)
    assert run("validate", str(path), "--repo-root", str(REPO_ROOT)) == 0

    # And the resolver must actually reject a deprecated real agent.
    plan["steps"][0]["agent"] = "picklist-governor"
    path2 = write_plan_file(tmp_path / "real-bad", plan)
    assert run("validate", str(path2), "--repo-root", str(REPO_ROOT)) == 1
