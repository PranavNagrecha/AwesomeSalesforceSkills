# FSL Apex Extensions — Work Template

Use this template when implementing Apex that calls the FSL scheduling or optimization APIs.

## Scope

**Skill:** `fsl-apex-extensions`

**Request summary:** (describe what the user asked for — e.g., "book appointment from LWC action", "bulk scheduling batch job", "trigger OAAS after technician cancellation")

## Context Gathered

Answer these before writing any code:

- **FSL package installed?** Yes / No
- **ServiceAppointment has ServiceTerritoryId assigned?** Yes / No / Assigned by: (flow/trigger/user)
- **Scheduling Policy ID available?** Yes (ID: ____________) / No — need to query
- **Operating Hours ID available?** Yes (ID: ____________) / Not needed (using territory hours)
- **Is DML performed before the FSL API call in the same transaction?** Yes / No
- **Scenario type:** Single record (interactive) / Bulk (batch) / OAAS optimization
- **Enhanced Scheduling and Optimization add-on licensed?** Yes / No / Unknown (required for OAAS)

## Transaction Boundary Decision

Based on context above:

- [ ] No prior DML — FSL call is safe in the current transaction (document why)
- [ ] Prior DML present — must split transaction:
  - [ ] Using Queueable (single record, interactive)
  - [ ] Using Batch with batchSize=1 (bulk)
  - [ ] Using @future(callout=true) (simple async, non-batch context only)

## Implementation Checklist

### Pre-code
- [ ] Confirmed ServiceAppointment.ServiceTerritoryId is assigned before schedule() call
- [ ] Confirmed Scheduling Policy record exists and ID is available
- [ ] Transaction boundary strategy selected (see above)

### Queueable implementation (if applicable)
- [ ] Class implements `Queueable, Database.AllowsCallouts`
- [ ] Constructor accepts SA ID, policy ID, and any other required IDs
- [ ] `execute()` method calls GetSlots() or schedule() with no prior DML
- [ ] Empty slot list is handled: `if (slots == null || slots.isEmpty()) { ... }`
- [ ] Exception is caught and logged; does not propagate silently

### Batch implementation (if applicable)
- [ ] Class implements `Database.Batchable<SObject>, Database.AllowsCallouts`
- [ ] `Database.executeBatch(new MyBatch(), 1)` — batchSize explicitly set to 1
- [ ] `execute()` contains a try/catch; failures logged, not re-thrown
- [ ] `start()` query filters for appointments with ServiceTerritoryId != null

### OAAS implementation (if applicable)
- [ ] Enhanced Scheduling and Optimization add-on confirmed present
- [ ] FSL.OAAS call is gated behind a feature flag or custom permission check
- [ ] Returned job ID is stored for audit/monitoring
- [ ] OAAS method chosen matches scenario (inDay / optimizeBySchedulingPolicy / reshuffle)

### Post-code
- [ ] Unit tests mock FSL callouts (HttpCalloutMock or Test.setMock)
- [ ] Tests verify async dispatch path (asserting Queueable/Batch is enqueued) rather than testing FSL internals
- [ ] `python3 scripts/check_fsl_apex.py --apex-dir <path>` passes with no warnings

## Code Skeleton

### Queueable (single record)

```apex
public class FSLBookingQueueable implements Queueable, Database.AllowsCallouts {
    private final Id saId;
    private final Id policyId;
    private final Id ohId;

    public FSLBookingQueueable(Id saId, Id policyId, Id ohId) {
        this.saId     = saId;
        this.policyId = policyId;
        this.ohId     = ohId;
    }

    public void execute(QueueableContext ctx) {
        List<FSL.AppointmentBookingSlot> slots =
            FSL.AppointmentBookingService.GetSlots(saId, policyId, ohId);

        if (slots == null || slots.isEmpty()) {
            System.debug(LoggingLevel.WARN, 'No available slots for SA: ' + saId);
            return;
        }

        FSL.AppointmentBookingSlot best = slots[0];
        FSL.ScheduleService.schedule(
            saId,
            policyId,
            best.Resource.Id,
            best.Interval_Start__c,
            best.Interval_End__c
        );
    }
}
```

### Batch (bulk, batchSize=1)

```apex
public class FSLBulkScheduleBatch
    implements Database.Batchable<SObject>, Database.AllowsCallouts {

    private final Id policyId;

    public FSLBulkScheduleBatch(Id schedulingPolicyId) {
        this.policyId = schedulingPolicyId;
    }

    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator([
            SELECT Id FROM ServiceAppointment
            WHERE  Status = 'None' AND ServiceTerritoryId != null
        ]);
    }

    public void execute(Database.BatchableContext bc, List<SObject> scope) {
        ServiceAppointment sa = (ServiceAppointment) scope[0];
        try {
            List<FSL.AppointmentBookingSlot> slots =
                FSL.AppointmentBookingService.GetSlots(sa.Id, policyId, null);
            if (slots != null && !slots.isEmpty()) {
                FSL.AppointmentBookingSlot best = slots[0];
                FSL.ScheduleService.schedule(
                    sa.Id, policyId,
                    best.Resource.Id, best.Interval_Start__c, best.Interval_End__c
                );
            }
        } catch (Exception e) {
            System.debug(LoggingLevel.ERROR, 'SA ' + sa.Id + ': ' + e.getMessage());
        }
    }

    public void finish(Database.BatchableContext bc) {}
}

// Invocation:
// Database.executeBatch(new FSLBulkScheduleBatch(policyId), 1);
```

## Notes

(Record any deviations from the standard patterns and why.)
