# MASTER_QUEUE.md — Universal Salesforce Skill Build Queue

<!--
PURPOSE:
  Single source of truth for the full Role × Domain × Cloud skill matrix.
  SKILLS_BACKLOG.md tracks the original 157 skills (current scope).
  This file drives the expanded vision: every SF role, every cloud, every task.

VISION:
  One public repo. Every Salesforce professional (Admin, BA, Dev, Data, Architect)
  drops it into Claude, Cursor, or any AI and gets role-appropriate, task-accurate
  Salesforce guidance grounded in official docs — not training data guesses.

AGENT INSTRUCTIONS (read before doing anything):
  1. Read CLAUDE.md and AGENT_RULES.md first. This file does not override them.
  2. Find the first row with status TODO in the queue below.
  3. Change status to IN_PROGRESS and record your agent name + ISO timestamp in the Notes column.
  4. python3 scripts/search_knowledge.py "<skill-name>" --domain <domain>
       → If has_coverage: true, the skill exists. Mark DUPLICATE and move to next.
       → If has_coverage: false, proceed.
  5. Read official sources for this domain from standards/official-salesforce-sources.md BEFORE writing anything.
  6. python3 scripts/new_skill.py <domain> <skill-name>
  7. Fill every TODO marker in every generated file with real, doc-grounded content.
       SKILL.md body must be 300+ words. Include "NOT for ..." in description.
       Triggers must be 3+ natural-language symptom phrases, 10+ chars each.
  8. python3 scripts/skill_sync.py --skill skills/<domain>/<skill-name>
       Fix every ERROR before continuing. Do not use --skip-validation.
  9. Add query fixture to vector_index/query-fixtures.json.
       Run python3 scripts/search_knowledge.py "<query>" and confirm skill appears in top 3.
  10. python3 scripts/validate_repo.py → must exit 0.
  11. Mark row DONE. Commit: skill package + registry/ + vector_index/ + docs/SKILLS.md.
  12. Move to the next TODO row.

RESEARCH TASKS (status = RESEARCH):
  These are not skill-creation tasks. They produce a list of skill rows to insert
  into this file before any skills can be built for that Cloud × Role cell.
  Steps for a RESEARCH task:
  1. Use web search to find the official Salesforce documentation and Trailhead trails
     for the specified Cloud and Role.
  2. Identify every distinct practitioner task that role performs in that cloud.
  3. Check each task against existing skills/ using search_knowledge.py.
  4. For each confirmed gap, add a TODO row to the appropriate section below.
  5. Mark the RESEARCH row DONE.

STATUS KEY:
  TODO       → Not started. Any agent can pick this up.
  IN_PROGRESS → Being built. Do not touch — another agent is working on it.
  DONE       → Complete. validate_repo.py passes. Committed.
  DUPLICATE  → Skill already exists. Skipped.
  BLOCKED    → Stopped. Read Notes before continuing.
  RESEARCH   → Research task. Produces TODO rows, not a skill.
-->

---

## Progress Summary

| Phase | Cloud | Total Cells | Skills Planned | Skills Done | TODO |
|-------|-------|-------------|----------------|-------------|------|
| 1 | Core Platform | 5 roles | 34 | 10 | 24 |
| 2 | Sales Cloud | 5 roles | RESEARCH | 0 | — |
| 3 | Service Cloud | 5 roles | RESEARCH | 0 | — |
| 4 | Experience Cloud | 5 roles | RESEARCH | 0 | — |
| 5 | Marketing Cloud / MCAE | 5 roles | RESEARCH | 0 | — |
| 6 | Revenue Cloud (CPQ) | 5 roles | RESEARCH | 0 | — |
| 7 | Field Service (FSL) | 5 roles | RESEARCH | 0 | — |
| 8 | Health Cloud | 5 roles | RESEARCH | 0 | — |
| 9 | Financial Services Cloud | 5 roles | RESEARCH | 0 | — |
| 10 | Nonprofit Cloud (NPSP) | 5 roles | RESEARCH | 0 | — |
| 11 | Commerce Cloud | 5 roles | RESEARCH | 0 | — |
| 12 | Agentforce / Einstein AI | 5 roles | RESEARCH | 0 | — |
| 13 | OmniStudio / Industries | 5 roles | RESEARCH | 0 | — |
| 14 | CRM Analytics / Tableau | 5 roles | RESEARCH | 0 | — |
| 15 | Integration (MuleSoft/APIs) | 5 roles | RESEARCH | 0 | — |
| 16 | DevOps (SFDX/Pipelines) | 5 roles | RESEARCH | 0 | — |

---

## Execution Order

Build phases sequentially. Within each phase, build roles in this order:
**Admin → BA → Dev → Data → Architect**

Reason: Admin defines the data model and configuration that Dev and Architect skills
reference. BA skills assume Admin config exists. Data skills assume Dev patterns exist.
Architect skills synthesize all of the above.

---

## Phase 1 — Core Platform (Foundation)

Core Platform skills apply across all clouds. Build these first.
Every skill here should work regardless of which Salesforce cloud the org has licensed.

### Core Platform × Admin Role

> Domain folder: `admin` | Official sources: Salesforce Help, Admin Trailhead, Admin Guide

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| DONE | custom-field-creation | How to create any field type on any object: type selection decision tree, naming, FLS, page layout placement, deployment. NOT for formula field logic (use formula-fields) or object design decisions. | Claude Sonnet 4.6 · 2026-04-03T00:00:00Z |
| DONE | object-creation-and-design | How to create a custom object: naming, API name, features (activities, chatter, history tracking), sharing model selection, tab creation. NOT for field design (use custom-field-creation). | Claude Sonnet 4.6 · 2026-04-03T00:00:00Z |
| DONE | picklist-and-value-sets | Global value sets vs object-local picklists, controlling and dependent fields, picklist value management, replacing picklist values in data. NOT for formula fields that reference picklists. | Claude Sonnet 4.6 · 2026-04-03T00:00:00Z |
| DONE | user-management | Creating, deactivating, and freezing users; assigning licenses, roles, and profiles; login hours and IP restrictions; delegated administration. NOT for permission sets (use permission-set-architecture). | Claude Sonnet 4.6 · 2026-04-03T00:00:00Z |
| DONE | org-setup-and-configuration | MFA enforcement, session settings, login policies, password policies, trusted IP ranges, My Domain, CSP settings. NOT for user-level security (use user-management or permission-sets-vs-profiles). | Reset — agent built but push failed |
| DONE | app-and-tab-configuration | Creating Lightning apps, configuring navigation items, adding tabs for custom objects, utility bar, app visibility by profile. NOT for Experience Cloud apps. | |
| DONE | global-actions-and-quick-actions | Object-specific quick actions vs global actions, action layouts, pre-filling fields, adding actions to page layouts and mobile. NOT for Flow-triggered actions. | |
| DONE | assignment-rules | Lead assignment rules, case assignment rules, rule entry criteria, queue assignment, round-robin patterns using Apex. NOT for approval process routing (use approval-processes). | |
| DONE | escalation-rules | Case escalation rules, time-based escalation, business hours configuration, escalation actions. NOT for assignment rules or approval processes. | |
| DONE | data-skew-and-sharing-performance | Recognizing data skew (account skew, ownership skew), impact on sharing recalculation, mitigation strategies. NOT for sharing model design (use sharing-and-visibility). | Claude Sonnet 4.6 · 2026-04-03T00:00:00Z |

### Core Platform × BA Role

> Domain folder: `admin` | BA skills live in admin domain — they produce requirements and process artifacts, not code.

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | requirements-gathering-for-sf | Eliciting and documenting Salesforce requirements: user story format for SF features, As-Is vs To-Be process mapping, gap analysis, stakeholder interview questions. NOT for technical design. | |
| TODO | process-mapping-and-automation-selection | Mapping business processes to Salesforce automation options: Flow vs Apex vs Workflow Email Alert vs Process Builder (legacy). Produces a recommendation, not an implementation. NOT for building the automation (use flow/* or apex/* skills). | |
| TODO | data-model-documentation | Documenting the Salesforce data model: ER diagrams, object relationship maps, field inventory, field usage analysis. NOT for designing the model (use object-creation-and-design or architect skills). | |
| TODO | uat-and-acceptance-criteria | Writing acceptance criteria for Salesforce features, UAT test script format, defect classification for SF, regression test planning. NOT for automated testing (use flow-testing or apex test-class-standards). | |
| TODO | change-management-and-training | User adoption planning, Salesforce training material structure, release communication templates, change impact assessment. NOT for org deployment (use change-management-and-deployment). | |

### Core Platform × Dev Role

> Dev skills for topics not already covered by existing apex/ lwc/ flow/ skills.

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | soql-fundamentals | Writing SOQL: SELECT syntax, WHERE filters, ORDER BY, LIMIT, OFFSET, relationship queries (child-to-parent, parent-to-child), aggregate functions, date literals. NOT for security enforcement (use soql-security) or query optimization (use apex-cpu-and-heap-optimization). | |
| TODO | sf-cli-and-sfdx-essentials | sf CLI auth, project setup, scratch org creation, source push/pull, deploy/retrieve commands, manifest (package.xml) basics. NOT for full CI/CD pipelines (use devops skills). | |
| TODO | metadata-api-and-package-xml | Metadata API concepts, package.xml structure, what can and cannot be retrieved, deployment order dependencies, destructiveChanges.xml. NOT for SFDX source format details (use sf-cli-and-sfdx-essentials). | |
| TODO | debug-logs-and-developer-console | Setting up debug logs, reading log levels, Developer Console query editor, anonymous Apex execution, Apex replay debugger basics. NOT for production incident debugging strategy (use debug-and-logging). | |
| TODO | named-credentials-and-callouts | Setting up Named Credentials for external callouts, using them in Apex HTTP requests, auth protocols supported. NOT for OAuth flows as a standalone pattern (use oauth-flows-and-connected-apps). | |

### Core Platform × Data Role

> Domain folder: `data`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | data-model-design-patterns | Choosing object relationships (Lookup vs MD vs Junction), field type selection for data integrity, indexing strategy for query performance, data model anti-patterns. NOT for object creation steps (use object-creation-and-design). | |
| TODO | data-migration-planning | ETL approach selection, migration sequence (parent before child), external ID strategy, validation rule bypass during migration, rollback planning. NOT for Data Loader mechanics (use data-import-and-management). | |
| TODO | data-quality-and-governance | Data quality rules in Salesforce, validation rules as data gates, duplicate management strategy, field history as audit trail, GDPR/data retention considerations. NOT for Duplicate Rules configuration (use duplicate-management). | |
| TODO | bulk-api-and-large-data-loads | Bulk API 2.0 vs REST API for large volumes, batch size guidance, serial vs parallel mode, monitoring bulk jobs, failed record handling. NOT for Data Loader UI steps (use data-import-and-management). | |
| TODO | data-archival-strategies | Big Object usage, archival to external storage, field history truncation, record count limits and their impact, soft-delete and recycle bin behavior. NOT for data migration (use data-migration-planning). | |
| TODO | soql-query-optimization | Selective queries, index usage, query plan tool, avoiding non-selective filters, skinny tables, field sets for dynamic queries. NOT for governor limits in Apex (use apex-cpu-and-heap-optimization). | |
| TODO | field-history-tracking | Enabling field history, 18-month retention limit, History related list behavior, querying history objects (AccountHistory, etc.), limitations and alternatives. NOT for Event Monitoring (use security skills). | |

### Core Platform × Architect Role

> Domain folder: `admin` (architecture guidance for platform-wide concerns)

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | solution-design-patterns | When to use declarative vs programmatic solutions, layered automation model, design tradeoffs (Flow vs Apex vs LWC), future-proofing configuration decisions. NOT for individual feature design (use role-specific skills). | |
| TODO | limits-and-scalability-planning | Governor limits that matter at scale (SOQL, DML, CPU, heap), org-wide limits (fields per object, custom objects, custom settings), planning for data volume growth. NOT for code-level optimization (use apex-cpu-and-heap-optimization). | |
| TODO | multi-org-strategy | When to use a single org vs multiple orgs, hub-and-spoke patterns, data sharing across orgs, Connected App and API patterns for multi-org. NOT for sandbox strategy (use sandbox-strategy). | |
| TODO | technical-debt-assessment | Identifying dead code, unused automations, overlapping flows and triggers, deprecated features in use, complexity indicators. Produces a findings report. NOT for implementing fixes. | |
| TODO | well-architected-review | Applying Salesforce Well-Architected Framework pillars (Trusted, Easy, Adaptable) to an org assessment. Produces a structured review. NOT for individual pillar deep-dives. | |
| TODO | platform-selection-guidance | Choosing the right Salesforce platform feature for a requirement: Flow vs Apex, LWC vs Aura (legacy), Custom Metadata vs Custom Settings vs Custom Objects, OmniStudio vs standard automation. NOT for implementation of the chosen option. | |
| TODO | security-architecture-review | Reviewing an org's security posture: sharing model completeness, FLS coverage, Apex security patterns, exposed APIs, Shield needs. Produces findings. NOT for implementing fixes (use security/* skills). | |

---

## Phase 2 — Sales Cloud

### Research Gate

Before creating any Sales Cloud skills, a research agent must complete the research tasks below.
The research output is a set of TODO rows inserted into the tables that follow.

| Status | Research Task | Instructions |
|--------|--------------|--------------|
| RESEARCH | sales-cloud-admin-research | Search official Sales Cloud docs and Trailhead. Identify every Admin task specific to Sales Cloud (Lead management, Opportunity management, Forecasting, Products & Pricebooks, Quotes, Territory Management, Einstein Activity Capture, High Velocity Sales). Add TODO rows to Admin table below. |
| RESEARCH | sales-cloud-ba-research | Identify BA tasks specific to Sales Cloud: sales process documentation, pipeline review configuration, forecast category mapping, territory hierarchy design. Add TODO rows to BA table below. |
| RESEARCH | sales-cloud-dev-research | Identify Dev tasks specific to Sales Cloud: Opportunity trigger patterns, Quote PDF customization, Territory API, Einstein Activity Capture integration. Add TODO rows to Dev table below. |
| RESEARCH | sales-cloud-data-research | Identify Data tasks specific to Sales Cloud: Lead conversion data mapping, Opportunity line item imports, historical pipeline migration. Add TODO rows to Data table below. |
| RESEARCH | sales-cloud-architect-research | Identify Architect tasks specific to Sales Cloud: multi-currency architecture, territory hierarchy design, CPQ vs standard Products decision. Add TODO rows to Architect table below. |

### Sales Cloud × Admin Role
<!-- Research agent inserts TODO rows here -->

### Sales Cloud × BA Role
<!-- Research agent inserts TODO rows here -->

### Sales Cloud × Dev Role
<!-- Research agent inserts TODO rows here -->

### Sales Cloud × Data Role
<!-- Research agent inserts TODO rows here -->

### Sales Cloud × Architect Role
<!-- Research agent inserts TODO rows here -->

---

## Phase 3 — Service Cloud

### Research Gate

| Status | Research Task | Instructions |
|--------|--------------|--------------|
| RESEARCH | service-cloud-admin-research | Search official Service Cloud docs. Identify Admin tasks: Case management, Omni-Channel routing, Entitlements and Milestones, SLA setup, Knowledge base, Email-to-Case, Chat, Einstein for Service. Add TODO rows below. |
| RESEARCH | service-cloud-ba-research | Identify BA tasks: SLA design, escalation matrix, knowledge taxonomy, agent console requirements. Add TODO rows below. |
| RESEARCH | service-cloud-dev-research | Identify Dev tasks: Case trigger patterns, Entitlement process Apex hooks, Knowledge article LWC, CTI integration. Add TODO rows below. |
| RESEARCH | service-cloud-data-research | Identify Data tasks: Case history migration, Knowledge article import, SLA reporting data model. Add TODO rows below. |
| RESEARCH | service-cloud-architect-research | Identify Architect tasks: Omni-Channel capacity model, Knowledge vs external CMS decision, Einstein Bot architecture. Add TODO rows below. |

### Service Cloud × Admin Role
<!-- Research agent inserts TODO rows here -->

### Service Cloud × BA Role
<!-- Research agent inserts TODO rows here -->

### Service Cloud × Dev Role
<!-- Research agent inserts TODO rows here -->

### Service Cloud × Data Role
<!-- Research agent inserts TODO rows here -->

### Service Cloud × Architect Role
<!-- Research agent inserts TODO rows here -->

---

## Phase 4 — Experience Cloud

### Research Gate

| Status | Research Task | Instructions |
|--------|--------------|--------------|
| RESEARCH | experience-cloud-admin-research | Search Experience Cloud docs. Identify Admin tasks: site creation and configuration, guest user security, member management, Audience targeting, CMS content, navigation menus, login and registration pages. Add TODO rows below. |
| RESEARCH | experience-cloud-ba-research | Identify BA tasks: portal requirements, self-service design, knowledge base taxonomy for portals. Add TODO rows below. |
| RESEARCH | experience-cloud-dev-research | Identify Dev tasks: LWR vs Aura template selection, Guest user Apex patterns, Experience Cloud LWC components, headless CMS integration. Add TODO rows below. |
| RESEARCH | experience-cloud-data-research | Identify Data tasks: external user data sharing, partner data access patterns. Add TODO rows below. |
| RESEARCH | experience-cloud-architect-research | Identify Architect tasks: licensing model selection, multi-site strategy, headless vs standard Experience Cloud. Add TODO rows below. |

### Experience Cloud × Admin Role
<!-- Research agent inserts TODO rows here -->

### Experience Cloud × BA Role
<!-- Research agent inserts TODO rows here -->

### Experience Cloud × Dev Role
<!-- Research agent inserts TODO rows here -->

### Experience Cloud × Data Role
<!-- Research agent inserts TODO rows here -->

### Experience Cloud × Architect Role
<!-- Research agent inserts TODO rows here -->

---

## Phase 5 — Marketing Cloud / MCAE (Pardot)

### Research Gate

| Status | Research Task | Instructions |
|--------|--------------|--------------|
| RESEARCH | marketing-cloud-admin-research | Search Marketing Cloud and MCAE/Pardot docs. Identify Admin tasks for both platforms. Note which tasks apply to Marketing Cloud Engagement vs MCAE vs Marketing Cloud Account Engagement. Add TODO rows below. |
| RESEARCH | marketing-cloud-ba-research | Identify BA tasks: campaign planning, lead scoring design, email journey mapping, consent and compliance requirements. Add TODO rows below. |
| RESEARCH | marketing-cloud-dev-research | Identify Dev tasks: AMPscript, SSJS, Marketing Cloud APIs, Pardot API, connector setup. Add TODO rows below. |
| RESEARCH | marketing-cloud-data-research | Identify Data tasks: data extension design, list management, suppression lists, Marketing Cloud Connect data sync. Add TODO rows below. |
| RESEARCH | marketing-cloud-architect-research | Identify Architect tasks: MC vs MCAE selection, multi-BU architecture, consent management architecture. Add TODO rows below. |

### Marketing Cloud × Admin Role
<!-- Research agent inserts TODO rows here -->

### Marketing Cloud × BA Role
<!-- Research agent inserts TODO rows here -->

### Marketing Cloud × Dev Role
<!-- Research agent inserts TODO rows here -->

### Marketing Cloud × Data Role
<!-- Research agent inserts TODO rows here -->

### Marketing Cloud × Architect Role
<!-- Research agent inserts TODO rows here -->

---

## Phase 6 — Revenue Cloud (CPQ & Billing)

### Research Gate

| Status | Research Task | Instructions |
|--------|--------------|--------------|
| RESEARCH | revenue-cloud-admin-research | Search Salesforce CPQ and Billing docs. Identify Admin tasks: product catalog setup, pricing rules, quote templates, billing schedules, contract management. Add TODO rows below. |
| RESEARCH | revenue-cloud-ba-research | Identify BA tasks: pricing model design, quote-to-cash process mapping, revenue recognition requirements. Add TODO rows below. |
| RESEARCH | revenue-cloud-dev-research | Identify Dev tasks: CPQ Apex plugin hooks, custom pricing actions, billing integration patterns. Add TODO rows below. |
| RESEARCH | revenue-cloud-data-research | Identify Data tasks: product catalog migration, historical order migration. Add TODO rows below. |
| RESEARCH | revenue-cloud-architect-research | Identify Architect tasks: CPQ vs Vlocity/Industries CPQ decision, multi-currency pricing architecture. Add TODO rows below. |

### Revenue Cloud × Admin Role
<!-- Research agent inserts TODO rows here -->

### Revenue Cloud × BA Role
<!-- Research agent inserts TODO rows here -->

### Revenue Cloud × Dev Role
<!-- Research agent inserts TODO rows here -->

### Revenue Cloud × Data Role
<!-- Research agent inserts TODO rows here -->

### Revenue Cloud × Architect Role
<!-- Research agent inserts TODO rows here -->

---

## Phase 7 — Field Service (FSL)

### Research Gate

| Status | Research Task | Instructions |
|--------|--------------|--------------|
| RESEARCH | fsl-admin-research | Search Field Service Lightning docs. Identify Admin tasks: resource setup, service territories, scheduling policies, work order configuration, mobile app setup. Add TODO rows below. |
| RESEARCH | fsl-ba-research | Identify BA tasks: scheduling optimization design, SLA configuration, crew management requirements. Add TODO rows below. |
| RESEARCH | fsl-dev-research | Identify Dev tasks: FSL Apex extension points, custom actions, mobile app extensions. Add TODO rows below. |
| RESEARCH | fsl-data-research | Identify Data tasks: work order history migration, resource and territory data setup. Add TODO rows below. |
| RESEARCH | fsl-architect-research | Identify Architect tasks: optimization policy design, offline-first architecture for mobile. Add TODO rows below. |

### FSL × Admin Role
<!-- Research agent inserts TODO rows here -->

### FSL × BA Role
<!-- Research agent inserts TODO rows here -->

### FSL × Dev Role
<!-- Research agent inserts TODO rows here -->

### FSL × Data Role
<!-- Research agent inserts TODO rows here -->

### FSL × Architect Role
<!-- Research agent inserts TODO rows here -->

---

## Phase 8 — Health Cloud

### Research Gate

| Status | Research Task | Instructions |
|--------|--------------|--------------|
| RESEARCH | health-cloud-admin-research | Search Health Cloud docs. Identify Admin tasks: patient/member setup, care plans, care team configuration, timeline configuration, referral management. Add TODO rows below. |
| RESEARCH | health-cloud-ba-research | Identify BA tasks: care coordination requirements, HIPAA workflow design. Add TODO rows below. |
| RESEARCH | health-cloud-dev-research | Identify Dev tasks: Health Cloud APIs, FHIR integration patterns, care plan Apex extensions. Add TODO rows below. |
| RESEARCH | health-cloud-data-research | Identify Data tasks: patient data migration, FHIR data mapping, consent data model. Add TODO rows below. |
| RESEARCH | health-cloud-architect-research | Identify Architect tasks: HIPAA compliance architecture, FHIR R4 integration design, data residency. Add TODO rows below. |

### Health Cloud × Admin Role
<!-- Research agent inserts TODO rows here -->

### Health Cloud × BA Role
<!-- Research agent inserts TODO rows here -->

### Health Cloud × Dev Role
<!-- Research agent inserts TODO rows here -->

### Health Cloud × Data Role
<!-- Research agent inserts TODO rows here -->

### Health Cloud × Architect Role
<!-- Research agent inserts TODO rows here -->

---

## Phase 9 — Financial Services Cloud

### Research Gate

| Status | Research Task | Instructions |
|--------|--------------|--------------|
| RESEARCH | fsc-admin-research | Search Financial Services Cloud docs. Identify Admin tasks: financial account setup, household model, referral configuration, compliant data sharing. Add TODO rows below. |
| RESEARCH | fsc-ba-research | Identify BA tasks: financial planning workflow design, compliance documentation requirements. Add TODO rows below. |
| RESEARCH | fsc-dev-research | Identify Dev tasks: FSC Apex extension points, compliant data sharing APIs. Add TODO rows below. |
| RESEARCH | fsc-data-research | Identify Data tasks: financial account migration, household data model setup. Add TODO rows below. |
| RESEARCH | fsc-architect-research | Identify Architect tasks: compliant data sharing model design, AML/KYC process architecture. Add TODO rows below. |

### FSC × Admin Role
<!-- Research agent inserts TODO rows here -->

### FSC × BA Role
<!-- Research agent inserts TODO rows here -->

### FSC × Dev Role
<!-- Research agent inserts TODO rows here -->

### FSC × Data Role
<!-- Research agent inserts TODO rows here -->

### FSC × Architect Role
<!-- Research agent inserts TODO rows here -->

---

## Phase 10 — Nonprofit Cloud (NPSP)

### Research Gate

| Status | Research Task | Instructions |
|--------|--------------|--------------|
| RESEARCH | npsp-admin-research | Search Nonprofit Cloud and NPSP docs. Identify Admin tasks: household account model, gift entry, soft credits, recurring donations, program management. Add TODO rows below. |
| RESEARCH | npsp-ba-research | Identify BA tasks: fundraising process mapping, program outcome tracking design. Add TODO rows below. |
| RESEARCH | npsp-dev-research | Identify Dev tasks: NPSP trigger framework extension, gift entry customization. Add TODO rows below. |
| RESEARCH | npsp-data-research | Identify Data tasks: constituent data migration, gift history import, NPSP data model mapping. Add TODO rows below. |
| RESEARCH | npsp-architect-research | Identify Architect tasks: NPSP vs Nonprofit Cloud (new) decision, program management data model design. Add TODO rows below. |

### NPSP × Admin Role
<!-- Research agent inserts TODO rows here -->

### NPSP × BA Role
<!-- Research agent inserts TODO rows here -->

### NPSP × Dev Role
<!-- Research agent inserts TODO rows here -->

### NPSP × Data Role
<!-- Research agent inserts TODO rows here -->

### NPSP × Architect Role
<!-- Research agent inserts TODO rows here -->

---

## Phase 11 — Commerce Cloud

### Research Gate

| Status | Research Task | Instructions |
|--------|--------------|--------------|
| RESEARCH | commerce-admin-research | Search Salesforce B2B and B2C Commerce docs. Note which tasks apply to B2B vs B2C. Identify Admin tasks: store setup, catalog configuration, pricing, checkout configuration. Add TODO rows below. |
| RESEARCH | commerce-ba-research | Identify BA tasks: B2B vs B2C requirement differences, checkout flow design. Add TODO rows below. |
| RESEARCH | commerce-dev-research | Identify Dev tasks: Commerce extension points, headless Commerce APIs, checkout integration. Add TODO rows below. |
| RESEARCH | commerce-data-research | Identify Data tasks: product catalog migration, order history import. Add TODO rows below. |
| RESEARCH | commerce-architect-research | Identify Architect tasks: B2B vs B2C architecture decision, headless vs standard Commerce, multi-store strategy. Add TODO rows below. |

### Commerce Cloud × Admin Role
<!-- Research agent inserts TODO rows here -->

### Commerce Cloud × BA Role
<!-- Research agent inserts TODO rows here -->

### Commerce Cloud × Dev Role
<!-- Research agent inserts TODO rows here -->

### Commerce Cloud × Data Role
<!-- Research agent inserts TODO rows here -->

### Commerce Cloud × Architect Role
<!-- Research agent inserts TODO rows here -->

---

## Phase 12 — Agentforce / Einstein AI

### Research Gate

| Status | Research Task | Instructions |
|--------|--------------|--------------|
| RESEARCH | agentforce-admin-research | Search Agentforce and Einstein docs. Identify Admin tasks: agent setup, topic configuration, action assignment, trust layer configuration, testing agents. Add TODO rows below (expand existing agentforce/ skills if appropriate). |
| RESEARCH | agentforce-ba-research | Identify BA tasks: agent use case design, topic and action requirements, conversation flow design. Add TODO rows below. |
| RESEARCH | agentforce-dev-research | Identify Dev tasks: custom agent actions via Apex/Flow, Prompt Builder templates, Einstein APIs, Model Builder. Add TODO rows below. |
| RESEARCH | agentforce-data-research | Identify Data tasks: Data Cloud setup for grounding, vector database patterns, retrieval augmented generation data prep. Add TODO rows below. |
| RESEARCH | agentforce-architect-research | Identify Architect tasks: Einstein Trust Layer architecture, multi-agent orchestration design, Data Cloud + Agentforce integration patterns. Add TODO rows below. |

### Agentforce × Admin Role
<!-- Research agent inserts TODO rows here -->

### Agentforce × BA Role
<!-- Research agent inserts TODO rows here -->

### Agentforce × Dev Role
<!-- Research agent inserts TODO rows here -->

### Agentforce × Data Role
<!-- Research agent inserts TODO rows here -->

### Agentforce × Architect Role
<!-- Research agent inserts TODO rows here -->

---

## Phase 13 — OmniStudio / Industries

### Research Gate

| Status | Research Task | Instructions |
|--------|--------------|--------------|
| RESEARCH | omnistudio-admin-research | Search OmniStudio docs. Identify Admin tasks not already covered by existing omnistudio/ skills. Check skills/omnistudio/ first. Add TODO rows below for gaps only. |
| RESEARCH | omnistudio-ba-research | Identify BA tasks: OmniScript flow design, FlexCard requirements, Integration Procedure design docs. Add TODO rows below. |
| RESEARCH | omnistudio-dev-research | Identify Dev tasks not already covered. Check skills/omnistudio/ first. Add TODO rows below for gaps only. |
| RESEARCH | omnistudio-data-research | Identify Data tasks: DataRaptor design patterns not covered, data migration for Industries objects. Add TODO rows below. |
| RESEARCH | omnistudio-architect-research | Identify Architect tasks: OmniStudio vs standard LWC/Flow decision, Industries Cloud architecture patterns. Add TODO rows below. |

### OmniStudio × Admin Role
<!-- Research agent inserts TODO rows here -->

### OmniStudio × BA Role
<!-- Research agent inserts TODO rows here -->

### OmniStudio × Dev Role
<!-- Research agent inserts TODO rows here -->

### OmniStudio × Data Role
<!-- Research agent inserts TODO rows here -->

### OmniStudio × Architect Role
<!-- Research agent inserts TODO rows here -->

---

## Phase 14 — CRM Analytics / Tableau

### Research Gate

| Status | Research Task | Instructions |
|--------|--------------|--------------|
| RESEARCH | analytics-admin-research | Search CRM Analytics (formerly Einstein Analytics / Tableau CRM) docs. Identify Admin tasks: dataset creation, dashboard sharing, app permissions, Data Manager. Also note where Tableau (server) vs CRM Analytics diverge. Add TODO rows below. |
| RESEARCH | analytics-ba-research | Identify BA tasks: KPI definition for dashboards, analytics requirements, data storytelling. Add TODO rows below. |
| RESEARCH | analytics-dev-research | Identify Dev tasks: SAQL queries, dashboard JSON, Einstein Discovery story creation, recipe design. Add TODO rows below. |
| RESEARCH | analytics-data-research | Identify Data tasks: dataset joins, data sync, augmentation, external data connectors. Add TODO rows below. |
| RESEARCH | analytics-architect-research | Identify Architect tasks: CRM Analytics vs Tableau vs standard Reports decision, row-level security in analytics, Data Cloud integration. Add TODO rows below. |

### CRM Analytics × Admin Role
<!-- Research agent inserts TODO rows here -->

### CRM Analytics × BA Role
<!-- Research agent inserts TODO rows here -->

### CRM Analytics × Dev Role
<!-- Research agent inserts TODO rows here -->

### CRM Analytics × Data Role
<!-- Research agent inserts TODO rows here -->

### CRM Analytics × Architect Role
<!-- Research agent inserts TODO rows here -->

---

## Phase 15 — Integration (MuleSoft / APIs)

### Research Gate

| Status | Research Task | Instructions |
|--------|--------------|--------------|
| RESEARCH | integration-admin-research | Search Salesforce integration docs. Identify Admin tasks: Named Credentials, Remote Site Settings, Connected Apps for external systems, outbound message setup. Check existing skills/integration/ first. Add TODO rows for gaps. |
| RESEARCH | integration-ba-research | Identify BA tasks: integration pattern selection, data mapping documentation, API contract requirements. Add TODO rows below. |
| RESEARCH | integration-dev-research | Identify Dev tasks not already covered by integration/ skills. Check skills/integration/ first. Add TODO rows for gaps only. |
| RESEARCH | integration-data-research | Identify Data tasks: CDC patterns, streaming integration data models, idempotent data sync design. Add TODO rows below. |
| RESEARCH | integration-architect-research | Identify Architect tasks: integration pattern selection (ESB vs point-to-point vs event-driven), MuleSoft architecture, API-led connectivity. Add TODO rows below. |

### Integration × Admin Role
<!-- Research agent inserts TODO rows here -->

### Integration × BA Role
<!-- Research agent inserts TODO rows here -->

### Integration × Dev Role
<!-- Research agent inserts TODO rows here -->

### Integration × Data Role
<!-- Research agent inserts TODO rows here -->

### Integration × Architect Role
<!-- Research agent inserts TODO rows here -->

---

## Phase 16 — DevOps (SFDX / Pipelines)

### Research Gate

| Status | Research Task | Instructions |
|--------|--------------|--------------|
| RESEARCH | devops-admin-research | Search Salesforce DevOps Center and Change Sets docs. Identify Admin tasks: change set creation, DevOps Center pipeline setup, release tracking. Add TODO rows below. |
| RESEARCH | devops-ba-research | Identify BA tasks: release planning, sprint-to-deployment mapping, environment strategy documentation. Add TODO rows below. |
| RESEARCH | devops-dev-research | Search SFDX, GitHub Actions, Copado, Gearset, and Flosum docs. Identify Dev tasks not already covered. Check skills/devops/ first. Add TODO rows for gaps only. |
| RESEARCH | devops-data-research | Identify Data tasks: data masking for sandboxes, sandbox seeding strategies, test data management. Add TODO rows below. |
| RESEARCH | devops-architect-research | Identify Architect tasks: branching strategy for SF, environment strategy (scratch org vs sandbox), CI/CD tool selection (native vs third-party). Add TODO rows below. |

### DevOps × Admin Role
<!-- Research agent inserts TODO rows here -->

### DevOps × BA Role
<!-- Research agent inserts TODO rows here -->

### DevOps × Dev Role
<!-- Research agent inserts TODO rows here -->

### DevOps × Data Role
<!-- Research agent inserts TODO rows here -->

### DevOps × Architect Role
<!-- Research agent inserts TODO rows here -->

---

## Handoff Log

| Agent | Task | Started | Completed | Notes |
|-------|------|---------|-----------|-------|
| — | — | — | — | — |

---

## Anti-Patterns (Do Not Do These)

- Do not create a skill for a Cloud × Role cell before completing the RESEARCH task for that cell.
- Do not write content from memory. Every factual claim needs an official source.
- Do not create overlapping skills. Always run search_knowledge.py first.
- Do not hand-edit registry/, vector_index/, or docs/SKILLS.md.
- Do not mark DONE until validate_repo.py exits 0.
- Do not skip the query fixture step. Skills with no fixture produce a WARN that fails CI.
