"""Expose SfSkills run-time agents over MCP.

An *agent* in this repo is an instruction document — ``agents/<name>/AGENT.md`` —
that any agentic LLM can read and follow. The MCP server does not execute the
agent; it surfaces the instructions so the client's own model can run them with
full skill-library + live-org context.

Two tools are exposed:

- ``list_agents`` — enumerate available agents (runtime + build-time +
  deprecated), with a one-line description pulled from the AGENT.md
  ``## What This Agent Does`` section.
- ``get_agent`` — fetch the full AGENT.md body plus a normalized metadata block
  the client can use to render tool arguments, citations, etc.

Agent classification is read from each AGENT.md's frontmatter at runtime:

    class:  runtime | build           — defined for every agent
    status: stable  | deprecated …    — agents with ``status: deprecated`` are
                                        redirect stubs; see
                                        ``list_deprecated_redirects``.

The MCP exposes four ``kind`` filters:

    "runtime"     — class:runtime AND not status:deprecated  (active runtime)
    "build"       — class:build                              (skill-factory)
    "deprecated"  — class:runtime AND status:deprecated      (redirect stubs)
    "all" / None  — everything

The tools intentionally return plain data (no side effects on the repo or the
target org). All execution lives in the caller's model.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from . import paths


# Frontmatter parsing — stdlib-only. The package keeps a single dependency
# (``mcp``); we will not pull in PyYAML for what amounts to two grep-equivalent
# field reads.
_FRONTMATTER_FENCE = "---"


def _read_frontmatter_field(md_path: Path, field: str) -> str | None:
    """Return the first scalar value of ``field`` in the frontmatter block.

    Reads only the leading frontmatter block (everything between the first two
    ``---`` fences). Returns ``None`` if the file has no frontmatter or the
    field is absent.
    """
    if not md_path.exists():
        return None
    pattern = re.compile(rf"^{re.escape(field)}\s*:\s*(.+?)\s*$")
    in_fm = False
    try:
        with md_path.open("r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.rstrip("\n")
                stripped = line.strip()
                if stripped == _FRONTMATTER_FENCE:
                    if not in_fm:
                        in_fm = True
                        continue
                    # Closing fence — stop reading.
                    return None
                if not in_fm:
                    # Files must start with frontmatter; if the first non-empty
                    # line isn't ``---`` there's nothing to parse.
                    if stripped:
                        return None
                    continue
                m = pattern.match(line)
                if m:
                    value = m.group(1).strip().strip("\"'")
                    return value or None
    except OSError:
        return None
    return None


@lru_cache(maxsize=1)
def _agent_classes() -> dict[str, str]:
    """Return ``{agent_name: kind}`` resolved from each AGENT.md's frontmatter.

    ``kind`` is one of ``runtime``, ``build``, ``deprecated``, or ``unknown``.
    """
    out: dict[str, str] = {}
    root = _agents_dir()
    if not root.exists():
        return out
    for entry in sorted(root.iterdir()):
        if not entry.is_dir() or entry.name.startswith((".", "_")):
            continue
        md = entry / "AGENT.md"
        if not md.exists():
            continue
        cls = _read_frontmatter_field(md, "class")
        status = _read_frontmatter_field(md, "status")
        if cls == "runtime":
            kind = "deprecated" if status == "deprecated" else "runtime"
        elif cls == "build":
            kind = "build"
        else:
            kind = "unknown"
        out[entry.name] = kind
    return out


def runtime_agent_count() -> int:
    """Active (non-deprecated) runtime agent count. Used by server descriptions."""
    return sum(1 for v in _agent_classes().values() if v == "runtime")


def total_agent_count() -> int:
    return len(_agent_classes())


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


_KIND_FILTER_VALUES = {"runtime", "build", "deprecated", "all", None}


def list_agents(kind: str | None = None) -> dict[str, Any]:
    """List agents available in the repo.

    ``kind`` filters the result set:

    - ``"runtime"`` — active user-facing agents (``class: runtime`` and not
      ``status: deprecated``)
    - ``"build"`` — skill-factory agents
    - ``"deprecated"`` — runtime stubs that redirect; pair with
      ``list_deprecated_redirects`` to find their canonical replacement
    - ``None`` / ``"all"`` — every agent
    """
    if kind not in _KIND_FILTER_VALUES:
        return {
            "agents": [],
            "count": 0,
            "error": (
                f"unknown kind {kind!r}; expected one of "
                f"{sorted(v for v in _KIND_FILTER_VALUES if v)}"
            ),
        }

    root = _agents_dir()
    if not root.exists():
        return {"agents": [], "count": 0, "error": f"agents directory not found at {root}"}

    classes = _agent_classes()
    items: list[dict[str, Any]] = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir() or entry.name.startswith((".", "_")):
            continue
        md = entry / "AGENT.md"
        if not md.exists():
            continue
        agent_kind = classes.get(entry.name, "unknown")
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
    kind = _agent_classes().get(agent_name, "unknown")
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
