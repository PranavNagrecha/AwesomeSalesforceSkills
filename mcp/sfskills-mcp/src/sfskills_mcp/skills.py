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

# Fallbacks matching config/retrieval-config.yaml, used when the data bundle
# ships without a config (PyPI install). Keep these in sync with that file.
DEFAULT_MIN_SKILL_SCORE = 1.5
DEFAULT_MIN_SKILL_MAX_SCORE = 1.0
DEFAULT_NAME_MATCH_WEIGHT = 1.5
DEFAULT_DESCRIPTION_MATCH_WEIGHT = 0.5


@lru_cache(maxsize=1)
def _retrieval_config() -> dict[str, float]:
    """Gate + ranking knobs, read once from config/retrieval-config.yaml.

    Falls back to the DEFAULT_* constants when the config is absent or PyYAML
    is not installed, so a bare data bundle still gates identically to the CLI.
    """
    defaults = {
        "min_skill_score": DEFAULT_MIN_SKILL_SCORE,
        "min_skill_max_score": DEFAULT_MIN_SKILL_MAX_SCORE,
        "name_match_weight": DEFAULT_NAME_MATCH_WEIGHT,
        "description_match_weight": DEFAULT_DESCRIPTION_MATCH_WEIGHT,
    }
    try:
        paths.ensure_pipelines_on_path()
        from pipelines.sync_engine import load_retrieval_config  # type: ignore[import-not-found]

        retrieval = (load_retrieval_config(paths.repo_root()) or {}).get("retrieval", {})
    except Exception:  # noqa: BLE001 — a missing/!parseable config must not break search
        return defaults
    return {key: float(retrieval.get(key, fallback)) for key, fallback in defaults.items()}


@lru_cache(maxsize=1)
def _skill_meta() -> dict[str, tuple[str, str]]:
    """``{skill_id: (name, description)}`` for the skill-centrality bonus.

    Built from the already-cached registry — no extra file read per query.
    """
    return {
        skill_id: (record.get("name", ""), record.get("description", ""))
        for skill_id, record in _registry_by_id().items()
    }


@lru_cache(maxsize=1)
def _skill_embeddings() -> dict[str, dict[str, Any]]:
    """Skill-level vectors (one per skill, ~5 MB) if the bundle carries them.

    Deliberately NEVER loads ``vector_index/embeddings.jsonl`` (535 MB of
    chunk-level vectors). Every indexed chunk carries a ``skill_id``, and
    ``pipelines.ranking.rerank_results`` prefers the skill-level vector whenever
    one exists — so the chunk file would cost half a gigabyte of RSS to change
    nothing.
    """
    path = paths.repo_root() / "vector_index" / "skill_embeddings.jsonl"
    if not path.exists():
        return {}
    out: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            skill_id = item.get("skill_id")
            if skill_id:
                out[skill_id] = item
    return out


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
    """Search across the SfSkills corpus.

    Returns a payload mirroring ``scripts/search_knowledge.py --json`` but
    scoped to the fields an MCP client needs: aggregated skill hits, their
    summary metadata, and top-matching chunks. Gating and ranking are kept in
    lockstep with the CLI — see the parity notes inline below, and
    ``evals/measurement/check_cli_mcp_parity.py`` for the regression test.
    """
    if not isinstance(query, str) or not query.strip():
        return {"error": "query is required", "query": query, "skills": [], "chunks": []}

    bounded_limit = max(1, min(int(limit or DEFAULT_SEARCH_LIMIT), MAX_SEARCH_LIMIT))

    paths.ensure_pipelines_on_path()
    from pipelines.embedding_backends import embed_query, parse_embedding_config  # type: ignore[import-not-found]
    from pipelines.lexical_index import search_index  # type: ignore[import-not-found]
    from pipelines.ranking import aggregate_skill_scores, rerank_results  # type: ignore[import-not-found]

    lexical_window = max(bounded_limit * 3, 30)
    lexical_rows = search_index(
        paths.lexical_index_path(),
        query,
        domain,
        lexical_window,
    )

    # Vector parity, opportunistically. A DEV install (repo root on disk) has
    # vector_index/skill_embeddings.jsonl and can rank exactly like the CLI. A
    # PyPI install is lexical-only BY CONSTRUCTION and always will be:
    #   - .gitignore excludes both embeddings.jsonl and skill_embeddings.jsonl,
    #   - .github/workflows/publish-mcp.yml bundles vector_index/ from a bare
    #     checkout without building an index, so neither file is in the wheel,
    #   - fastembed is an optional [embeddings] extra, not a hard dependency.
    # So we only pay fastembed's ~14s cold start when there are actually
    # vectors to compare the query against; with none, embedding it would be
    # pure latency for zero signal. The GATE is identical either way — that is
    # the divergence that mattered, and it is closed.
    skill_embeddings = _skill_embeddings()
    query_vector = None
    if skill_embeddings:
        try:
            from pipelines.sync_engine import load_retrieval_config  # type: ignore[import-not-found]

            query_vector = embed_query(query, parse_embedding_config(load_retrieval_config(paths.repo_root())))
        except Exception:  # noqa: BLE001 — no fastembed / no config: stay lexical
            query_vector = None

    ranked = rerank_results(
        query_vector,
        lexical_rows,
        {},
        domain,
        skill_embeddings=skill_embeddings,
    )

    # Parity with scripts/search_knowledge.run_search: the which-skill decision
    # gets its own skill-scoped window. Chunks with no skill_id (knowledge/
    # imports, official-source chunks) cannot aggregate into a skill, so
    # sharing one window let them spend the budget without being able to
    # answer. On the held-out set that cost 20 of 30 slots on "set up single
    # sign on" and 24 of 30 on "share data between two lightning web
    # components", both of which returned no coverage while the owning skill
    # sat in the index. Skipped entirely when the window is already all-skill.
    if any(not (row.get("skill_id") or "").strip() for row in lexical_rows):
        skill_ranked = rerank_results(
            query_vector,
            search_index(
                paths.lexical_index_path(),
                query,
                domain,
                lexical_window,
                skills_only=True,
            ),
            {},
            domain,
            skill_embeddings=skill_embeddings,
        )
    else:
        skill_ranked = ranked

    config = _retrieval_config()
    aggregated = aggregate_skill_scores(
        skill_ranked,
        bounded_limit,
        skill_meta=_skill_meta(),
        query=query,
        name_weight=config["name_match_weight"],
        description_weight=config["description_match_weight"],
    )
    # Same coverage gate as scripts/search_knowledge.run_search: max_score OR
    # cumulative score, never rank_score (the name bonus ranks, it does not
    # confer confidence). Previously this was `has_coverage = bool(results)`,
    # which meant the MCP claimed coverage on any lexical hit at all.
    gated = [
        hit for hit in aggregated
        if hit["max_score"] >= config["min_skill_max_score"]
        or hit["score"] >= config["min_skill_score"]
    ]

    registry = _registry_by_id()
    enriched_skills: list[dict[str, Any]] = []
    for hit in gated:
        record = registry.get(hit["id"])
        entry: dict[str, Any] = {
            "id": hit["id"],
            "score": hit["score"],
            "rank_score": hit["rank_score"],
        }
        if record:
            entry.update(
                {
                    "name": record.get("name"),
                    "category": record.get("category"),
                    "description": record.get("description"),
                    "file_location": record.get("file_location"),
                    "tags": record.get("tags", []),
                    # Lifecycle status. Defaults to "stable" when the record
                    # omits it. "stub" flags skills whose reference files
                    # still contain TODO placeholders — agents should treat
                    # the body as a hint and avoid quoting the references.
                    "status": record.get("status", "stable"),
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
        "has_coverage": len(enriched_skills) > 0,
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
