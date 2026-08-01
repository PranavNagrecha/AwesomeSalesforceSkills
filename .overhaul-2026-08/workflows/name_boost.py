"""Test a skill-name/description match signal against a hand-labeled held-out set.

Hypothesis: the ranker has no notion of skill centrality — it cannot tell
"this skill is ABOUT X" from "this skill MENTIONS X". Adding a signal for
query-to-skill-name/description overlap should fix the misroutes without
regressing the curated fixtures.
"""
import json
import os
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, os.getcwd())
from scripts.search_knowledge import build_search_context, _sanitize_query_for_fts5, embed_query  # noqa
from pipelines.lexical_index import search_index  # noqa
from pipelines.ranking import rerank_results, aggregate_skill_scores  # noqa

root = Path(os.getcwd())
ctx = build_search_context(root)

# Hand-labeled held-out set. Each label was verified to exist on disk.
# Written as a practitioner would type, NOT copied from any triggers: line.
LABELED = [
    ("create a validation rule", "admin/validation-rules"),
    ("set up email templates", "admin/email-templates-and-alerts"),
    ("configure approval process", "admin/approval-processes"),
    ("integrate with an external rest api", "integration/rest-api-patterns"),
    ("write apex unit tests", "apex/apex-test-setup-patterns"),
    ("clean up duplicate records", "admin/duplicate-management"),
    ("bulk load records into salesforce", "data/bulk-api-and-large-data-loads"),
    ("plan a data migration", "data/data-migration-planning"),
    ("track field history", "data/field-history-tracking"),
    ("configure omni channel routing", "admin/omni-channel-routing-setup"),
    ("manage picklist values", "admin/picklist-data-integrity"),
    ("review apex code for security", "security/secure-coding-review-checklist"),
    ("why is my LWC slow", "lwc/lwc-performance"),
    ("how do I add a new user in Salesforce", "admin/user-management"),
    ("audit who has modify all data", "security/privileged-access-management"),
    ("my batch job keeps timing out", "apex/batch-apex-patterns"),
    ("what breaks if we turn on person accounts", "data/person-accounts"),
    ("test that my AI agent doesn't hallucinate", "agentforce/agentforce-eval-harness"),
    ("set up single sign on", "security/sso-saml-troubleshooting"),
    ("encrypt sensitive fields", "architect/salesforce-shield-architecture"),
]
LABELED = [(q, s) for q, s in LABELED if (root / "skills" / s / "SKILL.md").exists()]
print(f"Hand-labeled held-out set: {len(LABELED)} queries (all labels verified on disk)")

registry = json.load(open("registry/skills.json"))
recs = registry if isinstance(registry, list) else registry.get("skills", registry)
META = {}
for r in recs:
    sid = r.get("id") or f"{r.get('category')}/{r.get('name')}"
    META[sid] = (r.get("name", ""), r.get("description", ""))

STOP = {"a", "an", "the", "how", "do", "i", "my", "is", "in", "to", "for", "of", "on",
        "and", "or", "with", "what", "why", "set", "up", "get", "can", "does", "salesforce"}


def toks(s):
    return {t for t in re.split(r"[^a-z0-9]+", s.lower()) if t and t not in STOP and len(t) > 2}


def name_bonus(qtok, sid):
    name, desc = META.get(sid, (sid.split("/")[-1], ""))
    ntok = toks(name.replace("-", " ")) | toks(sid.split("/")[-1].replace("-", " "))
    dtok = toks(desc)
    if not qtok:
        return 0.0
    n_ov = len(qtok & ntok) / len(qtok)
    d_ov = len(qtok & dtok) / len(qtok)
    return n_ov, d_ov


def rank(q):
    sq = _sanitize_query_for_fts5(q)
    lex = search_index(root / "vector_index" / "lexical.sqlite", sq, None, ctx.lexical_limit)
    qv = embed_query(sq, ctx.embedding_config)
    ranked = rerank_results(qv, lex, ctx.embeddings, None, skill_embeddings=ctx.skill_embeddings)
    return aggregate_skill_scores(ranked, ctx.result_limit)


fixtures = json.load(open("vector_index/query-fixtures.json"))["queries"]
random.seed(11)
fx = random.sample(fixtures, 400)

print("Ranking...", flush=True)
fx_ranked = [(f["expected_skill"], f["query"], rank(f["query"])) for f in fx]
ho_ranked = [(exp, q, rank(q)) for q, exp in LABELED]


def evaluate(wn, wd, label):
    def score_set(data):
        h1 = h3 = 0
        for expected, q, skills in data:
            qtok = toks(q)
            rescored = []
            for s in skills:
                n_ov, d_ov = name_bonus(qtok, s["id"])
                rescored.append((s["max_score"] + wn * n_ov + wd * d_ov, s["score"], s["id"]))
            rescored.sort(key=lambda x: (-x[0], -x[1], x[2]))
            ids = [r[2] for r in rescored]
            if expected in ids[:1]:
                h1 += 1
            if expected in ids[:3]:
                h3 += 1
        return h1 / len(data), h3 / len(data)

    f1, f3 = score_set(fx_ranked)
    o1, o3 = score_set(ho_ranked)
    print(f"{label:<34} | fixtures H@1 {f1:6.1%} H@3 {f3:6.1%} | held-out H@1 {o1:6.1%} H@3 {o3:6.1%}")


print()
print("=" * 100)
evaluate(0.0, 0.0, "baseline (max_score only)")
for wn, wd in [(0.5, 0.0), (1.0, 0.0), (1.5, 0.0), (1.0, 0.3), (1.5, 0.5), (2.0, 0.5), (2.0, 1.0), (3.0, 1.0)]:
    evaluate(wn, wd, f"name*{wn} + desc*{wd}")
print("=" * 100)
