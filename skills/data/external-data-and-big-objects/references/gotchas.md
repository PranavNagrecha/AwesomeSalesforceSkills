# Gotchas — External Data and Big Objects

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Non-Leading Index Column Queries Return Zero Results Silently

**What happens:** A Big Object query that looks perfectly reasonable comes back empty, or is rejected outright, and the reason is the shape of the WHERE clause rather than the data.

**When it occurs:** When the filter is not a gapless left-to-right prefix of the composite index. Per the SOQL and SOSL Reference, verbatim: "A SOQL query can only filter on the fields defined in the big object's index, in the order that they are defined, without gaps." For composite index `(AccountId__c, EventDate__c, EventType__c)`, filtering `WHERE EventDate__c = :date` skips the leading `AccountId__c` and is not a valid big object query.

Operator support compounds this. Index fields *before* the last one you filter on accept **`=` only** — no ranges. The last filtered field additionally accepts `<`, `>`, `<=`, `>=`, and `IN`. And `!=`, `LIKE`, `NOT IN`, `EXCLUDES`, `INCLUDES` are unsupported anywhere in the query. A design that assumed it could range-filter a middle index column will not work, and the fix is an index redesign, not a query rewrite.

**How to avoid:** Always design queries and indexes together. Draw out every query pattern before defining the composite index. Ensure every query filters on a continuous left-to-right prefix of the index fields. If two different query patterns need different leading columns, create two separate Big Objects or redesign the index to accommodate the most critical access pattern.

---

## Gotcha 2: `Database.insertImmediate` Failures Are Silent Unless Explicitly Checked

**What happens:** Records intended for a Big Object are silently dropped. The calling Apex method completes without exception. Downstream processes find no data in the Big Object.

**When it occurs:** `Database.insertImmediate()` never throws an exception on failure — it always returns a `Database.SaveResult`. If the caller discards the return value (which is valid syntax), insert failures are completely invisible. Common failure causes include index field values that violate the uniqueness constraint defined by the composite index, or fields exceeding defined max lengths.

**How to avoid:** Always capture the `Database.SaveResult` return value and inspect `result.isSuccess()`. Log failures to a durable error store (a custom object, a platform event, or an external log sink). In high-throughput paths where every record matters, consider a compensating retry queue for failed inserts.

```apex
// Correct: capture and check the result
Database.SaveResult sr = Database.insertImmediate(bigObjectRecord);
if (!sr.isSuccess()) {
    for (Database.Error err : sr.getErrors()) {
        // Route to your error handling / logging infrastructure
        logInsertError(err.getStatusCode(), err.getMessage(), bigObjectRecord);
    }
}
```

---

## Gotcha 3: The Big Object Read Path You Read About (Async SOQL) Was Retired in Summer '23

**What happens:** A design specifies Big Object reads via `POST /services/data/vXX.0/async-queries/` with a `targetObject`. The call returns 404. There is no deprecation warning, no shim, and no equivalent replacement API — the whole job-with-a-target-object model is gone.

**When it occurs:** Constantly, and it is structurally likely rather than a rare slip. Async SOQL was the documented Big Object query path for roughly six years, so nearly every blog post, Trailhead-adjacent write-up, Stack Exchange answer, and LLM training corpus predating mid-2023 presents it as *the* answer. Salesforce retired it with the **Summer '23** release (Help article 000394892). The corpus never caught up, so confidently-worded Async SOQL advice keeps being produced by both humans and models.

The damage is sequenced badly: the archival *write* path works, so a team builds ingestion, runs it for months, and hits the missing read path only when the first compliance or analytics query is due — with hundreds of millions of rows already landed.

**How to avoid:** Treat any mention of `async-queries` or `AsyncQueryJob` as a defect on sight. Per Salesforce Help: "You must use the Bulk API or batch Apex to query or report on custom Big Objects." In practice:

- **Standard SOQL** for bounded reads (index-prefix filters, normal query-row limits apply).
- **Batch Apex** over `Database.getQueryLocator` on the `__b` object for anything past one transaction. This replaces the job semantics — but *not* the automatic write into a target object. You aggregate in `execute()` and insert your summary rows in `finish()` yourself.
- **Bulk API query** to extract rows off-platform.

Separately, and still true: none of these paths reach External Objects (`__x`). If you need batch analytics over data in an external system, ingest a copy into a Big Object via Bulk API and read that, run the analytics in the external system, or use Data Cloud.

---

## Gotcha 4: Big Object Records Cannot Be Updated — Only Upserted via Index Match

**What happens:** A developer tries to update a Big Object record and receives an error, or submits what they believe is an update but gets a duplicate record instead.

**When it occurs:** Big Objects do not support the standard DML `update` operation. The only way to modify a Big Object record is to use `Database.insertImmediate()` with a record whose index field values exactly match an existing record — this performs an upsert based on the composite index. If any index field value differs, a new record is created rather than the existing one being modified.

**How to avoid:** Treat Big Object records as append-only or explicitly design for upsert-by-index. If you need to "correct" a record, re-insert with the same index key values (the composite index fields must be identical) and updated non-index field values. Communicate this constraint clearly to data engineers expecting standard CRUD semantics.

---

## Gotcha 5: External Object SOQL Queries in Loops Exhaust Callout Limits Immediately

**What happens:** An Apex batch job or trigger queries an External Object inside a loop. After the first few iterations, the transaction hits the 100-callout-per-transaction limit and throws a `CalloutException`, rolling back the entire transaction.

**When it occurs:** Every SOQL query against an External Object fires one callout to the external data source. A `for` loop over a list of 200 records, each querying an External Object for related data, fires 200 callouts — 100 over the limit.

**How to avoid:** Move External Object queries outside loops. Collect all the external IDs needed, issue a single `IN`-clause SOQL query against the External Object (one callout for the batch), and map results back to the records in-memory. Also monitor the Salesforce Connect request log in Setup to detect unexpectedly high callout volumes before they hit production limits.
