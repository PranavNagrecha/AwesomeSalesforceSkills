# Agent → Skill Map

This is the authoring reference for the run-time agent roster. Every skill id listed below has been verified to exist in `skills/<domain>/<slug>/SKILL.md` at the time of writing. When adding a new agent, cite only skills from this map (or verify a new citation before committing).

All 48 active run-time agents are documented in their own `AGENT.md`. This file maps every agent to the skills, templates, and decision trees it depends on.

## Harnesses (Wave 3)

Shared convention documents under `agents/_shared/harnesses/` that consolidate common patterns across related agents:

- **`migration_router`** (Wave 3a) — consolidates 4 automation migrators into `automation-migration-router`. See [harness README](./harnesses/migration_router/README.md).
- **`audit_harness`** (Wave 3b) — consolidates 15 single-mode auditors into `audit-router`. See [harness README](./harnesses/audit_harness/README.md).
- **`designer_base`** (Wave 3c) — shared conventions for 9 designer agents (not a consolidation; designers keep their public identity). See [harness README](./harnesses/designer_base/README.md). Inheriting agents declare `harness: designer_base` in their frontmatter:
  - `object-designer`, `permission-set-architect`, `flow-builder`, `omni-channel-routing-designer`, `sales-stage-designer`, `lead-routing-rules-designer`, `duplicate-rule-designer`, `sandbox-strategy-designer`, `omnistudio-designer` (Wave H).

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
- `flow/flow-testing`
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
- `devops/isv-license-management-and-trialforce` — ISV release-cycle items: LMA registration, Trialforce template re-approval, Feature Parameter rollout
- `admin/managed-package-installation-and-upgrade` — subscriber-side install / upgrade runbook for AppExchange packages; sequence sandbox-first windows in the train

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
- `integration/api-versioning-strategy`, `integration/mutual-tls-callouts`
- `integration/connect-rest-api-patterns`, `integration/private-connect-setup`
- `integration/salesforce-data-pipeline-etl`, `integration/api-governance-and-rate-limits`
- `integration/webhook-signature-verification` → (no runtime agent — uncited as of 2026-08-01) — inbound webhook HMAC/signature validation
- `integration/data-cloud-zero-copy-federation` — Lakehouse Federation auth surface (Snowflake/Databricks/BigQuery/Redshift) and rotation hazards

### LWC (6 new)
`lightning-record-page-auditor` additionally cites:
- `lwc/drag-and-drop`, `lwc/file-upload-patterns`, `lwc/virtualized-lists`
- `lwc/lwc-state-management`, `lwc/lwc-error-boundaries`, `lwc/lwc-internationalization`

### Flow (6 new)
`flow-builder`, `flow-analyzer` and `flow-orchestrator-designer` additionally cite (per affinity — ownership of four of these moved from `flow-builder` to `flow-analyzer` on 2026-08-01):
- `flow/flow-interview-debugging` → `flow-builder` — paused / errored interview inspection
- `flow/flow-http-callout-action` → `flow-builder`, `flow-analyzer` — Flow HTTP Callout and External Service invocation
- `flow/flow-dynamic-choices` → `flow-analyzer` — record-backed and picklist-backed choice sets in screen flows
- `flow/flow-reactive-screen-components` → `flow-analyzer` — screen-component reactivity and cross-field dependencies
- `flow/flow-data-tables` → `flow-analyzer` — the Data Table screen component and its selection model
- `flow/flow-and-platform-events` → `flow-analyzer`, `flow-orchestrator-designer` — publishing to and subscribing from Platform Events in Flow

### Flow (5 Wave E additions — 2026-04)
`flow-builder` and `automation-migration-router` additionally cite:
- `flow/flow-decision-element-patterns` — default outcome, null-safe branching, ordering
- `flow/flow-get-records-optimization` — indexed filters, loop lift, field trim
- `flow/flow-record-save-order-interaction` — before-save vs after-save placement + recursion
- `flow/flow-versioning-strategy` — activation policy, paused-interview pinning, rollback-by-activate-prior (migration router Phase 4)
- `flow/flow-apex-defined-types` → `flow-analyzer` — structured Flow variables for HTTP callout / External Service / invocable payloads (dropped by `flow-builder` 2026-08-01; the `automation-migration-router` half of this block's intro line was already inaccurate before that date and is left for a separate pass)

### OmniStudio (5 new)
Now owned by `omnistudio-designer` (see Wave H below), which cites all five along with the rest of the domain:
- `omnistudio/omnistudio-lwc-omniscript-migration`, `omnistudio/omnistudio-asynchronous-data-operations`
- `omnistudio/omnistudio-cache-strategies`, `omnistudio/omnistudio-multi-language`, `omnistudio/omnistudio-field-mapping-governance`

### Wave F (2026-05) — 20 new skills

New skills landed 2026-05 and are wired into the agents shown below.

#### Apex (4 new)
`code-reviewer`, `deployment-risk-scorer`, `integration-catalog-builder`, `email-template-modernizer` additionally cite:
- `apex/apex-schema-describe` → `code-reviewer`, `deployment-risk-scorer` — Schema describe API perf, FLS, picklist enumeration
- `apex/apex-enum-patterns` → `code-reviewer` — enum dispatch, valueOf safety, ordinals
- `apex/apex-jwt-bearer-flow` → `integration-catalog-builder` — JWT bearer for server-to-server auth
- `apex/apex-outbound-email-patterns` → `email-template-modernizer` — Messaging.SingleEmailMessage, OWA, replies, templates

#### LWC (7 new)
`lwc-builder`, `lwc-auditor` additionally cite:
- `lwc/lwc-lightning-record-forms` → `lwc-builder`, `lwc-auditor` — record-form / -edit-form / -view-form
- `lwc/lwc-custom-lookup` → (no runtime agent — uncited as of 2026-08-01) — typeahead lookup component
- `lwc/lwc-datatable-advanced` → (no runtime agent — uncited as of 2026-08-01) — inline edit, custom cell types, sorting
- `lwc/lwc-css-and-styling` → `lwc-builder`, `lwc-auditor` — SLDS hooks, --slds-c-* tokens, shadow DOM, ::part()
- `lwc/lwc-drag-and-drop` → (no runtime agent — uncited as of 2026-08-01) — HTML5 drag and drop in LWC
- `lwc/tableau-embedding-in-lightning` → (no runtime agent — uncited as of 2026-08-01) — Tableau dashboards in Lightning, JWT SSO
- `lwc/lwc-pubsub-patterns` → (no runtime agent — uncited as of 2026-08-01) — Lightning Message Service, pubsub utility

#### Data (4 new)
`data-model-reviewer`, `sandbox-strategy-designer` additionally cite:
- `data/salesforce-backup-and-restore` → `data-model-reviewer`, `sandbox-strategy-designer` — backup strategy, RPO/RTO
- `data/data-virtualization-patterns` → (no runtime agent — uncited as of 2026-08-01) — Salesforce Connect, External Objects, OData
- `data/currency-management-patterns` → (no runtime agent — uncited as of 2026-08-01) — multi-currency, dated exchange rates
- `data/salesforce-files-architecture` → (no runtime agent — uncited as of 2026-08-01) — ContentVersion, ContentDocument, ContentDocumentLink

#### Security (2 new)
`security-scanner`, `audit-router` additionally cite:
- `security/sso-saml-troubleshooting` → `audit-router` (`my_domain_session_security` classifier) — SAML response inspection
- `security/guest-user-security-audit` → `security-scanner`, `audit-router` (`sharing` classifier) — Experience Cloud guest user 2021 changes

#### Architect / Admin / Integration (3 new)
- `architect/revenue-cloud-architecture` → `waf-assessor`, `fit-gap-analyzer` — Revenue Cloud (CPQ/Billing successor) architecture
- `admin/report-type-strategy` → `audit-router` (`report_dashboard` classifier) — custom report types, with/without joins
- `integration/sustainability-reporting` → (no runtime agent — uncited as of 2026-08-01) — Net Zero Cloud / sustainability data integration

### Wave G (2026-07-08) — SOQL/SOSL Reference + Flow onboarding (15 new skills)

Onboarded from the official *SOQL and SOSL Reference* and three Flow articles (PR #7). Wired into the agents shown; existing agents can cite them without authoring changes.

#### Apex — SOQL (9 new)
`soql-optimizer`, `security-scanner` additionally cite:
- `apex/soql-outer-join-null-semantics` → `soql-optimizer` — `= null`/`!= null` in WHERE, outer-join null-vs-FALSE semantics
- `apex/soql-object-limits-and-restrictions` → `soql-optimizer` — ContentDocumentLink filter requirement, 100k-row non-filter cap
- `apex/soql-string-escaping-and-reserved-characters` → `security-scanner`, `soql-optimizer` — quoted-string escapes + reserved chars, injection-safe binding
- `apex/soql-format-function-localization` → `soql-optimizer` — `FORMAT()` locale-aware currency/date/number
- `apex/soql-using-scope-clause` → `soql-optimizer` — `USING SCOPE` (mine/everything/team/scoping rules)
- `apex/soql-for-view-and-for-reference` → `soql-optimizer` — `FOR VIEW` / `FOR REFERENCE` recent-items tracking
- `apex/soql-multiselect-picklist-queries` → `soql-optimizer` — `INCLUDES`/`EXCLUDES` multi-select filtering
- `apex/soql-aggregate-field-type-support` → `soql-optimizer` — which field types support `SUM`/`AVG`/`MIN`/`MAX`
- `apex/soql-date-functions` → `soql-optimizer` — `CALENDAR_*`/`DAY_ONLY`/fiscal date grouping + the GROUP-BY-repeat rule

#### Data — SOSL (3 new)
No runtime agent currently cites these — `data-model-reviewer`'s citations were removed 2026-08-01:
- `data/sosl-with-clauses` → (no runtime agent — uncited as of 2026-08-01) — the SOSL `WITH` clause family (NETWORK/SNIPPET/HIGHLIGHT/METADATA/PricebookId/DivisionFilter/SPELL_CORRECTION/DATA CATEGORY)
- `data/sosl-search-result-limits` → (no runtime agent — uncited as of 2026-08-01) — SOSL result-count limits and `RETURNING` shaping
- `data/sosl-external-object-search-limits` → (no runtime agent — uncited as of 2026-08-01) — external-object SOSL search limits

#### Flow (3 new)
`flow-analyzer` additionally cites:
- `flow/screen-flow-radio-button-group` → (no runtime agent — uncited as of 2026-08-01) — Summer '26 compact single-select Radio Button Group component
- `flow/screen-flow-choice-component-selection` → (no runtime agent — uncited as of 2026-08-01) — choosing among Radio/Picklist/Dependent/Checkbox/Visual Picker/Choice Lookup
- `flow/flow-open-a-page-action` → `flow-analyzer` — Summer '26 Open a Page post-flow navigation/redirect action

---

## Wave H (2026-07-31) — OmniStudio runtime agent

Before this wave, `skills/omnistudio/` was the only domain with zero agent coverage: 34 of 34 skills were cited by no agent, so the domain was unreachable through the runtime layer. `omnistudio-designer` closes that hole and becomes the domain's front door.

### `omnistudio-designer`

Runtime, `harness: designer_base`, `modes: [design, audit]`, `multi_dimensional: true`, slash command `/design-omnistudio`. Do not confuse it with `omni-channel-routing-designer` — Omni-Channel is service work routing, a different product.

UI layer:
- `omnistudio/omniscript-design-patterns`, `omnistudio/omniscript-session-state`, `omnistudio/omniscript-versioning`
- `omnistudio/flexcard-design-patterns`, `omnistudio/flexcard-container-composition`, `omnistudio/flexcard-state-management`
- `omnistudio/omnistudio-lwc-integration`, `omnistudio/omnistudio-custom-lwc-elements`
- `admin/omniscript-flow-design-requirements`, `admin/flexcard-requirements`

Data + orchestration layer:
- `omnistudio/dataraptor-patterns`, `omnistudio/dataraptor-load-and-extract`, `omnistudio/dataraptor-transform-optimization`
- `omnistudio/omnistudio-field-mapping-governance`
- `omnistudio/integration-procedures`, `omnistudio/integration-procedure-cacheable-patterns`, `omnistudio/omnistudio-remote-actions`
- `omnistudio/omnistudio-asynchronous-data-operations`

Rules, calculation, documents, and Industries surfaces:
- `omnistudio/business-rules-engine`, `omnistudio/calculation-procedures`, `omnistudio/calculation-procedure-design`
- `omnistudio/document-generation-omnistudio`, `omnistudio/omnistudio-multi-language`
- `omnistudio/industries-api-extensions`, `omnistudio/industries-cpq-vs-salesforce-cpq`

Reliability, security, performance:
- `omnistudio/omnistudio-error-handling-patterns`, `omnistudio/omnistudio-debugging`, `omnistudio/omnistudio-testing-patterns`
- `omnistudio/omnistudio-security`
- `omnistudio/omnistudio-performance`, `omnistudio/omnistudio-cache-strategies`, `architect/omnistudio-scalability-patterns`

Runtime flavour, deployment, and tool boundary:
- `omnistudio/omnistudio-vs-flow-decision`, `architect/omnistudio-vs-standard-decision`, `architect/omnistudio-vs-standard-architecture`
- `omnistudio/vlocity-to-native-omnistudio-migration`, `omnistudio/omnistudio-lwc-omniscript-migration`
- `omnistudio/omnistudio-deployment-datapacks`, `omnistudio/omnistudio-ci-cd-patterns`
- `data/omnistudio-metadata-management`, `data/omnistudio-datapack-migration`
- `admin/omnistudio-admin-configuration`

Wave 10 contract support:
- `admin/agent-output-formats`, `admin/salesforce-object-queryability`

Decision trees:
- `standards/decision-trees/performance-tuning.md` — Q16 (OmniStudio runtime) is the only OmniStudio branch in the tree layer; cite it for every latency recommendation.
- `standards/decision-trees/automation-selection.md` — cited for route-away only. This tree has no OmniStudio branch; the agent says so in plain text rather than inventing one.

Templates: none. There is no `templates/omnistudio/` directory yet — a real gap, tracked as follow-up work.

---

## MCP tools available to these agents

Existing: `search_skill`, `get_skill`, `describe_org`, `list_custom_objects`, `list_flows_on_object`, `validate_against_org`, `list_agents`, `get_agent`.

Added in Wave 0: `list_validation_rules`, `list_permission_sets`, `describe_permission_set`, `list_record_types`, `list_named_credentials`, `list_approval_processes`, `tooling_query`.

---

## Authoring rule

Before committing a new AGENT.md, run the citation gate from `pipelines/` (or the ad-hoc script in WARNED COMMITS) to confirm every `skills/`, `templates/`, `standards/` reference resolves. Mismatches = hard fail.
