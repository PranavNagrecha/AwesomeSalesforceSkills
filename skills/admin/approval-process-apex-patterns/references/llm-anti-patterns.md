# LLM Anti-Patterns — Approval Process Apex Patterns

Mistakes AI coding assistants commonly make when advising on
programmatic approval-process handling.

---

## Anti-Pattern 1: Hardcoded process-definition record Id

**What the LLM generates.**

```apex
req.setProcessDefinitionNameOrId('300xx0000000123');
```

**Why it happens.** The LLM sees a record Id in Setup or in
example code and emits it literally. Doesn't surface that the Id
isn't portable.

**Correct pattern.**

```apex
req.setProcessDefinitionNameOrId('Expense_Approval');
```

API name is stable across orgs.

**Detection hint.** Any `setProcessDefinitionNameOrId` with a
15- or 18-character record-Id pattern (`300...`) instead of an
API name is non-portable.

---

## Anti-Pattern 2: Bulk submission with default `allOrNone`

**What the LLM generates.**

```apex
Approval.ProcessResult[] results = Approval.process(requests);
```

**Why it happens.** Default-parameter call is the simplest form;
the LLM doesn't surface the all-or-none implication.

**Correct pattern.**

```apex
Approval.ProcessResult[] results = Approval.process(requests, false);
for (Integer i = 0; i < results.size(); i++) {
    if (!results[i].isSuccess()) { /* log per-row */ }
}
```

For bulk submissions where partial success is acceptable.

**Detection hint.** Any bulk Approval.process(...) call without
`allOrNone = false` (and without per-row error handling) is
all-or-nothing — not what most batch contexts want.

---

## Anti-Pattern 3: Default running-user as submitter in system batches

**What the LLM generates.** No `setSubmitterId` call; running user
becomes submitter implicitly.

**Why it happens.** Default behavior; LLM doesn't surface that
batch context's running user is wrong.

**Correct pattern.**

```apex
req.setSubmitterId(record.OwnerId);  // or appropriate user
```

When the running user is a system / batch / Automated Process
identity, set the submitter explicitly.

**Detection hint.** Any system-initiated submission (batch,
trigger, scheduled, Platform Event subscriber) without explicit
`setSubmitterId` will record the wrong submitter.

---

## Anti-Pattern 4: Process-instance vs workitem confusion

**What the LLM generates.**

```apex
ProcessInstance pi = [SELECT Id FROM ProcessInstance WHERE TargetObjectId = :recordId LIMIT 1];
req.setWorkitemId(pi.Id);  // wrong — pi.Id isn't a workitem Id
```

**Why it happens.** "Process Instance" sounds like the right thing
to act on; the LLM doesn't distinguish the parent (`ProcessInstance`)
from the actionable child (`ProcessInstanceWorkitem`).

**Correct pattern.**

```apex
ProcessInstanceWorkitem wi = [
    SELECT Id FROM ProcessInstanceWorkitem
    WHERE ProcessInstance.TargetObjectId = :recordId
      AND ProcessInstance.Status = 'Pending'
    ORDER BY ElapsedTimeInDays ASC LIMIT 1
];
req.setWorkitemId(wi.Id);
```

Better still when the submission happened in the same transaction:
`ProcessResult.getNewWorkitemIds()` returns the new workitem Ids
directly (apexrefguide.txt L3795-3801), so no query is needed at all.
Order on `ElapsedTimeInDays`, not `CreatedDate` — the Object
Reference field table for `ProcessInstanceWorkitem` documents the
elapsed-time fields as Filter and Sort and does not list `CreatedDate`
(object_reference.txt L226836-226852).

**Detection hint.** Any `setWorkitemId` call with a value sourced
from a ProcessInstance query is wrong-type confusion.

---

## Anti-Pattern 5: Action string case-mismatch

**What the LLM generates.**

```apex
req.setAction('approve');  // wrong case
```

**Why it happens.** "approve" reads naturally; the LLM emits
lowercase.

**Correct pattern.** Exact case-sensitive values:

- `'Approve'`
- `'Reject'`
- `'Removed'`

**Detection hint.** Any setAction call with lowercase string is
broken.

---

## Anti-Pattern 6: Recall called from a low-permission trigger context

**What the LLM generates.**

```apex
trigger ExpenseTrigger on Expense__c (after update) {
    // ... detect invalidation ...
    req.setAction('Removed');
    Approval.process(req);  // running as the editing user
}
```

**Why it happens.** Looks like the right place to put the recall.
Doesn't surface that recall is permission-restricted on many
processes.

**Correct pattern.** Either:
- Catch the permission failure and surface to admin queue.
- Move recall to a Platform Event subscriber that runs as a
  configured admin user.
- Document upfront that the editing user has recall permission.

**Detection hint.** Trigger-driven recalls without permission-error
handling are going to fail silently in production for non-admin
editors.

---

## Anti-Pattern 7: Auto-approval without audit-trail documentation

**What the LLM generates.** Auto-approval Apex with no comment
about audit-trail implications.

**Why it happens.** "Auto-approve when X" is the user's stated
need; the LLM emits the code without surfacing security
implications.

**Correct pattern.** Audit-trail comment in the Apex class:

```apex
/**
 * Auto-approves expense reports when the CFO system signals
 * approval via Platform Event.
 *
 * AUDIT NOTE: Salesforce records the running user (Automated
 * Process) as the approver, NOT the configured Director of
 * Finance. The approval policy is enforced upstream by the CFO
 * system; the platform audit trail reflects the Apex running
 * context.
 */
```

Plus a documented operational runbook.

**Detection hint.** Any auto-approval recipe without explicit
audit-trail discussion is missing a security review item.

---

## Anti-Pattern 8: Budgeting bulk submission by chunk size instead of by DML

**What the LLM generates.** One of two shapes, and both come from
the same misunderstanding:

```apex
Approval.process(requests);            // 1000 entries, allOrNone defaults true
```

```apex
for (Expense__c e : records) {         // worse: one DML per record
    Approval.ProcessSubmitRequest req = new Approval.ProcessSubmitRequest();
    req.setObjectId(e.Id);
    Approval.process(req);
}
```

**Why it happens.** The model has absorbed a "200 requests per
`Approval.process` call" rule that does not appear in the Apex
Reference Guide, the Apex Developer Guide, or the App Limits cheat
sheet, and reasons about chunk size instead of about DML.

**What the guides actually say.** `Approval.process` "counts against
the DML limits for your organization" (apexdev.txt L20633-20636).
The two binding numbers are 150 DML statements and 10,000 records
processed per transaction, and the governors table names
`Approval.process` in both rows (apexdev.txt L19548-19556,
L19620-19626).

**Correct pattern.** Build the requests in one loop, process them in
chunks in another, and count the statements:

```apex
List<Approval.ProcessSubmitRequest> requests = new List<Approval.ProcessSubmitRequest>();
for (Expense__c e : records) {
    Approval.ProcessSubmitRequest req = new Approval.ProcessSubmitRequest();
    req.setObjectId(e.Id);
    req.setProcessDefinitionNameOrId('Expense_Approval');
    requests.add(req);
}
for (Integer i = 0; i < requests.size(); i += 200) {
    Integer end = Math.min(i + 200, requests.size());
    List<Approval.ProcessSubmitRequest> chunk = new List<Approval.ProcessSubmitRequest>();
    for (Integer j = i; j < end; j++) chunk.add(requests[j]);
    Approval.process(chunk, false);   // one DML statement per chunk
}
```

**Detection hint.** A loop body that both constructs an
`Approval.Process*Request` and calls `Approval.process` is the
per-record shape — that is exactly what
`scripts/check_approval_process_apex_patterns.py` flags CRITICAL.
A model that cites "the 200-record governor" as its reason is
repeating an ungrounded number; the reason is DML.

---

## Anti-Pattern 9: Apex batch to clear a backlog of stuck approvals

**What the LLM generates.**

```apex
delete [SELECT Id FROM ProcessInstanceWorkitem WHERE ProcessInstance.Status = 'Pending'];
// or
Approval.unlock(stuckRecordIds);
```

**Why it happens.** "Hundreds of records are stuck pending after a
bad load / a rule change / a departed approver" sounds like an Apex
problem. `Approval.unlock()` per the Apex Reference only "unlocks
an object" — the record is still in the process, so it still can't
be resubmitted. `delete` on `ProcessInstanceWorkitem` is legal DML
(`delete()` is a supported call) but is not a documented way to
take a record out of a process.

**Correct pattern.** The bulk tool is declarative. From Setup,
enter **Mass Transfer Approval Requests** in the Quick Find box,
click **Find**, then pick one of its two options:

- **Mass remove records from an approval process** — unlocks the
  records and takes them out of the process, so they drop off the
  approvers' pending lists.
- **Mass transfer outstanding approval requests to a new user** —
  reassigns them instead (approver left, submission still valid);
  the target user must have permission to edit those records.

Comments entered on that screen land on the record's Approval
History related list, so the cleanup is auditable.

**Detection hint.** Backlog-clearing answers that reach for DML on
`ProcessInstanceWorkitem` or `Approval.unlock` solve a different
problem. Apex's removal path — `setAction('Removed')` per work
item, recall permission required (Gotcha 5) — is for targeted
recalls (Pattern D), not an admin backlog cleanup.
