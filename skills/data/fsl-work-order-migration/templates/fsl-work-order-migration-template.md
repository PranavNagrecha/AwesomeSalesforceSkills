# FSL Work Order Migration — Work Template

Use this template when planning or executing a Field Service work order data migration.

## Scope

**Skill:** `fsl-work-order-migration`

**Request summary:** (fill in — e.g. "Migrate 5 years of work order history from ServiceMax to Salesforce FSL")

## Context Gathered

- **Objects in scope:** WorkOrder / WorkOrderLineItem / ServiceAppointment / AssignedResource / ProductConsumed
- **Historical (completed) records in scope:** yes / no
- **Status values in source data:** (list all distinct values)
- **Products and PricebookEntry pre-loaded:** yes / no
- **External ID fields added:** yes / no
- **FSL optimization disabled:** yes / no

## Pre-Migration Checklist

- [ ] Extract distinct ServiceAppointment Status values from source
- [ ] Verify each status value is active in target org picklist
- [ ] Add `Legacy_Id__c` External ID field to: WorkOrder, WorkOrderLineItem, ServiceAppointment, AssignedResource, ProductConsumed
- [ ] Load Product2 and PricebookEntry records (Standard Pricebook, IsActive = true)
- [ ] Disable FSL optimization: Setup > Field Service Settings > Scheduling

## Migration Sequence

| Step | Object | Operation | Notes |
|------|--------|-----------|-------|
| 1 | Account / Contact / Asset | Upsert on Legacy_Id__c | Only if not already present |
| 2 | WorkOrder | Upsert on Legacy_Id__c | Set AccountId via Account Legacy_Id__c |
| 3 | WorkOrderLineItem | Upsert on Legacy_Id__c | Set WorkOrderId via WO Legacy_Id__c |
| 4 | ServiceAppointment | Upsert on Legacy_Id__c | Set ParentRecordId, Status must be active |
| 5 | AssignedResource | Upsert on Legacy_Id__c | Set ServiceAppointmentId, ServiceResourceId |
| 6 | ProductConsumed | Upsert on Legacy_Id__c | Set WorkOrderLineItemId, PricebookEntryId |

## Post-Migration Checklist

- [ ] Re-enable FSL optimization in Field Service Settings
- [ ] Validate record counts per object against source totals
- [ ] SOQL: `SELECT COUNT() FROM ServiceAppointment WHERE Status NOT IN ('Scheduled','Dispatched','Completed','None')`
- [ ] SOQL: `SELECT COUNT() FROM ProductConsumed WHERE PricebookEntryId = null`
- [ ] Spot-check 10 Work Orders end-to-end for correct child record associations
- [ ] Confirm AssignedResource records link to correct ServiceResource records

## Notes

(Record deviations, special handling, transformation rules applied.)
