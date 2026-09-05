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

## Gotcha 5: `'Removed'` is system-administrator-only, not "usually restricted"

**What happens.** Apex calls `setAction('Removed')` from a trigger
running as the record's editor. The recall is refused. Teams
routinely read this as an org-configuration problem and go looking
for a permission to grant; there isn't one to grant.

**When it occurs.** Any programmatic recall from a non-admin running
context — a trigger, a Queueable enqueued by a standard user, an
`@AuraEnabled` method behind a custom button.

**Ground truth.** The Apex Reference Guide states the constraint on
`setAction(actionType)` without qualification: "Valid values are:
Approve, Reject, or Removed. **Only system administrators can specify
Removed**" (apexrefguide.txt L4123-4127). Separately, the
`ApprovalProcess.allowRecall` metadata field controls the UI path:
"Whether to allow submitters to recall approval requests. If set to
false, only administrators can recall approval requests"
(api_meta.txt L23095-23098). These are two different gates — a
process with `allowRecall=true` still does not let non-admin Apex
pass `'Removed'`.

**How to avoid.**
- Do not design a recall path that runs in the editing user's
  context. Route the recall to something that executes as an admin,
  or park the record.
- Prefer reassignment where it satisfies the requirement.
  `ProcessInstanceWorkitem` supports `update()` and its `ActorId` is
  Updateable (object_reference.txt L226816-226835), so moving a
  request to a different approver is plain DML with no
  administrator gate.
- Where recall really is required, catch the failure and write the
  record to an admin-action queue. UNVERIFIED (2026-09-05): the
  guides do not name the exception type or status code returned when
  a non-admin specifies `'Removed'`, so catch broadly and log
  `getErrors()` rather than matching on a specific code.

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

## Gotcha 7: the bulk ceiling is DML statements and rows, not a 200-per-call cap

**What happens.** A team chunks submissions at 200 to respect a
"200 requests per `Approval.process` call" limit, then still blows
the transaction — because 40 chunks is 40 DML statements, and the
transaction already spent 120 elsewhere. The chunk size was never
the binding constraint.

**When it occurs.** Bulk submission in a trigger or a Batch Apex
`execute()` that also does ordinary DML on the same records.

**Ground truth.** Two documented limits apply, both from the Apex
Developer Guide's execution-governors table (apexdev.txt
L19548-19556 and footnote 2 at L19620-19626, mirrored in the App
Limits cheat sheet at salesforce_app_limits_cheatsheet.txt L64-67
and L135-141):

| Limit | Sync | Async |
|---|---|---|
| Total DML statements issued — `Approval.process` counts as one | 150 | 150 |
| Total records processed by DML statements, `Approval.process`, or `Database.emptyRecycleBin` | 10,000 | 10,000 |

The Apex Developer Guide restates it plainly: "the `process` method
counts against the DML limits for your organization" (apexdev.txt
L20633-20638). `Approval.lock` and `Approval.unlock` are also DML:
"they're blocked before a callout, they count toward your DML
limits, and if a failure occurs, they're rolled back along with the
rest of your transaction" (apexrefguide.txt L199732-199736).

UNVERIFIED (2026-09-05): no per-call list-size cap for
`Approval.process` appears in the Apex Reference Guide, the Apex
Developer Guide, or the App Limits cheat sheet. The commonly cited
200 figure is not grounded in these sources.

**How to avoid.** Budget the DML statements, not the chunk count:
a 10,000-row submission is at minimum 50 statements at a chunk size
of 200, so it belongs in Batch Apex with a scope that leaves DML
headroom for everything else in the transaction. Chunking at 200
remains sensible for heap and blast radius — treat it as a design
convention rather than a limit you are avoiding.

---

## Gotcha 8: `setNextApproverIds` takes exactly one Id, and only where a step needs one

**What happens.** Code passes a two-element list to
`setNextApproverIds`, expecting both users to receive the request,
or passes an approver to a process whose steps resolve their own
approvers. Either way the submission behaves unlike the code reads.

**When it occurs.** Generic submission helpers that always populate
`nextApproverIds` from a caller-supplied list.

**Ground truth.** The parameter is documented as "Must be a
single-entry list" and the method "sets the `ActorId` field of the
associated ProcessInstanceWorkItem" — it writes one actor, not a
set (apexrefguide.txt L3684-3695). The surrounding prose is
narrower still: "If the next step in your approval process is
another Apex approval process, you specify exactly one user ID as
the next approver. If not, you cannot specify a user ID and this
method must be null" (apexrefguide.txt L3631-3634).

Multiple approvers on a step are a *metadata* concern, not an Apex
one: `ApprovalStepApprover` holds an `Approver[]` plus
`whenMultipleApprovers` (`Unanimous` or `FirstResponse`), and "each
step supports up to 25 approvers" (api_meta.txt L23356-23368).

UNVERIFIED (2026-09-05): the widespread rule "you must set
`setNextApproverIds` whenever a step uses manual approver selection"
is not stated in the Apex Reference Guide. What the Metadata API
guide does say is that approver `type` `adhoc` means "the approver
for the step must be selected manually. For the first step, the
submitter selects the approver" (api_meta.txt L23389-23392), which
makes supplying the approver from Apex the natural reading — but
the failure mode when you omit it is not documented in these
sources.

**How to avoid.** Read the process's steps first. Populate
`setNextApproverIds` only for a step whose `assignedApprover` type
is `adhoc`, and populate it with exactly one Id.

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

---

## Gotcha 11: `setSubmitterId` rejects any user who isn't an allowed submitter

**What happens.** The month-end batch sets
`req.setSubmitterId(record.OwnerId)` so that approvals appear to
come from the owner. It works in the sandbox, where the process was
built with a wide submitter list. In production the process is
scoped to one role, and every row owned by someone outside that role
fails — while rows owned by insiders sail through. With
`allOrNone=false` the batch reports partial success and nobody
investigates the shortfall.

**When it occurs.** Any system-initiated submission on behalf of a
varying population of owners, against a process whose
`allowedSubmitters` is narrower than that population.

**Ground truth.** "The user must be one of the allowed submitters in
the process definition setup" — stated on both `getSubmitterId()`
and `setSubmitterId(userID)` (apexrefguide.txt L3868-3870,
L4021-4024). `allowedSubmitters` is a **required** field on
`ApprovalProcess` and takes an `ApprovalSubmitter[]` whose `type`
may be `group`, `role`, `user`, `roleSubordinates`,
`roleSubordinatesInternal`, `owner`, `creator`, `partnerUser`,
`customerPortalUser`, `portalRole`, `portalRoleSubordinates`, or
`allInternalUsers` (api_meta.txt L23100-23102, L23405-23450).

**How to avoid.** Before writing the batch, read the deployed
process's `allowedSubmitters`. Then choose deliberately: widen it
with `<type>owner</type>` so record owners always qualify, or stop
setting `setSubmitterId` at all and submit as one designated service
user whose identity the approval comment explains. Do not leave it
to chance across a population you don't control.

---

## Gotcha 12: `Approval.lock` / `unlock` are DML, and are blocked before a callout

**What happens.** A service class calls an external system, then
calls `Approval.unlock(records)` to release the approval lock in the
same method. Or it locks first and then makes the callout. One of
the two orderings throws "You have uncommitted work pending",
because the lock counted as DML.

**When it occurs.** Any method that mixes approval lock manipulation
with HTTP callouts — a common shape when an external system is the
source of the approve/reject signal.

**Ground truth.** From the `Approval` class usage notes: "Record
locks and unlocks are treated as DML. They're blocked before a
callout, they count toward your DML limits, and if a failure occurs,
they're rolled back along with the rest of your transaction. To
change this rollback behavior, use an `allOrNone` parameter"
(apexrefguide.txt L199732-199736).

**How to avoid.** Treat `lock` / `unlock` exactly like an `update`:
do all callouts first, or move the lock manipulation into a
`@future(callout=false)` / Queueable that runs after the callout
returns. Use the `allOrNothing=false` overload and read the returned
`LockResult` / `UnlockResult` array — its elements correspond
positionally to the input list (apexrefguide.txt L3491-3496).

Note also what `unlock` does *not* do: it drops the record lock, it
does not remove the pending approval. The `ProcessInstanceWorkitem`
survives and the approver can still act.

---

## Gotcha 13: `ActorId` is polymorphic over Group and User

**What happens.** The stuck-approval query selects `Actor.IsActive`
to find requests parked on deactivated users. It doesn't compile.
The developer works around it by selecting `ActorId` and querying
`User` separately — and the report then silently drops every request
assigned to a queue, because those actor Ids are not user Ids and
the second query returns nothing for them.

**When it occurs.** Any approval-hygiene report, on any process
whose steps include an `assignedApprover` of type `queue`.

**Ground truth.** On both `ProcessInstanceWorkitem.ActorId` and
`ProcessInstanceStep.ActorId`: "This field is a polymorphic
relationship field ... Refers To: Group, User"
(object_reference.txt L226648-226670, L226819-226833). The same
holds for `OriginalActorId`. The Metadata API's `Approver.type`
enum confirms queues are legitimate approvers: `adhoc`, `user`,
`userHierarchyField`, `relatedUserField`, `queue` (api_meta.txt
L23384-23400).

**How to avoid.** Use `TYPEOF` in the SELECT and branch on runtime
type:

```apex
List<ProcessInstanceWorkitem> items = [
    SELECT Id, ActorId, ElapsedTimeInDays,
           TYPEOF Actor
               WHEN User  THEN Username, IsActive
               WHEN Group THEN DeveloperName, Type
           END
    FROM ProcessInstanceWorkitem
    WHERE ProcessInstance.Status = 'Pending'
];
for (ProcessInstanceWorkitem w : items) {
    if (w.Actor instanceof User) {
        if (!((User) w.Actor).IsActive) { /* deactivated approver */ }
    } else {
        /* queue - report it as unclaimed, not as a broken user */
    }
}
```

Two related corrections while you are in that query. Age on
`ElapsedTimeInDays` / `InHours` / `InMinutes`, which the Object
Reference documents as Filter and Sort on both objects
(object_reference.txt L226836-226878) — `CreatedDate` is not in
either field table. And do not use `ProcessInstance.TargetObjectId
== null` as a deleted-source-record signal: the field's properties
are Filter, Group, Sort with no Nillable (object_reference.txt
L226147-226160), so it never returns empty.

---

## Gotcha 14: a null `processDefinitionNameOrId` routes by org process order, which deploys don't carry

**What happens.** Apex submits without naming a process, relying on
the platform to pick the right one by entry criteria — which it did
correctly for two years. A release adds a second approval process to
the same object. After the deploy, submissions land in the new
process in production and the old one in the sandbox, from identical
code and identical metadata.

**When it occurs.** Any org with more than one active approval
process on the same object, after any deployment that adds or
replaces one.

**Ground truth.** With the name unset, "the submission of a record
for approval evaluates entry criteria for all processes applicable
to the submitter. **The order of evaluation is based on the process
order of the setup**" (apexrefguide.txt L3987-3989). And that order
is not in the metadata: "The metadata doesn't include the order of
active approval processes. Sometimes you have to reorder the
approval processes in the destination org after deployment"
(api_meta.txt L23067-23068).

**How to avoid.** Always name the process explicitly in Apex.
Reserve the null form for a genuinely open "submit to whatever
applies" button. Add a post-deploy checklist item to verify process
order in Setup, and a preflight query that fails loudly when more
than one active process exists on the object:

```sql
SELECT DeveloperName, State FROM ProcessDefinition
WHERE TableEnumOrId = 'Expense__c' AND State = 'Active'
```

---

## Gotcha 15: `setSkipEntryCriteria(true)` is silently ignored when no process is named

**What happens.** A migration script sets
`setSkipEntryCriteria(true)` to push legacy records into approval
regardless of criteria, but doesn't set
`setProcessDefinitionNameOrId`. The flag does nothing; records that
fail entry criteria fail the submission, and the log shows a
criteria error the developer believed had been switched off.

**When it occurs.** Backfill and data-migration submissions written
against `setSkipEntryCriteria` alone.

**Ground truth.** "If the process definition name or ID is not
specified, this parameter is ignored and standard evaluation is
followed based on process order" (apexrefguide.txt L4005-4014). The
method's own summary says the same thing conditionally: "If the
process definition name or ID is not null, `setSkipEntryCriteria()`
determines whether to evaluate the entry criteria" (apexrefguide.txt
L3999-4001).

**How to avoid.** The two methods are a pair. Never call
`setSkipEntryCriteria(true)` without `setProcessDefinitionNameOrId`
in the same request builder — and write the justification for the
bypass next to the call, because the record you are pushing through
is one the admin's criteria were written to exclude.

---

## Gotcha 16: on a unanimous step, one rejection turns the other approvers into `NoResponse`

**What happens.** The approval audit report counts
`ProcessInstanceStep` rows where `StepStatus = 'Rejected'` to measure
rejection rate. On a two-approver unanimous step, one rejection
produces exactly one `Rejected` row; the other approver's row reads
`NoResponse`. The report undercounts, and "approvers who never
responded" is inflated by people who were never asked to.

**When it occurs.** Any step whose `whenMultipleApprovers` is
`Unanimous` (the default) or `FirstResponse`.

**Ground truth.** From the `StepStatus` field description: "If the
approval step requires unanimous approval and one approver rejects
the request, the value of this field for the other approvers changes
to `NoResponse`. Likewise, if approval is based on the first
response and an approver responds, the value of this field for the
other approvers changes to `NoResponse`" (object_reference.txt
L226753-226760). The nine valid values are Approved, Fault, Held,
NoResponse, Pending, Reassigned, Rejected, Removed, Started —
identical to `ProcessInstance.Status` (object_reference.txt
L226112-226145).

**How to avoid.** Measure rejection at the *instance* level
(`ProcessInstance.Status = 'Rejected'`), not the step level. When
step-level detail is genuinely needed, read
`whenMultipleApprovers` off the process metadata first and treat
`NoResponse` on a unanimous or first-response step as "superseded",
not as "ignored".

---

## Gotcha 17: deploying a process with no entry criteria over one that has them keeps the old criteria

**What happens.** A team removes `<entryCriteria>` from the approval
process in source control, intending every record to enter. The
deploy succeeds. Submissions still fail entry criteria — against
criteria that no longer exist anywhere in the repository.

**When it occurs.** Any overwrite deploy of an `ApprovalProcess`
whose source has dropped an `entryCriteria` block the target org
still has.

**Ground truth.** "When you deploy an approval process with no entry
criteria to overwrite an existing approval process with entry
criteria, then the entry criteria from the existing process are
applied to the deployed process" (api_meta.txt L23136-23139). This
compounds with the activation freeze on the same type: "After an
approval process is activated, you can't add, delete, or change the
order of the steps or change its reject or skip behavior, even if
the process is inactive" (api_meta.txt L23082-23086, restated for
`ApprovalStep` at L23284-23285), and "each approval process supports
up to 30 steps" (api_meta.txt L23286).

**How to avoid.** Removing entry criteria is not a source change —
it is a Setup change. Retrieve the process after every deploy and
diff it against source before trusting Apex that depends on the
criteria. Where criteria genuinely must go, delete the process and
redeploy it rather than overwriting, and expect to re-set process
order afterwards.
