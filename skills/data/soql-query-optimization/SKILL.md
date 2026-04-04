---
name: soql-query-optimization
description: "Use when a SOQL query is running slowly, causing timeouts, or returning UNABLE_TO_LOCK_ROW errors in large data volume orgs. Covers index-aware query writing, selectivity rules, the Query Plan tool, skinny tables, and dynamic field-set queries. Triggers: slow soql query, query timeout, non-selective query, query plan tool, index usage, soql optimization, large object performance. NOT for Apex CPU or heap governor limit issues (use apex-cpu-and-heap-optimization) or for writing basic SOQL (use soql-fundamentals)."
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
  - my soql query is running slowly on a large object
  - how do I use the query plan tool in salesforce
  - non-selective soql query causing timeout
  - index usage for soql performance
  - soql query optimization for large data volumes
  - skinny table request salesforce
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# SOQL Query Optimization

This skill activates when a SOQL query is slow, timing out, or causing load problems on a large-volume object. It guides practitioners through diagnosing selectivity, reading Query Plan output, requesting custom indexes, and restructuring queries to avoid full-table scans.

---

## Before Starting

Gather this context before working on anything in this domain:

- Object name and approximate total record count (check Setup > Storage Usage or run `SELECT COUNT() FROM Object__c`)
- The exact SOQL query that is slow or timing out
- Whether a Query Plan tool reading is available (Developer Console > Debug > Open Query Plan)
- Any error message text (QUERY_TIMEOUT, UNABLE_TO_LOCK_ROW, System.LimitException)
- Whether the object has soft-deleted records that significantly inflate total count

---

## Core Concepts

### 1. Selectivity and Index Usage

The Lightning Platform query optimizer decides whether to use an index or perform a full-table scan based on selectivity: the estimated fraction of total records a filter will return.

**Standard indexed fields (indexed by default on most objects):** Id, Name, OwnerId, CreatedDate, SystemModstamp, RecordTypeId, and all master-detail and lookup relationship fields.

**Selectivity thresholds (standard indexed fields):**
- The index is used when the filter matches fewer than 30% of total records, or fewer than 1,000,000 records — whichever is less.
- Example: on a 2M-record object, the standard index is used if the filter matches 450,000 or fewer records.

**Selectivity thresholds (custom indexed fields):**
- The index is used when the filter matches fewer than 10% of total records, or fewer than 333,333 records — whichever is less.
- Example: on a 5M-record object, a custom index is used if the filter matches 333,333 or fewer records.

**AND conditions:** The query optimizer uses indexes unless one filter alone returns more than 20% of records or 666,666 total records.

**OR conditions:** All fields in the OR clause must be indexed for any index to be used. The index is used only if all OR branches return fewer than 10% of records or 333,333 total records. If the OR branches are non-selective or non-indexed, Salesforce cannot use any index.

If no selective filter exists, the optimizer performs a full-table scan, which will time out on objects with 1M+ records.

### 2. The Query Plan Tool

The Query Plan tool in Developer Console (Debug > Open Query Plan) shows the execution plan Salesforce would use for a given SOQL query — without actually running the query.

**How to read output:**
- **Cost < 1.0** — Salesforce plans to use an index. Lower cost = better.
- **Cost > 1.0** — Full-table scan or an expensive operation. Queries in production on large objects with cost > 1.0 are at high risk of timeout.
- The tool lists alternative plans and their costs; the lowest-cost plan is selected.
- Each plan entry shows the cardinality (estimated rows to process) and the leading field used.

**Limitations:** The Query Plan tool is only available in Developer Console. It is not available in VS Code or the Salesforce CLI. Use it as a manual diagnostic step when investigating a slow query.

### 3. Index Types and Custom Index Requests

**Standard indexes** are maintained automatically by Salesforce for the fields listed above.

**Custom indexes** can be created on custom fields (except long text areas, rich text areas, non-deterministic formula fields, and encrypted text fields). Two paths:
1. **External ID checkbox** on a custom field — automatically creates a custom index when the field is marked as External ID in field metadata.
2. **Salesforce Support request** — for custom fields that are not External IDs, or for standard fields that are not automatically indexed, open a case with Salesforce Support to request a custom index.

**Non-deterministic formula fields cannot be indexed.** This includes formula fields that reference fields on related objects via lookups, reference multi-select picklists, reference currency fields in multicurrency orgs, or reference long text areas.

**Two-column (composite) custom indexes:** Useful for queries that filter on one field and sort by another (common in list views and reports). A composite index on `(field1__c, field2__c)` outperforms two single-column indexes for queries with `WHERE field1__c = :val ORDER BY field2__c`.

**Null handling:** By default, index tables do not include null-value records. If a query must filter for null values (`WHERE Field__c = null`), the standard index will not help. Salesforce Support can create custom indexes that include null rows.

### 4. Skinny Tables

Skinny tables are Salesforce-internal read-only copies of selected object fields, without joins. They are maintained by Salesforce and kept in sync with source data.

**When to request:** Objects with 10M+ records and recurring read-heavy queries (reports, list views, batch jobs) that access the same subset of fields. Request via Salesforce Support.

**Benefits:** Read-only queries that hit a skinny table skip the standard/custom field join, reducing I/O by 4–10x for qualifying queries.

**Constraints:**
- Maximum 200 columns per skinny table
- Cannot include fields from other objects (no cross-object fields)
- Read-only; not used for DML operations
- Copied to Full sandboxes only; not copied to Developer, Developer Pro, or Partial sandboxes
- Supported objects: custom objects, and Account, Contact, Opportunity, Lead, Case

**Tradeoff:** Adds maintenance overhead for Salesforce. Not appropriate for objects with low record counts or infrequent query patterns.

---

## Common Patterns

### Pattern 1: Diagnose and Rewrite a Non-Selective Query

**When to use:** A SOQL query on a large object (500K+ records) is timing out or returning slowly. You suspect non-selective filters.

**How it works:**

1. Open Developer Console. Go to **Debug > Open Query Plan**.
2. Paste the SOQL query and click **Execute**.
3. Review the cost value. If cost > 1.0, the query is doing a full-table scan.
4. Identify which WHERE clause fields are non-indexed or non-selective.
5. Options (in order of preference):
   - **Rewrite the query** to use a standard indexed field (OwnerId, CreatedDate, RecordTypeId) as the leading filter.
   - **Add a selective filter** that narrows the result set before applying non-selective conditions.
   - **Request a custom index** on a custom field if the field value distribution is selective (< 10% of records per value).
   - **Decompose an OR query** into multiple queries and merge results in Apex.

**Why not just add LIMIT:** Adding LIMIT to a non-selective query does not make it selective. The optimizer must still scan the table to find qualifying records before applying LIMIT.

### Pattern 2: OR Query Decomposition

**When to use:** A query uses OR conditions across fields where only one is indexed, causing the index to be bypassed entirely.

**How it works:**

Instead of:
```soql
SELECT Id, Name FROM Account
WHERE Region__c = 'West' OR Status__c = 'Active'
```

Decompose into two indexed queries and merge in Apex:
```apex
List<Account> westAccounts = [SELECT Id, Name FROM Account WHERE Region__c = 'West'];
List<Account> activeAccounts = [SELECT Id, Name FROM Account WHERE Status__c = 'Active'];
// Merge and deduplicate using a Map<Id, Account>
Map<Id, Account> combined = new Map<Id, Account>(westAccounts);
combined.putAll(new Map<Id, Account>(activeAccounts));
```

This works only if both fields are individually indexed. Each sub-query can use its own index.

**Why not the alternative:** A single OR query cannot use an index on only one branch. Both branches must be indexed and selective, or Salesforce falls back to a full-table scan.

### Pattern 3: Dynamic SOQL with Field Sets

**When to use:** Query fields need to be configurable by admins without code changes, or the query is built dynamically.

**How it works:**

Use Salesforce field sets defined on the object in Setup. In Apex:
```apex
List<Schema.FieldSetMember> fields = SObjectType.Account.fieldSets.MyFieldSet.getFields();
String query = 'SELECT Id';
for (Schema.FieldSetMember f : fields) {
    query += ', ' + f.getFieldPath();
}
query += ' FROM Account WHERE OwnerId = :userId LIMIT 200';
List<Account> results = Database.query(query);
```

**Important:** The same selectivity rules apply to dynamic SOQL. A `Database.query()` call with a non-selective WHERE clause will time out exactly as a static SOQL query would. Always ensure the WHERE clause in dynamic SOQL uses indexed fields.

**Avoid SELECT * patterns:** Do not query all fields using `FIELDS(ALL)` or `FIELDS(STANDARD)` in Apex — this is expensive on objects with many fields and large data volumes. Explicit field lists are always preferred.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Query cost > 1.0 in Query Plan, uses a formula field filter | Remove formula field from WHERE; store value in a regular field and index it | Formula fields are not indexable |
| OR across two fields, both custom, both selective | Decompose into two queries and merge in Apex | OR requires all branches to be indexed and selective |
| Custom field used as a primary filter on 1M+ records | Request custom index via Salesforce Support | Custom fields are not indexed by default |
| Query uses `LIKE '%value%'` (leading wildcard) | Switch to SOSL search if full-text search is needed; remove leading wildcard if not required | Leading wildcards prevent index usage with no workaround |
| Object has 10M+ records and recurring reports on same field subset | Request skinny table via Salesforce Support | Eliminates join overhead on read-heavy, large-volume objects |
| Query uses `WHERE Field__c = null` on non-indexed field | Request null-inclusive custom index or restructure query | Index tables exclude null rows by default |
| ORDER BY on non-selective query | Make the query selective first; ORDER BY alone does not help | ORDER BY applied after scan increases cost, not reduces it |
| Two-field filter pattern (WHERE f1 = :x ORDER BY f2) | Request two-column custom index on (f1, f2) | Single-column indexes are less efficient for this pattern |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking query optimization work complete:

- [ ] Query Plan tool shows cost < 1.0 for the optimized query
- [ ] All WHERE clause fields are either standard indexed or have a confirmed custom index
- [ ] No leading LIKE wildcards (`LIKE '%value'` or `LIKE '%value%'`) in the WHERE clause
- [ ] No formula fields referenced in the WHERE clause
- [ ] OR conditions either use only indexed, selective fields or have been decomposed
- [ ] Dynamic SOQL uses an explicit field list, not `FIELDS(ALL)` or `FIELDS(STANDARD)`
- [ ] A LIMIT clause is present where appropriate
- [ ] NULL-filter queries use a null-inclusive custom index if null filtering is required
- [ ] Skinny table request has been submitted to Support if object has 10M+ records and qualifies

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **The 10% selectivity threshold is per field, not per combined WHERE clause** — A query with two non-selective filters joined by AND is not automatically selective. The optimizer evaluates each filter independently and uses the threshold rules for AND/OR combinations. Two 15%-selective filters joined by AND may still trigger a full-table scan.
2. **Custom indexes do not help queries with leading LIKE wildcards** — `LIKE '%value%'` and `LIKE '%value'` patterns prevent any index from being used. There is no workaround short of restructuring the query or switching to SOSL.
3. **Adding ORDER BY to a non-selective query makes it worse, not better** — ORDER BY is evaluated after the initial scan. It adds a sort step on top of an already-expensive full-table scan and increases total cost.
4. **Soft-deleted records count toward selectivity calculations** — If an object has a large recycle bin population, the total record count used in selectivity thresholds includes those soft-deleted records. A filter that appears selective may not be once deleted records are counted. Use `SELECT COUNT() FROM Object__c WHERE IsDeleted = false` to get the live count.
5. **Custom indexes are not copied to most sandbox types** — Custom indexes created via Salesforce Support in production are copied to Full sandboxes only. Developer, Developer Pro, and Partial sandboxes do not receive them. Query Plan results and performance in those sandboxes may not reflect production behavior.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Optimized SOQL query | Rewritten query using indexed fields and avoiding non-selective patterns |
| Query Plan interpretation | Cost value, plan type, and recommended action based on Developer Console output |
| Custom index request guidance | Field API name, object, and justification to include in a Salesforce Support case |
| Skinny table request guidance | Field list, object, and qualifying query patterns to include in a Salesforce Support case |
| Query optimization report | Filled template from `templates/soql-query-optimization-template.md` |

---

## Related Skills

- `apex-cpu-and-heap-optimization` — Use when the issue is Apex CPU time or heap consumption, not query performance or query timeouts
- `soql-fundamentals` — Use when writing or learning basic SOQL syntax; this skill assumes SOQL fundamentals are already known
- `data-model-design-patterns` — Use when the index strategy decision needs to be incorporated into a broader object design or data model review
- `limits-and-scalability-planning` — Use when planning query performance at scale across multiple objects and future data growth milestones
- `data-skew-and-sharing-performance` — Use when query slowness is caused by ownership skew or sharing recalculation, not by filter non-selectivity
