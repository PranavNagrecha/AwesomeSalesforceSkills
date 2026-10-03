---
name: large-data-volume-architecture
description: "Use when designing or reviewing org-wide large data volume (LDV) concerns: query optimizer behavior and selectivity, custom indexes and skinny tables, sharing and ownership skew, bulk data loads, archival to Big Objects, and divisions. Triggers: LDV architecture review, skinny table request, ownership skew hurting sharing, millions of records on custom object, bulk load performance, 40 million rows on one object and queries crawl, tens of millions of records and everything is slow, object has grown too large and reports time out. NOT for rewriting individual SOQL statements or interpreting Query Plan output in isolation (use data/soql-query-optimization), sales-only Opportunity and Account skew playbooks (use architect/high-volume-sales-data-architecture), or Marketing Cloud data extensions."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Scalability
  - Reliability
tags:
  - large-data-volume-architecture
  - ldv
  - skinny-tables
  - custom-index
  - data-skew
  - sharing-performance
  - big-objects
  - bulk-load
  - selectivity
triggers:
  - "we need an LDV architecture review before our data grows further"
  - "ownership skew is slowing sharing recalculation across the org"
  - "should we request skinny tables or custom indexes for our custom object"
  - "millions of records on a custom object and reports are degrading"
  - "bulk load into salesforce is taking too long and hitting sharing limits"
  - "check whether our report filters are selective enough to use a custom index"
  - "plan moving old records off a 60 million row object without breaking reports"
inputs:
  - "Approximate record counts per high-volume object and monthly growth"
  - "Ownership distribution (especially any user or integration user near or above 10,000 owned records)"
  - "Which filters drive reports, list views, integrations, and batch jobs"
  - "Current sharing model complexity (roles, public groups, criteria-based rules)"
outputs:
  - "Index and skinny-table request strategy grounded in selectivity math"
  - "Skew and sharing remediation plan (ownership, parent-child distribution, deferral options)"
  - "Archival or Big Object boundary recommendation for cold data"
  - "Bulk load sequencing checklist (rules, triggers, sharing deferral)"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Large Data Volume Architecture

This skill activates when an org crosses the threshold where default Salesforce patterns stop scaling: reports slow down, sharing jobs queue, integrations time out, or bulk loads stall. It focuses on **architectural** levers the platform exposes—indexes, skinny tables, skew avoidance, sharing deferral, divisions, and Big Object boundaries—not on polishing a single SOQL string.

Large data volume is elastic in official documentation: the LDV guide names tens of thousands of users, tens of millions of records, or hundreds of gigabytes of total record storage. Even smaller orgs benefit once any one object crosses roughly one hundred thousand rows and operations become sensitive to selectivity and sharing cost.

---

## Before Starting

Gather this context before working on anything in this domain:

- What are the top five objects by row count, and which ones are still growing quickly?
- For those objects, who owns the rows? Is any single user (including an API or integration identity) approaching or exceeding ten thousand owned records?
- Which indexed fields appear in the WHERE clauses of reports, list views, batch Apex, and integrations? Are filters selective per the platform’s standard and custom index rules?
- Do you need transactional behavior on all historical rows, or can cold data move to Big Objects or external stores?

---

## Questions to Ask Before Configuring

Ask these before requesting an index, a skinny table, or a load window. Each traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What a proper design adds over just doing it |
|---|---|---|---|
| "What are the exact filters on the slow reports, list views, batch jobs, and integrations, including OR and LIKE?" | OR needs every field indexed; LIKE samples 100,000 rows (Gotchas 1 and 2) | A filter inventory per heavy path | Index requests target the filters that actually run |
| "How many rows match each filter value today, and how many rows does the object hold?" | Custom indexes need under 10% of the first million and 5% of the rest (Gotcha 4) | Distribution counts and the threshold for this row count | Selectivity is proven before Support is engaged |
| "Do any filters test for blank values, formulas, or special standard fields?" | Index tables omit nulls; non-deterministic formulas and fields like `Opportunity.Amount` cannot be indexed (Gotchas 5 and 6) | A list of filters that need a materialized field or a null-inclusive index | No Support case for an index the platform cannot build |
| "Who owns the rows, and which parents have the most children?" | Keep owners and parents under 10,000 records each (Gotcha 8) | Owner and parent distribution | Sharing and locking cost fall without buying hardware |
| "Which sandbox will performance testing run in?" | Skinny tables copy only to Full sandboxes (Gotcha 7) | A test environment that matches production access paths | Test results mean something |
| "What leaves the object, how, and in what order?" | Million-row deletes need Bulk API hard delete, children first; big extracts belong in Bulk API 2.0 (Gotchas 9 and 10) | An archive, delete, and extract plan | Retention purges and extracts finish inside their windows |

What a proper LDV design adds over "just asking Support for an index": thresholds computed for the real row count, filters rewritten where no index can help, skew removed at the source, and every Support request backed by distribution evidence.

---

## Core Concepts

### Selectivity and the Query Optimizer

Reports, list views, and SOQL all flow through the Lightning Platform query optimizer. The optimizer chooses indexes, join order, and how to minimize I/O—including **sharing joins**. For standard indexed fields, an index can drive the query when the filter matches less than thirty percent of the first million rows and less than fifteen percent of additional rows, capped at one million matching rows (UNVERIFIED 2026-10-03: the cap is not in the current LDV guide's threshold section). Correction (2026-10-03): for custom indexed fields, earlier text said the filter must match less than ten percent of total rows with a 333,333-row ceiling. The current LDV guide says less than ten percent of the first million rows and less than five percent of additional rows (5 million rows allows 300,000 matches). For AND, the optimizer uses the indexes unless one returns more than 20% of rows; for OR, unless they all return more than 10%, and every field in the OR must be indexed.

Practitioners should measure distribution with aggregate queries (for example, GROUP BY on filter fields) rather than guessing, then check the plan the optimizer would choose with the REST API `explain` parameter (Beta; REST API Developer Guide, "Get Feedback on Query Performance (Beta)"). Deleted rows affect statistics—exclude them when measuring if your org uses soft delete in queries (UNVERIFIED 2026-10-03).

### Skinny Tables

Skinny tables are optional, read-optimized physical row sets that duplicate a subset of columns from a wide object so read operations avoid joining the standard and custom field storage shapes. They are created only through Salesforce Customer Support, apply to Account, Contact, Opportunity, Lead, Case, and custom objects, support up to two hundred columns from the allowed field types (checkbox, currency, date, date/time, email, number, percent, phone, multi-select picklist, text, text area, long text area, URL), cannot include fields from other objects, omit soft-deleted records, and are synchronized when source rows change. They are not copied to non-Full sandboxes unless Support activates them, and Salesforce must update the definition when the report or query they serve changes (LDV guide, "Skinny Tables"). They help read-heavy workloads on millions of rows but add maintenance overhead—use them when measured join cost is the bottleneck, not as a default.

### Skew, Sharing, and Bulk Operations

**Ownership skew** (typically a single owner beyond roughly ten thousand records on an object) increases sharing calculation cost. **Parent-child skew** (very large related lists under one parent; the LDV guide says no parent should have more than 10,000 children) hurts UI and query latency and raises locking conflicts during loads. The LDV guide recommends deferring or sequencing sharing calculation, disabling Apex triggers and validations during massive loads when appropriate, using Batch Apex afterward, and avoiding unnecessary sharing work during initial seed loads—for example using wider org-wide defaults temporarily during controlled migrations then tightening.

Big Objects are the platform’s native store for billions of immutable rows; the LDV paper focuses on standard and custom objects and points to Bulk API and Batch Apex to land historical data in Big Objects for sustainable scale.

---

## Common Patterns

### Measure, Then Index or Skinny

**When to use:** A high-volume object drives reports or integrations and WHERE clauses are known.

**How it works:** Run distribution queries to prove selectivity. If filters cannot meet standard or custom thresholds, add External Id where applicable, request a custom index or two-column index, or—when the object is wide and read-mostly—open a support case for skinny tables after confirming only supported field types are needed.

**Why not the alternative:** Adding fields or dashboards without changing access paths increases full scans and sharing join cost.

### Redistribute Ownership and Narrow Sharing Rules

**When to use:** Sharing recalculation or row-level security jobs lag, especially after loads or role changes.

**How it works:** Split integration-owned rows across queue-based or role-aligned owners, break mega-parent hierarchies where the business allows, reduce criteria-based rule fan-out, and use documented deferral options for bulk cutovers.

**Why not the alternative:** More CPU on the same skewed ownership model yields diminishing returns.

### Archive Cold Data to Big Objects

**When to use:** Historical rows are rarely updated but still consume query and storage headroom.

**How it works:** Define a retention boundary, use asynchronous bulk movement into a Big Object, and point analytics or compliance reads at the archive. Keep transactional paths on the core object.

**Why not the alternative:** Keeping decades of detail on the transactional object preserves convenience but eventually breaks selectivity and user experience.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Filters cannot meet index selectivity thresholds | Redesign filters, add selective conjunctions, External Id, or custom index via Support / Metadata API | Non-selective paths force expensive scans |
| Object has very wide row shape and read-heavy reporting | Evaluate skinny table case with Support after column list is stable | Removes join between standard and custom storage for supported reads |
| Single owner or parent dominates row counts | Redistribute ownership or split logical parents | Lowers sharing and related-list cost per LDV skew guidance |
| Initial multi-million-row load | Sequence users/roles, owners, groups, rules; defer sharing; disable automation where safe | Reduces recomputation during load |
| Cold historical data rarely touched | Big Object archive with Bulk API / Batch Apex | Frees transactional object for selective workloads |

---

## Recommended Workflow

1. Inventory objects over roughly one hundred thousand rows and classify each as transactional, reporting, or archival.
2. For each hot object, chart owner distribution and top parent-child counts to locate skew.
3. Capture the exact filters used in reports, list views, batch jobs, and integrations; validate selectivity with aggregate SOQL.
4. Decide among filter redesign, custom index, two-column index, skinny table, sharing changes, or archival—document tradeoffs and support tickets required.
5. For loads or reorganizations, produce a sequencing plan (automation off, defer sharing where approved, validate post-load).
6. Re-measure after changes using the same queries and operational metrics.

---

## Review Checklist

- [ ] Row counts and growth rates documented for high-volume objects
- [ ] No undiagnosed ownership or parent-child skew above platform guidance thresholds
- [ ] Filters on heavy paths meet documented selectivity rules or have a remediation plan
- [ ] Skinny table or index requests include field lists, read/write profile, and sandbox type implications
- [ ] Archival boundaries and Big Object keys defined if cold data leaves transactional tables

---

## Salesforce-Specific Gotchas

1. **Custom indexes are not always self-service** — Support or Metadata API paths apply depending on field type; some field types cannot be indexed at all. The Metadata API `CustomIndex` type (API 50.0+) still requires contacting Support, and External ID fields (Auto Number, Email, Number, Text) get an index automatically.
2. **Skinny tables in Developer and partial sandboxes** — Only Full sandboxes copy skinny tables; other sandboxes do not, which can make performance testing asymmetrical.
3. **Optimizer thresholds differ for AND vs OR** — OR requires each side to be selective; naive dynamic SOQL that ORs many branches often defeats indexes.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| LDV assessment summary | Object inventory, skew findings, and filter selectivity notes |
| Platform request package | Column lists and justification for Support-driven skinny tables or special indexes |
| Load runbook | Ordered steps for bulk migration with automation and sharing considerations |

---

## Related Skills

- `data/soql-query-optimization` — Line-level SOQL tuning, Query Plan interpretation, and immediate query fixes
- `architect/high-volume-sales-data-architecture` — Sales-cloud-specific skew, pipeline reporting, and Opportunity archival patterns
- `data/external-data-and-big-objects` and `data/data-archival-strategies`: Big Object mechanics and archive design when archival is the focus (the local corpus also carries `knowledge/imports/salesforce-big-objects-guide.md`)
- `data/bulk-api-and-large-data-loads`: load sequencing, hard delete, and Bulk API 2.0 extracts
- `standards/decision-trees/performance-tuning.md`: read first when the symptom is "slow" and the cause is not yet known
