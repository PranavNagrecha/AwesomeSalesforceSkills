"""Measure the false 'Coverage: NONE' rate.

A false NONE = min_skill_score suppresses every skill (so the consumer is told
"the library has no coverage, use official docs") even though the expected
skill IS present in the unfiltered ranked list. That is the worst possible
retrieval failure for this product: the library owns the right answer and
actively denies it.
"""
import json
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, os.getcwd())
sys.path.insert(0, str(Path(os.getcwd()) / "scripts"))

from scripts.search_knowledge import (  # noqa: E402
    build_search_context,
    _sanitize_query_for_fts5,
    aggregate_skill_scores,
)
from pipelines.lexical_index import search_index  # noqa: E402
from pipelines.ranking import rerank_results  # noqa: E402
from scripts.search_knowledge import embed_query  # noqa: E402

N = int(sys.argv[1]) if len(sys.argv) > 1 else 300
root = Path(os.getcwd())
fixtures = json.load(open("vector_index/query-fixtures.json"))["queries"]
random.seed(11)
sample = random.sample(fixtures, min(N, len(fixtures)))

print(f"Building search context (loads chunks + embeddings)...", flush=True)
ctx = build_search_context(root)
print(f"min_skill_score = {ctx.min_skill_score}", flush=True)

stats = {
    "n": 0,
    "none_coverage": 0,
    "false_none_top1": 0,
    "false_none_top3": 0,
    "false_none_any": 0,
    "true_none": 0,
    "hit1_unfiltered": 0,
    "hit3_unfiltered": 0,
    "hit1_filtered": 0,
    "hit3_filtered": 0,
}
examples = []
suppressed_scores = []

for fx in sample:
    q = _sanitize_query_for_fts5(fx["query"])
    expected = fx["expected_skill"]
    rows = search_index(root / "vector_index" / "lexical.sqlite", q, None, ctx.lexical_limit)
    qv = embed_query(q, ctx.embedding_config)
    ranked = rerank_results(qv, rows, ctx.embeddings, None, skill_embeddings=ctx.skill_embeddings)
    all_skills = aggregate_skill_scores(ranked, ctx.result_limit)
    kept = [s for s in all_skills if s["score"] >= ctx.min_skill_score]

    ids_all = [s["id"] for s in all_skills]
    ids_kept = [s["id"] for s in kept]
    stats["n"] += 1
    if expected in ids_all[:1]:
        stats["hit1_unfiltered"] += 1
    if expected in ids_all[:3]:
        stats["hit3_unfiltered"] += 1
    if expected in ids_kept[:1]:
        stats["hit1_filtered"] += 1
    if expected in ids_kept[:3]:
        stats["hit3_filtered"] += 1

    if not kept:
        stats["none_coverage"] += 1
        if expected in ids_all[:1]:
            stats["false_none_top1"] += 1
        if expected in ids_all[:3]:
            stats["false_none_top3"] += 1
        if expected in ids_all:
            stats["false_none_any"] += 1
            sc = next(s["score"] for s in all_skills if s["id"] == expected)
            suppressed_scores.append(sc)
            if len(examples) < 15:
                examples.append(
                    (fx["query"], expected, round(sc, 3), ids_all[0] if ids_all else "-",
                     round(all_skills[0]["score"], 3) if all_skills else 0)
                )
        else:
            stats["true_none"] += 1

n = stats["n"]
print()
print("=" * 78)
print(f"SAMPLE: {n} fixture queries   min_skill_score={ctx.min_skill_score}")
print("=" * 78)
print(f'Reported "Coverage: NONE"        : {stats["none_coverage"]:4d}  ({stats["none_coverage"]/n:6.1%})')
print(f'  ...of which FALSE (expected skill was ranked #1) : {stats["false_none_top1"]:4d}')
print(f'  ...of which FALSE (expected skill in top 3)      : {stats["false_none_top3"]:4d}')
print(f'  ...of which FALSE (expected skill anywhere)      : {stats["false_none_any"]:4d}')
print(f'  ...genuinely uncovered                           : {stats["true_none"]:4d}')
print()
print(f'Hit@1 BEFORE threshold : {stats["hit1_unfiltered"]/n:6.1%}    AFTER threshold : {stats["hit1_filtered"]/n:6.1%}')
print(f'Hit@3 BEFORE threshold : {stats["hit3_unfiltered"]/n:6.1%}    AFTER threshold : {stats["hit3_filtered"]/n:6.1%}')
print()
if suppressed_scores:
    suppressed_scores.sort()
    mid = suppressed_scores[len(suppressed_scores) // 2]
    print(f"Suppressed correct-skill scores: min={suppressed_scores[0]:.3f} "
          f"median={mid:.3f} max={suppressed_scores[-1]:.3f}  (threshold {ctx.min_skill_score})")
print()
print("EXAMPLES OF FALSE 'NO COVERAGE' (library owns the answer but denies it):")
for q, exp, sc, top, tsc in examples:
    print(f'  q="{q[:66]}"')
    print(f'     expected={exp} score={sc}  (top ranked was {top} @ {tsc})')
