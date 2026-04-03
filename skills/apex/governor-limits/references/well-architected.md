# Governor Limits — Well-Architected Mapping

## Scalability

**Directly implements:**
- The entire governor limits topic is about Scalability — code that works for 1 record but fails at 200 is not production-grade
- Bulkification patterns (collect → query once → map → process → DML once) are the core Scalability pattern in Apex
- Batch Apex enables processing millions of records by breaking work into governor-limit-safe chunks

**Tag a finding as Scalability when:**
- SOQL or DML is inside a loop over `Trigger.new` or any collection
- A method works in manual testing but will fail during a bulk data import or integration sync
- A transaction processes a number of records close to DML row or SOQL row limits

---

## Reliability

**How it connects:**
- Code that hits governor limits throws unhandled `LimitException` and rolls back the entire transaction — potentially causing data loss or incomplete saves
- Async offloading with proper error handling (per-record try/catch in Queueable, `allOrNone=false` in Batch) prevents one bad record from failing a whole batch
- `Database.Stateful` in Batch preserves error counts across `execute()` calls for operational visibility

**Tag a finding as Reliability when:**
- A `LimitException` in a trigger causes partial rollback of a user-visible save operation
- A Queueable has no per-record error handling — one callout failure stops processing all remaining records
- `allOrNone=true` DML in Batch `execute()` causes entire chunk to roll back on one invalid record

---

## Performance

**How it connects:**
- CPU time limit (10s sync, 60s async) is a direct performance constraint — complex String operations, nested loops, and JSON parsing in loops are common causes
- Moving heavy processing to Queueable (60s budget) is a performance strategy, not just an architectural preference
- Batch Apex with the right chunk size (200 is typical default; can tune down to 1 for callouts) balances throughput with per-record memory

**Tag a finding as Performance when:**
- CPU time approaches the limit due to complex in-memory processing that could be simplified
- Batch chunk size is set higher than the API being called can handle, causing timeouts

---

## Operational Excellence

**How it connects:**
- `LimitMonitor.checkpoint()` (dev-time tool) makes limit consumption visible before reaching production
- Batch `finish()` with completion notification and error counts provides observability into scheduled processing
- Scheduled Apex pointing at a dispatch Batch (rather than many individual scheduled classes) keeps the 100-job limit manageable

**Tag a finding as Operational Excellence when:**
- No monitoring of limit usage in a critical service class that processes variable-sized inputs
- Batch Apex `finish()` has no notification — failures are silent until a user reports missing data

## Official Sources Used

- Salesforce Well-Architected Overview — performance and operability framing for transaction design
- Apex Developer Guide — transaction, bulk, and async behavior guidance
- Apex Reference Guide — Limits class and async API reference confirmation
