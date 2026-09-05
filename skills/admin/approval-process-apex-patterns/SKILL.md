---
name: approval-process-apex-patterns
description: "Programmatically driving Salesforce Approval Processes from Apex — `Approval.process(ProcessSubmitRequest)` to submit, `ProcessWorkitemRequest` to approve / reject / reassign, recall semantics, querying `ProcessInstance` and `ProcessInstanceWorkitem` to find pending approvals, and the bulk-submit / bulk-action error-row handling. Covers when to use Apex-driven approval (system-initiated submission, batch approvals, custom UIs) vs leaving the platform's standard buttons in place. NOT for the Approval Process metadata definition itself (that's admin / declarative — see admin/approval-processes), NOT for Flow-based approvals (use flow/flow-orchestration-patterns)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "apex submit approval process processsubmitrequest"
  - "processworkitemrequest approve reject reassign apex"
  - "approval process recall apex submission"
  - "query processinstance processinstanceworkitem pending"
  - "bulk approval apex governor limit"
  - "approval process delegated user reassign apex"
  - "submit for approval from apex fails no applicable approval process"
  - "approval history shows wrong submitted by user after batch"
  - "recall approval request from apex insufficient privileges"
  - "find approvals stuck with inactive approver soql"
  - "bulk submit records for approval hits dml limit"
  - "cannot edit approval process step after activation"
tags:
  - approval-process
  - apex
  - process-submit-request
  - process-workitem-request
  - process-instance
  - bulk-approval
inputs:
  - "Trigger: user-initiated submission (button on record) or system-initiated (batch / scheduled / event-driven)"
  - "Whether the approval needs to be approved / rejected / reassigned programmatically (vs only submitted)"
  - "Bulk requirement: single record per call, or a List<ProcessRequest> in one call"
  - "Error-row policy: fail-fast or partial-success"
outputs:
  - "Apex code using Approval.process() with the right Request type"
  - "Bulk-action error handling (allOrNone vs partial)"
  - "Query patterns to find pending approval items for a record / user"
  - "Recall pattern when the source record is invalidated mid-approval"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Approval Process Apex Patterns

The platform provides standard approval-process buttons (Submit for
Approval, Approve, Reject, Reassign) on record pages. They work for
human-driven, single-record approvals. They don't cover:

- Programmatic submission (a scheduled batch creates 1,000 records
  and submits them all for approval).
- Programmatic action (a system event approves / rejects on behalf
  of a user — careful with this one).
- Custom UI (a custom Lightning component that bundles submit +
  status display + approve buttons).
- Querying pending items (which records are awaiting approval, by
  whom, for how long).

This skill covers the Apex API for those cases.

What this skill is NOT. Defining the Approval Process itself
(entry criteria, approval steps, approver assignment) is
declarative admin work — see `admin/approval-processes`. The
modern Flow-based equivalent (Flow Orchestration with interactive
steps assigned to approvers) is a different runtime entirely — see
`flow/flow-orchestration-patterns`.

---

## Before Starting

- **Confirm the Approval Process is defined and active.** Apex
  references the process by developer name. Check it before you
  write anything else:

  ```sql
  SELECT Id, DeveloperName, Name, State, TableEnumOrId, LockType
  FROM ProcessDefinition
  WHERE DeveloperName = 'Expense_Approval'
  ```

  `State` must be `Active` (values: `Active`, `Inactive`,
  `Obsolete` — Object Reference, `ProcessDefinition`,
  object_reference.txt L225341-225426).
- **Confirm the submitter is an allowed submitter.** "The user must
  be one of the allowed submitters in the process definition setup"
  (Apex Reference, `setSubmitterId`, apexrefguide.txt L4021-4024).
  Setting `submitterId` to a record owner who isn't in
  `allowedSubmitters` fails that row.
- **Decide the bulk shape.** `Approval.process(...)` is overloaded
  for a single `ProcessRequest` or a `List<ProcessRequest>`, each
  with an optional `allOrNone` (apexrefguide.txt L200066-200172).
  Each call counts as one DML statement against the 150-statement
  limit, and the records it processes count against the 10,000
  records-processed limit (apexdev.txt L19548-19556, L19624).
- **Decide the error-row policy.** `allOrNone = true` (default):
  any failure rolls back the whole batch. `allOrNone = false`:
  "the remainder of the approval processes can still succeed"
  (apexrefguide.txt L200119-200123).

---

## Questions to Ask Before Configuring

Ask these before the first `new Approval.ProcessSubmitRequest()`. Every one of them maps to a row that fails at runtime rather than at compile time.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Who is in `allowedSubmitters` on this process, and is the record owner one of them?" | `setSubmitterId` rejects any user who isn't an allowed submitter, so a batch submitting on behalf of owners fails per row | The list of owner profiles/roles to add to `allowedSubmitters`, or a decision to submit as a single service submitter |
| "Is `allowRecall` true, and who is allowed to recall?" | `setAction('Removed')` is admin-only; `allowRecall=false` narrows recall to administrators entirely | Whether Pattern D can run in the editing user's context at all, or needs an admin-context escalation |
| "Does any step use approver type `adhoc` or `queue`?" | `adhoc` needs an approver supplied at submission; a queue-assigned workitem has an `ActorId` pointing at a Group, not a User | Which steps need `setNextApproverIds`, and whether the stuck-approval query can dereference `Actor.IsActive` at all |
| "Is this process the only active one on the object, and what is its process order?" | With `processDefinitionNameOrId` null the platform walks every applicable process in org process order — and process order is not carried in the metadata | A decision to always name the process explicitly, plus a post-deploy step to reset process order |
| "Is `whenMultipleApprovers` on any step `Unanimous`?" | On a unanimous step, one rejection flips every other approver's `StepStatus` to `NoResponse`, not `Rejected` | The correct filter for the approval-audit report, so rejections aren't undercounted |
| "How many rows will one transaction submit, and is it sync or async?" | `Approval.process` is DML: 150 statements and 10,000 records processed per transaction | The chunk size and whether this belongs in Batch Apex or Queueable rather than a trigger |
| "What happens to a row that fails — retry, park, or alert?" | `allOrNone=false` returns per-row `ProcessResult`s that nothing reads unless you write the handler | The error-row destination: a log object, a retry queue, or an admin notification |

What a proper implementation adds over just calling `Approval.process(req)`: submissions land in the right process under the right submitter, failed rows are visible and re-drivable instead of silently rolled back, and the approval audit trail says what an auditor expects it to say.

---

## Core Concepts

### Request types

| Request | Purpose |
|---|---|
| `Approval.ProcessSubmitRequest` | Submit a record into an approval process |
| `Approval.ProcessWorkitemRequest` | Take action on a pending work item — approve / reject / reassign / remove |

Both are passed to `Approval.process(...)`. The call returns a list
of `Approval.ProcessResult` (one per input Request) with success /
errors.

### `ProcessSubmitRequest` essentials

```apex
Approval.ProcessSubmitRequest req = new Approval.ProcessSubmitRequest();
req.setObjectId(record.Id);
req.setProcessDefinitionNameOrId('Expense_Approval_Process');  // approval process API name
req.setSubmitterId(UserInfo.getUserId());                       // who's "submitting"
req.setComments('Submitting via batch on month-end close');
req.setSkipEntryCriteria(false);                                 // run the entry criteria
Approval.ProcessResult result = Approval.process(req);
```

Key options:

| Method | Documented contract (Apex Reference Guide) |
|---|---|
| `setProcessDefinitionNameOrId(nameOrId)` | "The process definition developer name or process definition ID." If null, "every entry criteria of the process definition in the process order is evaluated and the one that satisfies is picked" (apexrefguide.txt L3974-3989). Use the developer name — record IDs are not portable. |
| `setSubmitterId(userID)` | "The user must be one of the allowed submitters in the process definition setup. If you don't set a submitter ID, the process uses the current user as the submitter" (apexrefguide.txt L4021-4024). |
| `setSkipEntryCriteria(skipEntryCriteria)` | Skips entry-criteria evaluation for the named process. "If the process definition name or ID is not specified, this parameter is ignored" (apexrefguide.txt L4005-4014). |
| `setComments(comments)` | Inherited from `ProcessRequest`. Lands in `ProcessInstanceStep.Comments`, limit 4,000 bytes (object_reference.txt L226666-226675). |
| `setNextApproverIds(nextApproverIds)` | Inherited from `ProcessRequest`. Parameter "must be a single-entry list"; it "sets the `ActorId` field of the associated ProcessInstanceWorkItem" (apexrefguide.txt L3631-3634, L3684-3695). |

`setSkipEntryCriteria(true)` submits a record the admin's criteria
were written to exclude. Record why in the calling class, not in a
commit message.

### `ProcessWorkitemRequest` essentials

```apex
// Find the pending workitem.
ProcessInstanceWorkitem workitem = [
    SELECT Id FROM ProcessInstanceWorkitem
    WHERE ProcessInstance.TargetObjectId = :recordId
      AND ProcessInstance.Status = 'Pending'
    ORDER BY CreatedDate DESC LIMIT 1
];

Approval.ProcessWorkitemRequest req = new Approval.ProcessWorkitemRequest();
req.setWorkitemId(workitem.Id);
req.setAction('Approve');     // 'Approve', 'Reject', 'Removed' (recall), or null + setNextApproverIds for reassign
req.setComments('Approved by system per policy 4.2');
Approval.ProcessResult result = Approval.process(req);
```

Action values — "Valid values are: Approve, Reject, or Removed.
Only system administrators can specify Removed"
(apexrefguide.txt L4123-4127):

| Value | Effect | Constraint |
|---|---|---|
| `'Approve'` | Approves the workitem | — |
| `'Reject'` | Rejects the workitem | On a `Unanimous` step, other approvers' steps flip to `NoResponse` |
| `'Removed'` | Recalls the submission | **System administrators only**, per the Apex Reference. `ApprovalProcess.allowRecall=false` narrows recall to administrators even in the UI (api_meta.txt L23095-23098) |
| null + `setNextApproverIds` | Reassign | The list must hold exactly one Id (apexrefguide.txt L3690-3695) |

You rarely need a query to find the workitem you just created.
`ProcessResult.getNewWorkitemIds()` returns "the IDs of the new
items submitted to the approval process" (apexrefguide.txt
L3795-3801), so a submit-then-approve sequence in the same
transaction reads straight from the submit result — this is the
shape the Apex Developer Guide's own sample uses (apexdev.txt
L20651-20715).

### Querying pending approvals

```apex
List<ProcessInstance> pending = [
    SELECT Id, TargetObjectId, Status, SubmittedById, ElapsedTimeInDays,
           (SELECT Id, ActorId FROM Workitems)
    FROM ProcessInstance
    WHERE Status = 'Pending'
      AND ProcessDefinition.DeveloperName = 'Expense_Approval'
];
```

`Workitems` is the child relationship name for
`ProcessInstanceWorkitem`, and `Steps` for `ProcessInstanceStep`
(object_reference.txt L226220-226240). Age on `ElapsedTimeInDays`,
not `CreatedDate` — the field tables for these objects document the
elapsed-time fields and do not list `CreatedDate`.

`ProcessInstance` is the in-flight approval. `ProcessInstanceStep`
is the audit trail of completed steps. `ProcessInstanceWorkitem`
is the open assignment to a specific approver.

| Object | Supported calls | Notes from the Object Reference |
|---|---|---|
| `ProcessDefinition` | `query`, `retrieve`, `search` | Read-only. `DeveloperName`, `State`, `LockType` (object_reference.txt L225355-225426) |
| `ProcessInstance` | `describeSObjects`, `query`, `retrieve` | `Status` picklist: Approved, Fault, Held, NoResponse, Pending, Reassigned, Rejected, Removed, Started (L226112-226145). `TargetObjectId` is **not** nillable (L226147-226160) |
| `ProcessInstanceStep` | `describeSObjects`, `query`, `retrieve` | Completed steps. `StepStatus` uses the same nine values (L226748-226766) |
| `ProcessInstanceWorkitem` | `delete`, `describeSObjects`, `query`, `retrieve`, **`update`** | Open assignments. `ActorId` is **Updateable**, so reassignment is also a plain DML update (L226816-226835) |
| `ProcessInstanceHistory` | read-only view | "Combines fields from ProcessInstanceStep and ProcessInstanceWorkitem" (L226802-226810) |

`ActorId` on both `ProcessInstanceStep` and `ProcessInstanceWorkitem`
is a **polymorphic** relationship field that "Refers To Group, User"
(object_reference.txt L226648-226670, L226820-226835). A bare
`Actor.IsActive` in the SELECT does not compile; use `TYPEOF`, and
handle the queue case where there is no user at all:

```sql
SELECT Id, ActorId, ElapsedTimeInDays, ProcessInstance.TargetObjectId,
       TYPEOF Actor
           WHEN User THEN Username, IsActive
           WHEN Group THEN DeveloperName
       END
FROM ProcessInstanceWorkitem
WHERE ProcessInstance.Status = 'Pending'
  AND ElapsedTimeInDays > 7
```

`ElapsedTimeInDays` / `InHours` / `InMinutes` are filterable and
sortable on both the workitem and the step
(object_reference.txt L226836-226878), which is what the
stuck-approval audit should age on.

### Locking and unlocking

`Approval.lock` / `Approval.unlock` / `Approval.isLocked` set and
read the approval lock independently of the process itself. Two
constraints worth internalising: "Salesforce admins can edit locked
records. Depending on your approval process configuration settings,
an assigned approver can also edit locked records", and "Record
locks and unlocks are treated as DML. They're blocked before a
callout, they count toward your DML limits, and if a failure occurs,
they're rolled back along with the rest of your transaction"
(apexrefguide.txt L199726-199736). Both take the same optional
`allOrNothing` flag and return `LockResult` / `UnlockResult` arrays
positionally matched to the input.

`Approval.unlock` drops the lock. It does **not** remove the pending
approval — the `ProcessInstanceWorkitem` survives and the approver
can still act on it.

### Bulk submission

The overload set is `process(request)`, `process(request, allOrNone)`,
`process(requests)`, `process(requests, allOrNone)`
(apexrefguide.txt L200066-200172). The guides document no per-call
cap on list size; what they do document is that each call is one DML
statement (150 per transaction) and that the records it processes
count against the 10,000 records-processed-per-transaction limit
(apexdev.txt L19548-19556, L19624). UNVERIFIED (2026-09-05): the
widely-repeated "200 requests per `Approval.process` call" figure
does not appear in the Apex Reference Guide, the Apex Developer
Guide, or the App Limits cheat sheet. Chunking at 200 is still a
sound convention — it keeps heap and per-call failure blast radius
predictable — but treat it as a design choice, not a documented
governor.

Chunk the list anyway, and count DML statements while you do:

```apex
List<Approval.ProcessSubmitRequest> requests = ...;
for (Integer i = 0; i < requests.size(); i += 200) {
    Integer end = Math.min(i + 200, requests.size());
    List<Approval.ProcessSubmitRequest> chunk =
        new List<Approval.ProcessSubmitRequest>();
    for (Integer j = i; j < end; j++) chunk.add(requests[j]);
    Approval.ProcessResult[] results = Approval.process(chunk, false);  // allOrNone = false
    for (Integer j = 0; j < results.size(); j++) {
        if (!results[j].isSuccess()) {
            // Log + decide per row
        }
    }
}
```

`allOrNone = false` is essential when you have known-bad rows mixed
in (e.g. records that don't match entry criteria — those will
fail individually rather than killing the whole batch).

---

## Common Patterns

### Pattern A — System-initiated batch submission

**When to use.** Month-end close: identify all expense reports past
threshold, submit them all into approval automatically.

```apex
public class MonthEndExpenseSubmitter {
    public static void submitOverThreshold() {
        List<Expense__c> toSubmit = [
            SELECT Id FROM Expense__c
            WHERE Status__c = 'Draft'
              AND Total_Amount__c >= 1000
              AND Submitted_Date__c = NULL
        ];

        List<Approval.ProcessSubmitRequest> requests = new List<Approval.ProcessSubmitRequest>();
        for (Expense__c e : toSubmit) {
            Approval.ProcessSubmitRequest req = new Approval.ProcessSubmitRequest();
            req.setObjectId(e.Id);
            req.setProcessDefinitionNameOrId('Expense_Approval');
            req.setSubmitterId(e.OwnerId);  // from the owner, not the running batch user
            req.setComments('Auto-submitted by month-end batch');
            requests.add(req);
        }

        // Bulk submit, allow partial success.
        for (Integer i = 0; i < requests.size(); i += 200) {
            Integer end = Math.min(i + 200, requests.size());
            List<Approval.ProcessSubmitRequest> chunk = new List<Approval.ProcessSubmitRequest>();
            for (Integer j = i; j < end; j++) chunk.add(requests[j]);
            Approval.ProcessResult[] results = Approval.process(chunk, false);
            for (Integer j = 0; j < results.size(); j++) {
                if (!results[j].isSuccess()) {
                    ApplicationLogger.warn(
                        'Submission failed: ' + requests[j].getObjectId() +
                        ' — ' + results[j].getErrors()
                    );
                }
            }
        }
    }
}
```

Key points: `setSubmitterId` to the owner (not the batch user),
`allOrNone = false`, log failures rather than abort.

The submitter caveat that bites here: every `OwnerId` you pass must
be an allowed submitter on the process, or that row fails
(apexrefguide.txt L4021-4024). If owners are a moving population,
either widen `allowedSubmitters` to `<type>owner</type>` /
`<type>allInternalUsers</type>` (api_meta.txt L23228-23262) or drop
`setSubmitterId` and submit as one designated service user, and say
so in the approval comment.

### Pattern B — Auto-approve based on system event

**When to use.** A downstream system signals approval (e.g. CFO
office signs off in an external system; a Platform Event fires;
Apex subscriber auto-approves the matching Salesforce expense).

```apex
trigger ExpenseApprovedEventSubscriber on Expense_Approved__e (after insert) {
    EventBus.TriggerContext ctx = EventBus.TriggerContext.currentContext();
    for (Expense_Approved__e e : Trigger.new) {
        try {
            ProcessInstanceWorkitem wi = findPendingWorkitem(e.Expense_Id__c);
            if (wi == null) {
                ctx.setResumeCheckpoint(e.ReplayId);
                continue;
            }
            Approval.ProcessWorkitemRequest req = new Approval.ProcessWorkitemRequest();
            req.setWorkitemId(wi.Id);
            req.setAction('Approve');
            req.setComments('Auto-approved by external CFO system; ref ' + e.External_Ref__c);
            Approval.process(req);
            ctx.setResumeCheckpoint(e.ReplayId);
        } catch (Exception ex) {
            ApplicationLogger.error('Auto-approve failed', ex);
            ctx.setResumeCheckpoint(e.ReplayId);
        }
    }
}
```

Caveat: auto-approval is a **security-sensitive** action. Audit
who can publish the trigger event. The approval-process-step
defines who's authorized to approve; programmatic auto-approval
bypasses that policy.

### Pattern C — Find stuck approvals

**When to use.** Operational monitoring — surface approvals waiting
on inactive users, approvals older than SLA, approvals on
deleted source records.

```apex
List<ProcessInstanceWorkitem> stuck = [
    SELECT Id, ActorId, ElapsedTimeInDays,
           TYPEOF Actor
               WHEN User THEN Username, IsActive
               WHEN Group THEN DeveloperName
           END,
           ProcessInstance.TargetObjectId, ProcessInstance.Status
    FROM ProcessInstanceWorkitem
    WHERE ProcessInstance.Status = 'Pending'
      AND ElapsedTimeInDays > 7
];

for (ProcessInstanceWorkitem w : stuck) {
    if (w.Actor instanceof User && !((User) w.Actor).IsActive) {
        // Assigned to a deactivated user — reassign.
    } else if (w.Actor instanceof Group) {
        // Assigned to a queue — nobody owns it personally; nudge the queue.
    }
}
```

Three corrections worth carrying: `ActorId` is polymorphic over
`Group` and `User`, so `Actor.IsActive` needs `TYPEOF` and a runtime
type check; age on `ElapsedTimeInDays`, which the Object Reference
documents as filterable, rather than on `CreatedDate`, which the
`ProcessInstanceWorkitem` field table does not list
(object_reference.txt L226816-226905); and do not test
`ProcessInstance.TargetObjectId == null` as a deleted-record signal —
that field is not nillable (object_reference.txt L226147-226160), so
it never comes back empty.

Run as a scheduled batch; surface results to admin dashboard or
notification channel.

### Pattern D — Recall a submission when the source record is invalidated

**When to use.** Source record changes mid-approval such that the
approval should no longer proceed. Example: expense report's
amount drops below the threshold that requires VP approval.

**Approach.** Trigger / flow on the source record detects the
invalidating change. Find the pending workitem and recall.

```apex
public static void recallApproval(Id recordId, String reason) {
    ProcessInstanceWorkitem wi = [
        SELECT Id FROM ProcessInstanceWorkitem
        WHERE ProcessInstance.TargetObjectId = :recordId
          AND ProcessInstance.Status = 'Pending'
        LIMIT 1
    ];
    Approval.ProcessWorkitemRequest req = new Approval.ProcessWorkitemRequest();
    req.setWorkitemId(wi.Id);
    req.setAction('Removed');  // recall
    req.setComments('Auto-recalled: ' + reason);
    Approval.process(req);
}
```

Permission note, stated flatly by the Apex Reference: "Only system
administrators can specify Removed" (apexrefguide.txt L4123-4127).
`ApprovalProcess.allowRecall` governs the UI equivalent — false means
"only administrators can recall approval requests" (api_meta.txt
L23094-23097). A recall from an ordinary user's trigger context will
fail, so route it: catch the failure and park the record for an
admin queue, or run the recall from an async context that executes
as a designated admin.

An alternative that needs no admin: reassign instead of recall.
`ProcessInstanceWorkitem` supports `update()` and `ActorId` is
Updateable (object_reference.txt L226816-226835), so moving the
request to a different approver is plain DML.

---

## Decision Guidance

| Situation | Approach | Reason |
|---|---|---|
| User clicks Submit for Approval on a record page | Standard platform button | No Apex needed |
| System submits 1000 records in a batch | **Pattern A** with `allOrNone = false` | Bulk-submit pattern; partial success preserves successful submissions |
| External system signals approval | **Pattern B** via Platform Event subscriber | Async, durable, decoupled |
| Find approvals stuck > 7 days on inactive users | **Pattern C** with scheduled batch | Operational monitoring |
| Source record changes invalidate the approval | **Pattern D** recall | Don't let an invalid approval complete |
| Backlog of records stuck pending (bad load, rule change, departed approver) | Setup → **Mass Transfer Approval Requests** (remove or transfer); no Apex | Declarative bulk cleanup — Pattern C only surfaces them; `Approval.unlock` drops the lock but removes nothing |
| Custom Lightning component shows approval status + buttons | Apex-driven submit + workitem actions | Wrap Approval.process() in @AuraEnabled |
| Approval step's `assignedApprover` type is `adhoc` | Supply the approver with `setNextApproverIds` (single-entry list) | `adhoc` means "the approver for the step must be selected manually" (api_meta.txt L23389-23392); the Apex guide constrains the list to one Id |
| Need to move a pending request to a different approver | `update` the `ProcessInstanceWorkitem.ActorId` | The field is Updateable and the object supports `update()` — no admin permission needed, unlike recall |
| Bulk approve as part of a system batch | **Pattern B** shape (find workitems → ProcessWorkitemRequest) | Same DML budget: one statement per call, rows against the 10,000 records-processed limit |
| User wants to delegate approvals to another user | Standard Delegated Approver field on User; no Apex | Platform handles delegation |
| Audit trail of who-approved-what | Query `ProcessInstanceStep` | Complete audit history per approval |

---

## Recommended Workflow

1. **Answer the `## Questions to Ask Before Configuring` table** into `templates/approval-process-apex-patterns-template.md`. The `allowedSubmitters`, `allowRecall`, and `adhoc`-approver answers decide whether Patterns A and D are even runnable in your context.
2. **Read the process definition, don't assume it.** Run the `ProcessDefinition` query from `## Before Starting`, then retrieve the `approvalProcess` metadata (`references/metadata-examples.md` § "Retrieve, lint, deploy") and read `allowedSubmitters`, `allowRecall`, `recordEditability`, and every step's `assignedApprover` and `whenMultipleApprovers`.
3. **Deploy the test fixture** — the minimal `ApprovalProcess` XML in `references/metadata-examples.md` — into a scratch org, so the Apex has something deterministic to submit into. Full declarative design lives in `admin/approval-processes`, not here.
4. **Write the service class** from `references/metadata-examples.md` § "The Apex service class": bulk submit with `allOrNone=false` and an error-row collector, workitem action via `getNewWorkitemIds()` or the `TYPEOF` query, and recall guarded by the admin-only constraint.
5. **Lint before you deploy:** `python3 skills/admin/approval-process-apex-patterns/scripts/check_approval_process_apex_patterns.py --manifest-dir force-app/main/default`. It reads `approvalProcesses/*.approvalProcess-meta.xml` and every `.cls` / `.trigger` in the tree, and flags a process name in Apex that no deployed process defines.
6. **Write the tests** from `references/metadata-examples.md` § "Test class skeleton": success, mixed-row partial success, the not-an-allowed-submitter failure, and the non-admin recall failure. Assert on `ProcessResult.getInstanceStatus()` and `getErrors()`, not just `isSuccess()`.
7. **Walk `references/gotchas.md`** and confirm each of the four correction gotchas (5, 7, 8, 11) does not apply to the code you just wrote.

---

## Review Checklist

- [ ] Approval process developer name (not record Id) is referenced in `setProcessDefinitionNameOrId`, and it is never left null when a specific process is intended.
- [ ] `setSubmitterId` is set explicitly when running-user-as-submitter is wrong, **and** every user it can be set to is in the process's `allowedSubmitters`.
- [ ] `setNextApproverIds` is passed a single-entry list, and only where a step actually needs it.
- [ ] `allOrNone = false` for bulk submissions where partial success is acceptable.
- [ ] `Approval.ProcessWorkitemRequest` finds the workitem via `ProcessInstanceWorkitem` query, not assumed.
- [ ] Auto-approval pattern (Pattern B) has explicit security review — who can publish the trigger event.
- [ ] Recall pattern (Pattern D) handles permission errors gracefully (some processes restrict recall to admins).
- [ ] Stuck-approval monitoring (Pattern C) runs as a scheduled batch with results surfaced to admins.
- [ ] Any query over `ActorId` uses `TYPEOF` and handles the `Group` (queue) branch.
- [ ] Aging filters use `ElapsedTimeInDays` / `InHours`, not `CreatedDate`.
- [ ] The transaction's `Approval.process` calls are counted against the 150-DML-statement budget alongside every other DML in the same transaction.
- [ ] `python3 scripts/check_approval_process_apex_patterns.py --manifest-dir <dx root>` passes, or every finding is triaged.

---

## Salesforce-Specific Gotchas

1. **`setProcessDefinitionNameOrId` accepts the API name; hardcoded record IDs break across orgs.** Use API name. (See `references/gotchas.md` § 1.)
2. **Default `allOrNone = true` rolls back the whole batch on first failure.** Bulk submissions need `allOrNone = false` to preserve successful records. (See `references/gotchas.md` § 2.)
3. **`setSubmitterId` defaults to the running user.** System batches that don't set it explicitly produce approvals "submitted by" the batch service account, not the actual owner. (See `references/gotchas.md` § 3.)
4. **`ProcessWorkitemRequest` action values are case-sensitive strings** — `'Approve'` not `'approve'`. (See `references/gotchas.md` § 4.)
5. **Recall (`'Removed'`) is documented as system-administrator-only.** Not "usually restricted" — the Apex Reference says only sysadmins can specify it. (See `references/gotchas.md` § 5.)
6. **Auto-approval bypasses the approval-process step's "Approver assignment"** — the platform records the running user as the approver, not the configured one. Audit implications. (See `references/gotchas.md` § 6.)
7. **The real bulk ceiling is DML, not a 200-request cap.** `Approval.process` burns a DML statement and its rows count toward the 10,000 records-processed limit. (See `references/gotchas.md` § 7.)
8. **`setSubmitterId` fails for any user not in `allowedSubmitters`** — the batch-submits-as-owner pattern breaks the moment an owner falls outside that list. (See `references/gotchas.md` § 11.)
9. **`ActorId` is polymorphic over Group and User**, so `Actor.IsActive` needs `TYPEOF` and a queue-assigned workitem has no user at all. (See `references/gotchas.md` § 13.)
10. **A null `processDefinitionNameOrId` routes by org process order**, and process order is not carried in the metadata across a deploy. (See `references/gotchas.md` § 14.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Apex class implementing the chosen pattern | Submit / action / monitor / recall |
| Bulk submission helper | Chunks 200-at-a-time with allOrNone = false + per-row error logging |
| Stuck-approval monitor | Scheduled batch query + admin notification |
| Test class | Covers success, partial-success, recall, and the inactive-approver case |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You need the deployable test-fixture `ApprovalProcess` XML, the bulk-submit / action / recall service class, the pending-approvals SOQL, the test-class skeleton, the package.xml, or the retrieve/deploy/verify commands |
| `references/gotchas.md` | A submission fails per-row, a recall is refused, a stuck-approval query returns nothing or won't compile, or a process that worked in the sandbox picks a different process in production |
| `references/examples.md` | Walking a concrete failure end to end — the rolled-back batch, the hardcoded process Id, the auto-approval audit finding, the invalidated-record recall, the stuck-approval sweep |
| `references/llm-anti-patterns.md` | Reviewing Apex an AI assistant wrote against the Approval namespace before you deploy it |
| `references/well-architected.md` | Justifying Apex-driven approval to an architecture review, or tracing the official source behind any claim in this skill |
| `templates/approval-process-apex-patterns-template.md` | Workflow step 1 — capturing the process-definition answers before any Apex is written |
| `scripts/check_approval_process_apex_patterns.py` | Workflow step 5, before every deploy that touches approval Apex or approval-process metadata |

---

## Related Skills

- `admin/approval-processes` — declarative definition of the approval process this skill drives.
- `flow/flow-orchestration-patterns` — modern multi-stage approval pattern in Flow; consider before reaching for Apex.
- `apex/apex-event-bus-subscriber` — when system events drive approval actions (Pattern B).
- `apex/apex-mocking-and-stubs` — for the test class that covers Approval.process() failure modes.
