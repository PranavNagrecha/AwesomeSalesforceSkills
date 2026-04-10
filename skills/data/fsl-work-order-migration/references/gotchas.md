# Gotchas — FSL Work Order Migration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Status Picklist Validation Is a Hard Insert Failure

**What happens:** Inserting a ServiceAppointment with a Status value not present in the target org's picklist throws `INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST`. The entire batch fails — not just the record with the missing value.

**When it occurs:** Every migration of historical service appointment data, especially from orgs where custom status values were added (e.g., "On Hold", "Parts Ordered") or from systems where "Completed" and "Cannot Complete" were used.

**How to avoid:** Before loading any ServiceAppointment records, extract all distinct Status values from the source data. Verify each exists as an active picklist value in the target org. Activate missing values in Setup > Object Manager > ServiceAppointment > Status field.

---

## Gotcha 2: AssignedResource Inserts Trigger Scheduling Engine

**What happens:** Bulk inserting AssignedResource records fires FSL's territory optimization and scheduling recalculation logic. For large loads (10,000+ records), this generates thousands of background optimization jobs that compete with the migration process, slow the load dramatically, and can overwrite migration-set scheduled times.

**When it occurs:** Any migration that loads AssignedResource records with FSL optimization settings enabled (the default for any configured FSL org).

**How to avoid:** Disable "Enable Optimization" and "Enable In-Day Optimization" in Setup > Field Service Settings > Scheduling before the AssignedResource load. Re-enable after migration validation is complete.

---

## Gotcha 3: ProductConsumed Requires PricebookEntryId — Not Product2Id

**What happens:** `ProductConsumed.UnitPrice` requires a `PricebookEntryId` — not just a `Product2Id`. The PricebookEntry must exist, must be active, and must reference the standard pricebook (unless the Work Order's account uses a custom pricebook). Missing PricebookEntry throws `FIELD_INTEGRITY_EXCEPTION`.

**When it occurs:** Migrations that transform ProductConsumed records without separately loading PricebookEntry records for all products.

**How to avoid:** Pre-load all Product2 records and corresponding PricebookEntry records (linked to the Standard Pricebook, `IsActive = true`) before loading ProductConsumed. Use the PricebookEntry external ID in the ProductConsumed load mapping.

---

## Gotcha 4: WorkOrderLineItem-to-ServiceAppointment Relationship Is Optional But Affects Hierarchy

**What happens:** ServiceAppointment has a lookup to WorkOrder (required) and an optional lookup to WorkOrderLineItem. When migrating data where appointments were associated with specific line items, the WOLI relationship must be preserved to maintain correct FSL data model structure — otherwise reports and FSL UI that roll up by WOLI will be incorrect.

**When it occurs:** Migrations where the source system tracked which line item each appointment was for.

**How to avoid:** Map `ServiceAppointment.ParentRecordId` to the WorkOrderLineItem's Id (not just the WorkOrder) when the relationship exists in source data.

---

## Gotcha 5: Disabling Triggers May Be Required for FSL Managed Package Orgs

**What happens:** In orgs using the FSL managed package (not FSL Core native), the package includes Apex triggers on ServiceAppointment, AssignedResource, and WorkOrder. These triggers fire on bulk inserts and can cause CPU limit errors, SOQL limit errors, or unexpected data manipulation during migration loads.

**When it occurs:** Managed package FSL orgs with large migration batch sizes.

**How to avoid:** Use the FSL package's trigger settings (custom setting `FSLTriggersSetting__c` or similar) to disable individual triggers before migration. Consult the FSL package documentation for the specific setting name in the installed version.
