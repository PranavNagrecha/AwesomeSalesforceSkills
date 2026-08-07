# External Data and Big Objects — Work Template

Use this template when designing or reviewing Big Object schemas, Big Object read paths, or External Object integrations.

> **Async SOQL was retired in Summer '23.** If the design you are reviewing routes Big Object reads through `POST /async-queries/` or `AsyncQueryJob`, that is the defect — the endpoint does not exist. Read via standard SOQL, Batch Apex, or Bulk API query.

## Scope

**Skill:** `external-data-and-big-objects`

**Request summary:** (fill in what the user asked for)

**Mechanism selected:** [ ] Big Object  [ ] External Object  [ ] Both

---

## Context Gathered

Answer these before proceeding:

| Question | Answer |
|---|---|
| Estimated record volume (current) | |
| Estimated annual growth rate | |
| Retention requirement (years) | |
| Query patterns (which fields in WHERE, ORDER BY) | |
| Latency requirement (real-time vs async/batch) | |
| Data location (stays external vs ingest into Salesforce) | |
| Existing org data storage headroom | |

---

## Big Object Design (if applicable)

### Object Name

`<ObjectName>__b`

### Fields

| Field API Name | Type | Length / Precision | In Composite Index? | Index Position |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |

### Composite Index Definition

List index fields in left-to-right order. This order determines query filter order.

1. `<FieldName>__c` — sort direction: ASC / DESC
2. `<FieldName>__c` — sort direction: ASC / DESC
3. `<FieldName>__c` — sort direction: ASC / DESC (if needed)

### Query Patterns Supported by This Index

Document every planned query and verify each one filters on a gapless left-to-right prefix of the index. Index fields *before* the last one you filter on accept `=` only; the last filtered field also accepts `<`, `>`, `<=`, `>=`, `IN`. `!=`, `LIKE`, `NOT IN`, `EXCLUDES`, and `INCLUDES` are unsupported anywhere.

| Query Pattern | Leading Index Columns Used | Valid? |
|---|---|---|
| `WHERE Field1 = :x AND Field2 >= :y` | Field1, Field2 | Yes — range on the last filtered field |
| `WHERE Field2 = :y` (skips Field1) | Field2 only | **NO — gap in the index prefix** |
| `WHERE Field1 >= :x AND Field2 = :y` | Field1, Field2 | **NO — range on a non-final index field** |
| `WHERE Field1 LIKE :x` | Field1 | **NO — `LIKE` unsupported on big objects** |

---

## Insert Pattern

```apex
// Template: Database.insertImmediate with error checking
<ObjectName>__b record = new <ObjectName>__b(
    <IndexField1>__c = /* value */,
    <IndexField2>__c = /* value */,
    <DataField1>__c  = /* value */
);

Database.SaveResult sr = Database.insertImmediate(record);
if (!sr.isSuccess()) {
    for (Database.Error err : sr.getErrors()) {
        // Replace with your logging / alerting mechanism
        System.debug(LoggingLevel.ERROR,
            'Big Object insert failed [' + err.getStatusCode() + ']: ' + err.getMessage());
    }
}
```

---

## Big Object Read Path

Pick one and record why. Async SOQL is not on the list — it was retired in Summer '23.

- [ ] **Standard SOQL** — result set fits inside the Apex query-row limit. Record the expected max row count: ______
- [ ] **Batch Apex** over `Database.getQueryLocator` — result set exceeds one transaction. This is the replacement for Async SOQL at volume.
- [ ] **Bulk API query** — rows are being extracted off-platform.

```apex
// Batch Apex skeleton. Note what Async SOQL used to do and no longer does:
// it wrote aggregate results into a targetObject as a side effect of the job.
// Nothing does that now — accumulate state and write the summary yourself.
public class <Name>Rollup implements Database.Batchable<SObject>, Database.Stateful {

    private Map<String, Integer> accumulator = new Map<String, Integer>();

    public Database.QueryLocator start(Database.BatchableContext bc) {
        // WHERE must be a gapless left-to-right prefix of the composite index.
        return Database.getQueryLocator([
            SELECT <fields>
            FROM <ObjectName>__b
            WHERE <IndexField1>__c = :value1 AND <IndexField2>__c >= :value2
        ]);
    }

    public void execute(Database.BatchableContext bc, List<<ObjectName>__b> scope) {
        // accumulate into instance state
    }

    public void finish(Database.BatchableContext bc) {
        // insert <TargetObject__c> summary rows here
    }
}
```

**Monitoring:** track the job via `AsyncApexJob` (`Status`, `NumberOfErrors`, `ExtendedStatus`) — the same way as any other Batch Apex job. There is no separate Big Object job API.

---

## External Object Design (if applicable)

| Property | Value |
|---|---|
| External Object API name | `<Name>__x` |
| External data source | |
| OData version | 2.0 / 4.0 / Custom Apex Adapter |
| External entity name | |
| Estimated records per SOQL query | |
| Callout timeout tolerance | |

### Callout Budget Check

Confirm the External Object is not queried inside a loop:

- [ ] All External Object queries use an `IN` clause over a collected set, not individual queries per record
- [ ] Maximum callouts per transaction estimated: _____ (must be < 100)
- [ ] Timeout for external endpoint documented: _____ seconds (Salesforce default limit: 10 s)

---

## Review Checklist

- [ ] All query patterns filter on a gapless left-to-right prefix of the composite index, with ranges only on the last filtered field
- [ ] `Database.insertImmediate()` return values are checked and failures are logged
- [ ] No reference anywhere to `async-queries` / `AsyncQueryJob` (retired Summer '23)
- [ ] If the design produces aggregates, the write into the summary object is implemented explicitly in `finish()` — nothing materialises it for you
- [ ] External Object queries are not inside loops
- [ ] Big Object storage growth projection reviewed against org storage allocation
- [ ] No triggers, reports, or roll-up summaries are placed on the Big Object
- [ ] `insertImmediate` upsert semantics (index-based) are understood and documented for the team

---

## Notes

Record any deviations from the standard pattern and the rationale:

(fill in)
