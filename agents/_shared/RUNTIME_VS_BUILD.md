# Runtime vs Build-time Agents

## Build-time agents (15)

These agents produce and maintain the skill library. End users of SfSkills do not invoke them directly. All fifteen carry `status: stable` in frontmatter; no graded run backs that status.

| Agent | Role |
|---|---|
| `orchestrator` | Runs the release loop from `RELEASES.yaml`: dispatches writers, merges and verifies one at a time, resumes from file + git |
| `backlog-intake` | Sizes one ask and slots it into a release in `RELEASES.yaml` |
| `task-mapper` | Maps Cloud × Role task universes into release-plan asks (`scripts/release_plan.py add`) |
| `content-researcher` | Writes a research brief of official sources for one skill topic |
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

Entry points: `/start-building`, `/add-to-backlog`, `/new-skill`, `/add-skill`.

---

## Run-time agents (70)

70 active run-time agents: 7 stable, 8 beta (the Tier 4 build-loop agents) and 55 experimental. Deprecated agents are counted separately below.

These agents use the skill library to do Salesforce work against a user's org or codebase. Every run-time agent follows [`AGENT_CONTRACT.md`](./AGENT_CONTRACT.md) — including the mandatory **Process Observations** section that analyzes the org itself while producing the deliverable — and cites every skill / template / decision-tree it consumed.

### Agents with some evidence — 15 (7 stable, 8 beta)

The seven `status: stable` agents below were each graded once, on one real input, in the 1.5.0 cycle, with mixed grades (two of them, `flow-builder` and `object-designer`, were graded partly wrong and have no recorded re-run). The eight Tier 4 build-loop agents are exercised by the five maintainer-run example builds under `examples/builds/`. `AGENT_CONTRACT.md` defines `experimental` as the status for an agent with no such evidence; the sections below keep the tier headings (tier sizes sum to 70) and split each tier into these rows and experimental rows.

#### Developer + architecture tier (28) — 3 stable

| Agent | Domain | Primary output | Slash command |
|---|---|---|---|
| `security-scanner` | Security | CRUD/FLS/sharing/secret findings report | `/scan-security` |
| `deployment-failure-triager` | DevOps | Evidence-grounded diagnosis of an existing deploy job or CLI JSON fixture | `/triage-deployment` |
| `access-path-explainer` | Security / Admin | Layered explanation of why a user can or cannot perform an operation | `/why-cant-user` |

#### Admin accelerators — Tier 1 (14) — 4 stable

| Agent | Domain | Primary output | Slash command |
|---|---|---|---|
| `field-impact-analyzer` | Admin / Data | Blast-radius report for a field | `/analyze-field-impact` |
| `object-designer` | Admin / Architecture | Setup-ready sObject design | `/design-object` |
| `permission-set-architect` | Admin / Security | PS / PSG / Muting design per persona | `/architect-perms` |
| `flow-builder` | Flow / Admin | Flow design from requirements + tree-based routing | `/build-flow` |

#### Orchestration — Tier 4 (8) — 8 beta

`status: beta`. These agents implement the requirement-to-build loop in [`standards/build-orchestration.md`](../../standards/build-orchestration.md): one agent per stage, one human gate between stages, builds tracked under `.sfskills/builds/<build-id>/`. None of them deploys or approves a gate — each stops and prints the next command for a human to run.

| Agent | Domain | Primary output | Slash command |
|---|---|---|---|
| `requirements-clarifier` | Requirements / Admin | Deduped question set + proposed defaults, written into `plan.json` and `CLARIFICATIONS.md` (gate G1) | `/clarify-requirements` |
| `build-planner` | Planning / Architecture | Scope, fit-gap entries, decisions, milestones and steps written into `plan.json` (`status: planned`, awaiting gate G2) | `/plan-build` |
| `plan-verifier` | Verification / QA | Per-step executability / grounding / testability verdicts in `plan.json.verification`; plan set `verified` or `plan-rejected` (gate G2) | `/verify-plan` |
| `build-step-runner` | Execution / DevOps | One step's artefacts + run envelope; step moved to `built` or `blocked` | `/run-build-step` |
| `step-tester` | Testing / DevOps | Machine-readable test result + human summary; step moved to `tested` or `failed` | `/test-build-step` |
| `build-doc-keeper` | Documentation / Admin | Re-rendered `PLAN.md`, decisions log, configuration-workbook rows, traceability rows; step moved to `documented` | `/keep-build-docs` |
| `milestone-verifier` | Verification / DevOps | Milestone acceptance report + manual-test checklist for gate G3 | `/verify-milestone` |
| `metadata-builder` | Admin / Metadata | Deploy-ready source-format metadata XML + `package.xml` fragment + deploy-order note for one declarative step, checked against the cited skills' own checkers | `/build-metadata` |

Composite commands that span the whole loop rather than one agent: `/run-build` (every step of one milestone) and `/build-from-requirements` (all five stages, gate by gate).

### Experimental — ungraded, slash commands still work (55)

`status: experimental`. These agents follow the contract and their slash commands and `get_agent(name)` still work, but nobody has graded their output end to end yet. Treat results as a draft to review, not a verdict. An agent moves up to `stable` when a graded run is committed as evidence.

#### Developer + architecture tier (28) — 25 experimental

| Agent | Domain | Primary output | Slash command |
|---|---|---|---|
| `apex-refactorer` | Apex | Refactored class + test class + PR-ready patch | `/refactor-apex` |
| `trigger-consolidator` | Apex | Consolidated TriggerHandler + migration plan | `/consolidate-triggers` |
| `test-class-generator` | Apex | Bulk-safe test class targeting ≥85% coverage | `/gen-tests` |
| `soql-optimizer` | Apex / Data | Ranked list of SOQL fixes with before/after | `/optimize-soql` |
| `flow-analyzer` | Flow | Flow-vs-Apex decision + bulkification findings | `/analyze-flow` |
| `bulk-migration-planner` | Integration / Data | Bulk API 2.0 / PE / Pub-Sub migration plan | `/plan-bulk-migration` |
| `lwc-builder` | LWC | Full LWC bundle (js/html/css/meta/tests) + optional Apex controller | `/build-lwc` |
| `lwc-auditor` | LWC | A11y + perf + security findings per bundle | `/audit-lwc` |
| `lwc-debugger` | LWC | Ranked hypotheses + diagnostic probes + proposed fix for a live LWC failure | `/debug-lwc` |
| `deployment-risk-scorer` | DevOps | Risk score + breaking-change list for a change set | `/score-deployment` |
| `apex-test-failure-triager` | Apex / DevOps | Evidence-grounded diagnosis of an existing Apex test run or CLI JSON fixture | `/triage-apex-tests` |
| `agentforce-builder` | Agentforce | Full action scaffold: Apex + topic + eval | `/build-agentforce-action` |
| `apex-builder` | Apex | Apex class(es) built from requirements + test class | `/build-apex` |
| `changeset-builder` | DevOps | Change set manifest + deployment checklist | `/build-changeset` |
| `flow-orchestrator-designer` | Flow | Flow Orchestrator design + stage / step map | `/design-flow-orchestrator` |
| `automation-migration-router` | Flow / Apex | Automation inventory → WFR/PB-to-Flow migration plan | `/automation-migration-router` |
| `change-impact-planner` | Admin / DevOps | Direct and transitive impact of a proposed metadata change | `/plan-metadata-change` |
| `automation-transaction-profiler` | Flow / Apex | Save-order automation inventory and recursion/DML risk | `/profile-automation` |
| `release-readiness-reviewer` | DevOps | Evidence-backed go/no-go for an explicit release scope | `/review-release-readiness` |
| `security-posture-reviewer` | Security | Scoped access/code/session/integration posture findings | `/review-security-posture` |
| `integration-incident-triager` | Integration | Incident classification from Named Credential and event evidence | `/triage-integration` |
| `data-migration-reconciler` | Data | Load reject/count reconciliation without writing records | `/reconcile-data-load` |
| `org-health-assessor-v2` | Architect | Trusted/Easy/Adaptable health roadmap from a snapshot | `/assess-org-health` |
| `agentforce-quality-engineer` | Agentforce | Agent topics/actions/tests/guardrails review | `/review-agentforce-agent` |
| `multi-org-drift-analyzer` | Architect / DevOps | Expected vs dangerous differences between two explicit snapshots | `/compare-orgs` |

#### Admin accelerators — Tier 1 (14) — 10 experimental

| Agent | Domain | Primary output | Slash command |
|---|---|---|---|
| `data-loader-pre-flight` | Data | Go/no-go checklist for a data load | `/preflight-load` |
| `duplicate-rule-designer` | Data / Admin | Matching + Duplicate Rules + post-load hygiene | `/design-duplicate-rule` |
| `assignment-and-auto-response-rules-designer` | Admin | Assignment rule + auto-response rule design | `/design-assignment-rules` |
| `business-hours-and-holidays-configurator` | Admin / Service | Business hours + holiday set configuration plan | `/configure-business-hours` |
| `config-workbook-author` | Admin | Configuration workbook (object / field / automation inventory) | `/author-config-workbook` |
| `custom-metadata-and-settings-designer` | Admin | CMDT / Custom Settings design + Apex usage patterns | `/design-custom-metadata` |
| `entitlement-and-milestone-designer` | Admin / Service | Entitlement process + milestone design | `/design-entitlements` |
| `experience-cloud-admin-designer` | Admin | Experience Cloud site design (member, guest, CMS) | `/design-experience-cloud` |
| `path-designer` | Admin | Path + guidance + key fields design per object / stage | `/design-path` |
| `process-flow-mapper` | Admin | Business process → Salesforce automation map | `/map-process-flow` |

#### Strategic — Tier 2 (9) — 9 experimental

| Agent | Domain | Primary output | Slash command |
|---|---|---|---|
| `data-model-reviewer` | Data / Architecture | Data-model domain review | `/review-data-model` |
| `integration-catalog-builder` | Integration / Security | Integration catalog + posture scorecard | `/catalog-integrations` |
| `csv-to-object-mapper` | Data | CSV → sObject mapping + VR collision report | `/map-csv-to-object` |
| `email-template-modernizer` | Admin | Template classification + migration plan | `/modernize-email-templates` |
| `audit-router` | Admin / Security | Routes to appropriate single-mode auditor or runs multi-mode audit | `/audit-router` |
| `fit-gap-analyzer` | Admin | Fit / gap analysis: requirements vs org configuration | `/run-fit-gap` |
| `story-drafter` | Admin | User stories with Given/When/Then acceptance criteria | `/draft-stories` |
| `salesforce-decision-facilitator` | Architect | Decision brief comparing viable options with hard gates, sensitivity and reversibility | `/decide-salesforce` |
| `salesforce-learning-guide` | Admin / Learning | Cited lesson with practice and knowledge checks for one Salesforce topic | `/learn-salesforce` |

#### Vertical + governance — Tier 3 (11) — 11 experimental

| Agent | Domain | Primary output | Slash command |
|---|---|---|---|
| `omni-channel-routing-designer` | Service | Queue + routing config + presence design | `/design-omni-channel` |
| `knowledge-article-taxonomy-agent` | Service / Experience | Taxonomy + lifecycle + channel-audience plan | `/design-knowledge-taxonomy` |
| `sales-stage-designer` | Sales | Stage ladder + forecast + VR gates + Path | `/design-sales-stages` |
| `lead-routing-rules-designer` | Sales / Marketing | Routing matrix + queues + SLAs | `/design-lead-routing` |
| `sandbox-strategy-designer` | DevOps | Environment ladder + scratch pools + refresh calendar | `/design-sandbox-strategy` |
| `release-train-planner` | DevOps | Package + branching + CI/CD + release calendar | `/plan-release-train` |
| `waf-assessor` | Architecture | Well-Architected scorecard + remediation backlog | `/assess-waf` |
| `agentforce-action-reviewer` | Agentforce | Per-action A–F scorecard + guardrails gap list | `/review-agentforce-action` |
| `profile-to-permset-migrator` | Admin / Security | Profile → Permission Set migration plan + PS / PSG design | `/migrate-profile-to-permset` |
| `user-access-diff` | Admin / Security | Side-by-side access comparison report between users | `/diff-users` |
| `omnistudio-designer` | OmniStudio / Industries | OmniScript + FlexCard + DataRaptor + Integration Procedure design or audit | `/design-omnistudio` |

<a id="deprecated-slash-command-redirects"></a>
### Deprecated (14)

These agents have `status: deprecated`; their AGENT.md files remain for reference and every one redirects to `audit-router`. Nine of their slash commands still exist in `commands/` and forward to the canonical form below; the other five commands were removed. The MCP tool `list_deprecated_redirects` returns the agent-to-replacement mapping.

| Agent | Deprecated slash command | Superseded by | Canonical form |
|---|---|---|---|
| `case-escalation-auditor` | `/audit-case-escalation` | `audit-router` | `/audit-router --domain=case_escalation` |
| `field-audit-trail-and-history-tracking-governor` | none (removed) | `audit-router` | `/audit-router --domain=field_audit_trail_history_tracking` |
| `lightning-record-page-auditor` | `/audit-record-page` | `audit-router` | `/audit-router --domain=lightning_record_page` |
| `list-view-and-search-layout-auditor` | none (removed) | `audit-router` | `/audit-router --domain=list_view_search_layout` |
| `my-domain-and-session-security-auditor` | none (removed) | `audit-router` | `/audit-router --domain=my_domain_session_security` |
| `org-drift-detector` | `/detect-drift` | `audit-router` | `/audit-router --domain=org_drift` |
| `picklist-governor` | `/govern-picklists` | `audit-router` | `/audit-router --domain=picklist` |
| `prompt-library-governor` | `/govern-prompt-library` | `audit-router` | `/audit-router --domain=prompt_library` |
| `quick-action-and-global-action-auditor` | none (removed) | `audit-router` | `/audit-router --domain=quick_action` |
| `record-type-and-layout-auditor` | `/audit-record-types` | `audit-router` | `/audit-router --domain=record_type_layout` |
| `report-and-dashboard-auditor` | `/audit-reports` | `audit-router` | `/audit-router --domain=report_dashboard` |
| `reports-and-dashboards-folder-sharing-auditor` | none (removed) | `audit-router` | `/audit-router --domain=reports_dashboards_folder_sharing` |
| `sharing-audit-agent` | `/audit-sharing` | `audit-router` | `/audit-router --domain=sharing` |
| `validation-rule-auditor` | `/audit-validation-rules` | `audit-router` | `/audit-router --domain=validation_rule` |

Entry points:
- **Slash command** — ask the AI to follow `commands/<command-name>.md`
- **Direct read** — point any AI at `agents/<agent-name>/AGENT.md`
- **MCP** — `get_agent(name)` on the SfSkills MCP server returns the AGENT.md body for the client's LLM to execute

Source-skill map for every agent (for authors): [`SKILL_MAP.md`](./SKILL_MAP.md).

---

## Why this split matters

A build-time agent writes INTO the repo. A run-time agent writes INTO the user's own Salesforce project (or returns a report they paste into a PR). They share the same AGENT.md contract and the same skill library, but their invocation, access scope, and review gates differ. See [`AGENT_CONTRACT.md`](./AGENT_CONTRACT.md).
