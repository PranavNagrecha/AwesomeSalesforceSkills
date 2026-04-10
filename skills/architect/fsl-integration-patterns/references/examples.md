# Examples — FSL Integration Patterns

## Example 1: ProductConsumed → ERP Inventory Feedback Loop

**Context:** A manufacturing field service org integrates FSL with SAP for inventory management. Product catalog and van stock sync from SAP to Salesforce nightly. When technicians record ProductConsumed in FSL Mobile, the van stock (ProductItem) is decremented in Salesforce automatically. However, SAP's warehouse ledger still shows the parts as available because no feedback loop exists.

**Problem:** SAP replenishment runs are based on its own warehouse ledger. Parts consumed in the field are not reflected in SAP until the end of week when a manual reconciliation is done. By midweek, dispatchers schedule jobs requiring parts that are actually out of stock, and technicians arrive without the needed parts.

**Solution:**
1. Add a Platform Event `Parts_Consumed__e` that fires when a `ProductConsumed` record is inserted or updated with `QuantityConsumed > 0`
2. An Apex subscriber or Flow subscriber sends the consumption event to an MuleSoft ESB queue
3. MuleSoft publishes the consumption to SAP's goods movement API, decrementing the warehouse ledger in near-real-time
4. Both ProductConsumed and ProductRequired have External IDs for idempotent upsert in both directions

**Why it works:** The Platform Event provides a near-real-time event stream from Salesforce to the integration layer without requiring synchronous callouts in the FSL Mobile update path. SAP's ledger stays accurate throughout the day, not just at end-of-week reconciliation.

---

## Example 2: IoT-Triggered Work Order with Async Scheduling

**Context:** An HVAC company has IoT sensors on commercial HVAC units that report anomalies. When a sensor detects an issue, a work order should be created automatically and a technician scheduled.

**Problem:** A developer implements an Apex handler on the IoT Platform Event that creates the WorkOrder and ServiceAppointment records, then immediately calls `FSL.ScheduleService.schedule()` synchronously. The handler throws `CalloutException: You have uncommitted work pending` because the DML (WorkOrder/SA creation) precedes the scheduling callout in the same transaction.

**Solution:**
```apex
// Platform Event handler — creates records only
trigger IoTWorkOrderTrigger on IoT_Alert__e (after insert) {
    List<WorkOrder> newWOs = new List<WorkOrder>();
    List<ServiceAppointment> newSAs = new List<ServiceAppointment>();
    
    for (IoT_Alert__e event : Trigger.new) {
        WorkOrder wo = new WorkOrder(
            Subject = 'IoT Alert: ' + event.Alert_Type__c,
            AccountId = event.Account_Id__c,
            Status = 'New'
        );
        newWOs.add(wo);
    }
    insert newWOs;
    
    // Create SAs and enqueue scheduling — NEVER call schedule() here
    for (WorkOrder wo : newWOs) {
        ServiceAppointment sa = new ServiceAppointment(
            ParentRecordId = wo.Id,
            Status = 'None'
        );
        newSAs.add(sa);
    }
    insert newSAs;
    
    // Enqueue scheduling for the next transaction
    System.enqueueJob(new FslScheduleQueueable(
        new Map<Id, ServiceAppointment>(newSAs).keySet()
    ));
}
```

**Why it works:** The event handler creates records (DML only, no callouts). Scheduling is delegated to a Queueable that runs in a fresh transaction where the scheduling callout is not preceded by uncommitted DML.

---

## Anti-Pattern: High-Frequency GPS Polling from Salesforce

**What practitioners do:** A developer implements a Scheduled Apex job that runs every 5 minutes and makes an outbound REST call to the fleet GPS API to retrieve the latest vehicle locations for 300 vehicles.

**What goes wrong:** 300 vehicles × 288 runs/day (every 5 minutes) = 86,400 outbound API calls per day, just for GPS. This exhausts the Salesforce Daily API Request limit for many orgs before noon, blocking all other integration and Apex code that uses API calls.

**Correct approach:** Have the fleet GPS system push location updates to Salesforce via inbound REST calls or batch file delivery every 10–15 minutes. The fleet system is the source of truth for vehicle location — it should push to Salesforce, not be polled by Salesforce.
