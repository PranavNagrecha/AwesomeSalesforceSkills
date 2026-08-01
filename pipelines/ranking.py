"""Ranking helpers for lexical and optional vector reranking."""

from __future__ import annotations

import re
from collections import defaultdict

from .embedding_backends import cosine_similarity


# Tokenizer for the skill-name/description match signal. Kept deliberately
# small and dumb: the +15pp held-out Hit@1 measurement on 2026-07-31 is tied to
# this exact stopword set and >2-char rule, so "improving" it invalidates the
# tuning of name_match_weight / description_match_weight in
# config/retrieval-config.yaml.
_STOPWORDS = {
    "a", "an", "the", "how", "do", "i", "my", "is", "in", "to", "for", "of", "on",
    "and", "or", "with", "what", "why", "set", "up", "get", "can", "does", "salesforce",
}

_TOKEN_SPLIT_RE = re.compile(r"[^a-z0-9]+")


def _tokens(value: str) -> set[str]:
    """Lowercase, split on non-alphanumerics, drop stopwords and short tokens."""
    return {
        token
        for token in _TOKEN_SPLIT_RE.split((value or "").lower())
        if token and token not in _STOPWORDS and len(token) > 2
    }


def _name_match_bonus(
    query_tokens: set[str],
    skill_id: str,
    skill_meta: dict[str, tuple[str, str]],
    name_weight: float,
    description_weight: float,
) -> float:
    """Bonus for query overlap with a skill's OWN name and description.

    Chunk-level lexical scoring answers "does this skill mention X". This
    answers "is this skill ABOUT X" — the missing centrality signal. Overlap is
    a fraction of the QUERY's tokens (not the name's), so a long descriptive
    name is not penalised and a long query is not trivially satisfied.
    """
    if not query_tokens:
        return 0.0
    name, description = skill_meta.get(skill_id, (skill_id.split("/")[-1], ""))
    name_tokens = _tokens(name.replace("-", " ")) | _tokens(skill_id.split("/")[-1].replace("-", " "))
    description_tokens = _tokens(description)
    name_overlap = len(query_tokens & name_tokens) / len(query_tokens)
    description_overlap = len(query_tokens & description_tokens) / len(query_tokens)
    return name_weight * name_overlap + description_weight * description_overlap


def rerank_results(
    query_vector: list[float] | None,
    lexical_rows: list[dict],
    embeddings: dict[str, dict],
    domain: str | None,
    skill_embeddings: dict[str, dict] | None = None,
) -> list[dict]:
    """Rerank lexical hits with optional vector boost.

    Two embedding sources, checked in order:
      1. ``skill_embeddings[row["skill_id"]]`` — skill-level vector. ~1K
         vectors total, covers the "which skill applies" question that
         retrieval is actually asking. Build via
         ``scripts/build_skill_embeddings.py``.
      2. ``embeddings[row["chunk_id"]]`` — chunk-level vector. Built by
         the full ``scripts/build_index.py`` pipeline (~3 hours on a Mac
         CPU for the 126K-chunk corpus). Falls back to chunk-level for
         finer-grained reranking when both indexes exist.

    Either, both, or neither can be present. When neither is present the
    function reduces to pure lexical reranking (its pre-2026-05-09 form).
    """
    skill_embeddings = skill_embeddings or {}
    ranked: list[dict] = []
    for index, row in enumerate(lexical_rows):
        # FTS5 bm25() returns negative values — more negative means more relevant.
        # The rows arrive pre-sorted best-first (most negative rank first), so
        # position 0 is the most relevant chunk. We use rank-based scoring so
        # the best chunk gets 1.0 and relevance decays with position. This is
        # more stable than a formula on the raw BM25 value, which would invert
        # the ordering (larger abs(rank) → smaller 1/(1+abs) score).
        lexical_score = 1.0 / (1.0 + index)
        boost = 0.0
        if domain and row.get("domain") == domain:
            boost += 0.2
        if row.get("skill_id"):
            boost += 0.1
        vector_score = 0.0
        if query_vector is not None:
            sid = row.get("skill_id")
            if sid and sid in skill_embeddings:
                vector_score = cosine_similarity(query_vector, skill_embeddings[sid]["vector"])
            elif row["chunk_id"] in embeddings:
                vector_score = cosine_similarity(query_vector, embeddings[row["chunk_id"]]["vector"])
        total_score = lexical_score + boost + (0.2 * vector_score)
        ranked.append(
            {
                **row,
                "score": total_score,
                "vector_score": vector_score,
                "lexical_score": lexical_score,
                "position": index,
            }
        )
    return sorted(ranked, key=lambda item: (-item["score"], item["position"]))


def aggregate_skill_scores(
    rows: list[dict],
    limit: int,
    *,
    skill_meta: dict[str, tuple[str, str]] | None = None,
    query: str | None = None,
    name_weight: float = 1.5,
    description_weight: float = 0.5,
) -> list[dict]:
    """Roll chunk hits up to skills and rank them.

    ``rows`` and ``limit`` stay positional — ``sfskills_mcp.skills.search_skill``
    calls this as ``aggregate_skill_scores(ranked, bounded_limit)``. Everything
    else is keyword-only and defaulted, so legacy callers are unaffected.

    Each record carries:
      ``score``     cumulative sum of every chunk this skill contributed
      ``max_score`` the skill's single best chunk
      ``rank_score`` ``max_score`` plus the name/description match bonus — the
                    value the list is actually ordered by

    Supplying ``skill_meta`` (``{skill_id: (name, description)}``) and ``query``
    turns on the skill-centrality bonus (see :func:`_name_match_bonus`). With
    either omitted the bonus is 0.0, ``rank_score == max_score``, and the
    ordering is identical to the pre-2026-07-31 behaviour. Registry metadata is
    never read here — the caller loads it once and passes it in.
    """
    aggregate: dict[str, dict] = {}
    for row in rows:
        skill_id = row.get("skill_id")
        if not skill_id:
            continue
        current = aggregate.get(skill_id)
        if current is None:
            aggregate[skill_id] = {
                "id": skill_id,
                "score": row["score"],
                "path": row["path"],
                "max_score": row["score"],
                "hit_count": 1,
            }
            continue
        current["score"] += row["score"]
        current["hit_count"] += 1
        if row["score"] > current["max_score"]:
            current["max_score"] = row["score"]
            current["path"] = row["path"]

    # The bonus is applied BEFORE truncation so a skill sitting outside the top
    # `limit` on chunk evidence alone can still be promoted on centrality.
    query_tokens = _tokens(query) if (skill_meta and query) else set()
    for record in aggregate.values():
        bonus = (
            _name_match_bonus(query_tokens, record["id"], skill_meta, name_weight, description_weight)
            if query_tokens
            else 0.0
        )
        record["rank_score"] = record["max_score"] + bonus

    # Primary sort: rank_score — centrality-adjusted best chunk. With no
    # metadata this reduces to max_score, i.e. the skill with the single most
    # relevant chunk wins. Secondary: cumulative score breaks ties.
    return sorted(
        aggregate.values(),
        key=lambda item: (-item["rank_score"], -item["score"], -item["hit_count"], item["id"]),
    )[:limit]


def collect_official_sources(rows: list[dict], chunk_lookup: dict[str, dict], limit: int) -> list[dict]:
    seen: dict[str, dict] = {}
    for row in rows:
        chunk = chunk_lookup.get(row["chunk_id"])
        if not chunk:
            continue
        for source_id in chunk.get("official_source_ids", []):
            if source_id not in seen:
                # Use the source_id as both key and title placeholder; the caller
                # canonicalizes against the manifest which carries the real title/URL.
                seen[source_id] = {"id": source_id, "title": source_id, "url": ""}
    return list(seen.values())[:limit]
