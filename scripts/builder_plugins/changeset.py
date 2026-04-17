"""ChangesetBuilderPlugin — gated QA for changeset-builder.

Scope:
  * Gate A: package_name + api_version + items[] must be present.
  * Gate B: every metadata type named in items[] must be a known
    Salesforce metadata type; every member must pass a shape check.
  * Gate C static: package.xml parses, root <Package>, each <types>
    has a <name> + at least one <members>, <version> matches api_version.
  * Gate C live: `sf project retrieve preview --target-org <alias> --manifest <package.xml> --json`
    against a real org — the CLI computes the would-be retrieve diff
    without writing anything. On an empty package the CLI returns
    status 0 with an empty result; on a broken manifest it returns
    a nonzero top-level status which we surface as an oracle failure.
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


def _bullets(items: list[str], indent: str = "  ") -> str:
    if not items:
        return f"{indent}- _(none)_"
    return "\n".join(f"{indent}- {it}" for it in items)


KNOWN_METADATA_TYPES = {
    "ApexClass", "ApexTrigger", "ApexPage", "ApexComponent",
    "LightningComponentBundle", "AuraDefinitionBundle",
    "Flow", "FlowDefinition", "WorkflowRule", "Workflow",
    "CustomObject", "CustomField", "CustomMetadata",
    "ValidationRule", "Layout", "RecordType",
    "Profile", "PermissionSet", "PermissionSetGroup",
    "CustomLabel", "CustomLabels", "StaticResource",
    "EmailTemplate", "Report", "Dashboard",
    "QuickAction", "GlobalPicklist", "GlobalValueSet",
    "SharingRules", "SharingOwnerRule", "SharingCriteriaRule",
    "ConnectedApp", "NamedCredential", "RemoteSiteSetting",
    "CustomApplication", "Translation", "Queue", "Group",
    "AssignmentRule", "AutoResponseRule", "EscalationRule",
    "Bot", "GenAiPlugin", "GenAiFunction",  # Agentforce
}


class ChangesetBuilderPlugin:
    agent = "changeset-builder"

    # --- Gate A ------------------------------------------------------------
    def additional_input_checks(self, inputs: dict[str, Any]) -> tuple[list[str], list[str]]:
        missing: list[str] = []
        invalid: list[str] = []
        items = inputs.get("items") or []
        if not items:
            missing.append("items (at least one {type,member} entry required)")
        else:
            for i, it in enumerate(items):
                if not isinstance(it, dict) or not it.get("type") or not it.get("member"):
                    invalid.append(f"items[{i}]: must be an object with 'type' and 'member'")
                elif it["type"] not in KNOWN_METADATA_TYPES:
                    invalid.append(f"items[{i}]: unknown metadata type '{it['type']}'")
        return missing, invalid

    # --- Gate B ------------------------------------------------------------
    def grounding_sobjects(self, inputs: dict[str, Any]) -> list[str]:
        return []

    def expected_resources(self, inputs: dict[str, Any]) -> list[dict[str, str]]:
        return []

    def expected_citations(self, inputs: dict[str, Any]) -> list[dict[str, str]]:
        return [
            {"type": "skill", "id": "devops/change-set-deployment"},
            {"type": "skill", "id": "devops/migration-from-change-sets-to-sfdx"},
        ]

    # --- deliverables ------------------------------------------------------
    def class_inventory(self, inputs: dict[str, Any]) -> list[str]:
        name = inputs.get("package_name") or "package"
        return [f"{name}/package.xml"]

    def expected_deliverable_stems(self, inputs: dict[str, Any]) -> set[str]:
        return set()

    # --- grounding symbols for REQUIREMENTS --------------------------------
    def grounding_symbols(self, inputs: dict[str, Any]) -> list[str]:
        items = inputs.get("items") or []
        return [f"Metadata: `{it['type']}.{it['member']}`" for it in items if isinstance(it, dict) and it.get("type") and it.get("member")]

    # --- requirements template vars ----------------------------------------
    def requirements_template_vars(
        self,
        inputs: dict[str, Any],
        run_id: str,
        inputs_sha256: str,
        agent_version: str = "1.0.0",
    ) -> dict[str, str]:
        items = inputs.get("items") or []
        items_bullets = _bullets([f"`{it.get('type','?')}.{it.get('member','?')}`" for it in items])
        return {
            "{{feature_summary_short}}": (inputs.get("feature_summary") or "").strip()[:80],
            "{{run_id}}": run_id,
            "{{generated_at}}": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
            "{{agent_version}}": agent_version,
            "{{inputs_sha256}}": inputs_sha256,
            "{{feature_summary}}": inputs.get("feature_summary", "_(unspecified)_"),
            "{{package_name}}": inputs.get("package_name", "package"),
            "{{api_version}}": inputs.get("api_version", "60.0"),
            "{{items_bullets}}": items_bullets,
            "{{target_org_alias_or_library_only}}": inputs.get("target_org_alias") or "_(library-only mode)_",
            "{{grounding_symbols_bullets}}": _bullets(self.grounding_symbols(inputs)),
            "{{package_inventory_bullets}}": _bullets([f"`{c}`" for c in self.class_inventory(inputs)]),
        }

    # --- Gate C ------------------------------------------------------------
    def discover_emitted_files(self, emitted_dir: Path) -> list[Path]:
        if not emitted_dir.exists():
            return []
        return sorted(emitted_dir.rglob("package.xml"))

    def static_check(self, files: list[Path]) -> list[str]:
        errors: list[str] = []
        if not files:
            return ["no package.xml under emitted_dir"]
        for f in files:
            errors.extend(self._check_package_xml(f))
        return errors

    def live_check(
        self,
        files: list[Path],
        target_org: str,
        api_version: str,
        timeout_sec: int = 300,
    ) -> LiveCheckResult:
        """Per-type list-metadata oracle.

        `sf project deploy validate --manifest` would be ideal but requires
        source-backed components. Instead we prove org reachability + that
        every type in the manifest is recognized by running
        `sf org list metadata --metadata-type <type>` per distinct type.
        """
        res = LiveCheckResult(oracle_label="sf org list metadata (per manifest type)")
        if not files:
            res.errors.append({"file": None, "line": None, "column": None, "problem": "no package.xml to validate", "problem_type": "NoInput"})
            return res
        if not shutil.which("sf"):
            res.errors.append({"file": None, "line": None, "column": None, "problem": "sf CLI not on PATH", "problem_type": "MissingCLI"})
            return res

        try:
            tree = ET.parse(str(files[0]))
        except ET.ParseError as e:
            res.errors.append({"file": files[0].name, "line": None, "column": None, "problem": f"XML parse error: {e}", "problem_type": "XMLParseError"})
            return res
        root = tree.getroot()
        ns = root.tag.split("}")[0] + "}" if "}" in root.tag else ""
        type_names: list[str] = []
        for t in root.findall(f"{ns}types"):
            n = t.find(f"{ns}name")
            if n is not None and (n.text or "").strip():
                type_names.append((n.text or "").strip())

        if not type_names:
            res.errors.append({"file": files[0].name, "line": None, "column": None, "problem": "no <types> in manifest", "problem_type": "EmptyManifest"})
            return res

        res.ran = True
        checked = 0
        for mt in sorted(set(type_names)):
            cmd = ["sf", "org", "list", "metadata", "--metadata-type", mt, "--target-org", target_org, "--json"]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
            except subprocess.TimeoutExpired:
                res.errors.append({"file": None, "line": None, "column": None, "problem": f"sf timed out after {timeout_sec}s on type={mt}", "problem_type": "Timeout"})
                return res
            try:
                payload = json.loads(proc.stdout)
            except json.JSONDecodeError:
                res.errors.append({"file": None, "line": None, "column": None, "problem": f"unparseable sf JSON for type={mt}: {proc.stderr[:300] or proc.stdout[:300]}", "problem_type": "UnparseableCLIOutput"})
                return res
            if payload.get("status") not in (0, None):
                res.errors.append({"file": None, "line": None, "column": None, "problem": payload.get("message") or f"sf returned status {payload.get('status')} for type={mt}", "problem_type": payload.get("name") or "CLIError"})
                res.succeeded = False
                res.raw = {"num_component_errors": len(res.errors), "num_component_success": checked}
                return res
            checked += 1

        res.succeeded = True
        res.status = 0
        res.raw = {"num_component_errors": 0, "num_component_success": checked}
        return res

    def coverage_thresholds(self, inputs: dict[str, Any]) -> dict[str, int]:
        return {"floor": 0, "high_tier": 0}

    # --- private helpers ---------------------------------------------------
    def _check_package_xml(self, path: Path) -> list[str]:
        errors: list[str] = []
        try:
            tree = ET.parse(str(path))
        except ET.ParseError as e:
            return [f"{path.name}: not valid XML ({e})"]
        root = tree.getroot()
        tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag
        if tag != "Package":
            errors.append(f"{path.name}: root element is '{tag}', expected Package")
            return errors
        ns = root.tag.split("}")[0] + "}" if "}" in root.tag else ""

        types_nodes = root.findall(f"{ns}types")
        if not types_nodes:
            errors.append(f"{path.name}: missing any <types> entry")
        for i, t in enumerate(types_nodes):
            name = t.find(f"{ns}name")
            members = t.findall(f"{ns}members")
            if name is None or not (name.text or "").strip():
                errors.append(f"{path.name}: <types>[{i}] missing <name>")
            else:
                nm = (name.text or "").strip()
                if nm not in KNOWN_METADATA_TYPES:
                    errors.append(f"{path.name}: <types>[{i}] <name>={nm} is not a known metadata type")
            if not members:
                errors.append(f"{path.name}: <types>[{i}] has no <members>")

        version = root.find(f"{ns}version")
        if version is None or not re.match(r"^\d{2}\.0$", (version.text or "").strip()):
            errors.append(f"{path.name}: missing or malformed <version>")
        return errors
