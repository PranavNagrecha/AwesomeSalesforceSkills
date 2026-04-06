---
name: knowledge-taxonomy-design
description: "Use when designing or restructuring a Salesforce Knowledge taxonomy: Data Category Group structure, hierarchy depth, article type selection, article lifecycle governance (Draft/Published/Archived), Validation Status gating, and content gap analysis via KCS methodology and Search Activity Gaps. Triggers: knowledge taxonomy design, data category hierarchy, knowledge article lifecycle, knowledge governance model, KCS content gap analysis, search activity gaps, knowledge category structure. NOT for Knowledge admin feature setup (use admin/knowledge-setup), NOT for Experience Cloud search configuration, NOT for Einstein Article Recommendations tuning."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Operational Excellence
  - User Experience
tags:
  - knowledge
  - data-categories
  - article-lifecycle
  - kcs
  - content-governance
  - taxonomy
triggers:
  - "how should I structure our Knowledge data categories for a multi-product support org"
  - "we are hitting limits on our knowledge category hierarchy and articles are hard to find"
  - "how do I govern the article lifecycle from draft through publish and archive with validation status"
  - "what is the right number of data category groups for our knowledge base"
  - "how do I use KCS methodology and Search Activity Gaps to find content gaps in Knowledge"
  - "how deep should our knowledge category hierarchy be"
inputs:
  - Number of products or business units requiring distinct article sets
  - Current article count and growth rate
  - Agent populations who will author vs consume articles
  - Channel surfaces (Service Console, Experience Cloud, Agentforce RAG)
  - Existing content governance process (if any)
  - Validation Status requirements (none, simple approval, full KCS Evolve loop)
outputs:
  - Data Category Group layout with recommended hierarchy depth
  - Article type inventory with field requirements per type
  - Article lifecycle governance model (roles, statuses, Validation Status config)
  - Content gap analysis approach using Search Activity Gaps and KCS Solve/Evolve loop
  - Migration or restructuring sequence for existing article sets
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Knowledge Taxonomy Design

Use this skill when designing or restructuring the taxonomy that underpins a Salesforce Knowledge base. It activates when a practitioner must decide how to organise Data Category Groups and hierarchy levels, govern article lifecycle (Draft → Published → Archived), gate publication through Validation Status, and identify content gaps using Search Activity Gaps and KCS methodology. It produces a structured taxonomy model, a lifecycle governance design, and a content gap analysis plan grounded in platform limits.

---

## Before Starting

Gather this context before working on anything in this domain:

- **How many distinct article audiences or products exist?** Each audience or product may warrant its own Data Category Group. Salesforce allows up to 5 Data Category Groups per object by default (maximum 5 total across the org; only 3 are active at once without a support request). Exceeding this forces awkward flattening inside a single group.
- **What is the most common wrong assumption?** That more hierarchy levels improve findability. Deep hierarchies (more than 3 levels for most orgs) increase categorisation overhead, cause miscategorisation, and make Search Activity Gaps analysis harder to act on. Flatter taxonomies with broader parent categories and specific leaves outperform deep trees in agent search speed.
- **What limits are in play?** 5 Data Category Groups per org (3 active by default), 5 hierarchy levels per group, 100 categories per group; article types are fixed-shape metadata — adding fields requires a new article type version; Validation Status is a single org-wide setting, not per-article-type; Search Activity Gaps dashboard retains data for rolling 90 days.

---

## Core Concepts

### Data Category Groups and Hierarchy

A Data Category Group is a named classification dimension applied to Knowledge articles (and Cases and Answers, if enabled). Each group holds a tree of categories up to 5 levels deep with up to 100 total categories per group. The hierarchy is navigated top-down in the agent console and Experience Cloud, so breadth at the second level determines how quickly agents locate content.

Salesforce enforces a default limit of 3 active Data Category Groups per org (maximum 5). Activating a group requires assigning it to the Knowledge object via Setup → Data Category Group Assignments. Deactivated groups remain in the system but are invisible to end users and agents — this is useful for managing taxonomy migrations without data loss.

**Hierarchy design principle:** Use 2–3 active levels for most orgs. Level 1 is the primary dimension (Product, Business Unit, or Topic). Level 2 is a sub-dimension (Product Family, Support Tier, or Subject Area). Level 3 is optional and should only exist where the article corpus is large enough to warrant it (>200 articles in the parent). Levels 4–5 are rarely justified and significantly increase maintenance burden.

### Article Lifecycle: Draft → Published → Archived

Every Knowledge article moves through a defined lifecycle controlled by Validation Status and Publication Status:

- **Draft** — Article is being authored. Visible only to agents with "Manage Articles" permission. Cannot surface in customer-facing channels or Agentforce RAG.
- **Published** — Article is live. Visible to configured audiences per Data Category visibility rules. Searchable in Service Console, Experience Cloud, and Einstein RAG contexts.
- **Archived** — Article is withdrawn from search results and channel surfaces but remains in the system for compliance and audit. Archived articles can be restored to Draft. Hard deletion is a separate action requiring "Delete Knowledge" permission.

**Validation Status** is an additional gating layer independent of Publication Status. It supports three built-in states — Not Validated, Work In Progress, Validated — and can be extended to custom picklist values via the KnowledgeArticleVersion standard object. A common pattern gates publication on `Validation Status = Validated`, enforced through a Before-Save Flow or process that blocks status transitions. This is the KCS "Evolve Loop" integration point.

### Validation Status as a Quality Gate

When Validation Status is enabled (Setup → Knowledge Settings → Enable Validation Status), it appears on every article. The setting is binary and org-wide; it cannot be toggled per article type. Once enabled, it cannot be disabled without clearing all existing Validation Status values first.

For KCS-aligned orgs, the standard pattern maps the KCS workflow stages to Validation Status:
- **Solve Loop** — article created during case resolution, status = Work In Progress, published immediately so agents can find and reuse it, refinement deferred
- **Evolve Loop** — article reviewed by a domain expert, status moved to Validated once content meets quality bar

### Content Gap Analysis via Search Activity Gaps

The Search Activity Gaps dashboard (Knowledge → Search Activity Gaps) shows search terms entered by agents and customers that returned zero results or low-CTR results. It is the primary signal for missing or poorly-titled articles. The dashboard retains 90 days of data and is segmented by channel (Internal, Primus, Experience Cloud).

KCS Solve Loop practice embeds article creation directly into case resolution: when an agent searches for an article during case work and finds nothing useful, they create a new article before closing the case. This turns every case into a content signal. Search Activity Gaps then validates that the new articles are eliminating the gaps over subsequent weeks.

---

## Common Patterns

### Product-First Category Group Layout

**When to use:** Multi-product orgs where agents are assigned to product queues and need to filter articles to their product scope quickly.

**How it works:**
1. Create one Data Category Group named `Products` with Level 1 = product family, Level 2 = individual product or version.
2. Create a second Data Category Group named `Topics` with Level 1 = topic type (How-To, Troubleshooting, Reference, Release Notes), Level 2 = subject domain.
3. Assign both groups to the Knowledge object. Leave the third slot for a future `Regions` or `Audience` group if needed.
4. Each article is tagged to one product leaf and one topic type. Agents filter by product first, topic second.

**Why not a single deep tree:** Combining product and topic in one tree forces articles to live at deep nodes (e.g., Products → Cloud CRM → Admin → Troubleshooting → Login). A single hierarchy means agents must navigate 4–5 levels to narrow results. Two flat groups allow independent filters that compose at query time.

### KCS Solve-and-Evolve Governance Model

**When to use:** Any org where agents handle high case volume and content quality has historically degraded because only specialists could publish articles.

**How it works:**
1. Enable Validation Status in Knowledge Settings.
2. Map `Validation Status = Work In Progress` to "published, agent-authored" articles (Solve Loop). Agents create and publish articles during case work; status signals the article needs expert review.
3. Map `Validation Status = Validated` to "reviewed, canonical" articles (Evolve Loop). Domain experts review Work In Progress articles weekly and promote to Validated once content meets quality criteria.
4. Build a Knowledge dashboard filtered to `Validation Status = Work In Progress` as the review queue for domain experts.
5. Track Search Activity Gaps weekly. When a gap disappears (zero-result search term now returns results), attribute it to the relevant Solve Loop article that closed the gap.

**Why not gate all publication on expert review:** KCS principle is that a timely imperfect article is more valuable than a perfect article delayed by approval. Gating on expert review introduces a bottleneck that kills agent adoption. The Solve Loop publishes immediately; the Evolve Loop improves over time.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single product, <500 articles | One Data Category Group with 2 levels (Topic, Sub-Topic) | Overhead of multiple groups not justified; single group with flat hierarchy is easy to maintain |
| Multi-product, each product has dedicated agent teams | One group per major dimension (Products, Topics) — up to 3 active | Keeps each dimension independently navigable; avoids deep combined tree |
| Articles serve both internal agents and Experience Cloud customers | Separate Validation Status tracking for each audience tier using custom picklist values | Default three values often insufficient; custom values allow audience-specific quality gates |
| Org has high case volume and agents don't author articles | Implement KCS Solve Loop — require article search before case close, prompt creation on zero results | Turns case volume into content creation signal; Search Activity Gaps closes the feedback loop |
| Existing deep taxonomy (4–5 levels) with poor search performance | Flatten to 2–3 levels during a structured migration: map leaf categories to new parents, re-assign articles in bulk via Workbench or Data Loader | Deep hierarchies penalise search relevance; flattening improves SOSL scoring of category-matched articles |
| Validation Status not enabled but org wants to go KCS | Enable carefully — cannot disable without clearing all values; plan the picklist design before enabling | One-way enablement means the picklist design must be final before go-live |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Audit current state.** Count existing Data Category Groups, active groups, hierarchy depth per group, total category count per group, and article count per leaf category. Export via Setup → Data Categories or query `DataCategory` and `DataCategoryGroup` objects via SOQL. Identify groups that are inactive or over-allocated.
2. **Define taxonomy dimensions.** Identify the independent classification axes that agents and customers use to find articles (Product, Topic Type, Audience, Region). Each independent axis is a candidate for its own Data Category Group. Confirm total required groups ≤ 3 active (request limit increase if 4–5 are genuinely required).
3. **Design hierarchy depth.** For each group, map the category tree. Target 2–3 levels for most groups. Apply the >200 articles rule before adding a Level 3 node. Document the proposed tree in a spreadsheet before creating categories in Setup.
4. **Design article lifecycle and Validation Status model.** Decide whether Validation Status is required. If yes, define the picklist values before enabling (default: Not Validated, Work In Progress, Validated; extend only if a distinct custom state is needed). Map each status to a role and a workflow step. Document who can transition from each status.
5. **Implement and migrate.** Create Data Category Groups and category trees in Setup. Re-assign articles to new categories using Data Loader (update `DataCategorySelection` records). Archive deprecated categories after migration is verified.
6. **Set up content gap analysis.** Enable Search Activity Gaps if not already active. Baseline the current gap list. Communicate the KCS Solve Loop expectation to agents: search before closing, create if nothing relevant exists. Schedule a weekly review of the Search Activity Gaps dashboard with domain expert reviewers.
7. **Validate and iterate.** After 30 days, review: category distribution (are articles evenly distributed or clustered in a few nodes?), Search Activity Gap trend (is the gap list shrinking?), Validation Status distribution (is Work In Progress queue growing faster than Evolve Loop can clear?). Adjust taxonomy or process based on findings.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Total active Data Category Groups ≤ 3 (or limit increase has been requested and approved)
- [ ] No Data Category Group exceeds 5 hierarchy levels or 100 categories
- [ ] Each article type's field set is documented and matches the article audience's information need
- [ ] Validation Status picklist values are defined and mapped to workflow roles before enablement
- [ ] KCS Solve Loop process is documented and communicated to agent population
- [ ] Search Activity Gaps dashboard is accessible and baseline gap list is captured
- [ ] Article migration or re-categorisation sequence is planned with rollback approach

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Validation Status cannot be disabled after enablement** — Once you enable Validation Status in Knowledge Settings, you cannot turn it off without first clearing all existing Validation Status field values on every article version. In orgs with thousands of articles, this is a significant data operation. Design the picklist before enabling; do not enable to "try it out" in production.
2. **Only 3 Data Category Groups are active by default** — Salesforce limits orgs to 3 *active* Data Category Groups by default, even though the object supports up to 5. Attempting to activate a fourth group silently fails in older UI or throws a Setup error in newer UI. If a design genuinely requires 4–5 groups, open a Salesforce support case to raise the limit before the architecture is locked.
3. **Archived articles remain in SOSL results until re-index** — When an article is archived, it does not immediately disappear from search results in all contexts. Experience Cloud search may continue surfacing archived articles for minutes to hours depending on search index refresh timing. Agents may link archived articles to cases during this window. Build article lifecycle communications to manage agent expectations.
4. **Data Category visibility is separate from article Publication Status** — An article can be Published but invisible to an agent or portal user if their profile's Data Category visibility does not include the article's category. This is a common source of "I can't find the article I just published" support requests. Always verify Data Category Group Assignments and visibility rules together with publication tests.
5. **Search Activity Gaps uses a 90-day rolling window only** — The dashboard does not persist historical snapshots beyond the rolling 90-day window. If you want to track gap closure trends over quarters or demonstrate KCS ROI to leadership, you must export the gap list regularly and store it externally. There is no API to programmatically export Search Activity Gaps data; it is a UI-only dashboard.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Data Category Group layout | Spreadsheet or diagram mapping Group names, hierarchy levels, category nodes, and estimated article counts per node |
| Article lifecycle governance doc | Matrix of Publication Status × Validation Status × role permissions showing who can create, review, publish, and archive |
| KCS Solve/Evolve process definition | Step-by-step process guide for agents (Solve Loop) and domain experts (Evolve Loop) with entry/exit criteria per stage |
| Content gap baseline | Exported Search Activity Gaps list at taxonomy go-live, used as baseline for gap-closure measurement |
| Migration sequence plan | Ordered steps for re-assigning existing articles to new category structure, with Data Loader field mapping |

---

## Related Skills

- architect/knowledge-vs-external-cms — Use alongside when deciding whether content should live in Salesforce Knowledge vs an external CMS with CMS Connect; taxonomy design only applies once the Knowledge decision is confirmed
- architect/service-cloud-architecture — Taxonomy design feeds the knowledge deflection strategy section of a Service Cloud architecture engagement
- architect/ai-ready-data-architecture — When Agentforce or another RAG system will ground on Knowledge articles, the taxonomy and Validation Status design directly affects RAG retrieval quality
