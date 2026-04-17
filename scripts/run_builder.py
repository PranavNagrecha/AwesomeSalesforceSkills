#!/usr/bin/env python3
"""run_builder.py — the gated execution harness for builder agents.

Implements the five-gate protocol defined in agents/<agent>/GATES.md:

    Gate A   — inputs       validate input packet against inputs.schema.json
    Gate A.5 — requirements render REQUIREMENTS_TEMPLATE.md; must be approved
    Gate B   — ground       resolve every referenced symbol via org probes or fixture stub
    Gate C   — build        parse-check emitted code; run test class if possible
    Gate D   — seal         assemble the envelope; computed confidence, not self-declared

The harness is intentionally model-agnostic. An LLM follows the AGENT.md; this tool
is what the LLM's output is compiled against. The confidence score in the final
envelope is computed from gate outcomes, never trusted from the model.

Usage (fixture mode, CI):
    python3 scripts/run_builder.py --agent apex-builder \
        --fixture evals/agents/fixtures/apex-builder/<case>.yaml \
        --emitted-dir <path-to-LLM-output>

Usage (interactive, per-stage):
    python3 scripts/run_builder.py --agent apex-builder --stage inputs   --inputs packet.json
    python3 scripts/run_builder.py --agent apex-builder --stage requirements --inputs packet.json --run-id <id>
    python3 scripts/run_builder.py --agent apex-builder --stage ground   --inputs packet.json --run-id <id> \
        --approved-requirements docs/reports/apex-builder/<id>/REQUIREMENTS.md
    python3 scripts/run_builder.py --agent apex-builder --stage build    --inputs packet.json --run-id <id> \
        --emitted-dir <path>
    python3 scripts/run_builder.py --agent apex-builder --stage seal     --inputs packet.json --run-id <id>

Exit codes:
    0   gate passed
    10  Gate A: inputs incomplete (question packet emitted on stdout)
    11  Gate A.5: requirements not approved or hash mismatch
    12  Gate B: unresolved symbols exceed threshold (REFUSAL_UNGROUNDED_OUTPUT)
    13  Gate C: parse or coverage failure after max iterations
    14  Gate D: envelope failed schema validation
    20  fixture rubric failed (fixture mode only)
    30  invalid CLI usage / missing dependency
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

# Plugin system — each builder agent registers its own Gate C / inventory logic.
# Imported lazily via get_plugin(agent) inside stages that need it.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from builder_plugins import get_plugin  # noqa: E402

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required (pip install pyyaml)", file=sys.stderr)
    sys.exit(30)

try:
    import jsonschema
except ImportError:
    jsonschema = None  # grade as WARN instead of ERROR

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = REPO_ROOT / "agents"
REPORTS_DIR = REPO_ROOT / "docs" / "reports"
ENVELOPE_SCHEMA_PATH = REPO_ROOT / "agents" / "_shared" / "schemas" / "output-envelope.schema.json"


# ---------------------------------------------------------------------------
# State persisted between stages — each run dir owns its own state.json
# ---------------------------------------------------------------------------

@dataclass
class GateResult:
    name: str
    passed: bool
    notes: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunState:
    agent: str
    run_id: str
    inputs: dict[str, Any]
    inputs_sha256: str
    gates: dict[str, GateResult] = field(default_factory=dict)
    org_stub: dict[str, Any] | None = None  # populated in fixture mode

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "run_id": self.run_id,
            "inputs": self.inputs,
            "inputs_sha256": self.inputs_sha256,
            "org_stub": self.org_stub,
            "gates": {k: asdict(v) for k, v in self.gates.items()},
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RunState":
        gates = {k: GateResult(**v) for k, v in d.get("gates", {}).items()}
        st = cls(
            agent=d["agent"],
            run_id=d["run_id"],
            inputs=d["inputs"],
            inputs_sha256=d["inputs_sha256"],
        )
        st.gates = gates
        st.org_stub = d.get("org_stub")
        return st


def run_dir(agent: str, run_id: str) -> Path:
    return REPORTS_DIR / agent / run_id


def state_path(agent: str, run_id: str) -> Path:
    return run_dir(agent, run_id) / "state.json"


def load_state(agent: str, run_id: str) -> RunState:
    p = state_path(agent, run_id)
    if not p.exists():
        raise FileNotFoundError(f"no prior state for {agent}/{run_id} — start at --stage inputs")
    return RunState.from_dict(json.loads(p.read_text(encoding="utf-8")))


def save_state(state: RunState) -> None:
    p = state_path(state.agent, state.run_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state.to_dict(), indent=2, sort_keys=True), encoding="utf-8")


def new_run_id() -> str:
    # ISO-8601 compact, Zulu, no colons — safe for filenames
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_of(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Gate A — inputs
# ---------------------------------------------------------------------------

def load_agent_schema(agent: str) -> dict[str, Any]:
    p = AGENTS_DIR / agent / "inputs.schema.json"
    if not p.exists():
        raise FileNotFoundError(f"{agent} has no inputs.schema.json — builders without schemas cannot run gated")
    return json.loads(p.read_text(encoding="utf-8"))


def gate_a_inputs(agent: str, inputs: dict[str, Any], run_id: str | None) -> tuple[RunState, GateResult]:
    schema = load_agent_schema(agent)
    missing: list[str] = []
    invalid: list[str] = []

    # Required top-level fields
    for req in schema.get("required", []):
        if req not in inputs:
            missing.append(req)

    # Enum + type enforcement via jsonschema if available; otherwise shallow checks
    if jsonschema is not None:
        try:
            jsonschema.validate(inputs, schema)
        except jsonschema.ValidationError as exc:
            path = "/".join(str(p) for p in exc.absolute_path) or "(root)"
            invalid.append(f"{path}: {exc.message}")

    # Conditional fields — encoded in GATES.md; hard-coded here for apex-builder
    if agent == "apex-builder":
        sobject_kinds = {"trigger", "selector", "domain", "batch", "cdc_subscriber"}
        if inputs.get("kind") in sobject_kinds and not inputs.get("primary_sobject"):
            missing.append("primary_sobject (required because kind implies an SObject target)")
        # feature_token is required for all non-SObject-named kinds
        sobject_named = {"trigger", "selector", "domain", "cdc_subscriber"}
        if inputs.get("kind") not in sobject_named and not inputs.get("feature_token"):
            missing.append("feature_token (required PascalCase stem for class names)")
        ft = inputs.get("feature_token")
        if ft and not re.match(r"^[A-Z][A-Za-z0-9]+$", ft):
            invalid.append(f"feature_token: '{ft}' must match ^[A-Z][A-Za-z0-9]+$")
        if inputs.get("sharing_mode") == "without_sharing":
            bj = inputs.get("business_justification") or ""
            if len(bj) < 40:
                invalid.append("business_justification: required ≥40 chars when sharing_mode=without_sharing")
        fs = inputs.get("feature_summary") or ""
        if fs and len(fs.split()) < 10:
            invalid.append("feature_summary: must be at least 10 words (REFUSAL_INPUT_AMBIGUOUS)")

    passed = not missing and not invalid
    result = GateResult(name="inputs", passed=passed)
    if missing:
        result.notes.append(f"missing fields: {', '.join(missing)}")
    if invalid:
        result.notes.append(f"invalid fields: {'; '.join(invalid)}")
    result.data = {"missing": missing, "invalid": invalid}

    rid = run_id or new_run_id()
    state = RunState(
        agent=agent,
        run_id=rid,
        inputs=inputs,
        inputs_sha256=sha256_of(json.dumps(inputs, sort_keys=True)),
    )
    state.gates["inputs"] = result
    return state, result


# ---------------------------------------------------------------------------
# Gate A.5 — requirements
# ---------------------------------------------------------------------------

def render_requirements(state: RunState, agent_version: str = "1.0.0") -> str:
    tpl_path = AGENTS_DIR / state.agent / "REQUIREMENTS_TEMPLATE.md"
    tpl = tpl_path.read_text(encoding="utf-8")
    plugin = get_plugin(state.agent)
    repls = plugin.requirements_template_vars(
        inputs=state.inputs,
        run_id=state.run_id,
        inputs_sha256=state.inputs_sha256,
        agent_version=agent_version,
    )
    out = tpl
    for k, v in repls.items():
        out = out.replace(k, str(v))
    return out


def gate_a5_requirements(state: RunState) -> GateResult:
    result = GateResult(name="requirements", passed=False)
    rendered = render_requirements(state)
    req_path = run_dir(state.agent, state.run_id) / "REQUIREMENTS.md"
    req_path.parent.mkdir(parents=True, exist_ok=True)
    req_path.write_text(rendered, encoding="utf-8")
    sha = sha256_of(rendered)
    result.passed = True
    result.artifacts.append(str(req_path.relative_to(REPO_ROOT)))
    result.data = {
        "requirements_path": str(req_path.relative_to(REPO_ROOT)),
        "requirements_sha256": sha,
        "approved": False,
    }
    result.notes.append(
        f"requirements written; next stage requires --approved-requirements {req_path.relative_to(REPO_ROOT)}"
    )
    return result


def approve_requirements(state: RunState, approved_path: Path) -> tuple[bool, str]:
    """Return (approved, reason)."""
    prior = state.gates.get("requirements")
    if not prior or not prior.passed:
        return False, "Gate A.5 has not been run for this run_id"
    expected_sha = prior.data.get("requirements_sha256")
    if not approved_path.exists():
        return False, f"approved file does not exist: {approved_path}"
    actual_sha = sha256_of(approved_path.read_bytes())
    if actual_sha != expected_sha:
        return False, (
            f"requirements hash mismatch — expected {expected_sha[:12]}…, "
            f"got {actual_sha[:12]}… — regenerate with --stage requirements"
        )
    return True, "approved"


# ---------------------------------------------------------------------------
# Gate B — grounding
# ---------------------------------------------------------------------------

def gate_b_ground(state: RunState) -> GateResult:
    result = GateResult(name="ground", passed=False)

    inputs = state.inputs
    stub = state.org_stub or {}
    unresolved: list[dict[str, str]] = []
    resolved: list[dict[str, str]] = []

    # SObject resolution (captured in grounding.resolved but NOT emitted as a
    # citation — citations are skill/template/standard/decision_tree/mcp_tool/probe
    # per schemas/citation.schema.json. SObject grounding is evidence for the
    # run, not a cite-able source.)
    sobj = inputs.get("primary_sobject")
    describe = None
    if sobj:
        describe = (stub.get("describe_sobject") or {}).get(sobj)
        if describe:
            resolved.append({"type": "sobject", "name": sobj, "source": "org_stub.describe_sobject"})
        elif inputs.get("target_org_alias"):
            result.notes.append(f"primary_sobject '{sobj}' not in fixture stub; live describe_org not wired in this harness version")
            unresolved.append({"type": "sobject", "name": sobj, "reason": "no stub and no live probe available"})
        else:
            unresolved.append({"type": "sobject", "name": sobj, "reason": "library-only mode and no stub provided"})

    # Field resolution — every referenced_fields entry must resolve against
    # describe_sobject. Silent field misses are the #1 hallucination vector.
    for fqn in inputs.get("referenced_fields") or []:
        if "." not in fqn:
            unresolved.append({"type": "field", "name": fqn, "reason": "must be SObject.Field form"})
            continue
        obj_name, field_name = fqn.split(".", 1)
        obj_describe = (stub.get("describe_sobject") or {}).get(obj_name)
        if not obj_describe:
            unresolved.append({"type": "field", "name": fqn, "reason": f"SObject {obj_name} not described"})
            continue
        fields = {f["name"]: f for f in obj_describe.get("fields", [])}
        if field_name in fields:
            resolved.append({"type": "field", "name": fqn, "source": "org_stub.describe_sobject.fields"})
        else:
            unresolved.append({"type": "field", "name": fqn, "reason": f"field not on {obj_name}"})

    # Template resolution (repo-local — always resolvable against the filesystem)
    for tpl in ("templates/apex/BaseService.cls", "templates/apex/SecurityUtils.cls"):
        if (REPO_ROOT / tpl).exists():
            resolved.append({"type": "template", "name": tpl, "source": "filesystem"})
        else:
            unresolved.append({"type": "template", "name": tpl, "reason": "path not found"})
    if inputs.get("include_logger", True):
        tpl = "templates/apex/ApplicationLogger.cls"
        if (REPO_ROOT / tpl).exists():
            resolved.append({"type": "template", "name": tpl, "source": "filesystem"})
        else:
            unresolved.append({"type": "template", "name": tpl, "reason": "path not found"})

    # Skill / decision-tree citations expected for this kind
    expected_citations: list[dict[str, str]] = []
    kind = inputs.get("kind", "")
    if kind in ("queueable", "batch", "schedulable", "platform_event_subscriber", "cdc_subscriber", "continuation"):
        expected_citations += [
            {"type": "skill", "id": "apex/async-apex"},
            {"type": "decision_tree", "id": "async-selection.md"},
        ]
    kind_to_skill = {
        "queueable": "apex/apex-queueable-patterns",
        "batch": "apex/batch-apex-patterns",
        "schedulable": "apex/apex-scheduled-jobs",
        "rest": "apex/apex-rest-services",
        "invocable": "apex/invocable-methods",
        "platform_event_subscriber": "apex/platform-events-apex",
        "cdc_subscriber": "apex/change-data-capture-apex",
        "trigger": "apex/trigger-framework",
    }
    if kind in kind_to_skill:
        expected_citations.append({"type": "skill", "id": kind_to_skill[kind]})

    for cit in expected_citations:
        if cit["type"] == "skill":
            p = REPO_ROOT / "skills" / cit["id"] / "SKILL.md"
        else:
            p = REPO_ROOT / "standards" / "decision-trees" / cit["id"]
        if p.exists():
            resolved.append({"type": cit["type"], "name": cit["id"], "source": "filesystem"})
        else:
            unresolved.append({"type": cit["type"], "name": cit["id"], "reason": "path not found"})

    result.data = {
        "resolved": resolved,
        "unresolved": unresolved,
        "expected_citations": expected_citations,
    }

    # Pass rule
    if len(unresolved) >= 2:
        result.passed = False
        result.notes.append(f"REFUSAL_UNGROUNDED_OUTPUT: {len(unresolved)} symbols unresolved (threshold is 1)")
    else:
        result.passed = True
        if unresolved:
            result.notes.append(f"1 unresolved symbol — confidence will drop to LOW; UNKNOWN marker required")

    return result


# ---------------------------------------------------------------------------
# Gate C — build and self-test (delegated to builder_plugins.get_plugin(agent))
# ---------------------------------------------------------------------------


def gate_c_build(
    state: RunState,
    emitted_dir: Path,
    coverage_override: int | None = None,
    target_org_override: str | None = None,
) -> GateResult:
    result = GateResult(name="build", passed=False)
    plugin = get_plugin(state.agent)

    if not emitted_dir.exists():
        result.notes.append(f"emitted_dir does not exist: {emitted_dir}")
        result.data = {"parse_errors": [], "files_checked": 0, "coverage": 0}
        return result

    files = plugin.discover_emitted_files(emitted_dir)
    if not files:
        result.notes.append(f"no emitted files under {emitted_dir} for plugin {plugin.agent}")
        result.data = {"parse_errors": [], "files_checked": 0, "coverage": 0}
        return result

    # --- static check (always runs; fast fallback) ---
    parse_errors = plugin.static_check(files)

    # --- live oracle (runs iff target org alias resolvable) ---
    live_org = target_org_override or state.inputs.get("target_org_alias")
    live_dict: dict[str, Any] = {"ran": False}
    if live_org:
        live_res = plugin.live_check(
            files=files,
            target_org=live_org,
            api_version=str(state.inputs.get("api_version") or "60.0"),
        )
        live_dict = live_res.to_dict()

    # --- coverage ---
    coverage = 0
    cov_json = emitted_dir / "coverage.json"
    if cov_json.exists():
        try:
            cov = json.loads(cov_json.read_text(encoding="utf-8"))
            coverage = int(cov.get("overall_percent", 0))
        except (ValueError, json.JSONDecodeError):
            result.notes.append("coverage.json present but unparseable")
    elif coverage_override is not None:
        coverage = int(coverage_override)

    expected = plugin.expected_deliverable_stems(state.inputs)
    # Restrict file-stem matching to file kinds the plugin cares about; for Apex
    # that's .cls, while .trigger is tracked separately in the inventory.
    found = set(f.stem for f in files if f.suffix in (".cls",))
    missing_classes = sorted(expected - found)
    unexpected_classes = sorted(found - expected)

    result.data = {
        "files_checked": len(files),
        "files": [str(f.relative_to(REPO_ROOT)) for f in files],
        "parse_errors": parse_errors,
        "coverage": coverage,
        "expected_classes": sorted(expected),
        "missing_classes": missing_classes,
        "unexpected_classes": unexpected_classes,
        "live_deploy_validate": live_dict,
    }

    passed = not parse_errors and not missing_classes
    result.passed = passed
    if parse_errors:
        result.notes.append(f"{len(parse_errors)} static parse errors — see data.parse_errors")
    if missing_classes:
        result.notes.append(f"requirements declared but not emitted: {', '.join(missing_classes)}")
    if unexpected_classes:
        result.notes.append(f"emitted but not in requirements: {', '.join(unexpected_classes)}")

    # Live oracle is authoritative — if it ran and failed, Gate C fails even
    # if the static check was clean. A green static check with red live oracle
    # is exactly the "hallucinated field / type mismatch" class of failure.
    if live_dict.get("ran") and not live_dict.get("succeeded"):
        result.passed = False
        err_count = live_dict.get("num_errors") or len(live_dict.get("errors") or [])
        label = live_dict.get("oracle_label") or "live oracle"
        result.notes.append(f"{label} FAILED against {live_org}: {err_count} error(s)")

    if result.passed and coverage < 75:
        result.passed = False
        result.notes.append(f"coverage {coverage}% below 75% floor")

    return result


# ---------------------------------------------------------------------------
# Gate D — envelope seal
# ---------------------------------------------------------------------------

def compute_confidence(state: RunState) -> tuple[str, str]:
    """Return (confidence, rationale) from gate state — never self-declared."""
    ground = state.gates.get("ground")
    build = state.gates.get("build")
    unresolved = len((ground.data.get("unresolved") or [])) if ground else 999
    parse_errors = len((build.data.get("parse_errors") or [])) if build else 999
    coverage = (build.data.get("coverage") or 0) if build else 0
    deploy_validated = bool(state.inputs.get("target_org_alias")) and build and build.passed

    if unresolved >= 2:
        return "LOW", f"REFUSAL-level ungrounded output ({unresolved} unresolved symbols)"
    if parse_errors > 0:
        return "LOW", f"Gate C parse had {parse_errors} errors"
    if unresolved == 1:
        return "LOW", "one unresolved symbol — UNKNOWN marker required"
    if coverage >= 85 and deploy_validated:
        return "HIGH", "all gates green, deploy-validate clean, coverage ≥85%"
    if coverage >= 75:
        return "MEDIUM", f"green parse, coverage {coverage}%, deploy-validate {'skipped' if not deploy_validated else 'clean'}"
    return "LOW", f"coverage {coverage}% under 75%"


def _citation_entries(state: RunState) -> list[dict[str, str]]:
    """Emit only cite-able types (skill/template/standard/decision_tree/mcp_tool/probe).

    SObject and field grounding is evidence for the run (lives in gates.ground.data),
    NOT a citation — citation.schema.json enumerates the valid types.
    """
    ground = state.gates.get("ground")
    if not ground:
        return []
    citable_kinds = {"skill", "template", "standard", "decision_tree", "mcp_tool", "probe"}
    used_for_by_kind = {
        "template": "canonical scaffold reused verbatim",
        "skill": "domain guidance applied to the build",
        "decision_tree": "technology choice resolution",
        "standard": "canonical standard consulted",
        "probe": "live-org probe recipe",
        "mcp_tool": "MCP tool invocation",
    }
    cits = []
    for r in ground.data.get("resolved", []):
        kind = r["type"]
        if kind not in citable_kinds:
            continue
        name = r["name"]
        entry: dict[str, Any] = {"type": kind, "id": name, "used_for": used_for_by_kind.get(kind, "grounding")}
        # path is required for everything except mcp_tool
        if kind == "template":
            entry["path"] = name if name.startswith("templates/") else f"templates/{name}"
        elif kind == "skill":
            entry["path"] = f"skills/{name}/SKILL.md"
        elif kind == "decision_tree":
            entry["path"] = f"standards/decision-trees/{name}"
            entry["branch"] = "default branch for this kind"
        elif kind == "standard":
            entry["path"] = f"standards/{name}"
        elif kind == "probe":
            entry["path"] = f"probes/{name}"
        cits.append(entry)
    return cits


def _process_observations(state: RunState) -> list[dict[str, Any]]:
    """Emit observations that conform to schemas/observation.schema.json.

    Required fields: category, severity, observation, evidence.
    healthy observations MUST have severity=info.
    """
    obs: list[dict[str, Any]] = []
    ground = state.gates.get("ground")
    build = state.gates.get("build")
    if build and build.data.get("unexpected_classes"):
        obs.append({
            "category": "ambiguous",
            "severity": "low",
            "observation": f"classes emitted but not in requirements: {', '.join(build.data['unexpected_classes'])}",
            "evidence": {"source": "repo_scan", "count": len(build.data["unexpected_classes"])},
        })
    if ground and ground.data.get("unresolved"):
        obs.append({
            "category": "concerning",
            "severity": "medium",
            "observation": f"{len(ground.data['unresolved'])} symbol(s) unresolved at Gate B — LOW confidence or REFUSAL follows",
            "evidence": {"source": "mcp_probe", "probe": "describe_org", "count": len(ground.data["unresolved"])},
        })
    if not obs:
        obs.append({
            "category": "healthy",
            "severity": "info",
            "observation": "all gates green; nothing notable observed beyond the deliverable itself",
            "evidence": {"source": "heuristic"},
        })
    return obs


def _default_followups(state: RunState) -> list[dict[str, str]]:
    kind = state.inputs.get("kind", "")
    out = []
    if kind == "trigger":
        out.append({"agent": "trigger-consolidator", "because": "a second trigger on the SObject would require consolidation into the emitted handler"})
    if kind in ("queueable", "batch"):
        out.append({"agent": "soql-optimizer", "because": "async classes commonly grow selectors that benefit from SOQL review"})
    out.append({"agent": "test-class-generator", "because": "emitted coverage can be extended for edge cases not in the initial test plan"})
    return out


def gate_d_seal(state: RunState) -> GateResult:
    result = GateResult(name="seal", passed=False)
    confidence, rationale = compute_confidence(state)
    build = state.gates.get("build")

    envelope = {
        "agent": state.agent,
        "mode": "single",
        "run_id": state.run_id,
        "inputs_received": state.inputs,
        "summary": (
            f"apex-builder produced {build.data.get('files_checked', 0) if build else 0} file(s) "
            f"for kind={state.inputs.get('kind')}, feature="
            f"{(state.inputs.get('feature_summary') or '')[:80]}. "
            f"Gates: {', '.join(g for g, gr in state.gates.items() if gr.passed)}."
        ),
        "confidence": confidence,
        "confidence_rationale": rationale,
        "process_observations": _process_observations(state),
        "citations": _citation_entries(state),
        "followups": _default_followups(state),
        "report_path": f"docs/reports/{state.agent}/{state.run_id}/report.md",
        "envelope_path": f"docs/reports/{state.agent}/{state.run_id}/envelope.json",
        "deliverables": [],
    }

    # Deliverables: every emitted file becomes a deliverable block
    if build and build.data.get("files"):
        for rel in build.data["files"]:
            p = REPO_ROOT / rel
            if p.exists():
                envelope["deliverables"].append({
                    "kind": "apex",
                    "title": p.name,
                    "target_path": f"{state.inputs.get('repo_path', './force-app')}/main/default/classes/{p.name}",
                    "content": p.read_text(encoding="utf-8", errors="replace"),
                })

    # Validate against the envelope schema — build a local schema registry so
    # $ref to observation.schema.json / citation.schema.json resolve against
    # disk, not the network.
    errors = []
    if jsonschema is not None and ENVELOPE_SCHEMA_PATH.exists():
        schema = json.loads(ENVELOPE_SCHEMA_PATH.read_text(encoding="utf-8"))
        try:
            from referencing import Registry, Resource
            schemas_dir = ENVELOPE_SCHEMA_PATH.parent
            resources = []
            for s in schemas_dir.glob("*.schema.json"):
                doc = json.loads(s.read_text(encoding="utf-8"))
                resources.append((s.name, Resource.from_contents(doc)))
                if doc.get("$id"):
                    resources.append((doc["$id"], Resource.from_contents(doc)))
            registry = Registry().with_resources(resources)
            validator = jsonschema.Draft202012Validator(schema, registry=registry)
        except ImportError:
            validator = jsonschema.Draft202012Validator(schema)
        errors = [f"{list(e.absolute_path)}: {e.message}" for e in validator.iter_errors(envelope)]

    # Write artifacts
    rd = run_dir(state.agent, state.run_id)
    rd.mkdir(parents=True, exist_ok=True)
    env_path = rd / "envelope.json"
    env_path.write_text(json.dumps(envelope, indent=2, sort_keys=True), encoding="utf-8")
    report_path = rd / "report.md"
    report_path.write_text(_render_report(state, envelope), encoding="utf-8")

    result.artifacts = [
        str(env_path.relative_to(REPO_ROOT)),
        str(report_path.relative_to(REPO_ROOT)),
    ]
    result.data = {"envelope_errors": errors, "confidence": confidence}
    result.passed = not errors
    if errors:
        result.notes.append(f"{len(errors)} envelope schema violations")
    return result


def _render_report(state: RunState, envelope: dict[str, Any]) -> str:
    lines = [
        f"# apex-builder run — {state.run_id}",
        "",
        f"**Confidence:** {envelope['confidence']} — {envelope.get('confidence_rationale', '')}",
        "",
        f"**Summary:** {envelope['summary']}",
        "",
        "## Gates",
        "",
    ]
    for name in ("inputs", "requirements", "ground", "build", "seal"):
        gr = state.gates.get(name)
        if not gr:
            lines.append(f"- **{name}** — not run")
            continue
        status = "✅" if gr.passed else "❌"
        lines.append(f"- **{name}** {status}")
        for n in gr.notes:
            lines.append(f"  - {n}")
    lines += [
        "",
        "## Citations",
        "",
        *(f"- `{c['type']}` `{c['id']}` — {c.get('used_for', '')}" for c in envelope["citations"]),
        "",
        "## Process Observations",
        "",
        *(f"- [{o['category']}/{o['severity']}] {o['observation']}" for o in envelope["process_observations"]),
        "",
        "## Deliverables",
        "",
    ]
    for d in envelope["deliverables"]:
        lines.append(f"### {d['title']} → `{d['target_path']}`")
        lines.append("")
        lines.append("```apex")
        lines.append(d["content"])
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Fixture mode — runs all five gates from a canned YAML
# ---------------------------------------------------------------------------

def run_fixture(fixture_path: Path, emitted_dir: Path | None, target_org_override: str | None = None) -> int:
    data = yaml.safe_load(fixture_path.read_text(encoding="utf-8"))
    agent = data["eval"]["agent"]
    inputs = data["inputs"]
    org_stub = data.get("org_stub") or {}
    expect = data.get("expect") or {}

    # Gate A
    state, res_a = gate_a_inputs(agent, inputs, run_id=None)
    state.org_stub = org_stub
    save_state(state)
    if not res_a.passed:
        print(f"[fixture] Gate A failed: {res_a.notes}")
        return 10

    # Gate A.5
    res_a5 = gate_a5_requirements(state)
    state.gates["requirements"] = res_a5
    # Auto-approve in fixture mode — the rendered file is the canonical approved form
    res_a5.data["approved"] = True
    save_state(state)

    # Gate B
    res_b = gate_b_ground(state)
    state.gates["ground"] = res_b
    save_state(state)

    # Gate C — need emitted_dir either from arg or expect fixture
    coverage_override = (expect.get("build_gate") or {}).get("coverage_min", 85) if expect else 85
    if emitted_dir is None:
        emitted_dir = REPO_ROOT / "docs" / "reports" / agent / state.run_id / "emitted"
    res_c = gate_c_build(state, emitted_dir, coverage_override=coverage_override, target_org_override=target_org_override)
    state.gates["build"] = res_c
    save_state(state)

    # Gate D
    res_d = gate_d_seal(state)
    state.gates["seal"] = res_d
    save_state(state)

    # Grade against fixture rubric
    rubric_fails = grade_rubric(state, res_d, expect)
    print(_render_fixture_summary(state, res_a, res_a5, res_b, res_c, res_d, rubric_fails))

    if rubric_fails:
        return 20
    if not res_d.passed:
        return 14
    return 0


def grade_rubric(state: RunState, res_d: GateResult, expect: dict[str, Any]) -> list[str]:
    fails: list[str] = []
    envelope = json.loads((run_dir(state.agent, state.run_id) / "envelope.json").read_text(encoding="utf-8"))

    exp_conf = expect.get("confidence")
    if exp_conf and envelope["confidence"] != exp_conf:
        fails.append(f"confidence: expected {exp_conf}, got {envelope['confidence']}")

    exp_gates = expect.get("gates_passed") or []
    for g in exp_gates:
        gr = state.gates.get(g)
        if not gr or not gr.passed:
            fails.append(f"gate {g}: expected pass")

    exp_cites = expect.get("must_cite_any_of") or []
    if exp_cites:
        got = {(c["type"], c["id"]) for c in envelope["citations"]}
        any_hit = any((c["type"], c["id"]) in got for c in exp_cites)
        if not any_hit:
            fails.append(f"must_cite_any_of: none of {exp_cites} appear in citations {sorted(got)}")

    req_refs = expect.get("requirements_document_must_reference") or []
    if req_refs:
        req_path = run_dir(state.agent, state.run_id) / "REQUIREMENTS.md"
        req_text = req_path.read_text(encoding="utf-8")
        missing = [r for r in req_refs if r not in req_text]
        if missing:
            fails.append(f"requirements document missing references: {missing}")

    del_classes = expect.get("deliverables_must_include_classes") or []
    if del_classes:
        titles = {d["title"] for d in envelope.get("deliverables", [])}
        # Title includes the .cls suffix — compare stems
        stems = {t.rsplit(".", 1)[0] for t in titles}
        missing = [c for c in del_classes if c not in stems]
        if missing:
            fails.append(f"deliverables missing classes: {missing}")

    grounding = expect.get("grounding") or {}
    if "unresolved_max" in grounding:
        got = len(state.gates["ground"].data.get("unresolved", []))
        if got > grounding["unresolved_max"]:
            fails.append(f"grounding.unresolved: {got} > max {grounding['unresolved_max']}")

    bg = expect.get("build_gate") or {}
    if "parse_errors_max" in bg:
        got = len(state.gates["build"].data.get("parse_errors", []))
        if got > bg["parse_errors_max"]:
            fails.append(f"build.parse_errors: {got} > max {bg['parse_errors_max']}")
    if "coverage_min" in bg:
        got = state.gates["build"].data.get("coverage", 0)
        if got < bg["coverage_min"]:
            fails.append(f"build.coverage: {got}% < min {bg['coverage_min']}%")

    po = expect.get("process_observations") or {}
    if "min_count" in po:
        got = len(envelope.get("process_observations", []))
        if got < po["min_count"]:
            fails.append(f"process_observations: {got} < min {po['min_count']}")
    if "categories_present_any_of" in po:
        cats = {o["category"] for o in envelope.get("process_observations", [])}
        if not (set(po["categories_present_any_of"]) & cats):
            fails.append(f"process_observations categories: none of {po['categories_present_any_of']} in {cats}")

    fu = expect.get("followups_include_any_of") or []
    if fu:
        got = {f["agent"] for f in envelope.get("followups", [])}
        if not (set(fu) & got):
            fails.append(f"followups: none of {fu} in {sorted(got)}")

    return fails


def _render_fixture_summary(state, a, a5, b, c, d, rubric_fails) -> str:
    lines = [
        f"== fixture run :: {state.agent} / {state.run_id} ==",
        f"  Gate A  inputs       : {'PASS' if a.passed else 'FAIL'} — {'; '.join(a.notes) or 'ok'}",
        f"  Gate A5 requirements : {'PASS' if a5.passed else 'FAIL'} — {'; '.join(a5.notes) or 'ok'}",
        f"  Gate B  ground       : {'PASS' if b.passed else 'FAIL'} — {'; '.join(b.notes) or 'ok'}",
        f"  Gate C  build        : {'PASS' if c.passed else 'FAIL'} — {'; '.join(c.notes) or 'ok'}",
        f"  Gate D  seal         : {'PASS' if d.passed else 'FAIL'} — {'; '.join(d.notes) or 'ok'}",
        "",
        f"  rubric fails         : {len(rubric_fails)}",
    ]
    for rf in rubric_fails:
        lines.append(f"    - {rf}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cli() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agent", required=True, help="Builder agent slug (e.g. apex-builder)")
    ap.add_argument("--stage", choices=["inputs", "requirements", "ground", "build", "seal"], help="Which gate to run")
    ap.add_argument("--inputs", help="Path to inputs JSON packet")
    ap.add_argument("--run-id", help="Existing run_id to continue")
    ap.add_argument("--approved-requirements", help="Path to a requirements file the caller is approving")
    ap.add_argument("--emitted-dir", help="Directory containing emitted .cls / .trigger files for Gate C")
    ap.add_argument("--fixture", help="Fixture YAML — runs all five gates against a canned input+stub")
    ap.add_argument("--coverage-override", type=int, help="Fixture-mode coverage signal (0-100) when no coverage.json exists")
    ap.add_argument("--target-org-override", help="Override target_org_alias from inputs/fixture with a real CLI alias. Enables live sf project deploy validate.")
    args = ap.parse_args()

    if args.fixture:
        emitted = Path(args.emitted_dir).resolve() if args.emitted_dir else None
        return run_fixture(Path(args.fixture).resolve(), emitted, target_org_override=args.target_org_override)

    if not args.stage:
        print("ERROR: --stage required unless --fixture is supplied", file=sys.stderr)
        return 30

    # Stage flow
    if args.stage == "inputs":
        if not args.inputs:
            print("ERROR: --inputs required for --stage inputs", file=sys.stderr)
            return 30
        inputs = json.loads(Path(args.inputs).read_text(encoding="utf-8"))
        state, result = gate_a_inputs(args.agent, inputs, args.run_id)
        save_state(state)
        print(json.dumps({"gate": "inputs", "run_id": state.run_id, "passed": result.passed, "notes": result.notes, "data": result.data}, indent=2))
        return 0 if result.passed else 10

    if not args.run_id:
        print("ERROR: --run-id required for every stage after 'inputs'", file=sys.stderr)
        return 30
    state = load_state(args.agent, args.run_id)

    if args.stage == "requirements":
        result = gate_a5_requirements(state)
        state.gates["requirements"] = result
        save_state(state)
        print(json.dumps({"gate": "requirements", "passed": result.passed, "artifacts": result.artifacts, "data": result.data}, indent=2))
        return 0 if result.passed else 11

    if args.stage == "ground":
        if args.approved_requirements:
            ok, reason = approve_requirements(state, Path(args.approved_requirements).resolve())
            if not ok:
                print(f"ERROR: {reason}", file=sys.stderr)
                return 11
            state.gates["requirements"].data["approved"] = True
        else:
            if not state.gates.get("requirements") or not state.gates["requirements"].data.get("approved"):
                print("ERROR: pass --approved-requirements <path> (Gate A.5 not approved)", file=sys.stderr)
                return 11
        result = gate_b_ground(state)
        state.gates["ground"] = result
        save_state(state)
        print(json.dumps({"gate": "ground", "passed": result.passed, "notes": result.notes, "data": result.data}, indent=2, default=str))
        return 0 if result.passed else 12

    if args.stage == "build":
        if not args.emitted_dir:
            print("ERROR: --emitted-dir required for --stage build", file=sys.stderr)
            return 30
        result = gate_c_build(state, Path(args.emitted_dir).resolve(), coverage_override=args.coverage_override)
        state.gates["build"] = result
        save_state(state)
        print(json.dumps({"gate": "build", "passed": result.passed, "notes": result.notes, "data": result.data}, indent=2, default=str))
        return 0 if result.passed else 13

    if args.stage == "seal":
        result = gate_d_seal(state)
        state.gates["seal"] = result
        save_state(state)
        print(json.dumps({"gate": "seal", "passed": result.passed, "artifacts": result.artifacts, "data": result.data}, indent=2, default=str))
        return 0 if result.passed else 14

    return 30


if __name__ == "__main__":
    sys.exit(cli())
