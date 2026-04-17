# Runtime vs Build-time Agents

## Build-time agents (12)

These agents produce and maintain the skill library. End users of SfSkills do not invoke them directly.

| Agent | Role |
|---|---|
| `orchestrator` | Reads `MASTER_QUEUE.md`, routes tasks, tracks status |
| `task-mapper` | Maps Cloud × Role task universes into queue rows |
| `content-researcher` | Grounds every claim in Tier 1–3 sources |
| `admin-skill-builder` | Builds Admin + BA skills |
| `dev-skill-builder` | Builds Apex / LWC / Flow / Integration / DevOps skills |
| `data-skill-builder` | Builds data modeling, migration, SOQL skills |
| `architect-skill-builder` | Builds solution-design + WAF-review skills |
| `code-reviewer` | Canon-gate review (templates, decision-trees, evals) |
| `validator` | Structural + quality gates before every commit |
| `currency-monitor` | Flags stale skills after each SF release |
| `org-assessor` | Audits a target org against the library (operator tool) |
| `release-planner` | Assembles release notes from skill deltas |

Entry points: `/run-queue`, `/new-skill`, `/request-skill`, scheduled task.

---

## Run-time agents (39)

These agents use the skill library to do real Salesforce work against a user's org or codebase. They are the primary value delivered to consumers of SfSkills. Every run-time agent follows [`AGENT_CONTRACT.md`](./AGENT_CONTRACT.md) — including the mandatory **Process Observations** section that analyzes the org itself while producing the deliverable — and cites every skill / template / decision-tree it consumed.

### Developer + architecture tier (11)

| Agent | Domain | Primary output | Slash command |
|---|---|---|---|
| `apex-refactorer` | Apex | Refactored class + test class + PR-ready patch | `/refactor-apex` |
| `trigger-consolidator` | Apex | Consolidated TriggerHandler + migration plan | `/consolidate-triggers` |
| `test-class-generator` | Apex | Bulk-safe test class targeting ≥85% coverage | `/gen-tests` |
| `soql-optimizer` | Apex / Data | Ranked list of SOQL fixes with before/after | `/optimize-soql` |
| `security-scanner` | Security | CRUD/FLS/sharing/secret findings report | `/scan-security` |
| `flow-analyzer` | Flow | Flow-vs-Apex decision + bulkification findings | `/analyze-flow` |
| `bulk-migration-planner` | Integration / Data | Bulk API 2.0 / PE / Pub-Sub migration plan | `/plan-bulk-migration` |
| `lwc-auditor` | LWC | A11y + perf + security findings per bundle | `/audit-lwc` |
| `deployment-risk-scorer` | DevOps | Risk score + breaking-change list for a change set | `/score-deployment` |
| `agentforce-builder` | Agentforce | Full action scaffold: Apex + topic + eval | `/build-agentforce-action` |
| `org-drift-detector` | Architect | Library ↔ org gap + bloat report | `/detect-drift` |

### Admin accelerators — Tier 1 (8)

| Agent | Domain | Primary output | Slash command |
|---|---|---|---|
| `field-impact-analyzer` | Admin / Data | Blast-radius report for a field | `/analyze-field-impact` |
| `object-designer` | Admin / Architecture | Setup-ready sObject design | `/design-object` |
| `permission-set-architect` | Admin / Security | PS / PSG / Muting design per persona | `/architect-perms` |
| `flow-builder` | Flow / Admin | Flow design from requirements + tree-based routing | `/build-flow` |
| `workflow-and-pb-migrator` | Automation | Migration plan: WFR / PB → Flow | `/migrate-workflow-pb` |
| `validation-rule-auditor` | Admin | VR audit (bypass, bulk safety, Flow coexistence) | `/audit-validation-rules` |
| `data-loader-pre-flight` | Data | Go/no-go checklist for a data load | `/preflight-load` |
| `duplicate-rule-designer` | Data / Admin | Matching + Duplicate Rules + post-load hygiene | `/design-duplicate-rule` |

### Strategic — Tier 2 (10)

| Agent | Domain | Primary output | Slash command |
|---|---|---|---|
| `sharing-audit-agent` | Security / Architecture | OWD + sharing + data-skew findings | `/audit-sharing` |
| `lightning-record-page-auditor` | Admin / UX | Record-page + Dynamic Forms scorecard | `/audit-record-page` |
| `approval-to-flow-orchestrator-migrator` | Automation | Approval → Orchestrator migration plan | `/migrate-approval-to-orchestrator` |
| `record-type-and-layout-auditor` | Admin | RT + layout + LRP mapping audit | `/audit-record-types` |
| `picklist-governor` | Admin | GVS adoption + drift + dependency audit | `/govern-picklists` |
| `data-model-reviewer` | Data / Architecture | Data-model domain review | `/review-data-model` |
| `integration-catalog-builder` | Integration / Security | Integration catalog + posture scorecard | `/catalog-integrations` |
| `report-and-dashboard-auditor` | Admin | Report + dashboard hygiene audit | `/audit-reports` |
| `csv-to-object-mapper` | Data | CSV → sObject mapping + VR collision report | `/map-csv-to-object` |
| `email-template-modernizer` | Admin | Template classification + migration plan | `/modernize-email-templates` |

### Vertical + governance — Tier 3 (10)

| Agent | Domain | Primary output | Slash command |
|---|---|---|---|
| `omni-channel-routing-designer` | Service | Queue + routing config + presence design | `/design-omni-channel` |
| `knowledge-article-taxonomy-agent` | Service / Experience | Taxonomy + lifecycle + channel-audience plan | `/design-knowledge-taxonomy` |
| `sales-stage-designer` | Sales | Stage ladder + forecast + VR gates + Path | `/design-sales-stages` |
| `lead-routing-rules-designer` | Sales / Marketing | Routing matrix + queues + SLAs | `/design-lead-routing` |
| `case-escalation-auditor` | Service | Assignment + escalation + milestone audit | `/audit-case-escalation` |
| `sandbox-strategy-designer` | DevOps | Environment ladder + scratch pools + refresh calendar | `/design-sandbox-strategy` |
| `release-train-planner` | DevOps | Package + branching + CI/CD + release calendar | `/plan-release-train` |
| `waf-assessor` | Architecture | Well-Architected scorecard + remediation backlog | `/assess-waf` |
| `agentforce-action-reviewer` | Agentforce | Per-action A–F scorecard + guardrails gap list | `/review-agentforce-action` |
| `prompt-library-governor` | Agentforce | Prompt template inventory + consolidation plan | `/govern-prompt-library` |

Entry points:
- **Slash command** — ask the AI to follow `commands/<command-name>.md`
- **Direct read** — point any AI at `agents/<agent-name>/AGENT.md`
- **MCP** — `get_agent(name)` on the SfSkills MCP server returns the AGENT.md body for the client's LLM to execute

Source-skill map for every agent (for authors): [`SKILL_MAP.md`](./SKILL_MAP.md).

---

## Why this split matters

A build-time agent writes INTO the repo. A run-time agent writes INTO the user's own Salesforce project (or returns a report they paste into a PR). They share the same AGENT.md contract and the same skill library, but their invocation, access scope, and review gates differ. See [`AGENT_CONTRACT.md`](./AGENT_CONTRACT.md).
