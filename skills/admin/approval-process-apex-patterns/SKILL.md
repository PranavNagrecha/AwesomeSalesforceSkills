---
name: approval-process-apex-patterns
description: "Programmatically driving Salesforce Approval Processes from Apex — `Approval.process(ProcessSubmitRequest)` to submit, `ProcessWorkitemRequest` to approve / reject / reassign, recall semantics, querying `ProcessInstance` and `ProcessInstanceWorkitem` to find pending approvals, and the bulk-submit / bulk-action error-row handling. Covers when to use Apex-driven approval (system-initiated submission, batch approvals, custom UIs) vs leaving the platform's standard buttons in place. NOT for the Approval Process metadata definition itself (that's admin / declarative — see admin/approval-process-design), NOT for Flow-based approvals (use flow/flow-orchestration-patterns)."
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
  - "Bulk requirement: single record per request or up to 200 per call"
  - "Error-row policy: fail-fast or partial-success"
outputs:
  - "Apex code using Approval.process() with the right Request type"
  - "Bulk-action error handling (allOrNone vs partial)"
  - "Query patterns to find pending approval items for a record / user"
  - "Recall pattern when the source record is invalidated mid-approval"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-04
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
declarative admin work — see `admin/approval-process-design`. The
modern Flow-based equivalent (Flow Orchestration with interactive
steps assigned to approvers) is a different runtime entirely — see
`flow/flow-orchestration-patterns`.

---

## Before Starting

- **Confirm the Approval Process is defined and active.** Apex calls
  reference the process by name; if it's inactive, the call fails
  with a generic error.
- **Decide who initiates the approval.** User-initiated submissions
  carry the user's context (running user becomes the submitter).
  System-initiated submissions need a `submitterId` (the user the
  approval is "from").
- **Decide the bulk shape.** `Approval.process(...)` accepts a list
  of Requests up to 200. Above that, batch the submissions.
- **Decide the error-row policy.** `allOrNone = true` (default):
  any failure rolls back the whole batch. `allOrNone = false`:
  individual failures are reported but successful submissions
  proceed.

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

- `setProcessDefinitionNameOrId` — the API name of the approval
  process. Use the API name; hardcoded record IDs are brittle.
- `setSubmitterId` — defaults to running user; set explicitly when
  you want the approval to appear as "submitted by" a specific user.
- `setSkipEntryCriteria(true)` — submit even if the record doesn't
  match the process's entry criteria. Useful but dangerous; document
  why.
- `setNextApproverIds(new List<Id>{ ... })` — override the platform's
  approver lookup. Required when the process uses "submitter
  manually selects approver".

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

Action values:

- `'Approve'` — approve the workitem.
- `'Reject'` — reject the workitem.
- `'Removed'` — recall the submission (admin-only typically; check
  process settings).
- For reassign: leave `action` null, set
  `setNextApproverIds(new List<Id>{ newApproverId })`.

### Querying pending approvals

```apex
List<ProcessInstance> pending = [
    SELECT Id, TargetObjectId, Status, CreatedDate,
           (SELECT ActorId, ProcessNodeId FROM Workitems)
    FROM ProcessInstance
    WHERE Status = 'Pending'
      AND TargetObject.Type = 'Expense_Report__c'
];
```

`ProcessInstance` is the in-flight approval. `ProcessInstanceStep`
is the audit trail of completed steps. `ProcessInstanceWorkitem`
is the open assignment to a specific approver.

The most common query is "find pending workitems older than N days
assigned to inactive users" — the stuck-approval audit pattern.

### Bulk submission

`Approval.process(...)` accepts a `List<ProcessRequest>` up to 200.
Above 200, batch into chunks:

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
    SELECT Id, ActorId, Actor.IsActive, CreatedDate,
           ProcessInstance.TargetObjectId, ProcessInstance.Status
    FROM ProcessInstanceWorkitem
    WHERE ProcessInstance.Status = 'Pending'
      AND CreatedDate < :Date.today().addDays(-7)
];

for (ProcessInstanceWorkitem w : stuck) {
    if (!w.Actor.IsActive) {
        // Reassign or recall.
    } else if (w.ProcessInstance.TargetObjectId == null) {
        // Source record deleted — recall.
    }
}
```

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

Permission note: the running user must have permission to recall
on this approval process. Some processes restrict recall to admins;
in that case the trigger needs to run as an admin context (custom
metadata-driven escalation).

---

## Decision Guidance

| Situation | Approach | Reason |
|---|---|---|
| User clicks Submit for Approval on a record page | Standard platform button | No Apex needed |
| System submits 1000 records in a batch | **Pattern A** with `allOrNone = false` | Bulk-submit pattern; partial success preserves successful submissions |
| External system signals approval | **Pattern B** via Platform Event subscriber | Async, durable, decoupled |
| Find approvals stuck > 7 days on inactive users | **Pattern C** with scheduled batch | Operational monitoring |
| Source record changes invalidate the approval | **Pattern D** recall | Don't let an invalid approval complete |
| Custom Lightning component shows approval status + buttons | Apex-driven submit + workitem actions | Wrap Approval.process() in @AuraEnabled |
| Approval process uses "manually select approver" | Always set `setNextApproverIds` | Required by the process; otherwise submit fails |
| Bulk approve as part of a system batch | **Pattern B** shape (find workitems → ProcessWorkitemRequest) | Same governor budget per call (200 max) |
| User wants to delegate approvals to another user | Standard Delegated Approver field on User; no Apex | Platform handles delegation |
| Audit trail of who-approved-what | Query `ProcessInstanceStep` | Complete audit history per approval |

---

## Recommended Workflow

1. **Confirm the approval process is defined and active.** API name is what Apex references.
2. **Identify the use case.** User-initiated standard button (no Apex), system-initiated submission (Pattern A), system-initiated action (Pattern B), monitoring (Pattern C), recall (Pattern D).
3. **Build with `allOrNone = false`** for any bulk submission to preserve successful submissions.
4. **Set `setSubmitterId` explicitly** when the running user isn't the right "from" user.
5. **For action requests**, query the workitem first (don't try to compute it from the record alone).
6. **Test the failure cases.** Inactive approver, record not matching entry criteria, recalled submission, bulk with mixed valid + invalid records.

---

## Review Checklist

- [ ] Approval process API name (not record Id) is referenced in `setProcessDefinitionNameOrId`.
- [ ] `setSubmitterId` is set explicitly when running-user-as-submitter is wrong.
- [ ] `allOrNone = false` for bulk submissions where partial success is acceptable.
- [ ] `Approval.ProcessWorkitemRequest` finds the workitem via `ProcessInstanceWorkitem` query, not assumed.
- [ ] Auto-approval pattern (Pattern B) has explicit security review — who can publish the trigger event.
- [ ] Recall pattern (Pattern D) handles permission errors gracefully (some processes restrict recall to admins).
- [ ] Stuck-approval monitoring (Pattern C) runs as a scheduled batch with results surfaced to admins.

---

## Salesforce-Specific Gotchas

1. **`setProcessDefinitionNameOrId` accepts the API name; hardcoded record IDs break across orgs.** Use API name. (See `references/gotchas.md` § 1.)
2. **Default `allOrNone = true` rolls back the whole batch on first failure.** Bulk submissions need `allOrNone = false` to preserve successful records. (See `references/gotchas.md` § 2.)
3. **`setSubmitterId` defaults to the running user.** System batches that don't set it explicitly produce approvals "submitted by" the batch service account, not the actual owner. (See `references/gotchas.md` § 3.)
4. **`ProcessWorkitemRequest` action values are case-sensitive strings** — `'Approve'` not `'approve'`. (See `references/gotchas.md` § 4.)
5. **Recall (`'Removed'` action) requires permission** that not every running user has. Test under the actual context. (See `references/gotchas.md` § 5.)
6. **Auto-approval bypasses the approval-process step's "Approver assignment"** — the platform records the running user as the approver, not the configured one. Audit implications. (See `references/gotchas.md` § 6.)
7. **Approval Process Apex API has a per-call governor of 200 requests.** Bulk submissions above 200 need batching. (See `references/gotchas.md` § 7.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Apex class implementing the chosen pattern | Submit / action / monitor / recall |
| Bulk submission helper | Chunks 200-at-a-time with allOrNone = false + per-row error logging |
| Stuck-approval monitor | Scheduled batch query + admin notification |
| Test class | Covers success, partial-success, recall, and the inactive-approver case |

---

## Related Skills

- `admin/approval-process-design` — declarative definition of the approval process this skill drives.
- `flow/flow-orchestration-patterns` — modern multi-stage approval pattern in Flow; consider before reaching for Apex.
- `apex/apex-event-bus-subscriber` — when system events drive approval actions (Pattern B).
- `apex/apex-mocking-and-stubs` — for the test class that covers Approval.process() failure modes.
