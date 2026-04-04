# External Data and Big Objects — Work Template

Use this template when designing or reviewing Big Object schemas, Async SOQL jobs, or External Object integrations.

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

Document every planned Async SOQL query and verify each one uses a continuous left-to-right prefix of the index:

| Query Pattern | Leading Index Columns Used | Valid? |
|---|---|---|
| `WHERE Field1 = :x AND Field2 >= :y` | Field1, Field2 | Yes |
| `WHERE Field2 = :y` (skips Field1) | Field2 only | **NO — returns zero results** |

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

## Async SOQL Job Template (if applicable)

```http
POST /services/data/v62.0/async-queries/
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "SELECT <fields> FROM <ObjectName>__b WHERE <IndexField1>__c = '<value>' AND <IndexField2>__c >= <value>",
  "operation": "insert",
  "targetObject": "<TargetObject__c>",
  "targetFieldMap": {
    "<sourceField>": "<targetField__c>"
  }
}
```

**Poll for completion:**

```http
GET /services/data/v62.0/async-queries/<jobId>
Authorization: Bearer <token>
```

Expected terminal statuses: `Completed`, `Failed`, `Aborted`

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

- [ ] All Async SOQL query patterns use a continuous left-to-right prefix of the composite index
- [ ] `Database.insertImmediate()` return values are checked and failures are logged
- [ ] Async SOQL job polling logic is implemented (no inline result assumption)
- [ ] External Object queries are not inside loops
- [ ] Big Object storage growth projection reviewed against org storage allocation
- [ ] No triggers, reports, or roll-up summaries are placed on the Big Object
- [ ] `insertImmediate` upsert semantics (index-based) are understood and documented for the team

---

## Notes

Record any deviations from the standard pattern and the rationale:

(fill in)
