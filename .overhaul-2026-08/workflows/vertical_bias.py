"""Test the 'vertical skills outrank generic skills on generic queries' hypothesis.

A generic platform question ("set up business hours") should never land on an
industry-specific skill (Financial Services Cloud action plans). Measure how
often it does.
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.getcwd())
from scripts.search_knowledge import build_search_context, _sanitize_query_for_fts5, embed_query  # noqa
from pipelines.lexical_index import search_index  # noqa
from pipelines.ranking import rerank_results, aggregate_skill_scores  # noqa

VERTICAL = re.compile(
    r"(^|/)(npsp|nonprofit|fsc|financial-services|health-cloud|hc-|industries|"
    r"omnistudio|automotive|energy|utilities|manufacturing|consumer-goods|"
    r"education|public-sector|media|comms|net-zero|loyalty|revenue-cloud|cpq)",
    re.I,
)

GENERIC = [
    "set up business hours and holidays",
    "clean up duplicate records",
    "encrypt sensitive fields",
    "improve record page load time",
    "configure approval process",
    "set up case escalation rules",
    "design a data model for a new object",
    "bulk load records into salesforce",
    "write apex unit tests",
    "build a screen flow for data entry",
    "configure sharing rules",
    "set up email templates",
    "create a validation rule",
    "audit user permissions",
    "integrate with an external rest api",
    "set up a scheduled job",
    "troubleshoot a failing deployment",
    "design a permission set architecture",
    "track field history",
    "build a lightning web component",
    "configure omni channel routing",
    "set up single sign on",
    "manage picklist values",
    "plan a data migration",
    "review apex code for security",
]

root = Path(os.getcwd())
ctx = build_search_context(root)

hits = 0
rows = []
for q in GENERIC:
    sq = _sanitize_query_for_fts5(q)
    lex = search_index(root / "vector_index" / "lexical.sqlite", sq, None, ctx.lexical_limit)
    qv = embed_query(sq, ctx.embedding_config)
    ranked = rerank_results(qv, lex, ctx.embeddings, None, skill_embeddings=ctx.skill_embeddings)
    skills = aggregate_skill_scores(ranked, ctx.result_limit)
    top = skills[0]["id"] if skills else "-"
    top3 = [s["id"] for s in skills[:3]]
    is_v = bool(VERTICAL.search(top))
    n_v = sum(1 for s in top3 if VERTICAL.search(s))
    if is_v:
        hits += 1
    rows.append((q, top, is_v, n_v, top3))

n = len(GENERIC)
print("=" * 90)
print(f"GENERIC QUERIES ROUTED TO A VERTICAL/INDUSTRY SKILL AT RANK 1: {hits}/{n} = {hits/n:.1%}")
print("=" * 90)
for q, top, is_v, n_v, top3 in rows:
    flag = "  <== VERTICAL" if is_v else ""
    print(f'{"V" if is_v else " "} "{q[:44]:<44}" -> {top}{flag}')
print()
print("Corpus baseline: share of all skills that are vertical-flavoured:")
import glob
allsk = [p.split("skills/")[1].rsplit("/SKILL.md", 1)[0] for p in glob.glob("skills/*/*/SKILL.md")]
vb = sum(1 for s in allsk if VERTICAL.search(s))
print(f"  {vb}/{len(allsk)} = {vb/len(allsk):.1%}")
print(f"  If ranking were unbiased, expect ~{vb/len(allsk):.1%} of rank-1 hits to be vertical.")
