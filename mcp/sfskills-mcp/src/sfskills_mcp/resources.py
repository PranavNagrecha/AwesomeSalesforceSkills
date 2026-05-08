"""Expose the SfSkills knowledge layer as MCP Resources.

MCP has three first-class primitives — Tools, Prompts, Resources. The
prototype only exposed Tools, which forces a tool round-trip for every skill
read. Resources let the client pre-list available knowledge artefacts and
fetch their bodies on demand without firing a tool, which is faster and
plays better with clients that pin retrieved context to the chat sidebar.

Five resource shapes:

- ``sfskills://catalog``                — slim list of every registered skill
                                          (id, category, description). One
                                          payload, ~150 KB on the current
                                          registry.
- ``sfskills://skill/{id}``             — full ``SKILL.md`` markdown for one
                                          skill. Use the ``domain__name`` form
                                          (e.g. ``apex__trigger-framework``)
                                          because MCP URI templates only match
                                          single path segments.
- ``sfskills://decision-tree/{name}``   — a routing tree under
                                          ``standards/decision-trees/``,
                                          identified by basename without
                                          ``.md`` (e.g. ``automation-selection``).
- ``sfskills://template/{path}``        — a canonical building block under
                                          ``templates/``. Same path-encoding:
                                          ``apex__TriggerHandler.cls`` rather
                                          than ``apex/TriggerHandler.cls``.
- ``sfskills://agent/{name}``           — full AGENT.md body for one agent.

Each ``read_resource`` returns the markdown text directly; the catalog returns
JSON.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

from . import paths, skills

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


# Used for both decision-tree names and template paths. Avoid path-traversal
# (``..``) and reject anything that looks like an absolute path.
_SAFE_NAME = re.compile(r"^[a-zA-Z0-9][\w./-]*$")


def _decision_trees_dir() -> Path:
    return paths.repo_root() / "standards" / "decision-trees"


def _templates_dir() -> Path:
    return paths.repo_root() / "templates"


def _agents_dir() -> Path:
    return paths.repo_root() / "agents"


# --------------------------------------------------------------------------- #
# Catalog                                                                     #
# --------------------------------------------------------------------------- #


@lru_cache(maxsize=1)
def skill_catalog_payload() -> str:
    """Return a slim JSON catalog of every registered skill.

    Cached — regenerating this on every fetch (981 entries, ~150 KB) wastes
    cycles for what's essentially static data during a server lifetime.
    """
    try:
        path = paths.registry_skills_json()
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return json.dumps({"error": f"registry unavailable: {e}", "skills": []})
    slim = [
        {
            "id": s.get("id"),
            "category": s.get("category"),
            "description": s.get("description"),
            "tags": s.get("tags", []),
        }
        for s in registry.get("skills", [])
    ]
    return json.dumps(
        {"skill_count": len(slim), "skills": slim},
        indent=2,
        ensure_ascii=False,
    )


# --------------------------------------------------------------------------- #
# Skill / agent / template / decision-tree readers                            #
# --------------------------------------------------------------------------- #


def read_skill(skill_id: str) -> str:
    """Return ``SKILL.md`` markdown for the given skill id, or a stub error."""
    payload = skills.get_skill(
        skill_id=skill_id,
        include_markdown=True,
        include_references=False,
    )
    if "error" in payload:
        return f"# Skill not found\n\n{payload['error']}\n"
    return payload.get("markdown", "")


def read_agent(agent_name: str) -> str:
    """Return AGENT.md markdown for the given agent."""
    if not _SAFE_NAME.match(agent_name or ""):
        return f"# Invalid agent name\n\n{agent_name!r} contains unsafe characters.\n"
    md = _agents_dir() / agent_name / "AGENT.md"
    if not md.exists():
        return f"# Agent not found\n\nNo AGENT.md at {md.relative_to(paths.repo_root())}\n"
    return md.read_text(encoding="utf-8")


def read_decision_tree(name: str) -> str:
    """Return the markdown body of a decision tree by basename (no ``.md``)."""
    if not _SAFE_NAME.match(name or ""):
        return f"# Invalid name\n\n{name!r} contains unsafe characters.\n"
    candidate = _decision_trees_dir() / f"{name}.md"
    if not candidate.exists():
        return f"# Decision tree not found\n\nNo file at standards/decision-trees/{name}.md\n"
    return candidate.read_text(encoding="utf-8")


def read_template(path: str) -> str:
    """Return the contents of a canonical template by relative path.

    Accepts both ``apex/TriggerHandler.cls`` (real on-disk shape) and
    ``apex__TriggerHandler.cls`` (URI-friendly form, since MCP resource
    templates can't match multiple path segments). Path traversal (``..``)
    and absolute paths are rejected.
    """
    if not path:
        return "// path is required\n"
    # Decode the URI-friendly double-underscore form.
    decoded = path.replace("__", "/")
    if not _SAFE_NAME.match(decoded):
        return f"// invalid path {path!r}\n"
    if ".." in decoded.split("/"):
        return f"// path traversal rejected: {path!r}\n"
    candidate = _templates_dir() / decoded
    try:
        candidate = candidate.resolve()
        candidate.relative_to(_templates_dir().resolve())
    except (OSError, ValueError):
        return f"// path resolves outside templates/: {path!r}\n"
    if not candidate.exists() or not candidate.is_file():
        return f"// template not found: templates/{decoded}\n"
    return candidate.read_text(encoding="utf-8", errors="replace")


# --------------------------------------------------------------------------- #
# Discovery (used by listing helpers and tests)                               #
# --------------------------------------------------------------------------- #


def list_decision_tree_names() -> list[str]:
    out: list[str] = []
    root = _decision_trees_dir()
    if not root.exists():
        return out
    for p in sorted(root.iterdir()):
        if p.suffix == ".md" and p.stem != "README":
            out.append(p.stem)
    return out


def list_template_paths() -> list[str]:
    """Return every regular file under ``templates/`` as a relative path."""
    out: list[str] = []
    root = _templates_dir()
    if not root.exists():
        return out
    for p in sorted(root.rglob("*")):
        if p.is_file() and not p.name.startswith("."):
            out.append(str(p.relative_to(root)).replace("\\", "/"))
    return out


# --------------------------------------------------------------------------- #
# Registration                                                                #
# --------------------------------------------------------------------------- #


def register_all(mcp: "FastMCP") -> dict[str, int]:
    """Register every resource shape on ``mcp``.

    Returns a dict ``{static_count, template_count}`` — useful for the test
    suite and for the ``health`` tool we'll add in Tier D.
    """
    @mcp.resource(
        "sfskills://catalog",
        name="catalog",
        description="Slim list of every registered SfSkills skill (id, category, description, tags).",
        mime_type="application/json",
    )
    def _catalog() -> str:
        return skill_catalog_payload()

    @mcp.resource(
        "sfskills://skill/{skill_id}",
        name="skill",
        description="Full SKILL.md markdown for a given skill id (e.g. 'apex/trigger-framework').",
        mime_type="text/markdown",
    )
    def _skill(skill_id: str) -> str:
        return read_skill(skill_id)

    @mcp.resource(
        "sfskills://agent/{agent_name}",
        name="agent",
        description="Full AGENT.md instruction file for a named agent (e.g. 'apex-refactorer').",
        mime_type="text/markdown",
    )
    def _agent(agent_name: str) -> str:
        return read_agent(agent_name)

    @mcp.resource(
        "sfskills://decision-tree/{name}",
        name="decision-tree",
        description="Markdown body of a routing decision tree from standards/decision-trees/.",
        mime_type="text/markdown",
    )
    def _tree(name: str) -> str:
        return read_decision_tree(name)

    @mcp.resource(
        "sfskills://template/{path}",
        name="template",
        description="Contents of a canonical building block under templates/ (TriggerHandler, ApplicationLogger, …).",
        mime_type="text/plain",
    )
    def _template(path: str) -> str:
        return read_template(path)

    return {
        "static_count": 1,    # only the catalog has a fixed URI
        "template_count": 4,  # skill / agent / decision-tree / template
    }
