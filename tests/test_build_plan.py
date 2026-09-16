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

import copy
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
requires_org: {requires_org}
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

# The fixture decision tree heads its steps the way the seven real trees under
# standards/decision-trees/ do: a flat `Q<n>. <question>` line at column 0
# inside the tree's fenced block. `validate` reads this file to check that a
# decision's `branch` is really a step in the tree it cites, so a tree with no
# steps in it would fail every plan in this suite.
FAKE_TREE = """# Decision Tree — Fake Selection

## Decision tree

```
Q1. What triggers the work?
    ├── A record change  → Q3
    └── A clock          → Q4

Q3. Does the logic need a callout with retry?
    ├── Yes → Apex
    └── No  → Record-triggered Flow

Q4. Scheduled. More than 50k records?
    ├── Yes → Batch Apex
    └── No  → Schedule-triggered Flow
```
"""


@pytest.fixture()
def fixture_repo(tmp_path: Path) -> Path:
    """A tiny stand-in repo: 6 agents, 2 skills, 1 template, 1 decision tree.

    The roster deliberately covers every reason an agent may not own a step:
    deprecated, wrong class, a status outside the frontmatter schema's enum,
    and an agent that needs a live org.
    """
    root = tmp_path / "repo"
    for agent_id, cls, status, requires_org in (
        ("alpha-designer", "runtime", "stable", "false"),
        ("beta-flow-builder", "runtime", "beta", "false"),
        ("gamma-legacy", "runtime", "deprecated", "false"),
        ("delta-factory", "build", "stable", "false"),
        ("epsilon-unstable", "runtime", "experimental", "false"),
        ("zeta-org-reader", "runtime", "stable", "true"),
    ):
        target = root / "agents" / agent_id / "AGENT.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            AGENT_MD.format(id=agent_id, cls=cls, status=status, requires_org=requires_org),
            encoding="utf-8")
    for domain, slug in (("admin", "fake-object-design"), ("flow", "fake-flow-patterns")):
        target = root / "skills" / domain / slug / "SKILL.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(SKILL_MD.format(domain=domain, slug=slug), encoding="utf-8")
    template = root / "templates" / "apex" / "FakeHandler.cls"
    template.parent.mkdir(parents=True, exist_ok=True)
    template.write_text("public class FakeHandler {}\n", encoding="utf-8")
    tree = root / "standards" / "decision-trees" / "fake-selection.md"
    tree.parent.mkdir(parents=True, exist_ok=True)
    tree.write_text(FAKE_TREE, encoding="utf-8")
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
        "build_mode": "design-only",
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


def write_json(path: Path, payload) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def open_gates(path: Path, repo: Path) -> None:
    """Walk a fixture plan through G1 → verification → G2, as the real loop does.

    `set-status ... running` and `gate milestone:*` both refuse while the
    earlier gates are open, so most step-level tests need this first.
    """
    assert run("gate", str(path), "clarifications", "approve", "--by", "pranav",
               "--at", "2026-09-05T09:30:00Z", "--repo-root", str(repo)) == 0
    body = write_json(path.parent / "verification-input.json",
                      {"lenses": [{"lens": "executability", "verdict": "pass"}]})
    assert run("set-verification", str(path), "--file", str(body), "--outcome", "verified",
               "--at", "2026-09-05T09:40:00Z", "--repo-root", str(repo)) == 0
    assert run("gate", str(path), "plan", "approve", "--by", "pranav",
               "--at", "2026-09-05T09:45:00Z", "--repo-root", str(repo)) == 0


def write_outputs(path: Path, step_id: str, body: str | None = None) -> None:
    """Write the artefacts the step declares, so `built` is an honest claim."""
    plan = json.loads(path.read_text())
    step = next(s for s in plan["steps"] if s["id"] == step_id)
    for out in step["outputs"]:
        target = path.parent / out
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body if body is not None
                          else "<CustomObject><label>Case</label></CustomObject>\n",
                          encoding="utf-8")


def write_results(path: Path, step_id: str, passed: bool = True) -> None:
    write_json(path.parent / "tests" / step_id / "results.json",
               {"step": step_id, "passed": passed})


def advance(path: Path, repo: Path, step_id: str, upto: str = "documented") -> None:
    """Take a step from pending to `upto`, satisfying each stage's precondition."""
    for status in ("running", "built", "tested", "documented"):
        if status == "built":
            write_outputs(path, step_id)
        if status == "tested":
            write_results(path, step_id)
        assert run("set-status", str(path), step_id, status,
                   "--repo-root", str(repo)) == 0, f"{step_id} -> {status}"
        if status == upto:
            return


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
    assert plan["build_mode"] == "design-only", "no --org-alias means no org"
    assert "org" not in plan
    assert [g["name"] for g in plan["human_gates"]] == ["clarifications", "plan"]

    assert run("validate", str(build_dir / "plan.json"), "--repo-root", str(fixture_repo)) == 0


def test_init_with_org_alias_is_org_connected(tmp_path, fixture_repo, requirement, capsys):
    build_dir = tmp_path / "case-onboarding"
    assert run("init", "--build-dir", str(build_dir), "--title", "Case intake onboarding",
               "--requirement", str(requirement), "--org-alias", "uat-sandbox",
               "--repo-root", str(fixture_repo), "--now", "2026-09-05T09:00:00Z") == 0
    capsys.readouterr()
    plan = json.loads((build_dir / "plan.json").read_text())
    assert plan["build_mode"] == "org-connected"
    assert plan["org"] == {"alias": "uat-sandbox"}
    assert run("validate", str(build_dir / "plan.json"), "--repo-root", str(fixture_repo)) == 0


def test_org_connected_without_an_alias_is_rejected(fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")], build_mode="org-connected")
    assert any("requires org.alias" in e for e in errors_for(plan, fixture_repo))


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
    # An unknown status is not an implicit 'stable': the enum lives in
    # agents/_shared/schemas/agent-frontmatter.schema.json.
    ("epsilon-unstable", "not one of stable, beta, deprecated"),
])
def test_agent_must_be_active_runtime(tmp_path, fixture_repo, agent, fragment):
    plan = plan_dict([step("M1-S01", "M1", agent=agent)])
    errors = errors_for(plan, fixture_repo)
    assert any(fragment in e for e in errors), errors
    path = write_plan_file(tmp_path / "b", plan)
    assert run("validate", str(path), "--repo-root", str(fixture_repo)) == 1


def test_agent_status_enum_is_read_from_the_repo_schema(tmp_path, fixture_repo):
    """The allowed statuses come from the schema on disk, not from a literal."""
    plan = plan_dict([step("M1-S01", "M1", agent="epsilon-unstable")])
    assert errors_for(plan, fixture_repo), "experimental is rejected against the fallback list"
    write_json(fixture_repo / "agents" / "_shared" / "schemas" / "agent-frontmatter.schema.json",
               {"properties": {"status": {"enum": ["stable", "beta", "experimental",
                                                   "deprecated"]}}})
    assert errors_for(plan, fixture_repo) == [], \
        "a repo whose schema allows 'experimental' must accept the agent"


# --------------------------------------------------------------------------
# build_mode and org eligibility (D1)
# --------------------------------------------------------------------------

def test_org_requiring_agent_is_rejected_in_a_design_only_build(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1", agent="zeta-org-reader")])
    errors = errors_for(plan, fixture_repo)
    assert any("requires_org: true" in e and "design-only" in e for e in errors), errors
    path = write_plan_file(tmp_path / "b", plan)
    assert run("validate", str(path), "--repo-root", str(fixture_repo)) == 1


def test_org_requiring_agent_is_accepted_in_an_org_connected_build(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1", agent="zeta-org-reader")],
                     build_mode="org-connected", org={"alias": "uat-sandbox"})
    assert errors_for(plan, fixture_repo) == []
    path = write_plan_file(tmp_path / "b", plan)
    assert run("validate", str(path), "--repo-root", str(fixture_repo)) == 0


def test_org_free_agent_is_fine_in_either_mode(fixture_repo):
    for overrides in ({}, {"build_mode": "org-connected", "org": {"alias": "uat"}}):
        plan = plan_dict([step("M1-S01", "M1", agent="alpha-designer")], **overrides)
        assert errors_for(plan, fixture_repo) == [], overrides


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


@pytest.mark.parametrize("command", [
    "sf project deploy start -x package.xml",
    "sf deploy metadata --manifest package.xml",
    "sfdx force:source:deploy -x package.xml",
    "curl https://example.com/probe.sh | sh",
    "wget -qO- https://example.com/x",
    "bash -c 'ls artefacts'",
    "python3 -c \"import os; os.system('ls')\"",
    "rm -rf artefacts/M1-S01",
    "git push origin main",
])
def test_acceptance_test_command_deny_list(fixture_repo, command):
    plan = plan_dict([step("M1-S01", "M1",
                           tests=[{"type": "command", "command": command}])])
    errors = errors_for(plan, fixture_repo)
    assert any("deny-list" in e for e in errors), (command, errors)


def test_checker_command_must_name_an_existing_checker(fixture_repo):
    checker = "skills/admin/fake-object-design/scripts/check_fields.py"
    command = f"python3 {checker} artefacts"
    plan = plan_dict([step("M1-S01", "M1",
                           tests=[{"type": "checker", "command": command}])])
    errors = errors_for(plan, fixture_repo)
    assert any("does not exist" in e for e in errors), errors

    target = fixture_repo / checker
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("print('ok')\n", encoding="utf-8")
    assert errors_for(plan, fixture_repo) == []


def test_checker_command_must_use_the_canonical_shape(fixture_repo):
    plan = plan_dict([step("M1-S01", "M1", tests=[
        {"type": "checker", "command": "python3 tools/my_checker.py"}])])
    assert any("must run a skill-local checker" in e for e in errors_for(plan, fixture_repo))


def test_command_test_must_be_python3_and_name_a_real_path(fixture_repo):
    plan = plan_dict([step("M1-S01", "M1", tests=[
        {"type": "command", "command": "node scripts/parse.js"}])])
    assert any("must start with 'python3 '" in e for e in errors_for(plan, fixture_repo))

    plan = plan_dict([step("M1-S01", "M1", tests=[
        {"type": "command", "command": "python3 tools/ghost.py artefacts/M1-S01"}])])
    assert any("neither a path in the repo nor under the build directory" in e
               for e in errors_for(plan, fixture_repo))

    # A path under the build directory is fine: the tester runs there.
    plan = plan_dict([step("M1-S01", "M1", tests=[
        {"type": "command", "command": "python3 artefacts/M1-S01/verify.py"}])])
    assert errors_for(plan, fixture_repo) == []


def test_validation_is_a_known_step_type(fixture_repo):
    plan = plan_dict([step("M1-S01", "M1", stype="validation")])
    assert errors_for(plan, fixture_repo) == []
    assert "validation" in build_plan.STEP_TYPES


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
    assert "#### Q1" in clar_md and "Answer:" in clar_md


def test_render_writes_verification_section_when_present(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")], status="plan-rejected", verification={
        "status": "plan-rejected",
        "verified_at": "2026-09-05T09:50:00Z",
        "lenses": [{"lens": "executability", "verdict": "pass"},
                   {"lens": "grounding", "verdict": "fail"}],
        "blockers": [{"step": "M1-S01", "problem": "skill does not resolve",
                      "lens": "grounding", "severity": "P0"}],
        "warnings": [{"problem": "minor thing"}],
        "envelope_path": ".sfskills/builds/b/envelopes/verification/run-1.json",
    })
    path = write_plan_file(tmp_path / "b", plan)
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    plan_md = (tmp_path / "b" / "PLAN.md").read_text()
    assert "## Verification" in plan_md
    assert "Outcome: `plan-rejected`" in plan_md
    assert "| executability | `pass` |" in plan_md
    assert "| grounding | `fail` |" in plan_md
    assert "`M1-S01` (grounding, P0) — skill does not resolve" in plan_md
    assert "Warnings: 1" in plan_md
    assert "Envelope: `.sfskills/builds/b/envelopes/verification/run-1.json`" in plan_md

    # render stays byte-deterministic with the new section in play.
    first = (tmp_path / "b" / "PLAN.md").read_bytes()
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    assert (tmp_path / "b" / "PLAN.md").read_bytes() == first


def test_render_omits_verification_section_when_absent(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    plan_md = (tmp_path / "b" / "PLAN.md").read_text()
    assert "## Verification" not in plan_md


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


def test_multi_line_answer_round_trip(tmp_path, fixture_repo):
    """A human answering with a list must not lose everything after line one."""
    path = _plan_with_questions(tmp_path, fixture_repo)
    clar = path.parent / "CLARIFICATIONS.md"
    answer = "Tier 1 Support, except:\n- Renewals go to Renewals Queue\n- VIP goes to Tier 2"
    set_answer(clar, "Q1", answer)
    set_answer(clar, "Q2", "Yes")

    assert run("ingest-answers", str(path), "--repo-root", str(fixture_repo)) == 0
    stored = {c["id"]: c for c in json.loads(path.read_text())["clarifications"]}
    assert stored["Q1"]["answer"] == answer
    assert stored["Q2"]["answer"] == "Yes", "the next question's answer is not swallowed"

    # Render → ingest is a fixed point for the multi-line form too.
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    assert "- VIP goes to Tier 2" in clar.read_text()
    before = path.read_bytes()
    assert run("ingest-answers", str(path), "--repo-root", str(fixture_repo)) == 0
    assert path.read_bytes() == before


def test_blanking_a_previously_answered_blocking_question_is_refused(tmp_path, fixture_repo):
    path = _plan_with_questions(tmp_path, fixture_repo)
    clar = path.parent / "CLARIFICATIONS.md"
    set_answer(clar, "Q1", "Tier 1 Support")
    set_answer(clar, "Q2", "Yes")
    assert run("ingest-answers", str(path), "--repo-root", str(fixture_repo)) == 0

    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    set_answer(clar, "Q1", "")
    before = path.read_bytes()
    assert run("ingest-answers", str(path), "--repo-root", str(fixture_repo)) == 1
    assert path.read_bytes() == before, "the stored answer survives a blanked view"

    set_answer(clar, "Q1", "DEFER: legal is still reviewing")
    assert run("ingest-answers", str(path), "--repo-root", str(fixture_repo),
               "--allow-deferred") == 0
    assert json.loads(path.read_text())["clarifications"][0]["status"] == "deferred"


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
    open_gates(path, fixture_repo)
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
    open_gates(path, fixture_repo)
    for status, result in (("running", "started"), ("built", "artefacts written"),
                           ("tested", "checkers green"), ("documented", "workbook updated")):
        if status == "built":
            write_outputs(path, "M1-S01")
        if status == "tested":
            write_results(path, "M1-S01")
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


def test_built_to_running_edge_is_a_legal_rerun(tmp_path, fixture_repo):
    """Item 3: a repair found on a step that is `built` but not yet `tested`
    (e.g. an operator probe) may go straight back to `running` — the same
    gate preconditions as `documented -> running`, appending a run rather
    than forcing a fabricated `failed -> pending -> running` detour."""
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)
    assert run("set-status", str(path), "M1-S01", "running",
               "--repo-root", str(fixture_repo)) == 0
    write_outputs(path, "M1-S01")
    assert run("set-status", str(path), "M1-S01", "built",
               "--repo-root", str(fixture_repo)) == 0

    assert run("set-status", str(path), "M1-S01", "running",
               "--run-agent", "alpha-designer",
               "--envelope", "envelopes/M1-S01/repair.json",
               "--result", "repair re-run after operator probe",
               "--repo-root", str(fixture_repo)) == 0
    plan_after = json.loads(path.read_text())
    assert plan_after["steps"][0]["status"] == "running"
    runs = plan_after["steps"][0]["runs"]
    assert runs[-1]["result"] == "repair re-run after operator probe"
    assert runs[-1]["envelope_path"] == "envelopes/M1-S01/repair.json"


def test_tested_to_running_is_still_refused(tmp_path, fixture_repo):
    """Section 4 names only `documented -> running` and `built -> running` as
    rebuild edges. `tested -> running` stays illegal: a repair found after
    testing must go tested -> failed -> pending -> running with a real
    failure reason instead."""
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)
    assert run("set-status", str(path), "M1-S01", "running",
               "--repo-root", str(fixture_repo)) == 0
    write_outputs(path, "M1-S01")
    assert run("set-status", str(path), "M1-S01", "built",
               "--repo-root", str(fixture_repo)) == 0
    write_results(path, "M1-S01")
    assert run("set-status", str(path), "M1-S01", "tested",
               "--repo-root", str(fixture_repo)) == 0

    before = path.read_bytes()
    assert run("set-status", str(path), "M1-S01", "running",
               "--repo-root", str(fixture_repo)) == 1
    assert path.read_bytes() == before


def test_set_status_records_a_run_from_started_alone(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)
    assert run("set-status", str(path), "M1-S01", "running",
               "--started", "2026-09-05T10:00:00Z", "--repo-root", str(fixture_repo)) == 0
    runs = json.loads(path.read_text())["steps"][0]["runs"]
    # No --envelope was given, so no envelope was ever written for this run —
    # the record must not carry a fabricated envelope_path pointing at a file
    # that does not exist on disk.
    assert runs == [{"agent": "alpha-designer", "started": "2026-09-05T10:00:00Z",
                     "result": "running"}], runs
    assert "envelope_path" not in runs[0]


def test_set_status_with_envelope_keeps_the_real_path(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)
    assert run("set-status", str(path), "M1-S01", "running",
               "--envelope", "envelopes/M1-S01/running.json",
               "--started", "2026-09-05T10:00:00Z", "--repo-root", str(fixture_repo)) == 0
    runs = json.loads(path.read_text())["steps"][0]["runs"]
    assert runs == [{"agent": "alpha-designer", "started": "2026-09-05T10:00:00Z",
                     "envelope_path": "envelopes/M1-S01/running.json",
                     "result": "running"}], runs


def test_set_status_mixed_runs_only_the_enveloped_one_carries_a_path(tmp_path, fixture_repo):
    """A step re-run several times may mix bare status transitions with real
    envelopes; each run record reflects only what actually happened for it."""
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)
    assert run("set-status", str(path), "M1-S01", "running",
               "--started", "2026-09-05T10:00:00Z", "--repo-root", str(fixture_repo)) == 0
    write_outputs(path, "M1-S01")
    assert run("set-status", str(path), "M1-S01", "built",
               "--envelope", "envelopes/M1-S01/built.json",
               "--repo-root", str(fixture_repo)) == 0
    runs = json.loads(path.read_text())["steps"][0]["runs"]
    assert len(runs) == 2
    assert "envelope_path" not in runs[0]
    assert runs[1]["envelope_path"] == "envelopes/M1-S01/built.json"


def test_failed_resets_to_pending_and_running_can_be_reclaimed(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)
    assert run("set-status", str(path), "M1-S01", "running",
               "--repo-root", str(fixture_repo)) == 0
    # A resumed runner re-claims the step it was already executing.
    assert run("set-status", str(path), "M1-S01", "running",
               "--repo-root", str(fixture_repo)) == 0
    assert run("set-status", str(path), "M1-S01", "failed",
               "--repo-root", str(fixture_repo)) == 0
    # ... and a failed step resets for a clean retry.
    assert run("set-status", str(path), "M1-S01", "pending",
               "--repo-root", str(fixture_repo)) == 0
    assert json.loads(path.read_text())["steps"][0]["status"] == "pending"


def test_set_status_running_starts_the_milestone(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)
    assert run("set-status", str(path), "M1-S01", "running",
               "--repo-root", str(fixture_repo)) == 0
    assert json.loads(path.read_text())["milestones"][0]["status"] == "building"


def test_set_status_running_refused_before_the_gates(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    before = path.read_bytes()
    assert run("set-status", str(path), "M1-S01", "running",
               "--repo-root", str(fixture_repo)) == 1
    assert path.read_bytes() == before


def test_set_status_running_refused_in_a_later_milestone(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1"), step("M2-S01", "M2")])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)
    # M2 is not the runnable milestone: milestone:M1 has not been accepted.
    assert run("set-status", str(path), "M2-S01", "running",
               "--repo-root", str(fixture_repo)) == 1
    assert run("set-status", str(path), "M1-S01", "running",
               "--repo-root", str(fixture_repo)) == 0


# --------------------------------------------------------------------------
# outputs and test results gate the 'built' and 'tested' statuses (D5)
# --------------------------------------------------------------------------

def test_check_outputs_reports_missing_empty_and_malformed(tmp_path, fixture_repo, capsys):
    plan = plan_dict([step("M1-S01", "M1", outputs=[
        "artefacts/M1-S01/Case.object-meta.xml",
        "artefacts/M1-S01/notes.md",
        "artefacts/M1-S01/Queue.queue-meta.xml",
    ])])
    path = write_plan_file(tmp_path / "b", plan)

    assert run("check-outputs", str(path), "M1-S01", "--repo-root", str(fixture_repo)) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["ok"] is False
    assert sorted(report["missing"]) == ["artefacts/M1-S01/Case.object-meta.xml",
                                         "artefacts/M1-S01/Queue.queue-meta.xml",
                                         "artefacts/M1-S01/notes.md"]

    (path.parent / "artefacts" / "M1-S01").mkdir(parents=True, exist_ok=True)
    (path.parent / "artefacts/M1-S01/Case.object-meta.xml").write_text(
        "<CustomObject/>\n", encoding="utf-8")
    (path.parent / "artefacts/M1-S01/notes.md").write_text("   \n", encoding="utf-8")
    (path.parent / "artefacts/M1-S01/Queue.queue-meta.xml").write_text(
        "<Queue><name>Tier 1\n", encoding="utf-8")

    assert run("check-outputs", str(path), "M1-S01", "--repo-root", str(fixture_repo)) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["missing"] == []
    assert report["empty"] == ["artefacts/M1-S01/notes.md"]
    assert len(report["malformed"]) == 1
    assert report["malformed"][0].startswith("artefacts/M1-S01/Queue.queue-meta.xml:")

    (path.parent / "artefacts/M1-S01/notes.md").write_text("field list\n", encoding="utf-8")
    (path.parent / "artefacts/M1-S01/Queue.queue-meta.xml").write_text(
        "<Queue><name>Tier 1</name></Queue>\n", encoding="utf-8")
    assert run("check-outputs", str(path), "M1-S01", "--repo-root", str(fixture_repo)) == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True


def test_built_is_refused_until_the_outputs_exist(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)
    assert run("set-status", str(path), "M1-S01", "running",
               "--repo-root", str(fixture_repo)) == 0
    assert run("set-status", str(path), "M1-S01", "built",
               "--repo-root", str(fixture_repo)) == 1, "a runner that wrote nothing cannot advance"
    assert json.loads(path.read_text())["steps"][0]["status"] == "running"
    write_outputs(path, "M1-S01")
    assert run("set-status", str(path), "M1-S01", "built",
               "--repo-root", str(fixture_repo)) == 0


def test_tested_needs_a_passing_results_json(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)
    advance(path, fixture_repo, "M1-S01", upto="built")

    assert run("set-status", str(path), "M1-S01", "tested",
               "--repo-root", str(fixture_repo)) == 1, "no results.json"
    write_results(path, "M1-S01", passed=False)
    assert run("set-status", str(path), "M1-S01", "tested",
               "--repo-root", str(fixture_repo)) == 1, "failing results.json"
    write_results(path, "M1-S01", passed=True)
    assert run("set-status", str(path), "M1-S01", "tested",
               "--repo-root", str(fixture_repo)) == 0


def test_tested_accepts_matching_artefact_hashes(tmp_path, fixture_repo, capsys):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)
    advance(path, fixture_repo, "M1-S01", upto="built")
    capsys.readouterr()
    assert run("check-outputs", str(path), "M1-S01", "--hashes",
               "--repo-root", str(fixture_repo)) == 0
    hashes = json.loads(capsys.readouterr().out)
    assert set(hashes) == set(json.loads(path.read_text())["steps"][0]["outputs"])
    for digest in hashes.values():
        assert isinstance(digest, str) and len(digest) == 64
        assert all(c in "0123456789abcdef" for c in digest)
    write_json(path.parent / "tests" / "M1-S01" / "results.json",
               {"step": "M1-S01", "passed": True, "artefact_hashes": hashes})
    assert run("set-status", str(path), "M1-S01", "tested",
               "--repo-root", str(fixture_repo)) == 0
    assert json.loads(path.read_text())["steps"][0]["status"] == "tested"


def test_tested_refuses_stale_artefact_hashes(tmp_path, fixture_repo, capsys):
    plan = plan_dict([step("M1-S01", "M1", outputs=[
        "artefacts/M1-S01/Case.object-meta.xml",
        "artefacts/M1-S01/notes.md",
    ])])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)
    advance(path, fixture_repo, "M1-S01", upto="built")
    step_body = json.loads(path.read_text())["steps"][0]
    out_rel = "artefacts/M1-S01/notes.md"
    hashes = build_plan.artefact_hashes_for_step(path.parent, step_body)
    write_json(path.parent / "tests" / "M1-S01" / "results.json",
               {"step": "M1-S01", "passed": True, "artefact_hashes": hashes})
    # Keep the file non-empty and valid so check-outputs still passes; only the digest drifts.
    (path.parent / out_rel).write_bytes((path.parent / out_rel).read_bytes() + b"x")
    before = path.read_text()
    assert run("set-status", str(path), "M1-S01", "tested",
               "--repo-root", str(fixture_repo)) == 1
    err = capsys.readouterr().err
    assert f"ERROR step M1-S01: results.json was written against different artefacts — " \
           f"1 output(s) changed since the tester ran (first: {out_rel}); " \
           f"re-run the tester (§ 5)." in err
    assert path.read_text() == before
    assert json.loads(before)["steps"][0]["status"] == "built"


def test_tested_accepts_results_without_artefact_hashes(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)
    advance(path, fixture_repo, "M1-S01", upto="built")
    write_results(path, "M1-S01", passed=True)
    assert run("set-status", str(path), "M1-S01", "tested",
               "--repo-root", str(fixture_repo)) == 0


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

    open_gates(path, fixture_repo)
    capsys.readouterr()

    assert run("next", str(path), "--repo-root", str(fixture_repo)) == 0
    runnable = json.loads(capsys.readouterr().out)
    assert [s["id"] for s in runnable] == ["M1-S01"], "M1-S02 waits on its dependency"

    advance(path, fixture_repo, "M1-S01")
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


def test_next_skips_a_blocked_only_milestone_once_its_gate_is_approved(
        tmp_path, fixture_repo, capsys):
    """A milestone whose only undocumented step is `blocked` (recorded, with a
    reason) and whose own `milestone:<id>` gate a human already approved is
    not "next" — it is done being actionable. `next` must move on to the
    following milestone rather than reporting `[]` forever."""
    plan = plan_dict([
        step("M1-S01", "M1", status="blocked", blocked_reason="skill-gap"),
        step("M2-S01", "M2"),
    ])
    plan["human_gates"] = [
        {"name": "clarifications", "status": "approved", "by": "p", "at": "2026-09-05T09:00:00Z"},
        {"name": "plan", "status": "approved", "by": "p", "at": "2026-09-05T09:00:00Z"},
        {"name": "milestone:M1", "status": "approved", "by": "p", "at": "2026-09-05T09:00:00Z"},
        {"name": "milestone:M2", "status": "pending"},
    ]
    path = write_plan_file(tmp_path / "b", plan)

    assert run("next", str(path), "--repo-root", str(fixture_repo)) == 0
    captured = capsys.readouterr()
    assert [s["id"] for s in json.loads(captured.out)] == ["M2-S01"]
    assert ("reason: milestone M1 skipped — its gate is approved and its only "
            "undocumented step(s) are blocked (M1-S01)") in captured.err


def test_next_still_reports_no_pending_steps_when_the_blocked_milestones_gate_is_open(
        tmp_path, fixture_repo, capsys):
    """Same blocked-only shape, but the milestone gate is still pending — the
    old, unhelpful-but-correct message stands: nothing is skipped."""
    plan = plan_dict([step("M1-S01", "M1", status="blocked", blocked_reason="skill-gap")])
    plan["human_gates"] = [
        {"name": "clarifications", "status": "approved", "by": "p", "at": "2026-09-05T09:00:00Z"},
        {"name": "plan", "status": "approved", "by": "p", "at": "2026-09-05T09:00:00Z"},
        {"name": "milestone:M1", "status": "pending"},
    ]
    path = write_plan_file(tmp_path / "b", plan)

    assert run("next", str(path), "--repo-root", str(fixture_repo)) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == []
    assert "reason: no pending steps in M1" in captured.err
    assert "skipped" not in captured.err


def test_next_does_not_skip_a_milestone_with_a_genuinely_pending_step(
        tmp_path, fixture_repo, capsys):
    """A milestone still carrying an ordinary pending step is never skipped,
    even if its gate happens to already be approved — only all-blocked
    milestones are eligible to be passed over."""
    plan = plan_dict([
        step("M1-S01", "M1", status="pending"),
        step("M2-S01", "M2"),
    ])
    plan["human_gates"] = [
        {"name": "clarifications", "status": "approved", "by": "p", "at": "2026-09-05T09:00:00Z"},
        {"name": "plan", "status": "approved", "by": "p", "at": "2026-09-05T09:00:00Z"},
        {"name": "milestone:M1", "status": "approved", "by": "p", "at": "2026-09-05T09:00:00Z"},
        {"name": "milestone:M2", "status": "pending"},
    ]
    path = write_plan_file(tmp_path / "b", plan)

    assert run("next", str(path), "--repo-root", str(fixture_repo)) == 0
    captured = capsys.readouterr()
    assert [s["id"] for s in json.loads(captured.out)] == ["M1-S01"]
    assert "skipped" not in captured.err


def test_gate_flow_end_to_end(tmp_path, fixture_repo, capsys):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)

    assert run("gate", str(path), "clarifications", "approve", "--by", "pranav",
               "--notes", "defaults accepted", "--at", "2026-09-05T10:00:00Z",
               "--repo-root", str(fixture_repo)) == 0
    body = write_json(tmp_path / "verification.json",
                      {"lenses": [{"lens": "grounding", "verdict": "pass"}]})
    assert run("set-verification", str(path), "--file", str(body), "--outcome", "verified",
               "--at", "2026-09-05T10:02:00Z", "--repo-root", str(fixture_repo)) == 0
    assert run("gate", str(path), "plan", "approve", "--by", "pranav",
               "--at", "2026-09-05T10:05:00Z", "--repo-root", str(fixture_repo)) == 0
    assert json.loads(path.read_text())["status"] == "approved"

    advance(path, fixture_repo, "M1-S01")

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


def test_gate_history_approve_reject_approve(tmp_path, fixture_repo):
    """Re-deciding a gate archives each prior state into history[], oldest first."""
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)

    assert run("gate", str(path), "clarifications", "approve", "--by", "alice",
               "--notes", "first yes", "--at", "2026-09-05T10:00:00Z",
               "--repo-root", str(fixture_repo)) == 0
    assert run("gate", str(path), "clarifications", "reject", "--by", "bob",
               "--notes", "changed mind", "--at", "2026-09-05T10:10:00Z",
               "--repo-root", str(fixture_repo)) == 0
    assert run("gate", str(path), "clarifications", "approve", "--by", "carol",
               "--notes", "final yes", "--at", "2026-09-05T10:20:00Z",
               "--repo-root", str(fixture_repo)) == 0

    gate = next(g for g in json.loads(path.read_text())["human_gates"]
                if g["name"] == "clarifications")
    assert gate["status"] == "approved"
    assert gate["by"] == "carol"
    assert gate["at"] == "2026-09-05T10:20:00Z"
    assert gate["notes"] == "final yes"
    assert [h["status"] for h in gate["history"]] == ["approved", "rejected"]
    assert gate["history"][0] == {"status": "approved", "by": "alice",
                                  "at": "2026-09-05T10:00:00Z", "notes": "first yes"}
    assert gate["history"][1] == {"status": "rejected", "by": "bob",
                                  "at": "2026-09-05T10:10:00Z", "notes": "changed mind"}
    assert all("history" not in h for h in gate["history"])


def test_gate_resign_on_done_build(tmp_path, fixture_repo):
    """resign keeps approved + build done; only history/by/at/notes move."""
    plan = plan_dict([step("M1-S01", "M1", status="documented")])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)
    assert run("gate", str(path), "milestone:M1", "approve", "--by", "alice",
               "--notes", "original acceptance", "--at", "2026-09-05T13:00:00Z",
               "--repo-root", str(fixture_repo)) == 0
    assert json.loads(path.read_text())["status"] == "done"

    assert run("gate", str(path), "milestone:M1", "resign", "--by", "codex",
               "--notes", "re-verified after repair", "--at", "2026-09-05T14:00:00Z",
               "--repo-root", str(fixture_repo)) == 0

    after = json.loads(path.read_text())
    assert after["status"] == "done"
    assert after["milestones"][0]["status"] == "accepted"
    gate = next(g for g in after["human_gates"] if g["name"] == "milestone:M1")
    assert gate["status"] == "approved"
    assert gate["by"] == "codex"
    assert gate["at"] == "2026-09-05T14:00:00Z"
    assert gate["notes"] == "re-verified after repair"
    assert len(gate["history"]) == 1
    assert gate["history"][0] == {"status": "approved", "by": "alice",
                                  "at": "2026-09-05T13:00:00Z",
                                  "notes": "original acceptance"}


def test_gate_resign_refused_when_not_approved(tmp_path, fixture_repo, capsys):
    """resign on a pending gate exits 1 and leaves the plan file untouched."""
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    before = path.read_bytes()

    assert run("gate", str(path), "milestone:M1", "resign", "--by", "codex",
               "--notes", "should not land", "--repo-root", str(fixture_repo)) == 1
    assert path.read_bytes() == before
    err = capsys.readouterr().err
    assert "gate 'milestone:M1' is 'pending', not 'approved'" in err
    assert "resign records new evidence for a standing approval" in err
    assert "use approve/reject to change the decision" in err


def test_gate_history_plan_still_validates(tmp_path, fixture_repo):
    """A plan whose gates carry history[] still passes validate."""
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    assert run("gate", str(path), "clarifications", "approve", "--by", "alice",
               "--notes", "first yes", "--at", "2026-09-05T10:00:00Z",
               "--repo-root", str(fixture_repo)) == 0
    assert run("gate", str(path), "clarifications", "reject", "--by", "bob",
               "--notes", "changed mind", "--at", "2026-09-05T10:10:00Z",
               "--repo-root", str(fixture_repo)) == 0
    assert run("gate", str(path), "clarifications", "approve", "--by", "carol",
               "--notes", "final yes", "--at", "2026-09-05T10:20:00Z",
               "--repo-root", str(fixture_repo)) == 0

    assert run("validate", str(path), "--repo-root", str(fixture_repo)) == 0


def test_middle_milestone_gate_sets_building_not_done(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1", status="documented"), step("M2-S01", "M2")])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)
    assert run("gate", str(path), "milestone:M1", "approve", "--by", "pranav",
               "--at", "2026-09-05T13:00:00Z", "--repo-root", str(fixture_repo)) == 0
    assert json.loads(path.read_text())["status"] == "building"


def test_plan_gate_rejection_archives_without_bumping(tmp_path, fixture_repo):
    """Contract § 3: archiving happens at the rejection, bumping at the re-plan.

    A plan rejected and then abandoned must not leave a v2 behind that no
    planner ever wrote — `set-plan` mints the new version, this does not.
    """
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    assert run("gate", str(path), "plan", "reject", "--by", "pranav",
               "--notes", "milestone 1 has no access step",
               "--at", "2026-09-05T10:30:00Z", "--repo-root", str(fixture_repo)) == 0
    after = json.loads(path.read_text())
    assert after["status"] == "plan-rejected"
    assert after["version"] == 1, "the rejection archives; the re-plan bumps"
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
    assert after["milestones"][0]["status"] == "rejected"
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
# gate integrity (D3) — a gate is a signature on a claim that must be true
# --------------------------------------------------------------------------

def test_plan_gate_approval_refused_until_verified(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    assert run("gate", str(path), "clarifications", "approve", "--by", "pranav",
               "--at", "2026-09-05T09:00:00Z", "--repo-root", str(fixture_repo)) == 0
    before = path.read_bytes()
    assert run("gate", str(path), "plan", "approve", "--by", "pranav",
               "--at", "2026-09-05T09:10:00Z", "--repo-root", str(fixture_repo)) == 1
    assert path.read_bytes() == before, "a refused gate writes nothing"

    body = write_json(tmp_path / "verification.json",
                      {"lenses": [{"lens": "testability", "verdict": "pass"}]})
    assert run("set-verification", str(path), "--file", str(body), "--outcome", "verified",
               "--at", "2026-09-05T09:20:00Z", "--repo-root", str(fixture_repo)) == 0
    assert run("gate", str(path), "plan", "approve", "--by", "pranav",
               "--at", "2026-09-05T09:30:00Z", "--repo-root", str(fixture_repo)) == 0
    assert json.loads(path.read_text())["status"] == "approved"


def test_clarifications_gate_refused_while_a_blocking_question_is_open(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")], clarifications=[
        {"id": "Q1", "question": "Which queue owns unrouted email?", "kind": "blocking",
         "status": "open"},
        {"id": "Q2", "question": "Business hours?", "kind": "informational", "status": "open"},
    ])
    path = write_plan_file(tmp_path / "b", plan)
    assert run("gate", str(path), "clarifications", "approve", "--by", "pranav",
               "--at", "2026-09-05T09:00:00Z", "--repo-root", str(fixture_repo)) == 1

    plan["clarifications"][0].update(status="deferred", answer="DEFER: legal is still reviewing")
    path = write_plan_file(tmp_path / "b", plan)
    assert run("gate", str(path), "clarifications", "approve", "--by", "pranav",
               "--at", "2026-09-05T09:00:00Z", "--repo-root", str(fixture_repo)) == 0


def test_milestone_gate_refused_out_of_order(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1", status="documented"),
                      step("M2-S01", "M2", status="documented")])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)
    before = path.read_bytes()
    assert run("gate", str(path), "milestone:M2", "approve", "--by", "pranav",
               "--at", "2026-09-05T13:00:00Z", "--repo-root", str(fixture_repo)) == 1
    assert path.read_bytes() == before
    assert run("gate", str(path), "milestone:M1", "approve", "--by", "pranav",
               "--at", "2026-09-05T13:10:00Z", "--repo-root", str(fixture_repo)) == 0
    assert run("gate", str(path), "milestone:M2", "approve", "--by", "pranav",
               "--at", "2026-09-05T13:20:00Z", "--repo-root", str(fixture_repo)) == 0
    assert json.loads(path.read_text())["status"] == "done"


def test_milestone_gate_refused_while_a_step_is_unfinished(tmp_path, fixture_repo, capsys):
    plan = plan_dict([step("M1-S01", "M1", status="documented"),
                      step("M1-S02", "M1", status="pending")])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)
    assert run("gate", str(path), "milestone:M1", "approve", "--by", "pranav",
               "--at", "2026-09-05T13:00:00Z", "--repo-root", str(fixture_repo)) == 1

    # A step blocked with a recorded reason is an accepted way to close a
    # milestone — the human sees it printed before they sign.
    on_disk = json.loads(path.read_text())
    on_disk["steps"][1].update(status="blocked",
                               blocked_reason="skill-gap: no Email-to-Case skill")
    write_json(path, on_disk)
    capsys.readouterr()
    assert run("gate", str(path), "milestone:M1", "approve", "--by", "pranav",
               "--at", "2026-09-05T13:00:00Z", "--repo-root", str(fixture_repo)) == 0
    assert "blocked (recorded): M1-S02" in capsys.readouterr().out


def test_reject_is_recorded_even_when_the_plan_is_invalid(tmp_path, fixture_repo):
    """A human rejects a plan *because* it is broken; refusing to record that traps the build."""
    plan = plan_dict([step("M1-S01", "M1", agent="gamma-legacy")])
    path = write_plan_file(tmp_path / "b", plan)
    assert run("validate", str(path), "--repo-root", str(fixture_repo)) == 1

    assert run("gate", str(path), "plan", "reject", "--by", "pranav",
               "--notes", "owned by a deprecated agent",
               "--at", "2026-09-05T10:30:00Z", "--repo-root", str(fixture_repo)) == 0
    after = json.loads(path.read_text())
    assert after["status"] == "plan-rejected"
    assert after["version"] == 1, "rejection archives without bumping"
    assert len(after["history"]) == 1

    assert run("gate", str(path), "clarifications", "reject", "--by", "pranav",
               "--at", "2026-09-05T10:40:00Z", "--repo-root", str(fixture_repo)) == 0
    assert json.loads(path.read_text())["status"] == "clarifying"

    # An *approval* still gets the full check, and an off-schema result never lands.
    plan["milestones"] = "not a list"
    bad = write_plan_file(tmp_path / "bad", plan)
    before = bad.read_bytes()
    assert run("gate", str(bad), "plan", "reject", "--by", "pranav",
               "--repo-root", str(fixture_repo)) == 1
    assert bad.read_bytes() == before


# --------------------------------------------------------------------------
# step-level human gates (D2)
# --------------------------------------------------------------------------

def test_step_gate_is_required_and_blocks_next_and_running(tmp_path, fixture_repo, capsys):
    plan = plan_dict([step("M1-S01", "M1", human_gate=True),
                      step("M1-S02", "M1", agent="beta-flow-builder", stype="automation",
                           skills=("flow/fake-flow-patterns",))])
    path = write_plan_file(tmp_path / "b", plan)

    # validate demands the step:<id> gate record; ensure-gates adds it pending.
    assert run("validate", str(path), "--repo-root", str(fixture_repo)) == 1
    assert "step:M1-S01" in capsys.readouterr().out
    assert run("ensure-gates", str(path), "--repo-root", str(fixture_repo)) == 0
    names = [g["name"] for g in json.loads(path.read_text())["human_gates"]]
    assert names == ["clarifications", "plan", "step:M1-S01", "milestone:M1"]
    assert run("validate", str(path), "--repo-root", str(fixture_repo)) == 0

    open_gates(path, fixture_repo)
    capsys.readouterr()
    assert run("next", str(path), "--repo-root", str(fixture_repo)) == 0
    captured = capsys.readouterr()
    assert [s["id"] for s in json.loads(captured.out)] == ["M1-S02"], "M1-S01 waits for its gate"
    assert "step:M1-S01" in captured.err

    assert run("set-status", str(path), "M1-S01", "running",
               "--repo-root", str(fixture_repo)) == 1
    assert run("gate", str(path), "step:M1-S01", "approve", "--by", "pranav",
               "--at", "2026-09-05T11:00:00Z", "--repo-root", str(fixture_repo)) == 0
    capsys.readouterr()
    assert run("next", str(path), "--repo-root", str(fixture_repo)) == 0
    assert [s["id"] for s in json.loads(capsys.readouterr().out)] == ["M1-S01", "M1-S02"]
    assert run("set-status", str(path), "M1-S01", "running",
               "--repo-root", str(fixture_repo)) == 0


# --------------------------------------------------------------------------
# structured writers — no agent hand-edits plan.json (D7)
# --------------------------------------------------------------------------

def test_set_clarifications_round_trip(tmp_path, fixture_repo, requirement, capsys):
    build_dir = tmp_path / "case-onboarding"
    assert run("init", "--build-dir", str(build_dir), "--title", "Case intake onboarding",
               "--requirement", str(requirement), "--repo-root", str(fixture_repo),
               "--now", "2026-09-05T09:00:00Z") == 0
    path = build_dir / "plan.json"
    body = write_json(tmp_path / "questions.json", [
        {"id": "Q1", "question": "Which queue owns unrouted email?", "kind": "blocking",
         "proposed_default": "Tier 1 Support", "status": "open",
         "source_skill": "admin/fake-object-design"},
    ])
    capsys.readouterr()
    assert run("set-clarifications", str(path), "--file", str(body),
               "--repo-root", str(fixture_repo)) == 0
    after = json.loads(path.read_text())
    assert after["status"] == "clarifying"
    assert [c["id"] for c in after["clarifications"]] == ["Q1"]

    # A non-array file is refused and nothing is written.
    before = path.read_bytes()
    junk = write_json(tmp_path / "junk.json", {"nope": True})
    assert run("set-clarifications", str(path), "--file", str(junk),
               "--repo-root", str(fixture_repo)) == 1
    assert path.read_bytes() == before


def test_set_plan_writes_the_planner_fields_and_the_gates(tmp_path, fixture_repo, requirement,
                                                          capsys):
    build_dir = tmp_path / "case-onboarding"
    assert run("init", "--build-dir", str(build_dir), "--title", "Case intake onboarding",
               "--requirement", str(requirement), "--repo-root", str(fixture_repo),
               "--now", "2026-09-05T09:00:00Z") == 0
    path = build_dir / "plan.json"
    steps = [step("M1-S01", "M1"), step("M1-S02", "M1", human_gate=True,
                                        depends_on=["M1-S01"])]
    body = write_json(tmp_path / "plan-body.json", {
        "scope": {"in": ["Case"], "out": ["CTI"], "fit_gap": []},
        "fit_gap": [{"requirement": "SLA clock", "verdict": "fit"}],
        "decisions": [{"id": "D1", "decision": "Flow, not Apex"}],
        "milestones": [{"id": "M1", "title": "Intake", "steps": ["M1-S01", "M1-S02"],
                        "acceptance_tests": [{"type": "manifest",
                                              "description": "package.xml consistent"}]}],
        "steps": steps,
    })
    capsys.readouterr()
    assert run("set-plan", str(path), "--file", str(body),
               "--repo-root", str(fixture_repo)) == 0
    after = json.loads(path.read_text())
    assert after["status"] == "planned"
    assert after["scope"]["fit_gap"] == [{"requirement": "SLA clock", "verdict": "fit"}], \
        "top-level fit_gap is merged into scope"
    assert [g["name"] for g in after["human_gates"]] == [
        "clarifications", "plan", "step:M1-S02", "milestone:M1"]
    assert run("validate", str(path), "--repo-root", str(fixture_repo)) == 0

    # Unknown keys belong to another writer.
    junk = write_json(tmp_path / "junk.json", {"human_gates": []})
    before = path.read_bytes()
    assert run("set-plan", str(path), "--file", str(junk),
               "--repo-root", str(fixture_repo)) == 1
    assert path.read_bytes() == before


def test_set_plan_refused_once_the_plan_is_signed_off(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)  # status -> approved
    body = write_json(tmp_path / "plan-body.json", {"decisions": []})
    before = path.read_bytes()
    assert run("set-plan", str(path), "--file", str(body),
               "--repo-root", str(fixture_repo)) == 1
    assert path.read_bytes() == before

    # Rejecting the plan gate reopens re-planning.
    assert run("gate", str(path), "plan", "reject", "--by", "pranav",
               "--at", "2026-09-05T14:00:00Z", "--repo-root", str(fixture_repo)) == 0
    assert json.loads(path.read_text())["status"] == "plan-rejected"
    assert run("set-plan", str(path), "--file", str(body),
               "--repo-root", str(fixture_repo)) == 0
    assert json.loads(path.read_text())["status"] == "planned"


def test_amend_step_replaces_declared_fields_and_records_before(tmp_path, fixture_repo, capsys):
    """A pending step's fields get corrected mid-build without a re-plan.

    Two milestones, M1 fully documented and gated (approving a non-last
    milestone puts the build status at 'building' — see
    test_middle_milestone_gate_sets_building_not_done), M2-S01 still pending.
    That is exactly the window set-plan refuses and amend-step exists for.
    """
    plan = plan_dict([step("M1-S01", "M1", status="documented"), step("M2-S01", "M2")])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)
    assert run("gate", str(path), "milestone:M1", "approve", "--by", "pranav",
               "--at", "2026-09-05T13:00:00Z", "--repo-root", str(fixture_repo)) == 0
    before_doc = json.loads(path.read_text())
    assert before_doc["status"] == "building"
    original_outputs = before_doc["steps"][1]["outputs"]
    assert before_doc["steps"][1]["id"] == "M2-S01"

    amendment = write_json(tmp_path / "amend-outputs.json", {
        "outputs": original_outputs + ["artefacts/M2-S01/deploy-order.md"],
    })
    capsys.readouterr()
    rc = run("amend-step", str(path), "M2-S01", "--file", str(amendment),
             "--by", "pranav", "--reason", "deploy order note was missing",
             "--at", "2026-09-05T14:00:00Z", "--repo-root", str(fixture_repo))
    out = capsys.readouterr().out
    assert rc == 0
    assert "M2-S01: amended outputs by pranav" in out
    assert "next:" in out

    after = json.loads(path.read_text())
    m2 = next(s for s in after["steps"] if s["id"] == "M2-S01")
    assert m2["outputs"] == original_outputs + ["artefacts/M2-S01/deploy-order.md"]
    assert len(m2["amendments"]) == 1
    record = m2["amendments"][0]
    assert record["by"] == "pranav"
    assert record["reason"] == "deploy order note was missing"
    assert record["at"] == "2026-09-05T14:00:00Z"
    assert record["fields"] == ["outputs"]
    assert record["before"] == {"outputs": original_outputs}
    # amend-step never touches gates, status or runs
    assert m2["status"] == "pending"
    assert m2["runs"] == []
    assert after["human_gates"] == before_doc["human_gates"]


def test_amend_step_refused_on_documented_step(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)  # status -> approved
    advance(path, fixture_repo, "M1-S01", upto="documented")
    before = path.read_bytes()

    amendment = write_json(tmp_path / "amend.json", {"notes": "tweak"})
    rc = run("amend-step", str(path), "M1-S01", "--file", str(amendment),
             "--by", "pranav", "--reason", "late fix", "--repo-root", str(fixture_repo))
    assert rc == 1
    assert path.read_bytes() == before


def test_amend_step_refused_when_step_gate_already_approved(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1", human_gate=True)])
    path = write_plan_file(tmp_path / "b", plan)
    assert run("ensure-gates", str(path), "--repo-root", str(fixture_repo)) == 0
    open_gates(path, fixture_repo)  # status -> approved
    assert run("gate", str(path), "step:M1-S01", "approve", "--by", "pranav",
               "--at", "2026-09-05T12:00:00Z", "--repo-root", str(fixture_repo)) == 0
    before = path.read_bytes()

    amendment = write_json(tmp_path / "amend.json", {"notes": "tweak"})
    rc = run("amend-step", str(path), "M1-S01", "--file", str(amendment),
             "--by", "pranav", "--reason", "late fix", "--repo-root", str(fixture_repo))
    assert rc == 1
    assert path.read_bytes() == before


def test_amend_step_refused_on_unknown_field(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)  # status -> approved
    before = path.read_bytes()

    amendment = write_json(tmp_path / "amend.json", {"status": "documented"})
    rc = run("amend-step", str(path), "M1-S01", "--file", str(amendment),
             "--by", "pranav", "--reason", "sneaky", "--repo-root", str(fixture_repo))
    assert rc == 1
    assert path.read_bytes() == before


def test_amend_step_refused_when_result_is_invalid(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)  # status -> approved
    before = path.read_bytes()

    amendment = write_json(tmp_path / "amend.json", {
        "acceptance_tests": [{"type": "bogus"}],
    })
    rc = run("amend-step", str(path), "M1-S01", "--file", str(amendment),
             "--by", "pranav", "--reason", "bad type", "--repo-root", str(fixture_repo))
    assert rc == 1
    assert path.read_bytes() == before, "a refused amendment must leave the file untouched"


def _write_fake_checker(fixture_repo: Path) -> str:
    """Create a real skill-local checker script so a 'checker' test passes
    the "command must name an existing checker" semantic gate, and return
    its canonical command string.
    """
    checker = fixture_repo / "skills" / "admin" / "fake-object-design" / "scripts" / "check_fields.py"
    checker.parent.mkdir(parents=True, exist_ok=True)
    checker.write_text("print('ok')\n", encoding="utf-8")
    rel = checker.relative_to(fixture_repo)
    return f"python3 {rel} --manifest-dir artefacts/M1-S01"


def test_amend_step_prose_only_on_documented_step_succeeds(tmp_path, fixture_repo, capsys):
    """A stale test description on an already-`documented` step gets corrected
    without a rebuild, and the amendment records `prose_only: true`.
    """
    command = _write_fake_checker(fixture_repo)
    plan = plan_dict([step("M1-S01", "M1", tests=[
        {"type": "checker", "command": command,
         "expected": "exit 0", "scope": "step",
         "description": "Scanned 14 metadata file(s)"},
    ])])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)  # status -> approved
    advance(path, fixture_repo, "M1-S01", upto="documented")
    before_doc = json.loads(path.read_text())
    assert before_doc["steps"][0]["status"] == "documented"
    current_tests = before_doc["steps"][0]["acceptance_tests"]

    fixed_tests = copy.deepcopy(current_tests)
    fixed_tests[0]["description"] = "Scanned 15 metadata file(s)"
    amendment = write_json(tmp_path / "amend-prose.json", {"acceptance_tests": fixed_tests})

    capsys.readouterr()
    rc = run("amend-step", str(path), "M1-S01", "--file", str(amendment), "--prose-only",
             "--by", "dry-run operator (Fable)", "--reason", "O-M1S01-01",
             "--at", "2026-09-11T10:00:00Z", "--repo-root", str(fixture_repo))
    out = capsys.readouterr().out
    assert rc == 0
    assert "M1-S01: amended acceptance_tests by dry-run operator (Fable) (prose-only)" in out

    after = json.loads(path.read_text())
    s1 = after["steps"][0]
    assert s1["status"] == "documented", "prose-only never touches status"
    assert s1["acceptance_tests"][0]["description"] == "Scanned 15 metadata file(s)"
    assert s1["acceptance_tests"][0]["command"] == current_tests[0]["command"]
    assert len(s1["amendments"]) == 1
    record = s1["amendments"][0]
    assert record["prose_only"] is True
    assert record["reason"] == "O-M1S01-01"
    assert record["fields"] == ["acceptance_tests"]
    assert record["before"] == {"acceptance_tests": current_tests}


def test_amend_step_prose_only_refused_when_command_differs(tmp_path, fixture_repo):
    command = _write_fake_checker(fixture_repo)
    plan = plan_dict([step("M1-S01", "M1", tests=[
        {"type": "checker", "command": command,
         "expected": "exit 0", "scope": "step", "description": "old description"},
    ])])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)  # status -> approved
    advance(path, fixture_repo, "M1-S01", upto="documented")
    before = path.read_bytes()

    current_tests = json.loads(before)["steps"][0]["acceptance_tests"]
    changed = copy.deepcopy(current_tests)
    changed[0]["description"] = "new description"
    changed[0]["command"] = changed[0]["command"] + " --extra-flag"
    amendment = write_json(tmp_path / "amend-prose.json", {"acceptance_tests": changed})

    rc = run("amend-step", str(path), "M1-S01", "--file", str(amendment), "--prose-only",
             "--by", "pranav", "--reason", "sneaking in a command change",
             "--repo-root", str(fixture_repo))
    assert rc == 1
    assert path.read_bytes() == before


def test_amend_step_prose_only_refused_when_test_count_differs(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1", tests=[
        {"type": "xml", "description": "every artefact parses"},
    ])])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)  # status -> approved
    advance(path, fixture_repo, "M1-S01", upto="documented")
    before = path.read_bytes()

    amendment = write_json(tmp_path / "amend-prose.json", {
        "acceptance_tests": [
            {"type": "xml", "description": "every artefact parses"},
            {"type": "manifest", "description": "extra test snuck in"},
        ],
    })
    rc = run("amend-step", str(path), "M1-S01", "--file", str(amendment), "--prose-only",
             "--by", "pranav", "--reason", "sneaking in an extra test",
             "--repo-root", str(fixture_repo))
    assert rc == 1
    assert path.read_bytes() == before


def test_amend_step_ordinary_mode_still_refuses_documented_step(tmp_path, fixture_repo):
    """--prose-only relaxes the status/gate gates; ordinary mode still does not."""
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    open_gates(path, fixture_repo)  # status -> approved
    advance(path, fixture_repo, "M1-S01", upto="documented")
    before = path.read_bytes()

    amendment = write_json(tmp_path / "amend.json", {"notes": "tweak"})
    rc = run("amend-step", str(path), "M1-S01", "--file", str(amendment),
             "--by", "pranav", "--reason", "late fix", "--repo-root", str(fixture_repo))
    assert rc == 1
    assert path.read_bytes() == before


def test_amend_step_allowed_at_planned_for_acceptance_tests_and_inputs(tmp_path, fixture_repo, capsys):
    """§ 3.1 / batch fix (a): a plan nobody has gated yet is a draft — the same

    reasoning `set-plan` already uses to allow a full rewrite at 'planned' and
    'plan-rejected' — so `amend-step` may correct `acceptance_tests` and
    `inputs` there without forcing a full re-plan round.
    """
    plan = plan_dict([step("M1-S01", "M1")])  # status: planned by default
    path = write_plan_file(tmp_path / "b", plan)
    before_doc = json.loads(path.read_text())
    assert before_doc["status"] == "planned"

    new_tests = [{"type": "xml", "description": "every artefact parses, corrected"}]
    amendment = write_json(tmp_path / "amend.json", {"acceptance_tests": new_tests})
    capsys.readouterr()
    rc = run("amend-step", str(path), "M1-S01", "--file", str(amendment),
             "--by", "pranav", "--reason", "checker argument fixed",
             "--at", "2026-09-05T10:00:00Z", "--repo-root", str(fixture_repo))
    out = capsys.readouterr().out
    assert rc == 0
    assert "M1-S01: amended acceptance_tests by pranav" in out

    after = json.loads(path.read_text())
    m1 = after["steps"][0]
    assert m1["acceptance_tests"] == new_tests
    assert m1["status"] == "pending"
    assert after["status"] == "planned"
    assert len(m1["amendments"]) == 1
    assert m1["amendments"][0]["fields"] == ["acceptance_tests"]

    new_inputs = {"object": "Case", "queue": "Tier 1 Support"}
    amendment2 = write_json(tmp_path / "amend2.json", {"inputs": new_inputs})
    rc2 = run("amend-step", str(path), "M1-S01", "--file", str(amendment2),
              "--by", "pranav", "--reason", "queue input added",
              "--at", "2026-09-05T10:05:00Z", "--repo-root", str(fixture_repo))
    assert rc2 == 0
    after2 = json.loads(path.read_text())
    assert after2["steps"][0]["inputs"] == new_inputs
    assert len(after2["steps"][0]["amendments"]) == 2


def test_amend_step_refused_at_planned_for_non_draft_fields(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])  # status: planned
    path = write_plan_file(tmp_path / "b", plan)
    before = path.read_bytes()

    amendment = write_json(tmp_path / "amend.json", {"notes": "tweak"})
    rc = run("amend-step", str(path), "M1-S01", "--file", str(amendment),
             "--by", "pranav", "--reason", "late fix", "--repo-root", str(fixture_repo))
    assert rc == 1
    assert path.read_bytes() == before


def test_amend_step_allowed_at_plan_rejected_for_acceptance_tests(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")], status="plan-rejected")
    path = write_plan_file(tmp_path / "b", plan)

    new_tests = [{"type": "xml", "description": "every artefact parses, corrected"}]
    amendment = write_json(tmp_path / "amend.json", {"acceptance_tests": new_tests})
    rc = run("amend-step", str(path), "M1-S01", "--file", str(amendment),
             "--by", "pranav", "--reason", "checker argument fixed",
             "--repo-root", str(fixture_repo))
    assert rc == 0
    after = json.loads(path.read_text())
    assert after["steps"][0]["acceptance_tests"] == new_tests
    assert after["status"] == "plan-rejected"


def test_amend_step_still_refused_at_verified_and_done(tmp_path, fixture_repo):
    """The draft allowance stops at 'planned'/'plan-rejected'. A verified plan

    has passed G2's lenses against its current tests/inputs, and a done build
    has no in-flight step left to correct — both stay refused exactly as
    'approved-with-an-approved-step-gate' already does.
    """
    for status in ("verified", "done"):
        plan = plan_dict([step("M1-S01", "M1")], status=status)
        path = write_plan_file(tmp_path / f"b-{status}", plan)
        before = path.read_bytes()
        amendment = write_json(tmp_path / f"amend-{status}.json",
                               {"acceptance_tests": [{"type": "xml", "description": "x"}]})
        rc = run("amend-step", str(path), "M1-S01", "--file", str(amendment),
                 "--by", "pranav", "--reason", "late fix", "--repo-root", str(fixture_repo))
        assert rc == 1, f"amend-step must still refuse at status {status!r}"
        assert path.read_bytes() == before


def test_set_verification_records_both_outcomes(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    body = write_json(tmp_path / "verification.json", {
        "lenses": [{"lens": "executability", "verdict": "fail",
                    "notes": "M1-S01 needs an org"}],
        "blockers": [{"step": "M1-S01", "problem": "owner requires an org", "lens":
                      "executability"}],
    })
    assert run("set-verification", str(path), "--file", str(body),
               "--outcome", "plan-rejected", "--by", "plan-verifier",
               "--at", "2026-09-05T09:50:00Z", "--repo-root", str(fixture_repo)) == 0
    after = json.loads(path.read_text())
    assert after["status"] == "plan-rejected"
    assert after["verification"]["status"] == "plan-rejected"
    assert after["verification"]["by"] == "plan-verifier"
    assert after["verification"]["verified_at"] == "2026-09-05T09:50:00Z"
    assert after["verification"]["blockers"][0]["step"] == "M1-S01"

    good = write_json(tmp_path / "verification-ok.json",
                      {"lenses": [{"lens": "executability", "verdict": "pass"}]})
    assert run("set-verification", str(path), "--file", str(good), "--outcome", "verified",
               "--at", "2026-09-05T10:00:00Z", "--repo-root", str(fixture_repo)) == 0
    assert json.loads(path.read_text())["status"] == "verified"


def test_set_verification_next_hint_is_scale_aware(tmp_path, fixture_repo, capsys):
    """standards/build-orchestration.md section 3.1: at `scale: ask` the plan
    gate is folded into the `go` alias (GATE_ALIASES), so the printed 'next'
    hint after a 'verified' outcome must name `go`, not the real `plan` gate a
    human can't legally call standalone at this scale. Absent scale keeps
    printing the real gate name unchanged (dry-run friction item 20)."""
    good = write_json(tmp_path / "verification-ok.json",
                      {"lenses": [{"lens": "executability", "verdict": "pass"}]})

    project_plan = plan_dict([step("M1-S01", "M1")])
    project_path = write_plan_file(tmp_path / "project", project_plan)
    capsys.readouterr()
    assert run("set-verification", str(project_path), "--file", str(good),
               "--outcome", "verified", "--repo-root", str(fixture_repo)) == 0
    out = capsys.readouterr().out
    assert f"gate {project_path} plan approve --by <who>" in out
    assert " go " not in out

    ask_plan = plan_dict([step("M1-S01", "M1")], scale="ask")
    ask_path = write_plan_file(tmp_path / "ask", ask_plan)
    capsys.readouterr()
    assert run("set-verification", str(ask_path), "--file", str(good),
               "--outcome", "verified", "--repo-root", str(fixture_repo)) == 0
    out = capsys.readouterr().out
    assert f"gate {ask_path} go approve --by <who>" in out
    assert "plan approve" not in out


def test_set_milestone_records_the_verifier_verdict(tmp_path, fixture_repo, capsys):
    plan = plan_dict([step("M1-S01", "M1", status="documented")])
    path = write_plan_file(tmp_path / "b", plan)
    report = path.parent / "reports" / "MILESTONE-M1-REPORT.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("# M1 acceptance\n", encoding="utf-8")

    assert run("set-milestone", str(path), "M1", "--status", "verified",
               "--report-path", "reports/MILESTONE-M1-REPORT.md",
               "--repo-root", str(fixture_repo)) == 0
    milestone = json.loads(path.read_text())["milestones"][0]
    assert milestone["status"] == "verified"
    assert milestone["report_path"] == "reports/MILESTONE-M1-REPORT.md"

    # A report path that is not on disk yet is a warning, not a refusal.
    capsys.readouterr()
    assert run("set-milestone", str(path), "M1", "--status", "rejected",
               "--report-path", "reports/MILESTONE-M1-REPORT-v2.md",
               "--repo-root", str(fixture_repo)) == 0
    assert "WARN report" in capsys.readouterr().out
    assert json.loads(path.read_text())["milestones"][0]["status"] == "rejected"

    assert run("set-milestone", str(path), "M9", "--status", "verified",
               "--report-path", "reports/x.md", "--repo-root", str(fixture_repo)) == 1


def test_set_milestone_next_hint_is_scale_aware(tmp_path, fixture_repo, capsys):
    """standards/build-orchestration.md section 3.1 / GATE_ALIASES: at
    `scale: ask` the M1 milestone gate is folded into the `accept` alias, so
    the printed 'next' hint after a 'verified' verdict must say `gate <plan>
    accept approve`, matching what RUN.md and the CLI actually accept — not
    the literal `milestone:M1 approve` the un-aliased gate name would suggest
    (dry-run friction item 20: this was the hint that used to be wrong)."""
    report = tmp_path / "b" / "reports" / "MILESTONE-M1-REPORT.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("# M1 acceptance\n", encoding="utf-8")

    project_plan = plan_dict([step("M1-S01", "M1", status="documented")])
    project_path = write_plan_file(tmp_path / "b", project_plan)
    capsys.readouterr()
    assert run("set-milestone", str(project_path), "M1", "--status", "verified",
               "--report-path", "reports/MILESTONE-M1-REPORT.md",
               "--repo-root", str(fixture_repo)) == 0
    out = capsys.readouterr().out
    assert f"gate {project_path} milestone:M1 approve --by <who>" in out
    assert "accept approve" not in out

    ask_plan = plan_dict([step("M1-S01", "M1", status="documented")], scale="ask")
    ask_path = write_plan_file(tmp_path / "ask-b", ask_plan)
    ask_report = ask_path.parent / "reports" / "MILESTONE-M1-REPORT.md"
    ask_report.parent.mkdir(parents=True, exist_ok=True)
    ask_report.write_text("# M1 acceptance\n", encoding="utf-8")
    capsys.readouterr()
    assert run("set-milestone", str(ask_path), "M1", "--status", "verified",
               "--report-path", "reports/MILESTONE-M1-REPORT.md",
               "--repo-root", str(fixture_repo)) == 0
    out = capsys.readouterr().out
    assert f"gate {ask_path} accept approve --by <who>" in out
    assert "milestone:M1 approve" not in out


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
    # Both real designers declare requires_org: true, so this plan is only
    # legal in an org-connected build — which is exactly the D1 rule, checked
    # against the roster as it actually is on disk.
    plan = plan_dict(steps, build_mode="org-connected", org={"alias": "uat-sandbox"})
    plan["decisions"][0]["decision_tree"] = REAL_TREE
    path = write_plan_file(tmp_path / "real", plan)
    assert run("validate", str(path), "--repo-root", str(REPO_ROOT)) == 0

    design_only = plan_dict(steps)
    design_only["decisions"][0]["decision_tree"] = REAL_TREE
    path_design = write_plan_file(tmp_path / "real-design-only", design_only)
    assert run("validate", str(path_design), "--repo-root", str(REPO_ROOT)) == 1

    # And the resolver must actually reject a deprecated real agent.
    plan["steps"][0]["agent"] = "picklist-governor"
    path2 = write_plan_file(tmp_path / "real-bad", plan)
    assert run("validate", str(path2), "--repo-root", str(REPO_ROOT)) == 1


# --------------------------------------------------------------------------
# grouped clarifications view (render + round-trip)
# --------------------------------------------------------------------------

def _grouped_plan(tmp_path: Path, fixture_repo: Path) -> Path:
    """Three groups, one of them absent — the shape a real clarifier emits."""
    plan = plan_dict([step("M1-S01", "M1")], clarifications=[
        {"id": "Q1", "question": "Which picklist values differ per record type?",
         "kind": "blocking", "status": "open", "group": "objects-and-fields",
         "owner_role": "Data steward",
         "answer_shape": "The picklistValues blocks per record type.",
         "proposed_default": "Two Case record types",
         "also_asked_by": ["flow/fake-flow-patterns"],
         "default_source": "skill-guidance"},
        {"id": "Q2", "question": "Which queue owns unrouted email?", "kind": "blocking",
         "status": "open", "group": "routing", "owner_role": "Support manager"},
        {"id": "Q3", "question": "Who signs off the layout?", "kind": "blocking",
         "status": "open"},
        {"id": "Q4", "question": "Which picklist is the default?", "kind": "blocking",
         "status": "open", "group": "objects-and-fields"},
        {"id": "Q5", "question": "Do we need a business-hours calendar?",
         "kind": "informational", "status": "open", "group": "sla",
         "answer_shape": "A BusinessHours name plus its timezone."},
    ])
    return write_plan_file(tmp_path / "b", plan)


def test_render_groups_questions_under_group_headings(tmp_path, fixture_repo):
    path = _grouped_plan(tmp_path, fixture_repo)
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    md = (path.parent / "CLARIFICATIONS.md").read_text(encoding="utf-8")

    # Group headings inside Blocking, first-appearance order, ungrouped last.
    blocking = md.split("## Blocking", 1)[1].split("## Informational", 1)[0]
    assert [line for line in blocking.splitlines() if line.startswith("### ")] == [
        "### objects-and-fields", "### routing", "### Other"]
    # Both members of the first group sit under it, in plan order.
    first_group = blocking.split("### objects-and-fields", 1)[1].split("### routing", 1)[0]
    assert "#### Q1" in first_group and "#### Q4" in first_group
    assert "#### Q2" not in first_group

    informational = md.split("## Informational", 1)[1]
    assert "### sla" in informational and "#### Q5" in informational

    # owner_role and answer_shape each render as one line, only when present.
    assert "**Who can answer:** Data steward" in md
    assert "**Answer shape:** The picklistValues blocks per record type." in md
    q2 = md.split("#### Q2", 1)[1].split("###", 1)[0]
    assert "**Who can answer:** Support manager" in q2
    assert "**Answer shape:**" not in q2

    # Still byte-deterministic.
    first = (path.parent / "CLARIFICATIONS.md").read_bytes()
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    assert (path.parent / "CLARIFICATIONS.md").read_bytes() == first


def test_grouped_view_still_round_trips(tmp_path, fixture_repo):
    """A `### <group>` heading between two questions must not eat an answer."""
    path = _grouped_plan(tmp_path, fixture_repo)
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    clar = path.parent / "CLARIFICATIONS.md"
    # Q4 is the last question before the `### routing` heading — the boundary case.
    set_answer(clar, "Q1", "Status and Reason")
    set_answer(clar, "Q4", "New\n- and Escalated")
    set_answer(clar, "Q2", "Tier 1 Support")
    set_answer(clar, "Q3", "The support manager")
    set_answer(clar, "Q5", "Yes — 9-5 Mon-Fri")

    assert run("ingest-answers", str(path), "--repo-root", str(fixture_repo)) == 0
    stored = {c["id"]: c for c in json.loads(path.read_text())["clarifications"]}
    assert stored["Q4"]["answer"] == "New\n- and Escalated"
    assert stored["Q2"]["answer"] == "Tier 1 Support", "the group heading swallowed an answer"
    assert stored["Q5"]["answer"] == "Yes — 9-5 Mon-Fri"
    assert all(c["status"] == "answered" for c in stored.values())

    # Render → ingest is a fixed point.
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    before = path.read_bytes()
    assert run("ingest-answers", str(path), "--repo-root", str(fixture_repo)) == 0
    assert path.read_bytes() == before


def test_render_reads_a_view_written_before_grouping(tmp_path, fixture_repo):
    """`### Q1` was the old heading shape; a stale view must still ingest."""
    path = _grouped_plan(tmp_path, fixture_repo)
    answers = build_plan.parse_clarification_answers(
        "## Blocking\n\n### Q1 — status: open\n\nAnswer: legacy heading\n")
    assert answers == {"Q1": "legacy heading"}


# --------------------------------------------------------------------------
# set-clarifications: one summary WARN, and --summary
# --------------------------------------------------------------------------

def _init_build(tmp_path: Path, fixture_repo: Path, requirement: Path) -> Path:
    build_dir = tmp_path / "case-onboarding"
    assert run("init", "--build-dir", str(build_dir), "--title", "Case intake onboarding",
               "--requirement", str(requirement), "--repo-root", str(fixture_repo),
               "--now", "2026-09-05T09:00:00Z") == 0
    return build_dir / "plan.json"


def test_open_blocking_questions_warn_once_not_per_question(tmp_path, fixture_repo,
                                                            requirement, capsys):
    path = _init_build(tmp_path, fixture_repo, requirement)
    body = write_json(tmp_path / "questions.json", [
        {"id": f"Q{i}", "question": f"Question {i}?", "kind": "blocking", "status": "open"}
        for i in range(1, 6)
    ] + [{"id": "Q6", "question": "Nice to know?", "kind": "informational", "status": "open"}])
    capsys.readouterr()
    assert run("set-clarifications", str(path), "--file", str(body),
               "--repo-root", str(fixture_repo)) == 0
    out = capsys.readouterr().out
    warns = [line for line in out.splitlines() if line.startswith("WARN")]
    assert warns == ["WARN 5 blocking question(s) still open — G1 cannot pass until they are "
                     "answered or deferred"], out
    assert "blocking and still open" not in out

    # `validate` reports the same one line, not one per question.
    capsys.readouterr()
    assert run("validate", str(path), "--repo-root", str(fixture_repo)) == 0
    assert len([l for l in capsys.readouterr().out.splitlines() if l.startswith("WARN")]) == 1


def test_no_warning_once_every_blocking_question_is_closed(tmp_path, fixture_repo,
                                                           requirement, capsys):
    path = _init_build(tmp_path, fixture_repo, requirement)
    body = write_json(tmp_path / "questions.json", [
        {"id": "Q1", "question": "Which queue?", "kind": "blocking", "status": "answered",
         "answer": "Tier 1"},
        {"id": "Q2", "question": "Which calendar?", "kind": "blocking", "status": "deferred",
         "answer": "DEFER: legal"},
    ])
    capsys.readouterr()
    assert run("set-clarifications", str(path), "--file", str(body),
               "--repo-root", str(fixture_repo)) == 0
    assert "still open" not in capsys.readouterr().out


def test_set_clarifications_summary_replaces_the_truncated_init_summary(
        tmp_path, fixture_repo, requirement, capsys):
    path = _init_build(tmp_path, fixture_repo, requirement)
    initial = json.loads(path.read_text())["requirement"]["summary"]
    body = write_json(tmp_path / "questions.json", [
        {"id": "Q1", "question": "Which queue owns unrouted email?", "kind": "blocking",
         "status": "open"},
    ])
    paragraph = ("Acme's B2B support team runs from a shared mailbox today; every inbound "
                 "email must become a Case, routed to the owning queue, with an SLA clock "
                 "running from first touch.")
    capsys.readouterr()
    assert run("set-clarifications", str(path), "--file", str(body),
               "--summary", paragraph, "--repo-root", str(fixture_repo)) == 0
    after = json.loads(path.read_text())
    assert after["requirement"]["summary"] == paragraph != initial
    assert after["requirement"]["source_path"] == "requirement.md", "source_path survives"
    assert "requirement.summary updated" in capsys.readouterr().out

    # Omitting --summary leaves the stored paragraph alone.
    assert run("set-clarifications", str(path), "--file", str(body),
               "--repo-root", str(fixture_repo)) == 0
    assert json.loads(path.read_text())["requirement"]["summary"] == paragraph


# --------------------------------------------------------------------------
# set-clarifications: informational defaults land pre-filled at scale 'ask'
# (contract § 3.1)
# --------------------------------------------------------------------------

def test_set_clarifications_fills_open_informational_defaults_at_scale_ask(
        tmp_path, fixture_repo, capsys):
    plan = plan_dict([step("M1-S01", "M1")], scale="ask")
    path = write_plan_file(tmp_path / "b", plan)
    body = write_json(tmp_path / "questions.json", [
        {"id": "Q1", "question": "Which queue owns unrouted email?", "kind": "blocking",
         "status": "open", "proposed_default": "Tier 1 Support"},
        {"id": "Q2", "question": "Should we log lead source?", "kind": "informational",
         "status": "open", "proposed_default": "Yes, on the Lead Source field"},
        {"id": "Q3", "question": "Already answered?", "kind": "informational",
         "status": "answered", "answer": "Custom text", "proposed_default": "ignored"},
        {"id": "Q4", "question": "Informational with no default?", "kind": "informational",
         "status": "open"},
    ])
    capsys.readouterr()
    assert run("set-clarifications", str(path), "--file", str(body),
               "--repo-root", str(fixture_repo)) == 0
    out = capsys.readouterr().out
    assert "1 informational default(s) applied (scale: ask)" in out

    by_id = {c["id"]: c for c in json.loads(path.read_text())["clarifications"]}
    # Blocking rows are never auto-filled, regardless of scale.
    assert by_id["Q1"]["status"] == "open"
    assert not by_id["Q1"].get("answer")
    # Open informational row with a default: filled and stamped.
    assert by_id["Q2"]["status"] == "answered"
    assert by_id["Q2"]["answer"] == "Yes, on the Lead Source field"
    assert by_id["Q2"]["default_source"] == "proposed_default (scale: ask)"
    # Already-answered informational row: left exactly alone.
    assert by_id["Q3"]["answer"] == "Custom text"
    assert by_id["Q3"]["status"] == "answered"
    # No proposed_default to fill from: stays open.
    assert by_id["Q4"]["status"] == "open"
    assert not by_id["Q4"].get("answer")


def test_set_clarifications_default_source_not_overwritten_if_already_set(
        tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")], scale="ask")
    path = write_plan_file(tmp_path / "b", plan)
    body = write_json(tmp_path / "questions.json", [
        {"id": "Q1", "question": "Nice to know?", "kind": "informational", "status": "open",
         "proposed_default": "Sure", "default_source": "skill-guidance"},
    ])
    assert run("set-clarifications", str(path), "--file", str(body),
               "--repo-root", str(fixture_repo)) == 0
    clar = json.loads(path.read_text())["clarifications"][0]
    assert clar["answer"] == "Sure"
    assert clar["status"] == "answered"
    assert clar["default_source"] == "skill-guidance", "an existing default_source is preserved"


def test_set_clarifications_does_not_fill_defaults_at_project_scale(
        tmp_path, fixture_repo):
    """`project` is the one tier § 3.1 leaves unchanged: every row, blocking
    or informational, still goes to the human."""
    def informational_question(name: str) -> Path:
        return write_json(tmp_path / name, [
            {"id": "Q1", "question": "Nice to know?", "kind": "informational", "status": "open",
             "proposed_default": "Sure"},
        ])

    # Absent scale == 'project' by contract.
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    assert run("set-clarifications", str(path), "--file", str(informational_question("q1.json")),
               "--repo-root", str(fixture_repo)) == 0
    clar = json.loads(path.read_text())["clarifications"][0]
    assert clar["status"] == "open" and not clar.get("answer")

    plan = plan_dict([step("M1-S01", "M1")], scale="project")
    path = write_plan_file(tmp_path / "c", plan)
    assert run("set-clarifications", str(path), "--file", str(informational_question("q2.json")),
               "--repo-root", str(fixture_repo)) == 0
    clar = json.loads(path.read_text())["clarifications"][0]
    assert clar["status"] == "open" and not clar.get("answer")


def test_set_clarifications_fills_open_informational_defaults_at_scale_feature(
        tmp_path, fixture_repo, capsys):
    """§ 3.1's feature-tier clarification-scope cell inherits the ask-tier
    default pre-fill — only the blocking-question ceiling and round count
    differ between the two tiers. The stamped default_source names the
    actual tier, not a hardcoded 'ask'."""
    plan = plan_dict([step("M1-S01", "M1")], scale="feature")
    path = write_plan_file(tmp_path / "b", plan)
    body = write_json(tmp_path / "questions.json", [
        {"id": "Q1", "question": "Which system of record wins on conflict?", "kind": "blocking",
         "status": "open", "proposed_default": "Salesforce"},
        {"id": "Q2", "question": "Should we log the sync timestamp?", "kind": "informational",
         "status": "open", "proposed_default": "Yes, on a hidden field"},
        {"id": "Q3", "question": "Already answered?", "kind": "informational",
         "status": "answered", "answer": "Custom text", "proposed_default": "ignored"},
    ])
    capsys.readouterr()
    assert run("set-clarifications", str(path), "--file", str(body),
               "--repo-root", str(fixture_repo)) == 0
    out = capsys.readouterr().out
    assert "1 informational default(s) applied (scale: feature)" in out

    by_id = {c["id"]: c for c in json.loads(path.read_text())["clarifications"]}
    # Blocking rows are never auto-filled, regardless of scale.
    assert by_id["Q1"]["status"] == "open"
    assert not by_id["Q1"].get("answer")
    # Open informational row with a default: filled and stamped with the
    # actual tier, not a hardcoded 'ask'.
    assert by_id["Q2"]["status"] == "answered"
    assert by_id["Q2"]["answer"] == "Yes, on a hidden field"
    assert by_id["Q2"]["default_source"] == "proposed_default (scale: feature)"
    # Already-answered informational row: left exactly alone.
    assert by_id["Q3"]["answer"] == "Custom text"


def test_set_clarifications_default_renders_and_can_be_overwritten_by_a_human(
        tmp_path, fixture_repo):
    """The filled default must show up in the rendered view (contract § 3.1:
    'listed in CLARIFICATIONS.md as defaults applied'), and a human must still
    be able to overwrite it through the normal render -> edit -> ingest loop."""
    plan = plan_dict([step("M1-S01", "M1")], scale="ask")
    path = write_plan_file(tmp_path / "b", plan)
    body = write_json(tmp_path / "questions.json", [
        {"id": "Q1", "question": "Should we log lead source?", "kind": "informational",
         "status": "open", "proposed_default": "Yes, on the Lead Source field"},
    ])
    assert run("set-clarifications", str(path), "--file", str(body),
               "--repo-root", str(fixture_repo)) == 0
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0

    clar_md = (path.parent / "CLARIFICATIONS.md").read_text()
    assert "#### Q1 — status: answered" in clar_md
    assert "Answer: Yes, on the Lead Source field" in clar_md

    run_md = (path.parent / "RUN.md").read_text()
    assert "## Defaults applied" in run_md
    assert "`Q1`" in run_md and "Yes, on the Lead Source field" in run_md
    assert "proposed_default (scale: ask)" in run_md

    # A human overwrites the pre-filled default...
    set_answer(path.parent / "CLARIFICATIONS.md", "Q1", "No — out of scope for this build")
    assert run("ingest-answers", str(path), "--repo-root", str(fixture_repo)) == 0
    clar = json.loads(path.read_text())["clarifications"][0]
    assert clar["answer"] == "No — out of scope for this build"
    assert clar["status"] == "answered"

    # ...and the overwrite is what renders back out.
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    assert "Answer: No — out of scope for this build" in \
        (path.parent / "CLARIFICATIONS.md").read_text()


# --------------------------------------------------------------------------
# export
# --------------------------------------------------------------------------

def _exportable_build(tmp_path: Path, fixture_repo: Path) -> Path:
    plan = plan_dict([step("M1-S01", "M1")], clarifications=[
        {"id": "Q1", "question": "Which queue owns unrouted email?", "kind": "blocking",
         "status": "answered", "answer": "Tier 1 Support", "group": "routing"},
    ])
    path = write_plan_file(tmp_path / "b", plan)
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    write_outputs(path, "M1-S01")
    write_results(path, "M1-S01")
    write_json(path.parent / "envelopes" / "M1-S01" / "run-1.json", {"agent": "alpha-designer"})
    (path.parent / "reports").mkdir(exist_ok=True)
    (path.parent / "reports" / "MILESTONE-M1-REPORT.md").write_text("# M1\n", encoding="utf-8")
    (path.parent / "workbook").mkdir(exist_ok=True)
    (path.parent / "workbook" / "01-objects.md").write_text("# Objects\n", encoding="utf-8")
    (path.parent / "decisions.md").write_text("# Decisions log\n", encoding="utf-8")
    (path.parent / "traceability.md").write_text("# Traceability\n", encoding="utf-8")
    (path.parent / "requirement.md").write_text("Inbound email to Case.\n", encoding="utf-8")
    return path


def test_export_copies_the_whole_build_directory(tmp_path, fixture_repo, capsys):
    path = _exportable_build(tmp_path, fixture_repo)
    dest = tmp_path / "examples" / "builds" / "case-onboarding"
    capsys.readouterr()
    assert run("export", str(path), str(dest), "--repo-root", str(fixture_repo)) == 0

    for rel in ("plan.json", "PLAN.md", "CLARIFICATIONS.md", "requirement.md", "decisions.md",
                "traceability.md", "workbook/01-objects.md",
                "artefacts/M1-S01/Case.object-meta.xml", "tests/M1-S01/results.json",
                "envelopes/M1-S01/run-1.json", "reports/MILESTONE-M1-REPORT.md"):
        assert (dest / rel).is_file(), f"{rel} was not exported"
    assert json.loads((dest / "plan.json").read_text()) == json.loads(path.read_text())

    out = capsys.readouterr().out
    expected = len([p for p in path.parent.rglob("*") if p.is_file()])
    assert f"{expected} file(s)" in out, out


def test_export_refuses_an_existing_destination_unless_forced(tmp_path, fixture_repo):
    path = _exportable_build(tmp_path, fixture_repo)
    dest = tmp_path / "out"
    assert run("export", str(path), str(dest), "--repo-root", str(fixture_repo)) == 0

    stale = dest / "artefacts" / "M1-S01" / "Gone.object-meta.xml"
    stale.write_text("<CustomObject/>\n", encoding="utf-8")
    assert run("export", str(path), str(dest), "--repo-root", str(fixture_repo)) == 1
    assert stale.is_file(), "a refused export must not touch the destination"

    assert run("export", str(path), str(dest), "--force",
               "--repo-root", str(fixture_repo)) == 0
    assert not stale.exists(), "--force replaces the destination rather than merging into it"
    assert (dest / "plan.json").is_file()


def test_export_force_preserves_a_hand_written_readme(tmp_path, fixture_repo, capsys):
    """The build never produces a README.md; --force must not wipe the
    operator's hand-written one at dest-dir's root (item 2, today's regression:
    a real README got clobbered by a re-export)."""
    path = _exportable_build(tmp_path, fixture_repo)
    dest = tmp_path / "out"
    assert run("export", str(path), str(dest), "--repo-root", str(fixture_repo)) == 0
    assert not (dest / "README.md").exists()

    (dest / "README.md").write_text("# Case Onboarding\n\nHand-written notes.\n",
                                     encoding="utf-8")
    stale = dest / "artefacts" / "M1-S01" / "Gone.object-meta.xml"
    stale.write_text("<CustomObject/>\n", encoding="utf-8")

    capsys.readouterr()
    assert run("export", str(path), str(dest), "--force",
               "--repo-root", str(fixture_repo)) == 0
    assert not stale.exists(), "--force still replaces everything else"
    assert (dest / "README.md").read_text(encoding="utf-8") == (
        "# Case Onboarding\n\nHand-written notes.\n"
    ), "README.md must survive --force untouched"
    assert "kept README.md" in capsys.readouterr().out


def test_export_refuses_an_invalid_plan(tmp_path, fixture_repo):
    path = _exportable_build(tmp_path, fixture_repo)
    plan = json.loads(path.read_text())
    plan["steps"][0]["agent"] = "gamma-legacy"  # deprecated
    path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    dest = tmp_path / "out"
    assert run("export", str(path), str(dest), "--repo-root", str(fixture_repo)) == 1
    assert not dest.exists()


def test_export_refuses_to_copy_the_build_into_itself(tmp_path, fixture_repo):
    path = _exportable_build(tmp_path, fixture_repo)
    assert run("export", str(path), str(path.parent / "copy"),
               "--repo-root", str(fixture_repo)) == 1


# --------------------------------------------------------------------------
# output envelope: extensions + the build-directory envelope path
# --------------------------------------------------------------------------

MINIMAL_ENVELOPE = {
    "agent": "requirements-clarifier",
    "mode": "single",
    "run_id": "2026-09-05T13-30-00Z",
    "report_path": ".sfskills/builds/case-onboarding/envelopes/clarify/"
                   "2026-09-05T13-30-00Z.md",
    "envelope_path": ".sfskills/builds/case-onboarding/envelopes/clarify/"
                     "2026-09-05T13-30-00Z.json",
    "summary": "Clarified the Acme case intake requirement into 97 questions.",
    "confidence": "MEDIUM",
    "process_observations": [],
    "citations": [],
}


def test_envelope_accepts_extensions_and_a_build_directory_path():
    """The two defects the clarifier dry run hit, checked through the helper."""
    pytest.importorskip("jsonschema")
    from scripts import validate_envelope as ve

    envelope = dict(MINIMAL_ENVELOPE)
    envelope["extensions"] = {
        "clarifications": [{"id": "Q1", "group": "routing"}],
        "capability_coverage": [{"capability": "Case priority picklist", "skills": []}],
    }
    assert ve.validate_envelope(envelope) == []

    # Without `extensions`, the same payload at the top level is still refused —
    # that is the reason the field had to exist.
    freestyle = dict(MINIMAL_ENVELOPE)
    freestyle["clarifications"] = [{"id": "Q1"}]
    assert any("clarifications" in msg for msg in ve.validate_envelope(freestyle))

    # The canonical docs/reports/ form keeps working.
    canonical = dict(MINIMAL_ENVELOPE)
    canonical["report_path"] = "docs/reports/requirements-clarifier/2026-09-05T13-30-00Z.md"
    canonical["envelope_path"] = "docs/reports/requirements-clarifier/2026-09-05T13-30-00Z.json"
    assert ve.validate_envelope(canonical) == []

    # And an arbitrary path is still not a report path.
    stray = dict(MINIMAL_ENVELOPE)
    stray["report_path"] = "notes/wherever.md"
    assert any("report_path" in msg for msg in ve.validate_envelope(stray))


def test_citation_type_agent_and_example_build_are_accepted():
    """Regression: three agents cited their own AGENT.md as `type: agent` and
    failed validation (standards/build-orchestration.md § 8 fix). `agent` and
    `example_build` are legal citation types, each requiring `path` like the
    other resolvable-on-disk types."""
    pytest.importorskip("jsonschema")
    from scripts import validate_envelope as ve

    agent_citation = dict(MINIMAL_ENVELOPE)
    agent_citation["citations"] = [{
        "type": "agent",
        "id": "requirements-clarifier",
        "path": "agents/requirements-clarifier/AGENT.md",
        "used_for": "cited its own playbook for the clarification loop",
    }]
    assert ve.validate_envelope(agent_citation) == []

    example_build_citation = dict(MINIMAL_ENVELOPE)
    example_build_citation["citations"] = [{
        "type": "example_build",
        "id": "case-onboarding",
        "path": "examples/builds/case-onboarding/README.md",
        "used_for": "referenced the worked case-intake build as a precedent",
    }]
    assert ve.validate_envelope(example_build_citation) == []

    # A citation type outside the enum is still refused.
    bogus = dict(MINIMAL_ENVELOPE)
    bogus["citations"] = [{
        "type": "bogus",
        "id": "whatever",
        "path": "whatever",
        "used_for": "should not validate",
    }]
    assert ve.validate_envelope(bogus) != []

    # `agent`/`example_build` still require `path`, like the other
    # resolvable-on-disk citation types.
    pathless = dict(MINIMAL_ENVELOPE)
    pathless["citations"] = [{
        "type": "agent",
        "id": "requirements-clarifier",
        "used_for": "missing path on purpose",
    }]
    assert ve.validate_envelope(pathless) != []


@pytest.mark.skipif(not (REPO_ROOT / ".sfskills" / "builds" / "case-onboarding").is_dir(),
                    reason="no local dry-run build in this checkout")
def test_the_dry_run_envelope_validates():
    pytest.importorskip("jsonschema")
    from scripts import validate_envelope as ve

    envelopes = sorted((REPO_ROOT / ".sfskills" / "builds" / "case-onboarding"
                        / "envelopes").rglob("*.json"))
    for path in envelopes:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not (isinstance(payload, dict) and "envelope_path" in payload):
            continue  # a side-car payload, not an envelope
        assert ve.validate_envelope(payload) == [], f"{path} does not validate"


# --------------------------------------------------------------------------
# decisions: the cited branch must really be in the cited tree
# --------------------------------------------------------------------------

def warnings_for(plan: dict, repo_root: Path) -> list[str]:
    schema = build_plan.load_schema()
    return [msg for level, msg in build_plan.validate_plan(plan, repo_root, schema)
            if level == "WARN"]


def _decision_plan(fixture_repo: Path, **decision) -> dict:
    """A one-step plan whose single decision is whatever the test hands in."""
    base = {"id": "D1", "decision": "Record-triggered Flow, not Apex",
            "rationale": "No callout needed."}
    base.update(decision)
    return plan_dict([step("M1-S01", "M1")], decisions=[base])


def test_a_decision_may_only_cite_a_tree_that_exists(fixture_repo):
    plan = _decision_plan(fixture_repo,
                          decision_tree="standards/decision-trees/invented-selection.md",
                          branch="Q3")
    errors = errors_for(plan, fixture_repo)
    assert any("invented-selection.md' does not exist" in e for e in errors), errors


def test_a_decision_may_not_cite_a_branch_the_tree_does_not_have(fixture_repo):
    """The failure this catches: a real tree plus a plausible, absent branch."""
    plan = _decision_plan(fixture_repo,
                          decision_tree="standards/decision-trees/fake-selection.md",
                          branch="Q9")
    errors = errors_for(plan, fixture_repo)
    assert any("has no step 'Q9'" in e for e in errors), errors

    # Q3 is in the fixture tree, so the same plan with the right branch passes.
    ok = _decision_plan(fixture_repo,
                        decision_tree="standards/decision-trees/fake-selection.md",
                        branch="Q3")
    assert errors_for(ok, fixture_repo) == []


def test_branch_ids_do_not_match_by_prefix(fixture_repo):
    """`Q1` must not be satisfied by the tree's `Q10`, nor `Q4` by `Q4a`."""
    tree = fixture_repo / "standards" / "decision-trees" / "prefix-selection.md"
    tree.write_text("```\nQ10. Scheduled job?\nQ4a. Sub-branch?\n```\n", encoding="utf-8")
    for branch in ("Q1", "Q4"):
        plan = _decision_plan(fixture_repo,
                              decision_tree="standards/decision-trees/prefix-selection.md",
                              branch=branch)
        assert any(f"has no step '{branch}'" in e for e in errors_for(plan, fixture_repo))
    for branch in ("Q10", "Q4a"):
        plan = _decision_plan(fixture_repo,
                              decision_tree="standards/decision-trees/prefix-selection.md",
                              branch=branch)
        assert errors_for(plan, fixture_repo) == [], branch


@pytest.mark.parametrize("heading", [
    "Q3. Does the logic need a callout?",          # the form all seven trees use
    "## Q3 — Apex CPU, heap, governor limits",     # performance-tuning's grouping
    "### Q3a. Sub-branch",
    "**Q3** Does the logic need a callout?",
    "- **Q3** Does the logic need a callout?",
    "Q3) Does the logic need a callout?",
    "Q3: Does the logic need a callout?",
    '<a id="q3"></a>',
    "{#q3}",
])
def test_branch_heading_forms_are_recognised(heading):
    branch = "Q3a" if "Q3a" in heading else "Q3"
    assert build_plan._branch_in_tree(f"# tree\n\n```\n{heading}\n```\n", branch), heading


@pytest.mark.parametrize("prose", [
    # Verbatim from automation-selection.md — a cross-reference, not a step.
    "  org-wide coverage; Flow has no equivalent gate. (Same gate as Q3 — the\n",
    "    keeps you in Flow and resolves at Q3.\n",
    "interviews per 24 h — or user licenses × 200, whichever is greater; see Q3.)\n",
])
def test_prose_mentioning_a_branch_is_not_a_heading(prose):
    """A branch id in running prose must not satisfy the citation check."""
    assert not build_plan._branch_in_tree(prose, "Q3"), prose


@pytest.mark.skipif(not (REPO_ROOT / "standards" / "decision-trees").is_dir(),
                    reason="running outside the SfSkills checkout")
@pytest.mark.parametrize("tree,branches", [
    ("automation-selection.md", ["Q1", "Q2", "Q3", "Q6", "Q10", "Q12"]),
    ("sharing-selection.md", ["Q1", "Q3", "Q5", "Q9"]),
])
def test_real_trees_answer_the_branch_check(tree, branches):
    """The regex is calibrated against how the real trees are actually headed."""
    text = (REPO_ROOT / "standards" / "decision-trees" / tree).read_text(encoding="utf-8")
    for branch in branches:
        assert build_plan._branch_in_tree(text, branch), f"{tree} {branch}"
    assert not build_plan._branch_in_tree(text, "Q99"), tree


def test_a_branch_without_a_tree_is_unverifiable(fixture_repo):
    plan = _decision_plan(fixture_repo, branch="Q3")
    assert any("branch 'Q3' with no decision_tree" in e
               for e in errors_for(plan, fixture_repo))


def test_source_reference_must_exist_on_disk(fixture_repo):
    """The escape hatch for a choice no tree covers is still a checked citation."""
    plan = _decision_plan(fixture_repo, adr_required=True,
                          source_reference="skills/admin/fake-object-design/references/"
                                           "nowhere.md")
    assert any("does not exist" in e for e in errors_for(plan, fixture_repo))

    reference = (fixture_repo / "skills" / "admin" / "fake-object-design" / "references"
                 / "routing-selector.md")
    reference.parent.mkdir(parents=True, exist_ok=True)
    reference.write_text("| Route a new Case | Assignment rule |\n", encoding="utf-8")
    ok = _decision_plan(fixture_repo, adr_required=True,
                        source_reference="skills/admin/fake-object-design/references/"
                                         "routing-selector.md")
    assert errors_for(ok, fixture_repo) == []
    assert not any("D1" in w for w in warnings_for(ok, fixture_repo))


def test_a_decision_grounded_in_nothing_warns(fixture_repo):
    plan = _decision_plan(fixture_repo)
    assert errors_for(plan, fixture_repo) == []
    assert any("cites neither a decision_tree nor a source_reference" in w
               for w in warnings_for(plan, fixture_repo))


# --------------------------------------------------------------------------
# checker argument form: a WARN, never a rewrite
# --------------------------------------------------------------------------

CHECKER_SKILL = "skills/admin/fake-object-design/scripts/check_fake.py"


def _with_checker(fixture_repo: Path, command: str) -> dict:
    target = fixture_repo / CHECKER_SKILL
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# checker\n", encoding="utf-8")
    return plan_dict([step("M1-S01", "M1",
                           tests=[{"type": "checker", "command": command}])])


NON_STANDARD_FORM = ("checker declares a non-standard argument form; "
                     "step-tester will run it verbatim")


def test_a_non_standard_checker_form_warns_but_does_not_fail(fixture_repo):
    """Three real skill checkers take a positional path or --file/--workbook."""
    for command in (f"python3 {CHECKER_SKILL} artefacts/M1-S01",
                    f"python3 {CHECKER_SKILL} --file artefacts/M1-S01/model.md",
                    f"python3 {CHECKER_SKILL} --workbook artefacts/M1-S01/workbook.md"):
        plan = _with_checker(fixture_repo, command)
        assert errors_for(plan, fixture_repo) == [], command
        assert any(w.endswith(NON_STANDARD_FORM) for w in warnings_for(plan, fixture_repo)), \
            command


def test_the_house_checker_form_warns_about_nothing(fixture_repo):
    for command in (f"python3 {CHECKER_SKILL} --manifest-dir artefacts/M1-S01",
                    f"python3 {CHECKER_SKILL} --manifest-dir=artefacts/M1-S01"):
        plan = _with_checker(fixture_repo, command)
        assert errors_for(plan, fixture_repo) == [], command
        assert not any(NON_STANDARD_FORM in w for w in warnings_for(plan, fixture_repo)), command


def test_a_missing_checker_is_still_an_error_not_a_warning(fixture_repo):
    """The argument-form WARN must not shadow the 'checker does not exist' ERROR."""
    plan = plan_dict([step("M1-S01", "M1", tests=[
        {"type": "checker",
         "command": "python3 skills/admin/fake-object-design/scripts/check_absent.py "
                    "artefacts/M1-S01"}])])
    errors = errors_for(plan, fixture_repo)
    assert any("does not exist" in e for e in errors), errors
    assert not any(NON_STANDARD_FORM in w for w in warnings_for(plan, fixture_repo))


# --------------------------------------------------------------------------
# render: the ADR column and the decision sub-bullets
# --------------------------------------------------------------------------

def _rendered_plan_md(tmp_path: Path, fixture_repo: Path, decisions: list[dict]) -> str:
    plan = plan_dict([step("M1-S01", "M1")], decisions=decisions)
    path = write_plan_file(tmp_path / "b", plan)
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    return (path.parent / "PLAN.md").read_text(encoding="utf-8")


def test_render_marks_adr_required_and_prints_the_decision_evidence(tmp_path, fixture_repo):
    reference = (fixture_repo / "skills" / "admin" / "fake-object-design" / "references"
                 / "routing-selector.md")
    reference.parent.mkdir(parents=True, exist_ok=True)
    reference.write_text("| Route a new Case | Assignment rule |\n", encoding="utf-8")
    body = _rendered_plan_md(tmp_path, fixture_repo, [
        {"id": "D1", "decision": "Record-triggered Flow, not Apex",
         "decision_tree": "standards/decision-trees/fake-selection.md", "branch": "Q3",
         "rationale": "No callout needed.",
         "branch_quote": "Q3. Does the logic need a callout with retry?\n"
                         "    ├── No  → Record-triggered Flow",
         "alternatives_rejected": ["Apex before-insert trigger", "After-save Flow"],
         "consequences": "No coverage gate, and no custom exception handling.",
         "adr_required": False},
        {"id": "D2", "decision": "Ownership at creation is set by Assignment Rules",
         "rationale": "No tree covers the Case rule engine.",
         "source_reference": "skills/admin/fake-object-design/references/routing-selector.md",
         "alternatives_rejected": ["Before-save Flow setting OwnerId"],
         "consequences": "Two post-save OwnerId writers remain.",
         "adr_required": True},
    ])
    header = "| Id | Decision | Decision tree | Branch | ADR | Rationale |"
    assert header in body
    rows = [line for line in body.splitlines() if line.startswith("| `D")]
    assert rows[0].split("|")[5].strip() == "", "D1 is tree-resolved: no ADR tick"
    assert rows[1].split("|")[5].strip() == "✔", "D2 has adr_required: true"

    # The evidence a reader needs without opening the tree, as sub-bullets.
    assert "- `D1`" in body
    assert ("  - Branch quote: Q3. Does the logic need a callout with retry? "
            "├── No → Record-triggered Flow") in body, "the quote is flattened to one line"
    assert ("  - Alternatives rejected: Apex before-insert trigger; After-save Flow") in body
    assert "  - Consequences: No coverage gate, and no custom exception handling." in body
    assert ("  - Source reference: "
            "`skills/admin/fake-object-design/references/routing-selector.md`") in body


def test_a_bare_decision_renders_no_empty_sub_bullets(tmp_path, fixture_repo):
    body = _rendered_plan_md(tmp_path, fixture_repo, [
        {"id": "D1", "decision": "Record-triggered Flow, not Apex",
         "decision_tree": "standards/decision-trees/fake-selection.md", "branch": "Q3",
         "rationale": "No callout needed."},
    ])
    assert "- `D1`" not in body
    assert "Branch quote" not in body


def test_the_decision_sub_bullets_are_byte_deterministic(tmp_path, fixture_repo):
    decisions = [
        {"id": "D1", "decision": "Record-triggered Flow, not Apex",
         "decision_tree": "standards/decision-trees/fake-selection.md", "branch": "Q3",
         "branch_quote": "Q3. Does the logic need a callout with retry?",
         "alternatives_rejected": ["Apex", "After-save Flow"],
         "consequences": "No coverage gate.", "adr_required": True},
    ]
    first = _rendered_plan_md(tmp_path / "one", fixture_repo, decisions)
    second = _rendered_plan_md(tmp_path / "two", fixture_repo, decisions)
    assert first.encode() == second.encode()


# --------------------------------------------------------------------------
# set-plan --summary
# --------------------------------------------------------------------------

def test_set_plan_summary_replaces_the_requirement_paragraph(
        tmp_path, fixture_repo, requirement, capsys):
    path = _init_build(tmp_path, fixture_repo, requirement)
    questions = write_json(tmp_path / "questions.json", [
        {"id": "Q1", "question": "Which queue?", "kind": "blocking",
         "status": "answered", "answer": "Tier 1"},
    ])
    assert run("set-clarifications", str(path), "--file", str(questions),
               "--summary", "The clarifier's paragraph.",
               "--repo-root", str(fixture_repo)) == 0

    steps = [step("M1-S01", "M1")]
    body = write_json(tmp_path / "plan-body.json", {
        "scope": {"in": ["Case"], "out": ["CTI"],
                  "fit_gap": [{"requirement": "SLA clock", "verdict": "fit"}]},
        "assumptions": [{"id": "A1", "text": "Service Cloud is licensed."}],
        "decisions": [{"id": "D1", "decision": "Flow, not Apex",
                       "decision_tree": "standards/decision-trees/fake-selection.md",
                       "branch": "Q3"}],
        "milestones": [{"id": "M1", "title": "Object model", "steps": ["M1-S01"],
                        "acceptance_tests": [{"type": "manifest", "description": "package.xml"}]}],
        "steps": steps,
    })
    paragraph = ("Inbound support email becomes a Case routed to the owning queue with an "
                 "SLA clock; CTI and the customer portal are out of scope, and the Billing "
                 "restriction is taken as record-level until Q13 is answered.")
    capsys.readouterr()
    assert run("set-plan", str(path), "--file", str(body), "--summary", paragraph,
               "--repo-root", str(fixture_repo)) == 0
    out = capsys.readouterr().out
    assert "requirement.summary updated" in out
    after = json.loads(path.read_text())
    assert after["requirement"]["summary"] == paragraph
    assert after["requirement"]["source_path"] == "requirement.md", "source_path survives"

    # Omitting --summary leaves the stored paragraph alone.
    assert run("set-plan", str(path), "--file", str(body),
               "--repo-root", str(fixture_repo)) == 0
    assert json.loads(path.read_text())["requirement"]["summary"] == paragraph

    # And `render` prints the whole paragraph, not a truncation.
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    assert paragraph in (path.parent / "PLAN.md").read_text(encoding="utf-8")


def test_set_plan_still_refuses_fields_it_does_not_own(tmp_path, fixture_repo, requirement):
    """--summary is a flag, not a seventh writable key in --file."""
    path = _init_build(tmp_path, fixture_repo, requirement)
    body = write_json(tmp_path / "plan-body.json",
                      {"requirement": {"source_path": "requirement.md", "summary": "sneaked in"}})
    assert run("set-plan", str(path), "--file", str(body),
               "--repo-root", str(fixture_repo)) == 1


# --------------------------------------------------------------------------
# the real dry-run plan — the fixture these gates were written against
# --------------------------------------------------------------------------

DRY_RUN_PLAN = REPO_ROOT / ".sfskills" / "builds" / "case-onboarding" / "plan.json"


@pytest.mark.skipif(not DRY_RUN_PLAN.is_file(),
                    reason="no local dry-run build in this checkout")
def test_the_dry_run_plan_still_validates(capsys):
    """Its nine decisions cite six real trees; every branch must resolve."""
    capsys.readouterr()
    assert run("validate", str(DRY_RUN_PLAN), "--repo-root", str(REPO_ROOT)) == 0
    out = capsys.readouterr().out
    assert not [line for line in out.splitlines() if line.startswith("ERROR")], out


@pytest.mark.skipif(not DRY_RUN_PLAN.is_file(),
                    reason="no local dry-run build in this checkout")
def test_the_dry_run_plan_renders_its_adr_decisions(tmp_path):
    plan = json.loads(DRY_RUN_PLAN.read_text(encoding="utf-8"))
    expected = sorted(d["id"] for d in plan["decisions"] if d.get("adr_required"))
    if not expected:
        pytest.skip("the live dry-run plan currently has no ADR decisions")

    body = build_plan.render_plan_md(plan)
    ticked = sorted(line.split("|")[1].strip().strip("`")
                    for line in body.splitlines()
                    if line.startswith("| `D") and line.split("|")[5].strip() == "✔")
    assert ticked == expected
    for did in expected:
        assert f"- `{did}`" in body, f"{did} renders its sub-bullets"


def test_set_verification_plan_rejected_archives_without_bumping(tmp_path, fixture_repo):
    """Both routes to plan-rejected archive the rejected body; neither bumps.

    Dry-run stage 5 found the verifier route archiving nothing; stage 6 found
    both routes bumping, which minted plan versions no planner had written.
    """
    build = tmp_path / "b"
    plan = plan_dict([step("M1-S01", "M1")], status="planned")
    path = write_plan_file(build, plan)
    assert run("ensure-gates", str(path), "--repo-root", str(fixture_repo)) == 0
    assert run("gate", str(path), "clarifications", "approve", "--by", "t", "--repo-root", str(fixture_repo)) == 0
    before = json.loads(path.read_text(encoding="utf-8"))
    body = write_json(tmp_path / "ver.json", {"lenses": [{"lens": "executability", "verdict": "fail"}],
                                                "blockers": [], "warnings": []})
    assert run("set-verification", str(path), "--file", str(body), "--outcome", "plan-rejected",
               "--repo-root", str(fixture_repo)) == 0
    after = json.loads(path.read_text(encoding="utf-8"))
    assert after["status"] == "plan-rejected"
    assert after["version"] == before["version"], "the rejection archives; the re-plan bumps"
    assert after["history"][-1]["version"] == before["version"]
    assert after["history"][-1]["plan"]["status"] == "planned"


# --------------------------------------------------------------------------
# Plan versioning — archive at rejection, bump at re-plan (contract § 3)
# --------------------------------------------------------------------------

def _replan_body(tmp_path: Path, name: str = "replan.json") -> Path:
    """A minimal, valid set-plan payload: one milestone, one step."""
    steps = [step("M1-S01", "M1")]
    return write_json(tmp_path / name, {
        "milestones": [{"id": "M1", "title": "Intake", "steps": ["M1-S01"],
                        "acceptance_tests": [{"type": "manifest",
                                              "description": "package.xml consistent"}]}],
        "steps": steps,
    })


def test_replan_after_gate_rejection_bumps_the_version_exactly_once(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")])
    path = write_plan_file(tmp_path / "b", plan)
    assert run("gate", str(path), "plan", "reject", "--by", "pranav",
               "--at", "2026-09-05T10:30:00Z", "--repo-root", str(fixture_repo)) == 0
    assert json.loads(path.read_text())["version"] == 1

    body = _replan_body(tmp_path)
    assert run("set-plan", str(path), "--file", str(body),
               "--repo-root", str(fixture_repo)) == 0
    after = json.loads(path.read_text())
    assert after["version"] == 2, "the re-plan is v2"
    assert after["status"] == "planned"
    assert [h["version"] for h in after["history"]] == [1]

    # A second set-plan at 'planned' is still the same v2 — only a rejection
    # followed by a re-plan moves the number.
    assert run("set-plan", str(path), "--file", str(body),
               "--repo-root", str(fixture_repo)) == 0
    assert json.loads(path.read_text())["version"] == 2


def test_replan_after_verifier_rejection_bumps_the_version_exactly_once(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")], status="planned")
    path = write_plan_file(tmp_path / "b", plan)
    verification = write_json(tmp_path / "ver.json",
                              {"lenses": [{"lens": "executability", "verdict": "fail"}]})
    assert run("set-verification", str(path), "--file", str(verification),
               "--outcome", "plan-rejected", "--at", "2026-09-05T11:00:00Z",
               "--repo-root", str(fixture_repo)) == 0
    assert json.loads(path.read_text())["version"] == 1

    body = _replan_body(tmp_path)
    assert run("set-plan", str(path), "--file", str(body),
               "--repo-root", str(fixture_repo)) == 0
    after = json.loads(path.read_text())
    assert after["version"] == 2
    assert [h["version"] for h in after["history"]] == [1]


def test_set_plan_from_clarifying_leaves_the_version_alone(tmp_path, fixture_repo):
    """The first plan of a build is v1 — planning is not re-planning."""
    plan = plan_dict([step("M1-S01", "M1")], status="clarifying")
    path = write_plan_file(tmp_path / "b", plan)
    body = _replan_body(tmp_path)
    assert run("set-plan", str(path), "--file", str(body),
               "--repo-root", str(fixture_repo)) == 0
    after = json.loads(path.read_text())
    assert after["version"] == 1
    assert after["status"] == "planned"
    assert after["history"] == []


# --------------------------------------------------------------------------
# Checker quality — scaffold stubs and checker scope (contract § 5)
# --------------------------------------------------------------------------

REAL_CHECKER = "\n".join(
    ['#!/usr/bin/env python3',
     '"""A checker with actual finding logic."""',
     'import argparse, sys',
     'from pathlib import Path',
     '']
    + [f"# body line {i}" for i in range(70)]
    + ['def main():',
       '    ap = argparse.ArgumentParser()',
       '    ap.add_argument("--manifest-dir", required=True)',
       '    args = ap.parse_args()',
       '    findings = [p for p in Path(args.manifest_dir).glob("*.xml") if not p.read_text()]',
       '    for f in findings:',
       '        print(f"ERROR {f} is empty")',
       '    return 1 if findings else 0',
       '',
       '',
       'if __name__ == "__main__":',
       '    sys.exit(main())',
       ''])

SHORT_STUB_CHECKER = (
    '#!/usr/bin/env python3\n"""Scaffold."""\nimport sys\n\n\ndef main():\n    return 1\n\n\n'
    'if __name__ == "__main__":\n    sys.exit(main())\n')

MARKER_STUB_CHECKER = REAL_CHECKER.replace(
    "# body line 0", "# TODO: Implement the real findings for this skill")


def add_checker(repo: Path, domain: str, slug: str, filename: str, source: str) -> str:
    """Drop a skill-local checker into the fixture repo; return its repo path."""
    rel = f"skills/{domain}/{slug}/scripts/{filename}"
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    skill = repo / "skills" / domain / slug / "SKILL.md"
    if not skill.is_file():
        skill.write_text(SKILL_MD.format(domain=domain, slug=slug), encoding="utf-8")
    return rel


def checker_test(rel: str, step_id: str, **extra) -> dict:
    out = {"type": "checker", "command": f"python3 {rel} --manifest-dir artefacts/{step_id}"}
    out.update(extra)
    return out


def warns_for(plan: dict, repo_root: Path) -> list[str]:
    schema = build_plan.load_schema()
    return [msg for level, msg in build_plan.validate_plan(plan, repo_root, schema)
            if level == "WARN"]


def test_stub_checker_warns_but_a_real_one_does_not(tmp_path, fixture_repo):
    real = add_checker(fixture_repo, "admin", "fake-object-design",
                       "check_fake_object_design.py", REAL_CHECKER)
    short = add_checker(fixture_repo, "admin", "fake-short",
                        "check_fake_short.py", SHORT_STUB_CHECKER)
    marker = add_checker(fixture_repo, "admin", "fake-marker",
                         "check_fake_marker.py", MARKER_STUB_CHECKER)

    plan = plan_dict([step("M1-S01", "M1", tests=[checker_test(real, "M1-S01")])])
    assert not [w for w in warns_for(plan, fixture_repo) if "scaffold stub" in w], \
        "a 70+ line checker with findings logic is not a stub"

    for rel, needle in ((short, "line(s) long"), (marker, "TODO: Implement")):
        plan = plan_dict([step("M1-S01", "M1", tests=[checker_test(rel, "M1-S01")])])
        stub_warns = [w for w in warns_for(plan, fixture_repo) if "scaffold stub" in w]
        assert len(stub_warns) == 1, (rel, warns_for(plan, fixture_repo))
        assert "the tester will fail this step" in stub_warns[0]
        assert needle in stub_warns[0]
        # A stub is a WARN, never an ERROR — the plan is still writable.
        assert errors_for(plan, fixture_repo) == []


def test_cross_referential_checker_warns_at_step_scope_only(tmp_path, fixture_repo):
    rel = add_checker(fixture_repo, "admin", "fake-escalation",
                      "check_escalation_rules.py", REAL_CHECKER)

    # routing/sla/access step + step scope (the default) -> WARN.
    for stype in ("routing", "sla", "access"):
        plan = plan_dict([step("M1-S01", "M1", stype=stype,
                               tests=[checker_test(rel, "M1-S01")])])
        hits = [w for w in warns_for(plan, fixture_repo) if "cross-referential" in w]
        assert len(hits) == 1, (stype, warns_for(plan, fixture_repo))
        assert '"scope": "build"' in hits[0] and "milestone acceptance test" in hits[0]

    # Declaring build scope answers the warning.
    plan = plan_dict([step("M1-S01", "M1", stype="routing",
                           tests=[checker_test(rel, "M1-S01", scope="build")])])
    assert not [w for w in warns_for(plan, fixture_repo) if "cross-referential" in w]
    assert errors_for(plan, fixture_repo) == []

    # A step type the checker does not reach across is not warned about, and
    # neither is a checker outside the documented cross-referential list.
    plan = plan_dict([step("M1-S01", "M1", stype="object-model",
                           tests=[checker_test(rel, "M1-S01")])])
    assert not [w for w in warns_for(plan, fixture_repo) if "cross-referential" in w]
    other = add_checker(fixture_repo, "admin", "fake-queues",
                        "check_queues.py", REAL_CHECKER)
    plan = plan_dict([step("M1-S01", "M1", stype="routing",
                           tests=[checker_test(other, "M1-S01")])])
    assert not [w for w in warns_for(plan, fixture_repo) if "cross-referential" in w]


def test_checker_scope_is_validated_and_rendered(tmp_path, fixture_repo):
    rel = add_checker(fixture_repo, "admin", "fake-object-design",
                      "check_fake_object_design.py", REAL_CHECKER)
    plan = plan_dict([step("M1-S01", "M1", tests=[checker_test(rel, "M1-S01", scope="build")])])

    # Schema enum + semantic check both refuse a scope outside step|build.
    bad = plan_dict([step("M1-S01", "M1", tests=[checker_test(rel, "M1-S01", scope="org")])])
    schema = build_plan.load_schema()
    assert build_plan.schema_errors(bad, schema, schema), "schema enum rejects an unknown scope"
    assert any("unknown scope" in msg for _lvl, msg
               in build_plan._acceptance_issues(bad["steps"][0]["acceptance_tests"],
                                                "step M1-S01", fixture_repo))

    body = build_plan.render_plan_md(plan)
    assert "[scope: build]" in body, "render surfaces a declared checker scope"
    # The default scope is not stamped on every row.
    plain = plan_dict([step("M1-S01", "M1", tests=[checker_test(rel, "M1-S01")])])
    assert "scope:" not in build_plan.render_plan_md(plain)

    # A scope on a non-checker test is a WARN, not a silent no-op.
    noisy = plan_dict([step("M1-S01", "M1", tests=[{"type": "xml", "scope": "build",
                                                    "description": "artefacts parse"}])])
    assert any("only means anything on a 'checker' test" in w
               for w in warns_for(noisy, fixture_repo))
    assert errors_for(noisy, fixture_repo) == []


def test_scope_must_agree_with_manifest_dir(fixture_repo):
    """Section 5: scope is intent; the literal --manifest-dir governs; disagreement WARNs."""
    rel = add_checker(fixture_repo, "admin", "fake-scope", "check_scope.py", REAL_CHECKER)

    # Agreeing pairs: step scope + artefacts/<step-id>, build scope + artefacts root.
    for scope, target in (("step", "artefacts/M1-S01"), ("build", "artefacts"), ("build", "artefacts/")):
        plan = plan_dict([step("M1-S01", "M1", tests=[
            {"type": "checker", "command": f"python3 {rel} --manifest-dir {target}", "scope": scope}])])
        assert not [w for w in warns_for(plan, fixture_repo) if "disagrees" in w], (scope, target)

    # Disagreeing pairs WARN and never ERROR.
    for scope, target in (("build", "artefacts/M1-S01"), ("step", "artefacts")):
        plan = plan_dict([step("M1-S01", "M1", tests=[
            {"type": "checker", "command": f"python3 {rel} --manifest-dir {target}", "scope": scope}])])
        hits = [w for w in warns_for(plan, fixture_repo) if "disagrees" in w]
        assert len(hits) == 1, (scope, target, warns_for(plan, fixture_repo))
        assert target.rstrip("/") in hits[0] and scope in hits[0]
        assert errors_for(plan, fixture_repo) == []


def test_rejected_body_archives_its_own_verdict_and_replan_clears_it(tmp_path, fixture_repo, requirement, capsys):
    """W06: history[v].plan.verification is the verdict that rejected v; a re-plan has no verification."""
    build_dir = tmp_path / "b"
    assert run("init", "--build-dir", str(build_dir), "--title", "Build B", "--requirement", str(requirement),
               "--repo-root", str(fixture_repo), "--now", "2026-09-05T09:00:00Z") == 0
    path = build_dir / "plan.json"
    body = write_json(tmp_path / "body.json", {
        "scope": {"in": ["Case"], "out": [], "fit_gap": []}, "fit_gap": [],
        "decisions": [{"id": "D1", "decision": "Flow"}],
        "milestones": [{"id": "M1", "title": "Intake", "steps": ["M1-S01"],
                        "acceptance_tests": [{"type": "manifest", "description": "ok"}]}],
        "steps": [step("M1-S01", "M1")],
    })
    capsys.readouterr()
    assert run("set-plan", str(path), "--file", str(body), "--repo-root", str(fixture_repo)) == 0
    v1 = write_json(tmp_path / "v1.json", {"lenses": [], "blockers": [{"step": "M1-S01", "problem": "x"}], "plan_version": 1})
    assert run("set-verification", str(path), "--file", str(v1), "--outcome", "plan-rejected",
               "--by", "verifier", "--repo-root", str(fixture_repo)) == 0
    plan = json.loads(path.read_text())
    assert plan["history"][-1]["version"] == 1
    assert plan["history"][-1]["plan"]["verification"]["plan_version"] == 1
    assert plan["history"][-1]["plan"]["verification"]["status"] == "plan-rejected"
    # re-plan -> v2 with no inherited verdict
    assert run("set-plan", str(path), "--file", str(body), "--repo-root", str(fixture_repo)) == 0
    plan = json.loads(path.read_text())
    assert plan["version"] == 2 and "verification" not in plan
    v2 = write_json(tmp_path / "v2.json", {"lenses": [], "blockers": [{"step": "M1-S01", "problem": "y"}], "plan_version": 2})
    assert run("set-verification", str(path), "--file", str(v2), "--outcome", "plan-rejected",
               "--by", "verifier", "--repo-root", str(fixture_repo)) == 0
    plan = json.loads(path.read_text())
    assert [h["plan"]["verification"]["plan_version"] for h in plan["history"]] == [1, 2]


def test_init_links_skills_into_the_build_dir(tmp_path, fixture_repo, requirement, capsys):
    """Section 5: declared checker commands resolve from the build dir via a skills symlink."""
    build_dir = tmp_path / "b"
    assert run("init", "--build-dir", str(build_dir), "--title", "Build B", "--requirement", str(requirement),
               "--repo-root", str(fixture_repo), "--now", "2026-09-05T09:00:00Z") == 0
    link = build_dir / "skills"
    assert link.is_symlink() and link.resolve() == (fixture_repo / "skills").resolve()
    link.unlink()
    capsys.readouterr()
    assert run("ensure-gates", str(build_dir / "plan.json"), "--repo-root", str(fixture_repo)) == 0
    assert link.is_symlink(), "ensure-gates recreates a missing skills link"


def test_export_skips_the_skills_symlink(tmp_path, fixture_repo, requirement, capsys):
    """Section 5/9: the build dir's skills link points into the repo and must not be exported."""
    build_dir = tmp_path / "b"
    assert run("init", "--build-dir", str(build_dir), "--title", "Build B", "--requirement", str(requirement),
               "--repo-root", str(fixture_repo), "--now", "2026-09-05T09:00:00Z") == 0
    assert (build_dir / "skills").is_symlink()
    dest = tmp_path / "out"
    capsys.readouterr()
    assert run("export", str(build_dir / "plan.json"), str(dest), "--repo-root", str(fixture_repo)) == 0
    assert not (dest / "skills").exists() and not (dest / "skills").is_symlink()
    assert (dest / "plan.json").is_file() and (dest / "requirement.md").is_file()


def test_documented_step_can_be_rebuilt():
    """Section 4: documented -> running and built -> running are the two rebuild
    paths; tested is not re-runnable — a repair found after testing goes
    tested -> failed -> pending -> running instead (item 3, 2026-09-12)."""
    from scripts.build_plan import ALLOWED_TRANSITIONS
    assert "running" in ALLOWED_TRANSITIONS["documented"]
    assert "running" in ALLOWED_TRANSITIONS["built"]
    assert "running" not in ALLOWED_TRANSITIONS["tested"]


def test_set_milestone_never_moves_an_accepted_milestone(tmp_path, fixture_repo, requirement, capsys):
    """F-12: an accepted milestone is the human's record; re-verification is appended, not overwritten."""
    build_dir = tmp_path / "b"
    assert run("init", "--build-dir", str(build_dir), "--title", "Build B", "--requirement", str(requirement),
               "--repo-root", str(fixture_repo), "--now", "2026-09-05T09:00:00Z") == 0
    path = build_dir / "plan.json"
    plan = json.loads(path.read_text())
    plan["milestones"] = [{"id": "M1", "title": "Intake", "steps": [],
                           "acceptance_tests": [{"type": "manifest", "description": "ok"}], "status": "accepted"}]
    plan["human_gates"].append({"name": "milestone:M1", "status": "approved", "by": "t", "at": "2026-09-05T10:00:00Z"})
    path.write_text(json.dumps(plan))
    (build_dir / "reports").mkdir(exist_ok=True)
    (build_dir / "reports" / "r.md").write_text("# r\n")
    capsys.readouterr()
    assert run("set-milestone", str(path), "M1", "--status", "verified", "--report-path", "reports/r.md",
               "--repo-root", str(fixture_repo)) == 0
    after = json.loads(path.read_text())["milestones"][0]
    assert after["status"] == "accepted"
    assert after["report_path"] == "reports/r.md"
    assert after["reverifications"][0]["verdict"] == "verified"


# --------------------------------------------------------------------------
# § 3.1 "Ceremony scales to the ask" — scale
# --------------------------------------------------------------------------

def test_init_without_scale_leaves_it_absent(tmp_path, fixture_repo, requirement, capsys):
    build_dir = tmp_path / "b"
    assert run("init", "--build-dir", str(build_dir), "--title", "Test Build",
               "--requirement", str(requirement), "--repo-root", str(fixture_repo),
               "--now", "2026-09-05T09:00:00Z") == 0
    out = capsys.readouterr().out
    plan = json.loads((build_dir / "plan.json").read_text())
    assert "scale" not in plan
    scale_line = next(l for l in out.splitlines() if l.strip().startswith("scale:"))
    assert "unset" in scale_line
    assert "override" not in scale_line


def test_init_with_scale_stores_it_and_echoes_the_override(tmp_path, fixture_repo, requirement, capsys):
    build_dir = tmp_path / "b"
    assert run("init", "--build-dir", str(build_dir), "--title", "Test Build",
               "--requirement", str(requirement), "--repo-root", str(fixture_repo),
               "--now", "2026-09-05T09:00:00Z", "--scale", "ask") == 0
    out = capsys.readouterr().out
    plan = json.loads((build_dir / "plan.json").read_text())
    assert plan["scale"] == "ask"
    build_mode_line = next(l for l in out.splitlines() if "build mode:" in l)
    scale_line = next(l for l in out.splitlines() if l.strip().startswith("scale:"))
    assert "ask" in scale_line
    assert "override" in scale_line
    assert build_mode_line is not None  # scale is echoed beside it, not replacing it


def test_init_rejects_an_unknown_scale(tmp_path, fixture_repo, requirement):
    build_dir = tmp_path / "b"
    rc = run("init", "--build-dir", str(build_dir), "--title", "Test Build",
             "--requirement", str(requirement), "--repo-root", str(fixture_repo),
             "--scale", "epic")
    assert rc == 2  # argparse's own choices= rejection


def test_set_scale_sets_it_on_intake(tmp_path, fixture_repo, capsys):
    plan = plan_dict([step("M1-S01", "M1")], status="intake")
    path = write_plan_file(tmp_path / "b", plan)
    capsys.readouterr()
    assert run("set-scale", str(path), "ask", "--by", "pranav",
               "--repo-root", str(fixture_repo)) == 0
    out = capsys.readouterr().out
    assert json.loads(path.read_text())["scale"] == "ask"
    assert "scale: ask (set by pranav)" in out
    assert "next:" in out and "set-clarifications" in out


def test_set_scale_sets_it_on_clarifying(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")], status="clarifying")
    path = write_plan_file(tmp_path / "b", plan)
    assert run("set-scale", str(path), "feature", "--by", "pranav",
               "--repo-root", str(fixture_repo)) == 0
    assert json.loads(path.read_text())["scale"] == "feature"


def test_set_scale_refused_once_planned(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")], status="planned")
    path = write_plan_file(tmp_path / "b", plan)
    before = path.read_bytes()
    rc = run("set-scale", str(path), "ask", "--by", "pranav",
             "--repo-root", str(fixture_repo))
    assert rc == 1
    assert path.read_bytes() == before  # left untouched


def test_set_scale_refused_once_building(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")], status="building")
    path = write_plan_file(tmp_path / "b", plan)
    before = path.read_bytes()
    rc = run("set-scale", str(path), "ask", "--by", "pranav",
             "--repo-root", str(fixture_repo))
    assert rc == 1
    assert path.read_bytes() == before


def test_set_scale_refused_change_without_force_names_old_and_new(tmp_path, fixture_repo, capsys):
    plan = plan_dict([step("M1-S01", "M1")], status="clarifying", scale="ask")
    path = write_plan_file(tmp_path / "b", plan)
    capsys.readouterr()
    rc = run("set-scale", str(path), "feature", "--by", "pranav",
             "--repo-root", str(fixture_repo))
    err = capsys.readouterr().err
    assert rc == 1
    assert json.loads(path.read_text())["scale"] == "ask"  # untouched
    assert "'ask'" in err and "'feature'" in err


def test_set_scale_change_allowed_with_force(tmp_path, fixture_repo, capsys):
    plan = plan_dict([step("M1-S01", "M1")], status="clarifying", scale="ask")
    path = write_plan_file(tmp_path / "b", plan)
    capsys.readouterr()
    rc = run("set-scale", str(path), "feature", "--by", "pranav", "--force",
             "--repo-root", str(fixture_repo))
    out = capsys.readouterr().out
    assert rc == 0
    assert json.loads(path.read_text())["scale"] == "feature"
    assert "ask -> feature" in out
    assert "set by pranav" in out


def test_set_scale_rejects_an_invalid_tier(tmp_path, fixture_repo):
    plan = plan_dict([step("M1-S01", "M1")], status="intake")
    path = write_plan_file(tmp_path / "b", plan)
    before = path.read_bytes()
    rc = run("set-scale", str(path), "epic", "--by", "pranav",
             "--repo-root", str(fixture_repo))
    assert rc == 2  # argparse's own choices= rejection
    assert path.read_bytes() == before


def test_set_scale_then_validate_still_passes(tmp_path, fixture_repo, capsys):
    plan = plan_dict([step("M1-S01", "M1")], status="intake")
    path = write_plan_file(tmp_path / "b", plan)
    assert run("set-scale", str(path), "project", "--by", "pranav",
               "--repo-root", str(fixture_repo)) == 0
    capsys.readouterr()
    rc = run("validate", str(path), "--repo-root", str(fixture_repo))
    assert rc == 0


def test_validate_warns_ask_scale_shape_mismatch(tmp_path, fixture_repo, capsys):
    steps = [step("M1-S01", "M1"), step("M1-S02", "M1", depends_on=["M1-S01"])]
    plan = plan_dict(steps, scale="ask")
    path = write_plan_file(tmp_path / "b", plan)
    capsys.readouterr()
    rc = run("validate", str(path), "--repo-root", str(fixture_repo))
    out = capsys.readouterr().out
    assert rc == 0, "a shape mismatch is a WARN, never an ERROR (§ 3.1: re-tier, not re-plan)"
    assert "scale 'ask' expects 1 milestone and 1 step" in out
    assert "§ 3.1" in out


def test_validate_warns_open_answer_without_assumption(tmp_path, fixture_repo, capsys):
    sid = "M1-S01"
    steps = [step(sid, "M1", inputs={"object": "Case", "answers": ["Q1"]})]
    plan = plan_dict(
        steps,
        clarifications=[{"id": "Q1", "question": "Which queue?", "kind": "informational",
                         "status": "open"}],
        assumptions=[],
    )
    path = write_plan_file(tmp_path / "b", plan)
    capsys.readouterr()
    rc = run("validate", str(path), "--repo-root", str(fixture_repo))
    out = capsys.readouterr().out
    assert rc == 0
    assert (
        f"step {sid} inputs.answers: Q1 is status 'open' and no assumptions[] row "
        f"applies it to this step — record the applied default as an assumption "
        f"(because names Q1, steps names {sid}) and list it under "
        f"inputs.defaults_applied, or answer the question (§ 3.1)"
    ) in out


def test_validate_no_warn_when_defaults_applied_names_assumption(tmp_path, fixture_repo, capsys):
    sid = "M1-S01"
    steps = [step(sid, "M1", inputs={
        "object": "Case",
        "answers": ["Q1"],
        "defaults_applied": {"Q1": "A1"},
    })]
    plan = plan_dict(
        steps,
        clarifications=[{"id": "Q1", "question": "Which queue?", "kind": "informational",
                         "status": "open"}],
        assumptions=[{"id": "A1", "text": "x", "because": "Q1 open", "risk": "low",
                      "steps": [sid]}],
    )
    path = write_plan_file(tmp_path / "b", plan)
    capsys.readouterr()
    rc = run("validate", str(path), "--repo-root", str(fixture_repo))
    out = capsys.readouterr().out
    assert rc == 0
    assert "inputs.answers:" not in out


def test_validate_no_warn_when_assumption_because_names_question(tmp_path, fixture_repo, capsys):
    sid = "M1-S01"
    steps = [step(sid, "M1", inputs={"object": "Case", "answers": ["Q1"]})]
    plan = plan_dict(
        steps,
        clarifications=[{"id": "Q1", "question": "Which queue?", "kind": "informational",
                         "status": "open"}],
        assumptions=[{"id": "A1", "text": "x",
                      "because": "Q1 informational, left open at G1; …",
                      "risk": "low", "steps": [sid]}],
    )
    path = write_plan_file(tmp_path / "b", plan)
    capsys.readouterr()
    rc = run("validate", str(path), "--repo-root", str(fixture_repo))
    out = capsys.readouterr().out
    assert rc == 0
    assert "inputs.answers:" not in out


def _repo_with_demo_thing_checker(tmp_path: Path, fixture_repo: Path) -> Path:
    """Repo root with skills/demo/thing and its check_thing.py (fixture is function-scoped)."""
    # fixture_repo already has agents/templates/trees; add the cited skill under it.
    skill = fixture_repo / "skills" / "demo" / "thing"
    (skill / "scripts").mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text("# demo/thing\n", encoding="utf-8")
    (skill / "scripts" / "check_thing.py").write_text("print('ok')\n", encoding="utf-8")
    return fixture_repo


def test_validate_warns_undeclared_checker_of_cited_skill(tmp_path, fixture_repo, capsys):
    repo = _repo_with_demo_thing_checker(tmp_path, fixture_repo)
    sid = "M1-S01"
    mid = "M1"
    plan = plan_dict([step(sid, mid, skills=["demo/thing"])])
    path = write_plan_file(tmp_path / "b", plan)
    capsys.readouterr()
    rc = run("validate", str(path), "--repo-root", str(repo))
    out = capsys.readouterr().out
    assert rc == 0
    assert (
        f"step {sid} skills: demo/thing ships check_thing.py but no checker test "
        f"on the step or on milestone {mid} runs it — declare it in "
        f"acceptance_tests[] (or on the milestone, if it needs cross-step "
        f"scope) or drop the skill from skills[] (§ 5)"
    ) in out


def test_validate_no_warn_when_checker_declared_on_step(tmp_path, fixture_repo, capsys):
    repo = _repo_with_demo_thing_checker(tmp_path, fixture_repo)
    sid = "M1-S01"
    command = "python3 skills/demo/thing/scripts/check_thing.py --manifest-dir artefacts/M1-S01"
    plan = plan_dict([step(sid, "M1", skills=["demo/thing"], tests=[
        {"type": "xml", "description": "every artefact parses"},
        {"type": "checker", "command": command},
    ])])
    path = write_plan_file(tmp_path / "b", plan)
    capsys.readouterr()
    rc = run("validate", str(path), "--repo-root", str(repo))
    out = capsys.readouterr().out
    assert rc == 0
    assert "ships check_thing.py but no checker test" not in out


def test_validate_no_warn_when_checker_declared_on_milestone(tmp_path, fixture_repo, capsys):
    repo = _repo_with_demo_thing_checker(tmp_path, fixture_repo)
    sid = "M1-S01"
    mid = "M1"
    command = "python3 skills/demo/thing/scripts/check_thing.py --manifest-dir artefacts"
    steps = [step(sid, mid, skills=["demo/thing"])]
    plan = plan_dict(steps, milestones=[{
        "id": mid,
        "title": "Milestone M1",
        "steps": [sid],
        "acceptance_tests": [
            {"type": "manifest", "description": "package.xml consistent"},
            {"type": "checker", "command": command},
        ],
    }])
    path = write_plan_file(tmp_path / "b", plan)
    capsys.readouterr()
    rc = run("validate", str(path), "--repo-root", str(repo))
    out = capsys.readouterr().out
    assert rc == 0
    assert "ships check_thing.py but no checker test" not in out


def test_validate_warns_feature_scale_shape_mismatch(tmp_path, fixture_repo, capsys):
    steps = [step(f"M1-S0{i}", "M1", depends_on=([f"M1-S0{i - 1}"] if i > 1 else []))
             for i in range(1, 7)]
    plan = plan_dict(steps, scale="feature")
    path = write_plan_file(tmp_path / "b", plan)
    capsys.readouterr()
    rc = run("validate", str(path), "--repo-root", str(fixture_repo))
    out = capsys.readouterr().out
    assert rc == 0
    assert "scale 'feature' expects 1 milestone and at most 5 steps" in out
    assert "§ 3.1" in out


def test_validate_no_shape_warn_when_scale_is_project_or_absent(tmp_path, fixture_repo, capsys):
    # Two milestones' worth of shape (more than 'ask' or 'feature' would allow)
    # is exactly what 'project' is for, and absent scale means 'project'.
    steps = [step("M1-S01", "M1"), step("M1-S02", "M1", depends_on=["M1-S01"])]
    for scale_kwargs in ({}, {"scale": "project"}):
        plan = plan_dict(steps, **scale_kwargs)
        label = scale_kwargs.get("scale", "absent")
        path = write_plan_file(tmp_path / f"b-{label}", plan)
        capsys.readouterr()
        rc = run("validate", str(path), "--repo-root", str(fixture_repo))
        out = capsys.readouterr().out
        assert rc == 0
        assert "scale 'ask' expects" not in out
        assert "scale 'feature' expects" not in out


def test_ensure_gates_ask_adds_milestone_but_no_step_gate(tmp_path, fixture_repo):
    steps = [step("M1-S01", "M1", human_gate=False)]
    plan = plan_dict(steps, scale="ask", human_gates=[])
    path = write_plan_file(tmp_path / "b", plan)
    assert run("ensure-gates", str(path), "--repo-root", str(fixture_repo)) == 0
    names = [g["name"] for g in json.loads(path.read_text())["human_gates"]]
    assert names == ["clarifications", "plan", "milestone:M1"]


def test_ensure_gates_ask_adds_no_step_gate_even_when_human_gate_true(tmp_path, fixture_repo, capsys):
    steps = [step("M1-S01", "M1", human_gate=True)]
    plan = plan_dict(steps, scale="ask", human_gates=[])
    path = write_plan_file(tmp_path / "b", plan)
    capsys.readouterr()
    assert run("ensure-gates", str(path), "--repo-root", str(fixture_repo)) == 0
    out = capsys.readouterr().out
    names = [g["name"] for g in json.loads(path.read_text())["human_gates"]]
    assert names == ["clarifications", "plan", "milestone:M1"]
    assert "step:M1-S01" not in names
    assert "human_gate: true at scale 'ask'" in out


def test_ensure_gates_still_adds_a_step_gate_at_project_scale(tmp_path, fixture_repo):
    """Control: the ask-only carve-out does not leak into the unscaled default."""
    steps = [step("M1-S01", "M1", human_gate=True)]
    plan = plan_dict(steps, human_gates=[])
    path = write_plan_file(tmp_path / "b", plan)
    assert run("ensure-gates", str(path), "--repo-root", str(fixture_repo)) == 0
    names = [g["name"] for g in json.loads(path.read_text())["human_gates"]]
    assert "step:M1-S01" in names


def test_gate_go_on_ask_writes_clarifications_and_plan_together(tmp_path, fixture_repo):
    steps = [step("M1-S01", "M1", human_gate=False)]
    plan = plan_dict(steps, scale="ask", status="verified")
    path = write_plan_file(tmp_path / "b", plan)
    assert run("gate", str(path), "go", "approve", "--by", "pranav",
               "--at", "2026-09-05T10:00:00Z", "--notes", "defaults accepted",
               "--repo-root", str(fixture_repo)) == 0
    after = json.loads(path.read_text())
    gates = {g["name"]: g for g in after["human_gates"]}
    assert gates["clarifications"]["status"] == "approved"
    assert gates["clarifications"]["by"] == "pranav"
    assert gates["clarifications"]["at"] == "2026-09-05T10:00:00Z"
    assert gates["clarifications"]["notes"] == "defaults accepted"
    assert gates["plan"]["status"] == "approved"
    assert gates["plan"]["by"] == "pranav"
    assert gates["plan"]["at"] == "2026-09-05T10:00:00Z"
    assert gates["plan"]["notes"] == "defaults accepted"
    assert after["status"] == "approved"


def test_gate_go_respects_preconditions_in_order_clarifications_then_plan(tmp_path, fixture_repo):
    """An open blocking clarification stops 'go' before the plan gate is even attempted."""
    steps = [step("M1-S01", "M1")]
    plan = plan_dict(steps, scale="ask", status="verified",
                     clarifications=[{"id": "Q1", "question": "Which profiles are exempt?",
                                      "kind": "blocking", "status": "open"}])
    path = write_plan_file(tmp_path / "b", plan)
    rc = run("gate", str(path), "go", "approve", "--by", "pranav", "--repo-root", str(fixture_repo))
    assert rc == 1
    after = json.loads(path.read_text())
    gates = {g["name"]: g for g in after["human_gates"]}
    assert gates["clarifications"]["status"] == "pending", "nothing is written once the first record refuses"
    assert gates["plan"]["status"] == "pending"
    assert after["status"] == "verified"


def test_gate_go_refuses_atomically_when_plan_is_not_verified(tmp_path, fixture_repo):
    """A half-applied 'go' is a bug: either both records land, or neither does.

    'clarifications' has nothing stopping its own approval here (no blocking
    clarification at all), but 'plan' requires build status 'verified' and
    this plan is still 'clarifying'. The old, non-atomic implementation wrote
    'clarifications' -> approved BEFORE discovering that 'plan' would refuse,
    leaving the alias half-applied on disk. The fix checks every member's
    precondition against one snapshot before writing any of them.
    """
    steps = [step("M1-S01", "M1", human_gate=False)]
    plan = plan_dict(steps, scale="ask", status="clarifying")  # clarifications: []
    path = write_plan_file(tmp_path / "b", plan)
    before = path.read_bytes()
    rc = run("gate", str(path), "go", "approve", "--by", "pranav", "--repo-root", str(fixture_repo))
    assert rc == 1
    assert path.read_bytes() == before, "nothing may be written when any alias member refuses"
    after = json.loads(path.read_text())
    gates = {g["name"]: g for g in after["human_gates"]}
    assert gates["clarifications"]["status"] == "pending"
    assert gates["plan"]["status"] == "pending"
    assert after["status"] == "clarifying"


def test_gate_go_and_accept_refuse_outside_ask_scale(tmp_path, fixture_repo, capsys):
    steps = [step("M1-S01", "M1")]
    for scale_kwargs in ({}, {"scale": "project"}, {"scale": "feature"}):
        label = scale_kwargs.get("scale", "absent")
        plan = plan_dict(steps, status="verified", **scale_kwargs)
        path = write_plan_file(tmp_path / f"b-{label}", plan)
        capsys.readouterr()
        assert run("gate", str(path), "go", "approve", "--by", "pranav",
                   "--repo-root", str(fixture_repo)) == 1
        assert run("gate", str(path), "accept", "approve", "--by", "pranav",
                   "--repo-root", str(fixture_repo)) == 1
        after = json.loads(path.read_text())
        assert all(g["status"] == "pending" for g in after["human_gates"]), \
            f"scale={label}: go/accept must not write anything"


def test_gate_go_error_names_the_actual_scale(tmp_path, fixture_repo, capsys):
    steps = [step("M1-S01", "M1")]
    plan = plan_dict(steps, status="verified")  # no 'scale' key at all
    path = write_plan_file(tmp_path / "b", plan)
    capsys.readouterr()
    rc = run("gate", str(path), "go", "approve", "--by", "pranav", "--repo-root", str(fixture_repo))
    assert rc == 1
    err = capsys.readouterr().err
    assert "'project'" in err, "absent scale is 'project' by contract, and the error should say so"

    plan2 = plan_dict(steps, status="verified", scale="feature")
    path2 = write_plan_file(tmp_path / "b2", plan2)
    capsys.readouterr()
    rc2 = run("gate", str(path2), "accept", "approve", "--by", "pranav", "--repo-root", str(fixture_repo))
    assert rc2 == 1
    err2 = capsys.readouterr().err
    assert "'feature'" in err2


def test_gate_go_then_accept_on_ask_takes_the_build_to_done(tmp_path, fixture_repo):
    steps = [step("M1-S01", "M1", human_gate=False)]
    plan = plan_dict(steps, scale="ask", status="verified")
    path = write_plan_file(tmp_path / "b", plan)
    assert run("gate", str(path), "go", "approve", "--by", "pranav",
               "--at", "2026-09-05T10:00:00Z", "--repo-root", str(fixture_repo)) == 0
    advance(path, fixture_repo, "M1-S01")
    assert run("gate", str(path), "accept", "approve", "--by", "pranav",
               "--at", "2026-09-05T11:00:00Z", "--repo-root", str(fixture_repo)) == 0
    after = json.loads(path.read_text())
    gate = next(g for g in after["human_gates"] if g["name"] == "milestone:M1")
    assert gate["status"] == "approved"
    assert gate["by"] == "pranav"
    assert gate["at"] == "2026-09-05T11:00:00Z"
    assert after["status"] == "done"


def test_status_prints_scale_on_the_build_mode_line(tmp_path, fixture_repo, capsys):
    steps = [step("M1-S01", "M1")]
    plan = plan_dict(steps, scale="ask")
    path = write_plan_file(tmp_path / "b", plan)
    capsys.readouterr()
    assert run("status", str(path), "--repo-root", str(fixture_repo)) == 0
    out = capsys.readouterr().out
    line = next(l for l in out.splitlines() if l.startswith("build mode:"))
    assert "scale: ask" in line


def test_status_prints_project_as_the_effective_default_scale(tmp_path, fixture_repo, capsys):
    steps = [step("M1-S01", "M1")]
    plan = plan_dict(steps)  # no 'scale' key
    path = write_plan_file(tmp_path / "b", plan)
    capsys.readouterr()
    assert run("status", str(path), "--repo-root", str(fixture_repo)) == 0
    out = capsys.readouterr().out
    line = next(l for l in out.splitlines() if l.startswith("build mode:"))
    assert "scale: project" in line


def test_status_prints_verification_line_when_plan_rejected(tmp_path, fixture_repo, capsys):
    """(b): a rejected plan's blockers live in `verification.blockers`, not in

    any step's status — this plan's one step is still 'pending' — so the
    bottom 'blockers:' section alone would print 'none' with nothing else
    said about why the plan was rejected. The line under 'status:' carries
    the real answer.
    """
    plan = plan_dict([step("M1-S01", "M1")], status="plan-rejected", verification={
        "status": "plan-rejected",
        "blockers": [{"step": "M1-S01", "problem": "x", "lens": "grounding"},
                     {"step": "M1-S01", "problem": "y", "lens": "testability"}],
    })
    path = write_plan_file(tmp_path / "b", plan)
    capsys.readouterr()
    assert run("status", str(path), "--repo-root", str(fixture_repo)) == 0
    out = capsys.readouterr().out
    lines = out.splitlines()
    status_idx = next(i for i, l in enumerate(lines) if l.startswith("status:"))
    assert lines[status_idx + 1] == "verification: plan-rejected  ·  blockers: M1-S01"
    # "blockers: none" from the bottom section is never the only word said
    # about blockers on a rejected plan.
    bottom_blockers_idx = lines.index("blockers:")
    assert lines[bottom_blockers_idx + 1] == "  none"
    assert any("verification:" in l and "M1-S01" in l for l in lines)


def test_status_prints_verification_line_when_verified(tmp_path, fixture_repo, capsys):
    plan = plan_dict([step("M1-S01", "M1")], status="verified", verification={
        "status": "verified", "blockers": [],
    })
    path = write_plan_file(tmp_path / "b", plan)
    capsys.readouterr()
    assert run("status", str(path), "--repo-root", str(fixture_repo)) == 0
    out = capsys.readouterr().out
    lines = out.splitlines()
    status_idx = next(i for i, l in enumerate(lines) if l.startswith("status:"))
    assert lines[status_idx + 1] == "verification: verified  ·  blockers: none"


def test_status_omits_verification_line_outside_rejected_or_verified(tmp_path, fixture_repo, capsys):
    plan = plan_dict([step("M1-S01", "M1")])  # status: planned
    path = write_plan_file(tmp_path / "b", plan)
    capsys.readouterr()
    assert run("status", str(path), "--repo-root", str(fixture_repo)) == 0
    out = capsys.readouterr().out
    assert "verification:" not in out


def test_set_plan_allowed_at_ask_scale_while_clarifying_with_blocking_answered(
        tmp_path, fixture_repo):
    """§ 3.1's worked example: answer -> planner -> verifier -> `gate go`.

    The planner runs while status is still 'clarifying' and gate
    'clarifications' is still 'pending' — there is no earlier point at which
    G1 gets approved on its own at scale 'ask'. That is fine as long as every
    blocking question already has an answer; an open *informational*
    question must not stand in the way.
    """
    steps = [step("M1-S01", "M1", human_gate=False)]
    plan = plan_dict(steps, status="clarifying", scale="ask", clarifications=[
        {"id": "Q1", "question": "Retroactive to existing records?", "kind": "blocking",
         "status": "answered", "answer": "No, new records only."},
        {"id": "Q2", "question": "Any nice-to-have reporting?", "kind": "informational",
         "status": "open"},
    ])
    path = write_plan_file(tmp_path / "b", plan)
    body = write_json(tmp_path / "plan-body.json", {"decisions": []})
    assert run("set-plan", str(path), "--file", str(body),
               "--repo-root", str(fixture_repo)) == 0
    after = json.loads(path.read_text())
    assert after["status"] == "planned"
    gates = {g["name"]: g for g in after["human_gates"]}
    assert gates["clarifications"]["status"] == "pending", "G1 is still signed later, by `gate go`"


def test_set_plan_refused_at_ask_scale_with_an_open_blocking_clarification(
        tmp_path, fixture_repo, capsys):
    steps = [step("M1-S01", "M1", human_gate=False)]
    plan = plan_dict(steps, status="clarifying", scale="ask", clarifications=[
        {"id": "Q1", "question": "Retroactive to existing records?", "kind": "blocking",
         "status": "open"},
    ])
    path = write_plan_file(tmp_path / "b", plan)
    body = write_json(tmp_path / "plan-body.json", {"decisions": []})
    before = path.read_bytes()
    capsys.readouterr()
    rc = run("set-plan", str(path), "--file", str(body), "--repo-root", str(fixture_repo))
    err = capsys.readouterr().err
    assert rc == 1
    assert path.read_bytes() == before
    assert "Q1" in err


def test_set_plan_at_project_scale_keeps_todays_rule_ignoring_open_blocking_clarification(
        tmp_path, fixture_repo):
    """Control: the new ask-only guard must not leak into 'feature'/'project'.

    Today's rule for those scales is the frozen-status check alone
    (PLAN_FROZEN_STATUSES) — an open blocking clarification has never
    stopped `set-plan` there, and this fix must not start stopping it now.
    """
    for scale_kwargs in ({}, {"scale": "feature"}):
        label = scale_kwargs.get("scale", "absent")
        steps = [step("M1-S01", "M1")]
        plan = plan_dict(steps, status="clarifying", clarifications=[
            {"id": "Q1", "question": "Retroactive to existing records?", "kind": "blocking",
             "status": "open"},
        ], **scale_kwargs)
        path = write_plan_file(tmp_path / f"b-{label}", plan)
        body = write_json(tmp_path / f"plan-body-{label}.json", {"decisions": []})
        assert run("set-plan", str(path), "--file", str(body),
                   "--repo-root", str(fixture_repo)) == 0, f"scale={label} must be unaffected"


def test_init_force_with_requirement_pointed_at_its_own_file_does_not_crash(
        tmp_path, fixture_repo, requirement, capsys):
    """`init --force` re-run with --requirement == the build's own requirement.md.

    shutil.copyfile(src, dst) raises SameFileError when src and dst resolve to
    the same file on disk — a real shape when a human (or an agent) re-runs
    init against the file init itself wrote on a previous pass.
    """
    build_dir = tmp_path / "b"
    assert run("init", "--build-dir", str(build_dir), "--title", "Test Build",
               "--requirement", str(requirement), "--repo-root", str(fixture_repo),
               "--now", "2026-09-05T09:00:00Z") == 0
    capsys.readouterr()
    rc = run("init", "--build-dir", str(build_dir), "--title", "Test Build",
             "--requirement", str(build_dir / "requirement.md"), "--force",
             "--repo-root", str(fixture_repo), "--now", "2026-09-05T09:05:00Z")
    assert rc == 0
    assert (build_dir / "requirement.md").read_text() == requirement.read_text()


def test_render_writes_run_md_only_at_ask_scale(tmp_path, fixture_repo):
    steps = [step("M1-S01", "M1")]

    plan_ask = plan_dict(steps, scale="ask")
    path_ask = write_plan_file(tmp_path / "ask", plan_ask)
    assert run("render", str(path_ask), "--repo-root", str(fixture_repo)) == 0
    assert (path_ask.parent / "RUN.md").is_file()

    for scale_kwargs in ({}, {"scale": "feature"}, {"scale": "project"}):
        label = scale_kwargs.get("scale", "absent")
        plan = plan_dict(steps, **scale_kwargs)
        path = write_plan_file(tmp_path / f"other-{label}", plan)
        assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
        assert not (path.parent / "RUN.md").exists(), f"scale={label} must not get a RUN.md"


def test_run_md_is_byte_deterministic_across_two_renders(tmp_path, fixture_repo):
    steps = [step("M1-S01", "M1",
                  tests=[{"type": "xml", "description": "every artefact parses"},
                         {"type": "manual", "description": "admin confirms the fault path emails"}])]
    plan = plan_dict(steps, scale="ask", clarifications=[
        {"id": "Q1", "question": "Which profiles are exempt?", "kind": "informational",
         "status": "answered", "answer": "none", "proposed_default": "none",
         "default_source": "proposed_default"},
        {"id": "Q2", "question": "Does it fire on insert too?", "kind": "blocking",
         "status": "deferred", "answer": "DEFER: ask the PM"},
    ])
    path = write_plan_file(tmp_path / "b", plan)
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    first = (path.parent / "RUN.md").read_bytes()
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    second = (path.parent / "RUN.md").read_bytes()
    assert first == second


def test_run_md_covers_the_required_sections(tmp_path, fixture_repo):
    steps = [step("M1-S01", "M1",
                  tests=[{"type": "xml", "description": "every artefact parses"},
                         {"type": "manual", "description": "admin confirms the fault path emails"}])]
    plan = plan_dict(steps, scale="ask", org={"alias": "uat-sandbox"}, build_mode="org-connected",
                     clarifications=[
                         {"id": "Q1", "question": "Which profiles are exempt?",
                          "kind": "informational", "status": "answered", "answer": "none",
                          "proposed_default": "none", "default_source": "proposed_default"},
                         {"id": "Q2", "question": "Does it fire on insert too?",
                          "kind": "blocking", "status": "deferred", "answer": "DEFER: ask the PM"},
                     ])
    # alpha-designer declares requires_org: false, so org-connected build_mode
    # does not change which agent may own the step.
    path = write_plan_file(tmp_path / "b", plan)
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    text = (path.parent / "RUN.md").read_text()

    assert "M1-S01" in text
    assert "alpha-designer" in text
    assert "admin/fake-object-design" in text
    assert "missing" in text  # the declared output has not been written yet
    assert "admin confirms the fault path emails" in text  # manual acceptance line
    assert "none" in text and "proposed_default" in text  # default applied, with its source
    assert "ask the PM" in text  # deferred question
    assert "clarifications" in text and "milestone:M1" in text  # gate states
    assert "python3 scripts/mock_deploy.py plan.json --org-alias uat-sandbox --milestone M1" in text

    write_outputs(path, "M1-S01")
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    text2 = (path.parent / "RUN.md").read_text()
    assert "exists" in text2


def test_run_md_splits_defaults_answers_deferred_and_open(tmp_path, fixture_repo):
    """A human-written answer must not be tagged as a default (driver's-log
    follow-up A): only a row with a real ``default_source`` — anything but
    the literal marker ``"none"`` requirements-clarifier stamps when it had
    no proposed default — belongs under 'Defaults applied'. Human answers
    land in a separate 'Answers given' section with no source tag, deferred
    rows keep 'Deferred questions', and still-open rows (the state a
    pre-fix ask build can be stuck in) get their own 'Open questions'."""
    steps = [step("M1-S01", "M1")]
    plan = plan_dict(steps, scale="ask", clarifications=[
        # A real default, applied and left as-is.
        {"id": "Q1", "question": "What should the error say?", "kind": "informational",
         "status": "answered", "answer": "Use the standard message.",
         "proposed_default": "Use the standard message.", "default_source": "skill-guidance"},
        # A human answer with no proposed default (default_source: "none").
        {"id": "Q2", "question": "Does Amount roll up from line items?", "kind": "blocking",
         "status": "answered", "answer": "No, it is typed directly.",
         "default_source": "none"},
        # A blocking question the human deferred.
        {"id": "Q3", "question": "Does it fire on insert too?", "kind": "blocking",
         "status": "deferred", "answer": "DEFER: ask the PM"},
        # An informational row still open, with a proposed default on file.
        {"id": "Q4", "question": "Is Amount on every layout?", "kind": "informational",
         "status": "open", "proposed_default": "Yes, on the standard layout."},
    ])
    path = write_plan_file(tmp_path / "b", plan)
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    text = (path.parent / "RUN.md").read_text()

    def section(name: str) -> str:
        marker = f"## {name}"
        start = text.index(marker) + len(marker)
        end = text.index("\n## ", start)
        return text[start:end]

    defaults = section("Defaults applied")
    assert "`Q1`" in defaults and "(source: skill-guidance)" in defaults
    assert "`Q2`" not in defaults
    assert "(source: none)" not in text

    answers_given = section("Answers given")
    assert "`Q2`" in answers_given and "No, it is typed directly." in answers_given
    assert "(source:" not in answers_given
    assert "`Q1`" not in answers_given

    deferred = section("Deferred questions")
    assert "`Q3`" in deferred and "ask the PM" in deferred

    open_qs = section("Open questions")
    assert "`Q4`" in open_qs
    assert "(proposed default: Yes, on the standard layout.)" in open_qs
    assert "`Q1`" not in open_qs and "`Q2`" not in open_qs and "`Q3`" not in open_qs


def test_run_md_shows_the_latest_test_result_when_present(tmp_path, fixture_repo):
    steps = [step("M1-S01", "M1")]
    plan = plan_dict(steps, scale="ask")
    path = write_plan_file(tmp_path / "b", plan)
    write_results(path, "M1-S01", passed=True)
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    text = (path.parent / "RUN.md").read_text()
    assert "results.json" in text
    assert "passed=true" in text


def test_run_md_renders_one_line_per_recorded_test_result(tmp_path, fixture_repo):
    """§ 3.1 promises RUN.md carries the checker commands with their exit
    codes, not just the aggregate `passed=` line. A minimal results.json
    (just step_id/passed, no `results[]`) must still render — this is the
    real shape step-tester writes: `results[]` for machine-run tests
    (xml/manifest/checker) and `skipped_manual[]` as bare strings for tests
    it could not run, synthesised here into a `manual-deferred` verdict."""
    steps = [step("M1-S01", "M1")]
    plan = plan_dict(steps, scale="ask")
    path = write_plan_file(tmp_path / "b", plan)
    write_json(path.parent / "tests" / "M1-S01" / "results.json", {
        "step_id": "M1-S01",
        "ran": ["xml", "manifest", "skills/admin/fake-object-design/scripts/check_fake.py"],
        "passed": False,
        "failed": ["skills/admin/fake-object-design/scripts/check_fake.py"],
        "skipped_manual": ["Given X, when Y, then Z."],
        "results": [
            {"name": "xml", "type": "xml",
             "runner": "ElementTree parse of every *.xml/*-meta.xml under artefacts/M1-S01/",
             "exit_code": None, "verdict": "pass"},
            {"name": "manifest", "type": "manifest",
             "runner": "two-way consistency check", "exit_code": None, "verdict": "pass"},
            {"name": "skills/admin/fake-object-design/scripts/check_fake.py", "type": "checker",
             "runner": "python3 skills/admin/fake-object-design/scripts/check_fake.py "
                       "--manifest-dir artefacts/M1-S01",
             "exit_code": 1, "verdict": "fail"},
        ],
    })
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    text = (path.parent / "RUN.md").read_text()

    assert "Recorded results (`tests/M1-S01/results.json`):" in text
    assert ("- type=xml label=ElementTree parse of every *.xml/*-meta.xml under "
            "artefacts/M1-S01/ exit=null verdict=pass") in text
    assert "- type=manifest label=two-way consistency check exit=null verdict=pass" in text
    assert ("- type=checker command=python3 skills/admin/fake-object-design/scripts/"
            "check_fake.py --manifest-dir artefacts/M1-S01 exit=1 verdict=fail") in text
    assert "- type=manual label=Given X, when Y, then Z. exit=null verdict=manual-deferred" in text
    # the aggregate line is kept, not replaced
    assert "Latest test run (`tests/M1-S01/results.json`): passed=false" in text

    # byte-deterministic: re-rendering the same plan.json changes nothing
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    assert (path.parent / "RUN.md").read_text() == text


def test_run_md_omits_recorded_results_when_results_json_has_no_results_array(
        tmp_path, fixture_repo):
    """The minimal / legacy shape (`write_results` writes only step + passed)
    must not crash and must not fabricate result lines out of nothing."""
    steps = [step("M1-S01", "M1")]
    plan = plan_dict(steps, scale="ask")
    path = write_plan_file(tmp_path / "b", plan)
    write_results(path, "M1-S01", passed=True)
    assert run("render", str(path), "--repo-root", str(fixture_repo)) == 0
    text = (path.parent / "RUN.md").read_text()
    assert "Recorded results" not in text
    assert "Latest test run (`tests/M1-S01/results.json`): passed=true" in text


def test_help_mentions_the_new_scale_flag_and_aliases():
    import contextlib
    import io

    expectations = (
        (["init", "--help"], "--scale"),
        (["validate", "--help"], "3.1"),
        (["ensure-gates", "--help"], "ask"),
        (["gate", "--help"], "go"),
        (["gate", "--help"], "accept"),
        (["render", "--help"], "RUN.md"),
        (["status", "--help"], "scale"),
        (["set-scale", "--help"], "--force"),
        (["set-scale", "--help"], "intake"),
    )
    for argv, needle in expectations:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with pytest.raises(SystemExit):
                build_plan.main(argv)
        assert needle in buf.getvalue(), f"{argv}: --help does not mention {needle!r}"
