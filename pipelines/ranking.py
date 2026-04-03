"""Ranking helpers for lexical and optional vector reranking."""

from __future__ import annotations

from collections import defaultdict

from .embedding_backends import cosine_similarity


def rerank_results(query_vector: list[float] | None, lexical_rows: list[dict], embeddings: dict[str, dict], domain: str | None) -> list[dict]:
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
        if query_vector is not None and row["chunk_id"] in embeddings:
            vector_score = cosine_similarity(query_vector, embeddings[row["chunk_id"]]["vector"])
        total_score = lexical_score + boost + (0.35 * vector_score)
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


def aggregate_skill_scores(rows: list[dict], limit: int) -> list[dict]:
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
    # Primary sort: max_score — the skill with the single most relevant chunk wins.
    # Secondary: cumulative score breaks ties between skills with equal max_score.
    return sorted(
        aggregate.values(),
        key=lambda item: (-item["max_score"], -item["score"], -item["hit_count"], item["id"]),
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
