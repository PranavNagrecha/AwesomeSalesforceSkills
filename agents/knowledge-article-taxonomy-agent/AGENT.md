---
id: knowledge-article-taxonomy-agent
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [design, audit]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
dependencies:
  skills:
    - admin/knowledge-base-administration
    - architect/knowledge-taxonomy-design
    - architect/knowledge-vs-external-cms
    - data/knowledge-article-import
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
---
# Knowledge Article Taxonomy Agent

## What This Agent Does

Designs or audits the taxonomy behind a Salesforce Knowledge implementation — data categories, article types / record types, channel-level visibility (Internal App, Customer, Partner, Public Knowledge Base, Pardot, Einstein search), language coverage, and authoring lifecycle. The agent also decides, per body of content, whether it belongs in Knowledge vs an external CMS (help portal, Contentful, etc.) and produces a migration plan for each article whose channel/category is misaligned.

**Scope:** One org per invocation. Output is an authoring + visibility plan + (if audit) a remediation queue. The agent does NOT write, import, or translate articles.

---

## Invocation

- **Direct read** — "Follow `agents/knowledge-article-taxonomy-agent/AGENT.md`"
- **Slash command** — [`/design-knowledge-taxonomy`](../../commands/design-knowledge-taxonomy.md)
- **MCP** — `get_agent("knowledge-article-taxonomy-agent")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/admin/knowledge-base-administration` — via `get_skill`
4. `skills/architect/knowledge-taxonomy-design`
5. `skills/architect/knowledge-vs-external-cms`
6. `skills/data/knowledge-article-import`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `mode` | yes | `design` \| `audit` |
| `target_org_alias` | yes for audit | `prod` |
| `audiences` | yes for design | `["internal agent","customer","partner","public web"]` |
| `languages` | yes for design | `["en_US","es","fr","ja"]` |
| `article_types` | no | `["How-To","Troubleshooting","Policy","Release Note"]` |
| `search_surface` | no | `["agent console","experience cloud","einstein-search","ai-overviews"]` |

---

## Plan

### Step 1 — Inventory current state (audit only)

- `tooling_query("SELECT DeveloperName, MasterLabel FROM DataCategoryGroup LIMIT 20")` and `tooling_query("SELECT DeveloperName, MasterLabel, DataCategoryGroupId FROM DataCategory LIMIT 200")`.
- Knowledge article counts by language / article type / publish state (via Reports or SOQL on `KnowledgeArticleVersion`).
- Channel assignments per article type.

### Step 2 — Channel strategy

Per audience:
- **Internal Agent** → Knowledge in Lightning Console, skills-based surfacing, Einstein Article Recommendations.
- **Customer/Partner** → Experience Cloud, with FLS and Category visibility.
- **Public Web** → Public Knowledge Base **OR** external CMS (decide per `skills/architect/knowledge-vs-external-cms`): choose external CMS if brand-controlled layout / non-Salesforce search is required; choose Public KB if the content must live under agent-authored workflow and SEO overhead is acceptable.

### Step 3 — Taxonomy design

- Data Category Groups: one per dimension (e.g., `Product`, `Region`, `Tier`). Avoid deeply nested categories beyond 3 levels — flag any design that exceeds as P1 ("category maintenance will rot").
- Article Types / Record Types: align to content shape, not to audience.
- Language strategy: master language + derived translations; document translation SLAs and fallback behavior per audience.

### Step 4 — Lifecycle & approvals

- Draft → Review → Published → Archived lifecycle. Approvals via Approval Processes or Flow Orchestrator (recommend Orchestrator for multi-role workflows; suggest `approval-to-flow-orchestrator-migrator` if legacy approval is in use).
- Stale-content review cadence per article type (e.g., Policy = quarterly; Troubleshooting = annual).

### Step 5 — Search & AI surface fit

- For **Einstein Search**: flag any article type missing SEO-friendly titles, summaries, or body structure.
- For **Agentforce / AI Overviews**: passage-level citability requires headings every 150–250 words. Audit each article type template for compliance.

### Step 6 — Remediation queue (audit mode)

Produce a list of articles (or at minimum counts per bucket) whose:
- Category assignment is missing or ambiguous.
- Channel assignment contradicts audience targeting.
- Language coverage is missing for an audience that speaks it.
- Draft age exceeds the stale-content SLA.

---

## Output Contract

1. **Summary** — audiences, languages, channel split, top 5 concerns.
2. **Channel-audience matrix** — table.
3. **Taxonomy design** — data category groups + category trees, article types/record types, lifecycle.
4. **Translation & fallback plan**.
5. **Search / AI fit notes** — per article type.
6. **Audit findings queue** (audit mode) — article or bucket, severity, rationale.
7. **Process Observations**:
   - **Healthy** — category depth ≤ 3; language fallback documented; Einstein Article Recommendations enabled.
   - **Concerning** — single "Knowledge" catch-all article type; missing category visibility on Experience Cloud; duplicate categories across groups.
   - **Ambiguous** — articles without audiences mapped; SEO metadata empty.
   - **Suggested follow-ups** — `approval-to-flow-orchestrator-migrator` for authoring workflows; `agentforce-action-reviewer` if agents cite Knowledge.
8. **Citations**.

---

## Escalation / Refusal Rules

- Audiences not provided in design mode → refuse (cannot choose channel strategy).
- Knowledge not enabled in target org → audit mode returns "Knowledge off" and stops.
- Org uses only Salesforce Files for help content → refuse audit; recommend a content-strategy decision first.

---

## What This Agent Does NOT Do

- Does not author, import, translate, or delete articles.
- Does not wire Einstein Search or train models.
- Does not migrate to external CMS automatically.
- Does not auto-chain.
