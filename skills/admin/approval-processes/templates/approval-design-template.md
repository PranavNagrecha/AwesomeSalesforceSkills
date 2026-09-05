# Approval Process Design Template

Fill this in before building or changing any Approval Process. Every row maps to an element of `approvalProcesses/<Object>.<Name>.approvalProcess-meta.xml`; the element name is given so the completed table can be transcribed straight into XML (`references/metadata-examples.md`).

Replace the bracketed guidance with your answer. A row you cannot answer is a design gap, not a formatting problem.

---

## Irreversible Decisions — settle these first

The Metadata API guide states that after activation you cannot add, delete, or reorder steps, or change reject or skip behaviour, even after deactivating the process. Everything in this block is frozen at first activation, in every org.

| Decision | XML element | Answer |
|---|---|---|
| Number of steps and their order | order of `approvalStep[]` | [e.g. 2 steps: Manager Approval, then Deal Desk Approval] |
| What happens when an approver rejects at each step after the first | `approvalStep.rejectBehavior.type` | [`RejectRequest` kills the request, or `BackToPrevious` returns it to the previous approver — per step; not allowed on step 1] |
| What happens to a record that does not meet a step's criteria | `approvalStep.ifCriteriaNotMet` | [`ApproveRecord`, `GotoNextStep`, or `RejectRecord` (first step only) — per step] |

Sign-off that these are agreed with the process owner: [name, date]

## Overview

| Property | XML element | Answer |
|---|---|---|
| Process name (API) | `fullName` / file name | [`Object.Process_Name`, e.g. `Opportunity.Discount_Approval`] |
| Label shown to users | `label` | [e.g. Opportunity Discount Approval] |
| Object | file name prefix | [standard or custom object being approved] |
| Business purpose | `description` | [the decision being made and who is accountable for it — one sentence] |
| Submitter population | `allowedSubmitters[]` | [one row per group: `type` = `owner` / `creator` / `user` / `group` / `role` / `roleSubordinates` / `roleSubordinatesInternal` / `partnerUser` / `customerPortalUser` / `portalRole` / `portalRoleSubordinates` / `allInternalUsers`; `submitter` is ignored for `owner`, `creator`, `allInternalUsers`] |
| Auto-submission, if any | — | [record-triggered Flow or Apex, and whether that running user is inside `allowedSubmitters`; name the process explicitly so process order cannot reroute it] |
| Who can edit while pending | `recordEditability` | [`AdminOnly` or `AdminOrCurrentApprover` — the record is always locked otherwise; `AdminOrCurrentApprover` also needs the approver to have edit access via permissions and OWD] |
| Lock after final approval | `finalApprovalRecordLock` | [`false` unless the business asked for a permanently frozen record; `true` means admin-only forever] |
| Lock after final rejection | `finalRejectionRecordLock` | [`false` unless rejected records must be frozen for audit] |
| Recall allowed for submitters | `allowRecall` | [`true`, or `false` to restrict recall to administrators] |
| Approval-request email template | `emailTemplate` | [`Folder/Developer_Name` of a **Classic** template, or omit for the default] |
| Fields shown on the approval page | `approvalPageFields.field[]` | [only the fields an approver needs to decide — these appear on mobile too] |
| Mobile / external approval page | `enableMobileDeviceAccess` | [`true` forbids `adhoc` approvers anywhere in the process] |
| Approval History related list | `showApprovalHistory` | [`true` to show it on the approval page; page layouts are separate] |
| Other active processes on this object, in order | not in metadata | [list them; the first whose entry criteria match wins, and the order must be set by hand in each org after deploy] |

## Entry Criteria

| Question | XML element | Answer |
|---|---|---|
| Which records may enter the process at all? | `entryCriteria.criteriaItems[]` **or** `entryCriteria.formula` — never both | [filter items as `field` / `operation` / `value`, or one formula; omit the element entirely to admit every record] |
| Filter logic across the items | `entryCriteria.booleanFilter` | [e.g. `1 AND (2 OR 3)`; without it the items are ANDed] |
| Fields that must be populated before submit | validation rule, not this file | [list them; a blank approver source is a runtime submission failure the approval engine will not catch for you] |
| How are invalid submissions blocked? | validation rule / Flow entry condition | [the rule name and its message; note that `valueField` field-to-field comparison is not supported in approval criteria, so cross-field checks belong in a formula or a validation rule] |
| How is this process kept distinct from the other active processes on this object? | — | [the criterion that makes them mutually exclusive, or an explicit statement that order is the tie-breaker] |

## Step Design

One row per step. Add or remove rows to match; document order is execution order, and the ceiling is 30 steps per process, 25 approvers per step.

| Step | Step entry criteria (`approvalStep.entryCriteria`) | Approver (`assignedApprover.approver.type` + `name`) | Multiple approvers (`whenMultipleApprovers`) | If criteria not met (`ifCriteriaNotMet`) | On rejection (`rejectBehavior.type`) | Delegation (`allowDelegate`) | Actions on approve / reject |
|---|---|---|---|---|---|---|---|
| 1 | [criteria, or none — every record that entered reaches step 1] | [`userHierarchyField` (no `name`; requires `nextAutomatedApprover`), `user` + username, `queue` + queue name, `relatedUserField` + lookup field name, or `adhoc` (no `name`)] | [`Unanimous` (default) or `FirstResponse`] | [`ApproveRecord`, `GotoNextStep`, or `RejectRecord`] | n/a on step 1 — final rejection actions govern | [`true` / `false`] | [`approvalActions` / `rejectionActions` references] |
| 2 | [criteria that make this step conditional] | [as above] | [`Unanimous` / `FirstResponse`] | [`ApproveRecord` or `GotoNextStep`] | [`RejectRequest` or `BackToPrevious`] | [`true` / `false`] | [references] |
| 3 | [delete this row if unused] | [as above] | [`Unanimous` / `FirstResponse`] | [`ApproveRecord` or `GotoNextStep`] | [`RejectRequest` or `BackToPrevious`] | [`true` / `false`] | [references] |

Hierarchy routing, required if any step uses `userHierarchyField`:

| Property | XML element | Answer |
|---|---|---|
| Hierarchy field | `nextAutomatedApprover.userHierarchyField` | [`Manager`, or a custom user hierarchy field] |
| First step reads that field on | `nextAutomatedApprover.useApproverFieldOfRecordOwner` | [`true` = the record owner's user record; `false` = the submitter's. Later steps always read the previous approver's record] |
| What happens when the field is empty | — | [the validation rule or fallback queue; there is no built-in fallback] |

## Submission, Outcome and Recall Actions

Every entry here is a `WorkflowActionReference` — a `name` plus a `type` of `Alert`, `FieldUpdate`, `Task`, or `OutboundMessage` — whose definition lives in `workflows/<Object>.workflow-meta.xml`. Deploy those first.

| Event | XML element | Actions |
|---|---|---|
| Initial submission | `initialSubmissionActions` | [e.g. FieldUpdate `Set_Approval_Status_Pending`; note the record locks regardless of any action] |
| Approved at a step | `approvalStep.approvalActions` | [per-step stamps or notifications, or none] |
| Rejected at a step | `approvalStep.rejectionActions` | [per-step notifications] |
| Final approval | `finalApprovalActions` | [FieldUpdate that records the outcome, Alert to the submitter] |
| Final rejection | `finalRejectionActions` | [FieldUpdate resetting status, Alert to the submitter] |
| Recall | `recallActions` | [what returns the record to its pre-submission state — nothing is reverted automatically] |
| Anything that must run in Flow | — | [the FieldUpdate above, plus a record-triggered Flow on that field; `FlowAction` in the action type enum is the closed flow-trigger pilot] |

Action inventory to deploy before the process:

| Action name | Type | Exists in target org? |
|---|---|---|
| [e.g. Set_Approval_Status_Pending] | [FieldUpdate] | [yes / to be deployed] |
| [e.g. Notify_Submitter_Approved] | [Alert] | [yes / to be deployed] |
| [email template `Folder/Name`] | [EmailTemplate, Classic] | [yes / to be deployed] |

## Operational Checks

- [ ] Irreversible Decisions block signed off before any activation, in any org
- [ ] Every approver source has a documented empty-value path (validation rule or fallback queue)
- [ ] `recordEditability` chosen deliberately, and tested with a real approver who is not a System Administrator
- [ ] Both final-lock booleans chosen deliberately, not inherited from a copied file
- [ ] Every referenced field update, alert, task, and outbound message exists in `workflows/<Object>.workflow-meta.xml`
- [ ] Every referenced email template exists in the target org and is a Classic template
- [ ] Org-wide email address used by any alert is verified in the target org
- [ ] Checker clean: `python3 skills/admin/approval-processes/scripts/check_approval_design.py --manifest-dir force-app/main/default`
- [ ] Process order set by hand in the target org after deploy, and recorded above
- [ ] One record submitted end to end as a real submitter, verified with the `ProcessInstance` / `ProcessInstanceWorkitem` queries in `references/metadata-examples.md`
- [ ] Pending-approval SLA agreed, with the `ElapsedTimeInDays` report that monitors it
- [ ] "Wrong tool?" check completed against `standards/decision-trees/automation-selection.md` — parallel reviewers, SLA timers, or cross-object stages route to `flow/orchestration-flows` instead
