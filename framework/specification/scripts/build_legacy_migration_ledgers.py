#!/usr/bin/env python3
"""Generate explicit V2 migration ledgers from an SfSkills repository snapshot.

The ledgers are migration evidence, not new canonical definitions. They ensure every
legacy skill, agent, command, and MCP tool has an explicit preservation or migration
posture before implementation changes are accepted.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required to rebuild migration ledgers") from exc

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "migration" / "catalogs"

PRODUCT_MAP: dict[str, list[str]] = {
    "agentforce-action-reviewer": ["P11"], "agentforce-builder": ["P11"],
    "apex-builder": ["P02", "P04"], "apex-refactorer": ["P02", "P04"],
    "assignment-and-auto-response-rules-designer": ["P05"],
    "audit-router": ["P03", "P07", "P10", "P12"],
    "automation-migration-router": ["P05"], "bulk-migration-planner": ["P09"],
    "business-hours-and-holidays-configurator": ["P04"], "changeset-builder": ["P06"],
    "config-workbook-author": ["P04", "P06"], "csv-to-object-mapper": ["P09"],
    "custom-metadata-and-settings-designer": ["P04"], "data-loader-pre-flight": ["P09"],
    "data-model-reviewer": ["P04", "P10"], "deployment-risk-scorer": ["P01", "P06"],
    "duplicate-rule-designer": ["P04", "P07"], "email-template-modernizer": ["P04"],
    "entitlement-and-milestone-designer": ["P04", "P05"],
    "experience-cloud-admin-designer": ["P04", "P07"], "field-impact-analyzer": ["P04"],
    "fit-gap-analyzer": ["P04"], "flow-analyzer": ["P05"], "flow-builder": ["P04", "P05"],
    "flow-orchestrator-designer": ["P05"], "integration-catalog-builder": ["P08"],
    "knowledge-article-taxonomy-agent": ["P04"], "lead-routing-rules-designer": ["P05"],
    "lwc-auditor": ["P04", "P06"], "lwc-builder": ["P04"], "lwc-debugger": ["P04"],
    "object-designer": ["P04"], "omni-channel-routing-designer": ["P05"],
    "omnistudio-designer": ["P04", "P08"], "path-designer": ["P04"],
    "permission-set-architect": ["P03", "P07"], "process-flow-mapper": ["P05"],
    "profile-to-permset-migrator": ["P03", "P07"], "release-train-planner": ["P06"],
    "sales-stage-designer": ["P04"], "sandbox-strategy-designer": ["P06"],
    "security-scanner": ["P03", "P07"], "soql-optimizer": ["P04", "P05", "P10"],
    "story-drafter": ["P04"], "test-class-generator": ["P02", "P06"],
    "trigger-consolidator": ["P05"], "user-access-diff": ["P03", "P12"],
    "waf-assessor": ["P10"],
}

COMMAND_PRODUCT_MAP: dict[str, list[str]] = {
    "analyze-field-impact": ["P04"], "analyze-flow": ["P05"],
    "architect-perms": ["P03", "P07"], "assess-org": ["P10"], "assess-waf": ["P10"],
    "audit-case-escalation": ["P05", "P10"], "audit-lwc": ["P04", "P06"],
    "audit-record-page": ["P04", "P10"], "audit-record-types": ["P03", "P04"],
    "audit-reports": ["P07", "P10"], "audit-router": ["P03", "P07", "P10", "P12"],
    "audit-sharing": ["P03", "P07"], "audit-validation-rules": ["P04", "P05"],
    "author-config-workbook": ["P04", "P06"], "automation-migration-router": ["P05"],
    "build-agentforce-action": ["P11"], "catalog-integrations": ["P08"],
    "consolidate-triggers": ["P05"], "detect-drift": ["P12"], "diff-users": ["P03", "P12"],
    "govern-picklists": ["P04"], "govern-prompt-library": ["P11"],
    "map-csv-to-object": ["P09"], "map-process-flow": ["P05"],
    "migrate-profile-to-permset": ["P03", "P07"], "optimize-soql": ["P04", "P05", "P10"],
    "plan-bulk-migration": ["P09"], "plan-release-train": ["P06"], "preflight-load": ["P09"],
    "release-notes": ["P06"], "review-agentforce-action": ["P11"],
    "review-data-model": ["P04", "P10"], "review": ["P04", "P06"],
    "scan-security": ["P07"], "score-deployment": ["P01", "P06"],
}

MAINTAINER_COMMANDS = {
    "add-skill", "build-skills", "new-agent", "new-skill", "onboard-source",
    "request-skill", "sync-upstream-skills",
}

TOOL_PRODUCT_MAP: dict[str, list[str]] = {
    "describe_org": ["P01", "P02", "P03", "P06", "P07", "P10", "P12"],
    "list_custom_objects": ["P04", "P09", "P10", "P12"],
    "list_flows_on_object": ["P04", "P05", "P10", "P12"],
    "validate_against_org": ["P04", "P06", "P10"],
    "list_validation_rules": ["P04", "P05", "P10", "P12"],
    "list_permission_sets": ["P03", "P07", "P12"],
    "describe_permission_set": ["P03", "P07", "P12"],
    "list_record_types": ["P03", "P04", "P12"],
    "list_named_credentials": ["P07", "P08", "P10", "P12"],
    "list_approval_processes": ["P04", "P05", "P10", "P12"],
    "probe_apex_references": ["P01", "P02", "P04", "P06"],
    "probe_flow_references": ["P01", "P04", "P05", "P06"],
    "probe_matching_rules": ["P04", "P07", "P10"],
    "probe_permset_shape": ["P03", "P07", "P12"],
    "probe_automation_graph": ["P04", "P05", "P10", "P12"],
    "list_apex_classes": ["P01", "P02", "P04", "P06", "P10", "P12"],
    "get_apex_class": ["P01", "P02", "P04", "P06"],
    "list_apex_triggers": ["P04", "P05", "P10", "P12"],
    "list_lwc_bundles": ["P04", "P06", "P10", "P12"],
    "get_lwc_bundle": ["P04", "P06"], "list_custom_fields": ["P03", "P04", "P09", "P12"],
    "describe_object_full": ["P03", "P04", "P05", "P09", "P10", "P12"],
    "list_orgs": ["P12"],
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def split_frontmatter(text: str) -> dict[str, Any]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    data = yaml.safe_load(text[4:end]) or {}
    return data if isinstance(data, dict) else {}


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def skill_rows(source: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted((source / "skills").glob("*/*/SKILL.md")):
        rel = path.relative_to(source).as_posix()
        meta = split_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
        skill_id = "/".join(path.relative_to(source / "skills").parts[:2])
        deps = meta.get("dependencies") or []
        triggers = meta.get("triggers") or []
        pillars = meta.get("well-architected-pillars") or []
        rows.append({
            "skill_id": skill_id,
            "domain": skill_id.split("/", 1)[0],
            "name": meta.get("name", path.parent.name),
            "description": str(meta.get("description", "")).replace("\n", " "),
            "version": meta.get("version", ""),
            "salesforce_version": meta.get("salesforce-version", ""),
            "runtime_orphan": str(bool(meta.get("runtime_orphan", False))).lower(),
            "trigger_count": len(triggers) if isinstance(triggers, list) else 0,
            "dependency_count": len(deps) if isinstance(deps, list) else 0,
            "well_architected_pillars": ";".join(str(x) for x in pillars),
            "path": rel,
            "sha256": sha256(path),
            "v2_disposition": "retain-knowledge-substrate",
            "native_host_default": "false",
            "selection_contract": "progressive-on-demand",
            "migration_notes": "Do not flatten into always-on host context; preserve package and evaluate through product context packs.",
        })
    return rows


def load_inventory() -> dict[str, Any]:
    return json.loads((OUT / "current-repository-inventory.json").read_text(encoding="utf-8"))


def agent_rows(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in inventory["agents"]:
        aid = item["id"]
        products = PRODUCT_MAP.get(aid, [])
        if item["class"] == "build":
            disposition = "preserve-maintainer-agent"
            action = "Keep outside the default product runtime; validate independently."
        elif item["status"] == "deprecated":
            disposition = "preserve-deprecation-redirect"
            action = "Retain redirect until replacement parity and migration tests pass."
        elif products:
            disposition = "reuse-as-legacy-specialist"
            action = "Reuse knowledge and proven steps during mapped product integration; do not auto-export as a native subagent."
        else:
            disposition = "preserve-legacy-specialist"
            action = "Keep reachable through legacy routing; promote only after a product job and behavioral QA justify it."
        rows.append({
            "agent_id": aid, "class": item["class"], "status": item["status"],
            "path": item["path"], "version": item.get("version", ""),
            "mapped_v2_products": ";".join(products), "v2_disposition": disposition,
            "native_host_default": "false", "required_action": action,
        })
    return rows


def command_rows(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in inventory["commands"]:
        cid = item["id"]
        products = COMMAND_PRODUCT_MAP.get(cid, [])
        if cid in MAINTAINER_COMMANDS:
            disposition = "preserve-maintainer-command"
            action = "Keep out of the end-user product surface and validate under maintainer policy."
        elif products:
            disposition = "preserve-legacy-alias-or-input"
            action = "Keep compatibility; map useful behavior into typed product commands only when the mapped product is implemented."
        else:
            disposition = "preserve-legacy-command"
            action = "Do not remove; assess from usage evidence before migration or deprecation."
        rows.append({
            "command_id": cid, "path": item["path"], "current_agents": ";".join(item.get("agents", [])),
            "mapped_v2_products": ";".join(products), "v2_disposition": disposition,
            "default_v2_surface": "false", "required_action": action,
        })
    return rows


def tool_rows(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    knowledge = {"search_skill", "get_skill", "list_agents", "get_agent", "search_agents", "search_templates", "search_decision_trees", "get_template", "get_decision_tree", "suggest_agent"}
    control = {"health", "list_deprecated_redirects", "get_invocation_modes", "emit_envelope"}
    rows = []
    for item in inventory["mcp_tools"]:
        tid = item["name"]
        products = TOOL_PRODUCT_MAP.get(tid, [])
        if tid == "tooling_query":
            disposition = "broker-internal-restricted"
            action = "Never expose directly to a product agent; require a typed broker operation and SOQL/policy validation."
        elif tid in knowledge:
            disposition = "retain-knowledge-plane"
            action = "Preserve; add bounded result and explicit index/error semantics where missing."
        elif tid in control:
            disposition = "retain-control-plane"
            action = "Preserve locally; align envelopes and doctor behavior with V2 contracts."
        elif products:
            disposition = "wrap-as-normalized-evidence"
            action = "Keep implementation where sound; expose only through typed read-only V2 evidence contracts."
        else:
            disposition = "preserve-unmapped-read-tool"
            action = "Keep for compatibility; do not grant to products until mapped and contract-tested."
        rows.append({
            "tool_id": tid, "function": item.get("function", ""), "annotations": item.get("annotations", ""),
            "argument_count": len(item.get("arguments", [])), "mapped_v2_products": ";".join(products),
            "v2_disposition": disposition, "direct_product_exposure": "false", "required_action": action,
        })
    return rows


def render_summary(counts: dict[str, int], snapshot_sha: str) -> str:
    return f"""# Legacy surface V2 disposition ledger

These generated ledgers give every artifact in the uploaded SfSkills snapshot an explicit V2 posture. They prevent implementation work from silently deleting, flattening, auto-exporting, or duplicating the existing system.

## Snapshot

- Uploaded archive SHA-256: `{snapshot_sha or 'not supplied'}`
- Skills: {counts['skills']}
- Canonical agents: {counts['agents']}
- Commands: {counts['commands']}
- MCP tools: {counts['tools']}

## Binding migration rules

1. `retain-knowledge-substrate` means preserve the skill package and load it progressively; it does not become an always-on host rule.
2. Legacy runtime agents are not automatically exported as native subagents.
3. Deprecated agents remain redirects until replacement parity and migration tests pass.
4. Legacy commands remain compatible until evidence supports migration or deprecation.
5. Raw/broad query tools remain broker-internal; products receive typed read-only evidence operations.
6. A mapping to a V2 product is an integration input, not proof that the legacy artifact already satisfies the V2 contract.
7. Cursor must update the corresponding ledger row, traceability, and tests when it changes a legacy artifact's disposition.

## Files

- `current-skills.csv` — all skill packages and preservation policy.
- `current-agents.csv` — all canonical agent definitions and product alignment.
- `current-commands.csv` — all command wrappers and compatibility posture.
- `current-mcp-tools.csv` — all registered MCP tools and broker posture.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True, help="Path to extracted AwesomeSalesforceSkills repository")
    parser.add_argument("--snapshot-sha256", default="")
    args = parser.parse_args()
    source = args.source.resolve()
    if not (source / "skills").is_dir() or not (source / "agents").is_dir():
        raise SystemExit(f"not an SfSkills repository: {source}")
    inventory = load_inventory()
    skills = skill_rows(source)
    agents = agent_rows(inventory)
    commands = command_rows(inventory)
    tools = tool_rows(inventory)
    write_csv(OUT / "current-skills.csv", skills, list(skills[0]))
    write_csv(OUT / "current-agents.csv", agents, list(agents[0]))
    write_csv(OUT / "current-commands.csv", commands, list(commands[0]))
    write_csv(OUT / "current-mcp-tools.csv", tools, list(tools[0]))
    counts = {"skills": len(skills), "agents": len(agents), "commands": len(commands), "tools": len(tools)}
    (OUT / "V2_DISPOSITION_LEDGER.md").write_text(render_summary(counts, args.snapshot_sha256), encoding="utf-8")
    print(json.dumps(counts, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
