# Well-Architected Notes — Entitlement Apex Hooks

## Relevant Pillars

- **Reliability** — SLA enforcement is a contractual commitment. Milestone completion code must handle bulk volumes, be idempotent where possible, and not fail silently. The silent-discard behavior of `IsCompleted = true` is a reliability anti-pattern because it produces no error signal and allows SLA violations to go undetected.
- **Performance** — Triggers on `Case` that query `CaseMilestone` must be bulk-safe. A trigger that issues one SOQL query per case record will hit governor limits at 101 cases. All queries must use `IN :idSet` patterns and all DML must operate on lists, not individual records in loops.
- **Operational Excellence** — Scheduled Apex for violation detection should include logging (Platform Events or custom object) and idempotency guards. Without these, re-runs after a failure silently reprocess or skip records, making SLA reporting unreliable.
- **Security** — `CaseMilestone` is a standard object with standard OLS/FLS. Service agents typically do not have edit access to `CaseMilestone`. Apex running in system context bypasses these checks, which is usually correct for automation but should be validated against the org's security model. Use `with sharing` on service classes unless there is an explicit reason to use `without sharing`.
- **Scalability** — For orgs with high case volumes, consider whether a trigger-based completion pattern will scale or whether a Batch Apex approach that processes milestones in chunks is more appropriate. Scheduled Apex for violation detection should use `LIMIT` in its query to stay within synchronous context limits.

## Architectural Tradeoffs

**Trigger vs. Scheduled Apex for milestone completion:**
An `after update` trigger on Case provides real-time completion as soon as the case field changes, which gives accurate `CompletionDate` timestamps. However, the trigger runs in the same transaction as the case save, which consumes CPU time and DML statements from the same governor limit budget. For orgs with complex case triggers already in place, consider whether the milestone completion can be deferred to a queueable job invoked from the trigger.

**Native milestone actions vs. Scheduled Apex for violation handling:**
The entitlement process supports native milestone actions (email alerts, field updates, outbound messages) triggered on violation. These are reliable, run outside the Apex governor limit model, and require no code maintenance. Scheduled Apex should only be used when the required violation response cannot be expressed in native actions — for example, creating related records, running complex logic, or calling external systems.

**Idempotency in violation detection:**
A scheduled job that processes violations without an idempotency guard will re-trigger business logic on every run until the milestone is manually resolved. This can cause duplicate tasks, emails, or escalations. The recommended guard is a boolean flag on the Case (`ViolationEscalated__c`) that is set once and excluded from subsequent queries.

## Anti-Patterns

1. **Writing IsCompleted instead of CompletionDate** — This is the highest-impact anti-pattern in the domain. It produces no error, passes all tests written against the wrong expectation, and silently leaves milestones open. The architectural risk is undetected SLA breaches. Always write `CompletionDate`.

2. **Trigger-based violation detection** — Implementing a `CaseMilestone` after-update trigger and checking for `IsViolated` state transitions assumes the platform fires a trigger when the background process sets `IsViolated = true`. It does not. The result is that the violation handler never runs, giving a false sense of security while violations are silently missed.

3. **Writing SlaExitDate to adjust deadlines at runtime** — Attempting to implement "dynamic SLA deadlines" by reading and writing `SlaExitDate` via Apex looks like it works in the Developer Console (no error) but has no effect. Organizations that require variable deadlines must model this through multiple entitlement processes with different time triggers, not through runtime field writes.

## Official Sources Used

- Salesforce Help: Set Up Entitlements and Milestones — https://help.salesforce.com/s/articleView?id=sf.entitlements_setup.htm
- Salesforce Help: Auto-Complete Case Milestones — https://help.salesforce.com/s/articleView?id=sf.entitlements_milestones_auto_complete.htm
- Salesforce Entitlements Implementation Guide (Spring '26) — https://help.salesforce.com/s/articleView?id=sf.entitlements_implementation_guide.htm
- CaseMilestone Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_casemilestone.htm
- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
