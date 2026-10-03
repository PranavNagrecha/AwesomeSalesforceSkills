# Governor Limits: Well-Architected Mapping

## Scalability

**Directly implements:**
- The entire governor limits topic is about Scalability: code that works for 1 record but fails at 200 (or 2,000 for platform event and CDC triggers) is not production-grade
- Bulkification patterns (collect, query once, map, process, DML once) are the core Scalability pattern in Apex
- Batch Apex enables processing millions of records by breaking work into governor-limit-safe chunks

**Tag a finding as Scalability when:**
- SOQL or DML is inside a loop over `Trigger.new` or any collection
- A method works in manual testing but will fail during a bulk data import or integration sync
- A transaction processes a number of records close to DML row or SOQL row limits

---

## Reliability

**How it connects:**
- A governor limit exception can't be handled (Apex Developer Guide 262, Execution Governors and Limits) and rolls back the transaction, so the user's save or the integration batch fails
- Async offloading with proper error handling (per-record try/catch in Queueable, `allOrNone=false` in Batch) prevents one bad record from failing a whole batch
- `Database.Stateful` in Batch preserves error counts across `execute()` calls for operational visibility

**Tag a finding as Reliability when:**
- A `LimitException` in a trigger causes partial rollback of a user-visible save operation
- A Queueable has no per-record error handling: one callout failure stops processing all remaining records
- `allOrNone=true` DML in Batch `execute()` causes entire chunk to roll back on one invalid record

---

## Performance

**How it connects:**
- CPU time limit (10,000 ms sync, 60,000 ms async; L19579) is a direct performance constraint: complex String operations, nested loops, and JSON parsing in loops are common causes
- Moving heavy processing to Queueable (60s budget) is a performance strategy, not just an architectural preference
- Batch Apex with the right scope size (default 200; up to 2,000 with a QueryLocator) balances throughput with per-scope limits

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
- Batch Apex `finish()` has no notification: failures are silent until a user reports missing data

## Official Sources Used

- Apex Developer Guide, Summer '26 (262): "Execution Governors and Limits" (Per-Transaction Apex Limits, Certified Managed Package Limits, Salesforce Platform Apex Limits, Static and Size-Specific Limits; pdftotext L19508 to L19916, quoted in `limits-table.md`), "Apex Cursors," "Asynchronous Apex and Mock Callouts," "Batch Apex Governor Limits," "Testing Future Methods." https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Apex Reference Guide, Summer '26 (262): `Test.startTest()`, `Limits.getApexCursors()`, `Limits.getApexCursorRows()`. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_reference_guide.pdf
- Salesforce Developer Limits and Allocations Quick Reference, Summer '26 (262): Apex limits summary. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf

### Earlier references kept from version 1.1.0 (checked 2026-10-03: atlas pages return a script shell, help.salesforce.com returns an app shell, and Well-Architected guide pages redirect to the home page, so no claim in this skill rests on these links)

- Salesforce Well-Architected Overview: performance and operability framing for transaction design
- [Execution Governors and Limits (Apex Developer Guide, atlas page)](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm): per-transaction limit values (the 262 PDF above was read instead)
- [Understanding Execution Governors and Limits (atlas page)](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_limits_intro.htm): how limits are enforced per transaction
- [Best Practices for Improving Apex Performance (atlas page)](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_limits_tips.htm): bulkification guidance
