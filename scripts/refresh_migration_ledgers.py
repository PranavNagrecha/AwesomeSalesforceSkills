#!/usr/bin/env python3
"""Refresh migration ledgers from the live repository.

Preserves existing disposition columns for unchanged artifact IDs and assigns
explicit V2 postures for known product-surface additions.
"""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_SCRIPTS = ROOT / "framework" / "specification" / "scripts"
OUT = ROOT / "framework" / "specification" / "migration" / "catalogs"

V2_AGENT_DISPOSITIONS: dict[str, tuple[str, str, str, str, str]] = {
    "deployment-failure-triager": (
        "runtime",
        "stable",
        "P01",
        "promote-native-product-agent",
        "Export as focused Cursor subagent for P01; not a legacy alias.",
    ),
    "apex-test-failure-triager": (
        "runtime",
        "stable",
        "P02",
        "promote-native-product-agent",
        "Export as focused Cursor subagent for P02; not a legacy alias.",
    ),
    "access-path-explainer": ("runtime", "stable", "P03", "promote-native-product-agent", "Export as focused Cursor subagent for P03."),
    "change-impact-planner": ("runtime", "stable", "P04", "promote-native-product-agent", "Export as focused Cursor subagent for P04."),
    "automation-transaction-profiler": ("runtime", "stable", "P05", "promote-native-product-agent", "Export as focused Cursor subagent for P05."),
    "release-readiness-reviewer": ("runtime", "stable", "P06", "promote-native-product-agent", "Export as focused Cursor subagent for P06."),
    "security-posture-reviewer": ("runtime", "stable", "P07", "promote-native-product-agent", "Export as focused Cursor subagent for P07."),
    "integration-incident-triager": ("runtime", "stable", "P08", "promote-native-product-agent", "Export as focused Cursor subagent for P08."),
    "data-migration-reconciler": ("runtime", "stable", "P09", "promote-native-product-agent", "Export as focused Cursor subagent for P09."),
    "org-health-assessor-v2": ("runtime", "stable", "P10", "promote-native-product-agent", "Export as focused Cursor subagent for P10."),
    "agentforce-quality-engineer": ("runtime", "stable", "P11", "promote-native-product-agent", "Export as focused Cursor subagent for P11."),
    "multi-org-drift-analyzer": ("runtime", "stable", "P12", "promote-native-product-agent", "Export as focused Cursor subagent for P12."),
}

V2_COMMAND_DISPOSITIONS: dict[str, tuple[str, str, str, str]] = {
    "triage-deployment": (
        "deployment-failure-triager",
        "P01",
        "promote-native-product-command",
        "true",
        "Primary P01 entry command; requires independent review and read-only broker.",
    ),
    "sfskills-doctor": (
        "",
        "",
        "promote-native-framework-command",
        "true",
        "Framework doctor/install verification; not a legacy alias.",
    ),
    "triage-apex-tests": (
        "apex-test-failure-triager",
        "P02",
        "promote-native-product-command",
        "true",
        "Primary P02 entry command; requires independent review and read-only broker.",
    ),
    "why-cant-user": ("access-path-explainer", "P03", "promote-native-product-command", "true", "Primary P03 entry command."),
    "plan-metadata-change": ("change-impact-planner", "P04", "promote-native-product-command", "true", "Primary P04 entry command."),
    "profile-automation": ("automation-transaction-profiler", "P05", "promote-native-product-command", "true", "Primary P05 entry command."),
    "review-release-readiness": ("release-readiness-reviewer", "P06", "promote-native-product-command", "true", "Primary P06 entry command."),
    "review-security-posture": ("security-posture-reviewer", "P07", "promote-native-product-command", "true", "Primary P07 entry command."),
    "triage-integration": ("integration-incident-triager", "P08", "promote-native-product-command", "true", "Primary P08 entry command."),
    "reconcile-data-load": ("data-migration-reconciler", "P09", "promote-native-product-command", "true", "Primary P09 entry command."),
    "assess-org-health": ("org-health-assessor-v2", "P10", "promote-native-product-command", "true", "Primary P10 entry command."),
    "review-agentforce-agent": ("agentforce-quality-engineer", "P11", "promote-native-product-command", "true", "Primary P11 entry command."),
    "compare-orgs": ("multi-org-drift-analyzer", "P12", "promote-native-product-command", "true", "Primary P12 entry command."),
}


def _merge_agent_row(existing: dict[str, str] | None, agent_id: str, path: str) -> dict[str, str]:
    if agent_id in V2_AGENT_DISPOSITIONS:
        _class, status, products, disposition, action = V2_AGENT_DISPOSITIONS[agent_id]  # type: ignore[misc]
        return {
            "agent_id": agent_id,
            "class": _class,
            "status": status,
            "path": path,
            "version": existing.get("version", "") if existing else "",
            "mapped_v2_products": products,
            "v2_disposition": disposition,
            "native_host_default": "true",
            "required_action": action,
        }
    if existing:
        existing = dict(existing)
        existing["path"] = path
        return existing
    return {
        "agent_id": agent_id,
        "class": "runtime",
        "status": "stable",
        "path": path,
        "version": "",
        "mapped_v2_products": "",
        "v2_disposition": "preserve-legacy-specialist",
        "native_host_default": "false",
        "required_action": "Ledger row added during live reconciliation; assess disposition.",
    }


V2_MCP_TOOL_DISPOSITIONS: dict[str, tuple[str, str, str, str]] = {
    "get_deployment_result": (
        "get_deployment_result",
        "_ANN_ORG_READ",
        "P01",
        "wrap-as-normalized-evidence",
        "P01 typed deployment evidence; broker-internal only.",
    ),
    "get_apex_test_run": ("get_apex_test_run", "_ANN_ORG_READ", "P02", "wrap-as-normalized-evidence", "P02 typed Apex test evidence; broker-internal only."),
    "get_user_access_evidence": ("get_user_access_evidence", "_ANN_ORG_READ", "P03", "wrap-as-normalized-evidence", "P03 typed access evidence; broker-internal only."),
    "get_component_dependency_evidence": ("get_component_dependency_evidence", "_ANN_ORG_READ", "P04", "wrap-as-normalized-evidence", "P04 typed dependency evidence; broker-internal only."),
    "get_automation_inventory": ("get_automation_inventory", "_ANN_ORG_READ", "P05", "wrap-as-normalized-evidence", "P05 typed automation inventory; broker-internal only."),
    "get_flow_test_result": ("get_flow_test_result", "_ANN_ORG_READ", "P06", "wrap-as-normalized-evidence", "P06 typed flow-test evidence; broker-internal only."),
    "get_code_analysis_result": ("get_code_analysis_result", "_ANN_ORG_READ", "P07", "wrap-as-normalized-evidence", "P07 typed code-analysis evidence; broker-internal only."),
    "get_integration_config_summary": ("get_integration_config_summary", "_ANN_ORG_READ", "P08", "wrap-as-normalized-evidence", "P08 typed integration evidence; broker-internal only."),
    "get_data_load_result": ("get_data_load_result", "_ANN_ORG_READ", "P09", "wrap-as-normalized-evidence", "P09 typed data-load evidence; broker-internal only."),
    "get_org_snapshot_manifest": ("get_org_snapshot_manifest", "_ANN_ORG_READ", "P10", "wrap-as-normalized-evidence", "P10 typed org-snapshot evidence; broker-internal only."),
    "get_agentforce_test_result": ("get_agentforce_test_result", "_ANN_ORG_READ", "P11", "wrap-as-normalized-evidence", "P11 typed Agentforce test evidence; broker-internal only."),
    "compare_org_snapshots": ("compare_org_snapshots", "_ANN_ORG_READ", "P12", "wrap-as-normalized-evidence", "P12 typed org-compare evidence; broker-internal only."),
}


def _merge_tool_row(existing: dict[str, str] | None, tool_id: str) -> dict[str, str]:
    if tool_id in V2_MCP_TOOL_DISPOSITIONS:
        function, annotations, products, disposition, action = V2_MCP_TOOL_DISPOSITIONS[tool_id]
        return {
            "tool_id": tool_id,
            "function": function,
            "annotations": annotations,
            "argument_count": existing.get("argument_count", "") if existing else "",
            "mapped_v2_products": products,
            "v2_disposition": disposition,
            "direct_product_exposure": "false",
            "required_action": action,
        }
    if existing:
        return dict(existing)
    return {
        "tool_id": tool_id,
        "function": tool_id,
        "annotations": "",
        "argument_count": "",
        "mapped_v2_products": "",
        "v2_disposition": "preserve-unmapped-read-tool",
        "direct_product_exposure": "false",
        "required_action": "Ledger row added during live reconciliation; assess disposition.",
    }


def _merge_command_row(existing: dict[str, str] | None, command_id: str, path: str) -> dict[str, str]:
    if command_id in V2_COMMAND_DISPOSITIONS:
        agents, products, disposition, surface, action = V2_COMMAND_DISPOSITIONS[command_id]
        return {
            "command_id": command_id,
            "path": path,
            "current_agents": agents,
            "mapped_v2_products": products,
            "v2_disposition": disposition,
            "default_v2_surface": surface,
            "required_action": action,
        }
    if existing:
        existing = dict(existing)
        existing["path"] = path
        return existing
    return {
        "command_id": command_id,
        "path": path,
        "current_agents": "",
        "mapped_v2_products": "",
        "v2_disposition": "preserve-legacy-command",
        "default_v2_surface": "false",
        "required_action": "Ledger row added during live reconciliation; assess disposition.",
    }


def _read_csv(path: Path, id_column: str) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {(row.get(id_column) or ""): row for row in rows if row.get(id_column)}


def _write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from pipelines.framework.migration_reconcile import (  # noqa: PLC0415
        _discover_agents,
        _discover_commands,
        _discover_mcp_tools,
        _discover_skills,
    )

    proc = subprocess.run(  # noqa: S603
        [
            sys.executable,
            str(SPEC_SCRIPTS / "build_legacy_migration_ledgers.py"),
            "--source",
            str(ROOT),
        ],
        cwd=SPEC_SCRIPTS.parent,
        check=False,
    )
    if proc.returncode != 0:
        return proc.returncode

    live_agents = _discover_agents(ROOT)
    live_commands = _discover_commands(ROOT)
    existing_agents = _read_csv(OUT / "current-agents.csv", "agent_id")
    existing_commands = _read_csv(OUT / "current-commands.csv", "command_id")

    agent_fields = list(next(iter(existing_agents.values())).keys()) if existing_agents else [
        "agent_id", "class", "status", "path", "version", "mapped_v2_products",
        "v2_disposition", "native_host_default", "required_action",
    ]
    command_fields = list(next(iter(existing_commands.values())).keys()) if existing_commands else [
        "command_id", "path", "current_agents", "mapped_v2_products", "v2_disposition",
        "default_v2_surface", "required_action",
    ]

    agent_rows = [
        _merge_agent_row(existing_agents.get(aid), aid, path)
        for aid, path in sorted(live_agents.items())
    ]
    command_rows = [
        _merge_command_row(existing_commands.get(cid), cid, path)
        for cid, path in sorted(live_commands.items())
    ]
    _write_csv(OUT / "current-agents.csv", agent_rows, agent_fields)
    _write_csv(OUT / "current-commands.csv", command_rows, command_fields)

    live_tools = _discover_mcp_tools(ROOT)
    existing_tools = _read_csv(OUT / "current-mcp-tools.csv", "tool_id")
    tool_fields = list(next(iter(existing_tools.values())).keys()) if existing_tools else [
        "tool_id", "function", "annotations", "argument_count", "mapped_v2_products",
        "v2_disposition", "direct_product_exposure", "required_action",
    ]
    tool_rows = [
        _merge_tool_row(existing_tools.get(tid), tid)
        for tid in sorted(live_tools)
    ]
    _write_csv(OUT / "current-mcp-tools.csv", tool_rows, tool_fields)

    print(
        f"Refreshed ledgers: skills={len(_discover_skills(ROOT))} "
        f"agents={len(agent_rows)} commands={len(command_rows)} tools={len(tool_rows)}"
    )
    subprocess.run(  # noqa: S603
        [sys.executable, str(SPEC_SCRIPTS / "build_framework_manifest.py")],
        cwd=SPEC_SCRIPTS.parent,
        check=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
