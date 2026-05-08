"""Knowledge-search tools for the SfSkills MCP.

The skill library already has FTS5-backed search via ``skills.search_skill``,
but the rest of the knowledge layer — agents, templates, decision-trees —
isn't in the lexical index (the indexer walks ``skills/`` and a thin slice
of ``standards/`` only). Three small in-memory indexes here cover them:

- ``search_agents``         — score agents/<name>/AGENT.md by title + summary
                              + body keyword matches
- ``search_templates``      — score templates/<path> by path-token + body
                              keyword matches; useful for finding the right
                              canonical building block
- ``search_decision_trees`` — score standards/decision-trees/<name>.md by
                              tree title + per-section heading + body
                              keyword matches; returns the matching tree
                              plus its top section

Plus two readers for the LLM to pull the full body once it picks a result:

- ``get_template(path)``      — same as ``resources.read_template`` but
                                surfaced as a tool for clients that don't
                                speak Resources
- ``get_decision_tree(name)`` — same as ``resources.read_decision_tree``

Index size today: ~75 agents + ~72 templates + 6 trees = ~150 files. A naive
keyword scan reads the whole set on cold start (cached after) in ~10 ms.
Once the corpus crosses ~1000 files we'll move to a real FTS5 secondary
index; for now the simple scan keeps the dependency surface unchanged.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from . import paths, resources


# --------------------------------------------------------------------------- #
# Shared scoring                                                              #
# --------------------------------------------------------------------------- #


# Match word characters; case-insensitive comparison happens at scoring time.
_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def _tokenize(s: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(s or "")]


def _score(query_terms: list[str], *, title: str, headings: str, body: str) -> float:
    """Weighted token match. Title matches dominate; headings second; body third.

    Trivial scoring on purpose — the corpora here are small enough that even
    naive ranking gives the right top hit. Replace with FTS5 if accuracy
    starts to matter.
    """
    if not query_terms:
        return 0.0
    title_l = title.lower()
    headings_l = headings.lower()
    body_l = body.lower()
    score = 0.0
    for term in query_terms:
        score += 5.0 * title_l.count(term)
        score += 2.0 * headings_l.count(term)
        score += 1.0 * body_l.count(term)
    return score


def _bound_limit(limit: int, ceiling: int = 50) -> int:
    return max(1, min(int(limit or 10), ceiling))


# --------------------------------------------------------------------------- #
# search_agents                                                                #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class _AgentDoc:
    name: str
    path: str
    title: str
    summary: str
    body: str


@lru_cache(maxsize=1)
def _agent_corpus() -> tuple[_AgentDoc, ...]:
    out: list[_AgentDoc] = []
    root = paths.repo_root() / "agents"
    if not root.exists():
        return ()
    for entry in sorted(root.iterdir()):
        if not entry.is_dir() or entry.name.startswith((".", "_")):
            continue
        md = entry / "AGENT.md"
        if not md.exists():
            continue
        body = md.read_text(encoding="utf-8")
        # Title = first H1 if present, else the agent name. Summary = first
        # non-empty paragraph after "## What This Agent Does", which the
        # AGENT_CONTRACT requires.
        title = entry.name
        m = re.search(r"^#\s+(.+?)\s*$", body, re.MULTILINE)
        if m:
            title = m.group(1).strip()
        summary = ""
        m = re.search(r"^##\s+What This Agent Does\s*$(.*?)^## ", body, re.MULTILINE | re.DOTALL)
        if m:
            for chunk in re.split(r"\n\s*\n", m.group(1).strip()):
                chunk = chunk.strip()
                if chunk and not chunk.startswith("#"):
                    summary = chunk
                    break
        out.append(_AgentDoc(
            name=entry.name,
            path=str(md.relative_to(paths.repo_root())),
            title=title,
            summary=summary,
            body=body,
        ))
    return tuple(out)


def search_agents(query: str, limit: int = 10) -> dict[str, Any]:
    """Rank agents by token match against title + summary + body."""
    if not isinstance(query, str) or not query.strip():
        return {"error": "query is required", "query": query, "agents": []}
    bounded = _bound_limit(limit)
    terms = _tokenize(query)
    hits: list[tuple[float, _AgentDoc]] = []
    for doc in _agent_corpus():
        score = _score(terms, title=doc.title, headings=doc.summary, body=doc.body)
        if score > 0:
            hits.append((score, doc))
    hits.sort(key=lambda x: x[0], reverse=True)
    return {
        "query": query,
        "result_count": len(hits[:bounded]),
        "agents": [
            {
                "name": doc.name,
                "title": doc.title,
                "summary": doc.summary,
                "path": doc.path,
                "score": round(score, 3),
            }
            for score, doc in hits[:bounded]
        ],
    }


# --------------------------------------------------------------------------- #
# search_templates                                                             #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class _TemplateDoc:
    path: str               # e.g. "apex/TriggerHandler.cls"
    body: str


@lru_cache(maxsize=1)
def _template_corpus() -> tuple[_TemplateDoc, ...]:
    out: list[_TemplateDoc] = []
    root = paths.repo_root() / "templates"
    if not root.exists():
        return ()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        try:
            body = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        out.append(_TemplateDoc(
            path=str(path.relative_to(root)).replace("\\", "/"),
            body=body,
        ))
    return tuple(out)


def search_templates(query: str, limit: int = 10) -> dict[str, Any]:
    """Rank canonical templates. Path tokens (e.g. ``apex``,
    ``TriggerHandler``) are scored as title matches — finding
    ``apex/TriggerHandler.cls`` for the query "trigger handler" is the
    primary use case."""
    if not isinstance(query, str) or not query.strip():
        return {"error": "query is required", "query": query, "templates": []}
    bounded = _bound_limit(limit)
    terms = _tokenize(query)
    hits: list[tuple[float, _TemplateDoc]] = []
    for doc in _template_corpus():
        # Treat the path itself (apex/TriggerHandler.cls) as title-grade signal.
        path_title = doc.path.replace("/", " ").replace(".", " ")
        score = _score(terms, title=path_title, headings="", body=doc.body)
        if score > 0:
            hits.append((score, doc))
    hits.sort(key=lambda x: x[0], reverse=True)
    return {
        "query": query,
        "result_count": len(hits[:bounded]),
        "templates": [
            {
                "path": doc.path,
                "uri": f"sfskills://template/{doc.path.replace('/', '__')}",
                "preview": _first_n_lines(doc.body, 8),
                "score": round(score, 3),
            }
            for score, doc in hits[:bounded]
        ],
    }


def _first_n_lines(body: str, n: int) -> str:
    return "\n".join(body.splitlines()[:n])


# --------------------------------------------------------------------------- #
# search_decision_trees                                                        #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class _TreeDoc:
    name: str           # basename without .md
    title: str
    sections: tuple[tuple[str, str], ...]  # (heading, section_body) pairs
    body: str


@lru_cache(maxsize=1)
def _tree_corpus() -> tuple[_TreeDoc, ...]:
    out: list[_TreeDoc] = []
    root = paths.repo_root() / "standards" / "decision-trees"
    if not root.exists():
        return ()
    for path in sorted(root.iterdir()):
        if path.suffix != ".md" or path.stem == "README":
            continue
        body = path.read_text(encoding="utf-8")
        title = path.stem.replace("-", " ").title()
        m = re.search(r"^#\s+(.+?)\s*$", body, re.MULTILINE)
        if m:
            title = m.group(1).strip()
        # Carve sections by H2 / H3 headings — useful for "which subsection
        # answers my Flow vs Apex question".
        sections: list[tuple[str, str]] = []
        section_iter = re.finditer(r"^(#{2,3})\s+(.+?)\s*$", body, re.MULTILINE)
        last_end: int | None = None
        last_heading: str | None = None
        for m in section_iter:
            if last_heading is not None and last_end is not None:
                sections.append((last_heading, body[last_end:m.start()]))
            last_heading = m.group(2).strip()
            last_end = m.end()
        if last_heading is not None and last_end is not None:
            sections.append((last_heading, body[last_end:]))
        out.append(_TreeDoc(
            name=path.stem,
            title=title,
            sections=tuple(sections),
            body=body,
        ))
    return tuple(out)


def search_decision_trees(query: str, limit: int = 6) -> dict[str, Any]:
    """Rank decision trees by token match. For each ranked tree, also
    surface the section (H2/H3) inside it that matched best — agents are
    supposed to cite the specific branch that resolved their decision."""
    if not isinstance(query, str) or not query.strip():
        return {"error": "query is required", "query": query, "trees": []}
    bounded = _bound_limit(limit)
    terms = _tokenize(query)
    hits: list[tuple[float, _TreeDoc, str | None, float]] = []
    for doc in _tree_corpus():
        # Score the tree as a whole.
        section_titles = " ".join(s[0] for s in doc.sections)
        tree_score = _score(terms, title=doc.title, headings=section_titles, body=doc.body)
        if tree_score == 0:
            continue
        # Find best sub-section.
        best_section: str | None = None
        best_section_score = 0.0
        for heading, content in doc.sections:
            sec_score = _score(terms, title=heading, headings="", body=content)
            if sec_score > best_section_score:
                best_section_score = sec_score
                best_section = heading
        hits.append((tree_score, doc, best_section, best_section_score))
    hits.sort(key=lambda x: x[0], reverse=True)
    return {
        "query": query,
        "result_count": len(hits[:bounded]),
        "trees": [
            {
                "name": doc.name,
                "title": doc.title,
                "uri": f"sfskills://decision-tree/{doc.name}",
                "best_section": best_heading,
                "best_section_score": round(best_score, 3),
                "score": round(tree_score, 3),
            }
            for tree_score, doc, best_heading, best_score in hits[:bounded]
        ],
    }


# --------------------------------------------------------------------------- #
# get_template / get_decision_tree                                             #
# --------------------------------------------------------------------------- #


def get_template(path: str) -> dict[str, Any]:
    """Return one canonical template's contents. Wraps
    ``resources.read_template`` so MCP clients that don't speak Resources
    still have a tool path."""
    body = resources.read_template(path)
    if body.startswith("//") and ("invalid" in body or "rejected" in body or "not found" in body):
        return {"error": body.strip().lstrip("/").strip(), "path": path}
    return {"path": path, "body": body, "byte_size": len(body)}


def get_decision_tree(name: str) -> dict[str, Any]:
    """Return one decision tree's full markdown."""
    body = resources.read_decision_tree(name)
    if body.startswith("# Decision tree not found") or body.startswith("# Invalid"):
        return {"error": body.strip().lstrip("# "), "name": name}
    return {"name": name, "body": body, "byte_size": len(body)}
