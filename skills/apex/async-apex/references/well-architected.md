# Well-Architected Notes: Async Apex

## Relevant Pillars

### Scalability

Async Apex is often the mechanism that makes a design scale past a single transaction. Queueable, Batch, and scheduled dispatch patterns help distribute work into governor-safe units.

Tag findings as Scalability when:
- the workload can exceed synchronous governor limits
- a trigger or controller tries to process too much in one transaction
- a team chooses Batch because of record volume, not habit

### Performance

Performance improves when heavy work moves out of the user transaction and into background processing with the right chunk size or queue depth.

Tag findings as Performance when:
- the user is waiting on work that should happen after commit
- batch scope size is mismatched to the actual API or DML load
- a scheduler is doing heavy work inline instead of dispatching a worker

### Reliability

Async work fails differently from synchronous work. Monitoring, retries, and partial-success design decide whether failures are actionable or silent.

Tag findings as Reliability when:
- a Queueable or Batch has no durable error reporting
- async fan-out creates unpredictable job counts
- partial success is needed but the async worker still uses all-or-none behavior

## Architectural Tradeoffs

- **Queueable vs Batch:** Queueable is simpler and better for application-level async work; Batch is better when volume or fresh limits per scope are the actual need.
- **Legacy future vs modernization:** `@future` is still valid for narrow cases, but modern designs usually benefit from Queueable visibility and composition.
- **Schedule worker vs schedule dispatcher:** Inline schedulers look simple initially and become expensive operationally later.

## Anti-Patterns

1. **Enqueueing jobs in a loop**: operationally noisy and limit-prone (50 enqueues per synchronous transaction, 1 per asynchronous one).
2. **Using Batch for small transactional after-save work**: too much framework overhead for a Queueable problem, and it competes for 5 batch slots.
3. **Treating `@future` as the default async primitive**: loses job IDs, non-primitive state, and chaining; Salesforce recommends Queueable instead.

## Official Sources Used

- Apex Developer Guide, Summer '26 (262): "Execution Governors and Limits" (Per-Transaction Apex Limits, Salesforce Platform Apex Limits; pdftotext lines L19529 to L19837), "Asynchronous Apex," "Queueable Apex" and "Queueable Apex Limits," "Detecting Duplicate Queueable Jobs," "Future Annotation," "Future Method Considerations," "Future Methods," "Testing Future Methods," "Batch Apex Governor Limits," "Holding Batch Jobs in the Apex Flex Queue," "Testing Batch Apex," "Apex Scheduler Limits," "Apex Scheduler Notes and Best Practices." https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Object Reference for the Salesforce Platform, Summer '26 (262): "AsyncApexJob" (Status values including Holding for the flex queue). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Platform Events Developer Guide, Summer '26 (262): Publish Immediately behavior and rollback. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/platform_events.pdf
- Salesforce Developer Limits and Allocations Quick Reference, Summer '26 (262): asynchronous Apex limits summary. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf

### Earlier references kept from version 1.0.0 (checked 2026-10-03: atlas pages return a script shell, help.salesforce.com returns an app shell, and Well-Architected guide pages redirect to the home page, so no claim in this skill rests on these links)

- Apex Developer Guide, Execution Governors and Limits (atlas page): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Apex Developer Guide, Future Methods (atlas page): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_invoking_future_methods.htm
- Apex Developer Guide, Queueable Apex (atlas page): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_queueing_jobs.htm
- Apex Reference Guide: `Queueable`, `Database.Batchable`, and related API reference
- Salesforce Well-Architected Overview: scalability, performance, and reliability framing
