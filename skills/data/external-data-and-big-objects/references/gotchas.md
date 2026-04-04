# Gotchas — External Data and Big Objects

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Non-Leading Index Column Queries Return Zero Results Silently

**What happens:** An Async SOQL job completes with status `Completed` and zero errors, but the target object has zero new records. No error message is produced. The query appears to succeed but retrieves nothing.

**When it occurs:** When a WHERE clause filters on a column that is not the first (leading) column of the composite index, or when it skips a column in the middle of the index chain. For a Big Object with composite index `(AccountId__c, EventDate__c, EventType__c)`, a query `WHERE EventDate__c = :date` skips `AccountId__c` and returns nothing. Salesforce does not raise an error — it simply finds no matching partition.

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

## Gotcha 3: Async SOQL Cannot Query External Objects

**What happens:** A team designs a workflow where an External Object (backed by Salesforce Connect) holds the data and expects to run Async SOQL jobs over it for batch reporting. The job is submitted but fails or returns no results.

**When it occurs:** Async SOQL operates on data stored within the Salesforce Big Object storage tier and standard objects. It does not proxy callouts to external data sources the way synchronous SOQL against External Objects does. Submitting an Async SOQL query referencing an `__x` object will fail or return an error indicating the object is unsupported.

**How to avoid:** Async SOQL is for Big Objects and certain standard objects — not External Objects. If you need batch analytics over data in an external system, one of these approaches is correct: (a) periodically ingest a copy into a Big Object using the Bulk API, then run Async SOQL; (b) run the analytics directly in the external system; (c) use Salesforce Data Cloud for federated queries if licensed.

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
