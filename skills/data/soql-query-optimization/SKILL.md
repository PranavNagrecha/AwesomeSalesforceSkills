---
name: soql-query-optimization
description: "Use when a SOQL query is running slowly, causing timeouts, or returning UNABLE_TO_LOCK_ROW errors in large data volume orgs. Covers index-aware query writing, selectivity rules, the Query Plan tool, skinny tables, and dynamic field-set queries. Triggers: slow soql query, query timeout, non-selective query, query plan tool, index usage, soql optimization, large object performance. NOT for org-wide large-data-volume architecture — ownership or account data skew, Big Object archival, tens of millions of rows on one object — use architect/large-data-volume-architecture. NOT for the custom-index or composite-index request itself — use data/custom-index-requests. NOT for Apex CPU or heap governor limits — use apex/apex-cpu-and-heap-optimization. NOT for writing basic SOQL — use apex/soql-fundamentals."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
tags:
  - soql
  - query-optimization
  - indexes
  - large-data-volumes
  - performance
inputs:
  - The SOQL query or queries that are performing poorly
  - Object name and approximate record count
  - Query Plan tool output (if available)
  - Error message if any (UNABLE_TO_LOCK_ROW, QUERY_TIMEOUT, etc.)
outputs:
  - Optimized query or rewrite recommendation
  - Index strategy recommendation
  - Query Plan tool interpretation
  - Skinny table or custom index request guidance
triggers:
  - "my soql query is running slowly on a large object"
  - "how do I use the query plan tool in salesforce"
  - "non-selective soql query causing timeout"
  - "index usage for soql performance"
  - "soql query optimization for large data volumes"
  - "skinny table request salesforce"
  - "check whether my SOQL filter is selective before moving it into a trigger"
  - "get a query plan from the REST API explain parameter instead of Developer Console"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-10-19
---

# SOQL Query Optimization

This skill activates when a SOQL query is slow, timing out, or causing load problems on a large-volume object. It guides practitioners through measuring selectivity, reading query-plan output, choosing between a rewrite, a custom index, and a skinny table, and restructuring queries so the optimizer can drive them from an index.

---

## Before Starting

Gather this context before working on anything in this domain:

- Object name and total row count, including Recycle Bin rows (in Apex, `SELECT COUNT() FROM Object__c ALL ROWS` versus `SELECT COUNT() FROM Object__c WHERE IsDeleted = false`; over REST, the `queryAll` resource)
- The exact SOQL query that is slow or timing out, with bind variables replaced by real literals
- A query plan: Developer Console Query Plan, or `GET /services/data/v67.0/query/?explain=<query>`
- Where the query runs: trigger, batch `start`, Lightning controller, report, list view, or an integration
- Any error text (QUERY_TIMEOUT, System.QueryException, System.LimitException)

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "How many rows does the object hold today, including the Recycle Bin, and how fast is it growing?" | Index thresholds are percentages of the object's rows, and deleted rows still sit in the table the query must exclude (Gotcha 4) | A row count for the threshold arithmetic, and a date when the query will stop being selective |
| "Will this query run inside a trigger, now or after a refactor?" | The Apex guide singles out queries inside triggers as the place selectivity matters most (Gotcha 6) | A gate: the plan must show `relativeCost` under 1.0 before the query moves into trigger code |
| "Which filter is meant to drive the query, and how many rows does it match on its own?" | Each indexed filter is checked against its own threshold, and an AND can be selective when neither filter is (Gotcha 1) | A `GROUP BY ROLLUP` count per filter value instead of a guess |
| "Does any filter use `!=`, `NOT`, a comparison with an empty string, or a leading `%`?" | Negative operators and empty-value comparisons usually stop a custom index from being used (Gotcha 8) | A rewrite to a positive filter, or a placeholder value such as `NA` in place of null |
| "Is any filter field a formula, and does the formula cross a lookup or use TODAY()?" | Non-deterministic formulas cannot be indexed (Gotcha 2) | A stored field, or a cross-object filter on an indexed parent field |
| "Was a large load, delete, or update run in the last day?" | Optimizer statistics are gathered nightly, so plans can be wrong right after a bulk change (Gotcha 7) | A rerun of the plan the next day before anyone files a Support case |
| "Which sandbox will we test performance in?" | Custom indexes are copied to every sandbox created from production; skinny tables reach only Full sandboxes (Gotcha 5) | A test environment whose plans match production |

A proper optimization adds a measured plan, threshold arithmetic tied to the real row count, and a recorded index decision; "just adding LIMIT" or an index request without numbers leaves the query to fail again when the object grows.

---

## Core Concepts

### 1. Selectivity thresholds

The query optimizer runs a pre-query against its own statistics to decide whether an index is worth using. The thresholds are tiered by the object's row count:

| Index type | Used when the filter matches less than | Worked examples from the LDV guide |
|---|---|---|
| Standard index | 30% of the first million rows and 15% of rows beyond that | 2M rows → 450,000; 5M rows → 900,000 |
| Custom index | 10% of the first million rows and 5% of rows beyond that | 500K rows → 50,000; 5M rows → 300,000 |

Standard indexes exist by default on Id, Name, OwnerId, CreatedDate, SystemModstamp, RecordTypeId, Division, Email on Contact and Lead, and every lookup and master-detail field. Custom fields marked External ID or Unique are indexed too.

Combining filters:

- **AND**: the optimizer uses the indexes unless one returns more than 20% of the object's rows. The overall condition is selective when each filter targets less than twice its threshold, or when the intersection of the filters is under the threshold.
- **OR**: each filter must meet its threshold individually, and every field in the OR must be indexed for any index to be used.
- **LIKE**: the optimizer does not use its statistics table; it samples up to 100,000 rows of real data to decide.

If a filter misses its threshold, only that index is excluded; other indexed filters in the WHERE clause can still drive the query.

### 2. Reading a query plan

Two tools return the same kind of plan without running the query:

- **Developer Console Query Plan** — turned on by the `Enable Query Plan` user preference.
- **REST `explain` parameter** — `GET /services/data/vXX.X/query/?explain=<SOQL, or a report or list view Id>`, available since API 30.0 and labelled Beta. It works from any REST client, such as `curl` with a bearer token, so plans can be captured in CI.

| Plan field | What it tells you |
|---|---|
| `leadingOperationType` | `Index`, `Sharing`, `Other`, or `TableScan` (no index) |
| `relativeCost` | Cost compared with the selective-query threshold; above 1.0 means the query is not selective |
| `cardinality` / `sobjectCardinality` | Estimated rows returned versus rows in the object |
| `notes` | Why a filter was not considered, for example "unindexed" |

Plans come back sorted from most to least optimal; the first one is what runs. A worked request and response is in `references/query-plan-worked-example.md`.

### 3. Indexes you can get, and how

- **External ID or Unique** on Auto Number, Email, Number, or Text fields creates an index at deploy time.
- **Custom index by request**: Customer Support creates indexes on other custom fields and on standard fields that are not indexed by default. The Metadata API also has a `CustomIndex` type (API 50.0+, `.indx-meta` files in the `customindex` folder) whose use still requires contacting Support first.
- **Cannot be indexed**: long text area, rich text area, encrypted text, multi-select picklists, currency fields in a multicurrency org, non-deterministic formulas (lookup references, TODAY and NOW, and the other cases the LDV guide lists), and formulas that call TEXT() on a picklist.
- **Nulls**: index tables leave out null rows by default. Support can build a null-inclusive index, and existing indexes must be rebuilt to include nulls. Two-column indexes can hold nulls in the second column.
- **Two-column indexes** help when one field selects and another sorts (list views), or when two fields are always filtered together.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- excerpt: one CustomIndex component (.indx-meta, customindex folder; file name is illustrative).
     Deploy only after Customer Support has agreed the index; see the CustomIndex type in the Metadata API guide. -->
<CustomIndex xmlns="http://soap.sforce.com/2006/04/metadata">
    <allowNullValues>false</allowNullValues>
</CustomIndex>
```

### 4. Skinny tables

A skinny table is a Salesforce-maintained table holding standard and custom fields together, so read-only queries that touch only its fields skip the join between the two. It omits soft-deleted rows and stays in sync with the source table. Customer Support creates and changes it; you cannot. Limits: 200 columns, no fields from other objects, custom objects plus Account, Contact, Opportunity, Lead, and Case only, copied to Full sandboxes only. The LDV guide warns that a skinny table used in the wrong context can make performance worse, so request one only for objects with millions of rows and a stable set of read-heavy queries.

---

## Common Patterns

### Pattern 1: Diagnose and rewrite a non-selective query

1. Capture the plan (Developer Console or `?explain=`). `relativeCost` above 1.0, or `TableScan` as the first plan, means no index can drive the query.
2. Count rows per filter value: `SELECT Status__c, COUNT(Id) FROM Loan_Application__c GROUP BY ROLLUP(Status__c)`.
3. Compare each count with the threshold for that index type and the object's row count.
4. Options, in order: lead with an indexed standard field (CreatedDate range, RecordTypeId, OwnerId); add a positive, selective filter; ask for a custom index if one value matches under 10%; split an OR into separate queries.

### Pattern 2: OR decomposition

The LDV guide's fix when two indexed fields joined by OR exceed the threshold is to run two queries and join the results:

```apex
Map<Id, Account> combined = new Map<Id, Account>(
    [SELECT Id, Name FROM Account WHERE Region__c = 'West']
);
combined.putAll(new Map<Id, Account>(
    [SELECT Id, Name FROM Account WHERE Status__c = 'Active']
));
List<Account> results = combined.values();
```

Each half must be selective on its own, and the split spends one extra SOQL query against the transaction limit.

### Pattern 3: Recent-records query with ORDER BY on an indexed field

For "records created in the last N days" on an object too large for the CreatedDate threshold, the LDV guide's case study adds `ORDER BY` on the indexed field and a `LIMIT` under 100,000; the optimizer then uses the ORDER BY index without the threshold check:

```soql
SELECT Id, Product_Code__c
FROM Customer_Product__c
WHERE CreatedDate = LAST_N_DAYS:3
ORDER BY CreatedDate
LIMIT 99999
```

This returns at most 99,999 rows; if more were created in the window, the rest are not returned.

### Pattern 4: Dynamic SOQL from a field set

```apex
List<Schema.FieldSetMember> members = SObjectType.Account.fieldSets.Summary_Fields.getFields();
List<String> paths = new List<String>{ 'Id' };
for (Schema.FieldSetMember m : members) {
    paths.add(m.getFieldPath());
}
Id ownerId = UserInfo.getUserId();
String soql = 'SELECT ' + String.join(paths, ', ')
    + ' FROM Account WHERE OwnerId = :ownerId LIMIT 200';
List<Account> rows = Database.query(soql);
```

Selectivity rules are the same for dynamic and static SOQL. Prefer explicit field lists: every selected field counts toward the 6 MB synchronous or 12 MB asynchronous heap.

---

## Decision Guidance

| Situation | Recommended approach | Reason |
|---|---|---|
| `relativeCost` above 1.0 and the filter is a formula | Filter on the source field, or on a stored copy that can be indexed | Non-deterministic formulas cannot be indexed |
| OR across two indexed fields, each selective alone | Two queries merged in Apex | OR needs every branch indexed and under its threshold |
| Custom field drives a query on a large object | Custom index request with GROUP BY counts attached | Custom fields are not indexed unless External ID or Unique |
| `LIKE '%term%'` on a large object | Confirm with `?explain=`; use SOSL for keyword search | LIKE index use is decided by sampling 100,000 rows |
| Last-N-days query over the CreatedDate threshold | `ORDER BY CreatedDate LIMIT` under 100,000 | The ORDER BY index is used without the threshold check |
| Filter is `= null` | Null-inclusive index, or store a placeholder such as `NA` | Index tables exclude nulls by default |
| Millions of rows, the same field subset read by many reports | Skinny table request | Removes the standard/custom field join for read-only queries |
| One field selects and another sorts in a list view | Two-column custom index | One index serves both the filter and the sort |

---

## Recommended Workflow

1. Record the object, the row count including the Recycle Bin, the call site, and the literal query in `templates/soql-query-optimization-template.md`.
2. Capture the plan with `?explain=` or Developer Console Query Plan, and save the JSON or screenshot next to the filled template.
3. Run `GROUP BY ROLLUP` counts for every filter field and do the threshold arithmetic from Core Concepts §1 against the real row count.
4. Pick the fix from Decision Guidance; for an index or skinny table, fill the request section of the template with the counts as evidence.
5. Run `python3 skills/data/soql-query-optimization/scripts/check_soql_query_optimization.py --manifest-dir force-app/main/default`, resolve every ERROR, and review the WARN lines for queries on large objects.
6. Re-capture the plan after the change and confirm `relativeCost` is under 1.0 with an `Index` leading operation; for trigger code, also run the Apex tests that drive the trigger with 200 records.

---

## Review Checklist

- [ ] The plan for the final query shows `relativeCost` under 1.0 and an `Index` leading operation
- [ ] Threshold arithmetic uses the object's real row count, deleted rows included
- [ ] No negative operator, empty-string comparison, or leading-wildcard LIKE drives the query
- [ ] No non-deterministic formula field is a filter
- [ ] OR branches are each indexed and selective, or the query is split
- [ ] Index or skinny-table requests carry the GROUP BY counts that justify them
- [ ] Performance was tested in a sandbox with the same indexes (any sandbox for custom indexes; Full only for skinny tables)
- [ ] The checker reports no ERROR lines

---

## Salesforce-Specific Gotchas

Full write-ups live in `references/gotchas.md`:

| # | Gotcha |
|---|---|
| 1 | AND across two non-selective filters can still be selective |
| 2 | Non-deterministic formula filters never use an index |
| 3 | ORDER BY plus LIMIT can rescue a last-N-days query; LIMIT alone does not fix a scan |
| 4 | Recycle Bin rows still sit in the table the query scans |
| 5 | Custom indexes reach every sandbox; skinny tables reach only Full sandboxes |
| 6 | Trigger context is where a non-selective query hurts most |
| 7 | Optimizer statistics are refreshed nightly |
| 8 | Negative operators and empty-value comparisons defeat custom indexes |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Optimized SOQL query | Rewritten query led by an indexed, selective filter |
| Query plan record | `?explain=` JSON or Query Plan capture, before and after |
| Index request evidence | Object, field, value counts, and the threshold arithmetic |
| CustomIndex metadata | `.indx-meta` file, only after Support has agreed the index |
| Optimization report | Filled `templates/soql-query-optimization-template.md` |

---

## Related Skills

- `apex/apex-cpu-and-heap-optimization` — the problem is CPU time or heap, not query selectivity
- `apex/soql-fundamentals` — basic SOQL syntax
- `data/custom-index-requests` — preparing and tracking the index or skinny-table request itself
- `data/data-model-design-patterns` — building the index strategy into an object design
- `data/sosl-search-patterns` — keyword search that should not be a LIKE query
- `architect/large-data-volume-architecture` — data skew, archival, and object-level volume strategy
- `architect/limits-and-scalability-planning` — query performance against growth projections
- `admin/data-skew-and-sharing-performance` — slowness caused by ownership skew or sharing recalculation
