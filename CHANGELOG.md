# Changelog

All notable changes to SfSkills are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The project uses semantic versioning keyed to the Salesforce release cadence (minor bumps per Spring/Summer/Winter release).

## [Unreleased] — Wave 3 + Wave 4a Redesign

A substantial redesign completed in April 2026 (commits `8bcabde` through `f7de019`), landing in waves 0 through 4a-2 of the approved plan at `/Users/user/.claude/plans/keen-napping-wombat.md`.

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

The full as-built agent roster prior to redesign is documented in the Waves 0–D commit log. The redesign preserves every rule but consolidates the agent surface into routers + shared harnesses per `/Users/user/.claude/plans/keen-napping-wombat.md`.
