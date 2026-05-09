"""SfSkills MCP server — exposes the SfSkills library and live org metadata over MCP."""

# Bumped at the end of each Tier:
#   0.1.0 — Wave-2 baseline (23 tools, hand-coded agent roster)
#   0.1.1 — Tier A: drift fix (frontmatter-driven counts, freshness tests)
#   0.2.0 — Tier B: tool annotations + 68 prompts + 5 resource shapes + probe progress
#   0.3.0 — Tier C: 14 new tools (8 dev-org + 5 search + suggest_agent)
#   0.4.0 — Tier D: health tool + per-tool timeouts + PyPI publish prep
#   0.4.1 — Hygiene patch: rebuild data bundle without hardcoded /Users/ paths
#           in commands/audit-router.md / automation-migration-router.md /
#           run-queue.md (the latter had broken `cd /Users/<author>/...` shell
#           snippets in the prompt body); drop 2 unused imports.
#   0.4.2 — Retrieval quality: agents/templates/decision-trees Hit@1 lifted
#           18→95% / 25→89% / 56→82% via slug-aware scorer (whole-word slug
#           match weight 15, light suffix stemmer for verb forms, slug
#           coverage bonus, bigram bonus, sqrt-capped body weight). Pre-commit
#           hook decoupled from chunk-level embeddings rebuild via
#           --skip-embeddings (the explicit `python3 scripts/build_index.py`
#           path still encodes). Skill-level + chunk-level embedding indexes
#           plumbed through pipelines/ranking.rerank_results — chunk-level
#           default at vector weight 0.2 lifts NL Hit@3 +1.8pp on 1,418-Q
#           audit while curated 1,285-Q baseline holds at 98.6%.
__version__ = "0.4.2"
