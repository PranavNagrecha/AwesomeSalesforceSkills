# Examples — Entitlement Apex Hooks

## Example 1: Auto-Complete "First Response" Milestone When Case Status Changes

**Context:** A service org requires that the "First Response" SLA milestone is automatically marked complete the moment an agent changes a case status from "New" to anything else, indicating a response has been sent.

**Problem:** Without Apex automation, agents must manually complete the milestone in the Entitlements related list, which is error-prone and often skipped. A developer's first instinct is to write `caseMilestone.IsCompleted = true`, which compiles without error but is silently ignored by the platform, leaving the milestone open indefinitely.

**Solution:**

```apex
// CaseMilestoneTrigger.trigger
trigger CaseMilestoneTrigger on Case (after update) {
    CaseMilestoneService.completeFirstResponseMilestone(Trigger.new, Trigger.oldMap);
}
```

```apex
// CaseMilestoneService.cls
public class CaseMilestoneService {

    private static final String FIRST_RESPONSE_TYPE = 'First Response';

    public static void completeFirstResponseMilestone(
            List<Case> newCases,
            Map<Id, Case> oldMap) {

        // Collect IDs of cases that just left 'New' status
        Set<Id> caseIds = new Set<Id>();
        for (Case c : newCases) {
            Case oldCase = oldMap.get(c.Id);
            if (oldCase.Status == 'New' && c.Status != 'New') {
                caseIds.add(c.Id);
            }
        }
        if (caseIds.isEmpty()) return;

        // Query open milestones of the target type for those cases
        List<CaseMilestone> toComplete = [
            SELECT Id, CompletionDate
            FROM CaseMilestone
            WHERE CaseId IN :caseIds
              AND MilestoneType.Name = :FIRST_RESPONSE_TYPE
              AND CompletionDate = null
        ];
        if (toComplete.isEmpty()) return;

        // Write CompletionDate — NOT IsCompleted
        Datetime completedAt = System.now();
        for (CaseMilestone cm : toComplete) {
            cm.CompletionDate = completedAt;
        }
        update toComplete;
    }
}
```

**Why it works:** `CompletionDate` is the actual writable control field. Once a non-null `CompletionDate` is persisted, the platform formula `IsCompleted` evaluates to `true`. The trigger is `after update` because the milestone DML is a separate transaction from the case update.

---

## Example 2: Scheduled Violation Detection with Idempotency Guard

**Context:** A support operations team needs a daily escalation when a "Resolution" milestone is violated — specifically, a Task assigned to the case owner's manager should be created once per violated milestone.

**Problem:** There is no trigger or platform event that fires when `IsViolated` becomes `true`. A developer cannot intercept this state change reactively. A naive scheduled class without an idempotency guard will create duplicate tasks every time it runs after the violation.

**Solution:**

```apex
// MilestoneViolationScheduler.cls
public class MilestoneViolationScheduler implements Schedulable {

    private static final String RESOLUTION_TYPE = 'Resolution';

    public void execute(SchedulableContext sc) {
        handleViolatedMilestones();
    }

    @TestVisible
    private static void handleViolatedMilestones() {

        // Query violated, incomplete milestones that have not yet been escalated
        // ViolationEscalated__c is a custom checkbox on Case (default false)
        List<CaseMilestone> violated = [
            SELECT Id, CaseId, TargetDate, Case.OwnerId, Case.ViolationEscalated__c
            FROM CaseMilestone
            WHERE MilestoneType.Name = :RESOLUTION_TYPE
              AND IsViolated = true
              AND CompletionDate = null
              AND Case.ViolationEscalated__c = false
            LIMIT 200
        ];
        if (violated.isEmpty()) return;

        Set<Id> caseIds = new Set<Id>();
        List<Task> tasksToInsert = new List<Task>();

        for (CaseMilestone cm : violated) {
            caseIds.add(cm.CaseId);
            // Create a follow-up task assigned to the case owner
            tasksToInsert.add(new Task(
                Subject       = 'SLA Violation: Resolution milestone exceeded',
                WhatId        = cm.CaseId,
                OwnerId       = cm.Case.OwnerId,
                ActivityDate  = Date.today(),
                Priority      = 'High',
                Status        = 'Not Started'
            ));
        }

        insert tasksToInsert;

        // Mark cases as escalated so this batch does not re-process them
        List<Case> casesToUpdate = new List<Case>();
        for (Id caseId : caseIds) {
            casesToUpdate.add(new Case(
                Id = caseId,
                ViolationEscalated__c = true
            ));
        }
        update casesToUpdate;
    }
}
```

Schedule registration (run in Developer Console or deployment script):

```apex
// Schedule to run every 30 minutes
String cron = '0 0,30 * * * ?';
System.schedule('Milestone Violation Escalation', cron, new MilestoneViolationScheduler());
```

**Why it works:** The `Case.ViolationEscalated__c` flag acts as an idempotency guard. The scheduler only processes milestones where the parent case has not yet been flagged, so repeated runs do not create duplicate tasks. The LIMIT 200 ensures the class stays within governor limits for a synchronous scheduled context.

---

## Anti-Pattern: Writing IsCompleted Directly

**What practitioners do:** After reading Salesforce documentation that says a milestone is "complete" when `IsCompleted = true`, developers write:

```apex
// WRONG — IsCompleted is read-only; this DML call silently discards the field value
for (CaseMilestone cm : milestonesToComplete) {
    cm.IsCompleted = true;
}
update milestonesToComplete;
// Result: DML succeeds, no exception, but all milestones remain IsCompleted = false
```

**What goes wrong:** The update DML call succeeds without exception. Querying the same records immediately after shows `IsCompleted = false`. The milestone is still open. Because there is no error signal, this bug often persists through code review and into production.

**Correct approach:**

```apex
// CORRECT — CompletionDate is the writable control field
for (CaseMilestone cm : milestonesToComplete) {
    cm.CompletionDate = System.now();
}
update milestonesToComplete;
// Result: IsCompleted is now true (formula recalculation)
```
