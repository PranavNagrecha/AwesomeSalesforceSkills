#!/usr/bin/env python3
"""Search the local knowledge and skill corpus."""

from __future__ import annotations

import argparse
import json
import sys
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Search the repo-native skill and knowledge corpus.")
    parser.add_argument("query", help="Query text")
    parser.add_argument("--domain", help="Optional domain filter")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args()

    config = load_retrieval_config(ROOT)
    retrieval_config = config.get("retrieval", {})
    lexical_limit = int(retrieval_config.get("lexical_limit", 30))
    result_limit = int(retrieval_config.get("result_limit", 10))
    snippet_length = int(retrieval_config.get("snippet_length", 220))
    min_skill_score = float(retrieval_config.get("min_skill_score", 0.0))

    # Embeddings threshold check — warn when corpus size crosses the configured threshold
    embeddings_cfg = config.get("embeddings", {})
    if not embeddings_cfg.get("enabled", False):
        warn_threshold = int(embeddings_cfg.get("warn_threshold", 300))
        require_threshold = int(embeddings_cfg.get("require_threshold", 500))
        skill_count = sum(1 for _ in (ROOT / "skills").rglob("SKILL.md"))
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

    lexical_rows = search_index(ROOT / "vector_index" / "lexical.sqlite", args.query, args.domain, lexical_limit)
    chunks = load_chunks(ROOT / "vector_index" / "chunks.jsonl")
    embedding_config = parse_embedding_config(config)
    query_vector = embed_query(args.query, embedding_config)
    embeddings = load_embeddings(ROOT / "vector_index" / "embeddings.jsonl")
    ranked = rerank_results(query_vector, lexical_rows, embeddings, args.domain)
    all_skills = aggregate_skill_scores(ranked, result_limit)
    skills = [s for s in all_skills if s["score"] >= min_skill_score]
    has_coverage = len(skills) > 0
    raw_official_sources = collect_official_sources(ranked, chunks, result_limit)
    registry_skills = load_registry_skills(ROOT / "registry" / "skills.json")
    source_manifest_entries = [
        item
        for item in load_sources_manifest(ROOT)
        if item.get("type") == "official-doc"
    ]
    source_manifest_by_id = {
        item["id"]: item
        for item in source_manifest_entries
    }
    source_manifest_by_title = {
        item["title"]: item
        for item in source_manifest_entries
    }
    official_sources = dedupe_official_sources(
        [
            canonicalize_official_source(item, source_manifest_by_id, source_manifest_by_title)
            for item in raw_official_sources
        ],
        result_limit,
    )
    seen_source_ids = {item["id"] for item in official_sources}
    for skill in skills:
        record = registry_skills.get(skill["id"])
        if not record:
            continue
        for label in record.get("official_sources", []):
            title = normalize_official_source_label(label)
            source_entry = source_manifest_by_title.get(title)
            if source_entry and source_entry["id"] not in seen_source_ids:
                official_sources.append(
                    canonicalize_official_source(source_entry, source_manifest_by_id, source_manifest_by_title)
                )
                seen_source_ids.add(source_entry["id"])
            elif title:
                fallback = canonicalize_official_source(
                    {"title": title, "url": ""},
                    source_manifest_by_id,
                    source_manifest_by_title,
                )
                if fallback["id"] not in seen_source_ids:
                    official_sources.append(fallback)
                    seen_source_ids.add(fallback["id"])
            if len(official_sources) >= result_limit:
                break
        if len(official_sources) >= result_limit:
            break
    chunk_results = [
        {
            "id": row["chunk_id"],
            "score": round(row["score"], 6),
            "path": row["path"],
            "snippet": make_snippet(row["text"], snippet_length),
        }
        for row in ranked[:result_limit]
    ]
    payload = {
        "query": args.query,
        "domain_filter": args.domain,
        "has_coverage": has_coverage,
        "skills": skills,
        "chunks": chunk_results,
        "official_sources": official_sources,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    print(f"Query: {args.query}")
    if args.domain:
        print(f"Domain: {args.domain}")
    print("")
    if not has_coverage:
        print("Coverage: NONE — no skill meets the confidence threshold. Use official sources below.")
    print("Top skills:")
    for skill in skills:
        print(f"- {skill['id']} ({skill['score']:.3f})")
    print("")
    print("Top chunks:")
    for chunk in chunk_results:
        print(f"- {chunk['path']} [{chunk['score']:.3f}]")
        print(f"  {chunk['snippet']}")
    if official_sources:
        print("")
        print("Related official sources:")
        for source in official_sources:
            print(f"- {source['id']}: {source['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
