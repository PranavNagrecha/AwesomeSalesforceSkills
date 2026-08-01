# Runtime vs Build-time Agents

## Build-time agents (14)

These agents produce and maintain the skill library. End users of SfSkills do not invoke them directly.

| Agent | Role |
|---|---|
| `orchestrator` | Reads `MASTER_QUEUE.md`, routes tasks, tracks status |
| `task-mapper` | Maps Cloud × Role task universes into queue rows |
| `content-researcher` | Grounds every claim in Tier 1–3 sources |
| `admin-skill-builder` | Builds Admin + BA skills |
| `dev-skill-builder` | Builds Apex / LWC / Flow / Integration / DevOps skills |
| `devops-skill-builder` | Builds DevOps / release-engineering skills |
| `data-skill-builder` | Builds data modeling, migration, SOQL skills |
| `architect-skill-builder` | Builds solution-design + WAF-review skills |
| `code-reviewer` | Canon-gate review (templates, decision-trees, evals) |
| `validator` | Structural + quality gates before every commit |
| `currency-monitor` | Flags stale skills after each SF release |
| `org-assessor` | Audits a target org against the library (operator tool) |
| `release-planner` | Assembles release notes from skill deltas |
| `security-skill-builder` | Builds Security skills |

Entry points: `/run-queue`, `/new-skill`, `/request-skill`, scheduled task.

---

## Run-time agents (48)

These agents use the skill library to do real Salesforce work against a user's org or codebase. They are the primary value delivered to consumers of SfSkills. Every run-time agent follows [`AGENT_CONTRACT.md`](./AGENT_CONTRACT.md) — including the mandatory **Process Observations** section that analyzes the org itself while producing the deliverable — and cites every skill / template / decision-tree it consumed.

### Developer + architecture tier (16)

| Agent | Domain | Primary output | Slash command |
|---|---|---|---|
| `apex-refactorer` | Apex | Refactored class + test class + PR-ready patch | `/refactor-apex` |
| `trigger-consolidator` | Apex | Consolidated TriggerHandler + migration plan | `/consolidate-triggers` |
| `test-class-generator` | Apex | Bulk-safe test class targeting ≥85% coverage | `/gen-tests` |
| `soql-optimizer` | Apex / Data | Ranked list of SOQL fixes with before/after | `/optimize-soql` |
| `security-scanner` | Security | CRUD/FLS/sharing/secret findings report | `/scan-security` |
| `flow-analyzer` | Flow | Flow-vs-Apex decision + bulkification findings | `/analyze-flow` |
| `bulk-migration-planner` | Integration / Data | Bulk API 2.0 / PE / Pub-Sub migration plan | `/plan-bulk-migration` |
| `lwc-builder` | LWC | Full LWC bundle (js/html/css/meta/tests) + optional Apex controller | `/build-lwc` |
| `lwc-auditor` | LWC | A11y + perf + security findings per bundle | `/audit-lwc` |
| `lwc-debugger` | LWC | Ranked hypotheses + diagnostic probes + proposed fix for a live LWC failure | `/debug-lwc` |
| `deployment-risk-scorer` | DevOps | Risk score + breaking-change list for a change set | `/score-deployment` |
| `agentforce-builder` | Agentforce | Full action scaffold: Apex + topic + eval | `/build-agentforce-action` || `apex-builder` | Apex | Apex class(es) built from requirements + test class | `/build-apex` |
| `changeset-builder` | DevOps | Change set manifest + deployment checklist | `/build-changeset` |
| `flow-orchestrator-designer` | Flow | Flow Orchestrator design + stage / step map | `/design-flow-orchestrator` |
| `automation-migration-router` | Flow / Apex | Automation inventory → WFR/PB-to-Flow migration plan | `/automation-migration-router` |

### Admin accelerators — Tier 1 (14)

| Agent | Domain | Primary output | Slash command |
|---|---|---|---|
| `field-impact-analyzer` | Admin / Data | Blast-radius report for a field | `/analyze-field-impact` |
| `object-designer` | Admin / Architecture | Setup-ready sObject design | `/design-object` |
| `permission-set-architect` | Admin / Security | PS / PSG / Muting design per persona | `/architect-perms` |
| `flow-builder` | Flow / Admin | Flow design from requirements + tree-based routing | `/build-flow` || `data-loader-pre-flight` | Data | Go/no-go checklist for a data load | `/preflight-load` |
| `duplicate-rule-designer` | Data / Admin | Matching + Duplicate Rules + post-load hygiene | `/design-duplicate-rule` |
| `assignment-and-auto-response-rules-designer` | Admin | Assignment rule + auto-response rule design | `/design-assignment-rules` |
| `business-hours-and-holidays-configurator` | Admin / Service | Business hours + holiday set configuration plan | `/configure-business-hours` |
| `config-workbook-author` | Admin | Configuration workbook (object / field / automation inventory) | `/author-config-workbook` |
| `custom-metadata-and-settings-designer` | Admin | CMDT / Custom Settings design + Apex usage patterns | `/design-custom-metadata` |
| `entitlement-and-milestone-designer` | Admin / Service | Entitlement process + milestone design | `/design-entitlements` |
| `experience-cloud-admin-designer` | Admin | Experience Cloud site design (member, guest, CMS) | `/design-experience-cloud` |
| `path-designer` | Admin | Path + guidance + key fields design per object / stage | `/design-path` |
| `process-flow-mapper` | Admin | Business process → Salesforce automation map | `/map-process-flow` |

### Strategic — Tier 2 (7)

| Agent | Domain | Primary output | Slash command |
|---|---|---|---|
| `data-model-reviewer` | Data / Architecture | Data-model domain review | `/review-data-model` |
| `integration-catalog-builder` | Integration / Security | Integration catalog + posture scorecard | `/catalog-integrations` |
| `csv-to-object-mapper` | Data | CSV → sObject mapping + VR collision report | `/map-csv-to-object` |
| `email-template-modernizer` | Admin | Template classification + migration plan | `/modernize-email-templates` |
| `audit-router` | Admin / Security | Routes to appropriate single-mode auditor or runs multi-mode audit | `/audit-router` |
| `fit-gap-analyzer` | Admin | Fit / gap analysis: requirements vs org configuration | `/run-fit-gap` |
| `story-drafter` | Admin | User stories with Given/When/Then acceptance criteria | `/draft-stories` |

### Vertical + governance — Tier 3 (11)

| Agent | Domain | Primary output | Slash command |
|---|---|---|---|
| `omni-channel-routing-designer` | Service | Queue + routing config + presence design | `/design-omni-channel` |
| `knowledge-article-taxonomy-agent` | Service / Experience | Taxonomy + lifecycle + channel-audience plan | `/design-knowledge-taxonomy` |
| `sales-stage-designer` | Sales | Stage ladder + forecast + VR gates + Path | `/design-sales-stages` |
| `lead-routing-rules-designer` | Sales / Marketing | Routing matrix + queues + SLAs | `/design-lead-routing` |
| `sandbox-strategy-designer` | DevOps | Environment ladder + scratch pools + refresh calendar | `/design-sandbox-strategy` |
| `release-train-planner` | DevOps | Package + branching + CI/CD + release calendar | `/plan-release-train` |
| `waf-assessor` | Architecture | Well-Architected scorecard + remediation backlog | `/assess-waf` |
| `agentforce-action-reviewer` | Agentforce | Per-action A–F scorecard + guardrails gap list | `/review-agentforce-action` || `profile-to-permset-migrator` | Admin / Security | Profile → Permission Set migration plan + PS / PSG design | `/migrate-profile-to-permset` |
| `user-access-diff` | Admin / Security | Side-by-side access comparison report between users | `/diff-users` |
| `omnistudio-designer` | OmniStudio / Industries | OmniScript + FlexCard + DataRaptor + Integration Procedure design or audit | `/design-omnistudio` |

### Deprecated (14)

These agents have `status: deprecated` — their AGENT.md files remain for reference, and their slash commands are forwarded to `audit-router`. The Wave-3b consolidation folded the single-mode auditors and governors into `audit-router`; nine of these were previously listed in the runtime tiers above and have now been moved here so the tier counts reflect active agents only.

| Agent | Deprecated slash command | Superseded by |
|---|---|---|
| `case-escalation-auditor` | `/audit-case-escalation` | `audit-router` |
| `field-audit-trail-and-history-tracking-governor` | `/govern-field-history` | `audit-router` |
| `lightning-record-page-auditor` | `/audit-record-page` | `audit-router` |
| `list-view-and-search-layout-auditor` | `/audit-list-views` | `audit-router` |
| `my-domain-and-session-security-auditor` | `/audit-identity-and-session` | `audit-router` |
| `org-drift-detector` | `/detect-drift` | `audit-router` |
| `picklist-governor` | `/govern-picklists` | `audit-router` |
| `prompt-library-governor` | `/govern-prompt-library` | `audit-router` |
| `quick-action-and-global-action-auditor` | `/audit-actions` | `audit-router` |
| `record-type-and-layout-auditor` | `/audit-record-types` | `audit-router` |
| `report-and-dashboard-auditor` | `/audit-reports` | `audit-router` |
| `reports-and-dashboards-folder-sharing-auditor` | `/audit-report-folder-sharing` | `audit-router` |
| `sharing-audit-agent` | `/audit-sharing` | `audit-router` |
| `validation-rule-auditor` | `/audit-validation-rules` | `audit-router` |

Entry points:
- **Slash command** — ask the AI to follow `commands/<command-name>.md`
- **Direct read** — point any AI at `agents/<agent-name>/AGENT.md`
- **MCP** — `get_agent(name)` on the SfSkills MCP server returns the AGENT.md body for the client's LLM to execute

Source-skill map for every agent (for authors): [`SKILL_MAP.md`](./SKILL_MAP.md).

---

## Why this split matters

A build-time agent writes INTO the repo. A run-time agent writes INTO the user's own Salesforce project (or returns a report they paste into a PR). They share the same AGENT.md contract and the same skill library, but their invocation, access scope, and review gates differ. See [`AGENT_CONTRACT.md`](./AGENT_CONTRACT.md).
