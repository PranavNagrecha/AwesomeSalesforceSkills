#!/usr/bin/env python3
"""Run the held-out retrieval benchmark.

Why this exists: ``vector_index/query-fixtures.json`` is 1,356 paraphrases of
the ``triggers:`` frontmatter that is itself indexed, so it measures the easy
case. On 2026-07-31 the fixtures reported a 0.8% "Coverage: NONE" rate against
23.3% on hand-written realistic phrasings — a 29x gap. ``heldout-queries.json``
is the honest counterpart: hand-written, never indexed, every label verified on
disk. Its ``description`` field documents the conventions for adding entries.

Metrics are computed over the GATED ``payload["skills"]`` list — what a caller
actually sees — not over the raw aggregate.

Usage:
  python3 evals/measurement/run_heldout.py
  python3 evals/measurement/run_heldout.py --no-embeddings --json
  python3 evals/measurement/run_heldout.py --tag evidence-20
  python3 evals/measurement/run_heldout.py --check
  python3 evals/measurement/run_heldout.py --queries vector_index/query-fixtures.json --use-domain

Exit codes:
  0  pass
  1  a threshold floor was breached, or --check found a problem
  2  a label points at a skill that does not exist on disk (reported before
     any metric, because a benchmark with a phantom label measures nothing)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.search_knowledge as search_knowledge  # noqa: E402

DEFAULT_QUERIES = ROOT / "evals" / "measurement" / "heldout-queries.json"
FIXTURES_PATH = ROOT / "vector_index" / "query-fixtures.json"

# Registry categories. Every one must be represented in the benchmark, else a
# whole domain can rot unmeasured.
CATEGORIES = [
    "admin", "agentforce", "apex", "architect", "data", "devops",
    "flow", "integration", "lwc", "omnistudio", "security",
]
MIN_QUERIES = 120
MIN_PER_CATEGORY = 6


def load_queries(path: Path) -> list[dict]:
    """Accept both the benchmark shape and vector_index/query-fixtures.json.

    Both use ``{"queries": [{"query", "expected_skill", "domain", ...}]}``; the
    benchmark adds ``tags`` and the fixtures add ``top_k``.
    """
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("queries", payload) if isinstance(payload, dict) else payload
    if not isinstance(entries, list):
        raise ValueError(f"{path}: expected a list of queries")
    return entries


def missing_labels(entries: list[dict]) -> list[str]:
    """Labels whose skill package is not on disk, in file order, deduped."""
    seen: set[str] = set()
    missing: list[str] = []
    for entry in entries:
        skill_id = entry.get("expected_skill", "")
        if not skill_id or skill_id in seen:
            continue
        seen.add(skill_id)
        if not (ROOT / "skills" / skill_id / "SKILL.md").exists():
            missing.append(skill_id)
    return missing


def check_benchmark(path: Path, entries: list[dict]) -> list[str]:
    """Structural problems with the benchmark file. Empty list means healthy."""
    problems: list[str] = []

    if len(entries) < MIN_QUERIES:
        problems.append(f"only {len(entries)} queries, need >= {MIN_QUERIES}")

    queries = [entry.get("query", "") for entry in entries]
    duplicates = sorted({q for q in queries if queries.count(q) > 1})
    if duplicates:
        problems.append(f"{len(duplicates)} duplicate query string(s): {duplicates[:5]}")

    per_category: dict[str, int] = {}
    for entry in entries:
        category = entry.get("expected_skill", "/").split("/")[0]
        per_category[category] = per_category.get(category, 0) + 1
    for category in CATEGORIES:
        count = per_category.get(category, 0)
        if count < MIN_PER_CATEGORY:
            problems.append(f"category `{category}` has {count} entries, need >= {MIN_PER_CATEGORY}")
    for category in sorted(set(per_category) - set(CATEGORIES)):
        problems.append(f"category `{category}` is not a registry category")

    # Held out means held out: nothing may be lifted verbatim from the fixture
    # set, or the benchmark quietly becomes the thing it is meant to audit.
    if path.resolve() != FIXTURES_PATH.resolve() and FIXTURES_PATH.exists():
        fixture_queries = {f["query"] for f in load_queries(FIXTURES_PATH)}
        overlap = sorted(set(queries) & fixture_queries)
        if overlap:
            problems.append(f"{len(overlap)} query string(s) copied verbatim from query-fixtures.json: {overlap[:5]}")

    return problems


def build_context(use_embeddings: bool) -> search_knowledge.SearchContext:
    """Build the SearchContext once.

    ``use_embeddings=False`` reproduces the CI configuration exactly: fastembed
    absent, ``embeddings.jsonl`` absent, ``skill_embeddings.jsonl`` absent. We
    stub the loaders instead of reading 535 MB off disk and discarding it.
    """
    if use_embeddings:
        return search_knowledge.build_search_context(ROOT)

    original_load = search_knowledge.load_embeddings
    original_load_skill = search_knowledge._load_skill_embeddings
    original_parse = search_knowledge.parse_embedding_config
    search_knowledge.load_embeddings = lambda *_a, **_kw: {}
    search_knowledge._load_skill_embeddings = lambda *_a, **_kw: {}
    search_knowledge.parse_embedding_config = lambda *_a, **_kw: original_parse(
        {"embeddings": {"enabled": False}}
    )
    try:
        return search_knowledge.build_search_context(ROOT)
    finally:
        search_knowledge.load_embeddings = original_load
        search_knowledge._load_skill_embeddings = original_load_skill
        search_knowledge.parse_embedding_config = original_parse


def evaluate(
    entries: list[dict],
    ctx: search_knowledge.SearchContext,
    use_domain: bool,
    default_top_k: int,
) -> dict:
    hit_at_1 = 0
    hit_at_3 = 0
    none_count = 0
    misses: list[dict] = []

    for entry in entries:
        expected = entry["expected_skill"]
        domain = entry.get("domain") if use_domain else None
        payload = search_knowledge.run_search(entry["query"], ctx, domain=domain)
        skill_ids = [skill["id"] for skill in payload.get("skills", [])]
        top_k = int(entry.get("top_k", default_top_k))
        if not payload.get("has_coverage"):
            none_count += 1
        if skill_ids[:1] == [expected]:
            hit_at_1 += 1
        if expected in skill_ids[:top_k]:
            hit_at_3 += 1
        else:
            misses.append(
                {
                    "query": entry["query"],
                    "expected": expected,
                    "got": skill_ids[:top_k],
                }
            )

    total = len(entries) or 1
    return {
        "n": len(entries),
        "hit_at_1": hit_at_1 / total,
        "hit_at_3": hit_at_3 / total,
        "none_rate": none_count / total,
        "misses_count": len(misses),
        "misses": misses,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--queries", default=str(DEFAULT_QUERIES), help="Benchmark JSON (default: the held-out set)")
    parser.add_argument("--tag", action="append", default=[], help="Only entries carrying this tag (repeatable)")
    parser.add_argument(
        "--use-domain", action="store_true",
        help="Pass each entry's `domain` into run_search. OFF by default because a "
             "real user supplies none; the published held-out numbers are domain-free.",
    )
    parser.add_argument("--top-k", type=int, default=3, help="Hit@k depth (a per-entry `top_k` overrides it)")
    parser.add_argument(
        "--no-embeddings", action="store_true",
        help="Force the CI configuration (no fastembed, no vector files)",
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    parser.add_argument("--check", action="store_true", help="Validate the benchmark file only; run no queries")
    parser.add_argument("--min-hit1", type=float, help="Fail when Hit@1 falls below this")
    parser.add_argument("--min-hit3", type=float, help="Fail when Hit@3 falls below this")
    parser.add_argument("--max-none", type=float, help="Fail when the NONE rate rises above this")
    args = parser.parse_args()

    path = Path(args.queries)
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    entries = load_queries(path)

    # Loud, first, before any metric: a phantom label makes every number a lie.
    missing = missing_labels(entries)
    if missing:
        print(f"FAIL: {len(missing)} label(s) point at a skill that does not exist on disk:", file=sys.stderr)
        for skill_id in missing:
            print(f"  {skill_id}  (expected {ROOT / 'skills' / skill_id / 'SKILL.md'})", file=sys.stderr)
        return 2

    if args.check:
        problems = check_benchmark(path, entries)
        if problems:
            print(f"FAIL: {path.name} has {len(problems)} problem(s):", file=sys.stderr)
            for problem in problems:
                print(f"  {problem}", file=sys.stderr)
            return 1
        print(f"OK: {path.name} — {len(entries)} queries, all labels resolve, all {len(CATEGORIES)} categories covered.")
        return 0

    if args.tag:
        wanted = set(args.tag)
        entries = [entry for entry in entries if wanted & set(entry.get("tags", []))]
        if not entries:
            print(f"FAIL: no entries carry tag(s) {sorted(wanted)}", file=sys.stderr)
            return 1

    ctx = build_context(use_embeddings=not args.no_embeddings)
    mode = "lexical-only" if args.no_embeddings else "fastembed+skill-vectors"
    result = evaluate(entries, ctx, use_domain=args.use_domain, default_top_k=args.top_k)
    result["embeddings_mode"] = mode
    result["queries_file"] = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    result["use_domain"] = args.use_domain
    result["tags"] = sorted(args.tag)

    breaches: list[str] = []
    if args.min_hit1 is not None and result["hit_at_1"] < args.min_hit1:
        breaches.append(f"Hit@1 {result['hit_at_1']:.4f} < floor {args.min_hit1}")
    if args.min_hit3 is not None and result["hit_at_3"] < args.min_hit3:
        breaches.append(f"Hit@3 {result['hit_at_3']:.4f} < floor {args.min_hit3}")
    if args.max_none is not None and result["none_rate"] > args.max_none:
        breaches.append(f"NONE rate {result['none_rate']:.4f} > ceiling {args.max_none}")
    result["breaches"] = breaches

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Held-out benchmark: {result['queries_file']}")
        print(f"  mode        : {mode}")
        print(f"  domain hint : {'on' if args.use_domain else 'off'}")
        if args.tag:
            print(f"  tags        : {', '.join(sorted(args.tag))}")
        print(f"  n           : {result['n']}")
        print(f"  Hit@1       : {result['hit_at_1']:.1%}")
        print(f"  Hit@{args.top_k}       : {result['hit_at_3']:.1%}")
        print(f"  NONE rate   : {result['none_rate']:.1%}")
        print(f"  misses      : {result['misses_count']}")
        if result["misses"]:
            print("")
            print("  --- misses ---")
            for miss in result["misses"]:
                got = miss["got"][0] if miss["got"] else "(none)"
                print(f"  {miss['query'][:62]:<62} want {miss['expected']}  got {got}")

    for breach in breaches:
        print(f"FAIL: {breach}", file=sys.stderr)
    return 1 if breaches else 0


if __name__ == "__main__":
    sys.exit(main())
