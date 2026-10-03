---
name: analytics-requirements-gathering
description: "Use this skill to elicit, document, and validate CRM Analytics requirements — covering data source mapping (Salesforce object sync vs external connector vs Data Cloud), transformation needs, audience-specific lens or dashboard views, and drill-down path specifications — before any dataset or dashboard is built. Trigger keywords: CRM Analytics requirements, analytics data source mapping, CRM Analytics audience requirements, analytics visualization requirements. NOT for the formula and target behind each KPI — use admin/analytics-kpi-definition. NOT for building the dashboard once requirements are agreed — use admin/analytics-dashboard-design."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "stakeholders have requested CRM Analytics dashboards but no requirements document exists yet"
  - "need to map which Salesforce objects and external sources will feed CRM Analytics datasets"
  - "different user roles need different views of the same data — need to document audience-specific requirements"
  - "analytics project kickoff needs to capture data source types, transformation needs, and drill-down paths"
  - "team needs to know if standard Reports can serve the need or if CRM Analytics is required"
  - "write the requirements for a CRM Analytics app before anyone builds a dataset"
  - "decide who sees which rows in a CRM Analytics dashboard"
tags:
  - crm-analytics
  - requirements-gathering
  - analytics-requirements
  - data-source-mapping
  - analytics-requirements-gathering
inputs:
  - "List of stakeholder reporting needs and questions the analytics should answer"
  - "User roles and personas who will use the analytics"
  - "Data sources: Salesforce objects, external files, Data Cloud DMOs"
  - "Existing report or dashboard examples that show what stakeholders want"
outputs:
  - "CRM Analytics requirements document with data source inventory"
  - "Audience matrix mapping user roles to specific lens or dashboard views"
  - "Data transformation requirements for dataflow/recipe design"
  - "Decision record: CRM Analytics vs standard Reports"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
runtime_orphan: true
runtime_orphan_reason: "No run-time agent covers CRM Analytics / Einstein Discovery. This skill was previously listed in audit-router's Mandatory Reads, but no audit-router classifier routes to it and report_dashboard's own scope excludes CRM Analytics migration, so the citation was decorative rather than load-bearing. Removed 2026-08-14 rather than left as a citation an agent never honoured. Re-wire when a CRM Analytics agent exists."
---

# Analytics Requirements Gathering

This skill activates when a practitioner needs to gather, document, and validate CRM Analytics requirements before any dataset, dataflow, or dashboard is built. It produces a requirements package: data source inventory, audience matrix, transformation requirements, refresh budget, and drill-down specifications. The analytics developer uses it as the authoritative spec.

---

## Before Starting

Gather this context before working on anything in this domain:

- Decide first whether stakeholders need CRM Analytics or standard Reports and Dashboards. CRM Analytics fits cross-object aggregation, external data, predictive insight, and multi-audience row-level security. For single-object reporting with no external data, standard Reports are the cheaper choice.
- Confirm the org's CRM Analytics platform license. The Analytics Platform Setup Guide states several limits per license (for example, concurrent dataflow runs differ between CRM Analytics Plus and CRM Analytics Growth), so the license shapes the refresh plan, not only the price.
- Synced Salesforce objects land as connected objects. The CRM Analytics REST API guide states that connected objects "can't be visualized directly"; a recipe or dataflow must build a dataset from them.
- Capture the source type of every input (Salesforce local sync, external connection, Data Cloud, CSV upload). The type decides the extraction path, the limits that apply, and whether a recipe or dataflow is needed.

---

## Questions to Ask Before Configuring

Ask these before anyone designs a dataset. Each one traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Which questions must the analytics answer, and could a standard report answer them?" | CRM Analytics costs licenses and build effort; some needs fit Reports | A documented platform decision with its reason | No dashboard built on a license the need did not justify |
| "Who may see which rows, and is that the same as their Salesforce record access?" | A dataset without row-level security shows every row to anyone with dataset access (gotcha 3) | An audience matrix with a predicate or sharing-inheritance choice per role | Row-level security designed before the first dataset exists, not retrofitted |
| "How fresh must each source be, and what other dataflows and recipes already run?" | Dataflow and recipe runs share a 60-run rolling 24-hour limit (gotcha 5) | A refresh cadence per source that fits the run budget | Schedules that keep running instead of being refused at the daily limit |
| "Which exact fields does each source need, including fields that hold sensitive data?" | The Integration User extracts data; a job fails on fields it cannot read (gotcha 2) | A field list checked against the Integration User's access | A first run that succeeds, and sensitive fields excluded on purpose |
| "Do predicates need custom User fields such as region or territory?" | The Security User must be able to read every User field a predicate references (gotcha 6) | The User fields named in the requirement | Predicates that query without errors on day one |
| "Is any source outside this Salesforce org (another org, a warehouse, Data Cloud)?" | External and output connections count against org limits differently from the local connection (gotcha 7) | A source-type column in the data source matrix | A refresh plan that does not surprise the integration team |

What a proper requirements package adds over "just building a dashboard": a platform decision that can be defended, a row-level security model per audience, and a refresh plan that fits the org's run limits.

---

## Core Concepts

### Data Source Types

| Source type | Setup | Grounding |
|---|---|---|
| Salesforce local sync | Data sync loads source objects as connected objects; a recipe or dataflow builds the dataset | REST guide: connected objects "can't be visualized directly" |
| External connection | Connector and credentials; data synced as connected objects, then prepared by a recipe | REST guide, Replicated Dataset resources |
| Data Cloud | UNVERIFIED (2026-10-03): direct query of Data Cloud objects without a dataset, and its SAQL limits, are help-only claims not re-read in this pass | None in fetched guides |
| CSV upload | Creates a dataset directly; upload with metadata for row-level security | Security guide: predicate in the external data metadata file |

Requirements must name the type of every source. The implementation path differs per type.

### Audience-Specific Views

CRM Analytics separates two access layers, and requirements must state both:

| Layer | What it controls | How it is configured |
|---|---|---|
| App sharing | Who can open the app and its dashboards and datasets | `WaveApplication` shares with View, EditAllContents, or Manage access to users, groups, or roles |
| Row-level security | Which rows each user sees in a dataset | A security predicate on the dataset, or sharing inheritance from Salesforce objects |

Sharing inheritance increases sync, job, and query time, and the more complex the sharing settings, the larger the impact (Analytics Security Implementation Guide).

### Transformation Requirements

Raw object data usually needs work before it is useful:

- field renames for consistent naming across datasets
- computed fields (revenue tiers, fiscal period labels, region groupings)
- dataset joins, with the join type stated (keep every primary row, or only matches)
- date dimension derivations (fiscal year and quarter from `CloseDate`)

Requirements must specify each transformation. The developer cannot infer them from field names.

---

## Common Patterns

### Pattern: Data Source Mapping Matrix

**When to use:** At the start of every CRM Analytics requirements engagement.

**How it works:**
1. List every data source the analytics needs.
2. For each source record the type, the connection, the fields needed, and the refresh cadence.
3. For Salesforce objects list fields, not just objects; extra fields lengthen sync and recipe runs.
4. For external sources confirm the connector and credentials exist or are in scope.

### Pattern: Audience Matrix

**When to use:** More than one role will use the analytics and they should see different rows or layouts.

**How it works:**
1. List every role or persona.
2. For each role record which rows they may see (own records, team, territory, all).
3. Record whether they need a different dashboard layout or the same dashboard filtered.
4. Name the mechanism per role: security predicate, sharing inheritance, or app sharing only.

The worked artifact, an audience matrix turned into deployable app sharing and a dataset predicate, is in `references/metadata-examples.md`.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single-object reporting with filters and grouping | Standard Reports and Dashboards | No CRM Analytics license required |
| Cross-object aggregation (Opportunity, Account, Activity) | CRM Analytics | Recipes join datasets and persist the result |
| Predictive scoring or trend analysis | CRM Analytics with Einstein Discovery | Predictive features need the CRM Analytics license |
| Data from an external warehouse | CRM Analytics external connection | External data cannot feed standard Reports |
| Different rows for VP and individual rep | Security predicate or sharing inheritance on the dataset | App sharing alone controls access to the app, not rows |
| Frequent refresh on many sources | Plan the run budget first | 60 dataflow and recipe runs per rolling 24 hours, shared |

---

## Recommended Workflow

1. **Qualify the platform decision.** Decide CRM Analytics or standard Reports, write the reason down, and confirm the CRM Analytics license.
2. **List the reporting questions.** Every dataset and dashboard must trace to a question.
3. **Build the data source matrix.** For each question identify the source, its type, the exact fields, and the refresh cadence. Check the fields against the Integration User's access.
4. **Document transformations.** Joins with their type, computed fields, date derivations, and renames.
5. **Build the audience matrix.** Roles, the rows each may see, the predicate or sharing-inheritance choice, and any custom User fields the predicates need.
6. **Budget the refreshes.** Count every scheduled dataflow and recipe that runs longer than two minutes against the 60-run rolling 24-hour limit.
7. **Review with stakeholders and the developer.** Confirm the package is complete and buildable, then hand off with `references/metadata-examples.md` as the configuration target.

---

## Review Checklist

- [ ] CRM Analytics vs standard Reports decision documented with rationale
- [ ] CRM Analytics license confirmed
- [ ] Every data source has a type (local sync / external / Data Cloud / CSV)
- [ ] Field-level requirements per source, checked against the Integration User
- [ ] Transformation requirements specified (joins with type, computed fields, date dimensions)
- [ ] Audience matrix complete with a row-level security mechanism per role
- [ ] Custom User fields used in predicates listed for the Security User
- [ ] Refresh cadence per source fits the 60-run daily budget
- [ ] Drill-down paths documented for each summary visualization

---

## Salesforce-Specific Gotchas

The deep versions, with sources, live in `references/gotchas.md`.

| # | Gotcha | One-line consequence |
|---|---|---|
| 1 | Connected objects can't be visualized directly | A requirement that stops at "sync Opportunity" has no dataset |
| 2 | The Integration User decides what can be extracted | Jobs fail on unreadable fields |
| 3 | No predicate means every row for everyone with access | A shared dashboard leaks rows |
| 4 | Sharing inheritance costs job and query time | Heavy sharing slows every refresh |
| 5 | 60 dataflow and recipe runs per rolling 24 hours | Aggressive cadences block other jobs |
| 6 | The Security User must read predicate User fields | Queries error when a custom User field is unreadable |
| 7 | External and output connections count against org limits | Integration budgets are hit unexpectedly |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| CRM Analytics requirements document | Questions, data source inventory, transformations, audience matrix, drill-down paths |
| Data source mapping matrix | Per-source type, connection, fields, refresh cadence |
| Audience matrix | Roles mapped to app sharing and row-level security |
| Refresh budget | Scheduled jobs counted against the 60-run daily limit |
| CRM Analytics vs Reports decision record | Decision with rationale and license confirmation |

---

## Related Skills

- `admin/analytics-kpi-definition`: define KPI formulas and targets after requirements are gathered
- `admin/saql-query-development`: downstream implementation using this document
- `admin/requirements-gathering-for-sf`: general Salesforce requirements gathering companion
- `admin/analytics-recipe-design`: turns the transformation requirements into a recipe
