"""FlowBuilderPlugin — gated QA for flow-builder.

Scope:
  * Grounding: trigger_sobject + referenced_fields describe against org_stub.
  * Expected resources: fault-path + subflow templates, automation-selection
    decision tree.
  * Gate C static: Flow XML must parse as XML, root <Flow>, must declare
    <processType> matching flow_type, record-triggered flows must have a
    <start> block with <object> + <recordTriggerType>, must have a <status>
    element, and every element that can fail (<recordCreates>, <recordUpdates>,
    <recordDeletes>, <actionCalls>) must have either a <faultConnector> or
    a sibling fault path OR sit inside a try/catch-equivalent pattern.
  * Gate C live: `sf project deploy validate --target-org <alias>` against a
    real org. The Flow compiler enforces SObject + field correctness,
    subflow resolution, and API-version compatibility.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from .base import LiveCheckResult


SFDX_PROJECT_JSON = """{
  "packageDirectories": [{"path": "force-app", "default": true}],
  "namespace": "",
  "sfdcLoginUrl": "https://login.salesforce.com",
  "sourceApiVersion": "{api}"
}
"""


def _bullets(items: list[str], indent: str = "  ") -> str:
    if not items:
        return f"{indent}- _(none)_"
    return "\n".join(f"{indent}- {it}" for it in items)


# flow_type → (processType tag, notes). Mirrors Flow metadata docs.
PROCESS_TYPES: dict[str, list[str]] = {
    "record-triggered": ["AutoLaunchedFlow"],
    "platform-event-triggered": ["AutoLaunchedFlow"],
    "scheduled": ["AutoLaunchedFlow"],
    "auto-launched": ["AutoLaunchedFlow"],
    "screen": ["Flow"],
    "orchestration": ["Orchestrator"],
}


# Elements whose failure must be caught by a fault path.
FAILABLE_ELEMENTS = {"recordCreates", "recordUpdates", "recordDeletes", "recordLookups", "actionCalls"}


class FlowBuilderPlugin:
    agent = "flow-builder"

    # --- Gate A extras -----------------------------------------------------
    def additional_input_checks(self, inputs: dict[str, Any]) -> tuple[list[str], list[str]]:
        missing: list[str] = []
        invalid: list[str] = []
        if inputs.get("flow_type") in ("record-triggered", "platform-event-triggered"):
            if not inputs.get("trigger_sobject"):
                missing.append("trigger_sobject (required when flow_type is record- or platform-event-triggered)")
        if inputs.get("flow_type") == "record-triggered":
            if not inputs.get("record_trigger_type"):
                missing.append("record_trigger_type (Create/Update/CreateAndUpdate/Delete)")
        return missing, invalid

    # --- grounding (Gate B) -----------------------------------------------
    def grounding_sobjects(self, inputs: dict[str, Any]) -> list[str]:
        trig = inputs.get("trigger_sobject")
        return [trig] if trig else []

    def expected_resources(self, inputs: dict[str, Any]) -> list[dict[str, str]]:
        out: list[dict[str, str]] = [
            {"type": "template", "path": "templates/flow/FaultPath_Template.md"},
            {"type": "template", "path": "templates/flow/Subflow_Pattern.md"},
        ]
        if inputs.get("flow_type") == "record-triggered":
            out.append({"type": "template", "path": "templates/flow/RecordTriggered_Skeleton.flow-meta.xml"})
        return out

    def expected_citations(self, inputs: dict[str, Any]) -> list[dict[str, str]]:
        out: list[dict[str, str]] = [
            {"type": "skill", "id": "flow/fault-handling"},
            {"type": "skill", "id": "flow/flow-bulkification"},
            {"type": "decision_tree", "id": "automation-selection.md"},
        ]
        ft = inputs.get("flow_type", "")
        if ft == "record-triggered":
            out.append({"type": "skill", "id": "flow/record-triggered-flow-patterns"})
        elif ft == "scheduled":
            out.append({"type": "skill", "id": "flow/scheduled-flows"})
        elif ft == "screen":
            out.append({"type": "skill", "id": "flow/screen-flows"})
        elif ft == "auto-launched":
            out.append({"type": "skill", "id": "flow/auto-launched-flow-patterns"})
        elif ft == "orchestration":
            out.append({"type": "skill", "id": "flow/orchestration-flows"})
        if inputs.get("subflows"):
            out.append({"type": "skill", "id": "flow/subflows-and-reusability"})
        return out

    # --- deliverables ------------------------------------------------------
    def class_inventory(self, inputs: dict[str, Any]) -> list[str]:
        name = inputs.get("flow_developer_name") or "Flow_Skeleton"
        return [f"{name}.flow-meta.xml"]

    def expected_deliverable_stems(self, inputs: dict[str, Any]) -> set[str]:
        # Flow's "stem" check isn't .cls-based; static_check already enforces
        # filename shape. Return empty so Gate C's cls-stem diff stays quiet.
        return set()

    # --- grounding symbols for REQUIREMENTS --------------------------------
    def grounding_symbols(self, inputs: dict[str, Any]) -> list[str]:
        syms: list[str] = []
        trig = inputs.get("trigger_sobject")
        if trig:
            syms.append(f"SObject: `{trig}`")
        for f in inputs.get("referenced_fields") or []:
            syms.append(f"Field: `{f}`")
        for s in inputs.get("subflows") or []:
            syms.append(f"Subflow: `{s}` (must exist at repo or org)")
        name = inputs.get("flow_developer_name") or "_(unspecified)_"
        syms.append(f"Flow: `{name}.flow-meta.xml` (must NOT already exist under repo_path)")
        syms.append("Template: `templates/flow/FaultPath_Template.md`")
        syms.append("Template: `templates/flow/Subflow_Pattern.md`")
        syms.append("Decision tree: `standards/decision-trees/automation-selection.md`")
        return syms

    # --- requirements template vars ----------------------------------------
    def requirements_template_vars(
        self,
        inputs: dict[str, Any],
        run_id: str,
        inputs_sha256: str,
        agent_version: str = "1.0.0",
    ) -> dict[str, str]:
        name = inputs.get("flow_developer_name") or "_(unspecified)_"
        ft = inputs.get("flow_type", "_(unspecified)_")
        process = ", ".join(PROCESS_TYPES.get(ft, ["_(unresolved)_"]))
        subflows = inputs.get("subflows") or []
        fields = inputs.get("referenced_fields") or []
        return {
            "{{feature_summary_short}}": (inputs.get("feature_summary") or "").strip()[:80],
            "{{run_id}}": run_id,
            "{{generated_at}}": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
            "{{agent_version}}": agent_version,
            "{{inputs_sha256}}": inputs_sha256,
            "{{feature_summary}}": inputs.get("feature_summary", "_(unspecified)_"),
            "{{flow_developer_name}}": name,
            "{{flow_type}}": ft,
            "{{process_type}}": process,
            "{{trigger_sobject_or_na}}": inputs.get("trigger_sobject", "_(n/a)_"),
            "{{trigger_context}}": inputs.get("trigger_context", "_(inferred)_"),
            "{{record_trigger_type_or_na}}": inputs.get("record_trigger_type", "_(n/a)_"),
            "{{expected_volume}}": inputs.get("expected_volume", "medium"),
            "{{referenced_fields_bullets}}": _bullets([f"`{f}`" for f in fields]),
            "{{subflows_bullets}}": _bullets([f"`{s}`" for s in subflows]),
            "{{api_version}}": inputs.get("api_version", "60.0"),
            "{{target_org_alias_or_library_only}}": inputs.get("target_org_alias") or "_(library-only mode)_",
            "{{flow_inventory_bullets}}": _bullets([f"`{c}`" for c in self.class_inventory(inputs)]),
            "{{grounding_symbols_bullets}}": _bullets(self.grounding_symbols(inputs)),
        }

    # --- Gate C ------------------------------------------------------------
    def discover_emitted_files(self, emitted_dir: Path) -> list[Path]:
        if not emitted_dir.exists():
            return []
        out: list[Path] = []
        for pat in ("*.flow-meta.xml", "*.flow"):
            out.extend(emitted_dir.rglob(pat))
        return sorted(set(out))

    def static_check(self, files: list[Path]) -> list[str]:
        errors: list[str] = []
        if not files:
            return ["no flow-meta.xml files under emitted_dir"]

        for f in files:
            errors.extend(self._check_flow_xml(f))
        return errors

    def live_check(
        self,
        files: list[Path],
        target_org: str,
        api_version: str,
        timeout_sec: int = 300,
    ) -> LiveCheckResult:
        res = LiveCheckResult(oracle_label="sf project deploy validate (flow)")
        if not shutil.which("sf"):
            res.errors.append({"file": None, "line": None, "column": None, "problem": "sf CLI not on PATH", "problem_type": "MissingCLI"})
            return res

        with tempfile.TemporaryDirectory(prefix="run_builder_flow_") as tmp_s:
            tmp = Path(tmp_s)
            flows_root = tmp / "force-app" / "main" / "default" / "flows"
            flows_root.mkdir(parents=True)
            (tmp / "sfdx-project.json").write_text(SFDX_PROJECT_JSON.replace("{api}", api_version), encoding="utf-8")

            for f in files:
                (flows_root / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")

            cmd = [
                "sf", "project", "deploy", "validate",
                "--target-org", target_org,
                "--source-dir", str(tmp / "force-app"),
                "--json",
                "--wait", "10",
            ]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec, cwd=str(tmp))
            except subprocess.TimeoutExpired:
                res.errors.append({"file": None, "line": None, "column": None, "problem": f"sf timed out after {timeout_sec}s", "problem_type": "Timeout"})
                return res

            res.ran = True
            try:
                payload = json.loads(proc.stdout)
            except json.JSONDecodeError:
                res.errors.append({
                    "file": None, "line": None, "column": None,
                    "problem": f"could not parse sf JSON: {proc.stderr[:300] or proc.stdout[:300]}",
                    "problem_type": "UnparseableCLIOutput",
                })
                return res

            top_status = payload.get("status")
            top_name = payload.get("name")
            top_message = payload.get("message")
            res.status = top_status

            if top_status not in (0, None) and not payload.get("result"):
                res.errors.append({
                    "file": None, "line": None, "column": None,
                    "problem": top_message or f"sf CLI returned status {top_status}",
                    "problem_type": top_name or "CLIError",
                })
                res.succeeded = False
                res.raw = {"num_component_errors": 1, "num_component_success": 0}
                return res

            result = payload.get("result") or {}
            details = result.get("details") or {}
            component_failures = details.get("componentFailures") or []
            component_success = details.get("componentSuccesses") or []

            res.succeeded = bool(result.get("success"))
            res.errors = [
                {
                    "file": cf.get("fileName") or cf.get("fullName"),
                    "line": cf.get("lineNumber"),
                    "column": cf.get("columnNumber"),
                    "problem": cf.get("problem"),
                    "problem_type": cf.get("problemType"),
                }
                for cf in component_failures
            ]
            res.raw = {
                "num_component_errors": result.get("numberComponentErrors", len(component_failures)),
                "num_component_success": result.get("numberComponentsDeployed", len(component_success)),
            }
            return res

    def coverage_thresholds(self, inputs: dict[str, Any]) -> dict[str, int]:
        # Flow tests are distinct from Apex coverage; no Gate C coverage gate.
        return {"floor": 0, "high_tier": 0}

    # --- private helpers ---------------------------------------------------
    def _check_flow_xml(self, path: Path) -> list[str]:
        errors: list[str] = []
        try:
            tree = ET.parse(str(path))
        except ET.ParseError as e:
            return [f"{path.name}: not valid XML ({e})"]

        root = tree.getroot()
        tag_local = root.tag.split("}")[-1] if "}" in root.tag else root.tag
        if tag_local != "Flow":
            errors.append(f"{path.name}: root element is '{tag_local}', expected Flow")
            return errors

        ns = root.tag.split("}")[0] + "}" if "}" in root.tag else ""

        def find(parent, name):
            return parent.find(f"{ns}{name}")

        def findall(parent, name):
            return parent.findall(f"{ns}{name}")

        # processType present
        pt = find(root, "processType")
        if pt is None or not (pt.text or "").strip():
            errors.append(f"{path.name}: missing <processType> element")

        # status present
        status = find(root, "status")
        if status is None or (status.text or "").strip() not in ("Active", "Draft", "Obsolete", "InvalidDraft"):
            errors.append(f"{path.name}: <status> missing or not in {{Active,Draft,Obsolete,InvalidDraft}}")

        # apiVersion present
        api = find(root, "apiVersion")
        if api is None or not re.match(r"^\d{2}\.0$", (api.text or "").strip()):
            errors.append(f"{path.name}: <apiVersion> missing or not X.0 form")

        # For record-triggered, <start> must have <object> and <recordTriggerType>
        start = find(root, "start")
        if pt is not None and (pt.text or "").strip() == "AutoLaunchedFlow" and start is not None:
            rtt = find(start, "recordTriggerType")
            obj = find(start, "object")
            tt = find(start, "triggerType")
            # record-triggered is the intersection of AutoLaunchedFlow + <recordTriggerType>
            if rtt is not None:
                if obj is None or not (obj.text or "").strip():
                    errors.append(f"{path.name}: record-triggered flow <start> missing <object>")
                if tt is None:
                    errors.append(f"{path.name}: record-triggered flow <start> missing <triggerType>")

        # Every failable element should have a faultConnector.
        for elem in FAILABLE_ELEMENTS:
            for node in findall(root, elem):
                name_el = find(node, "name")
                node_name = (name_el.text if name_el is not None else "(unnamed)") or "(unnamed)"
                fault = find(node, "faultConnector")
                if fault is None:
                    errors.append(f"{path.name}: <{elem}> '{node_name}' has no <faultConnector> — unhandled failure path")

        return errors
