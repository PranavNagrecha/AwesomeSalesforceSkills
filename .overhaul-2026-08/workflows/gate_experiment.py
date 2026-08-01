"""Decisive experiment on the coverage gate.

Current behaviour: skills are RANKED by max_score (best single chunk) but the
coverage GATE compares min_skill_score against `score`, the CUMULATIVE sum of
chunk scores. That rewards breadth of weak matches and punishes one precise
match, which is backwards for this corpus.

This sweeps alternative gate functions across BOTH:
  - the 1,356 curated fixtures (the metric the repo already tracks; must not regress)
  - 60 held-out realistic phrasings (the metric that reflects real users)
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.getcwd())
from scripts.search_knowledge import (  # noqa: E402
    build_search_context, _sanitize_query_for_fts5, embed_query,
)
from pipelines.lexical_index import search_index  # noqa: E402
from pipelines.ranking import rerank_results, aggregate_skill_scores  # noqa: E402

root = Path(os.getcwd())
ctx = build_search_context(root)

fixtures = json.load(open("vector_index/query-fixtures.json"))["queries"]
import random
random.seed(11)
fx_sample = random.sample(fixtures, 400)
heldout = [r["q"] for r in json.load(open(
    "/private/tmp/claude-501/-Users-pranavnagrecha-VS-Code-Personal-SfSkills/"
    "c190ea2f-6abb-4296-8a86-59fc95885f09/scratchpad/heldout-results.json"))]


def rank(q):
    sq = _sanitize_query_for_fts5(q)
    rows = search_index(root / "vector_index" / "lexical.sqlite", sq, None, ctx.lexical_limit)
    qv = embed_query(sq, ctx.embedding_config)
    ranked = rerank_results(qv, rows, ctx.embeddings, None, skill_embeddings=ctx.skill_embeddings)
    return aggregate_skill_scores(ranked, ctx.result_limit)


GATES = {
    "current (cumulative >= 1.5)": lambda s: s["score"] >= 1.5,
    "max_score >= 1.5":            lambda s: s["max_score"] >= 1.5,
    "max_score >= 1.2":            lambda s: s["max_score"] >= 1.2,
    "max_score >= 1.0":            lambda s: s["max_score"] >= 1.0,
    "max_score >= 0.8":            lambda s: s["max_score"] >= 0.8,
    "max>=1.0 OR cumulative>=1.5": lambda s: s["max_score"] >= 1.0 or s["score"] >= 1.5,
    "max>=0.8 OR cumulative>=1.5": lambda s: s["max_score"] >= 0.8 or s["score"] >= 1.5,
}

print("Ranking fixtures...", flush=True)
fx_ranked = [(fx["expected_skill"], rank(fx["query"])) for fx in fx_sample]
print("Ranking held-out...", flush=True)
ho_ranked = [(None, rank(q)) for q in heldout]

print()
print("=" * 96)
print(f"{'GATE':<32} | {'FIXTURES (n=400)':<34} | {'HELD-OUT (n=60)'}")
print(f"{'':<32} | {'Hit@1    Hit@3    falseNONE':<34} | {'NONE rate':<12}")
print("=" * 96)

for name, fn in GATES.items():
    h1 = h3 = none_ct = false_none = 0
    for expected, skills in fx_ranked:
        kept = [s for s in skills if fn(s)]
        ids = [s["id"] for s in kept]
        if expected in ids[:1]:
            h1 += 1
        if expected in ids[:3]:
            h3 += 1
        if not kept:
            none_ct += 1
            if expected in [s["id"] for s in skills]:
                false_none += 1
    ho_none = sum(1 for _, skills in ho_ranked if not [s for s in skills if fn(s)])
    n = len(fx_ranked)
    print(f"{name:<32} | {h1/n:6.1%}  {h3/n:6.1%}   {false_none:3d} false      "
          f"| {ho_none:2d}/60 = {ho_none/60:5.1%}")

print("=" * 96)
print()
print("Interpretation: the fixture Hit@1/Hit@3 must not regress (sacred floor),")
print("while the held-out NONE rate should fall sharply. A gate that improves")
print("held-out coverage without moving fixture Hit@1 is a free win.")
