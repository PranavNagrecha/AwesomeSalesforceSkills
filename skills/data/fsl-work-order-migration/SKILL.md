---
name: fsl-work-order-migration
description: "Use this skill when migrating Work Order, Work Order Line Item, Service Appointment, AssignedResource, and ProductConsumed data into a Salesforce Field Service org. Trigger keywords: FSL data migration, WorkOrder import, ServiceAppointment migration, AssignedResource load, ProductConsumed migration, work order history data load. NOT for Case data migration, standard Account/Contact migration without FSL objects, or configuring FSL after a migration."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Security
triggers:
  - "How do I load historical work orders and service appointments into FSL"
  - "AssignedResource inserts triggering scheduling automation during migration"
  - "What is the correct insert order for FSL work order migration records"
  - "Migrating ServiceAppointment with Completed status fails during FSL data load"
  - "ProductConsumed migration requires PricebookEntry records to exist first"
tags:
  - fsl
  - field-service
  - data-migration
  - work-order
  - service-appointment
  - fsl-work-order-migration
inputs:
  - "Source system work order records with related line items, appointments, and assignments"
  - "Target FSL org with work types, scheduling policies, and territories configured"
  - "Whether historical completed appointments or only open/scheduled records are in scope"
outputs:
  - "Ordered migration sequence for FSL work order object hierarchy"
  - "Guidance on status picklist value activation requirements"
  - "Configuration changes needed before and after migration load"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# FSL Work Order Migration

This skill activates when a data migration project includes Field Service Lightning (FSL) work order objects: WorkOrder, WorkOrderLineItem, ServiceAppointment, AssignedResource, and ProductConsumed. FSL's object hierarchy, status-based automation, and scheduling engine introduce insert-order constraints and automation-firing risks not present in standard CRM migrations.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether historical completed appointments are in scope or only open/scheduled records. Migrating Completed status requires the `Completed` value to be active in the ServiceAppointment Status picklist before load.
- Determine whether FSL scheduling automation (Global Optimization, territory-based auto-scheduling) should fire during migration or be disabled. AssignedResource inserts can trigger scheduling engine recalculations — this must be disabled during migration.
- Verify PricebookEntry records exist for all products that appear in ProductConsumed records. Missing PricebookEntry prevents ProductConsumed insert.
- Confirm External ID fields are added to all FSL objects used in the migration for upsert-safe re-run capability.

---

## Core Concepts

### Insert Order — FSL Object Hierarchy

FSL's object model has strict parent-child dependencies. Attempting to insert child records before parents fail with lookup validation errors. The correct sequence is:

1. Account / Contact / Asset (if not already present)
2. WorkOrder (lookup to Account, Contact, Asset optional)
3. WorkOrderLineItem (lookup to WorkOrder)
4. ServiceAppointment (lookup to WorkOrder or WorkOrderLineItem)
5. AssignedResource (lookup to ServiceAppointment + ServiceResource)
6. ProductConsumed (lookup to WorkOrderLineItem + PricebookEntry)

Each step must complete with zero errors before proceeding to the next. Use External IDs and upsert operations so failed loads can be re-run without duplicates.

### Status Picklist Constraints

ServiceAppointment has a `Status` picklist whose values are tied to FSL lifecycle transitions. Attempting to insert a ServiceAppointment record with a status value (e.g., `Completed`, `Cannot Complete`) that does not exist as an active picklist value in the target org will fail.

Before migration, verify all source status values are active in the target org's ServiceAppointment Status picklist. For historical closed appointments, this means activating `Completed`, `Cannot Complete`, and any custom values present in the source system.

### Scheduling Automation During Migration

When AssignedResource records are inserted, FSL's territory-based scheduling engine may interpret the insert as a new assignment and trigger optimization jobs, recalculations, or time-slot evaluations. These can:
- Conflict with migrated scheduled times
- Generate duplicate scheduling history
- Slow the migration significantly

**Best practice:** Disable FSL optimization settings in Setup > Field Service Settings before migration. Re-enable after load completes and data is validated.

### ProductConsumed Requirements

`ProductConsumed` records represent parts actually used on a job. They require a `PricebookEntryId` lookup to a valid PricebookEntry for the product. If the PricebookEntry does not exist (e.g., product is not in the org's standard pricebook), the insert fails.

Pre-migration step: load or confirm all Products and their PricebookEntry records in the standard pricebook before loading ProductConsumed.

---

## Common Patterns

### Upsert with External IDs

**When to use:** All FSL migration loads to ensure re-runnable, duplicate-safe loads.

**How it works:** Add a custom External ID field (e.g., `Legacy_Id__c`) to WorkOrder, WorkOrderLineItem, ServiceAppointment, AssignedResource, and ProductConsumed. Use Data Loader or the Bulk API 2.0 upsert operation with the external ID as the match key.

```
// Data Loader upsert mapping
WorkOrder.Legacy_Id__c → Source.WORK_ORDER_ID
WorkOrder.Account__r.Legacy_Account_Id__c → Source.ACCOUNT_ID
```

**Why not insert:** Plain insert with no External ID makes re-runs create duplicates. Upsert allows resuming a failed migration without cleanup.

### Disabling Automation Before Migration

**When to use:** Any time AssignedResource or ServiceAppointment records are loaded in bulk.

**How it works:**
1. Setup > Field Service Settings > Scheduling > uncheck "Enable Optimization"
2. If using FSL Triggers (managed package), disable via `FinServ__TriggerSettings__c` custom setting equivalent for FSL — or use the FSL Trigger Settings custom setting to disable individual triggers
3. Load migration data
4. Re-enable settings
5. Validate assigned resource records and scheduled times

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Historical closed appointments | Activate Completed/CannotComplete status values before load | Status picklist insert validation fails otherwise |
| Large volume AssignedResource load | Disable FSL optimization before load | Prevents automation interference and slowdown |
| ProductConsumed missing PricebookEntry | Pre-load Products + PricebookEntry first | Hard dependency — insert fails without it |
| Need re-runnable migration | Use upsert with External IDs on all objects | Prevents duplicates on re-run |
| Migrating only open/scheduled (not historical) | Disable Completed status loading, focus on None/Scheduled | Simplifies status picklist requirements |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Inventory all source status values** — Extract distinct ServiceAppointment Status values from source data. Confirm each is active in the target org's Status picklist. Activate missing values before migration begins.
2. **Disable FSL scheduling automation** — In Setup > Field Service Settings, disable optimization before loading any AssignedResource or ServiceAppointment records.
3. **Add External ID fields** — Add `Legacy_Id__c` (or equivalent) External ID fields to WorkOrder, WorkOrderLineItem, ServiceAppointment, AssignedResource, and ProductConsumed.
4. **Pre-load Products and PricebookEntry records** — Ensure all products referenced by ProductConsumed have active PricebookEntry records in the standard pricebook.
5. **Load in strict hierarchy order** — Account/Contact/Asset → WorkOrder → WorkOrderLineItem → ServiceAppointment → AssignedResource → ProductConsumed. Validate zero errors at each step before proceeding.
6. **Re-enable FSL automation** — After all records are loaded and spot-validated, re-enable scheduling optimization in Field Service Settings.
7. **Validate data integrity** — Run SOQL to confirm all ServiceAppointments have at least one AssignedResource where expected, all ProductConsumed records have valid PricebookEntryId, and status values match source data.

---

## Review Checklist

- [ ] All source ServiceAppointment status values are active in target org
- [ ] FSL optimization disabled before AssignedResource load
- [ ] External IDs added to all FSL migration objects
- [ ] Products and PricebookEntry records exist for all ProductConsumed references
- [ ] Migration runs in strict hierarchy order with zero errors at each step
- [ ] FSL optimization re-enabled and validated after migration
- [ ] Post-load SOQL validation run to check record counts and key field values

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Status picklist validation is hard — not advisory** — Inserting a ServiceAppointment with a status value not in the org's picklist throws `INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST`. This stops bulk loads and requires picklist activation before the load, not after.
2. **AssignedResource inserts trigger FSL scheduling engine** — Inserting AssignedResource records without disabling optimization can trigger time-slot recalculations that overwrite migrated scheduled times or generate spurious history records.
3. **ProductConsumed requires PricebookEntry, not just Product** — A Product2 record alone is insufficient. The product must have an active PricebookEntry in a pricebook assigned to the Work Order's account. Missing PricebookEntry throws `FIELD_INTEGRITY_EXCEPTION`.
4. **Case migration and Work Order migration are separate** — Work Orders may be related to Cases but the two objects have independent migration paths. Loading WorkOrders that reference non-existent Case records will fail on the lookup field — migrate Cases first if WO-Case relationships are in scope.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| FSL migration sequence table | Ordered list of objects to load with dependency notes |
| Pre-migration configuration checklist | Status values, External IDs, automation disable steps |
| Post-migration validation SOQL | Queries to verify record counts and data integrity |

---

## Related Skills

- data/fsl-territory-data-setup — Service territory, operating hours, and resource data setup required before FSL work order migration
- data/fsl-resource-and-skill-data — ServiceResource and ServiceResourceSkill data that AssignedResource records reference
