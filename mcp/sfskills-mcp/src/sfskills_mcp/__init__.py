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
#   0.4.4 — Pre-prod QA dispatch (ExampleOrg Dev PN, 997 skills, 47 runtime
#           agents). 18 fixes spanning 6 P0 release blockers, 9 P1 polish,
#           3 P2 housekeeping. Highlights:
#           P0 product bugs (6): list_flows_on_object now queries
#             FlowDefinitionView via Standard SOQL (Flow.DeveloperName fails
#             on API 67); list_custom_fields drops the unsupported SOQL
#             ESCAPE clause and filters __c suffix client-side; tooling_query
#             skips auto-LIMIT on non-grouped aggregate queries; fastembed
#             import is gracefully optional (pip install sfskills-mcp[embeddings]);
#             dead citations to data-cloud-reverse-etl-to-core-salesforce
#             removed from 2 build-time AGENT.mds; run_sf_json returns a
#             structured error when stdout has no JSON object instead of
#             silently returning {}.
#           Envelope contract (3): emit_envelope now validates every
#             envelope against output-envelope.schema.json via
#             jsonschema.Draft202012Validator + a pre-loaded
#             referencing.Registry (graceful fallback if jsonschema is
#             absent); schema $ids migrated from
#             https://sfskills.local/... to urn:sfskills:<name> so
#             cross-schema $refs resolve without network access; run_id
#             pattern rejects `:` per DELIVERABLE_CONTRACT.md (filesystem
#             safety).
#           Doc drift (1): 4 docs corrected — the old roster total dropped
#             by 9 to the current 47 (the 9 that moved to deprecated
#             wrappers via audit-router consolidation).
#           Slash-command + alias mismatches (2): two AGENT.mds advertised
#             slash commands that didn't exist (/design-cmt-or-settings,
#             /design-entitlement-and-milestones); commands/
#             automation-migration-router.md and its AGENT.md aligned on
#             /automation-migration-router (legacy aliases preserved).
#           Retrieval (2): flow/fault-handling adds 4 triggers covering
#             "fault path subflow" phrasing; automation-selection title
#             carries "(Flow vs Apex)" and a cross-tree comparison
#             paragraph (lifts but does not fully solve the
#             flow-pattern-selector slug bias).
#           P2 housekeeping (3): sf CLI floor documented (2.0.0 minimum,
#             2.103.7 tested in QA, latest recommended); access_token_preview
#             docs corrected — fully masked ("***"), not prefix/suffix
#             preview as previously claimed; the legacy hard-coded
#             skill-count fallback string retired from
#             SERVER_INSTRUCTIONS — registry/skills.json is the only source
#             of truth, pinned in _STALE_LITERALS to prevent regression.
#   0.4.5 / 0.4.6 — no history entry was written at the time; see the git log
#           for tags mcp-v0.4.4..mcp-v0.4.6. Only 0.4.6 ever reached PyPI.
#   0.4.7 — Data-bundle release. Server code is unchanged; what ships is a
#           refreshed corpus. (a) Depth pass on 50 skill packages (~10 KB ->
#           55-90 KB each). (b) Agentforce topics->subagents rename landed on
#           the routing surface: the term reached 39 package bodies but 0
#           shipped glosses, because build_gloss() ranks lead last and glosses
#           run at the 220-char cap. Four trigger substitutions fixed it;
#           scripts/check_gloss_coverage.py now makes the failure checkable.
#           (c) Documentation rewritten and re-verified against the repo.
#           (d) Retracted the "79.2% -> 92.2% Hit@1" routing headline — it did
#           not survive re-scoring; router accuracy 88.3% -> 96.1% stands.

__version__ = "0.4.7"
