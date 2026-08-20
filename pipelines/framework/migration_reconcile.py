"""Reconcile legacy migration ledgers against the live SfSkills repository."""

from __future__ import annotations

import ast
import csv
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LEDGER_DIR = ROOT / "framework" / "specification" / "migration" / "catalogs"
MCP_SERVER = ROOT / "mcp" / "sfskills-mcp" / "src" / "sfskills_mcp" / "server.py"


@dataclass(frozen=True)
class ReconcileDelta:
    artifact_class: str
    delta_kind: str
    artifact_id: str
    detail: str


@dataclass
class MigrationReconcileResult:
    valid: bool
    repo_root: str
    ledger_dir: str
    counts: dict[str, dict[str, int]] = field(default_factory=dict)
    deltas: list[ReconcileDelta] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["deltas"] = [asdict(item) for item in self.deltas]
        return payload


def _read_csv_ids(path: Path, id_column: str) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            artifact_id = (row.get(id_column) or "").strip()
            if not artifact_id:
                continue
            rows[artifact_id] = row
    return rows


def _discover_skills(repo: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    skills_root = repo / "skills"
    for skill_md in sorted(skills_root.glob("*/*/SKILL.md")):
        domain = skill_md.parent.parent.name
        name = skill_md.parent.name
        result[f"{domain}/{name}"] = skill_md.relative_to(repo).as_posix()
    return result


def _discover_agents(repo: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for agent_md in sorted((repo / "agents").glob("*/AGENT.md")):
        if agent_md.parent.name.startswith("_"):
            continue
        result[agent_md.parent.name] = agent_md.relative_to(repo).as_posix()
    return result


def _discover_commands(repo: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for command_md in sorted((repo / "commands").glob("*.md")):
        result[command_md.stem] = command_md.relative_to(repo).as_posix()
    return result


def _discover_mcp_tools(repo: Path) -> dict[str, str]:
    if not MCP_SERVER.is_file():
        return {}
    tree = ast.parse(MCP_SERVER.read_text(encoding="utf-8"))
    names: dict[str, str] = {}
    rel = MCP_SERVER.relative_to(repo).as_posix()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            is_tool = False
            if isinstance(decorator, ast.Call):
                func = decorator.func
                if isinstance(func, ast.Name) and func.id == "tool":
                    is_tool = True
                elif isinstance(func, ast.Attribute) and func.attr == "tool":
                    is_tool = True
            if is_tool:
                names[node.name] = rel
                break
    return names


def _compare_sets(
    artifact_class: str,
    live: dict[str, str],
    ledger: dict[str, dict[str, str]],
    id_column: str,
    path_column: str,
    *,
    compare_paths: bool = True,
) -> list[ReconcileDelta]:
    deltas: list[ReconcileDelta] = []
    live_ids = set(live)
    ledger_ids = set(ledger)
    for artifact_id in sorted(live_ids - ledger_ids):
        deltas.append(
            ReconcileDelta(
                artifact_class=artifact_class,
                delta_kind="added_in_repo",
                artifact_id=artifact_id,
                detail=live[artifact_id],
            )
        )
    for artifact_id in sorted(ledger_ids - live_ids):
        deltas.append(
            ReconcileDelta(
                artifact_class=artifact_class,
                delta_kind="missing_in_repo",
                artifact_id=artifact_id,
                detail=ledger[artifact_id].get(path_column, ""),
            )
        )
    for artifact_id in sorted(live_ids & ledger_ids):
        if not compare_paths:
            continue
        live_path = live[artifact_id]
        ledger_path = ledger[artifact_id].get(path_column, "")
        if ledger_path and live_path != ledger_path:
            deltas.append(
                ReconcileDelta(
                    artifact_class=artifact_class,
                    delta_kind="path_renamed",
                    artifact_id=artifact_id,
                    detail=f"ledger={ledger_path} live={live_path}",
                )
            )
    return deltas


def reconcile_migration_ledgers(
    repo_root: Path | None = None,
    ledger_dir: Path | None = None,
) -> MigrationReconcileResult:
    repo = (repo_root or ROOT).resolve()
    ledgers = (ledger_dir or LEDGER_DIR).resolve()
    result = MigrationReconcileResult(
        valid=True,
        repo_root=str(repo),
        ledger_dir=str(ledgers),
    )

    required = {
        "skills": ("current-skills.csv", "skill_id", "path"),
        "agents": ("current-agents.csv", "agent_id", "path"),
        "commands": ("current-commands.csv", "command_id", "path"),
        "mcp_tools": ("current-mcp-tools.csv", "tool_id", "function"),
    }
    live = {
        "skills": _discover_skills(repo),
        "agents": _discover_agents(repo),
        "commands": _discover_commands(repo),
        "mcp_tools": _discover_mcp_tools(repo),
    }

    for artifact_class, (filename, id_column, path_column) in required.items():
        ledger_path = ledgers / filename
        if not ledger_path.is_file():
            result.valid = False
            result.deltas.append(
                ReconcileDelta(
                    artifact_class=artifact_class,
                    delta_kind="ledger_missing",
                    artifact_id=filename,
                    detail=str(ledger_path),
                )
            )
            continue
        ledger_rows = _read_csv_ids(ledger_path, id_column)
        result.counts[artifact_class] = {
            "live": len(live[artifact_class]),
            "ledger": len(ledger_rows),
        }
        deltas = _compare_sets(
            artifact_class,
            live[artifact_class],
            ledger_rows,
            id_column,
            path_column,
            compare_paths=artifact_class != "mcp_tools",
        )
        result.deltas.extend(deltas)

    blocking = {
        item
        for item in result.deltas
        if item.delta_kind in {"added_in_repo", "missing_in_repo", "ledger_missing", "path_renamed"}
    }
    if blocking:
        result.valid = False
    return result


def write_reconciliation_report(result: MigrationReconcileResult, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Migration ledger reconciliation",
        "",
        f"- Repository: `{result.repo_root}`",
        f"- Ledger directory: `{result.ledger_dir}`",
        f"- Status: {'PASS' if result.valid else 'FAIL'}",
        "",
        "## Counts",
        "",
        "| Artifact class | Live | Ledger |",
        "| --- | ---: | ---: |",
    ]
    for artifact_class, counts in sorted(result.counts.items()):
        lines.append(f"| {artifact_class} | {counts['live']} | {counts['ledger']} |")
    lines.extend(["", "## Deltas", ""])
    if not result.deltas:
        lines.append("No deltas — every live artifact has an explicit ledger row with matching identity.")
    else:
        for item in result.deltas:
            lines.append(
                f"- **{item.artifact_class}** `{item.artifact_id}` — "
                f"{item.delta_kind}: {item.detail}"
            )
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
