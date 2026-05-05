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
    ORDER BY CreatedDate DESC LIMIT 1
];
req.setWorkitemId(wi.Id);
```

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

## Anti-Pattern 8: Submitting > 200 records in one Approval.process() call

**What the LLM generates.**

```apex
Approval.process(requests);  // requests has 1000 entries
```

**Why it happens.** "Just bulk it" instinct; doesn't surface the
200-per-call governor.

**Correct pattern.** Chunk into 200-record slices:

```apex
for (Integer i = 0; i < requests.size(); i += 200) {
    Integer end = Math.min(i + 200, requests.size());
    List<Approval.ProcessSubmitRequest> chunk = new List<Approval.ProcessSubmitRequest>();
    for (Integer j = i; j < end; j++) chunk.add(requests[j]);
    Approval.process(chunk, false);
}
```

**Detection hint.** Any single Approval.process() call with a list
larger than 200 entries hits the governor.
