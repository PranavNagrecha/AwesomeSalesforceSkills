#!/usr/bin/env python3
"""Search the local knowledge and skill corpus.

This module exposes both a CLI (``main``) and a reusable library API
(``build_search_context`` + ``run_search``). The library API is what
``scripts/validate_repo.py`` uses for fixture validation: loading the lexical
index once and reusing it across hundreds of fixture queries saves ~15 minutes
per validation run (744 fixtures * 1.3s subprocess cost -> single in-process
load + loop).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipelines.embedding_backends import embed_query, load_embeddings, parse_embedding_config
from pipelines.knowledge_builder import load_sources_manifest
from pipelines.lexical_index import search_index
from pipelines.ranking import aggregate_skill_scores, collect_official_sources, rerank_results
from pipelines.sync_engine import load_retrieval_config


def load_chunks(path: Path) -> dict[str, dict]:
    chunks: dict[str, dict] = {}
    if not path.exists():
        return chunks
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        chunks[item["id"]] = item
    return chunks


def make_snippet(text: str, length: int) -> str:
    compact = " ".join(text.split())
    return compact[: length - 1] + "…" if len(compact) > length else compact


def load_registry_skills(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {item["id"]: item for item in payload.get("skills", [])}


def normalize_official_source_label(value: str) -> str:
    for separator in (" — ", " - "):
        if separator in value:
            return value.split(separator, 1)[0].strip()
    return value.strip()


def canonicalize_official_source(
    item: dict,
    manifest_by_id: dict[str, dict],
    manifest_by_title: dict[str, dict],
) -> dict:
    source_id = str(item.get("id", "")).strip()
    if source_id and source_id in manifest_by_id:
        source = manifest_by_id[source_id]
        return {"id": source["id"], "title": source["title"], "url": source.get("url", "")}

    title = normalize_official_source_label(str(item.get("title", "")))
    if title and title in manifest_by_title:
        source = manifest_by_title[title]
        return {"id": source["id"], "title": source["title"], "url": source.get("url", "")}

    fallback_id = source_id or title.lower().replace(" ", "-")
    return {
        "id": fallback_id,
        "title": title or fallback_id,
        "url": str(item.get("url", "")),
    }


def dedupe_official_sources(items: list[dict], limit: int) -> list[dict]:
    deduped: list[dict] = []
    seen: set[str] = set()
    for item in items:
        key = item.get("id") or item.get("title") or item.get("url")
        if not key or key in seen:
            continue
        deduped.append(item)
        seen.add(key)
        if len(deduped) >= limit:
            break
    return deduped


@dataclass
class SearchContext:
    """Pre-loaded resources that are reused across many queries.

    Build ONCE via :func:`build_search_context`, reuse for N queries. The
    expensive loads are ``chunks.jsonl`` (~100 MB) and the source manifest;
    holding them in memory means a 744-fixture validation run goes from
    ~16 minutes (subprocess-per-fixture) to ~15 seconds.
    """

    root: Path
    config: dict
    lexical_limit: int
    result_limit: int
    snippet_length: int
    min_skill_score: float
    embedding_config: object  # parse_embedding_config's opaque return
    embeddings: dict
    chunks: dict
    registry_skills: dict
    source_manifest_by_id: dict
    source_manifest_by_title: dict


def build_search_context(root: Path) -> SearchContext:
    """Load every static resource a query needs. Call once per process."""
    config = load_retrieval_config(root)
    retrieval_config = config.get("retrieval", {})
    source_manifest_entries = [
        item for item in load_sources_manifest(root) if item.get("type") == "official-doc"
    ]
    return SearchContext(
        root=root,
        config=config,
        lexical_limit=int(retrieval_config.get("lexical_limit", 30)),
        result_limit=int(retrieval_config.get("result_limit", 10)),
        snippet_length=int(retrieval_config.get("snippet_length", 220)),
        min_skill_score=float(retrieval_config.get("min_skill_score", 0.0)),
        embedding_config=parse_embedding_config(config),
        embeddings=load_embeddings(root / "vector_index" / "embeddings.jsonl"),
        chunks=load_chunks(root / "vector_index" / "chunks.jsonl"),
        registry_skills=load_registry_skills(root / "registry" / "skills.json"),
        source_manifest_by_id={item["id"]: item for item in source_manifest_entries},
        source_manifest_by_title={item["title"]: item for item in source_manifest_entries},
    )


def run_search(query: str, ctx: SearchContext, domain: str | None = None) -> dict:
    """Run one query against the pre-loaded context. Returns the same payload
    shape the CLI emits with ``--json``. Pure (no stdout/stderr, no exit)."""
    lexical_rows = search_index(
        ctx.root / "vector_index" / "lexical.sqlite",
        query,
        domain,
        ctx.lexical_limit,
    )
    query_vector = embed_query(query, ctx.embedding_config)
    ranked = rerank_results(query_vector, lexical_rows, ctx.embeddings, domain)
    all_skills = aggregate_skill_scores(ranked, ctx.result_limit)
    skills = [s for s in all_skills if s["score"] >= ctx.min_skill_score]
    has_coverage = len(skills) > 0
    raw_official_sources = collect_official_sources(ranked, ctx.chunks, ctx.result_limit)
    official_sources = dedupe_official_sources(
        [
            canonicalize_official_source(item, ctx.source_manifest_by_id, ctx.source_manifest_by_title)
            for item in raw_official_sources
        ],
        ctx.result_limit,
    )
    seen_source_ids = {item["id"] for item in official_sources}
    for skill in skills:
        record = ctx.registry_skills.get(skill["id"])
        if not record:
            continue
        for label in record.get("official_sources", []):
            title = normalize_official_source_label(label)
            source_entry = ctx.source_manifest_by_title.get(title)
            if source_entry and source_entry["id"] not in seen_source_ids:
                official_sources.append(
                    canonicalize_official_source(source_entry, ctx.source_manifest_by_id, ctx.source_manifest_by_title)
                )
                seen_source_ids.add(source_entry["id"])
            elif title:
                fallback = canonicalize_official_source(
                    {"title": title, "url": ""},
                    ctx.source_manifest_by_id,
                    ctx.source_manifest_by_title,
                )
                if fallback["id"] not in seen_source_ids:
                    official_sources.append(fallback)
                    seen_source_ids.add(fallback["id"])
            if len(official_sources) >= ctx.result_limit:
                break
        if len(official_sources) >= ctx.result_limit:
            break
    chunk_results = [
        {
            "id": row["chunk_id"],
            "score": round(row["score"], 6),
            "path": row["path"],
            "snippet": make_snippet(row["text"], ctx.snippet_length),
        }
        for row in ranked[: ctx.result_limit]
    ]
    return {
        "query": query,
        "domain_filter": domain,
        "has_coverage": has_coverage,
        "skills": skills,
        "chunks": chunk_results,
        "official_sources": official_sources,
    }


def _emit_embeddings_warning(root: Path, config: dict) -> None:
    """Emit the stderr warning about embeddings. Separated so the library API
    doesn't spam stderr when called from the validator."""
    embeddings_cfg = config.get("embeddings", {})
    if embeddings_cfg.get("enabled", False):
        return
    warn_threshold = int(embeddings_cfg.get("warn_threshold", 300))
    require_threshold = int(embeddings_cfg.get("require_threshold", 500))
    skill_count = sum(1 for _ in (root / "skills").rglob("SKILL.md"))
    if skill_count >= require_threshold:
        print(
            f"WARNING: {skill_count} skills detected — embeddings are strongly recommended "
            f"(require_threshold: {require_threshold}). "
            "See config/retrieval-config.yaml for setup instructions.",
            file=sys.stderr,
        )
    elif skill_count >= warn_threshold:
        print(
            f"WARNING: {skill_count} skills detected — consider enabling embeddings "
            f"(warn_threshold: {warn_threshold}). "
            "See config/retrieval-config.yaml for setup instructions.",
            file=sys.stderr,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Search the repo-native skill and knowledge corpus.")
    parser.add_argument("query", help="Query text")
    parser.add_argument("--domain", help="Optional domain filter")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args()

    ctx = build_search_context(ROOT)
    _emit_embeddings_warning(ROOT, ctx.config)
    payload = run_search(args.query, ctx, domain=args.domain)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    print(f"Query: {args.query}")
    if args.domain:
        print(f"Domain: {args.domain}")
    print("")
    if not payload["has_coverage"]:
        print("Coverage: NONE — no skill meets the confidence threshold. Use official sources below.")
    print("Top skills:")
    for skill in payload["skills"]:
        print(f"- {skill['id']} ({skill['score']:.3f})")
    print("")
    print("Top chunks:")
    for chunk in payload["chunks"]:
        print(f"- {chunk['path']} [{chunk['score']:.3f}]")
        print(f"  {chunk['snippet']}")
    if payload["official_sources"]:
        print("")
        print("Related official sources:")
        for source in payload["official_sources"]:
            print(f"- {source['id']}: {source['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
