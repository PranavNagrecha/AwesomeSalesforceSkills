# Well-Architected Notes — Case Trigger Patterns

## Relevant Pillars

- **Reliability** — The most critical pillar for this skill. Assignment rule invocation, entitlement association, and milestone completion are all silent failure surfaces. Using `Database.DmlOptions` correctly and completing milestones explicitly are required for reliable SLA and routing behavior. Triggers must be bulkified to avoid governor limit failures under batch load.
- **Operational Excellence** — Merge handling and assignment rule invocation require explicit, documented behavior. Teams that do not know DML bypasses assignment rules will discover the problem only in production. The trigger patterns in this skill make the behavior explicit and testable.
- **Security** — Handler classes must use `with sharing` to respect record-level access. Field-level security checks are required when stamping `Case.EntitlementId` or updating `CaseMilestone` records from a trigger running in a system context, depending on org configuration and trigger framework design.
- **Performance** — The entitlement association handler must not query SOQL inside a loop. A single `EntitlementContact` query using `IN :contactIds` handles the full trigger batch. The milestone completion handler similarly uses a single `CaseMilestone` query per batch.
- **Scalability** — All patterns must be implemented as bulkified handler methods. Triggers that call `Database.insert()` with `DmlOptions` on every record individually rather than in a collected list will hit DML limits quickly in batch or integration contexts.

## Architectural Tradeoffs

**Assignment rule invocation location:** The `Database.DmlOptions` call can be placed either in the handler that performs the DML (preferred for service-layer architectures) or in a wrapper utility. Placing it in the trigger body itself creates tight coupling to trigger context and makes the service layer harder to test in isolation. Prefer to encapsulate the DmlOptions construction in the service method that owns the insert.

**Entitlement association timing:** Doing this in `Before Insert` avoids an extra DML round-trip but requires writing directly to `Trigger.new` records. Some trigger frameworks discourage mutating `Trigger.new` outside the trigger body. If the framework prohibits this, the fallback is `After Insert` with an explicit update DML, at the cost of one additional DML statement per batch.

**Milestone completion placement:** An After Update trigger keeps this logic co-located with the case close detection. An alternative is a Process Builder or Flow on Case close. The trigger approach is preferable when the org uses a trigger framework, because it keeps all Case automation in one place and avoids interleaving platform automation with declarative automation in ways that are hard to trace.

## Anti-Patterns

1. **Using the `insert` keyword when assignment rules must fire** — The developer assumes platform DML and UI DML behave identically with respect to assignment rules. They do not. Always use `Database.insert()` with `DmlOptions` when assignment rule evaluation is required. This anti-pattern produces silent misfires in production that are extremely difficult to diagnose.

2. **Querying milestones in the same transaction as case close and expecting `IsCompleted = true`** — The platform evaluates entitlement process milestones asynchronously. A Flow or trigger that closes a case and then immediately checks milestone completion in the same execution context will read stale data. The explicit `CaseMilestone.CompletionDate` update is the only reliable way to mark milestones complete synchronously.

3. **Running merge cleanup logic unconditionally in a delete trigger** — Without checking `MasterRecordId`, all delete trigger logic runs for both merge deletes and true deletes. This can cause data loss (archival of records that should have migrated to the master) or double-processing (firing integration callouts for records that still exist under a different Id).

## Official Sources Used

- Apex Developer Guide — Triggers and Merge Statements — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_merge_statements.htm
- Apex Developer Guide — Database.DmlOptions Class — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_methods_system_database_dmloptions.htm
- REST API Developer Guide — Assignment Rule Header — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/headers_assignmentrule.htm
- Salesforce Help — Run Case Assignment Rule from Apex — https://help.salesforce.com/s/articleView?id=000386162&type=1
- Entitlement Implementation Guide — https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/entitlements_implementation_guide.pdf
- Salesforce Well-Architected — Reliability — https://architect.salesforce.com/well-architected/reliable/overview
- Salesforce Well-Architected — Operational Excellence — https://architect.salesforce.com/well-architected/operational-excellence/overview
