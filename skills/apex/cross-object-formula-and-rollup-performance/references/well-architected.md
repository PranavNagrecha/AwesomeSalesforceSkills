# Well-Architected Notes — Cross-Object Formula and Rollup Performance

## Relevant Pillars

- **Performance** — Cross-object formulas add query complexity at read time; rollup recalculations add write-time overhead. Both degrade as data volume grows. Proper spanning management and incremental rollup strategies keep transaction times predictable.
- **Scalability** — The 15 spanning relationship limit is a hard ceiling that constrains schema evolution. LDV rollup timeouts prevent orgs from growing child record volumes without schema redesign. Planning for these limits early avoids costly retrofits.
- **Reliability** — Stale rollup values in triggers cause silent logic errors that only manifest under specific timing conditions. Rollup filter blindness to distant record changes creates data integrity gaps that are difficult to detect and reproduce.
- **Operational Excellence** — Maintaining a spanning relationship inventory prevents surprise save-time failures. Monitoring rollup recalculation duration after metadata deploys ensures data accuracy SLAs are met.

## Architectural Tradeoffs

### Native Rollup vs. Apex-Managed Rollup

Native rollups are zero-code, automatically handle insert/update/delete/undelete, and are always in sync (within the save transaction). However, they perform full recalculations when filters are involved, cannot be indexed, and time out on LDV objects. Apex-managed rollups offer incremental updates and full control over locking and filtering, but require trigger code, test coverage, and careful handling of all DML events including undelete.

### Cross-Object Formula vs. Stored Denormalized Field

Cross-object formulas are declarative, always current, and require no sync logic. But they consume spanning relationships (hard-limited), are never indexable, and add read-time overhead. Stored denormalized fields are indexable and faster to query, but require a trigger or flow to keep them in sync, introducing a maintenance and reliability cost.

### Synchronous Rollup Read vs. Deferred Async Read

Reading a rollup in the same transaction is simpler and avoids async complexity. But the value is stale until step 13 completes. Deferring to a Queueable adds latency and consumes an async job slot, but guarantees the correct value. The tradeoff is correctness vs. simplicity and resource consumption.

## Anti-Patterns

1. **Treating spanning relationships as unlimited** — Adding cross-object formulas without tracking the cumulative spanning count leads to sudden save-time failures when the 15-reference limit is hit. The failure blocks all metadata changes on the object until references are reduced.
2. **Relying on native rollups for LDV objects** — Keeping native rollup summary fields on objects with 300k+ children per parent leads to recalculation timeouts that corrupt displayed values and block user transactions.
3. **Assuming rollup values are current in triggers** — Writing trigger logic that branches on a parent's rollup field value without accounting for the step-13 timing gap produces intermittent data quality bugs that are difficult to reproduce in test environments with small data sets.

## Official Sources Used

- Salesforce Help — Roll-Up Summary Field — https://help.salesforce.com/s/articleView?id=sf.fields_about_roll_up_summary_fields.htm
- Salesforce Help — Maximum 15 Object References — https://help.salesforce.com/s/articleView?id=000384498
- Salesforce Engineering Blog — Record Locking — https://engineering.salesforce.com/reduce-record-locking/
- Apex Developer Guide — Order of Execution — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
