# SfSkills — Salesforce AI Skill Library

The universal Salesforce knowledge layer for AI coding assistants.

Drop this into Claude Code, Cursor, Aider, Windsurf, or any AI tool and get role-accurate, source-grounded Salesforce guidance — for every role, every cloud, every task.

**686 skills · shared Apex/LWC/Flow templates · golden evals · live-org MCP server.**
1119+ skills planned across 5 roles × 16 clouds.

---

## What Makes This Different

Three layers that turn generic LLMs into Salesforce-literate agents:

1. **Skills** (`skills/<domain>/<skill>/`) — 686 structured guides. Every skill carries source-grounded instructions, code examples, gotchas, WAF mapping, and a per-skill list of **LLM anti-patterns** the model must refuse to produce.
2. **Shared canon** — One set of reusable building blocks the skills all point at, so the AI never reinvents them:
   - `templates/` → TriggerHandler, ApplicationLogger, SecurityUtils, HttpClient, TestDataFactory, LWC skeleton, Flow fault paths, Agentforce actions.
   - `standards/decision-trees/` → Routing for automation, async, integration, and sharing decisions — agents consult these **before** writing code.
   - `evals/` → Golden P0 cases for flagship skills. Output quality is testable, not vibes-based.
3. **Live-org MCP server** (`mcp/sfskills-mcp/`) — An AI agent can read this library **and** ask your actual org "does this already exist?" via your `sf` CLI auth. No secrets handled in-process. [Jump to setup ↓](#mcp-server-live-org-context)

---

## Who This Is For

| Role | What you get |
|------|-------------|
| **Admin** | Step-by-step configuration guides, FLS checklists, automation decision trees |
| **BA** | Requirements templates, UAT scripts, process mapping frameworks |
| **Developer** | Apex patterns with test classes, LWC component scaffolds, Flow best practices |
| **Data** | Migration runbooks, SOQL optimization, Bulk API patterns, LDV strategies |
| **Architect** | Decision frameworks, WAF reviews, scalability planning, ADR templates |

---

## Supported AI Tools

| Tool | Setup |
|------|-------|
| **Claude Code** | Clone + open. Works automatically via `CLAUDE.md`. |
| **Cursor** | `python3 scripts/export_skills.py --platform cursor` then copy `exports/cursor/.cursor/` to your project |
| **Aider** | `python3 scripts/export_skills.py --platform aider` then `aider --read exports/aider/CONVENTIONS.md` |
| **Windsurf** | `python3 scripts/export_skills.py --platform windsurf` then copy `exports/windsurf/.windsurf/` to your project |
| **Augment** | `python3 scripts/export_skills.py --platform augment` then copy `exports/augment/.augment/` to your project |
| **Any LLM** | Copy any `skills/<domain>/<skill>/SKILL.md` as a system prompt |

---

## 5-Minute Setup

```bash
# 1. Clone
git clone https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git
cd AwesomeSalesforceSkills

# 2. Install dependencies
python3 -m pip install -r requirements.txt

# 3a. Claude Code — works automatically via CLAUDE.md. Just open the repo.

# 3b. Cursor / Windsurf / Aider / Augment — export and copy:
python3 scripts/export_skills.py --platform cursor   # or windsurf | aider | augment | all
cp -r exports/cursor/.cursor/ /path/to/your/sf-project/

# 4. Search what's in the library
python3 scripts/search_knowledge.py "trigger recursion"
python3 scripts/search_knowledge.py "permission sets" --domain admin
```

Want your AI to see your actual org too? Install the **MCP server** below.

---

## What a Skill Looks Like

Every skill is a structured guide an AI follows end-to-end. Example for `apex/trigger-framework`:

```
trigger-framework/
├── SKILL.md              ← the AI's instructions: modes, gather questions, step-by-step
├── references/
│   ├── examples.md       ← real code examples with test classes
│   ├── gotchas.md        ← non-obvious platform behaviors
│   └── well-architected.md  ← WAF pillar mapping + official sources
├── templates/
│   └── trigger-framework-template.md  ← deployable scaffold
└── scripts/
    └── check_trigger.py  ← local validator (stdlib only, no pip)
```

Skills are plain markdown. They work in any AI tool that can read a file.

---

## Shared Templates

Canonical, copy-pasteable Salesforce building blocks live under `templates/`:

```
templates/
├── apex/              TriggerHandler, TriggerControl, BaseDomain/Service/Selector,
│                      ApplicationLogger, SecurityUtils, HttpClient
├── apex/tests/        TestDataFactory, TestRecordBuilder, MockHttpResponseGenerator,
│                      TestUserFactory, BulkTestPattern
├── apex/cmdt/         Trigger_Setting__mdt, Logger_Setting__mdt
├── apex/custom_objects/  Application_Log__c (+ fields)
├── lwc/               jest.config.js, component-skeleton/ (bundle + tests),
│                      patterns/ (wire, imperative, LDS form)
├── flow/              RecordTriggered_Skeleton, FaultPath_Template, Subflow_Pattern
└── agentforce/        AgentSkeleton.json, AgentActionSkeleton.cls, AgentTopic_Template.md
```

Every skill in this repo references these canonical files instead of
re-inventing scaffolds. AI tools reading the skills get one consistent
implementation of each Salesforce idiom — testable, version-pinned, and
deployable.

Drop the files you need into your SFDX project under `force-app/main/default/`
and rename. See [templates/README.md](./templates/README.md) for the layout
and dependency order.

---

## Covered Skills

| Domain | Skills |
|--------|--------|
| Admin | 200 — custom fields, objects, picklists, users, org setup, page layouts, permission sets, sharing, validation rules, flows, reports, data skew, requirements gathering, Experience Cloud site setup, member management, CMS content, guest access, moderation, SEO, portal requirements, self-service design, partner community, community engagement, CPQ product catalog and bundles, CPQ pricing rules, CPQ quote templates, FSL work orders, service territories, resource management, scheduling policies, mobile app setup, Health Cloud patient setup, care plan configuration, care program management, FSC financial accounts, household model configuration, FSC referral management, NPSP household accounts, gift entry and processing, soft credits and matching, recurring donations, Marketing Cloud Engagement setup, MCAE/Pardot setup, Email Studio, Journey Builder, Marketing Cloud Connect, MCAE lead scoring and grading, consent management, email deliverability, B2B Commerce store setup, CRM Analytics app creation, analytics dashboard design, integration-admin connected apps, remote site settings, outbound message setup, integration user management, change data capture admin... |
| Apex | 97 — trigger framework, batch, async, security patterns, callouts, mocking, platform cache, SOQL fundamentals, sf CLI and SFDX essentials, Metadata API and package.xml, debug logs and Developer Console, apex managed sharing, scheduled jobs, email services, fflib enterprise patterns, mixed DML and setup objects, record locking, callout-DML transaction boundaries, trigger-flow coexistence, apex performance profiling... |
| LWC | 32 — wire service, component communication, testing, accessibility, offline, performance, toast and notifications, dynamic components, imperative Apex, message channel patterns, LWR site development, Experience Cloud LWC components, authentication flows, headless CMS API, API access patterns, search customization, multi-IdP SSO... |
| Flow | 23 — record-triggered, screen flows, fault handling, bulkification, subflows, governance, debugging, auto-launched flow patterns, collection processing, External Services callouts, Flow for Slack Core Actions, flow action framework, flow large-data-volume patterns, Process Builder to Flow migration, Workflow Rule to Flow migration... |
| OmniStudio | 21 — OmniScript design, DataRaptor, Integration Procedures, security, FlexCard design patterns, calculation procedures, DataPack deployment, performance optimization, Industries CPQ vs Salesforce CPQ, OmniStudio testing patterns, OmniStudio CI/CD patterns... |
| Agentforce | 28 — agent actions, topic design, Einstein Trust Layer, agent creation, Einstein Copilot for Sales, Einstein Prediction Builder, Einstein Copilot for Service, Model Builder and BYOLLM, RAG patterns, agent testing and evaluation, persona design, MCP tool definition in Apex, Salesforce MCP server setup... |
| Security | 25 — org hardening, permission set groups, Shield Platform Encryption, event monitoring, field audit trail, transaction security policies, login forensics, network security and trusted IPs, sandbox data masking, API security and rate limiting, experience cloud security, FERPA compliance, MFA enforcement strategy, OAuth token management... |
| Integration | 35 — GraphQL, OAuth flows, Salesforce Connect, REST API patterns, SOAP API patterns, named credentials, Streaming API and PushTopic, platform events integration, Change Data Capture for external subscribers, callout limits and async patterns, file and document integration, idempotent integration patterns, Data Cloud Ingestion API streaming vs bulk, Pub/Sub API gRPC patterns, Revenue Lifecycle Management DRO, Loyalty Management setup, Slack Salesforce integration setup, Data Cloud query API, Data Cloud activation development, Data Cloud integration strategy, Bulk API 2.0 patterns, Slack Workflow Builder... |
| Data | 85 — multi-currency, SOSL, rollup alternatives, data model design patterns, data migration planning, data quality and governance, bulk API and large data loads, data archival strategies, SOQL query optimization, service data archival, external user data sharing, community user migration, community analytics, partner data access patterns, volunteer management requirements, NPSP gift history import, B2B Commerce product catalog migration, Order Management order history migration, OCI inventory data, Data Cloud DMO identity resolution, Data Cloud consent and privacy, Revenue Cloud data model... |
| Architect | 90 — solution design patterns, limits and scalability planning, multi-org strategy, technical debt assessment, well-architected review, platform selection guidance, security architecture review, Experience Cloud licensing model, multi-site architecture, headless vs LWR vs Aura decision framework, Experience Cloud performance and CDN, Experience Cloud integration patterns (SSO, widgets, Data Cloud), MuleSoft Anypoint Platform runtime model selection, large-data-volume architecture, Data Cloud vs CRM Analytics decision... |
| DevOps | 50 — scratch org management, sandbox refresh and templates, unlocked package development, second-generation managed packages, DevOps Center pipeline, GitHub Actions for Salesforce, post-deployment validation, deployment error troubleshooting, rollback and hotfix strategy, pre-deployment checklist, go-live cutover planning, VS Code extensions, SFDX project structure, multi-package development, API version management, 1GP managed package development, CPQ deployment patterns, Salesforce CLI automation, code review checklist... |

**See the full catalog:** [docs/SKILLS.md](./docs/SKILLS.md)

---

## Using Skills in Practice

### Ask your AI to use a specific skill
```
"Use the trigger-framework skill to build an Account trigger handler"
"Follow the batch-apex-patterns skill to review this batch class"
"Apply the permission-set-architecture skill to this org assessment"
```

### Let the AI find the right skill
```
"My trigger is firing twice on the same record update"
→ AI searches, finds recursive-trigger-prevention skill, applies it

"Why can't my user see the field even though they have object access?"
→ AI searches, finds soql-security + permission-set-architecture, applies both
```

### Search skills yourself
```bash
python3 scripts/search_knowledge.py "my flow is hitting limits"
python3 scripts/search_knowledge.py "callout timeout" --domain integration
python3 scripts/search_knowledge.py "data skew performance" --domain data
```

---

## Request a Missing Skill

Three ways:

**Run the `/request-skill` command** — Ask the AI to follow [`commands/request-skill.md`](./commands/request-skill.md). It asks 4 questions, checks existing coverage, and adds a TODO row to `MASTER_QUEUE.md` automatically.

**Add directly to the queue** — Open `MASTER_QUEUE.md` and append a row:
```markdown
| TODO | your-skill-name | What it does. NOT for what it doesn't cover. | |
```

**Open a GitHub issue** — Title: `[Skill Request] <domain>: <skill-name>`. Describe the use case, the role, and which cloud it applies to.

---

## Contribute a Skill

See [CONTRIBUTING.md](./CONTRIBUTING.md) for the full workflow.

The short version:
```bash
# 1. Check it doesn't already exist
python3 scripts/search_knowledge.py "<your topic>"

# 2. Scaffold it
python3 scripts/new_skill.py <domain> <skill-name>

# 3. Fill every TODO in the generated files
#    — Reference templates/ for any Apex/LWC/Flow scaffolds (don't inline your own)
#    — Cite standards/decision-trees/ if your skill recommends a technology

# 4. Sync and validate
python3 scripts/skill_sync.py --skill skills/<domain>/<skill-name>
python3 scripts/validate_repo.py
python3 evals/scripts/run_evals.py --structure          # if you added a golden eval

# 5. Open a PR
```

Every skill must pass three gates before merging:
- **Structural gate** — `validate_repo.py` exits 0
- **Canon gate** — scaffolds reference `templates/`; technology choices cite `standards/decision-trees/`; any `@InvocableMethod` or agent action uses `templates/agentforce/AgentActionSkeleton.cls` as the base shape
- **Quality gate** — `standards/skill-content-contract.md` (source grounding, content depth, agent usability, contradiction check, freshness) plus `references/llm-anti-patterns.md` populated with real failure modes for that skill

Flagship skills additionally carry a golden eval under `evals/golden/` with 3+ P0 cases.

---

## Update an Existing Skill

Found something wrong? Source changed? Platform behavior updated?

```bash
# Edit the skill files
# Then:
python3 scripts/skill_sync.py --skill skills/<domain>/<skill-name>
python3 scripts/validate_repo.py
# Open a PR with what changed and why
```

Or tell the AI:
```
"The trigger-framework skill is missing guidance for the new Flow-triggered Apex pattern in Spring '25"
```
The Currency Monitor agent will handle it if you flag it during a release cycle.

---

## Standards and Rules

| File | What it defines |
|------|----------------|
| `AGENT_RULES.md` | Canonical workflow rules for agents and contributors |
| `CLAUDE.md` | Claude Code-specific instructions |
| `templates/` | Canonical Apex / LWC / Flow / Agentforce scaffolds every skill points at |
| `standards/source-hierarchy.md` | 4-tier source trust ladder + contradiction rules |
| `standards/skill-content-contract.md` | 5 quality gates every skill must pass |
| `standards/decision-trees/` | Cross-skill routing: automation, async, integration, sharing |
| `standards/official-salesforce-sources.md` | Official doc URLs by domain |
| `standards/well-architected-mapping.md` | WAF pillar definitions and scoring |
| `standards/naming-conventions.md` | Apex, LWC, Flow, Object naming rules |
| `standards/code-review-checklist.md` | Full code review checklist |
| `skills/*/*/references/llm-anti-patterns.md` | Per-skill list of wrong outputs the model must refuse to produce |
| `evals/` | Golden output-quality evals for flagship skills (10 skills × 3 P0 cases) |

---

## Agents: Build-time vs Run-time

This repo ships **two classes of agents**, both as instruction files (`agents/<name>/AGENT.md`) that any agentic AI can follow (Claude Code, Codex, Cursor, Windsurf, or any MCP client).

| Class | Purpose | Who invokes |
|---|---|---|
| **Build-time (12)** | Produce and maintain the skill library itself | Repo maintainers, `/run-queue` |
| **Run-time (39)** | Use the library to do real Salesforce work in your codebase / org | You — via slash commands, direct AGENT.md reads, or MCP `get_agent` |

The contract every agent follows: [`agents/_shared/AGENT_CONTRACT.md`](./agents/_shared/AGENT_CONTRACT.md).
The full roster: [`agents/_shared/RUNTIME_VS_BUILD.md`](./agents/_shared/RUNTIME_VS_BUILD.md).

---

### Run-time Agents (the ones you call)

Each agent takes concrete inputs, composes skills + templates + decision-trees + (optional) live-org probes, and returns a PR-ready report or plan. **Three invocation modes** — all fire the same AGENT.md:

1. **Slash command** — ask your AI to follow `commands/<name>.md`
2. **Direct read** — point any AI at `agents/<name>/AGENT.md`
3. **MCP** — call `get_agent(name)` on the SfSkills MCP server; the server returns the instructions for your model to execute

Every run-time agent follows the same 8-section contract (including a mandatory **Process Observations** block that flags healthy, concerning, and ambiguous patterns in the org while producing the output), cites every skill / template / decision-tree it used, and never writes to your org.

#### Developer + architecture tier (11)

| Agent | Slash command | What it does |
|---|---|---|
| `apex-refactorer` | [`/refactor-apex`](./commands/refactor-apex.md) | Refactor an Apex class onto the canonical `templates/apex/` patterns + generate a test class |
| `trigger-consolidator` | [`/consolidate-triggers`](./commands/consolidate-triggers.md) | Collapse N triggers on one sObject into the handler framework with a deactivation plan |
| `test-class-generator` | [`/gen-tests`](./commands/gen-tests.md) | Generate a bulk-safe ≥ 85%-coverage test class using `TestDataFactory` / `BulkTestPattern` |
| `soql-optimizer` | [`/optimize-soql`](./commands/optimize-soql.md) | Find and fix SOQL anti-patterns (query-in-loop, non-selective, no-security) |
| `security-scanner` | [`/scan-security`](./commands/scan-security.md) | Audit CRUD/FLS, sharing, hardcoded secrets, Remote Sites vs Named Credentials |
| `flow-analyzer` | [`/analyze-flow`](./commands/analyze-flow.md) | Decide Flow vs Apex per the automation decision tree + bulkification review |
| `bulk-migration-planner` | [`/plan-bulk-migration`](./commands/plan-bulk-migration.md) | Pick Bulk API 2.0 / Platform Events / Pub/Sub / REST Composite from volume + latency |
| `lwc-auditor` | [`/audit-lwc`](./commands/audit-lwc.md) | A11y + performance + security audit of an LWC bundle |
| `deployment-risk-scorer` | [`/score-deployment`](./commands/score-deployment.md) | Pre-deploy risk score vs live org (breaking-change list via MCP probes) |
| `agentforce-builder` | [`/build-agentforce-action`](./commands/build-agentforce-action.md) | Scaffold Agentforce action: Apex `@InvocableMethod` + topic YAML + test + golden eval |
| `org-drift-detector` | [`/detect-drift`](./commands/detect-drift.md) | Library ↔ live-org gap and bloat report across every flagship prescription |

#### Admin accelerators — Tier 1 (8)

| Agent | Slash command | What it does |
|---|---|---|
| `field-impact-analyzer` | [`/analyze-field-impact`](./commands/analyze-field-impact.md) | Blast-radius report before renaming or deleting a field |
| `object-designer` | [`/design-object`](./commands/design-object.md) | Setup-ready sObject design from a concept (fields, RTs, VRs, layouts) |
| `permission-set-architect` | [`/architect-perms`](./commands/architect-perms.md) | Profile-less PS / PSG / Muting design per persona |
| `flow-builder` | [`/build-flow`](./commands/build-flow.md) | Design a Flow from requirements, route to Apex when the tree says so |
| `workflow-and-pb-migrator` | [`/migrate-workflow-pb`](./commands/migrate-workflow-pb.md) | Migrate legacy Workflow Rules + Process Builders to Flow |
| `validation-rule-auditor` | [`/audit-validation-rules`](./commands/audit-validation-rules.md) | Audit VRs for bypass, bulk safety, and Flow coexistence |
| `data-loader-pre-flight` | [`/preflight-load`](./commands/preflight-load.md) | Go/no-go checklist for a Data Loader / Bulk API load |
| `duplicate-rule-designer` | [`/design-duplicate-rule`](./commands/design-duplicate-rule.md) | Matching + Duplicate Rules scoped to the load and post-load hygiene |

#### Strategic — Tier 2 (10)

| Agent | Slash command | What it does |
|---|---|---|
| `sharing-audit-agent` | [`/audit-sharing`](./commands/audit-sharing.md) | OWD + sharing-rule findings, data-skew hot-list, guest-user exposure |
| `lightning-record-page-auditor` | [`/audit-record-page`](./commands/audit-record-page.md) | Dynamic Forms, render cost, related-list strategy, Path, LWC weight |
| `approval-to-flow-orchestrator-migrator` | [`/migrate-approval-to-orchestrator`](./commands/migrate-approval-to-orchestrator.md) | Migrate Approval Processes to Flow Orchestrator with parallel-run plan |
| `record-type-and-layout-auditor` | [`/audit-record-types`](./commands/audit-record-types.md) | Flag RT proliferation, Master Layout issues, LRP mapping gaps |
| `picklist-governor` | [`/govern-picklists`](./commands/govern-picklists.md) | GVS adoption, inactive-value drift, dependent-chain probe |
| `data-model-reviewer` | [`/review-data-model`](./commands/review-data-model.md) | Review relationships, rollups, External IDs, growth forecast, indexes |
| `integration-catalog-builder` | [`/catalog-integrations`](./commands/catalog-integrations.md) | NCs + Remote Sites + Connected Apps + certs, scored for posture |
| `report-and-dashboard-auditor` | [`/audit-reports`](./commands/audit-reports.md) | Stale / unfiltered / dashboard running-user leakage, subscription abuse |
| `csv-to-object-mapper` | [`/map-csv-to-object`](./commands/map-csv-to-object.md) | Map CSV headers → sObject fields + External ID + VR collision report |
| `email-template-modernizer` | [`/modernize-email-templates`](./commands/modernize-email-templates.md) | Classic / Lightning / Enhanced LEX classification + migration plan |

#### Vertical + governance — Tier 3 (10)

| Agent | Slash command | What it does |
|---|---|---|
| `omni-channel-routing-designer` | [`/design-omni-channel`](./commands/design-omni-channel.md) | Queue + routing-config + presence design with capacity math |
| `knowledge-article-taxonomy-agent` | [`/design-knowledge-taxonomy`](./commands/design-knowledge-taxonomy.md) | Data categories, article types, channel-audience matrix, lifecycle |
| `sales-stage-designer` | [`/design-sales-stages`](./commands/design-sales-stages.md) | Opportunity stage ladder + forecast categories + VR gates + Path |
| `lead-routing-rules-designer` | [`/design-lead-routing`](./commands/design-lead-routing.md) | Source × geo × product routing matrix, queues, SLAs, conversion handoff |
| `case-escalation-auditor` | [`/audit-case-escalation`](./commands/audit-case-escalation.md) | Assignment + escalation + entitlement + milestone coverage audit |
| `sandbox-strategy-designer` | [`/design-sandbox-strategy`](./commands/design-sandbox-strategy.md) | Environment ladder + scratch pools + refresh calendar + masking |
| `release-train-planner` | [`/plan-release-train`](./commands/plan-release-train.md) | Package strategy, branching, CI/CD gates, release calendar, hotfix plan |
| `waf-assessor` | [`/assess-waf`](./commands/assess-waf.md) | Well-Architected scorecard across Trusted / Easy / Adaptable / Resilient / Composable |
| `agentforce-action-reviewer` | [`/review-agentforce-action`](./commands/review-agentforce-action.md) | Per-action A–F scorecard + topic coherence + guardrails gap list |
| `prompt-library-governor` | [`/govern-prompt-library`](./commands/govern-prompt-library.md) | Prompt template inventory, duplicate detection, Trust Layer alignment |

Full list + source-skill map: [`agents/_shared/SKILL_MAP.md`](./agents/_shared/SKILL_MAP.md).

---

### How the library itself gets built

The build-time agents live in the same `agents/` tree. They're the skill factory:

```
MASTER_QUEUE.md                  what needs to be built
      │
      ▼
agents/orchestrator/             routes TODOs to the right builder
      │
      ├── agents/task-mapper/           researches Cloud × Role task universes
      ├── agents/content-researcher/    grounds every claim in Tier 1–3 sources
      ├── agents/admin-skill-builder/   builds Admin + BA skills
      ├── agents/dev-skill-builder/     builds Apex / LWC / Flow / Integration / DevOps
      ├── agents/data-skill-builder/    builds data modeling, migration, SOQL
      ├── agents/architect-skill-builder/  builds solution design + WAF review
      ├── agents/code-reviewer/         canon-gate review (templates, decision-trees, evals)
      ├── agents/validator/             structural + quality gates before every commit
      ├── agents/currency-monitor/      flags stale skills after each SF release
      ├── agents/org-assessor/          audits a target org against the library
      └── agents/release-planner/       assembles release notes from skill deltas
```

Operators drive the system via slash commands under `commands/` (invoke by asking the AI to "follow `commands/<name>.md`"):

| Command | What it does |
|---|---|
| [`/run-queue`](./commands/run-queue.md) | Autonomous loop: claim → research → build → validate → commit |
| [`/new-skill`](./commands/new-skill.md) | Scaffold one skill through the full contract |
| [`/request-skill`](./commands/request-skill.md) | 4-question flow to append a TODO to `MASTER_QUEUE.md` |
| [`/assess-org`](./commands/assess-org.md) | Run `agents/org-assessor` against a live org via the MCP server |
| [`/review`](./commands/review.md) | Run `agents/code-reviewer` against a PR or local change |
| [`/release-notes`](./commands/release-notes.md) | Generate release notes from recent skill deltas |

### Source Hierarchy

Every claim in every skill is grounded against a 4-tier trust ladder. When sources disagree, the lower tier loses. Defined in [`standards/source-hierarchy.md`](./standards/source-hierarchy.md).

- **Tier 1** — Official Salesforce docs (ground truth)
- **Tier 2** — Trailhead, Salesforce Architects blog, Salesforce Ben
- **Tier 3** — Andy in the Cloud, Apex Hours, Salesforce Stack Exchange
- **Tier 4** — Community signal (context only, never the basis for a claim)

---

## Roadmap

**Shipped in v1:**

- [x] 686 skills across Admin, Apex, LWC, Flow, OmniStudio, Agentforce, Security, Integration, Data, Architect, DevOps
- [x] Shared templates (Apex handler framework, logger, security utils, HTTP client, test factories, LWC skeleton, Flow fault paths, Agentforce action shell)
- [x] Decision trees for automation, async, integration, and sharing selection
- [x] Golden evals for 10 flagship skills (30 P0 cases)
- [x] MCP server exposing the library + live-org lookups

**In flight toward v2 (1119+ planned):**

- [ ] Per-cloud tagging across every skill (`clouds: [...]` in registry)
- [ ] Expand golden evals from 10 → 40 flagship skills
- [ ] Role-specific landing pages (Admin, BA, Developer, Data, Architect)
- [ ] Deeper cloud coverage: Sales, Service, Experience, Marketing, Revenue (CPQ), Field Service, Health, FSC, Nonprofit, Commerce, CRM Analytics, MuleSoft
- [ ] Currency monitor — automated staleness flagging after each Salesforce release

Live queue: [MASTER_QUEUE.md](./MASTER_QUEUE.md)

---

## Maintainer

**Pranav Nagrecha** — Salesforce Technical Architect

**Version:** 1.0.0 | **Last Updated:** April 2026

Issues → [GitHub Issues](https://github.com/PranavNagrecha/AwesomeSalesforceSkills/issues)
Skill requests → `/request-skill` in Claude Code or open an issue with `[Skill Request]` prefix

---

## MCP Server (live-org context)

The `mcp/sfskills-mcp/` package exposes this library and your real Salesforce
org to any MCP-capable AI tool so the agent can answer "does this trigger
framework already exist in my org?" **without asking you**.

Fifteen tools, all read-only:

| Tool                       | What it does                                                                    |
| -------------------------- | ------------------------------------------------------------------------------- |
| `search_skill`             | Lexical search over the 686+ SfSkills corpus with optional domain filter.       |
| `get_skill`                | Full SKILL.md + registry metadata for a given skill id.                         |
| `describe_org`             | `sf org display` summary (org id, instance, edition, sandbox/scratch flags).    |
| `list_custom_objects`      | Custom sObjects in the target org with optional substring filter.               |
| `list_flows_on_object`     | Flows (record / scheduled / platform-event triggered) targeting an sObject.    |
| `validate_against_org`     | Category-aware probe: does the skill's guidance already have analogs in the org?|
| `list_agents`              | Enumerate SfSkills run-time + build-time agents (one-line summary each).        |
| `get_agent`                | Fetch an agent's full AGENT.md (refactorer, scanner, admin accelerators, etc.) so the caller's model can execute it. |
| `list_validation_rules`    | Validation rules for a given sObject with formula, active flag, error display. |
| `list_permission_sets`     | Permission sets + groups + muting permission sets, with license + assignment counts. |
| `describe_permission_set`  | Full object / field / user permission matrix for a specific permission set.    |
| `list_record_types`        | Record types, active flag, master-layout assignments, picklist value scoping.  |
| `list_named_credentials`   | Named Credentials + External Credentials (read-only; never returns secrets).   |
| `list_approval_processes`  | Approval processes + steps + next approver rules for an sObject.               |
| `tooling_query`            | Generic read-only Tooling API SOQL with a DML/mutation blocklist (escape hatch for admin-land agents). |

### Install

```bash
# From the repo root
python3 -m pip install -e mcp/sfskills-mcp

# Authenticate via the Salesforce CLI (no secrets enter the MCP server)
sf org login web --alias my-dev
sf config set target-org=my-dev
```

### Connect your AI tool

The server speaks the standard MCP stdio transport, so it drops into every
modern AI coding tool with a single snippet. Quick start for Cursor
(`~/.cursor/mcp.json` or project-scoped `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "sfskills": {
      "command": "python3",
      "args": ["-m", "sfskills_mcp"],
      "env": { "SFSKILLS_REPO_ROOT": "/absolute/path/to/AwesomeSalesforceSkills" }
    }
  }
}
```

**[→ Full setup guide for every MCP-capable AI tool](./mcp/sfskills-mcp/docs/CONNECT.md)**
— Claude Code, Claude Desktop, Cursor, Windsurf, Zed, VS Code (Copilot Agent),
Cline, Continue, Sourcegraph Cody, OpenAI Codex CLI, Gemini CLI, Goose,
LibreChat, Open WebUI, JetBrains AI Assistant, 5ire, and the generic stdio
transport — with per-client pitfalls, verification steps (MCP Inspector),
troubleshooting, and the security model.

See [mcp/sfskills-mcp/README.md](./mcp/sfskills-mcp/README.md) for tool
schemas, validate_against_org probe routing, and design notes.
