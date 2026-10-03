---
name: high-volume-sales-data-architecture
description: "Use when designing or reviewing Salesforce orgs with large Opportunity and Account volumes, including archival strategy, report performance, data skew prevention, SOQL tuning for sales queries, and index planning. Triggers: 'opportunity table is slow', 'account ownership skew', 'sales report timing out', 'archive old opportunities'. NOT for org-wide LDV design on non-sales objects - use architect/large-data-volume-architecture. NOT for tuning one query or reading a Query Plan - use data/soql-query-optimization."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Scalability
  - Reliability
tags:
  - high-volume-sales-data-architecture
  - data-skew
  - opportunity-archival
  - report-optimization
  - soql-performance
  - skinny-tables
  - big-objects
triggers:
  - "opportunity queries are slow and we have millions of records"
  - "account ownership skew is degrading sharing recalculation performance"
  - "sales pipeline reports time out or hit row limits"
  - "how do I archive old closed opportunities without losing reporting history"
  - "find which users and accounts are skewed before we realign territories"
  - "size a custom index request for our pipeline report filter on 5 million opportunities"
inputs:
  - "current Opportunity and Account record counts and growth rate"
  - "existing indexes, sharing model, and ownership distribution"
  - "report types and filters used by the sales team"
  - "retention policy requirements for closed opportunities"
outputs:
  - "data skew analysis with remediation recommendations"
  - "archival strategy using Big Objects or external storage"
  - "index and skinny table request specifications for Salesforce Support"
  - "optimized SOQL patterns for high-volume sales queries"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# High Volume Sales Data Architecture

Use this skill when a Salesforce org's sales data has grown to the point where queries slow down, reports time out, sharing recalculation stalls, or archival becomes necessary. The highest-leverage moves are usually fixing ownership and parent-child skew, making filters selective against the documented index thresholds, and archiving closed historical Opportunities, with the sharing and encryption consequences of a big-object archive designed in rather than discovered.

---

## Before Starting

Gather this context before working on anything in this domain:

- What are the current record counts for Account, Opportunity, and OpportunityLineItem? What is the monthly growth rate?
- How is Account ownership distributed? Does any single user (including integration users) own more than 10,000 Accounts?
- Which sales reports are slow or timing out, and what filters do they use? Are they using selective or non-selective WHERE clauses?

---

## Questions to Ask Before Configuring

Each question traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Which users own more than 10,000 Accounts or Opportunities, and which Accounts have more than 10,000 children?" | Ownership and parent-child skew drive sharing time and lock contention (Gotchas 1, 2) | The skew list from the queries in `references/examples.md` | Redistribution before the next realignment, with deferred sharing for the big move |
| "For each slow report or query, how many rows does the filter match against the table size?" | Index use follows tiered thresholds, different for standard and custom indexes (Gotcha 3) | A threshold calculation per filter | Index requests only where they will be used |
| "Which slow-report columns are formulas or come from parent objects?" | Skinny tables cannot hold them (Gotcha 5) | A column audit and a list of formulas to store as values | A skinny table request that actually removes the join |
| "Who may see archived deals, and are any source fields encrypted?" | Big objects have no record-level sharing and store encrypted data in clear text (Gotcha 7) | An access group for the archive and an encrypted-field rule | Reps keep normal visibility through a summary object; no clear-text copies |
| "Which archive lookups will users make, in what field order?" | Big object SOQL filters only along the index, with no aggregates (Gotcha 6) | An index designed for those lookups | Archive pages that work without Async workarounds |
| "How will the archival job prove every row landed before deleting the source?" | `insertImmediate()` reports failures in results, not exceptions (Gotcha 8) | A reconciliation step that gates the hard delete | No silent data loss |

What proper configuration adds over "just archiving and adding indexes": the archive keeps the security model, the indexes match the thresholds the optimizer applies, and the delete step is gated on proof.

---

## Core Concepts

High-volume sales data problems in Salesforce cluster around four areas: data skew on parent objects, query selectivity, report row limits, and the cost of keeping historical records online. Understanding all four is necessary because fixing one in isolation often shifts the bottleneck to another.

### Data Skew on Sales Objects

Data skew occurs when a disproportionate number of child records point to a single parent or when a single owner holds too many records. Account ownership skew is the most common variety in sales orgs. The LDV guide's rule is to avoid any user owning more than 10,000 records and any parent having more than 10,000 children; above that, sharing recalculation for that owner's records slows. The same problem appears on Opportunity when a single Account accumulates thousands of Opportunities, causing lock contention on DML operations against that Account.

The fix is to redistribute ownership across role-appropriate users or queue-based owners, and to split high-child-count Accounts into logical sub-accounts where the business model permits.

### Query Selectivity and Custom Indexes

The platform maintains indexes on RecordTypeId, Division, CreatedDate, Systemmodstamp, Name, Email (contacts and leads), lookup and master-detail fields, and the record Id. A standard index is used when the filter matches less than 30% of the first million records and less than 15% of additional records; a custom index when it matches less than 10% of the first million and less than 5% of additional records (LDV guide). Earlier versions of this skill gave flat 10% and 5% figures; use the tiered rule. UNVERIFIED (2026-10-03): the 200,000-record threshold for the trigger "non-selective query" exception is not in a fetched source.

Custom indexes are created by contacting Salesforce Support or by deploying `CustomIndex` metadata, which Support must enable; External ID fields are indexed automatically. Skinny tables, read-only copies of frequently queried columns, are created by Support and help most on tables with millions of records.

### Report Row Limits and Pipeline Reporting

Salesforce reports display a capped number of detail rows in the UI (UNVERIFIED (2026-10-03): the 2,000-row figure, and how summary totals and dashboards treat rows beyond it, are Help-only). Verify a large report's grand total against a SOQL `SUM()` with the same filters before trusting it (Gotcha 9).

Pipeline reports need highly selective date-range filters (e.g., CloseDate within current quarter) plus indexed fields in the filter criteria. Avoid "all time" pipeline views on objects with millions of records.

### Opportunity Archival with Big Objects

Big Objects provide a Salesforce-native archival target for historical Opportunity data. They give consistent performance from 1 million to 1 billion records and use a composite index for retrieval (UNVERIFIED (2026-10-03): the storage-limit treatment is not stated in the fetched guide). Standard SOQL works, but only along the index, with no aggregate functions. Big objects do not support triggers, flows, or processes, support only object and field permissions (no sharing rules), and store encrypted source data as clear text. Earlier versions of this skill said reads require Async SOQL; the current Big Objects and SOQL guides document synchronous SOQL with index-order filters.

The archival pattern is: ETL closed Opportunities older than the retention window into a custom Big Object, validate row counts, then hard-delete the originals. Keep a lightweight "Archived_Opportunity__c" custom object with key summary fields if users need in-app lookups without Async SOQL.

---

## Common Patterns

### Pattern 1: Ownership Redistribution for Skew Remediation

**When to use:** A single user or integration account owns more than 10,000 Accounts or the sharing recalculation job exceeds acceptable duration.

**How it works:**

1. Query ownership distribution: `SELECT OwnerId, COUNT(Id) FROM Account GROUP BY OwnerId ORDER BY COUNT(Id) DESC`.
2. Identify owners exceeding the 10K threshold.
3. Redistribute records to territory-aligned users or Queues in parent-sorted batches. Accounts have no assignment rules; the Data Loader assignment rule setting applies only to cases and leads and overrides the CSV Owner value, so leave it empty. Use a trigger bypass flag for the load window and the defer sharing calculation permission for very large moves.
4. For integration users that create records, set a post-insert process (Flow or trigger) to reassign ownership to the appropriate territory owner immediately.

**Why not the alternative:** Leaving skew in place and adding more sharing rules makes the problem exponentially worse. Each new sharing rule recalculation iterates over the skewed owner's full record set.

### Pattern 2: Tiered Archival with Big Objects

**When to use:** Opportunity table exceeds 5 million records and most are Closed Won/Lost older than 2 years with no active business process dependencies.

**How it works:**

1. Define a custom Big Object (e.g., `Archived_Opportunity__b`) with a composite index on AccountId + CloseDate + OpportunityId.
2. Build a Batch Apex job that queries Opportunities matching the archival criteria, inserts corresponding Big Object records via `Database.insertImmediate()`, and inspects every returned `SaveResult`, because failures do not throw.
3. After successful archival batch, run a separate hard-delete batch to remove archived Opportunities.
4. Maintain an `Archived_Opportunity__c` summary custom object with key fields for UI lookups. It keeps normal sharing, which the big object cannot.

**Why not the alternative:** Soft-deleting to the recycle bin still counts against storage and query performance. External archival (e.g., to S3) loses Salesforce-native querying. Do not archive encrypted fields to the big object without a decision: they land in clear text.

### Pattern 3: Custom Index and Skinny Table Requests

**When to use:** Sales reports on Opportunity or Account consistently time out despite having reasonable filters.

**How it works:**

1. Identify the slow report's filter fields using the report metadata API or Setup > Reports.
2. Verify selectivity against the tiered thresholds: under 10% of the first million rows plus 5% of the remainder for a custom index (300,000 rows at 5 million), or 30% plus 15% for a standard index.
3. File a Salesforce Support case requesting a custom index on the specific field(s), or ask Support to enable `CustomIndex` metadata so the index is tracked in source control. Include record counts and the tiered threshold calculation.
4. For wide objects with many fields but reports using only 5-10 columns, request a skinny table that includes only the needed columns plus the filter fields.

**Why not the alternative:** Report restructuring cannot overcome a missing index on a million-row table. But Well-Architected classes custom indexes and skinny tables as "short-term workarounds" that can add technical debt; the structural fixes are skew removal, archiving or purging, aggregation objects, and data tiering. Use indexes to relieve pain while those land.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single owner has >10K Accounts | Redistribute ownership to queues or territory users | Sharing recalculation cost scales linearly with owned-record count; >10K causes measurable degradation |
| Opportunity table >5M records, most historical | Archive to Big Object, hard-delete originals | Reduces query surface, storage costs, and sharing complexity for active records |
| Pipeline report times out | Add selective date filter + request custom index on the filter field | Index makes the filter selective; verify totals against SOQL (row display cap UNVERIFIED) |
| Single Account has >10K child Opportunities | Split into logical sub-accounts or implement lookup to parent grouping object | Lock contention on parent during batch DML; child count skew degrades SOQL on parent |
| Wide Opportunity object with 200+ fields | Request skinny table with report-relevant columns | Reduces I/O per query; skinny tables serve report and API reads transparently |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Profile the data** -- Query record counts for Account, Opportunity, OpportunityLineItem, and any custom sales objects. Identify tables in the millions of rows, where the LDV guidance applies most. Check monthly growth rate from CreatedDate distribution.
2. **Detect skew** -- Run ownership distribution queries on Account and Opportunity. Flag any owner with more than 10,000 records. Check for parent-child skew by querying Accounts with the highest Opportunity child counts.
3. **Audit query selectivity** -- Review slow SOQL queries and report filters. For each, apply the tiered thresholds (standard 30% of the first million plus 15% beyond; custom 10% plus 5%) and confirm with the Query Plan tool. Identify missing indexes.
4. **Design the archival boundary** -- Agree on a retention window (e.g., 2 years from CloseDate for Closed opportunities). Define the Big Object schema with composite index fields. Validate that no active automation (Flows, triggers, scheduled jobs) depends on records past the archival boundary.
5. **Remediate skew and request indexes** -- Redistribute ownership for skewed users. File Salesforce Support cases for custom indexes and skinny tables with selectivity evidence.
6. **Implement archival batch** -- Build and test the Batch Apex archival job in a sandbox with production-representative data volumes. Validate Big Object row counts match source counts before enabling hard-delete.
7. **Validate and monitor** -- Confirm report performance improvement after indexes are active. Set up scheduled reports or dashboard monitors for ownership distribution drift and record count growth.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] No single user owns more than 10,000 Accounts or Opportunities
- [ ] All high-volume SOQL queries use selective WHERE clauses against indexed fields
- [ ] Pipeline and forecast reports use selective, indexed date-range filters, and large-report totals were checked against a SOQL `SUM()`
- [ ] Archival Big Object schema is defined with an index matching user lookups; access is limited and encrypted fields are handled
- [ ] Archival batch job has been tested with production-scale data in sandbox
- [ ] Skinny table and custom index requests have been filed with Salesforce Support where needed
- [ ] Sharing rule recalculation duration is within acceptable SLA after ownership redistribution

---

## Salesforce-Specific Gotchas

Full detail and sources in `references/gotchas.md`. The short list, including four corrections to earlier versions of this skill:

1. Keep owners and parents below 10,000 records; use deferred sharing for big ownership moves.
2. Index thresholds are tiered (standard 30%/15%, custom 10%/5% of the first million and beyond), not flat.
3. Custom indexes can be tracked as `CustomIndex` metadata and are copied to sandboxes; they are not silently lost on refresh.
4. Skinny tables can contain encrypted data but not formulas or fields from other objects; maximum 200 columns.
5. Big objects support synchronous SOQL along the index, not only Async SOQL, and no aggregates.
6. Big objects have no record-level sharing and store encrypted source data in clear text.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Data skew analysis | Ownership distribution report identifying users exceeding 10K threshold with redistribution plan |
| Archival specification | Big Object schema, composite index definition, retention boundary, and batch job design |
| Index request template | Salesforce Support case content with record counts, selectivity calculations, and field specifications |
| Optimized query catalog | Rewritten SOQL patterns for high-volume sales queries with selectivity verification |

---

## Related Skills

- limits-and-scalability-planning -- Use alongside this skill when data volume is part of a broader limits assessment across the entire org
- sales-cloud-architecture -- Consult when the data architecture decisions affect Sales Cloud feature configuration (territories, forecasting, CPQ)
- technical-debt-assessment -- Reference when historical data volume growth is a symptom of unmanaged technical debt in sales automation

---

## Official Sources Used

- Best Practices for Deployments with Large Data Volumes (Summer '26 PDF) -- https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_large_data_volumes_bp.pdf (full list in `references/well-architected.md`)
- Salesforce Large Data Volumes Best Practices -- https://developer.salesforce.com/docs/atlas.en-us.salesforce_large_data_volumes_bp.meta/salesforce_large_data_volumes_bp/ldv_deployments_introduction.htm
- Salesforce Well-Architected: Performance -- https://architect.salesforce.com/well-architected/easy/performance
