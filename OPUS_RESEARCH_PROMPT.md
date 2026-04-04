# Master Research Prompt — Opus Queue Population

Paste this entire prompt into a fresh Claude Opus session with access to the repo at:
`/Users/pranavnagrecha/VS Code/Personal/SfSkills`

---

## Your Mission

You are a Salesforce skills researcher and queue architect. Your job is to fully populate `MASTER_QUEUE.md` with TODO rows for every skill that should exist in this repo — so that an autonomous hourly build agent can pick them up and build them without any further human input.

**The list below is a starting point, not a ceiling.** You are expected to go beyond it. If you discover skill areas, Salesforce products, practitioner workflows, or role-specific tasks that are not listed here but should exist — add them. Use your knowledge of the full Salesforce ecosystem, official docs, Trailhead, and release notes to find gaps the list misses.

Examples of things that might be missing from the initial list:
- Data Cloud / CDP — data streams, identity resolution, calculated insights, activation
- Net Zero Cloud — carbon accounting, emission factors, sustainability reporting
- Education Cloud — student success hub, advisor workflows
- Automotive Cloud — vehicle lifecycle, dealer management
- Consumer Goods Cloud — visit execution, retail execution
- Manufacturing Cloud — account-based forecasting, rebate management
- Public Sector Solutions — licensing, permits, inspections
- Loyalty Management — program setup, tier rules, partner loyalty
- Slack integration patterns — Slack-first workflows, Slack Connect, Flow for Slack
- Advanced Flow patterns beyond what Core Platform covers (Flow for Industries, etc.)
- Advanced LWC patterns not yet in the repo (offline, mobile, performance)
- Advanced Apex patterns not yet in the repo (platform cache, CDC in Apex, etc.)
- MuleSoft Anypoint Platform — beyond basic connector usage
- Tableau CRM / CRM Analytics — dashboards, SAQL, predictive analytics
- Einstein features per cloud — not just generic Agentforce
- Salesforce Functions (even if deprecated — practitioners still encounter it)
- Any Trailhead learning path that represents a real practitioner skill gap

When in doubt: if a Salesforce professional would Google it, it should be a skill.

When you are done, the MASTER_QUEUE.md should have real, actionable TODO rows for:
- Every cloud phase (Phases 2–16 and beyond if you find more)
- Every underbuilt domain (devops, security, agentforce, omnistudio, integration)
- Every role × cloud combination that has real practitioner tasks
- Any additional Salesforce products or skill areas you discover through research

The hourly build agent does the actual building. You do the research and queue population. Do not build any skills yourself.

---

## Step 1 — Read the repo

Read these files completely before doing anything:

1. `CLAUDE.md` — repo rules and structure
2. `AGENT_RULES.md` — skill naming, domain conventions, quality gates
3. `MASTER_QUEUE.md` — the queue you are populating
4. `standards/official-salesforce-sources.md` — where to find official docs
5. Run: `python3 scripts/search_knowledge.py "salesforce" --json` to understand what already exists

Also run:
```bash
find skills/ -name "SKILL.md" | sed 's|skills/||' | sed 's|/SKILL.md||' | sort
```
This gives you every skill already built. Do NOT add TODO rows for skills that already exist.

---

## Step 2 — Understand the TODO row format

Every TODO row must follow this exact format:

```markdown
| TODO | skill-name-in-kebab-case | One sentence: what this skill covers and when to use it. NOT for [explicit exclusion that prevents overlap with other skills]. | |
```

Rules for the description:
- Must include "NOT for ..." — this is enforced by the validator
- Must be specific enough that a builder agent knows exactly what to write
- Should name the key concepts/features covered
- Should be 1 sentence, under 200 characters

Rules for the skill name:
- All lowercase kebab-case
- No domain prefix unless genuinely ambiguous across domains
- Must be unique across the entire repo

Rules for domain assignment:
- Admin tasks → `admin`
- BA tasks → `admin` (BA skills live in admin domain)
- Dev tasks → most specific: `apex` / `lwc` / `flow` / `integration` / `devops`
- Data tasks → `data`
- Architect tasks → `architect`
- OmniStudio tasks → `omnistudio`
- Agentforce/Einstein tasks → `agentforce`
- Security tasks → `security`

---

## Step 3 — Research and populate domain gaps first

These domains are underbuilt and need a full skill sweep BEFORE cloud-specific work. Research each one using official Salesforce documentation and Trailhead, then add TODO rows directly to the correct section in MASTER_QUEUE.md.

Add a new section at the top of MASTER_QUEUE.md called `## Phase 0 — Domain Sweeps (Cross-Cloud)` just above Phase 1. This is where cross-cloud domain skills live.

### 3a — DevOps Domain (~40-50 skills needed)

Research: `developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/`
Research: Salesforce CLI docs, Unlocked Packages, DevOps Center, Change Sets, Scratch Orgs

Cover every practitioner task across:
- Source control and version control with Salesforce (Git + SFDX)
- Scratch org creation, management, and shape
- Sandboxes: types, refresh strategy, data masking
- Deployment: change sets, SFDX deploy, manifest/package.xml
- Unlocked packages: design, versioning, dependencies
- 2nd-generation managed packages (2GP)
- DevOps Center: pipeline stages, work items, bundling
- CI/CD pipelines: Bitbucket, GitHub Actions, GitLab CI for Salesforce
- Environment strategy: scratch → sandbox → staging → production
- Org branching strategy: org-based vs artifact-based
- Automated testing in pipelines: apex test run, code coverage gates
- Release management: release notes, rollback planning
- Static analysis: PMD, Salesforce Code Analyzer
- Permission set deployment ordering and dependencies
- Post-install scripts and pre-deployment checks

### 3b — Security Domain (~20-25 skills needed)

Research: `help.salesforce.com/s/articleView?id=sf.security_overview.htm`
Research: Salesforce Shield docs, Security Health Check, Event Monitoring

Cover every practitioner task across:
- Salesforce Shield: Platform Encryption, Event Monitoring, Field Audit Trail
- Security Health Check: reading scores, remediating findings
- Event Monitoring: log types, querying logs, threat detection patterns
- Login forensics and identity verification
- Transaction Security policies (Einstein + legacy)
- Network security: trusted IP ranges, My Domain, CSP Trusted Sites
- Data masking in sandboxes
- Apex security: SOQL injection prevention, FLS enforcement patterns, CRUD enforcement
- API security: OAuth scopes, Connected App policies, IP restrictions
- Certificate and key management
- Data classification and sensitivity labels
- GDPR/data privacy: right to erasure, data subject requests in Salesforce
- Guest user security: profile hardening, site security best practices
- B2C/Experience Cloud security hardening

### 3c — Agentforce / Einstein AI Domain (~15-20 skills needed)

Research: `developer.salesforce.com/docs/einstein/genai/`
Research: Agentforce documentation, Einstein Trust Layer, Prompt Builder

Cover every practitioner task across:
- Agentforce agent creation: topics, actions, instructions
- Standard agents vs custom agents
- Agent actions: Apex actions, Flow actions, prompt actions
- Einstein Trust Layer: data masking, zero retention, audit trail
- Prompt Builder: prompt templates, grounding, flex templates
- Model selection and configuration (Einstein models vs Bring Your Own LLM)
- Einstein Copilot (now Agentforce) in Sales Cloud and Service Cloud
- Einstein for Service: case classification, article recommendations
- Einstein for Sales: opportunity scoring, activity capture
- RAG (Retrieval Augmented Generation) patterns in Salesforce
- Testing agents: conversation simulation, topic coverage testing
- Agent security: user permissions, data access scoping
- Vector databases and Data Cloud integration for AI grounding
- Einstein Analytics vs CRM Analytics naming/positioning

### 3d — OmniStudio Domain (extend existing ~4 skills to ~20)

Research: `developer.salesforce.com/docs/atlas.en-us.salesforce_vlocity.meta/`
Research: OmniStudio documentation, Industries documentation

Already built: `dataraptor-patterns`, `integration-procedures`, `omniscript-design-patterns`, `omnistudio-security`

Cover the gaps:
- FlexCards: design patterns, data sources, actions, state management
- DataRaptor Load vs Extract vs Transform — decision guide (separate from existing patterns skill)
- Calculation Procedures and Matrices
- OmniStudio debugging: console, breakpoints, DataRaptor testing
- OmniStudio deployment: DataPacks, version control
- OmniStudio performance optimization
- Industries CPQ vs standard Salesforce CPQ
- OmniStudio LWC integration (calling OmniScripts from LWC)
- OmniChannel Framework integration with OmniStudio
- Managed vs unmanaged OmniStudio components
- OmniStudio migration from Vlocity to native OmniStudio

### 3e — Integration Domain (extend existing ~3 skills to ~20)

Research: `developer.salesforce.com/docs/atlas.en-us.api_rest.meta/`
Research: Platform Events docs, Change Data Capture docs, MuleSoft basics

Already built: `graphql-api-patterns`, `oauth-flows-and-connected-apps`, `salesforce-connect-external-objects`

Cover the gaps:
- REST API: CRUD operations, query endpoint, bulk operations, versioning
- SOAP API: WSDL, partner vs enterprise WSDL, when to use SOAP
- Streaming API: PushTopic, Generic Streaming, limits
- Platform Events: publish/subscribe patterns, replay ID, error handling
- Change Data Capture: which objects, change event fields, replay
- Bulk API 2.0: job management, serial vs parallel, monitoring
- Composite API: composite requests, sObject tree, batch limits
- Outbound Messages: workflow-triggered, SOAP endpoint requirements
- External Services: OpenAPI import, invocable actions from flows
- MuleSoft Anypoint: Salesforce connector, watermark pattern, error handling
- Event-driven architecture: platform events vs CDC vs streaming API decision
- Webhook patterns: inbound (site.com/services/apexrest) vs outbound
- Named Credentials: per-user vs per-org, legacy vs new format
- Callout limits and async callout patterns

---

## Step 4 — Populate all cloud phases (Phases 2–16)

For each cloud phase, replace the RESEARCH rows with actual TODO rows. Do not leave any RESEARCH rows — convert them all to real skills.

For each Cloud × Role combination:
1. Web search the official Salesforce documentation for that cloud and role
2. Identify every distinct practitioner task (not features — tasks with a start, steps, and output)
3. Check if it already exists: `python3 scripts/search_knowledge.py "<task>" --json`
4. If `has_coverage: false` → add a TODO row
5. If `has_coverage: true` → skip (do not add duplicate)

Minimum skills per major cloud × role cell: 5
Maximum: 20 (group related sub-tasks if over 20)

### Phase 2 — Sales Cloud
Roles: Admin, BA, Dev, Data, Architect
Key topics: Leads, Opportunities, Forecasting, Products & Pricebooks, Quotes, CPQ basics, Territory Management, Einstein Activity Capture, Cadences/High Velocity Sales, Sales Engagement

### Phase 3 — Service Cloud
Roles: Admin, BA, Dev, Data, Architect
Key topics: Cases, Omni-Channel routing, Entitlements & Milestones, SLAs, Knowledge base, Email-to-Case, Chat & Messaging, Einstein for Service, Service Console, Field Service lite

### Phase 4 — Experience Cloud
Roles: Admin, BA, Dev, Data, Architect
Key topics: Site creation, Templates (LWR vs Aura), Guest user security, Member management, Digital Experiences, CMS content, Portals, Partner communities, Customer communities, Headless CMS

### Phase 5 — Marketing Cloud / MCAE
Roles: Admin, BA, Dev, Data, Architect
Key topics: Marketing Cloud Engagement (email, journeys, automations), MCAE/Pardot (lead scoring, engagement studio), Marketing Cloud Account Engagement, Marketing Cloud Connect, data extensions, AMPscript, SSJS, consent management

### Phase 6 — Revenue Cloud (CPQ)
Roles: Admin, BA, Dev, Data, Architect
Key topics: Products & Pricebooks, CPQ Quote configuration, Pricing rules, Quote templates, Contracts, Billing, Revenue recognition, Subscription management, Amendment & renewal

### Phase 7 — Field Service (FSL)
Roles: Admin, BA, Dev, Data, Architect
Key topics: Work orders, Service territories, Resources, Scheduling & optimization, Mobile app, Inventory management, Service appointments, Crew management, Shifts

### Phase 8 — Health Cloud
Roles: Admin, BA, Dev, Data, Architect
Key topics: Patient/member setup, Care plans, Care teams, Timeline, Referral management, HIPAA compliance patterns, FHIR integration, Care program management

### Phase 9 — Financial Services Cloud
Roles: Admin, BA, Dev, Data, Architect
Key topics: Financial accounts, Household model, Referrals, Compliant data sharing, AML/KYC workflows, Wealth management, Insurance, Mortgage/lending workflows

### Phase 10 — Nonprofit Cloud (NPSP)
Roles: Admin, BA, Dev, Data, Architect
Key topics: Constituent management, Donation & gift processing, Recurring donations, Soft credits, Household accounts, Grant management, Program management, Volunteers

### Phase 11 — Commerce Cloud
Roles: Admin, BA, Dev, Data, Architect
Key topics: B2B Commerce, B2C Commerce (SFCC), Store setup, Product catalogs, Pricing & promotions, Checkout, Order management, Headless commerce, Commerce Einstein

### Phase 12 — Agentforce / Einstein AI (Cloud-Specific)
Roles: Admin, BA, Dev, Data, Architect
Key topics: Cloud-specific AI use cases — Sales AI, Service AI, Marketing AI, Analytics AI — beyond the core Agentforce domain skills already added in Phase 0

### Phase 13 — OmniStudio / Industries (Cloud-Specific)
Roles: Admin, BA, Dev, Data, Architect
Key topics: Industry-specific OmniStudio usage — Insurance, Communications, Energy, Public Sector — beyond core OmniStudio domain skills

### Phase 14 — CRM Analytics / Tableau
Roles: Admin, BA, Dev, Data, Architect
Key topics: Dashboard creation, Lenses & datasets, SAQL, Dataflows & recipes, Einstein Discovery, Predictive analytics, Tableau CRM vs Tableau Desktop, embedding analytics in Salesforce

### Phase 15 — Integration (MuleSoft/APIs — Cloud-Specific)
Roles: Admin, BA, Dev, Data, Architect
Key topics: Cloud-specific integration patterns beyond the core integration domain skills — Sales Cloud sync patterns, Service Cloud CTI integration, Marketing Cloud Connect, Health Cloud FHIR, etc.

### Phase 16 — DevOps (Cloud-Specific Deployment Patterns)
Roles: Admin, BA, Dev, Data, Architect
Key topics: Cloud-specific deployment concerns beyond core devops domain — CPQ deployment ordering, OmniStudio DataPack deployment, Health Cloud metadata dependencies, etc.

---

## Step 5 — Update MASTER_QUEUE.md structure

After adding all TODO rows:

1. **Remove all RESEARCH rows** — replace each one with the actual TODO rows you researched. RESEARCH rows are a placeholder; you are converting them to real work.

2. **Add proper table headers** to each Cloud × Role section:
```markdown
### Sales Cloud × Admin Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | skill-name | Description. NOT for exclusion. | |
```

3. **Update the Progress Summary table** at the top of MASTER_QUEUE.md:
   - Replace all `RESEARCH` entries in Skills Planned with actual counts
   - Example: `| 2 | Sales Cloud | 5 roles | 28 | 0 | 28 |`

4. **Add Phase 0 section** at the top (above Phase 1) for the domain sweeps:
```markdown
## Phase 0 — Domain Sweeps (Cross-Cloud)

These skills apply across all clouds. Build before cloud-specific phases.

### DevOps Domain
> Domain folder: `devops`
| Status | Skill Name | Description | Notes |
...

### Security Domain
> Domain folder: `security`
...

### Agentforce Domain
> Domain folder: `agentforce`
...

### OmniStudio Domain (gaps only)
> Domain folder: `omnistudio`
...

### Integration Domain (gaps only)
> Domain folder: `integration`
...
```

---

## Step 5b — Audit already-built domains for gaps

The following domains have skills but are not complete. For each one, look at what's already built and identify what's missing:

```bash
find skills/apex -name "SKILL.md" | xargs grep -l "^name:" | sort
find skills/lwc -name "SKILL.md" | xargs grep -l "^name:" | sort
find skills/flow -name "SKILL.md" | xargs grep -l "^name:" | sort
find skills/admin -name "SKILL.md" | xargs grep -l "^name:" | sort
```

For each domain, ask: "What would a senior Salesforce professional expect to find here that isn't here yet?"

Examples of likely gaps:
- `apex`: Continuation callouts, Custom Iterables, Custom Iterators, Apex Managed Sharing, without sharing patterns, Apex Email Service
- `lwc`: Composable Design System, LWC for Mobile, Dynamic Forms integration, LWC in Flows as screen components, MessageChannel advanced patterns
- `flow`: Flow debugging, Flow limits and anti-patterns, Auto-launched flows, Flow interviews, Pause elements and wait events
- `admin`: Territories (Enterprise Territory Management), Advanced approval routing, Custom permissions, Delegated administration deep dive, Community/Experience Cloud basics for admins
- `data`: Data Cloud setup, identity resolution, Big Objects for archival, Change Data Capture for data teams

Add any confirmed gaps as TODO rows in the appropriate Phase 1 domain section (Core Platform × [Role]).

---

## Step 6 — Quality checks before committing

For each TODO row you add, verify:
- [ ] Skill name is unique (not already in `skills/` directory)
- [ ] Description includes "NOT for ..."
- [ ] Domain folder is correct for the role
- [ ] Skill is a real practitioner task, not a feature description
- [ ] No TODO row duplicates an existing built skill

Run at the end:
```bash
python3 scripts/search_knowledge.py "devops" --json
python3 scripts/search_knowledge.py "security" --json
python3 scripts/search_knowledge.py "agentforce" --json
```
Scan results to confirm no duplicates slipped through.

---

## Step 7 — Commit

```bash
cd "/Users/pranavnagrecha/VS Code/Personal/SfSkills"
git add MASTER_QUEUE.md
git commit -m "research: populate full queue — Phase 0 domain sweeps + Phases 2-16 all clouds

Phase 0 (domain sweeps):
  - devops: N TODO rows
  - security: N TODO rows
  - agentforce: N TODO rows
  - omnistudio: N TODO rows (gaps)
  - integration: N TODO rows (gaps)

Phases 2-16 (all clouds):
  - Sales Cloud: N TODO rows
  - Service Cloud: N TODO rows
  [... continue for each cloud]

Total new TODO rows: N
All RESEARCH rows converted to real TODO rows.
Queue is now fully pre-populated for autonomous build agent.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"

git push origin main || gh repo sync PranavNagrecha/AwesomeSalesforceSkills --source main --force
```

---

## What the hourly agent does after you finish

Nothing changes for the hourly agent. It reads MASTER_QUEUE.md, finds TODO rows, builds 6 skills per run, marks them DONE. With a fully populated queue of 400-600 TODO rows, it runs continuously without any human input until every skill is built.

Your job ends when you push. The agent does the rest.
