"""Expose SfSkills run-time agents over MCP.

An *agent* in this repo is an instruction document — ``agents/<name>/AGENT.md`` —
that any agentic LLM can read and follow. The MCP server does not execute the
agent; it surfaces the instructions so the client's own model can run them with
full skill-library + live-org context.

Two tools are exposed:

- ``list_agents`` — enumerate available agents (run-time + build-time), with a
  one-line description pulled from the AGENT.md "What This Agent Does" section.
- ``get_agent`` — fetch the full AGENT.md body plus a normalized metadata block
  the client can use to render tool arguments, citations, etc.

The tools intentionally return plain data (no side effects on the repo or the
target org). All execution lives in the caller's model.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from . import paths


_RUNTIME_AGENTS = frozenset(
    {
        # Wave-1 developer + architecture tier (11)
        "apex-refactorer",
        "trigger-consolidator",
        "test-class-generator",
        "soql-optimizer",
        "security-scanner",
        "flow-analyzer",
        "bulk-migration-planner",
        "lwc-auditor",
        "deployment-risk-scorer",
        "agentforce-builder",
        "org-drift-detector",
        # Wave A — Tier-1 admin accelerators (8)
        "field-impact-analyzer",
        "object-designer",
        "permission-set-architect",
        "flow-builder",
        "workflow-and-pb-migrator",
        "validation-rule-auditor",
        "data-loader-pre-flight",
        "duplicate-rule-designer",
        # Wave B — Tier-2 strategic (10)
        "sharing-audit-agent",
        "lightning-record-page-auditor",
        "approval-to-flow-orchestrator-migrator",
        "record-type-and-layout-auditor",
        "picklist-governor",
        "data-model-reviewer",
        "integration-catalog-builder",
        "report-and-dashboard-auditor",
        "csv-to-object-mapper",
        "email-template-modernizer",
        # Wave C — Tier-3 vertical + governance (10)
        "omni-channel-routing-designer",
        "knowledge-article-taxonomy-agent",
        "sales-stage-designer",
        "lead-routing-rules-designer",
        "case-escalation-auditor",
        "sandbox-strategy-designer",
        "release-train-planner",
        "waf-assessor",
        "agentforce-action-reviewer",
        "prompt-library-governor",
    }
)


def _agents_dir() -> Path:
    return paths.repo_root() / "agents"


def _agent_md_path(agent_name: str) -> Path:
    return _agents_dir() / agent_name / "AGENT.md"


def _first_paragraph_after(markdown: str, heading: str) -> str:
    """Return the first non-empty paragraph after ``## <heading>``.

    Falls back to the first non-empty paragraph of the document.
    """
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.MULTILINE)
    m = pattern.search(markdown)
    body = markdown[m.end():] if m else markdown
    for chunk in re.split(r"\n\s*\n", body.strip()):
        chunk = chunk.strip()
        if chunk and not chunk.startswith("#"):
            return chunk
    return ""


def list_agents(kind: str | None = None) -> dict[str, Any]:
    """List agents available in the repo.

    ``kind`` filters the result set: ``"runtime"`` returns only user-facing
    agents (the ones in :data:`_RUNTIME_AGENTS`), ``"build"`` returns only
    the skill-factory agents, and ``None`` / ``"all"`` returns both.
    """
    root = _agents_dir()
    if not root.exists():
        return {"agents": [], "error": f"agents directory not found at {root}"}

    items: list[dict[str, Any]] = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir() or entry.name.startswith((".", "_")):
            continue
        md = entry / "AGENT.md"
        if not md.exists():
            continue
        is_runtime = entry.name in _RUNTIME_AGENTS
        agent_kind = "runtime" if is_runtime else "build"
        if kind and kind != "all" and kind != agent_kind:
            continue
        body = md.read_text(encoding="utf-8")
        summary = _first_paragraph_after(body, "What This Agent Does")
        items.append(
            {
                "name": entry.name,
                "kind": agent_kind,
                "path": str(md.relative_to(paths.repo_root())),
                "summary": summary,
            }
        )
    return {"agents": items, "count": len(items)}


def get_agent(agent_name: str) -> dict[str, Any]:
    """Fetch a single agent's full instructions.

    Returns the raw markdown body plus a metadata block with the detected
    kind, invocation hint, and a relative path the client can use when
    writing citations.
    """
    md = _agent_md_path(agent_name)
    if not md.exists():
        return {
            "error": f"Agent '{agent_name}' not found. Call list_agents to see available agents.",
        }

    body = md.read_text(encoding="utf-8")
    kind = "runtime" if agent_name in _RUNTIME_AGENTS else "build"
    return {
        "name": agent_name,
        "kind": kind,
        "path": str(md.relative_to(paths.repo_root())),
        "summary": _first_paragraph_after(body, "What This Agent Does"),
        "markdown": body,
        "slash_command_hint": (
            f"Ask the AI to follow agents/{agent_name}/AGENT.md "
            f"or the matching commands/*.md wrapper."
        ),
    }
