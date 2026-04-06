---
name: high-volume-sales-data-architecture
description: "Use when designing or reviewing Salesforce orgs with large Opportunity and Account volumes, including archival strategy, report performance, data skew prevention, SOQL tuning for sales queries, and index planning. Triggers: 'opportunity table is slow', 'account ownership skew', 'sales report timing out', 'archive old opportunities'. NOT for generic large data volume planning across arbitrary custom objects, non-sales data models, or Marketing Cloud data extensions."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# High Volume Sales Data Architecture

Use this skill when a Salesforce org's sales data has grown to the point where queries slow down, reports time out, sharing recalculation stalls, or archival becomes necessary. The highest-leverage moves are usually fixing ownership skew on Account, adding selective custom indexes, and moving closed-won historical Opportunities to Big Objects before tuning anything else.

---

## Before Starting

Gather this context before working on anything in this domain:

- What are the current record counts for Account, Opportunity, and OpportunityLineItem? What is the monthly growth rate?
- How is Account ownership distributed? Does any single user (including integration users) own more than 10,000 Accounts?
- Which sales reports are slow or timing out, and what filters do they use? Are they using selective or non-selective WHERE clauses?

---

## Core Concepts

High-volume sales data problems in Salesforce cluster around four areas: data skew on parent objects, query selectivity, report row limits, and the cost of keeping historical records online. Understanding all four is necessary because fixing one in isolation often shifts the bottleneck to another.

### Data Skew on Sales Objects

Data skew occurs when a disproportionate number of child records point to a single parent or when a single owner holds too many records. Account ownership skew is the most common variety in sales orgs. When a single user owns more than 10,000 Account records, sharing rule recalculation slows dramatically because the platform must recompute visibility for every record that user owns. The same problem appears on Opportunity when a single Account accumulates thousands of Opportunities, causing lock contention on DML operations against that Account.

The fix is to redistribute ownership across role-appropriate users or queue-based owners, and to split high-child-count Accounts into logical sub-accounts where the business model permits.

### Query Selectivity and Custom Indexes

Salesforce maintains standard indexes on Id, Name, OwnerId, CreatedDate, SystemModstamp, and lookup/master-detail fields. A SOQL query is selective when its WHERE clause filters to less than 10% of total records for a standard index or less than 5% for a custom index (with a floor of 333,333 records in either case). Non-selective queries against tables with more than 200,000 records risk the "non-selective query" exception in triggers and may full-table-scan in reports.

Custom indexes must be requested through Salesforce Support. They are not self-service. Skinny tables -- read-only copies of frequently queried columns -- can also be requested for objects exceeding 100,000 records and dramatically reduce report and query I/O.

### Report Row Limits and Pipeline Reporting

Salesforce reports return a maximum of 2,000 detail rows in the UI. Summary and matrix reports can aggregate across more records but still cap at the underlying query limit. Dashboard components use the filtered report row set, so a non-selective pipeline report will silently return incomplete data rather than erroring.

Pipeline reports need highly selective date-range filters (e.g., CloseDate within current quarter) plus indexed fields in the filter criteria. Avoid "all time" pipeline views on objects with millions of records.

### Opportunity Archival with Big Objects

Big Objects provide a Salesforce-native archival target for historical Opportunity data. They support up to billions of rows, use a composite primary key for indexed retrieval, and do not count against standard storage limits. The tradeoff is that Big Objects support only Async SOQL for reads and have no trigger, workflow, or formula support. They are write-once stores for analytics and compliance, not transactional tables.

The archival pattern is: ETL closed Opportunities older than the retention window into a custom Big Object, validate row counts, then hard-delete the originals. Keep a lightweight "Archived_Opportunity__c" custom object with key summary fields if users need in-app lookups without Async SOQL.

---

## Common Patterns

### Pattern 1: Ownership Redistribution for Skew Remediation

**When to use:** A single user or integration account owns more than 10,000 Accounts or the sharing recalculation job exceeds acceptable duration.

**How it works:**

1. Query ownership distribution: `SELECT OwnerId, COUNT(Id) FROM Account GROUP BY OwnerId ORDER BY COUNT(Id) DESC`.
2. Identify owners exceeding the 10K threshold.
3. Redistribute records to territory-aligned users or Queues. Use Data Loader in batch mode with `assignment rule` headers off to avoid trigger overhead.
4. For integration users that create records, set a post-insert process (Flow or trigger) to reassign ownership to the appropriate territory owner immediately.

**Why not the alternative:** Leaving skew in place and adding more sharing rules makes the problem exponentially worse. Each new sharing rule recalculation iterates over the skewed owner's full record set.

### Pattern 2: Tiered Archival with Big Objects

**When to use:** Opportunity table exceeds 5 million records and most are Closed Won/Lost older than 2 years with no active business process dependencies.

**How it works:**

1. Define a custom Big Object (e.g., `Archived_Opportunity__b`) with a composite index on AccountId + CloseDate + OpportunityId.
2. Build a Batch Apex job that queries Opportunities matching the archival criteria, inserts corresponding Big Object records via `Database.insertImmediate()`, and logs results.
3. After successful archival batch, run a separate hard-delete batch to remove archived Opportunities.
4. Optionally maintain an `Archived_Opportunity__c` summary custom object with key fields for UI lookups.

**Why not the alternative:** Soft-deleting to the recycle bin still counts against storage and query performance. External archival (e.g., to S3) loses Salesforce-native querying.

### Pattern 3: Custom Index and Skinny Table Requests

**When to use:** Sales reports on Opportunity or Account consistently time out despite having reasonable filters.

**How it works:**

1. Identify the slow report's filter fields using the report metadata API or Setup > Reports.
2. Verify selectivity: the filter must return less than 10% of total records (standard index) or 5% (custom index).
3. File a Salesforce Support case requesting a custom index on the specific field(s). Include record counts and the selectivity calculation.
4. For wide objects with many fields but reports using only 5-10 columns, request a skinny table that includes only the needed columns plus the filter fields.

**Why not the alternative:** Query hints and report restructuring cannot overcome a missing index on a million-row table. The index request is the structural fix.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single owner has >10K Accounts | Redistribute ownership to queues or territory users | Sharing recalculation cost scales linearly with owned-record count; >10K causes measurable degradation |
| Opportunity table >5M records, most historical | Archive to Big Object, hard-delete originals | Reduces query surface, storage costs, and sharing complexity for active records |
| Pipeline report times out | Add selective date filter + request custom index on CloseDate or Stage | Reports silently truncate at 2K detail rows; index makes the filter selective |
| Single Account has >10K child Opportunities | Split into logical sub-accounts or implement lookup to parent grouping object | Lock contention on parent during batch DML; child count skew degrades SOQL on parent |
| Wide Opportunity object with 200+ fields | Request skinny table with report-relevant columns | Reduces I/O per query; skinny tables serve report and API reads transparently |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Profile the data** -- Query record counts for Account, Opportunity, OpportunityLineItem, and any custom sales objects. Identify tables exceeding 200K records. Check monthly growth rate from CreatedDate distribution.
2. **Detect skew** -- Run ownership distribution queries on Account and Opportunity. Flag any owner with more than 10,000 records. Check for parent-child skew by querying Accounts with the highest Opportunity child counts.
3. **Audit query selectivity** -- Review slow SOQL queries and report filters. For each, calculate whether the filter returns fewer than 10% (standard index) or 5% (custom index) of total records. Identify missing indexes.
4. **Design the archival boundary** -- Agree on a retention window (e.g., 2 years from CloseDate for Closed opportunities). Define the Big Object schema with composite index fields. Validate that no active automation (Flows, triggers, scheduled jobs) depends on records past the archival boundary.
5. **Remediate skew and request indexes** -- Redistribute ownership for skewed users. File Salesforce Support cases for custom indexes and skinny tables with selectivity evidence.
6. **Implement archival batch** -- Build and test the Batch Apex archival job in a sandbox with production-representative data volumes. Validate Big Object row counts match source counts before enabling hard-delete.
7. **Validate and monitor** -- Confirm report performance improvement after indexes are active. Set up scheduled reports or dashboard monitors for ownership distribution drift and record count growth.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] No single user owns more than 10,000 Accounts or Opportunities
- [ ] All high-volume SOQL queries use selective WHERE clauses against indexed fields
- [ ] Pipeline and forecast reports include date-range filters that keep result sets under 2,000 detail rows
- [ ] Archival Big Object schema is defined with appropriate composite index
- [ ] Archival batch job has been tested with production-scale data in sandbox
- [ ] Skinny table and custom index requests have been filed with Salesforce Support where needed
- [ ] Sharing rule recalculation duration is within acceptable SLA after ownership redistribution

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Sharing recalculation is not incremental** -- When a sharing rule changes or ownership transfers occur at scale, the platform recalculates sharing for the entire set of affected records, not just the changed ones. An owner with 50K records causes a recalculation 5x more expensive than one with 10K records, not proportionally more.
2. **Non-selective queries silently succeed in reports but truncate** -- Unlike Apex, which throws a `System.QueryException` for non-selective queries on large tables, reports simply return the first 2,000 matching detail rows with no error. Users see "correct-looking" but incomplete pipeline numbers.
3. **Big Object Async SOQL has no real-time use case** -- Async SOQL queries against Big Objects return results to a target object, not inline. Any design that assumes synchronous reads from Big Objects (e.g., in a Lightning page load) will fail. Use the summary custom object pattern for UI access.
4. **Custom indexes require ongoing maintenance** -- Custom indexes added by Salesforce Support can be silently dropped during major upgrades or org migrations. After any major release or sandbox refresh, verify that custom indexes are still active by testing query plans via the Query Plan tool in Developer Console.
5. **Skinny tables do not include formula fields** -- Skinny tables are physical column subsets and cannot include formula fields, roll-up summary fields, or encrypted fields. Reports that depend on formula columns cannot benefit from skinny tables for those specific columns.

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

- Salesforce Large Data Volumes Best Practices -- https://developer.salesforce.com/docs/atlas.en-us.salesforce_large_data_volumes_bp.meta/salesforce_large_data_volumes_bp/ldv_deployments_introduction.htm
- Salesforce Well-Architected: Performance -- https://architect.salesforce.com/well-architected/easy/performance
