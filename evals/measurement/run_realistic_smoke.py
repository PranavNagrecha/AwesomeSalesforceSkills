#!/usr/bin/env python3
"""Smoke-test the secondary corpora retrieval against hand-crafted realistic
queries (the way a real user would talk to the MCP).

The synthetic NL generator covers breadth; this file covers fidelity.

Usage:
    python3 evals/measurement/run_realistic_smoke.py \\
        --fixtures evals/measurement/realistic_queries.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "mcp" / "sfskills-mcp" / "src"))

from sfskills_mcp import library, paths as _paths  # noqa: E402

_paths.repo_root = lambda: REPO  # type: ignore[assignment]


def _agent_top_ids(query: str, k: int) -> list[str]:
    return [a["name"] for a in library.search_agents(query, limit=k).get("agents", [])][:k]


def _template_top_ids(query: str, k: int) -> list[str]:
    return [t["path"] for t in library.search_templates(query, limit=k).get("templates", [])][:k]


def _tree_top_ids(query: str, k: int) -> list[str]:
    return [t["name"] for t in library.search_decision_trees(query, limit=k).get("trees", [])][:k]


SEARCHERS = {
    "agents": _agent_top_ids,
    "templates": _template_top_ids,
    "decision-trees": _tree_top_ids,
}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--fixtures", default=str(REPO / "evals" / "measurement" / "realistic_queries.json"))
    p.add_argument("--top-k", type=int, default=3)
    args = p.parse_args()

    fixtures = json.loads(Path(args.fixtures).read_text())

    by_corpus = defaultdict(list)
    for fx in fixtures:
        by_corpus[fx["corpus"]].append(fx)

    overall_hit1 = 0
    overall_hit3 = 0
    total = 0
    misses: list[dict] = []

    for corpus, items in by_corpus.items():
        searcher = SEARCHERS[corpus]
        hit1 = 0
        hit3 = 0
        for fx in items:
            topk = searcher(fx["query"], args.top_k)
            if topk and topk[0] == fx["expected"]:
                hit1 += 1
            if fx["expected"] in topk:
                hit3 += 1
            else:
                misses.append({
                    "corpus": corpus,
                    "query": fx["query"],
                    "expected": fx["expected"],
                    "top1": topk[0] if topk else None,
                    "top3": topk[:3],
                })
        n = len(items)
        total += n
        overall_hit1 += hit1
        overall_hit3 += hit3
        print(f"{corpus:>16}  N={n:3}  Hit@1={hit1/n:.0%}  Hit@3={hit3/n:.0%}")

    print(f"{'OVERALL':>16}  N={total:3}  Hit@1={overall_hit1/total:.1%}  Hit@3={overall_hit3/total:.1%}")
    if misses:
        print("\nMisses:")
        for m in misses[:20]:
            print(f"  [{m['corpus']:>15}] {m['query']!r}")
            print(f"        expected: {m['expected']}  top1: {m['top1']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
