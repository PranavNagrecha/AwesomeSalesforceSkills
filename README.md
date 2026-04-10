# SfSkills — Salesforce AI Skill Library

The universal Salesforce knowledge layer for AI coding assistants.

Drop this into Claude Code, Cursor, Aider, Windsurf, or any AI tool and get role-accurate, source-grounded Salesforce guidance — for every role, every cloud, every task.

**447 skills built. 640+ planned across 5 roles × 16 clouds.**

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

## 5-Minute Setup (Claude Code)

```bash
# 1. Clone
git clone https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git
cd AwesomeSalesforceSkills

# 2. Install dependencies
python3 -m pip install -r requirements.txt

# 3. Search what's available
python3 scripts/search_knowledge.py "trigger recursion"
python3 scripts/search_knowledge.py "permission sets" --domain admin
python3 scripts/search_knowledge.py "bulk data load"

# 4. Open in Claude Code — skills activate automatically
```

---

## 5-Minute Setup (Cursor / Windsurf / Aider / Augment)

```bash
# 1. Clone
git clone https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git
cd AwesomeSalesforceSkills

# 2. Install dependencies
python3 -m pip install -r requirements.txt

# 3. Export for your tool
python3 scripts/export_skills.py --platform cursor      # or windsurf / aider / augment
python3 scripts/export_skills.py --all                  # export for every platform at once

# 4. Copy the output into your Salesforce project
cp -r exports/cursor/.cursor/ /path/to/your/sf-project/
```

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

## Covered Skills

| Domain | Skills |
|--------|--------|
| Admin | 122 — custom fields, objects, picklists, users, org setup, page layouts, permission sets, sharing, validation rules, flows, reports, data skew, requirements gathering, Experience Cloud site setup, member management, CMS content, guest access, moderation, SEO, portal requirements, self-service design, partner community, community engagement, CPQ product catalog and bundles, CPQ pricing rules, CPQ quote templates, FSL work orders, service territories, resource management, scheduling policies, mobile app setup, Health Cloud patient setup, care plan configuration, care program management, FSC financial accounts, household model configuration, FSC referral management, NPSP household accounts, gift entry and processing, soft credits and matching, recurring donations, Marketing Cloud Engagement setup, MCAE/Pardot setup, Email Studio, Journey Builder, Marketing Cloud Connect, MCAE lead scoring and grading, consent management, email deliverability, B2B Commerce store setup... |
| Apex | 69 — trigger framework, batch, async, security patterns, callouts, mocking, platform cache, SOQL fundamentals, sf CLI and SFDX essentials, Metadata API and package.xml, debug logs and Developer Console, apex managed sharing, scheduled jobs, email services, fflib enterprise patterns, mixed DML and setup objects, record locking, callout-DML transaction boundaries, trigger-flow coexistence, apex performance profiling... |
| LWC | 31 — wire service, component communication, testing, accessibility, offline, performance, toast and notifications, dynamic components, imperative Apex, message channel patterns, LWR site development, Experience Cloud LWC components, authentication flows, headless CMS API, API access patterns, search customization, multi-IdP SSO... |
| Flow | 18 — record-triggered, screen flows, fault handling, bulkification, subflows, governance, debugging, auto-launched flow patterns, collection processing, External Services callouts... |
| OmniStudio | 18 — OmniScript design, DataRaptor, Integration Procedures, security, FlexCard design patterns, calculation procedures, DataPack deployment, performance optimization, Industries CPQ vs Salesforce CPQ... |
| Agentforce | 22 — agent actions, topic design, Einstein Trust Layer, agent creation, Einstein Copilot for Sales, Einstein Prediction Builder, Einstein Copilot for Service, Model Builder and BYOLLM, RAG patterns, agent testing and evaluation, persona design, MCP tool definition in Apex, Salesforce MCP server setup... |
| Security | 23 — org hardening, permission set groups, Shield Platform Encryption, event monitoring, field audit trail, transaction security policies, login forensics, network security and trusted IPs, sandbox data masking, API security and rate limiting, experience cloud security, FERPA compliance... |
| Integration | 20 — GraphQL, OAuth flows, Salesforce Connect, REST API patterns, SOAP API patterns, named credentials, Streaming API and PushTopic, platform events integration, Change Data Capture for external subscribers, callout limits and async patterns, file and document integration... |
| Data | 35 — multi-currency, SOSL, rollup alternatives, data model design patterns, data migration planning, data quality and governance, bulk API and large data loads, data archival strategies, SOQL query optimization, service data archival, external user data sharing, community user migration, community analytics, partner data access patterns... |
| Architect | 37 — solution design patterns, limits and scalability planning, multi-org strategy, technical debt assessment, well-architected review, platform selection guidance, security architecture review, Experience Cloud licensing model, multi-site architecture, headless vs LWR vs Aura decision framework, Experience Cloud performance and CDN, Experience Cloud integration patterns (SSO, widgets, Data Cloud)... |
| DevOps | 38 — scratch org management, sandbox refresh and templates, unlocked package development, second-generation managed packages, DevOps Center pipeline, GitHub Actions for Salesforce, post-deployment validation, deployment error troubleshooting, rollback and hotfix strategy, pre-deployment checklist, go-live cutover planning, VS Code extensions, SFDX project structure, multi-package development, API version management... |

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

If you need a skill that doesn't exist yet:

**Option 1 — Tell the AI (Claude Code):**
```
/request-skill
```
The agent asks what you need, checks for existing coverage, and adds it to the build queue.

**Option 2 — Add directly to the queue:**
Open `MASTER_QUEUE.md` and add a row to the relevant section:
```markdown
| TODO | your-skill-name | What it does. NOT for what it doesn't cover. | |
```

**Option 3 — Open a GitHub issue:**
Title: `[Skill Request] <domain>: <skill-name>`
Body: describe the use case, the role, and what cloud it applies to.

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

# 4. Sync and validate
python3 scripts/skill_sync.py --skill skills/<domain>/<skill-name>
python3 scripts/validate_repo.py

# 5. Open a PR
```

Every skill must pass two gates before merging:
- **Structural gate:** `validate_repo.py` exits 0
- **Quality gate:** `standards/skill-content-contract.md` — source grounding, content depth, agent usability, contradiction check, freshness

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
| `standards/source-hierarchy.md` | 4-tier source trust ladder + contradiction rules |
| `standards/skill-content-contract.md` | 5 quality gates every skill must pass |
| `standards/official-salesforce-sources.md` | Official doc URLs by domain |
| `standards/well-architected-mapping.md` | WAF pillar definitions and scoring |
| `standards/naming-conventions.md` | Apex, LWC, Flow, Object naming rules |
| `standards/code-review-checklist.md` | Full code review checklist |

---

## Architecture

```
MASTER_QUEUE.md          ← what needs to be built
      │
      ▼
Orchestrator Agent       ← routes tasks to the right builder
      │
      ├── Task Mapper         ← researches Cloud × Role task universes
      ├── Content Researcher  ← grounds every claim in official sources (Tier 1-3)
      ├── Admin Skill Builder ← builds Admin + BA skills
      ├── Dev Skill Builder   ← builds Apex, LWC, Flow, Integration, DevOps skills
      ├── Data Skill Builder  ← builds data modeling, migration, SOQL skills
      ├── Architect Builder   ← builds solution design, WAF review skills
      ├── Currency Monitor    ← flags stale skills after each SF release
      └── Validator           ← structural + quality gates before every commit
```

Skills are grounded in a 4-tier source hierarchy:
- **Tier 1:** Official Salesforce docs (ground truth)
- **Tier 2:** Trailhead, Salesforce Architects blog, Salesforce Ben
- **Tier 3:** Andy in the Cloud, Apex Hours, Salesforce Stack Exchange
- **Tier 4:** Community signal (context only, never the basis for a claim)

---

## Roadmap

- [x] Core Platform skills (77 built)
- [ ] Sales Cloud × all roles
- [ ] Service Cloud × all roles
- [ ] Experience Cloud × all roles
- [ ] Marketing Cloud / MCAE × all roles
- [ ] Revenue Cloud (CPQ) × all roles
- [ ] Field Service × all roles
- [ ] Health Cloud × all roles
- [ ] Financial Services Cloud × all roles
- [ ] Nonprofit Cloud × all roles
- [ ] Commerce Cloud × all roles
- [ ] Agentforce / Einstein AI × all roles
- [ ] OmniStudio / Industries × all roles
- [ ] CRM Analytics × all roles
- [ ] Integration (MuleSoft) × all roles
- [ ] DevOps × all roles

Track progress: [MASTER_QUEUE.md](./MASTER_QUEUE.md)

---

## Maintainer

**Pranav Nagrecha** — Salesforce Technical Architect

**Version:** 1.0.0 | **Last Updated:** April 2026

Issues → [GitHub Issues](https://github.com/PranavNagrecha/AwesomeSalesforceSkills/issues)
Skill requests → `/request-skill` in Claude Code or open an issue with `[Skill Request]` prefix
