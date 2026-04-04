---
name: custom-index-requests
description: "Use when standard Salesforce indexes are insufficient for query performance on high-volume objects: requesting custom indexes via Salesforce Support for standard fields, deploying custom field indexes via Metadata API, requesting skinny tables, or designing two-column composite indexes. NOT for SOQL query optimization techniques (use data/soql-query-optimization) or general large data volume design (use architect skills)."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "SOQL query is doing a TableScan on a large object and standard indexes are not helping"
  - "how do I request a custom index from Salesforce Support for a non-standard field"
  - "when should I request a skinny table for an object with millions of records"
  - "how do I request a two-column composite index for a filter plus sort query"
  - "query is still slow even though the field has an External ID index"
tags:
  - custom-index
  - skinny-tables
  - large-data-volumes
  - query-performance
  - salesforce-support
inputs:
  - "Object name and approximate record count"
  - "The SOQL query (or queries) that is performing poorly"
  - "Query plan output from the Query Plan tool in Developer Console"
  - "Field(s) used in WHERE and ORDER BY clauses of the slow query"
outputs:
  - "Recommendation: custom index, skinny table, or two-column index"
  - "Salesforce Support case template for requesting index or skinny table"
  - "Selectivity validation: confirm the field meets index selectivity thresholds"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Custom Index Requests

This skill activates when a Salesforce org's standard indexing is insufficient to make SOQL queries selective on high-volume objects, and a practitioner needs to request a custom index or skinny table from Salesforce Support, or deploy a custom field index via Metadata API. The standard indexes (system fields, standard indexed fields, External ID fields) cover most cases — custom indexes fill gaps for specific access patterns that cannot be made selective with standard techniques.

---

## Before Starting

Gather this context before working on anything in this domain:

- Run the Query Plan tool in Developer Console on the slow query. Set the estimated row count to your actual record count. Look for "TableScan" in the plan — this means no selective index was found. Look for the "cost" column; a cost < 1 means the index is likely to be used.
- Know the record count on the object. Salesforce defines selectivity thresholds as a percentage of total records. A filter is selective if it returns fewer than 10% of records (for most standard/custom indexes). If your WHERE clause will always match 50% of records, an index will not help.
- Know whether the field is a custom field or a standard field. Custom fields can be indexed via Metadata API. Standard fields (e.g., `CreatedDate` with wide date ranges, `Name` with null-inclusive filters) require a Salesforce Support case.
- Know whether the object uses Person Accounts. Some index behaviors differ for objects with Person Account data due to the dual Account/Contact nature.

---

## Core Concepts

### Standard vs Custom Indexes

Salesforce automatically maintains indexes on:
- `Id` (always)
- `Name` (for most objects)
- `OwnerId`
- `CreatedDate`, `SystemModstamp`
- `RecordTypeId`
- `Master-detail relationship fields` (parent ID lookup fields)
- Custom fields marked as External ID or Unique
- All standard relationship lookup fields

**Custom indexes** extend indexing to non-indexed fields. They are maintained by Salesforce, not by the customer. There are two paths to request them:
1. **Custom fields**: Deploy a `CustomField` metadata type with `externalId: false` — this creates a non-unique index. The Metadata API supports this without a Support case.
2. **Standard fields, null-inclusive indexes, or non-standard patterns**: Require a Salesforce Support case. Salesforce evaluates the request before creating the index.

### Selectivity Thresholds

An index is only used by the query optimizer when the filter is **selective** — meaning the index dramatically reduces the result set. The thresholds are:

| Filter type | Threshold for index use |
|---|---|
| Standard index (Id, Name, etc.) | < 30% of records (or < 300,000 records in orgs with 1M+) |
| Custom index | < 10% of records |
| Null-inclusive index | Depends on null distribution; Support evaluates case-by-case |

If your WHERE clause filter matches 40% of Account records, a custom index on that field will still result in a TableScan. Salesforce will not use an index that is not selective enough. This is the most common reason a custom index request does not improve performance.

### Skinny Tables

Skinny tables are Salesforce-maintained flattened copies of a subset of fields from a large object. They are used to accelerate read-heavy queries that always filter and return the same fields. Requirements:
- Skinny table requests go to Salesforce Support.
- Maximum 200 fields per skinny table.
- Best for read-heavy patterns where the same query runs thousands of times per day.
- Skinny tables are created for **Full sandbox copies only** — Partial and Developer sandboxes do not include skinny tables. You cannot test skinny table performance in a Developer sandbox.
- Skinny tables do NOT help with queries that have highly non-selective WHERE clauses. They reduce column width but not row count.

### Two-Column (Composite) Indexes

A two-column index indexes two fields together. It is most effective when a query filters on column A AND sorts/filters on column B simultaneously. Example: `WHERE OwnerId = :userId ORDER BY CreatedDate DESC` — a two-column index on (OwnerId, CreatedDate) can serve both the filter and the sort from a single index scan.

Two-column indexes require a Salesforce Support case. They are evaluated on a case-by-case basis and require a realistic selectivity analysis.

---

## Common Patterns

### Deploying a Custom Field Index via Metadata API

**When to use:** The slow query filters on a custom field (e.g., `ExternalAccount__c`, `CustomerSegment__c`) that is not marked as External ID or Unique.

**How it works:**
Add or update the `CustomField` metadata in your sfdx project. Set `externalId` to `false` and `unique` to `false` to create a non-unique index:

```xml
<!-- force-app/main/default/objects/Account/fields/CustomerSegment__c.field-meta.xml -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
  <fullName>CustomerSegment__c</fullName>
  <label>Customer Segment</label>
  <type>Text</type>
  <length>50</length>
  <externalId>false</externalId>
  <unique>false</unique>
  <trackFeedHistory>false</trackFeedHistory>
</CustomField>
```

Wait — there is a nuance here. Simply having a custom field does NOT create an index. You create an index on a custom field by setting `externalId: true` (which creates a unique indexed field) OR by submitting a Salesforce Support case requesting a non-unique custom index on the field. The Metadata API itself does not have a direct "add index" switch for non-External-ID custom fields.

For non-unique, non-External-ID custom field indexing: open a Salesforce Support case with the object, field API name, a sample SOQL query, and the Query Plan output.

### Preparing a Salesforce Support Case for a Custom Index

**When to use:** Requesting any custom index, skinny table, or two-column index from Salesforce Support.

**Required information for the Support case:**
1. Org ID (15-character production org ID, not sandbox).
2. Object API name and approximate record count.
3. The exact SOQL query that is slow, with realistic bind variable values substituted.
4. Query Plan tool output (screenshot or text) showing TableScan.
5. The field(s) to be indexed and their current values distribution (e.g., "30% of records have Status__c = 'Active', 70% have other values").
6. Expected query frequency (queries per hour or day) — helps Salesforce justify index maintenance cost.
7. Business justification: what process is blocked by the slow query.

Salesforce will evaluate selectivity before creating the index. If the field is not selective enough, they will recommend an alternative approach.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Custom field, non-selective WHERE clause | External ID flag (creates index) OR Support case | Fastest path for custom fields; no Support wait time for External ID |
| Standard field (CreatedDate, Name) with non-selective filter | Support case for custom index | Standard field indexing changes require Salesforce backend access |
| Query filters on field A and sorts on field B | Support case for two-column index on (A, B) | Single-column indexes cannot serve both filter and sort efficiently |
| Very high-frequency read query on same field set | Support case for skinny table | Skinny table reduces I/O per read; best for read-heavy constant-query patterns |
| Filter matches >10% of records | Refactor query to add more selective filters | Index will not be used regardless; need additional WHERE conditions |
| Performance issue on Partial/Developer sandbox | Test must be done in Full sandbox | Skinny tables and custom indexes are not copied to Partial/Dev sandboxes |

---

## Recommended Workflow

1. Run the Query Plan tool on the slow SOQL query. Set the estimated row count to the actual production record count. Identify whether a TableScan is occurring.
2. Check the selectivity threshold: estimate what percentage of records your WHERE clause filter matches. If >10% for a custom field or >30% for a standard field, the index will not help — refactor the query first.
3. Determine the field type: custom field vs standard field. For a custom field, assess whether External ID designation is appropriate (External IDs are intended for integration key fields).
4. If a custom non-unique index is needed on a custom field, or if the field is a standard field, or if a two-column or skinny table is needed — open a Salesforce Support case with all required information.
5. Validate the index after creation: re-run the Query Plan. The plan should no longer show TableScan; it should show an index-based plan with cost < 1.
6. Monitor query performance in production for 1–2 weeks post-index creation. Large orgs may take time to backfill the index.

---

## Review Checklist

- [ ] Query Plan tool confirms TableScan on the target query
- [ ] Selectivity threshold verified: filter returns <10% of records
- [ ] Field type identified: custom field (Metadata API path) vs standard field (Support case)
- [ ] If Support case needed: org ID, object, field, SOQL, Query Plan output, and field value distribution included
- [ ] Post-index Query Plan confirms index is being used (no TableScan, cost < 1)
- [ ] Skinny table requests verified against Full sandbox requirement before testing

---

## Salesforce-Specific Gotchas

1. **External ID fields create a unique index — not a non-unique index** — marking a field as External ID enforces uniqueness at the database level. If the field has (or will have) duplicate values, using External ID will cause upsert failures. Use External ID only for genuinely unique integration keys; request a non-unique custom index via Support for non-unique filter fields.
2. **Custom indexes are not copied to Partial or Developer sandboxes** — only Full sandbox copies preserve custom indexes and skinny tables. If you test performance in a Developer sandbox and it looks fine, that tells you nothing about production behavior where the index matters.
3. **Index selectivity is recalculated at query time** — a field that is selective today may become non-selective as data grows. An index that speeds up queries now may stop being used when the object reaches 10M records if the field's distribution changes. Monitor query plans periodically on high-volume objects.
4. **Skinny table does not survive sandbox refresh** — each Full sandbox refresh re-copies the skinny table from production. A skinny table that exists on a refreshed sandbox is a copy of production's skinny table. If production does not have the skinny table, the refreshed sandbox will not have it either.
5. **Two-column index field order matters** — a two-column index on (OwnerId, CreatedDate) accelerates `WHERE OwnerId = :x ORDER BY CreatedDate` but NOT `WHERE CreatedDate > :d AND OwnerId = :x` where CreatedDate is the leading filter. The leading column must be the filter column for the index to be useful. Specify the correct column order in your Support case.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Query Plan analysis | TableScan identification, estimated cost, and selectivity calculation for the target query |
| Salesforce Support case template | Pre-filled case with org ID, object, field, SOQL, Query Plan output, and field distribution |
| Post-index validation | Query Plan re-run confirming index usage and performance improvement measurement |

---

## Related Skills

- data/soql-query-optimization — SOQL query tuning techniques, selective filters, avoiding non-selective patterns
- data/external-data-and-big-objects — Big Objects and async SOQL for archival queries
- architect/limits-and-scalability-planning — planning for data volume growth and index strategy at scale
