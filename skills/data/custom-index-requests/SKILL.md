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
  - "prepare the evidence Salesforce Support needs before they add a custom index"
  - "deploy a CustomIndex file after Support approves a null-inclusive index"
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
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-10-19
---

# Custom Index Requests

This skill activates when a query on a high-volume object cannot be made selective with the indexes the org already has, and someone must decide between marking a custom field External ID or Unique, asking Customer Support for a custom index, a two-column index, or a skinny table, and then proving the result. Query rewriting belongs to `data/soql-query-optimization`; this skill is about getting the right index and evidence.

---

## Before Starting

Gather this context before working on anything in this domain:

- The slow query with real literal values, and its plan from Developer Console Query Plan or `GET /services/data/v67.0/query/?explain=<query>`.
- The object's row count, including Recycle Bin rows, and a `GROUP BY` count of the filter values the query uses.
- Whether the filter field is custom or standard, its data type, and whether it is a formula.
- Whether the filter compares with null, and whether the query also sorts.
- Which sandbox will be used to test: custom indexes reach every sandbox created from production after the index exists; skinny tables reach only Full sandboxes.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "How many rows match the filter value, out of how many rows in total?" | The optimizer only uses a custom index under 10% of the first million rows and 5% beyond (Gotcha 3) | Threshold arithmetic attached to the request, before anyone files a case |
| "Must the field's values be unique?" | Unique enforces uniqueness; External ID alone does not, and both create an index (Gotcha 1) | The right flag, and no surprise duplicate errors or upsert ambiguity |
| "Is the field a formula, long text, rich text, encrypted text, or a multi-select picklist?" | Those types can't take a custom index (Gotcha 2) | A stored copy of the value designed before the request |
| "Does the query filter on null?" | Index tables leave out null rows unless Support builds a null-inclusive index (Gotcha 4) | A null-inclusive request, or a placeholder value instead of null |
| "Which field selects and which sorts, or are both always filtered together?" | A two-column index follows the documented column roles (Gotcha 5) | A column order in the case that matches the query |
| "Is the problem many reports reading the same fields across millions of rows?" | Skinny tables help read-only queries that use only their fields, and can hurt in the wrong context (Gotcha 6) | A skinny-table request scoped to a stable field list |
| "Where will we test, and when?" | Custom indexes reach all sandboxes created afterwards; skinny tables only Full sandboxes; statistics refresh nightly (Gotcha 7) | A test plan whose plans match production |

A proper request adds counts, a plan, and the exact index shape; a request that only says "please index this field" comes back with questions, or produces an index the optimizer never uses.

---

## Core Concepts

### Which index path applies

| Need | Path | Notes |
|---|---|---|
| Custom Auto Number, Email, Number, or Text field used as a filter | Mark it External ID (or Unique if values must be unique) | Salesforce creates the index; no case needed |
| Other custom field types, or a standard field not indexed by default | Customer Support case | Support evaluates the request |
| Null rows must be indexed | Support case for a null-inclusive index | Existing indexes must be rebuilt to include nulls |
| One field selects, another sorts (or both filter) | Support case for a two-column index | Same restrictions as single-column, except nulls are allowed in the second column |
| Many read-only queries over the same field subset | Support case for a skinny table | Up to 200 columns, no cross-object fields |

The Metadata API also has a `CustomIndex` type (API 50.0+, `.indx-meta` files in the `customindex` folder) with `allowNullValues` and, from API 61.0, `booleanIndexedValue`. Its special access rule says to review the LDV guide's index section and then contact Customer Support, so it records an index Support has agreed; it is not a self-service shortcut.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- objects/Lead/fields/Inbound_Key__c.field-meta.xml: External ID makes Salesforce index the field.
     externalId=false (the default) creates no index. Unique is a separate flag. -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Inbound_Key__c</fullName>
    <label>Inbound Key</label>
    <type>Text</type>
    <length>40</length>
    <externalId>true</externalId>
    <unique>false</unique>
</CustomField>
```

### Thresholds the request must meet

| Index type | Used when the filter matches less than | Examples from the LDV guide |
|---|---|---|
| Standard | 30% of the first million rows, 15% of rows beyond | 2M → 450,000; 5M → 900,000 |
| Custom | 10% of the first million rows, 5% of rows beyond | 500K → 50,000; 5M → 300,000 |

The optimizer checks each index against its own threshold with a pre-query against its statistics table, and the statistics are gathered nightly.

### What Support needs in the case

Org ID, object and row count, the literal query, the plan output, the field and its value distribution, the index shape (single, null-inclusive, two-column with column order, or skinny-table field list), how often the query runs, and what business process waits on it.

---

## Common Patterns

### Pattern 1: Self-service index on a custom key field

The query filters on a custom Text field that holds an integration key. Mark it External ID in the field metadata (above), deploy, and capture the plan again: `leadingOperationType` should be `Index` on that field. Add `unique` only if duplicates must be rejected.

### Pattern 2: Support-built index on a non-key field

The field is a picklist or a standard field, or the filter is on null. Attach the counts and plan to a case using `templates/custom-index-requests-template.md`. When Support confirms, capture the plan again in production and in a new sandbox.

### Pattern 3: Two-column index for a list view

An Account list view selects by `State__c` and sorts by `City__c`. Ask for a two-column index with `State__c` first and `City__c` second, the order the LDV guide uses for this case.

---

## Decision Guidance

| Situation | Recommended approach | Reason |
|---|---|---|
| Custom key field, values unique by design | External ID plus Unique | Index plus enforced uniqueness |
| Custom filter field with repeated values | External ID only, if Text/Number/Email/Auto Number | Index without a uniqueness constraint |
| Picklist, date, or standard field | Support case | Not available through field flags |
| Filter on null | Null-inclusive index, or store a placeholder value | Nulls are excluded from index tables by default |
| Filter matches more than the threshold | Change the query (add a selective filter) before any request | The optimizer will skip the index |
| Non-deterministic formula in the filter | Store the value in a regular field and index that | Non-deterministic formulas can't be indexed |
| Many reports over the same fields on millions of rows | Skinny table request | Avoids the join between standard and custom field tables |

---

## Recommended Workflow

1. Capture the plan and the `GROUP BY` counts, and record them in `templates/custom-index-requests-template.md` with the threshold arithmetic for the object's row count.
2. Pick the path from Decision Guidance; for a self-service index, edit the field's `.field-meta.xml` to set `externalId` (and `unique` only if required) to true.
3. Run `python3 skills/data/custom-index-requests/scripts/check_custom_index_requests.py --manifest-dir force-app/main/default` and fix every ERROR (for example, `externalId` set on a picklist, or a malformed `CustomIndex` file); review WARN lines on categorical fields made External ID or Unique.
4. For Support paths, file the case with the evidence list from Core Concepts; `references/support-case-worked-example.md` shows a filled one.
5. After the index exists, capture the plan in production and in a sandbox created afterwards; expect `Index` as the leading operation and `relativeCost` under 1.0, and re-check after the next nightly statistics run.

---

## Review Checklist

- [ ] The request carries a plan and value counts, with arithmetic for the real row count
- [ ] The filter value is under the custom-index threshold, or the query was changed first
- [ ] External ID and Unique were chosen deliberately (uniqueness is only enforced by Unique)
- [ ] No index is requested on a non-indexable type or non-deterministic formula
- [ ] Null filtering is covered by a null-inclusive index or a placeholder value
- [ ] Two-column requests state the column order; skinny-table requests list the fields
- [ ] Post-index plans were captured in production and in a sandbox created after the index
- [ ] The checker reports no ERROR lines

---

## Salesforce-Specific Gotchas

Full write-ups are in `references/gotchas.md`:

| # | Gotcha |
|---|---|
| 1 | External ID indexes the field but does not make it unique |
| 2 | Some field types can never take a custom index |
| 3 | An index that misses its threshold is simply not used |
| 4 | Null rows are not in the index unless Support rebuilds it |
| 5 | Two-column indexes have a selecting column and a sorting column |
| 6 | Skinny tables help only the queries they cover, and can hurt |
| 7 | Custom indexes reach every new sandbox; skinny tables reach only Full sandboxes |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Index decision | Self-service flag, Support index, two-column index, or skinny table, with the reason |
| Field metadata change | `.field-meta.xml` with `externalId` (and `unique` if required) set to true |
| Support case | Filled template with counts, plan, and index shape |
| CustomIndex metadata | `.indx-meta` file, only for an index Support has agreed |
| Validation record | Plans before and after, in production and a new sandbox |

---

## Related Skills

- `data/soql-query-optimization` — rewriting the query and reading plans
- `data/data-model-design-patterns` — choosing external ID and key fields at design time
- `data/external-data-and-big-objects` — when the data belongs in a big object instead
- `architect/large-data-volume-architecture` — object-level volume strategy
- `architect/limits-and-scalability-planning` — planning index strategy against growth
