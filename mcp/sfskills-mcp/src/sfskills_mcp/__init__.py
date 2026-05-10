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
#   0.4.3 — Production hardening surfaced by live-org integration testing
#           (ExampleOrg Dev PN sandbox, 4,000+ ApexClass, 30,000+ CustomField).
#           10 fixes:
#           Security (1): universal credential redactor in sf_cli covering
#             every stdout/stderr path + parsed-payload walker. Stops the
#             accessToken leak demonstrated when sf CLI emits a warning
#             before its JSON.
#           Broken probes (3): probe_apex_references (Body LIKE not
#             filterable), probe_flow_references (Metadata one-row
#             restriction → two-pass), probe_matching_rules (four schema
#             mistakes: IsActive→RuleStatus, FieldName→Field, MatchingRuleItem
#             and DuplicateRule require Standard API not Tooling,
#             DuplicateRule.ParentId never existed).
#           tooling_query polish (3): string-literal stripping so DML scan
#             stops false-positive-blocking ``WHERE Name = 'foo INSERT bar'``,
#             default flipped tooling=True→False (Standard API is the
#             common case), SELECT detection allows newline/tab/leading
#             whitespace.
#           suggest_agent (1): decision-tree score floor (default 20)
#             suppresses irrelevant trees — Phase 6 audit 2/8 correct →
#             8/8 correct.
#           Sandbox detection (1): infer is_sandbox from instance_url when
#             sf CLI omits it (sandbox/scratch/develop variants + legacy
#             CS pods).
#           Warning-prefix JSON parsing (1): strip sf CLI warning lines
#             before json.loads — same root cause as the security leak,
#             now closed at the parsing layer too.
__version__ = "0.4.3"
