# Well-Architected Mapping: Apex Trigger Framework

---

## Pillars Addressed

### Scalability
Single-trigger + handler pattern ensures all records in a bulk operation are processed in one handler invocation. SOQL and DML are batched outside loops. The pattern scales to 200 records without hitting governor limits by design.

- WAF check: One trigger per object?
- WAF check: Bulkified — all SOQL before loops, all DML on collections?

### Reliability
Recursion guard prevents infinite loops. Activation bypass enables disabling without deployment during incidents or data migrations. Clear before/after-save boundaries prevent forbidden DML errors.

- WAF check: Recursion guard present and tested?
- WAF check: Activation bypass exists — can this trigger be disabled in 30 seconds without a deploy?

### Operational Excellence
Handler pattern makes logic testable in isolation. Activation bypass via Custom Metadata means configuration is deployable across environments. Static recursion guard reset method prevents test order dependencies.

- WAF check: Handler class is independently testable?
- WAF check: Activation config is in Custom Metadata (deployable) not Custom Setting (manual per env)?

## Official Sources Used

Each bullet names the claim it supports. Claims in this package without a source
below carry an inline `UNVERIFIED (<date>):` marker at the point of use.

- Apex Developer Guide, "Triggers and Order of Execution" (https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm) — supports: before-save record-triggered flows run *ahead* of all before triggers; a workflow field update re-executes before-update and after-update triggers "one more time (and only one more time)"; `Trigger.old` after a workflow field update holds the pre-edit value, not the value from the first pass; a process or flow DML sends the record back through the save procedure; and the order of execution is undefined when more than one trigger is defined on an object for the same event — the grounding for "one trigger per object".
- Apex Developer Guide, "Trigger Context Variables" (https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_context_variables.htm) — supports: `Trigger.new` records "can only be modified in before triggers" and throw in after contexts; `Trigger.newMap` exists only in before-update, after-insert, after-update and after-undelete; `Trigger.old` / `Trigger.oldMap` only in update and delete; `Trigger.old` is always read-only; and `Trigger.size` counts only the current batch, because DML over 200 records is processed in batches with the trigger invoked per batch. Also: a trigger's code block cannot contain the `static` keyword, which is why the recursion guard must live on the handler class.
- Apex Developer Guide, "Static and Instance Methods, Variables, and Initialization Code" and "Using Batch Apex" (https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_static.htm) — supports: a static variable is scoped to the Apex transaction and "reset across transaction boundaries", so it persists across trigger invocations within one transaction; each execution of a batch Apex job "is considered a discrete transaction" (1,000 records without a scope parameter is five transactions of 200), so a static guard has one lifetime per chunk; static variables are not reverted by a rollback; and every test method runs as its own transaction with the static context reinitialised, which is why a reset between test *methods* is dead code.
- Apex Developer Guide, "Bulk DML Exception Handling" / trigger considerations (https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_bulk.htm) — supports: a partial-success DML fires triggers again on subsequent attempts within the *same* transaction, so static class variables are not reset between attempts; and triggers fire on batches from Bulk API, Data Loader, and integrations rather than on single records.
- Apex Developer Guide, "Trigger and Bulk Request Best Practices" (https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_bestpract.htm) — supports: minimise SOQL by preprocessing records into sets used with an `IN` clause; minimise DML by operating on collections; triggers are designed for bulk operation.
- Apex Developer Guide, "Common Bulk Trigger Idioms" (https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_bulk_idioms.htm) — supports: the Set → SOQL `IN` → Map-by-Id correlation idiom; using `Trigger.newMap` / `Trigger.oldMap` to correlate with query results; and the unique-field bulk rollback/retry cycle that "assigns new keys to the new records", making the record id in the duplicate error stale.
- Apex Developer Guide, versioned behaviour changes for API 65.0 (https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_keywords_modifiers.htm) — supports: "In API version 65.0 and later, an abstract or override method requires a protected, public, or global access modifier", and an absent modifier defaults to private, so a bare `override` on a handler hook stops compiling.
- Metadata API Developer Guide, `ApexClass` and `ApexTrigger` (https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_classes.htm) — supports: the `.trigger` suffix with a `TriggerName-meta.xml` companion in the `triggers` folder; `apiVersion` and `status` are required on `ApexTrigger`; `status` accepts `Active`, `Inactive`, `Deleted` for a trigger; and `ApexCodeUnitStatus` "includes an `Inactive` option, but it's only supported for `ApexTrigger`; it isn't supported for `ApexClass`".
- Salesforce Object Reference, `WorkOrder` (https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_workorder.htm) — supports the example package's field use: `EndDate` is "blank unless you set up an Apex trigger or quick action to populate it"; `ParentWorkOrderId` is a self-lookup to `WorkOrder`; and `Status` is a customisable picklist whose standard values include `New`, `In Progress`, `On Hold` and `Completed`.
- Salesforce Well-Architected — reliability and operability framing for trigger architecture: a trigger that cannot be switched off without a deployment is an operability defect, not a style preference.
