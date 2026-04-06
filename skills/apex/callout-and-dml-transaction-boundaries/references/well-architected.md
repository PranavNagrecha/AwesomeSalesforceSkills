# Well-Architected Notes — Callout and DML Transaction Boundaries

## Relevant Pillars

- **Reliability** — Separating callouts from DML into distinct transaction boundaries prevents runtime exceptions and ensures that both the database write and the external call execute successfully. A failed callout does not roll back committed DML, and vice versa, which makes each operation independently reliable.
- **Performance** — Deferring callouts to Queueable Apex avoids holding synchronous transactions open while waiting for external system responses. Users see faster page loads and trigger execution completes sooner.
- **Scalability** — The Queueable pattern scales to bulk operations. A single enqueue can process multiple record IDs, and chaining allows sequential callouts without blocking the synchronous path.
- **Operational Excellence** — Explicit integration status fields and error handling in Queueable classes make failures visible. Operations teams can query for failed sync records and retry without developer intervention.

## Architectural Tradeoffs

The core tradeoff is **synchronous simplicity versus eventual consistency**:

- **Callout-first synchronous** keeps the code simple and the transaction atomic, but it only works when no DML has occurred earlier in the transaction. It also means the user waits for the external system to respond.
- **Queueable after DML** decouples the callout from the user-facing transaction, improving responsiveness, but introduces eventual consistency. The external system may not reflect Salesforce data immediately, and failure handling becomes the developer's responsibility.
- **Chained Queueable** handles complex multi-callout flows but adds operational complexity. Each link in the chain must handle its own failures, and debugging requires tracing across multiple async jobs.

## Anti-Patterns

1. **Catch-and-ignore the CalloutException** — Wrapping a post-DML callout in a try-catch and logging the error creates silent integration failures. The callout never executes; the catch block just hides the problem. Fix the transaction boundary instead.
2. **Using Database.rollback() to clear uncommitted work** — Savepoints and rollbacks do not reset the callout restriction. Developers who rely on this pattern get the same exception after the rollback. The only fix is a separate transaction.
3. **Passing full sObjects to @future methods** — `@future` methods cannot accept sObject parameters. Developers who try this get a compile error. Even when passing IDs, @future cannot chain, making it inferior to Queueable for most use cases.

## Official Sources Used

- Apex Developer Guide: Invoking Callouts Using Apex — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts.htm
- Apex Developer Guide: Callout Limits and Limitations — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_timeouts.htm
- Salesforce Help: "You have uncommitted work pending" — https://help.salesforce.com/s/articleView?id=000389332
- Apex Developer Guide: Queueable Apex — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_queueing_jobs.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
