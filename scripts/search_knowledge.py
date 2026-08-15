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
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipelines.embedding_backends import embed_query, load_embeddings, parse_embedding_config
from pipelines.knowledge_builder import load_sources_manifest
from pipelines.lexical_index import search_index
from pipelines.ranking import aggregate_skill_scores, collect_official_sources, rerank_results
from pipelines.sync_engine import load_retrieval_config


def _load_skill_embeddings(path: Path) -> dict[str, dict]:
    """Load skill-level embeddings (one vector per skill).

    Built by ``scripts/build_skill_embeddings.py``. ~1000 vectors,
    encodes in <2 minutes vs the chunk-level pipeline's ~3 hours.
    """
    if not path.exists():
        return {}
    out: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        sid = item.get("skill_id")
        if sid:
            out[sid] = item
    return out

# NOTE: scripts/query_enrichment.py is committed but NOT wired into run_search.
# Two attempts at vocabulary expansion both failed to lift NL Hit@1:
#   - Token-stream concat (concat long-forms into the FTS5 query): -5% on
#     curated baseline due to over-expansion diluting precise author keywords.
#   - Post-retrieval score boost: flat on NL synthetic queries (74.3% →
#     74.4%) and -0.2% on curated. The synthetic NL distribution doesn't
#     lean heavily on abbreviations; the few that do are already resolved
#     by FTS5 prefix matching (`fls*` matches `flsmanager`, etc.).
# Keep query_enrichment.py available for ad-hoc CLI use.


# The exact bytes `json.dumps(chunk, sort_keys=True)` emits for a chunk that
# carries no official sources. `pipelines/sync_engine.build_chunks_jsonl` uses
# default separators, so an empty list serialises with one space after the
# colon. See `load_official_source_chunks` for why this is safe to trust.
_EMPTY_OFFICIAL_SOURCE_IDS = '"official_source_ids": []'


def load_official_source_chunks(path: Path) -> dict[str, dict]:
    """Load ONLY the chunks that carry a non-empty ``official_source_ids``.

    This is deliberately not "load chunks". ``chunks.jsonl`` is 126 MB /
    130,151 records, and the single consumer of this mapping —
    ``pipelines.ranking.collect_official_sources`` — reads exactly one field
    off it, ``official_source_ids``, for the <=30 rows the lexical pass
    returned. On the current corpus 30 records out of 130,151 have a non-empty
    value; the other 130,121 map to ``[]``.

    Dropping the empty ones cannot change the result. ``collect_official_sources``
    skips a chunk it cannot find (``if not chunk: continue``) and iterates an
    empty list for a chunk it does find, so both paths contribute nothing to
    the output and nothing to the insertion order of its ``seen`` dict.

    Two properties matter for memory, and they are separate:

    * We iterate the file handle rather than ``read_text().splitlines()``. The
      old form materialised the whole 126 MB file as one ``str`` and then split
      it into 130,151 more, before a single record was parsed.
    * We keep 30 dicts instead of 130,151.

    The ``_EMPTY_OFFICIAL_SOURCE_IDS`` skip is a pure speed optimisation
    (1.48s -> 0.13s) and is fail-safe by construction: it can only ever cause
    us to PARSE a line we could have skipped, never to SKIP a line we needed.
    A line whose field is non-empty cannot contain the marker, because JSON
    escapes the quotes of any string value (an occurrence inside chunk text
    reads ``\\"official_source_ids\\": []``, which does not match). If the
    serialisation ever changes, the marker simply stops matching and every
    line falls through to ``json.loads`` — slower, still correct.
    """
    chunks: dict[str, dict] = {}
    if not path.exists():
        return chunks
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if _EMPTY_OFFICIAL_SOURCE_IDS in line:
                continue
            if not line.strip():
                continue
            item = json.loads(line)
            if item.get("official_source_ids"):
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

    Build ONCE via :func:`build_search_context`, reuse for N queries. That is
    what makes in-process fixture validation viable at all: a 1,356-fixture run
    pays the load once instead of spawning 1,356 subprocesses.

    What is actually expensive here has changed, and the old docstring's claim
    that ``chunks.jsonl`` (~100 MB) is the cost was wrong in both directions:

    * ``embeddings.jsonl`` was the larger half — 535 MB on disk, ~2 GB resident
      — and it is loaded only when ``embeddings.enabled`` is true. With it
      false, ``embed_query`` returns ``None`` and ``pipelines.ranking``
      never reads the mapping, so loading it was pure waste. See
      :func:`build_search_context`.
    * ``chunks.jsonl`` is 126 MB, but only 30 of its 130,151 records are ever
      read. ``official_source_chunks`` holds those 30. See
      :func:`load_official_source_chunks`.

    ``official_source_chunks`` is named for what it holds, NOT ``chunks``. The
    rename is load-bearing: code that assumed a full chunk mapping and wrote
    ``ctx.chunks.get(cid, {}).get("text", "")`` would now silently get an empty
    string for 130,121 of 130,151 ids. An ``AttributeError`` on the old name is
    the outcome we want instead.
    """

    root: Path
    config: dict
    lexical_limit: int
    result_limit: int
    snippet_length: int
    min_skill_score: float
    embedding_config: object  # parse_embedding_config's opaque return
    embeddings: dict
    skill_embeddings: dict
    official_source_chunks: dict
    registry_skills: dict
    source_manifest_by_id: dict
    source_manifest_by_title: dict
    # Trailing defaulted fields — added 2026-07-31. Defaults keep any existing
    # positional SearchContext(...) construction working unchanged.
    min_skill_max_score: float = 1.0
    # {skill_id: (name, description)} for the skill-centrality bonus. Derived
    # once from registry_skills; pipelines/ranking.py never touches the registry.
    skill_meta: dict = field(default_factory=dict)
    name_weight: float = 1.5
    description_weight: float = 0.5


def build_search_context(root: Path) -> SearchContext:
    """Load every static resource a query needs. Call once per process."""
    config = load_retrieval_config(root)
    retrieval_config = config.get("retrieval", {})
    source_manifest_entries = [
        item for item in load_sources_manifest(root) if item.get("type") == "official-doc"
    ]
    registry_skills = load_registry_skills(root / "registry" / "skills.json")
    embedding_config = parse_embedding_config(config)
    # Load the 535 MB chunk-vector file ONLY when it can be read.
    # `embed_query` returns None whenever `enabled` is false
    # (pipelines/embedding_backends.py), and `rerank_results` gates every read
    # of this mapping behind `if query_vector is not None`
    # (pipelines/ranking.py). So with embeddings disabled the dict was loaded,
    # held at ~2 GB for the life of the process, and never once consulted.
    #
    # This does NOT change behaviour in either branch: enabled -> identical
    # load, disabled -> a mapping that provably nothing reads.
    #
    # HISTORICAL NOTE, kept because the reasoning still applies. This comment
    # used to warn that config/retrieval-config.yaml set `enabled: false`
    # "TEMPORARILY ... for build-agent memory safety" and that flipping it back
    # would silently restore ~2 GB of resident memory per search process. Both
    # halves are now obsolete: the config has said `enabled: true` since
    # 2026-08-13, and the memory figure was re-measured at 472 MB peak RSS —
    # embeddings.jsonl is gitignored and not built, so only the ~5 MB
    # skill_embeddings.jsonl is read. The load is still whole-file, so the
    # keyed-vector-store fix that config file names remains the right one if
    # chunk-level embeddings are ever rebuilt locally.
    embeddings = (
        load_embeddings(root / "vector_index" / "embeddings.jsonl")
        if embedding_config.enabled
        else {}
    )
    return SearchContext(
        root=root,
        config=config,
        lexical_limit=int(retrieval_config.get("lexical_limit", 30)),
        result_limit=int(retrieval_config.get("result_limit", 10)),
        snippet_length=int(retrieval_config.get("snippet_length", 220)),
        min_skill_score=float(retrieval_config.get("min_skill_score", 0.0)),
        embedding_config=embedding_config,
        embeddings=embeddings,
        skill_embeddings=_load_skill_embeddings(root / "vector_index" / "skill_embeddings.jsonl"),
        official_source_chunks=load_official_source_chunks(root / "vector_index" / "chunks.jsonl"),
        registry_skills=registry_skills,
        source_manifest_by_id={item["id"]: item for item in source_manifest_entries},
        source_manifest_by_title={item["title"]: item for item in source_manifest_entries},
        # In-code fallbacks, not zeros: scripts/validate_repo_bench.py writes a
        # synthetic retrieval config that carries none of these keys. The
        # min_skill_max_score fallback only ever ADMITS more skills, so a config
        # that omits it behaves like the pre-2026-07-31 gate plus the OR arm.
        min_skill_max_score=float(retrieval_config.get("min_skill_max_score", 1.0)),
        skill_meta={
            skill_id: (record.get("name", ""), record.get("description", ""))
            for skill_id, record in registry_skills.items()
        },
        name_weight=float(retrieval_config.get("name_match_weight", 1.5)),
        description_weight=float(retrieval_config.get("description_match_weight", 0.5)),
    )


_FTS5_SAFE_RE = re.compile(r"[^A-Za-z0-9\-]+")


def _sanitize_query_for_fts5(query: str) -> str:
    """Reduce a user query to FTS5-safe tokens (alphanum + hyphen).

    SQLite FTS5 raises a syntax error on raw user input that contains operator
    characters: ``+``, ``%``, ``*``, ``"``, ``^``, ``(``, ``)``. Real users
    type these in natural-language queries (e.g. "salesforce + slack",
    "100% test coverage", "apex *ngFor"). Without this guard,
    ``pipelines/lexical_index.search_index`` crashes with
    ``sqlite3.OperationalError: fts5: syntax error near "+"``.

    We strip down to alphanumerics and hyphens — that's a strict superset of
    what the existing tokenizer indexes anyway, so retrieval quality is
    unchanged on safe queries and graceful on previously-crashing queries.
    """
    return " ".join(t for t in _FTS5_SAFE_RE.sub(" ", query).split() if t)


def run_search(query: str, ctx: SearchContext, domain: str | None = None) -> dict:
    """Run one query against the pre-loaded context. Returns the same payload
    shape the CLI emits with ``--json``. Pure (no stdout/stderr, no exit)."""
    query = _sanitize_query_for_fts5(query)
    index_path = ctx.root / "vector_index" / "lexical.sqlite"
    lexical_rows = search_index(index_path, query, domain, ctx.lexical_limit)
    # Embed the query only when there is something to compare it against.
    # Both vector files are gitignored (they exceed GitHub's file limit and are
    # rebuilt locally), so a fresh clone with `enabled: true` and fastembed
    # installed would otherwise pay a ~7 s model load plus a per-query encode
    # to produce a vector that `rerank_results` has no vectors to score
    # against — pure latency for zero signal. The MCP surface has always had
    # this guard; the CLI did not. `embed_query` already returns None when
    # embeddings are disabled or fastembed is missing, so this covers the
    # third case: enabled, installed, and nothing built.
    has_vectors = bool(ctx.embeddings) or bool(ctx.skill_embeddings)
    query_vector = embed_query(query, ctx.embedding_config) if has_vectors else None
    ranked = rerank_results(
        query_vector,
        lexical_rows,
        ctx.embeddings,
        domain,
        skill_embeddings=ctx.skill_embeddings,
    )
    # Which-skill-covers-this gets its OWN window. `lexical_limit` is a budget,
    # and chunks with no skill_id (knowledge/ imports, official-source chunks)
    # can never aggregate into a skill — they spend slots without being able to
    # answer the question. Sharing one window let them starve the answer on
    # exactly the queries that already struggled: measured on the held-out set
    # they take 7.5% of the window overall, but 20 of 30 slots on "set up
    # single sign on" and 24 of 30 on "share data between two lightning web
    # components", both of which returned Coverage: NONE while the owning skill
    # sat in the index. Reuse `ranked` when it is already all-skill so the
    # common query pays nothing extra.
    if any(not (row.get("skill_id") or "").strip() for row in lexical_rows):
        skill_ranked = rerank_results(
            query_vector,
            search_index(index_path, query, domain, ctx.lexical_limit, skills_only=True),
            ctx.embeddings,
            domain,
            skill_embeddings=ctx.skill_embeddings,
        )
    else:
        skill_ranked = ranked
    all_skills = aggregate_skill_scores(
        skill_ranked,
        ctx.result_limit,
        skill_meta=ctx.skill_meta,
        query=query,
        name_weight=ctx.name_weight,
        description_weight=ctx.description_weight,
    )
    # Coverage gate reads max_score / score — deliberately NOT rank_score. The
    # name/description bonus is a RANKING signal (which skill answers), not a
    # CONFIDENCE signal (whether to answer at all); folding it into the gate
    # would let a title coincidence manufacture coverage the corpus lacks.
    # The OR is the fix for a units mismatch: the ranker sorted on max_score
    # (best single chunk) while the gate read score (cumulative), so one precise
    # match was suppressed while three weak ones passed.
    skills = [
        s for s in all_skills
        if s["max_score"] >= ctx.min_skill_max_score or s["score"] >= ctx.min_skill_score
    ]
    has_coverage = len(skills) > 0
    raw_official_sources = collect_official_sources(ranked, ctx.official_source_chunks, ctx.result_limit)
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
        # Print rank_score, the value the list is ordered by. Printing the
        # cumulative `score` here made the output look unsorted.
        print(f"- {skill['id']} ({skill['rank_score']:.3f})")
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
