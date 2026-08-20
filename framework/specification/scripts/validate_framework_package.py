#!/usr/bin/env python3
"""Validate the SFAEF specification package and its cross-artifact contracts."""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:  # pragma: no cover - explicitly reported
    Draft202012Validator = None
    FormatChecker = None

ROOT = Path(__file__).resolve().parents[1]
REQ_RE = re.compile(r"\bSFAEF-\d{3}-\d{3}\b")
FORBIDDEN_PRODUCT_PERMISSIONS = {
    "salesforce.metadata.write",
    "salesforce.data.write",
    "salesforce.apex.execute",
    "salesforce.permissions.write",
    "salesforce.package.write",
    "salesforce.org.write",
}
FORBIDDEN_PERMISSION_FRAGMENTS = (
    "create_org",
    "delete_org",
    "assign_permission",
    "quick_deploy",
    "destructive",
)


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    path: str | None = None


class Validator:
    def __init__(self, root: Path):
        self.root = root
        self.findings: list[Finding] = []
        self.counts: dict[str, int] = {}

    def add(self, severity: str, code: str, message: str, path: Path | str | None = None) -> None:
        rel = None
        if isinstance(path, Path):
            try:
                rel = path.relative_to(self.root).as_posix()
            except ValueError:
                rel = str(path)
        elif path is not None:
            rel = str(path)
        self.findings.append(Finding(severity, code, message, rel))

    def load_json(self, path: Path) -> Any | None:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            self.add("error", "json_parse", str(exc), path)
            return None

    def validate_json_schemas(self) -> None:
        if Draft202012Validator is None:
            self.add("error", "dependency_missing", "jsonschema is required to validate local schemas")
            return
        validated = 0
        for path in sorted(self.root.rglob("*.json")):
            if "__pycache__" in path.parts:
                continue
            data = self.load_json(path)
            if not isinstance(data, dict):
                continue
            schema_ref = data.get("$schema")
            if not schema_ref or str(schema_ref).startswith(("http://", "https://")):
                continue
            schema_path = (path.parent / schema_ref).resolve()
            try:
                schema_path.relative_to(self.root.resolve())
            except ValueError:
                self.add("error", "schema_escape", f"schema path escapes package: {schema_ref}", path)
                continue
            if not schema_path.exists():
                self.add("error", "schema_missing", f"missing local schema: {schema_ref}", path)
                continue
            schema = self.load_json(schema_path)
            if not isinstance(schema, dict):
                continue
            validator = Draft202012Validator(schema, format_checker=FormatChecker())
            for error in sorted(validator.iter_errors(data), key=lambda item: list(item.path)):
                location = "/" + "/".join(str(x) for x in error.path)
                self.add("error", "schema_invalid", f"{location}: {error.message}", path)
            validated += 1
        self.counts["schema_validated_json"] = validated

    def collect(self, directory: str, id_key: str = "id") -> dict[str, dict]:
        result: dict[str, dict] = {}
        for path in sorted((self.root / directory).glob("*.json")):
            data = self.load_json(path)
            if not isinstance(data, dict) or id_key not in data:
                continue
            identifier = str(data[id_key])
            if identifier in result:
                self.add("error", "duplicate_id", f"duplicate id {identifier}", path)
            result[identifier] = data
        return result

    def validate_requirements(self) -> None:
        discovered: dict[str, tuple[str, int]] = {}
        for path in sorted((self.root / "spec").glob("[0-9][0-9][0-9]-*.md")):
            for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                for requirement_id in REQ_RE.findall(line):
                    if not line.lstrip().startswith(requirement_id + "."):
                        continue
                    if requirement_id in discovered:
                        self.add("error", "requirement_duplicate", f"{requirement_id} already at {discovered[requirement_id]}", path)
                    discovered[requirement_id] = (path.relative_to(self.root).as_posix(), line_no)
        catalog_path = self.root / "implementation" / "requirements.csv"
        catalog: dict[str, dict[str, str]] = {}
        if not catalog_path.exists():
            self.add("error", "requirement_catalog_missing", "implementation/requirements.csv is missing")
        else:
            with catalog_path.open(encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    requirement_id = row.get("requirement_id", "")
                    if requirement_id in catalog:
                        self.add("error", "requirement_catalog_duplicate", requirement_id, catalog_path)
                    catalog[requirement_id] = row
            for requirement_id, (source, line) in discovered.items():
                row = catalog.get(requirement_id)
                if not row:
                    self.add("error", "requirement_catalog_omission", requirement_id, catalog_path)
                elif row.get("spec_file") != source or int(row.get("line") or 0) != line:
                    self.add("error", "requirement_catalog_drift", f"{requirement_id}: expected {source}:{line}, got {row.get('spec_file')}:{row.get('line')}", catalog_path)
            for requirement_id in sorted(set(catalog) - set(discovered)):
                self.add("error", "requirement_catalog_orphan", requirement_id, catalog_path)
        self.counts["requirements"] = len(discovered)

    def validate_definitions(self) -> None:
        products = self.collect("products/definitions")
        agents = self.collect("agents/definitions")
        commands = self.collect("commands/specs")
        tools = self.collect("mcp/tool-specs")
        contexts = self.collect("context/context-packs")
        scenarios = self.collect("qa/scenarios")
        sources = self.collect("research/sources")
        self.counts.update({
            "products": len(products), "agents": len(agents), "commands": len(commands),
            "evidence_tools": len(tools), "context_packs": len(contexts),
            "qa_scenarios": len(scenarios), "research_sources": len(sources),
        })
        context_by_product = {value.get("product_id"): value for value in contexts.values()}
        for pid, product in products.items():
            if product.get("id") != pid:
                self.add("error", "product_id_mismatch", f"map key {pid} != object id {product.get('id')}")
            if not (self.root / "products" / f"{pid}-{product.get('slug')}.md").exists():
                self.add("error", "product_doc_missing", f"missing product narrative for {pid}")
            for aid in product.get("agent_ids", []):
                if aid not in agents:
                    self.add("error", "product_agent_missing", f"{pid} references {aid}")
            for cid in product.get("command_ids", []):
                if cid not in commands:
                    self.add("error", "product_command_missing", f"{pid} references {cid}")
                elif commands[cid].get("product_id") != pid:
                    self.add("error", "command_product_mismatch", f"{cid} points to {commands[cid].get('product_id')}, expected {pid}")
            for tid in product.get("tool_ids", []):
                if tid not in tools:
                    self.add("error", "product_tool_missing", f"{pid} references {tid}")
            for sid in product.get("known_truth_scenarios", []):
                if sid not in scenarios:
                    self.add("error", "scenario_missing", f"{pid} references {sid}")
                elif scenarios[sid].get("product_id") != pid:
                    self.add("error", "scenario_product_mismatch", f"{sid} points to {scenarios[sid].get('product_id')}, expected {pid}")
            if pid not in context_by_product:
                self.add("error", "context_pack_missing", pid)
            for perm in product.get("permissions", []):
                normalized = perm.lower().strip()
                if normalized in FORBIDDEN_PRODUCT_PERMISSIONS or any(
                    marker in normalized for marker in FORBIDDEN_PERMISSION_FRAGMENTS
                ):
                    self.add("error", "product_write_permission", f"{pid} declares {perm}")
            if product.get("context_policy", {}).get("transcript_handoff") is True:
                self.add("error", "transcript_handoff_enabled", pid)
        for aid, agent in agents.items():
            if not (self.root / "agents" / ("core" if agent.get("kind") == "core" else "product") / f"{aid}.md").exists():
                self.add("error", "agent_doc_missing", aid)
            pid = agent.get("product_id")
            if pid and pid not in products:
                self.add("error", "agent_product_missing", f"{aid} references {pid}")
            for tid in agent.get("tool_ids", []):
                if tid not in tools:
                    self.add("error", "agent_tool_missing", f"{aid} references {tid}")
            if agent.get("context_policy", {}).get("transcript_handoff") is True:
                self.add("error", "transcript_handoff_enabled", aid)
            for collaborator in agent.get("collaborators", []):
                if collaborator not in agents:
                    self.add("error", "agent_collaborator_missing", f"{aid} references {collaborator}")
                if collaborator == aid:
                    self.add("error", "agent_self_collaboration", aid)
            authority = agent.get("authority_profile", {})
            if authority.get("authority_from_user_prose") is not False or authority.get("authority_from_other_agents") is not False:
                self.add("error", "agent_authority_escalation", aid)
            if authority.get("salesforce_access") not in {"none", "read-only"}:
                self.add("error", "agent_salesforce_authority", f"{aid}: {authority.get('salesforce_access')}")
            if agent.get("kind") == "product" and agent.get("completion_review_required") is not True:
                self.add("error", "product_review_not_required", aid)
            if agent.get("recommended_host_exposure") == "top-level" and aid != "sf-intent-router":
                self.add("warning", "broad_top_level_agent", aid)
        for cid, command in commands.items():
            pid = command.get("product_id")
            if pid and pid not in products:
                self.add("error", "command_product_missing", f"{cid} references {pid}")
            for aid in command.get("agent_ids", []):
                if aid not in agents:
                    self.add("error", "command_agent_missing", f"{cid} references {aid}")
            for tid in command.get("tool_ids", []):
                if tid not in tools:
                    self.add("error", "command_tool_missing", f"{cid} references {tid}")
            allowed_statuses = set(command.get("allowed_statuses", []))
            for error in command.get("errors", []):
                if error.get("status") not in allowed_statuses:
                    self.add("error", "command_error_status", f"{cid}/{error.get('code')}: {error.get('status')} not in {sorted(allowed_statuses)}")
            if pid:
                if command.get("requires_independent_review") is not True:
                    self.add("error", "product_command_review_not_required", cid)
                if "independent_review" not in command.get("orchestration_stages", []):
                    self.add("error", "product_command_review_stage_missing", cid)
                if command.get("side_effects", {}).get("salesforce") != "read-only":
                    self.add("error", "product_command_salesforce_effect", f"{cid}: {command.get('side_effects', {}).get('salesforce')}")
            if cid == "sfskills-qa-run" and command.get("side_effects", {}).get("salesforce") != "qa-disposable-only":
                self.add("error", "qa_command_authority", cid)
            if len(command.get("aliases", [])) != len(set(command.get("aliases", []))):
                self.add("error", "command_alias_duplicate", cid)
        for tid, tool in tools.items():
            if tool.get("read_only") is not True:
                self.add("error", "product_tool_not_read_only", tid)
            if tool.get("unknown_tool_default") != "deny":
                self.add("error", "unknown_tool_not_denied", tid)
            if int(tool.get("max_page_bytes", 0)) > 32768:
                self.add("error", "tool_page_too_large", f"{tid}: {tool.get('max_page_bytes')}")
            result_schema = tool.get("result_schema")
            if not result_schema or not (self.root / "schemas" / result_schema).exists():
                self.add("error", "tool_result_schema_missing", f"{tid}: {result_schema}")
            pagination = tool.get("pagination", {})
            if int(pagination.get("max_page_bytes", 0)) > int(tool.get("max_page_bytes", 0)):
                self.add("error", "tool_pagination_exceeds_contract", tid)
            if int(pagination.get("default_limit", 0)) > int(pagination.get("max_limit", 0)):
                self.add("error", "tool_pagination_limit_order", tid)
            if tool.get("cache_policy", {}).get("cross_target") is not False:
                self.add("error", "tool_cross_target_cache", tid)
            never_retry = set(tool.get("retry_policy", {}).get("never_retry_errors", []))
            required_never_retry = {"invalid_input", "policy_denied", "authentication_unavailable", "redaction_failure"}
            if not required_never_retry.issubset(never_retry):
                self.add("error", "tool_unsafe_retry_policy", f"{tid}: missing {sorted(required_never_retry - never_retry)}")
            error_codes = [item.get("code") for item in tool.get("error_codes", [])]
            if len(error_codes) != len(set(error_codes)):
                self.add("error", "tool_error_code_duplicate", tid)
            if tool.get("requires_target_pinning") and "target_mismatch" not in error_codes:
                self.add("error", "tool_target_mismatch_missing", tid)
        for context_id, context in contexts.items():
            pid = context.get("product_id")
            if pid not in products:
                self.add("error", "context_product_missing", f"{context_id} references {pid}")
            target = int(context.get("target_files", 0))
            hard = int(context.get("hard_files", 0))
            if target > hard or hard > 12:
                self.add("error", "context_budget_invalid", f"{context_id}: target={target}, hard={hard}")
            if int(context.get("max_tool_page_bytes", 0)) > 32768:
                self.add("error", "context_tool_page_too_large", context_id)
        for sid, scenario in scenarios.items():
            if scenario.get("product_id") not in products:
                self.add("error", "scenario_product_missing", f"{sid} references {scenario.get('product_id')}")
            finding_ids = [item.get("id") for item in scenario.get("required_findings", [])]
            if len(finding_ids) != len(set(finding_ids)):
                self.add("error", "scenario_finding_duplicate", sid)

    def validate_migration_ledgers(self) -> None:
        expected = {
            "migration/catalogs/current-skills.csv": 1034,
            "migration/catalogs/current-agents.csv": 78,
            "migration/catalogs/current-commands.csv": 70,
            "migration/catalogs/current-mcp-tools.csv": 40,
        }
        for rel, expected_rows in expected.items():
            path = self.root / rel
            if not path.exists():
                self.add("error", "migration_ledger_missing", rel)
                continue
            with path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            if len(rows) != expected_rows:
                self.add("error", "migration_ledger_count", f"{rel}: expected {expected_rows}, found {len(rows)}", path)
            self.counts[Path(rel).stem.replace("current-", "legacy_")] = len(rows)
        skill_path = self.root / "migration/catalogs/current-skills.csv"
        if skill_path.exists():
            with skill_path.open(encoding="utf-8", newline="") as handle:
                skills = list(csv.DictReader(handle))
            ids = [row.get("skill_id", "") for row in skills]
            if len(ids) != len(set(ids)):
                self.add("error", "migration_skill_duplicate", "current-skills.csv contains duplicate skill IDs", skill_path)
            if any(row.get("v2_disposition") != "retain-knowledge-substrate" for row in skills):
                self.add("error", "migration_skill_disposition", "every baseline skill must have an explicit preserve-first disposition", skill_path)

    def validate_package_hygiene(self) -> None:
        for path in sorted(self.root.rglob("*")):
            if path.is_symlink():
                self.add("error", "symlink_prohibited", "specification package must be self-contained", path)
            if path.is_file() and path.suffix in {".pyc", ".pyo"}:
                self.add("error", "compiled_artifact", "remove compiled Python artifact", path)
        required = [
            "README.md", "START_HERE.md", "SPEC_INDEX.md", "VERSION",
            "implementation/CURSOR_BUILD_SFSAEF_V2.md",
            "implementation/REVIEW_RETURN_CONTRACT.md",
            "commands/API_REFERENCE.md",
            "mcp/TOOL_REFERENCE.md",
            "agents/CONTRACT_REFERENCE.md",
            "reference-kernel/README.md",
        ]
        for rel in required:
            if not (self.root / rel).exists():
                self.add("error", "required_file_missing", rel)

    def validate(self) -> dict[str, Any]:
        self.validate_json_schemas()
        self.validate_requirements()
        self.validate_definitions()
        self.validate_migration_ledgers()
        self.validate_package_hygiene()
        errors = sum(1 for item in self.findings if item.severity == "error")
        warnings = sum(1 for item in self.findings if item.severity == "warning")
        return {
            "valid": errors == 0,
            "root": str(self.root),
            "counts": self.counts,
            "summary": {"errors": errors, "warnings": warnings},
            "findings": [asdict(item) for item in self.findings],
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    result = Validator(ROOT).validate()
    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(f"SFAEF package valid: {result['valid']}")
        for key, value in sorted(result["counts"].items()):
            print(f"  {key}: {value}")
        print(f"  errors: {result['summary']['errors']}")
        print(f"  warnings: {result['summary']['warnings']}")
        for item in result["findings"]:
            location = f" [{item['path']}]" if item.get("path") else ""
            print(f"{item['severity'].upper()} {item['code']}{location}: {item['message']}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
