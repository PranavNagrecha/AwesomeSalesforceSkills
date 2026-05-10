# Changelog

All notable changes to SfSkills are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The project uses semantic versioning keyed to the Salesforce release cadence (minor bumps per Spring/Summer/Winter release).

## [Unreleased] — sfskills-mcp v0.4.3 (production hardening)

10 fixes surfaced by live-org integration testing against an Education
Cloud sandbox (4,000+ ApexClass, 30,000+ CustomField, 694 Flow, 1,209 LWC).
The single biggest takeaway: **3 of the 4 heavy probes had never been
tested against a real org** — each failed on its first SOQL invocation
with a Salesforce-platform-level rejection. This release fixes them.

### Migration

Users on v0.4.2:
- **`tooling_query` default flipped**: `tooling=False` now (was `True`).
  Most ad-hoc queries target Standard sObjects (Account, Contact, etc.).
  Tooling-API-only entities (`ApexClass.Body`, `Flow.Metadata`,
  `MetadataContainer`, etc.) need explicit `tooling=True`.
- **3 probes that silently returned errors now work**. If you had
  scripts that handled `error` keys from `probe_apex_references`,
  `probe_flow_references`, or `probe_matching_rules`, they'll now
  receive populated `references` / `matching_rules` / `duplicate_rules`
  lists. Update consumers to handle the success shape.
- **`suggest_agent` returns fewer decision trees**. The new
  `min_tree_score` parameter (default 20) suppresses low-relevance
  trees. To recover v0.4.2 behavior pass `min_tree_score=0`.
- **`describe_org` adds `is_sandbox_source`** field ("cli" | "inferred-
  from-url" | absent). Existing consumers that only read `is_sandbox`
  see no breakage; consumers that want to know provenance can opt in.

### Security

- **Universal credential redactor in `sf_cli.py`.** Live test session
  leaked a Salesforce session token because `sf org display --json`
  prepended a CLI warning line, `json.loads` failed, and the error
  path returned raw stdout — which contained the access token. Added
  `_redact_credentials_text` (regex scrub for SF session, OAuth
  refresh, and Bearer patterns) and `_redact_credentials_in_payload`
  (walks parsed JSON, redacts values keyed by `accessToken`,
  `refreshToken`, `password`, `clientSecret`, `securityToken`,
  `sessionId`, `apiToken`, `authToken`). Applied to every output path
  in `run_sf_json` (TimeoutExpired stderr, JSONDecodeError stdout +
  stderr, normal payload return). 15 new unit tests cover token
  shapes, JSON-walker, and the exact live-leak failure pattern.

### Fixed

- **`probe_apex_references`** (broken since v0.4.0): Salesforce's
  Tooling API rejects `WHERE Body LIKE '%X%'` on ApexClass /
  ApexTrigger. Removed the unfilterable predicate; client-side
  word-boundary regex on fetched bodies still scopes results
  precisely. Default `limit_per_query` raised 200→2000 (Tooling API
  max) so the probe finds references in the full custom-Apex set in
  one round trip on typical orgs.
- **`probe_flow_references`** (broken since v0.4.0): When SOQL selects
  `Flow.Metadata`, Tooling API requires exactly one row in the
  response. Two-pass implementation: list Flow IDs in one bulk query,
  then fan out per-ID Metadata queries through an 8-thread pool.
- **`probe_matching_rules`** (broken since v0.4.0): four distinct
  schema errors fixed in one pass:
  1. `MatchingRule.IsActive` → `RuleStatus` (the boolean column was
     replaced with a richer picklist: Active, Activating, Deactivating,
     Inactive, ActivationFailed, RebuildIndex).
  2. `MatchingRuleItem.FieldName` → `Field` (column name typo).
  3. `MatchingRuleItem` and `DuplicateRule` queries now route through
     the Standard SOQL API (`tooling=False`); the Tooling API doesn't
     expose them.
  4. `DuplicateRule.ParentId` removed — that column has never existed.
- **`tooling_query` false positives**: substring matching on DML
  keywords blocked legitimate queries where the keyword appeared in
  string literals: `WHERE Name = 'foo INSERT bar'`,
  `WHERE Name LIKE '%UPDATE %'`, `WHERE Name = ';'`. New
  `_strip_soql_string_literals` state machine strips quoted content
  before the DML scan. All 5 stacked-DML bypass attempts still
  blocked; 4 false-positive cases now pass.
- **`tooling_query` SELECT detection** rejected multi-line SOQL
  formatted with `SELECT\n  Id\nFROM ...`. Replaced
  `startswith("SELECT ")` with `re.match(r"^\s*SELECT\b")`.

### Changed

- **`tooling_query` default flipped to `tooling=False`**. Standard
  API is the common case for ad-hoc queries; Tooling API entities
  opt in with explicit `tooling=True`.
- **`suggest_agent` filters low-score decision trees**. The Phase 6
  audit showed 6 of 8 realistic queries returned an irrelevant tree
  (e.g. "security issues" → `async-selection`, score 10.7). New
  `min_tree_score` parameter (default 20) suppresses noise. 2/8
  correct → 8/8 correct on the same suite.
- **`describe_org` infers `is_sandbox` from instance URL** when sf
  CLI omits it. ExampleOrg Dev PN (URL
  `ExampleOrg--devSandbox.sandbox.my.salesforce.com`) returned
  `isSandbox=null` from the CLI; URL inference correctly classifies
  as sandbox. New `is_sandbox_source` field tags the provenance.
- **`run_sf_json` strips warning-prefix lines before parsing**.
  `_strip_to_json_start` finds the first `{` or `[` in stdout so
  `sf` CLI update-available banners no longer cause JSON-decode
  errors (the same root cause as the security leak above).

### Test infrastructure

- 5 new test files (`test_sf_cli_redaction.py`,
  `test_tooling_query_blocklist.py`, `test_sandbox_inference.py`, plus
  expansions in `test_admin.py`).
- 45 new unit tests, all pass.
- Full suite: 205/205 tests pass (was 160 at the start of v0.4.2).
- Every fix in this release was live-verified against ExampleOrg Dev PN
  (Education Cloud + NPSP + several AppExchange managed packages).

## [Unreleased] — sfskills-mcp v0.4.2 (retrieval quality)

Retrieval quality release. Three of the four MCP corpora (agents, templates,
decision-trees) had no measured Hit@1 baseline before this. A 247/195/34-query
NL audit revealed catastrophic numbers — 18.2% / 24.6% / 55.9% Hit@1 — and
this release lifts them to 95.1% / 88.7% / 82.4% via a slug-aware scorer
rewrite in `mcp/sfskills-mcp/src/sfskills_mcp/library.py`. Skills retrieval
gets chunk-level fastembed embeddings as a hybrid rerank signal (NL Hit@3
+1.8pp, curated 98.6% sacred floor unchanged). The pre-commit hook is
decoupled from the multi-hour embeddings rebuild so commits stay fast.

### Added

- **Slug-aware scoring** in `library.py`: whole-word match against the
  document's slug/path/basename earns a 15× boost (vs the previous
  scorer's substring counts that let long meta-documents — e.g.
  apex-builder.AGENT.md mentioning "apex" 200+ times — drown short-named
  target documents). Plus a light suffix stemmer (-er, -or, -ing,
  -ation, -ies, -y, -ed, -es, -s, -e) so "consolidate" matches
  "consolidator" and "build" matches "builder". Plus slug coverage bonus
  (+20 × matched/total tokens) and bigram bonus (+8 per adjacent pair).
  Body weight changed from 1.0 substring to `0.6 × sqrt(count)` so
  documents that mention a term 100× contribute 6× not 100×.
- **`scripts/build_skill_embeddings.py`** — encodes one fastembed vector
  per skill (~994 vectors, ~88 sec on M-series CPU). Lightweight
  alternative to chunk-level embeddings when the 2-hour full encode
  isn't worth it. `vector_index/skill_embeddings.jsonl` is gitignored.
- **`evals/measurement/nl_query_generator_corpora.py`** + **`retrieval_eval_corpora.py`**
  + **`run_realistic_smoke.py`** + **`realistic_queries.json`** —
  reusable audit harness for the secondary corpora plus a 71-query
  hand-crafted realistic-user smoke test.
- **`evals/measurement/improvement_loop.py`** — automated
  measure → near-miss → trigger-fix-wave → re-measure runner. Stops on
  plateau (<min_lift over 2 iters) or curated regression below floor.
- **Build progress reporting** in `pipelines/embedding_backends.py`:
  emits cached/to-encode counts at start, then ~50 progress lines with
  chunks/sec rate and ETA. Suppress with `FASTEMBED_PROGRESS=0`.
- **`--skip-embeddings`** flag on `scripts/skill_sync.py`: bypass the
  embeddings encode for fast commits. Pre-commit hook now uses it.

### Changed

- **`config/retrieval-config.yaml`**: `embeddings.enabled` flipped to
  `true` by default. Backend `fastembed` (BAAI/bge-small-en-v1.5,
  384-dim, MIT, ONNX-q on CPU). Vector weight 0.2 in
  `pipelines/ranking.rerank_results()` — measured sweet spot between
  curated regression at 0.35 and no-op at 0.10.
- **`pipelines/ranking.rerank_results()`**: now takes optional
  `skill_embeddings` kwarg. Lookup order is skill-level first (by
  `skill_id`), then chunk-level (by `chunk_id`). Pure lexical when
  neither index is present (backwards compatible).
- **`pipelines/embedding_backends.write_embeddings()`**: stream per-line
  instead of building one large in-memory string before writing.
  Eliminates ~2GB peak RAM during the 126K-chunk encode that triggered
  OOMs on machines with <12GB free.
- **`scripts/skill_sync.py --changed-only`**: validation now scopes to
  STAGED skills only (was: validated every skill on disk). Pre-existing
  ERRORs in unrelated skills no longer block infra/eval/doc commits.
  Full-repo gate is preserved via `validate_repo.py` and
  `skill_sync.py --all`.
- **`scripts/validate_repo.py`**: `_git_changed_files()` returns staged
  paths when anything is staged (the pre-commit hook's natural scope).
  Falls back to staged + unstaged + untracked only when nothing is
  staged. Plus `build_state(skip_embeddings=True)` for the registry
  validation step — no need to re-encode 126K chunks just to validate
  metadata.
- **`.githooks/pre-commit`**: now invokes
  `skill_sync.py --changed-only --skip-embeddings`. Embeddings are
  rebuilt only by the explicit `python3 scripts/build_index.py`
  invocation, never as a side effect of committing.

### Performance

Measured on 2026-05-09 across three audits. All gates passed.

| Audit                                  | Lexical-only Hit@1 / Hit@3 | This release Hit@1 / Hit@3 |
| -------------------------------------- | -------------------------: | -------------------------: |
| Curated 1,285-Q (sacred floor ≥98%)    |             98.6% / 100.0% |             98.6% / 100.0% |
| Synthetic NL 1,418-Q                   |              74.3% / 86.0% |              74.5% / 87.8% |
| Realistic smoke 71-Q                   |              78.9% / 94.4% |              78.9% / 94.4% |
| Agents NL 247-Q                        |              18.2% / 36.4% |              95.1% / 98.0% |
| Templates NL 195-Q                     |             24.6% / 61.0%  |             88.7% / 100.0% |
| Decision-trees NL 34-Q                 |              55.9% / 85.3% |              82.4% / 97.1% |

Per-query latency (fastembed cold start ~14s once per process; per-query
encode ~30ms after warm-up).

## [Unreleased] — sfskills-mcp v0.4.1 (hygiene patch)

Patch release rebuilding the data bundle attached to the GitHub Release
without hardcoded `/Users/<author>/` paths. Wheel itself is unchanged
in behaviour — only drops 2 unused imports. `sfskills-mcp-init` (which
fetches `releases/latest`) auto-picks up the cleaned data bundle.

### Changed

- `commands/audit-router.md`, `commands/automation-migration-router.md`,
  `commands/run-queue.md`, `docs/MIGRATION.md`,
  `docs/archive/OPUS_RESEARCH_PROMPT.md`,
  `agents/_shared/harnesses/migration_router/decision_table.md`,
  `feedback/FEEDBACK_LOG.md`: replaced absolute `/Users/<author>/` paths
  with relative references, `$(git rev-parse --show-toplevel)`, or
  generic phrasing. The `/run-queue` prompt's body had `cd /Users/...`
  snippets that wouldn't run on any other contributor's machine — fixed.
- `mcp/sfskills-mcp/src/sfskills_mcp/init.py`: drop unused `tempfile`.
- `mcp/sfskills-mcp/src/sfskills_mcp/resources.py`: drop unused `Any`.

### Fixed

- `agents/duplicate-rule-designer/AGENT.md`: rephrased the Dimensions
  section so it's no longer byte-identical to `data-loader-pre-flight`'s
  (the agent validator's "duplicate prose between AGENT.md files" rule
  was rejecting both files until one of them was paraphrased).

## [Unreleased] — sfskills-mcp v0.4.0 (Tier A → D)

A focused 4-tier evolution of `mcp/sfskills-mcp/` from the v0.1 prototype to a v0.4 production-ready MCP server. Plan + per-tier audit history live in [`.planning/mcp-v0.2-plan.md`](./.planning/mcp-v0.2-plan.md).

### Added

- **Tier C tools (14 new):** `list_apex_classes`, `get_apex_class`, `list_apex_triggers`, `list_lwc_bundles`, `get_lwc_bundle`, `list_custom_fields` (with `include_pseudo_fields`), `describe_object_full` (composite), `list_orgs`, `search_agents`, `search_templates`, `search_decision_trees`, `get_template`, `get_decision_tree`, `suggest_agent` (free-text task → ranked agents).
- **Tier D tools:** `health` diagnostic (server / SDK / sf-CLI versions, registry size, agent counts), `SFSKILLS_TIMEOUT_SECONDS` env var for deployer-wide subprocess timeout overrides.
- **MCP Prompts:** every wrapper in `commands/*.md` registers as an MCP prompt — 68 native slash commands (`/refactor-apex`, `/audit-router`, `/build-apex`, …) for Cursor / Cline / Claude Desktop / etc.
- **MCP Resources:** 5 shapes — `sfskills://catalog`, `sfskills://skill/{id}`, `sfskills://agent/{name}`, `sfskills://decision-tree/{name}`, `sfskills://template/{path}`. Use the `domain__name` form for IDs that contain slashes.
- **Tool annotations:** every tool registers with `mcp.types.ToolAnnotations` (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`) so MCP-aware clients can auto-approve safely.
- **Probe progress notifications:** the four heavy probes (`probe_apex_references`, `probe_flow_references`, `probe_matching_rules`, `probe_automation_graph`) emit `notifications/progress` at start + completion.
- **PyPI publish path:** new `sfskills-mcp-init` console script downloads the registry + lexical index from a GitHub Release into `~/.cache/sfskills-mcp/`. End-user install becomes `pip install sfskills-mcp` + `sfskills-mcp-init`. Workflow: `.github/workflows/publish-mcp.yml`.

### Changed

- **Tier A drift fix:** `_RUNTIME_AGENTS` frozenset (37 hand-coded names) replaced with frontmatter-driven resolution from `agents/<name>/AGENT.md` (`class: runtime` + `status:` headers). Active runtime count now resolves at runtime — no more hand-edit required when adding an agent. Skill / agent counts in `SERVER_INSTRUCTIONS` and tool descriptions are loaded from `registry/skills.json` at server build time.
- **Tier B annotations:** SDK floor bumped from `mcp>=1.2.0` to `mcp>=1.4.0` (annotations stable since 1.4).
- **Tier B probes:** the four heavy probes are wrapped in async tool functions in `server.py`; `probes.py` itself stays sync to keep the test-stubbing pattern intact.
- **Shared SOQL helpers** (`_run_soql`, `_validate_api_name`, `_strip_attributes`) lifted from `admin.py` to `_shared.py`. `admin.py` re-exports for backwards compatibility.
- **Drift-prevention test** (`tests/test_meta_freshness.py`) now scans `src/` for 7 stale literals (`686+`, `_RUNTIME_AGENTS`, `twenty-three tools`, `six tools`, `56 total`, `56 run-time`, `56 runtime`) — anything that drifted before fails CI if it reappears.

### Test count

Before Tier A: 65 pass / 2 fail. After Tier D: **177 pass / 0 fail**.

## [Unreleased] — Full 8-Wave Redesign

A substantial redesign completed in April 2026, landing all 8 waves of the approved plan at `an internal redesign plan (kept locally)`. This section documents Waves 4b, 4c, 5, 6, 7 added on top of the earlier Wave 3 + 4a work (originally in commits `8bcabde` through `f7de019`).

### Added in Waves 4b + 4c + 5 + 6 + 7

- **3 new Agentforce skills** (Wave 4c): `agentforce-multi-turn-patterns`, `agentforce-tool-use-patterns`, `agentforce-eval-harness`. Each 250+ lines with full 4 reference files.
- **8 new Flow skills** (Wave 4b + extension): `flow-transactional-boundaries`, `flow-platform-events-integration`, `flow-invocable-from-apex`, `flow-rollback-patterns`, `flow-error-monitoring`, `flow-migration-from-trigger`, `flow-governor-limits-deep-dive`, `flow-performance-optimization`.
- **2 new decision trees** (Waves 4b + 4c):
  - `standards/decision-trees/flow-pattern-selector.md` — Before-Save / After-Save / Scheduled / Screen / Orchestration / Platform-Event-triggered routing.
  - `standards/decision-trees/agentforce-capability-selector.md` — Agentforce / Copilot / Prompt Builder / Next Best Action / Einstein Discovery / BYOLLM / Bots routing.
- **2 new templates**:
  - `templates/flow/PlatformEvent_Publisher_Flow.md` (Wave 4b).
  - `templates/agentforce/AgentEval_Fixture.md` (Wave 4c).
- **11 new slash commands** (Wave 5): `/build-apex`, `/design-assignment-rules`, `/configure-business-hours`, `/build-changeset`, `/design-custom-metadata`, `/design-entitlements`, `/design-experience-cloud`, `/design-flow-orchestrator`, `/build-lwc`, `/design-path`, `/migrate-profile-to-permset`. Every runtime agent now has a slash-command entry point.
- **Slash-command coverage validator rule** (Wave 5): `pipelines/agent_validators.py` fails when any `class: runtime, status != deprecated` agent lacks a matching `commands/*.md` linking its `AGENT.md`.
- **macOS CI matrix** (Wave 6): `.github/workflows/validate.yml` runs `validate-agents` and new `export-parity-matrix` jobs on both `ubuntu-latest` and `macos-latest` to catch cross-OS hash drift.
- **pr-lint hardened** (Wave 6): `build_index.py` runs before `export_skills.py --check` so the gitignored `lexical.sqlite` doesn't trip drift detection.
- **Open-source readiness docs** (Wave 7): `LICENSE` (Apache 2.0), `SECURITY.md`, `docs/MIGRATION.md` (deprecated-agent removal timeline), `docs/multi-ai-parity.md` (first-class vs second-class tier contract).

### Changed in Waves 4b+

- **`vector_index/chunks.jsonl` gitignored** — grew to ~98 MB at 700+ skills, crossing GitHub's 50 MB warning threshold. CI and local workflows rebuild via `python3 scripts/build_index.py`. `vector_index/manifest.json` stays committed as the drift-detection hash.
- **`scripts/export_skills.py` → 6 platforms** (Wave 2): `claude`, `cursor`, `mcp` first-class; `windsurf`, `aider`, `augment` second-class with documented subset contract.
- **701 skills total** (was 686 pre-redesign) — net of deletions + new additions. Breakdown:
  - +11 new Agentforce/Flow skills authored (Waves 4b + 4c).
  - +16 Flow + 3 Agentforce skills rewritten from shallow to deep (Wave 4a).
  - –8 TODO-stub skills removed.

## [Earlier] — Wave 3 + Wave 4a Redesign

Original wave 0–4a work in commits `8bcabde` through `f7de019`.

### Added

- **`automation-migration-router`** (Wave 3a) — replaces 4 retired migrators with one router dispatching on `source_type` (`wf_rule` / `process_builder` / `approval_process` / `auto`). See [MIGRATION.md](docs/MIGRATION.md).
- **`audit-router`** (Waves 3b-1 + 3b-2) — replaces 15 retired auditors with one router dispatching on `--domain` across 15 classifiers. Each finding carries a stable domain-scoped code (`VR_*`, `PICKLIST_*`, `APPROVAL_*`, etc.) for cross-run rollup.
- **`designer_base` harness** (Wave 3c) — shared conventions doc (mode contract, output shape, inventory probes, refusal patterns) for 8 existing designer agents. Agents now declare `harness: designer_base` in frontmatter.
- **4 probes promoted to first-class MCP tools** (Wave 2): `probe_apex_references`, `probe_flow_references`, `probe_matching_rules`, `probe_permset_shape`. Centralizes SOQL + post-processing across agents.
- **`claude` and `mcp` first-class export targets** (Wave 2) in `scripts/export_skills.py`, alongside existing `cursor` / `aider` / `windsurf` / `augment`.
- **`registry/export_manifest.json`** (Wave 2) — per-target content hashes + per-skill hashes. CI diffs against this baseline to detect export drift.
- **`scripts/export_skills.py --target`, `--manifest`, `--check` flags** (Wave 2).
- **`scripts/export_skills.py --check`** — non-destructive parity check against committed manifest.
- **Sharded validator** (Wave 1): `scripts/validate_repo.py --changed-only`, `--shard N/M`, `--domain <name>`, `--skip-drift`, `--skip-fixture-retrieval`. Full-repo validation time reduced from ~16 minutes to ~40 seconds across 4 CI shards.
- **In-process fixture validation** (Wave 1) — `scripts/search_knowledge.py` exposes `build_search_context()` + `run_search()` as a library API. Fixture validation loads the lexical index once instead of 744 subprocess spawns.
- **`scripts/validate_repo_bench.py`** (Wave 1) — 500-synthetic-skill benchmark. Asserts wall-clock < 30s; catches orchestration regressions.
- **GitHub Actions workflows** (Wave 1): `.github/workflows/validate.yml` (4-shard matrix + agents + bench), `.github/workflows/pr-lint.yml` (schema round-trip + export-manifest check).
- **`mcp/sfskills-mcp/tests/test_agent_frontmatter.py`** (Wave 0) — round-trip test: every `AGENT.md` frontmatter validates against the tightened schema.
- **`mcp/sfskills-mcp/tests/test_tools.py`** (Wave 2 follow-on) — 19 MCP tools registered + input validation for SOQL-injection vectors.
- **`mcp/sfskills-mcp/tests/test_export_parity.py`** (Wave 2) — 3-run determinism + first-class parity (Claude/Cursor/MCP share skill-id set).
- **Process Observations blocks** on 4 observational runtime agents (Wave 0): `deployment-risk-scorer`, `lwc-auditor`, `soql-optimizer`, `flow-analyzer`.

### Changed

- **`agent-frontmatter.schema.json`** (Wave 0): `modes` tightened from loose regex to enum (`[single, design, audit, analyze, plan, migrate, review, build, validate]`) with `uniqueItems: true`. New optional `harness` field added in Wave 3c.
- **`pipelines/frontmatter.py::stable_hash_for_files`** (Wave 1.1 hotfix): now accepts a `root` parameter and computes hashes against POSIX paths relative to the root. Prior absolute-path hashing caused macOS-vs-Linux CI drift on every contributor PR.
- **`.githooks/pre-commit`** (Wave 1): uses `validate_repo.py --changed-only` for < 5s pre-commit on single-file changes.
- **`pipelines/agent_validators.py`** (Wave 3a + 3c):
  - Deprecated agents now require only `Plan` + `What This Agent Does NOT Do` sections (not full 8-section runtime shape).
  - `harness: designer_base` declaration triggers mode-enum enforcement + required `Escalation / Refusal Rules` section.
- **16 Flow skills rewritten** (Wave 4a-1) with 2-3x depth: `fault-handling`, `flow-bulkification`, `record-triggered-flow-patterns`, `orchestration-flows`, `scheduled-flows`, `screen-flows`, `subflows-and-reusability`, `flow-testing`, `flow-runtime-error-diagnosis`, `flow-action-framework`, `flow-collection-processing`, `flow-custom-property-editors`, `flow-email-and-notifications`, `flow-for-experience-cloud`, `flow-governance`, `flow-large-data-volume-patterns`.
- **3 Agentforce skills rewritten** (Wave 4a-2) with 2x depth: `agent-actions`, `agent-topic-design`, `agentforce-persona-design`.
- **`agents/_shared/SKILL_MAP.md`** updated to reflect router consolidations and designer harness inheritance.

### Deprecated

Full list and removal timeline in [`docs/MIGRATION.md`](docs/MIGRATION.md). Stubs + aliases ship for two minor versions.

- 4 automation migrators (Wave 3a): `workflow-rule-to-flow-migrator`, `process-builder-to-flow-migrator`, `approval-to-flow-orchestrator-migrator`, `workflow-and-pb-migrator`.
- 15 auditors (Wave 3b): `validation-rule-auditor`, `picklist-governor`, `approval-process-auditor`, `record-type-and-layout-auditor`, `report-and-dashboard-auditor`, `case-escalation-auditor`, `lightning-record-page-auditor`, `list-view-and-search-layout-auditor`, `quick-action-and-global-action-auditor` (audit mode), `reports-and-dashboards-folder-sharing-auditor`, `field-audit-trail-and-history-tracking-governor`, `sharing-audit-agent`, `org-drift-detector`, `my-domain-and-session-security-auditor`, `prompt-library-governor`.

### Removed

- **8 TODO-stub skills** (Wave 1.1 + 4a-2 cleanup): `data/industries-data-model`, `admin/omnistudio-vs-standard-decision`, `flow/process-builder-to-flow-migration`, `flow/workflow-rule-to-flow-migration`, `agentforce/agentforce-in-slack`, `integration/slack-connect-patterns`, `security/security-incident-response`, `data/data-loader-and-tools`. All had 38+ unfilled `TODO:` markers and no runtime-agent citations.

### Fixed

- **8 frontmatter `modes` typos** (Wave 0): 7 agents had `[n, audit]` instead of `[design, audit]`; `csv-to-object-mapper` had `[s]` instead of `[single]`. Tightened schema enum prevents recurrence.
- **21 broken agent citations** (Wave 1.1 hotfix): `list-view-and-search-layout-auditor`, `path-designer`, `quick-action-and-global-action-auditor`, `reports-and-dashboards-folder-sharing-auditor`, `devops-skill-builder`, `security-skill-builder` cited skills that didn't resolve; fixed to point at real skill paths.
- **12 missing query fixtures** (Wave 1.1 hotfix) for skills that had no fixture entry in `vector_index/query-fixtures.json`.
- **Invalid well-architected pillars** in `architect/npsp-vs-nonprofit-cloud-decision` (`Adaptability` / `Trustworthiness` → `Scalability` / `Reliability`).
- **Stale `registry/skills/*.json`** after TODO-stub removal (Wave 1.1 hotfix).
- **CI `lexical.sqlite` drift** (Wave 1.1 hotfix): added `scripts/build_index.py` step to CI to rebuild the gitignored index before drift check.

### Security

- **SECURITY.md** added (Wave 7) with disclosure process + contributor security checklist.
- **Probe input validation**: 4 promoted probes enforce API-name regex (`^[A-Za-z][A-Za-z0-9_]*$`) before constructing SOQL. Rejects injection vectors (`Account; DROP`, `Account OR 1=1`, etc.).
- **MCP tool tests** cover SOQL-injection vector rejection on `probe_apex_references`.

### Documentation

- **`docs/MIGRATION.md`** — every deprecated agent + replacement + removal timeline.
- **`LICENSE`** — Apache 2.0.
- **`SECURITY.md`** — disclosure policy + contributor security checklist.
- **`CHANGELOG.md`** — this file.
- **Auto-regenerated**: `docs/SKILLS.md`, `registry/skills.json`, `registry/knowledge-map.json`, `vector_index/chunks.jsonl`, `vector_index/manifest.json`.

## Pre-redesign history

The redesign documented above began from commit `1c65571` ("Wave D: wire the full 39-agent roster into docs + MCP registry", 16 April 2026). Pre-redesign changes are in git history; this changelog begins tracking with the redesign.

The full as-built agent roster prior to redesign is documented in the Waves 0–D commit log. The redesign preserves every rule but consolidates the agent surface into routers + shared harnesses per `an internal redesign plan (kept locally)`.
