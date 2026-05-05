# Examples — Approval Process Apex Patterns

## Example 1 — Bulk submission rolling back on the first failure

**Context.** Month-end batch submits 500 expense reports for
approval. One report's owner has been deactivated; the platform
rejects the submission for that record. The whole batch rolls back —
zero of 500 submissions go through.

**Wrong code.**

```apex
Approval.ProcessResult[] results = Approval.process(requests);
// allOrNone defaults to TRUE
```

**Why it's wrong.** Default `allOrNone = true` means any failure
aborts the whole call. One inactive owner blocks 499 valid
submissions.

**Right code.**

```apex
Approval.ProcessResult[] results = Approval.process(requests, false);
for (Integer i = 0; i < results.size(); i++) {
    if (!results[i].isSuccess()) {
        ApplicationLogger.warn(
            'Submission failed: ' + requests[i].getObjectId() +
            ' — ' + JSON.serialize(results[i].getErrors())
        );
    }
}
```

`allOrNone = false`, log per-row failures, successful submissions
proceed.

---

## Example 2 — Hardcoded process definition Id breaks on sandbox refresh

**Context.** Apex submits expense reports referencing the approval
process by record Id:

```apex
req.setProcessDefinitionNameOrId('300xx0000000123');  // wrong
```

**What goes wrong.** Sandbox refresh produces a new approval
process record with a different Id. Apex still references the old
Id; submissions fail with "Process definition not found".

**Right answer.** Reference by API name:

```apex
req.setProcessDefinitionNameOrId('Expense_Approval');
```

API name is stable across orgs. Sandbox refresh, dev → prod migration —
all preserve the API name.

---

## Example 3 — Auto-approval security audit

**Context.** Apex subscriber on a Platform Event auto-approves
expense reports based on signals from a downstream CFO system. A
month later, audit asks "who approved this report?" Audit trail
shows the running user of the Platform Event subscriber's Apex
trigger — typically the Automated Process user.

**The audit concern.** The original approval process step said
"Approver = Director of Finance". The auto-approval used Apex's
running-user context, not the configured approver. The audit
trail's "approved by" reflects the Apex context, not the policy.

**Right approach.** Two options:

- **Document explicitly** that auto-approval is policy-driven, not
  approver-driven. The audit trail is correct (Automated Process
  user); the policy is documented separately. Acceptable for
  most cases.
- **Run the auto-approval Apex as an impersonation of the
  configured approver.** Requires Modify All Data + careful
  context-switching. More secure-feeling but adds complexity. Most
  orgs choose option 1 with explicit documentation.

The wrong answer is treating auto-approval as equivalent to
manual approval without surfacing the audit-trail difference.

---

## Example 4 — Recall when the source record is invalidated

**Context.** Expense report submitted for VP approval (because
amount > $1000). Owner subsequently splits the expense across two
new reports, each $500. The original report's amount drops below
threshold; VP approval is no longer needed.

**Right answer.** Trigger on `Expense__c` after-update detects the
amount change and recalls:

```apex
trigger ExpenseTrigger on Expense__c (after update) {
    for (Expense__c e : Trigger.new) {
        Expense__c old = Trigger.oldMap.get(e.Id);
        if (e.Total_Amount__c < 1000 && old.Total_Amount__c >= 1000) {
            ApprovalRecaller.recallIfPending(e.Id, 'Amount dropped below threshold');
        }
    }
}
```

```apex
public class ApprovalRecaller {
    public static void recallIfPending(Id recordId, String reason) {
        List<ProcessInstanceWorkitem> wis = [
            SELECT Id FROM ProcessInstanceWorkitem
            WHERE ProcessInstance.TargetObjectId = :recordId
              AND ProcessInstance.Status = 'Pending'
            LIMIT 1
        ];
        if (wis.isEmpty()) return;  // no pending approval to recall
        Approval.ProcessWorkitemRequest req = new Approval.ProcessWorkitemRequest();
        req.setWorkitemId(wis[0].Id);
        req.setAction('Removed');
        req.setComments('Auto-recalled: ' + reason);
        try {
            Approval.process(req);
        } catch (Exception ex) {
            // Recall permission may be restricted; log and continue.
            ApplicationLogger.warn('Recall failed', ex);
        }
    }
}
```

Critical: the running user (the user editing the expense) may not
have recall permission. Catch the exception and either escalate
to an admin queue or accept that some recalls require manual
admin intervention.

---

## Example 5 — Stuck approvals on inactive users

**Context.** Quarterly audit reveals 47 expense reports stuck in
approval. Half are assigned to users who left the company.

**Right approach.** Scheduled batch that runs daily:

```apex
public class StuckApprovalAuditor implements Schedulable {
    public void execute(SchedulableContext sc) {
        List<ProcessInstanceWorkitem> stuck = [
            SELECT Id, ActorId, Actor.IsActive, Actor.Username,
                   ProcessInstance.TargetObjectId, CreatedDate
            FROM ProcessInstanceWorkitem
            WHERE ProcessInstance.Status = 'Pending'
              AND CreatedDate < :Date.today().addDays(-3)
        ];

        List<Stuck_Approval__c> records = new List<Stuck_Approval__c>();
        for (ProcessInstanceWorkitem w : stuck) {
            records.add(new Stuck_Approval__c(
                Workitem_Id__c = w.Id,
                Actor_Username__c = w.Actor.Username,
                Actor_Active__c = w.Actor.IsActive,
                Aged_Days__c = Date.today().daysBetween(w.CreatedDate.date())
            ));
        }
        if (!records.isEmpty()) insert records;
    }
}
```

Surface `Stuck_Approval__c` records to admin via report subscription.
Inactive-actor records require reassignment (admin action); aged
records require nudge to active actor.

---

## Anti-Pattern: Querying ProcessInstance instead of ProcessInstanceWorkitem for actions

```apex
ProcessInstance pi = [
    SELECT Id FROM ProcessInstance
    WHERE TargetObjectId = :recordId LIMIT 1
];
Approval.ProcessWorkitemRequest req = new Approval.ProcessWorkitemRequest();
req.setWorkitemId(pi.Id);  // wrong — pi.Id is not a workitem Id
```

**What goes wrong.** `setWorkitemId` requires a
`ProcessInstanceWorkitem.Id`, not a `ProcessInstance.Id`. The call
fails with a confusing error.

**Correct.** Query `ProcessInstanceWorkitem` directly:

```apex
ProcessInstanceWorkitem wi = [
    SELECT Id FROM ProcessInstanceWorkitem
    WHERE ProcessInstance.TargetObjectId = :recordId
      AND ProcessInstance.Status = 'Pending'
    ORDER BY CreatedDate DESC LIMIT 1
];
req.setWorkitemId(wi.Id);
```
