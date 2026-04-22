---
name: tableau-salesforce-connector
description: "Tableau ↔ Salesforce integration patterns: Tableau Salesforce connector, Tableau for Salesforce, CRM Analytics alternative, Data Cloud + Tableau, embedded Tableau dashboards. Choose between connector modes (live, extract, direct-to-Data-Cloud). NOT for CRM Analytics Studio (use crm-analytics-foundation). NOT for generic Tableau Server setup."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Performance
  - Security
tags:
  - tableau
  - tableau-cloud
  - connector
  - data-cloud
  - reporting
  - embedded-analytics
  - crm-analytics
triggers:
  - "how do we connect tableau to salesforce for reporting"
  - "tableau salesforce connector live vs extract decision"
  - "tableau for salesforce vs crm analytics what to choose"
  - "embed tableau dashboards in salesforce record pages"
  - "tableau data cloud integration pattern"
  - "tableau salesforce api limits for reporting"
inputs:
  - Tableau edition (Tableau Cloud, Tableau Server, Tableau for Salesforce)
  - Reporting scope (operational, analytical, executive)
  - Data volume and refresh cadence needs
  - Embedding requirements (Salesforce record page, community, standalone)
outputs:
  - Connector mode recommendation (live / extract / Data Cloud)
  - API usage forecast against Salesforce limits
  - Embedding architecture (Tableau Viz / iframe / Tableau for Salesforce)
  - Refresh and governance plan
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Tableau ↔ Salesforce Connector

Activate when integrating Tableau (Cloud, Server, or Tableau for Salesforce) with Salesforce for reporting and dashboards. The connector has several modes with very different API-limit, freshness, and cost implications; choosing the wrong mode is a frequent source of silent throttling and stale dashboards.

## Before Starting

- **Distinguish Tableau for Salesforce from vanilla Tableau.** Tableau for Salesforce is a specific SKU with native record-page embedding (Tableau Viz LWC). Vanilla Tableau Cloud needs Connected App + iframe.
- **Measure the reporting surface.** A single executive dashboard refreshed daily is different from 50 operational dashboards with hourly refreshes. API budget is the governor.
- **Decide on governance.** Data Cloud + Tableau centralizes governance; raw Salesforce connector gives freshness but each dashboard is a bespoke SOQL payload.

## Core Concepts

### Connector modes

- **Live connection** — Tableau queries Salesforce via REST/SOQL on every view. Fresh but API-expensive.
- **Extract** — Tableau pulls periodically into a data extract (TDE / Hyper). Fast for users, older data, explicit refresh schedule.
- **Data Cloud → Tableau** — Data Cloud ingests Salesforce + other sources, Tableau queries Data Cloud's Hyper DB via Zero Copy.

### Tableau for Salesforce embedding

Tableau Viz LWC renders a Tableau dashboard on a Salesforce record page with context passing (e.g., AccountId to dashboard filter). Works with Tableau Cloud and Tableau Server. Requires Connected App setup.

### API limits

Live connections consume API calls and SOQL governor limits. A dashboard with many worksheets hits the API for each. Budget matters.

### Row-level security

Tableau RLS via user filters or Data Cloud sharing → differs from Salesforce sharing. Match Tableau security to Salesforce intent (or use CRM Analytics which inherits sharing natively).

## Common Patterns

### Pattern: Executive dashboards — extract-based

Daily extract of a curated dataset. Dashboards serve from the extract — fast, predictable, no API pressure. Refresh in off-hours.

### Pattern: Operational dashboards on record pages — Tableau for Salesforce + live

Tableau Viz LWC on Account page with live connection filtered by AccountId. User sees current data; API cost scoped to the single context.

### Pattern: Cross-source analytics — Data Cloud + Tableau Zero Copy

Data Cloud ingests Salesforce, marketing, external data. Tableau queries Data Cloud via Zero Copy. Centralized governance; decoupled from Salesforce API limits.

### Pattern: Hybrid — extract for base, live for drill

Base dashboard uses extract (speed). Drill-through opens a live-connected view (freshness on demand). Optimizes for most users while preserving on-demand freshness.

## Decision Guidance

| Scenario | Recommended Mode | Reason |
|---|---|---|
| Executive daily dashboard | Extract | API-light, user-fast |
| Embedded record page dashboard | Live + Tableau for Salesforce | Contextual freshness |
| Cross-source analytics | Data Cloud + Tableau | Governance, scale |
| Salesforce sharing fidelity required | CRM Analytics (alternative) | Native inheritance |
| High-volume operational (50+ live dashboards) | Data Cloud intermediary | Avoid API ceiling |

## Recommended Workflow

1. Classify each dashboard: audience, refresh cadence, embedding context.
2. Forecast API consumption per dashboard in live mode; compare against org API limit.
3. Choose connector mode per dashboard (not org-wide — it is per-workbook).
4. Configure Tableau Connected App + OAuth; set up Tableau for Salesforce if using Tableau Viz LWC.
5. Build one dashboard end-to-end; validate embedding, filters, security.
6. Establish extract refresh schedule; monitor refresh duration and failure rate.
7. Document governance: who publishes, who sees what, how row-level security is enforced.

## Review Checklist

- [ ] Per-dashboard mode decision documented
- [ ] API forecast within org limits with headroom
- [ ] Tableau Connected App + OAuth configured
- [ ] Tableau Viz LWC components tested on record pages
- [ ] Row-level security validated against Salesforce sharing intent
- [ ] Extract refresh monitoring in place
- [ ] Rollback plan if a dashboard causes API throttling

## Salesforce-Specific Gotchas

1. **Tableau live queries run SOQL that can exceed selectivity requirements.** Non-selective queries fail in large orgs regardless of API budget.
2. **Tableau Connected App uses OAuth 2.0; lifetime tokens must be scoped.** Over-scoped tokens expose data beyond the dashboard's purpose.
3. **Tableau for Salesforce uses cross-domain iframe — CSP and CORS matter.** Misconfiguration silently blanks the viz without surface errors.

## Output Artifacts

| Artifact | Description |
|---|---|
| Dashboard inventory with mode | Per dashboard: live / extract / Data Cloud |
| API consumption forecast | SOQL + REST call estimate |
| Embedding architecture | Tableau Viz LWC setup, CSP changes |
| RLS mapping | Salesforce sharing → Tableau user filters |

## Related Skills

- `data/data-cloud-foundation` — Data Cloud as analytical source
- `integration/integration-pattern-selection` — adjacent integration choices
- `data/crm-analytics-foundation` — alternative analytics path
