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
