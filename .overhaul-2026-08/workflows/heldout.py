"""Held-out realistic-query probe.

The 1,356 fixtures in vector_index/query-fixtures.json are author-curated
trigger phrasings — they are close paraphrases of text that is itself indexed,
so they measure the easy case. These 60 queries are written the way a working
Salesforce practitioner actually types into an AI assistant, deliberately
avoiding the vocabulary of the trigger lines. No labels needed for the headline
metric: how often does the library say "Coverage: NONE" on a question it
plainly should answer?
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.getcwd())
from scripts.search_knowledge import (  # noqa: E402
    build_search_context, _sanitize_query_for_fts5, aggregate_skill_scores, embed_query,
)
from pipelines.lexical_index import search_index  # noqa: E402
from pipelines.ranking import rerank_results  # noqa: E402

QUERIES = [
    # admin — basic, high frequency
    "how do I add a new user in Salesforce",
    "give someone access to an object without changing their profile",
    "stop sales reps from editing closed opportunities",
    "make a field required only for one record type",
    "set up an approval when a discount is over 20 percent",
    "our picklist has 400 values and nobody knows which are used",
    "why can't my user see the record their manager owns",
    "deactivate a user but keep their records",
    "send an email when a case has been open too long",
    "build a report showing opportunities with no activity in 30 days",
    # dev
    "why is my LWC slow",
    "my trigger fires twice and I don't know why",
    "too many SOQL queries 101 error",
    "how do I stop my flow from hitting SOQL limits",
    "write a test that actually catches bulk problems",
    "call an external REST API from Apex with OAuth",
    "my batch job keeps timing out",
    "share data between two lightning web components",
    "mock an HTTP callout in a test class",
    "the record page is loading really slowly",
    # data
    "migrate 5 million records into Salesforce without blowing up",
    "clean up duplicate accounts",
    "our reports are timing out on a big object",
    "load data in the right order when objects reference each other",
    "delete personal data for GDPR",
    "keep an external system and Salesforce in sync both ways",
    # architect / decisions
    "should I use Flow or Apex for this",
    "when do I need a queueable instead of a future method",
    "how do I decide between platform events and change data capture",
    "justify sharing model changes to leadership",
    "what breaks if we turn on person accounts",
    "planning a multi org consolidation",
    # security
    "audit who has modify all data",
    "our security review flagged CRUD FLS issues",
    "encrypt a field that's already got data in it",
    "set up SSO with Okta",
    "restrict access by IP address",
    # agentforce / AI
    "build an agent that can look up an order status",
    "my agentforce action returns the wrong record",
    "ground a prompt template in CRM data",
    "test that my AI agent doesn't hallucinate",
    # devops
    "our deployment keeps failing on test coverage",
    "set up CI for a Salesforce project",
    "move changes from sandbox to production safely",
    "what's the deal with unlocked packages",
    # flow
    "flow is erroring for some users but not others",
    "screen flow needs to show different fields based on a picklist",
    "schedule something to run every night",
    "flow keeps sending me error emails",
    # service / experience
    "route cases to the right queue based on product",
    "set up business hours and holidays for SLAs",
    "build a customer portal where they can log cases",
    "knowledge articles aren't showing up in search",
    # integration
    "our middleware calls are hitting API limits",
    "expose Salesforce data to an external app securely",
    "handle retries when a callout fails",
    # misc / vague — the honest hard cases
    "the org is a mess where do I start",
    "make Salesforce faster",
    "we're going live next month what should I check",
    "reduce our technical debt",
]

root = Path(os.getcwd())
ctx = build_search_context(root)
none_ct = 0
rows_out = []
for q in QUERIES:
    sq = _sanitize_query_for_fts5(q)
    rows = search_index(root / "vector_index" / "lexical.sqlite", sq, None, ctx.lexical_limit)
    qv = embed_query(sq, ctx.embedding_config)
    ranked = rerank_results(qv, rows, ctx.embeddings, None, skill_embeddings=ctx.skill_embeddings)
    all_skills = aggregate_skill_scores(ranked, ctx.result_limit)
    kept = [s for s in all_skills if s["score"] >= ctx.min_skill_score]
    top = all_skills[0] if all_skills else None
    if not kept:
        none_ct += 1
    rows_out.append({
        "q": q,
        "covered": bool(kept),
        "top": top["id"] if top else None,
        "top_score": round(top["score"], 3) if top else 0.0,
        "kept": [s["id"] for s in kept[:3]],
    })

n = len(QUERIES)
print("=" * 84)
print(f"HELD-OUT REALISTIC QUERIES: n={n}   min_skill_score={ctx.min_skill_score}")
print(f'Reported "Coverage: NONE": {none_ct}/{n} = {none_ct/n:.1%}')
print(f'(same metric on curated fixtures: 0.8%)')
print("=" * 84)
print()
print("--- SUPPRESSED (told the caller there is no coverage) ---")
for r in rows_out:
    if not r["covered"]:
        print(f'  {r["top_score"]:5.3f}  "{r["q"][:58]}"  -> best was {r["top"]}')
print()
print("--- COVERED ---")
for r in rows_out:
    if r["covered"]:
        print(f'  {r["top_score"]:5.3f}  "{r["q"][:58]}"  -> {r["kept"][0]}')
json.dump(rows_out, open("/private/tmp/claude-501/-Users-pranavnagrecha-VS-Code-Personal-SfSkills/c190ea2f-6abb-4296-8a86-59fc95885f09/scratchpad/heldout-results.json", "w"), indent=1)
