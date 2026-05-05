# Gotchas — Approval Process Apex Patterns

Non-obvious Approval Process Apex API behaviors that bite real
production code.

---

## Gotcha 1: `setProcessDefinitionNameOrId` accepts API name; record IDs aren't portable

**What happens.** Apex code uses the approval process record Id
(`300xx0000000123`). Sandbox refresh creates a new approval process
with a different Id; Apex still references the old one. Submissions
fail.

**When it occurs.** Apex written against Setup-page record Ids
rather than API names.

**How to avoid.** Always reference by API name:
`req.setProcessDefinitionNameOrId('Expense_Approval')`. API names
are stable across orgs.

---

## Gotcha 2: Default `allOrNone = true` rolls back the whole batch

**What happens.** Bulk submission of 500 records — one record fails
entry criteria — all 500 roll back. Zero successful submissions.

**When it occurs.** Default Approval.process() call signature
without the explicit allOrNone parameter.

**How to avoid.** `Approval.process(requests, false)` for bulk —
allows partial success. Iterate over results to log per-row
failures.

---

## Gotcha 3: `setSubmitterId` defaults to the running user

**What happens.** A scheduled batch submits expense reports. The
batch runs as the Automated Process user. Without explicit
`setSubmitterId`, every submission appears as "submitted by
Automated Process" instead of "submitted by [the actual record
owner]".

**When it occurs.** System-initiated submissions where the running
context isn't the right "from" user.

**How to avoid.** Always set `setSubmitterId` explicitly in
batch / trigger / system contexts:

```apex
req.setSubmitterId(record.OwnerId);
```

---

## Gotcha 4: `ProcessWorkitemRequest` action values are case-sensitive

**What happens.** Apex uses `req.setAction('approve')` (lowercase).
The platform doesn't recognize the action; submission fails or
defaults to no-op.

**When it occurs.** Typos / case-mismatch from copy-paste.

**How to avoid.** Use the exact platform-defined values:
- `'Approve'`
- `'Reject'`
- `'Removed'` (for recall)

Reassignment uses null action plus `setNextApproverIds`.

---

## Gotcha 5: Recall (`'Removed'`) requires permission not every user has

**What happens.** Apex calls `setAction('Removed')` from a trigger
running as the record's editor (not an admin). The recall fails
with a permissions error.

**When it occurs.** Triggers / flows that auto-recall on record
invalidation, when the editing user doesn't have process-recall
permission.

**How to avoid.**
- Document which approval processes restrict recall to admins.
- Either: design the trigger to run in an admin context (custom
  metadata-driven escalation, or a Platform Event subscriber that
  runs as a configured admin user).
- Or: catch the permission failure and surface to an admin-action
  queue rather than failing silently.

---

## Gotcha 6: Auto-approval bypasses the approval process step's "Approver assignment"

**What happens.** Approval process step says "Approver = Director
of Finance". Apex auto-approves via `setAction('Approve')` running
as the Automated Process user. The audit trail records "approved by
Automated Process", not Director of Finance.

**When it occurs.** Auto-approval patterns driven by external
signals (Pattern B in SKILL.md).

**How to avoid.** Either accept the audit-trail mismatch (and
document it explicitly so auditors understand the policy is
upstream of the platform action), or impersonate the configured
approver context (more complex, requires Modify All Data and
careful context-switching).

---

## Gotcha 7: 200-request governor per Approval.process() call

**What happens.** Apex passes 1000 ProcessSubmitRequests in a single
call. The platform throws a governor-limit exception.

**When it occurs.** Bulk submissions without batching.

**How to avoid.** Chunk into 200-record slices:

```apex
for (Integer i = 0; i < requests.size(); i += 200) {
    Integer end = Math.min(i + 200, requests.size());
    List<Approval.ProcessSubmitRequest> chunk = ...
    Approval.process(chunk, false);
}
```

Each chunk counts as one DML statement against the 150-DML governor;
plan accordingly for very large batches that may need a
Queueable / Batch Apex shape.

---

## Gotcha 8: `Approval.ProcessSubmitRequest` doesn't support all approval-process variants

**What happens.** Approval process configured with "Submitter
manually selects approver". Apex submits without
`setNextApproverIds`. Submission fails with "Next approver not
specified".

**When it occurs.** Approval processes that defer approver
selection to the submitter (vs platform formula).

**How to avoid.** Always set `setNextApproverIds` when the process
requires manual approver selection. Inspect the process definition
upfront to know which knob to set.

---

## Gotcha 9: Querying for "pending" approvals returns empty after recall

**What happens.** Apex queries `ProcessInstance` filtered by
`Status = 'Pending'` to find items to act on. After a recall, the
ProcessInstance.Status becomes `Removed` — the query no longer
returns it. Subsequent code that expected to find the recalled item
gets nothing.

**When it occurs.** Recall + re-find logic that doesn't account
for status transitions.

**How to avoid.** Be explicit about which Status values the query
includes. For "pending" only, `Status = 'Pending'` is correct. For
"any approval that ever existed", drop the Status filter and check
explicitly in code.

---

## Gotcha 10: Approval Process metadata changes don't migrate in-flight approvals

**What happens.** Admin updates an approval process (adds a step,
changes approvers). In-flight approvals continue with the previous
process definition. The new behavior applies only to approvals
submitted after the change.

**When it occurs.** Mid-cycle approval process updates.

**How to avoid.** Plan approval-process changes during quiet
periods. Document expected mid-flight behavior. Or recall in-flight
items and resubmit under the new process for high-value cases.
