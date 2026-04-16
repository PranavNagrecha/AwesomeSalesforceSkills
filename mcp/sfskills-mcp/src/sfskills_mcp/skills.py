"""Skill-registry-backed operations for the SfSkills MCP server.

Two tools live here:

- ``search_skill`` — lexical search over the repo's SQLite FTS5 index, with
  skill-level aggregation matching ``scripts/search_knowledge.py``.
- ``get_skill`` — return the registry record, the SKILL.md body, and
  (optionally) reference files for a given skill id.

Skill ids use ``/`` internally (``apex/trigger-framework``). On disk the
registry stores them as ``<domain>__<name>.json`` under ``registry/skills/``;
SKILL.md lives at ``skills/<domain>/<name>/SKILL.md``.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from . import paths


MAX_SEARCH_LIMIT = 50
DEFAULT_SEARCH_LIMIT = 10
MAX_REFERENCE_CHARS = 40_000


def _load_registry() -> dict[str, Any]:
    path = paths.registry_skills_json()
    if not path.exists():
        raise FileNotFoundError(
            f"registry/skills.json not found at {path}. Run "
            "'python3 scripts/skill_sync.py --all' to generate it."
        )
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _registry_by_id() -> dict[str, dict[str, Any]]:
    payload = _load_registry()
    return {item["id"]: item for item in payload.get("skills", [])}


def _slim_registry_record(record: dict[str, Any]) -> dict[str, Any]:
    """Return the registry record without the large ``chunk_ids`` array."""
    return {k: v for k, v in record.items() if k != "chunk_ids"}


def _normalize_skill_id(skill_id: str) -> str:
    """Accept either ``apex/trigger-framework`` or ``apex__trigger-framework``."""
    cleaned = skill_id.strip()
    if "__" in cleaned and "/" not in cleaned:
        domain, _, name = cleaned.partition("__")
        return f"{domain}/{name}"
    return cleaned


def _read_skill_markdown(file_location: str) -> str:
    skill_md = paths.repo_root() / file_location / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(f"SKILL.md not found at {skill_md}")
    return skill_md.read_text(encoding="utf-8")


def _list_reference_files(file_location: str) -> list[dict[str, Any]]:
    refs_dir = paths.repo_root() / file_location / "references"
    if not refs_dir.exists():
        return []
    out: list[dict[str, Any]] = []
    for child in sorted(refs_dir.iterdir()):
        if child.is_file() and child.suffix == ".md":
            out.append(
                {
                    "name": child.name,
                    "path": str(child.relative_to(paths.repo_root())),
                    "bytes": child.stat().st_size,
                }
            )
    return out


def _read_reference_files(file_location: str) -> list[dict[str, Any]]:
    files = _list_reference_files(file_location)
    for meta in files:
        full = paths.repo_root() / meta["path"]
        text = full.read_text(encoding="utf-8")
        truncated = len(text) > MAX_REFERENCE_CHARS
        meta["content"] = text[:MAX_REFERENCE_CHARS]
        meta["truncated"] = truncated
    return files


def search_skill(
    query: str,
    domain: str | None = None,
    limit: int = DEFAULT_SEARCH_LIMIT,
) -> dict[str, Any]:
    """Lexical search across the SfSkills corpus.

    Returns a payload mirroring ``scripts/search_knowledge.py --json`` but
    scoped to the fields an MCP client needs: aggregated skill hits, their
    summary metadata, and top-matching chunks.
    """
    if not isinstance(query, str) or not query.strip():
        return {"error": "query is required", "query": query, "skills": [], "chunks": []}

    bounded_limit = max(1, min(int(limit or DEFAULT_SEARCH_LIMIT), MAX_SEARCH_LIMIT))

    paths.ensure_pipelines_on_path()
    from pipelines.lexical_index import search_index  # type: ignore[import-not-found]
    from pipelines.ranking import aggregate_skill_scores, rerank_results  # type: ignore[import-not-found]

    lexical_rows = search_index(
        paths.lexical_index_path(),
        query,
        domain,
        max(bounded_limit * 3, 30),
    )
    ranked = rerank_results(None, lexical_rows, {}, domain)
    aggregated = aggregate_skill_scores(ranked, bounded_limit)

    registry = _registry_by_id()
    enriched_skills: list[dict[str, Any]] = []
    for hit in aggregated:
        record = registry.get(hit["id"])
        entry: dict[str, Any] = {"id": hit["id"], "score": hit["score"]}
        if record:
            entry.update(
                {
                    "name": record.get("name"),
                    "category": record.get("category"),
                    "description": record.get("description"),
                    "file_location": record.get("file_location"),
                    "tags": record.get("tags", []),
                }
            )
        enriched_skills.append(entry)

    chunks_payload = [
        {
            "id": row["chunk_id"],
            "score": round(row["score"], 6),
            "path": row["path"],
            "skill_id": row.get("skill_id"),
            "domain": row.get("domain"),
            "snippet": _snippet(row["text"], 220),
        }
        for row in ranked[:bounded_limit]
    ]

    return {
        "query": query,
        "domain_filter": domain,
        "has_coverage": bool(enriched_skills),
        "skills": enriched_skills,
        "chunks": chunks_payload,
    }


def get_skill(
    skill_id: str,
    include_markdown: bool = True,
    include_references: bool = False,
) -> dict[str, Any]:
    """Return the registry record plus (optionally) SKILL.md and references."""
    normalized = _normalize_skill_id(skill_id)
    record = _registry_by_id().get(normalized)
    if record is None:
        return {
            "error": f"skill not found: {normalized}",
            "hint": "Use search_skill to find candidate ids, or check "
                    "'registry/skills.json' for the canonical list.",
        }

    out: dict[str, Any] = {"skill": _slim_registry_record(record)}
    file_location = record.get("file_location")
    if file_location and include_markdown:
        try:
            out["markdown"] = _read_skill_markdown(file_location)
        except FileNotFoundError as exc:
            out["markdown_error"] = str(exc)
    if file_location:
        out["references"] = (
            _read_reference_files(file_location) if include_references else _list_reference_files(file_location)
        )
    return out


def _snippet(text: str, length: int) -> str:
    compact = " ".join((text or "").split())
    return compact[: length - 1] + "\u2026" if len(compact) > length else compact


def _all_skill_ids() -> Iterable[str]:
    return _registry_by_id().keys()
