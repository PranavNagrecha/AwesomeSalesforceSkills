# FSL Scheduling API — Work Template

Use this template when implementing Apex code that calls FSL scheduling API classes.

## Scope

**Skill:** `fsl-scheduling-api`

**Request summary:** (fill in — e.g. "Implement automated slot retrieval and booking for Work Order intake flow")

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **ESO licensed / ESO territories:** (yes/no, which territories)
- **Transaction context (where does the call originate):** (e.g. @AuraEnabled, Queueable, Trigger, Batch)
- **Volume:** (single SA or bulk)
- **Operation needed:** (GetSlots only / GetSlots + GradeSlots + schedule() / direct schedule() / OAAS)
- **Scheduling policy Id(s):** (record Ids or lookup method)

## Transaction Boundary Plan

If implementing GetSlots + schedule():

| Step | Transaction | Action |
|------|-------------|--------|
| 1 | Tx 1 | Call GetSlots (and optionally GradeSlots) — callouts only, no DML |
| 2 | Tx 1 | Return slot data to calling component or store in intermediate object |
| 3 | Tx 2 | DML: update ArrivalWindowStart / ArrivalWindowEnd on ServiceAppointment |
| 4 | Tx 2 | Call FSL.ScheduleService.schedule() |
| 5 | Tx 2 | Check result != null; handle no-resource case |

## Implementation Checklist

- [ ] No DML precedes FSL scheduling callouts in the same transaction
- [ ] Bulk scheduling uses Batch Apex with `Database.executeBatch(job, 1)`
- [ ] schedule() return value checked for null before accessing result fields
- [ ] OAAS calls originate from Queueable or Scheduled Apex, not synchronous controllers
- [ ] ESO licensing and per-territory enrollment confirmed
- [ ] Error/null cases log to custom error object or platform event
- [ ] Integration tested against real scheduling policy and territory in sandbox

## Pattern Applied

(Choose one and note why)

- [ ] **Two-transaction booking flow** — user-facing slot selection with hard assignment
- [ ] **Batch Apex bulk scheduling** — automated bulk assignment post-migration or nightly run
- [ ] **Queueable auto-schedule** — single SA auto-assignment triggered from trigger or Flow
- [ ] **OAAS Global/In-Day/Resource** — background territory optimization

## Code Snippets

```apex
// Transaction 1 — Slot retrieval
@AuraEnabled
public static List<Map<String, Object>> getSlots(Id saId, Id policyId) {
    List<FSL.Scheduling.TimeSlot> slots =
        FSL.AppointmentBookingService.GetSlots(saId, null, policyId);
    List<FSL.Scheduling.TimeSlot> graded =
        FSL.GradeSlotsService.GradeSlots(saId, slots, policyId);
    // serialize and return to LWC
    List<Map<String, Object>> result = new List<Map<String, Object>>();
    for (FSL.Scheduling.TimeSlot ts : graded) {
        result.add(new Map<String, Object>{
            'startTime' => ts.startTime,
            'endTime'   => ts.endTime,
            'grade'     => ts.grade
        });
    }
    return result;
}

// Transaction 2 — Confirm booking
@AuraEnabled
public static void confirmBooking(Id saId, Datetime windowStart, Datetime windowEnd, Id policyId) {
    ServiceAppointment sa = [SELECT Id FROM ServiceAppointment WHERE Id = :saId FOR UPDATE];
    sa.ArrivalWindowStart = windowStart;
    sa.ArrivalWindowEnd   = windowEnd;
    update sa;
    FSL.ScheduleResult res = FSL.ScheduleService.schedule(saId, policyId);
    if (res == null) {
        throw new AuraHandledException('No resource available for selected window.');
    }
}
```

## Notes

(Record any deviations from the standard pattern and why.)
