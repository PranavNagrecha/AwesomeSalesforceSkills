# Well-Architected Notes — Governor Limit Recovery Patterns

## Relevant Pillars

- **Reliability** — Governor limits are the most common cause of unplanned Apex transaction failures in production. Proactive limit checking and savepoint-based recovery directly reduce the blast radius of limit breaches: partial results are preserved, failed units are queued for retry, and users receive actionable errors instead of opaque system failures.
- **Performance Efficiency** — CPU time and heap limits force explicit resource budgeting. Designing code to checkpoint against `Limits.getCpuTime()` and `Limits.getHeapSize()` surfaces performance regressions early and encourages efficient data structures, lazy loading, and early termination patterns.
- **Operational Excellence** — Limit headroom telemetry (logging remaining SOQL/DML budget at key checkpoints) feeds into monitoring dashboards and alerting. `BatchApexErrorEvent` subscribers produce structured retry queues that ops teams can observe without parsing raw debug logs.

## Architectural Tradeoffs

**Proactive checkpoints vs. partition-at-design-time:** Limits class checkpoints are a runtime safety net, not a substitute for correct architectural partitioning. A loop that issues one SOQL per record is still a design problem even if it has a checkpoint. Checkpoints should be the last defense, not the primary design strategy.

**Savepoints vs. separate transactions:** Using savepoints to achieve partial rollback within a single transaction keeps the work in one context, but it tightens the DML budget and adds complexity. For most bulk operations, designing for independent idempotent units (each record succeeds or fails on its own) is simpler and more scalable than savepoint-based recovery.

**BatchApexErrorEvent as observability vs. compensation:** The event is best used for observability and lightweight compensation (status flag updates, notifications). It is not appropriate for complex multi-step compensation logic — that belongs in a dedicated retry batch or queueable triggered by the status flag update.

## Anti-Patterns

1. **Try/catch as limit recovery** — Using `try/catch(Exception e)` to "handle" governor limits. `LimitException` is uncatchable; the catch block never fires. The correct pattern is proactive headroom checks with `Limits.*` before the operation.

2. **Savepoints as error-swallowing** — Setting a savepoint, performing risky operations, catching all exceptions, rolling back silently, and continuing without surfacing the error or deferring the work. This masks failures, leaves no audit trail, and silently drops records that needed processing.

3. **Assuming rollback clears all state** — Rolling back a savepoint and assuming the Apex runtime is fully reset. Static variables, in-memory sObject Id fields, and any external side effects (platform events published before the rollback) are not reverted. Treating rollback as a full-reset leads to phantom record processing and incorrect cache state.

## Official Sources Used

- Apex Developer Guide — Execution Governors and Limits — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Apex Developer Guide — System.Limits Class — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_limits.htm
- Apex Developer Guide — Using Governor Limit Email Warnings — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing_governor_limits.htm
- Apex Developer Guide — Database.setSavepoint and Database.rollback — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_transaction_control.htm
- Apex Developer Guide — BatchApexErrorEvent — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_batch_error_event.htm
- Salesforce Well-Architected — Reliability Pillar — https://architect.salesforce.com/docs/architect/well-architected/guide/reliability.html
- Apex Developer Guide (main) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
