---
name: crm-analytics-vs-tableau-decision
description: "Use when deciding between CRM Analytics (formerly Einstein Analytics / Tableau CRM) and Tableau Desktop, Tableau Server, or Tableau Cloud for a Salesforce-centric analytics requirement. Triggers: 'CRM Analytics vs Tableau', 'which BI tool for Salesforce', 'Tableau for Salesforce data', 'Einstein Analytics vs Tableau', 'analytics platform decision', 'licensing comparison CRM Analytics Tableau', 'Tableau Next', 'Tableau+ for Salesforce'. NOT for implementation guidance on configuring CRM Analytics datasets, recipes, or Tableau workbooks — use admin/einstein-analytics-basics for that."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Scalability
  - Operational Excellence
triggers:
  - "Should we use CRM Analytics or Tableau for our Salesforce reporting and dashboards?"
  - "Which BI tool is better for Salesforce data — CRM Analytics or Tableau?"
  - "Our org has Tableau and Salesforce — should we use Tableau for Salesforce analytics or switch to CRM Analytics?"
  - "What is the licensing difference between CRM Analytics and Tableau?"
  - "Can Tableau connect to Salesforce data in real time?"
tags:
  - crm-analytics
  - tableau
  - decision-framework
  - architect
  - licensing
  - bi
inputs:
  - "Business analytics requirement and primary data sources (Salesforce-only vs multi-system)"
  - "Freshness requirement (real-time, near-real-time, daily batch)"
  - "Audience (Salesforce users, data analysts, external stakeholders)"
  - "Existing Salesforce license tier and org edition"
  - "Existing Tableau investment (Tableau Server / Tableau Cloud / Tableau Next)"
  - "Row-level security requirements and Salesforce sharing model constraints"
outputs:
  - "Platform recommendation (CRM Analytics, Tableau, or both) with documented rationale"
  - "Licensing model summary and cost-driver comparison"
  - "Integration depth analysis (live Salesforce data vs extract)"
  - "Decision record suitable for architecture review"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# CRM Analytics vs Tableau — Decision Framework

Use this skill when an architecture decision is needed between Salesforce CRM Analytics and Tableau (Desktop, Server, Cloud, or Tableau Next). It produces a documented, rationale-grounded recommendation. It does NOT guide implementation of either platform.

---

## Before Starting

Gather this context before making any recommendation:

- What is the primary data source — Salesforce objects only, or a mix that includes data warehouses, ERP, marketing platforms, or other non-Salesforce systems?
- What is the required data freshness — true real-time (sub-minute), near-real-time (minutes to hours), or scheduled daily/weekly batch?
- Who is the audience — Salesforce-licensed users working inside Lightning pages, or data analysts and business users who operate outside Salesforce?
- Does the requirement involve enforcing the Salesforce sharing model (record-level security tied to OWD, sharing rules, or profile visibility) in the analytics layer?
- What Salesforce edition and existing license inventory is in place? CRM Analytics requires specific Permission Set Licenses (Growth, Plus, or Einstein 1 editions).
- Does the organization have an existing Tableau investment — Tableau Server on-premise, Tableau Cloud, or Tableau Next (Tableau+ SKU)?

---

## Core Concepts

### CRM Analytics: Salesforce-Native Embedded Analytics

CRM Analytics (formerly Einstein Analytics, formerly branded as Tableau CRM — see gotchas) is Salesforce's native analytics platform embedded directly in the Salesforce org. It queries Salesforce data through datasets that sync from the org's objects, and uses SAQL (Salesforce Analytics Query Language) for computation. Because it runs inside the Salesforce trust boundary, it can enforce the Salesforce sharing model at dataset row level, embed dashboards directly into Lightning record pages and app pages, and be assigned through Salesforce Permission Set Licenses (PSLs). Data access is governed by the same profile and permission set stack as the rest of the org.

CRM Analytics is the right primary choice when: the data is predominantly Salesforce objects, the audience is Salesforce-licensed users, embedding in Lightning is a requirement, or the sharing model must govern analytical row-level access without a separate ETL security sync.

### Tableau: Multi-Source Enterprise BI via Connector Extract

Tableau (Desktop, Server, Cloud, and Tableau Next) is a separate Salesforce product with its own license model (Creator, Explorer, Viewer roles, or Tableau+ capacity model). The native Salesforce connector for Tableau operates as an **extract connector** — it pulls data from Salesforce into a Tableau extract on a scheduled refresh cadence. It does not provide a live query connection to Salesforce objects.

Key connector constraints that architects must know:
- **Extract-only**: Tableau's Salesforce connector does not support live/direct query against Salesforce. Every dashboard reflects the most recent extract, not current record state.
- **30-day lookback cap on incremental refresh**: Incremental extract refreshes using the connector are capped at a 30-day lookback window. Rows modified beyond that window are not re-fetched unless a full extract runs.
- **No Custom SQL**: The Salesforce connector does not support Custom SQL queries, unlike most database connectors in Tableau. Data shaping must happen before Tableau or through Tableau Prep.
- **10,000-character API query limit**: The connector enforces a 10,000-character limit on the underlying Salesforce API query string, which constrains complex multi-field SOQL expressions passed through the connector.

These constraints mean that Tableau is not a suitable replacement for real-time Salesforce operational analytics or use cases requiring immediate record-level visibility. It is the right choice when the requirement is cross-system BI across Salesforce and non-Salesforce data sources, or when a large existing Tableau investment is already in place.

### Tableau Next (Tableau+ SKU): Forward Path for Enterprise and Agentic BI

Tableau Next, sold as the Tableau+ SKU, reached general availability in June 2025. It is the strategic forward path for organizations combining Tableau with Salesforce's Agentforce platform and Data 360. Tableau Next introduces agentic BI capabilities, Agentforce integration for natural-language analytics queries, and tighter coupling with the Salesforce data platform (including Data Cloud / Data 360). Architects evaluating long-term platform strategy for enterprise orgs with significant Salesforce investment and complex multi-source analytics should include Tableau Next in the evaluation rather than treating Tableau as a static product.

### Licensing: Two Completely Different Models

CRM Analytics licensing is additive to the Salesforce org license. Users need a Salesforce user license plus a CRM Analytics Permission Set License (PSL). PSLs are assigned per user inside the org, and access is managed through Salesforce permission sets — not a separate user directory. The PSL tier (Growth vs Plus) determines which CRM Analytics features the user can access.

Tableau licenses are entirely separate from the Salesforce org. Tableau uses a Creator / Explorer / Viewer role model for Tableau Server and Tableau Cloud, or a capacity-based model under Tableau+. Tableau users do not need Salesforce licenses, and Salesforce users do not automatically have Tableau access. This separation is both a cost implication (two independent license stacks) and an access management concern (two separate user directories to keep in sync).

---

## Decision Guidance

| Situation | Recommended Platform | Reason |
|---|---|---|
| All data lives in Salesforce objects; audience are Salesforce users | CRM Analytics | Native access, no extract lag, shares Salesforce security model |
| Dashboards must be embedded in Lightning record pages or App Builder | CRM Analytics | Tableau cannot be natively embedded in Lightning without separate iFrame/Salesforce integration |
| Row-level security must mirror Salesforce OWD and sharing rules | CRM Analytics | Dataset row-level security can enforce Salesforce sharing model; Tableau extracts lose this enforcement |
| Data sources include external data warehouse, ERP, or marketing cloud | Tableau | Multi-source connectivity is Tableau's core strength; CRM Analytics is optimized for Salesforce data |
| Near-real-time (sub-hourly) Salesforce data required | CRM Analytics | Tableau Salesforce connector refreshes are scheduled extract jobs; no live query |
| Audience is primarily data analysts outside Salesforce who own complex self-service BI | Tableau | Creator/Explorer model fits analyst-led workbook authoring better than Salesforce PSL model |
| Organization has large existing Tableau Server investment | Tableau (extend existing) | Rationalizing onto existing licensed infrastructure avoids dual licensing cost |
| Enterprise org needs Agentforce-integrated analytics and Data 360 strategy | Tableau Next (Tableau+) | Tableau Next is the Agentforce-native BI forward path as of June 2025 |
| Salesforce data freshness beyond 30 days in incremental refresh | CRM Analytics | Tableau Salesforce connector incremental refresh has 30-day lookback cap |
| Complex SOQL with many fields needed to drive analytics | CRM Analytics | Tableau Salesforce connector has 10,000-character API query limit and no Custom SQL |

---

## Common Patterns

### Pattern: Hybrid Architecture (CRM Analytics + Tableau)

**When to use:** The org needs both Salesforce-native operational dashboards for sales and service teams inside Lightning, and enterprise cross-system BI for finance or data science teams who work outside Salesforce.

**How it works:**
1. CRM Analytics serves the Salesforce-embedded experience: pipeline dashboards in the Sales App, service metrics embedded on Account record pages, mobile-accessible KPI decks for field teams.
2. Tableau connects to the data warehouse (Snowflake, Databricks, Redshift) for cross-system reporting: blended revenue analytics combining Salesforce opportunity data (extracted nightly) with ERP actuals and marketing attribution.
3. Overlap is minimized by agreeing on a "Salesforce operational BI" boundary owned by CRM Analytics and an "enterprise strategic BI" boundary owned by Tableau.

**Why not Tableau for everything:** Tableau's Salesforce connector extract lag and 30-day lookback cap make it unsuitable for the operational, real-time Salesforce reporting that sales and service teams depend on daily.

### Pattern: CRM Analytics for Regulated Sharing Model Enforcement

**When to use:** The org has complex record-level security — territory hierarchies, account team sharing, custom sharing rules — and the analytics must respect those boundaries without duplicating security logic in Tableau.

**How it works:**
1. Datasets in CRM Analytics are configured with row-level security predicates that reference the Salesforce sharing model.
2. Users see only the records their Salesforce profile and permission sets allow — the same data they would see in a standard Salesforce report.
3. There is no separate ETL job to replicate security groups into Tableau row filters.

**Why not Tableau:** Tableau extracts do not carry Salesforce record-level sharing metadata. Replicating that security in Tableau requires a custom row-level security implementation that must be kept in sync with every Salesforce sharing rule change — a high-maintenance and error-prone approach.

---

## Recommended Workflow

1. **Clarify data topology first** — determine whether the data is Salesforce-only or multi-source before any platform discussion. Multi-source requirements immediately widen the evaluation toward Tableau.
2. **Confirm freshness requirement against connector constraints** — if near-real-time Salesforce data is required, document that Tableau's Salesforce connector is extract-only and cannot meet that requirement; CRM Analytics must be the answer for that use case.
3. **Map the audience and license inventory** — identify whether the analytics consumers are Salesforce-licensed users (CRM Analytics PSL path) or independent analysts (Tableau Creator/Explorer path), and confirm what licenses are already owned.
4. **Assess sharing model enforcement need** — if row-level security must mirror Salesforce OWD or sharing rules, CRM Analytics is the only viable native option without a custom Tableau RLS implementation.
5. **Check for existing Tableau investment** — if a Tableau Server or Tableau Cloud contract is already in place, rationalize onto that infrastructure for non-Salesforce use cases before adding CRM Analytics licensing cost.
6. **Evaluate Tableau Next (Tableau+) if the org has an Agentforce or Data 360 roadmap** — for orgs building toward Agentforce-integrated analytics, Tableau Next is the GA forward path as of June 2025 and should be included in the architectural evaluation.
7. **Document the decision record** — produce a written rationale using the decision template, including data sources, freshness requirements, audience, license model, and the specific connector constraints that drove the recommendation.

---

## Review Checklist

Run through these before finalizing the decision recommendation:

- [ ] Confirmed whether Salesforce data is the only source or whether non-Salesforce systems are in scope
- [ ] Confirmed the Tableau Salesforce connector's extract-only nature has been communicated if Tableau is evaluated
- [ ] Confirmed the 30-day incremental refresh lookback cap has been noted if Tableau is evaluated for Salesforce-heavy use cases
- [ ] Confirmed whether row-level security must mirror the Salesforce sharing model
- [ ] Confirmed which platform licenses are already owned and whether dual licensing is acceptable
- [ ] Confirmed whether the org has an Agentforce or Data 360 roadmap that changes the Tableau Next evaluation
- [ ] Decision record produced and grounded in documented platform constraints (not just preference)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **"Tableau CRM" is a deprecated marketing name for CRM Analytics** — Salesforce rebranded "Einstein Analytics" to "Tableau CRM" (circa 2020) and then rebranded again to "CRM Analytics" (circa 2022). "Tableau CRM" is not the same product as Tableau Desktop, Tableau Server, Tableau Cloud, or Tableau Next. Conflating these names leads to incorrect license procurement and wrong architectural decisions.
2. **Tableau's Salesforce connector is extract-only, not live** — The native connector does not support live/direct query against Salesforce. Stakeholders expecting real-time Salesforce data in Tableau dashboards will be disappointed at the first refresh cycle. This must be surfaced in the decision, not discovered post-deployment.
3. **30-day incremental refresh lookback cap** — Tableau's incremental refresh on the Salesforce connector only re-fetches records modified in the last 30 days. Historical changes beyond that window are not re-synced unless a full extract runs. This makes Tableau unsuitable for use cases that need historical accuracy without scheduled full refreshes.
4. **CRM Analytics PSL assignments are separate from Salesforce user licenses** — Simply having a Salesforce license does not grant CRM Analytics access. Each user who needs CRM Analytics access requires an explicit Permission Set License assignment. Large rollouts that skip license planning break on day one of go-live.
5. **Tableau Next (Tableau+) is not the same as the legacy Tableau Creator role** — Tableau Next is a new SKU with capacity-based pricing and Agentforce integration, GA as of June 2025. Organizations on legacy Tableau Creator/Explorer/Viewer contracts are not automatically upgraded to Tableau Next capabilities.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Platform recommendation | Written decision (CRM Analytics, Tableau, or hybrid) with documented rationale against the decision criteria |
| Licensing model comparison | Side-by-side summary of CRM Analytics PSL model vs Tableau Creator/Explorer/Viewer or Tableau+ model |
| Connector constraint summary | Documented Tableau Salesforce connector limits (extract-only, 30-day cap, no Custom SQL, 10,000-char limit) relevant to the specific use case |
| Decision record | Template-based artifact suitable for architecture review board or design authority submission |

---

## Related Skills

- **admin/einstein-analytics-basics** — Use for implementation guidance on CRM Analytics datasets, recipes, dataflows, and dashboard design. This decision skill stops at the recommendation; einstein-analytics-basics covers the build.
- **architect/insurance-cloud-architecture** — Use when the analytics decision is happening inside an Insurance Cloud or Financial Services Cloud org where industry data model constraints affect the platform choice.
- **data/industries-data-model** — Use when the analytics data sources include Industry Cloud objects and you need to understand the data model before evaluating CRM Analytics dataset design.
