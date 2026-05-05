# Agent → Skill Map

This is the authoring reference for the run-time agent roster. Every skill id listed below has been verified to exist in `skills/<domain>/<slug>/SKILL.md` at the time of writing. When adding a new agent, cite only skills from this map (or verify a new citation before committing).

All 56 active run-time agents are documented in their own `AGENT.md`. This file maps every agent to the skills, templates, and decision trees it depends on.

## Harnesses (Wave 3)

Shared convention documents under `agents/_shared/harnesses/` that consolidate common patterns across related agents:

- **`migration_router`** (Wave 3a) — consolidates 4 automation migrators into `automation-migration-router`. See [harness README](./harnesses/migration_router/README.md).
- **`audit_harness`** (Wave 3b) — consolidates 15 single-mode auditors into `audit-router`. See [harness README](./harnesses/audit_harness/README.md).
- **`designer_base`** (Wave 3c) — shared conventions for 8 designer agents (not a consolidation; designers keep their public identity). See [harness README](./harnesses/designer_base/README.md). Inheriting agents declare `harness: designer_base` in their frontmatter:
  - `object-designer`, `permission-set-architect`, `flow-builder`, `omni-channel-routing-designer`, `sales-stage-designer`, `lead-routing-rules-designer`, `duplicate-rule-designer`, `sandbox-strategy-designer`.

---

## Wave A — Tier 1 (7 admin accelerators)

### `field-impact-analyzer`
- `admin/custom-field-creation`, `admin/formula-fields`, `admin/picklist-and-value-sets`
- `admin/lookup-filter-cross-object-patterns`
- `data/field-history-tracking`, `data/record-merge-implications`
- `architect/metadata-coverage-and-dependencies`, `devops/metadata-api-coverage-gaps`
- `templates/admin/naming-conventions.md`

### `object-designer`
- `admin/object-creation-and-design`, `admin/custom-field-creation`
- `admin/lookup-filter-cross-object-patterns`
- `data/data-model-design-patterns`, `data/external-id-strategy`, `data/person-accounts`
- `architect/solution-design-patterns`, `architect/large-data-volume-architecture`
- `admin/record-type-strategy-at-scale`, `admin/validation-rules`
- `standards/decision-trees/sharing-selection.md`
- `templates/admin/naming-conventions.md`

### `permission-set-architect`
- `admin/permission-set-architecture`, `admin/permission-sets-vs-profiles`
- `security/permission-set-groups-and-muting`
- `admin/custom-permissions`, `admin/delegated-administration`, `admin/user-access-policies`
- `admin/user-management`, `admin/integration-user-management`
- `devops/permission-set-deployment-ordering`
- `templates/admin/permission-set-patterns.md`

### `flow-builder`
- `flow/record-triggered-flow-patterns`, `flow/screen-flows`, `flow/scheduled-flows`, `flow/auto-launched-flow-patterns`
- `flow/flow-bulkification`, `flow/fault-handling`, `flow/subflows-and-reusability`
- `flow/orchestration-flows`, `flow/flow-testing`
- `standards/decision-trees/automation-selection.md`
- `templates/flow/FaultPath_Template.md`, `templates/flow/Subflow_Pattern.md`

### `automation-migration-router` (Wave 3a)

Single canonical migrator for legacy automation (Workflow Rules, Process
Builder, Approval Processes). Skills cited per `source_type` dispatch in
[`agents/_shared/harnesses/migration_router/decision_table.md`](./harnesses/migration_router/decision_table.md).

- `flow/record-triggered-flow-patterns`, `flow/fault-handling`, `flow/flow-bulkification`
- `flow/subflows-and-reusability`, `flow/auto-launched-flow-patterns`, `flow/scheduled-flows`
- `flow/orchestration-flows` (for `approval_process` dispatch)
- `admin/flow-for-admins`, `admin/approval-processes`
- `apex/trigger-and-flow-coexistence`
- `standards/decision-trees/automation-selection.md`
- `templates/flow/RecordTriggered_Skeleton.flow-meta.xml`, `templates/flow/FaultPath_Template.md`, `templates/flow/Subflow_Pattern.md`

### `audit-router` (Wave 3b-1)

Single canonical auditor for admin domains (validation rules, picklists,
record types, reports, etc.). Wave 3b-2 will add 10 more domains.
Per-domain skill citations live in each
[`classifiers/<domain>.md`](./harnesses/audit_harness/classifiers/)
under the classifier's `Mandatory Reads` section.

- `admin/validation-rules`, `admin/formula-fields`, `admin/picklist-field-integrity-issues`
- `admin/picklist-and-value-sets`, `admin/multi-language-and-translation`
- `admin/approval-processes`, `admin/queues-and-public-groups`
- `admin/record-type-strategy-at-scale`, `admin/record-types-and-page-layouts`
- `admin/reports-and-dashboards`, `admin/reports-and-dashboards-fundamentals`
- `admin/report-performance-tuning`, `admin/analytics-permission-and-sharing`
- `admin/data-export-service` (real-backup-vs-evidence-archive disambiguation)
- `flow/orchestration-flows`
- `data/data-quality-and-governance`
- `devops/metadata-diff-between-sandboxes` (org_drift classifier)
- `standards/decision-trees/automation-selection.md`
- `templates/admin/validation-rule-patterns.md`, `templates/admin/naming-conventions.md`

### `validation-rule-auditor` (deprecated — use `audit-router --domain validation_rule`)

### `data-loader-pre-flight`
- `admin/data-import-and-management`, `admin/duplicate-management`
- `data/bulk-api-and-large-data-loads`, `data/external-id-strategy`, `data/record-merge-implications`
- `data/field-history-tracking`, `data/lead-data-import-and-dedup`

### `duplicate-rule-designer`
- `admin/duplicate-management`
- `data/large-scale-deduplication`, `data/lead-data-import-and-dedup`
- `data/data-quality-and-governance`

---

## Wave B — Tier 2 (10 strategic)

### `sharing-audit-agent`
- `admin/sharing-and-visibility`, `admin/delegated-administration`
- `data/sharing-recalculation-performance`, `admin/data-skew-and-sharing-performance`
- `admin/queues-and-public-groups`, `admin/enterprise-territory-management`
- `admin/experience-cloud-guest-access`, `admin/experience-cloud-member-management`
- `standards/decision-trees/sharing-selection.md`

### `lightning-record-page-auditor`
- `admin/dynamic-forms-and-actions`, `admin/lightning-app-builder-advanced`
- `admin/lightning-page-performance-tuning`
- `admin/record-types-and-page-layouts`, `admin/path-and-guidance`
- `lwc/lwc-performance`

### `record-type-and-layout-auditor` (deprecated — use `audit-router --domain record_type_layout`)

### `picklist-governor` (deprecated — use `audit-router --domain picklist`)

### `data-model-reviewer`
- `data/data-model-design-patterns`, `data/external-id-strategy`, `data/roll-up-summary-alternatives`
- `admin/object-creation-and-design`, `admin/data-model-documentation`
- `architect/solution-design-patterns`, `architect/high-volume-sales-data-architecture`

### `integration-catalog-builder`
- `admin/integration-admin-connected-apps`, `admin/connected-apps-and-auth`
- `admin/remote-site-settings`, `admin/integration-user-management`
- `integration/named-credentials-setup`, `integration/oauth-flows-and-connected-apps`
- `integration/platform-event-schema-evolution`
- `security/connected-app-security-policies`, `security/certificate-and-key-management`
- `architect/integration-framework-design`, `architect/integration-security-architecture`

### `report-and-dashboard-auditor` (deprecated — use `audit-router --domain report_dashboard`)

### `csv-to-object-mapper`
- `admin/object-creation-and-design`, `admin/custom-field-creation`
- `admin/data-import-and-management`, `data/external-id-strategy`

### `email-template-modernizer`
- `admin/email-templates-and-alerts`

---

## Wave C — Tier 3 (10 vertical / governance)

### `omni-channel-routing-designer`
- `admin/omni-channel-routing-setup`, `admin/case-management-setup`, `admin/messaging-and-chat-setup`
- `architect/omni-channel-capacity-model`, `architect/multi-channel-service-architecture`

### `knowledge-article-taxonomy-agent`
- `admin/knowledge-base-administration`
- `architect/knowledge-taxonomy-design`, `architect/knowledge-vs-external-cms`
- `data/knowledge-article-import`

### `sales-stage-designer`
- `admin/opportunity-management`, `admin/pipeline-review-design`, `admin/sales-process-mapping`
- `admin/collaborative-forecasts`

### `lead-routing-rules-designer`
- `admin/lead-management-and-conversion`, `admin/assignment-rules`, `admin/queues-and-public-groups`
- `admin/enterprise-territory-management`

### `case-escalation-auditor`
- `admin/escalation-rules`, `admin/assignment-rules`, `admin/case-management-setup`
- `admin/entitlements-and-milestones`

### `sandbox-strategy-designer`
- `admin/sandbox-strategy`, `devops/environment-strategy`, `devops/sandbox-refresh-and-templates`
- `devops/scratch-org-management`, `devops/scratch-org-pools`
- `admin/data-export-service`, `architect/hyperforce-architecture` (sandbox-vs-prod migration cadence, refresh windows)

### `release-train-planner`
- `devops/release-management`, `devops/environment-strategy`, `devops/package-development-strategy`
- `devops/unlocked-package-development`, `devops/second-generation-managed-packages`
- `devops/git-branching-for-salesforce`, `devops/release-notes-automation`

### `waf-assessor`
- `architect/well-architected-review`, `architect/security-architecture-review`
- `architect/limits-and-scalability-planning`, `architect/nfr-definition-for-salesforce`
- `architect/ha-dr-architecture`, `architect/hyperforce-architecture`

### `agentforce-action-reviewer`
- `agentforce/agent-actions`, `agentforce/agent-topic-design`, `agentforce/agent-testing-and-evaluation`
- `agentforce/agent-action-input-slot-extraction`
- `agentforce/agentforce-guardrails`, `agentforce/agentforce-observability`
- `agentforce/einstein-trust-layer`, `agentforce/agentforce-persona-design`

### `prompt-library-governor`
- `agentforce/prompt-builder-templates`, `agentforce/einstein-trust-layer`
- `agentforce/agentforce-guardrails`, `agentforce/agentforce-observability`

---

## Wave D — 2026 skill pack additions (50 skills)

New skills landed in 2026-04 and are available for citation. Existing agents can reference them without authoring changes; the mapping below is the recommended affinity.

### Agentforce (8 new)
`agentforce-action-reviewer`, `prompt-library-governor` additionally cite:
- `agentforce/agent-action-error-handling`, `agentforce/prompt-injection-defense`, `agentforce/prompt-template-versioning`
- `agentforce/agent-action-unit-tests`, `agentforce/agent-rate-limit-strategy`, `agentforce/agent-security-review`
- `agentforce/agent-metric-dashboards`, `agentforce/agent-deployment-checklist`

### Security (10 new)
`sharing-audit-agent`, `permission-set-architect`, `waf-assessor`, `lightning-record-page-auditor`, `integration-catalog-builder` additionally cite (per affinity):
- `security/apex-managed-sharing-patterns`, `security/dynamic-sharing-recalculation` → sharing-audit-agent
- `security/privileged-access-management`, `security/session-high-assurance-policies`, `security/api-only-user-hardening` → permission-set-architect
- `security/shield-kms-byok-setup`, `security/salesforce-shield-deployment`, `security/customer-data-request-workflow` → waf-assessor
- `security/clickjack-and-frame-protection`, `security/csp-and-trusted-urls` → lightning-record-page-auditor

### DevOps (8 new)
`release-train-planner`, `sandbox-strategy-designer` additionally cite:
- `devops/feature-flag-custom-metadata`, `devops/pipeline-secrets-management`, `devops/sfdx-monorepo-patterns`
- `devops/packaging-dependency-graph`, `devops/sfdx-hardis-integration`, `devops/pr-policy-templates`, `devops/devops-center-advanced`
- `devops/scratch-org-snapshots` → sandbox-strategy-designer

### Integration (7 new)
`integration-catalog-builder` additionally cites:
- `integration/api-versioning-strategy`, `integration/mutual-tls-callouts`, `integration/webhook-signature-verification`
- `integration/connect-rest-api-patterns`, `integration/private-connect-setup`
- `integration/salesforce-data-pipeline-etl`, `integration/api-governance-and-rate-limits`
- `integration/data-cloud-zero-copy-federation` — Lakehouse Federation auth surface (Snowflake/Databricks/BigQuery/Redshift) and rotation hazards

### LWC (6 new)
`lightning-record-page-auditor` additionally cites:
- `lwc/drag-and-drop`, `lwc/file-upload-patterns`, `lwc/virtualized-lists`
- `lwc/lwc-state-management`, `lwc/lwc-error-boundaries`, `lwc/lwc-internationalization`

### Flow (6 new)
`flow-builder` additionally cites:
- `flow/flow-dynamic-choices`, `flow/flow-interview-debugging`, `flow/flow-and-platform-events`
- `flow/flow-reactive-screen-components`, `flow/flow-data-tables`, `flow/flow-http-callout-action`

### Flow (5 Wave E additions — 2026-04)
`flow-builder` and `automation-migration-router` additionally cite:
- `flow/flow-decision-element-patterns` — default outcome, null-safe branching, ordering
- `flow/flow-get-records-optimization` — indexed filters, loop lift, field trim
- `flow/flow-record-save-order-interaction` — before-save vs after-save placement + recursion
- `flow/flow-versioning-strategy` — activation policy, paused-interview pinning, rollback-by-activate-prior (migration router Phase 4)
- `flow/flow-apex-defined-types` — structured Flow variables for HTTP callout / External Service / invocable payloads

### OmniStudio (5 new)
No existing dedicated agent; skills are available for new agents and ad-hoc queries:
- `omnistudio/omnistudio-lwc-omniscript-migration`, `omnistudio/omnistudio-asynchronous-data-operations`
- `omnistudio/omnistudio-cache-strategies`, `omnistudio/omnistudio-multi-language`, `omnistudio/omnistudio-field-mapping-governance`

---

## MCP tools available to these agents

Existing: `search_skill`, `get_skill`, `describe_org`, `list_custom_objects`, `list_flows_on_object`, `validate_against_org`, `list_agents`, `get_agent`.

Added in Wave 0: `list_validation_rules`, `list_permission_sets`, `describe_permission_set`, `list_record_types`, `list_named_credentials`, `list_approval_processes`, `tooling_query`.

---

## Authoring rule

Before committing a new AGENT.md, run the citation gate from `pipelines/` (or the ad-hoc script in WARNED COMMITS) to confirm every `skills/`, `templates/`, `standards/` reference resolves. Mismatches = hard fail.
