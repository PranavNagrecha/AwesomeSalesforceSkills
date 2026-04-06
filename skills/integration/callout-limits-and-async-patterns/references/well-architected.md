# Well-Architected Notes — Callout Limits And Async Patterns

## Relevant Pillars

- **Reliability** — Selecting the wrong callout pattern (e.g., synchronous callout after DML) produces hard runtime failures. The correct async pattern eliminates these failure modes and ensures callout success is not dependent on transaction ordering.
- **Scalability** — The 100-callout limit per transaction requires thoughtful design for high-volume integrations. Batch Apex + Queueable chaining enables integration patterns that scale to millions of records without hitting limits.
- **Operational Excellence** — Async callout patterns (Queueable) enable failure handling and retry logic that synchronous callouts do not support. Queueable jobs can be monitored in Setup > Apex Jobs, and error handling in `execute()` can log failures for review.

## Architectural Tradeoffs

- **Synchronous vs Async:** Synchronous callouts return results to the caller immediately but cannot run after DML and add latency to user-facing operations. Async callouts (Queueable) are non-blocking but results cannot be returned to the UI directly.
- **@future vs Queueable:** @future is simpler to implement but cannot pass sObjects, cannot chain, and cannot be called from Batch. Queueable removes all these restrictions at the cost of slightly more code.
- **Continuation vs Queueable for LWC:** Continuation keeps the user session open and returns a result to the LWC. Queueable runs independently and cannot return a value to the calling UI component. Choose based on whether the user needs to wait for the result.

## Anti-Patterns

1. **Making callouts directly in triggers without checking for prior DML** — Any DML in the trigger transaction (even from a separate class) invalidates synchronous callouts. Always use Queueable for trigger-initiated callouts.
2. **Using @future for scenarios requiring sObject parameters or chaining** — @future is effectively deprecated for new integrations in favor of Queueable. It should only be used for legacy code or trivially simple fire-and-forget operations.
3. **Hardcoding callout endpoints in Apex** — Named Credentials should be used for all callout endpoints. Hardcoding makes endpoint rotation, environment switching, and authentication changes require code deployments.

## Official Sources Used

- Apex Developer Guide — Apex Callouts — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts.htm
- Apex Developer Guide — Governor Limits — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Apex Developer Guide — Continuation Class — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_continuation.htm
- Salesforce Apex Reference Guide — Continuation — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_Continuation.htm
- REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm
