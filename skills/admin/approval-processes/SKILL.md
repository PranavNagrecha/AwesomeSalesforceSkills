---
name: approval-processes
description: "Design, review, or troubleshoot Salesforce Approval Processes. Triggers: 'submit for approval', 'approver', 'record locked', 'recall approval', 'approval step', 'discount approval', 'approvalProcess metadata', 'ProcessInstanceWorkitem', 'recordEditability', 'process order', 'no approver found', 'pending approval'. NOT for submitting or acting on approvals from Apex - use admin/approval-process-apex-patterns. NOT for CPQ Advanced Approvals (SBAA rules and chains) - use admin/cpq-approval-workflows. NOT for multi-stage cross-object orchestration with SLAs - use flow/orchestration-flows."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - User Experience
  - Operational Excellence
tags: ["approval-process", "approvers", "record-locking", "routing", "escalation"]
triggers:
  - "approval is not routing to the right person"
  - "approver not receiving notification email"
  - "record stuck in pending approval"
  - "how do I recall an approval"
  - "approval step skipping or not firing"
  - "multiple approvers assigned incorrectly"
  - "record is locked and nobody can edit it while it is pending approval"
  - "submit for approval fails because no approver was found"
  - "write the approvalProcess metadata xml for a discount approval"
  - "deployed approval process picked the wrong process in production"
  - "query pending approval requests older than our SLA"
  - "cannot reorder approval steps after activating the process"
inputs: ["approval criteria", "approver source", "record lock requirements", "the object and the workflow actions (field updates, email alerts, tasks) the process will fire"]
outputs: ["approval design guidance", "approval risk findings", "approval routing recommendations", "deployable approvalProcess metadata and the matching workflow actions", "verification SOQL over ProcessInstance / ProcessInstanceWorkitem"]
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

You are a Salesforce Admin expert in approval workflow design. Your goal is to build approval paths that are clear to submitters, reliable for approvers, and simple enough to operate without turning every business exception into a broken locked record.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.
Only ask for information not already covered there.

Gather if not available:
- What object is being approved, and what event should trigger submission?
- Who approves: named users, managers, lookup fields, or queues via custom logic?
- Should the record lock during approval, and who still needs edit access?
- Does the process need recall, re-submit, delegation, or mobile/email approval?
- Is this really a standard Approval Process, or is it multi-object workflow that belongs in Flow/custom objects?

## Questions to Ask Before Configuring

Ask these before opening Setup. Each one maps to a behaviour that is irreversible after activation, or to a runtime failure the metadata cannot express.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "How many active approval processes will this object have, and in what order?" | A submission enters exactly one process: entry criteria are evaluated for every process applicable to the submitter, in the org's process order, and the first that matches wins. Process order is not carried in the metadata | The ordered process list, plus a note that order must be re-set by hand in the target org after deploy |
| "Who may submit, and does that include portal or partner users?" | `allowedSubmitters` is required and typed (`owner`, `creator`, `user`, `group`, `role`, `roleSubordinates`, `partnerUser`, `customerPortalUser`, `allInternalUsers`, …). Leaving it at `owner` silently excludes the ops team that actually files these | The `allowedSubmitters` block, and whether an Apex/Flow auto-submit runs as someone not in it |
| "Who edits the record while it is pending — nobody, or the current approver too?" | `recordEditability` is `AdminOnly` or `AdminOrCurrentApprover`; the record is always locked otherwise. The approver route additionally requires that the approver already has edit access through permissions and OWD | The chosen enum, and the named exception process for in-flight corrections |
| "Where does each step's approver come from, and what happens when that source is empty?" | Approver `type` is `adhoc`, `user`, `userHierarchyField`, `relatedUserField`, or `queue`. `userHierarchyField` only works if `nextAutomatedApprover` is declared on the process; a blank hierarchy or lookup field is a runtime submission failure, not a design-time error | The approver type per step and the pre-submission validation rule or fallback queue |
| "When an approver rejects at step 2, does the whole request die or go back to step 1?" | `rejectBehavior` (`RejectRequest` vs `BackToPrevious`) is set per step, is not allowed on the first step, and cannot be changed once the process has been activated — even after deactivating it | The per-step reject behaviour, decided before the first activation |
| "Do steps that do not match their criteria approve, reject, or skip?" | `ifCriteriaNotMet` is `ApproveRecord`, `RejectRecord` (first step only), or `GotoNextStep`. `GotoNextStep` on the first step means a record matching no later step is rejected | The explicit per-step value instead of the accidental default |
| "Which actions fire on submit, approve, reject, and recall — and do those objects exist in the target org?" | Approval actions are workflow action references (`Alert`, `FieldUpdate`, `Task`, `OutboundMessage`), which live in `workflows/<Object>.workflow-meta.xml`, not in the approval file. A referenced alert, template, or field update that is missing fails the deploy | The action inventory and the deploy order: workflow actions and email template first, process second |

What a proper configuration adds over just building it in Setup: the process is reproducible from source, the record-lock and reject-behaviour decisions are made while they are still changeable, every approver source has a documented empty-value path, and the deploy carries its workflow actions and templates with it instead of failing on a missing reference.

## How This Skill Works

### Mode 1: Build from Scratch

Use this for a new approval requirement.

1. Confirm the process deserves approval at all - many "approvals" are really notifications or task routing.
2. Choose the pattern with the matrix below.
3. Define entry criteria tightly so only approval-worthy records can be submitted.
4. Define approver source explicitly and what happens if it is blank.
5. Define submission, approval, rejection, and recall outcomes before building the first step.
6. Test locked-record behavior with real submitter and approver personas, not just as SysAdmin.

### Mode 2: Review Existing

Use this for inherited approval processes or orgs with approval sprawl.

1. Check entry criteria for over-submission or duplicate submission paths.
2. Check whether steps still reflect the real org structure and approver ownership.
3. Check what actions fire on submit, approve, reject, and recall - especially field updates and emails.
4. Check whether record locking blocks legitimate admin or business operations.
5. Check whether the process should be replaced by Flow or a custom approval object because the logic outgrew standard approvals.

### Mode 3: Troubleshoot

Use this when records will not submit, approvers are wrong, or locked records are blocking work.

1. Identify the stage of failure: submission, step routing, approval action, rejection action, or recall.
2. Check entry criteria and approver resolution first - blank approver fields break otherwise valid submissions.
3. Check lock behavior and who actually has edit rights while the record is pending.
4. Check whether submit/approval/rejection actions are colliding with validation rules, flows, or email alerts.
5. If the business wants exception handling that standard Approval Processes cannot model cleanly, stop patching and redesign.

## Approval Pattern Decision Matrix

| Requirement | Use This | Avoid |
|-------------|----------|-------|
| Linear approval on one object with clear submit/approve/reject outcomes | Standard Approval Process | Reinventing it in Flow first |
| Approval depends on dynamic branching across many objects | Flow + custom approval object | Forcing everything into standard Approval Process |
| Need approval history and locked-record behavior out of the box | Standard Approval Process | Manual task-only process |
| Need parallel reviewers, SLA timers, or exception-heavy orchestration | Custom approval model | Pretending standard approval steps will stay maintainable |

Route before you build: `standards/decision-trees/automation-selection.md`, cheat-sheet row **"Approval chain"** — first choice *Approval Process, then Flow post-approval*; second choice *Flow with branching*; never *Apex custom approval*. When the requirement is a multi-stage, cross-object review with per-stage owners and SLAs, the tree sends you out of this skill to `flow/orchestration-flows`.

## Locking and Recall Rules

- **Locking is a feature, not a side effect**: decide who can still edit while pending.
- **Recall is not rollback**: if submission actions sent emails or updated fields, recall does not magically undo them.
- **Approver source must be owned**: manager-based or lookup-field routing breaks when user records are stale.
- **Email and mobile approval should be tested with the real template and device mix**, not assumed.

The lock is not optional. The Object Reference states it directly for `ProcessDefinition.LockType`: when a record is in the approval process it is always locked and only an administrator can edit it, though the currently assigned approver can also be allowed to edit. The only dial you turn is `recordEditability`:

| `recordEditability` | Who can edit a pending record |
|---|---|
| `AdminOnly` | Users with **Modify All Data**, or **Modify All Records** on that object |
| `AdminOrCurrentApprover` | Those two, plus the assigned approver — who must already have edit access through user permissions and the org-wide sharing defaults for the object |

Two more locks are separate booleans, both defaulting to `false`: `finalApprovalRecordLock` keeps the record locked after all approvals are given, and `finalRejectionRecordLock` keeps it locked after final rejection. Setting `finalApprovalRecordLock` to `true` with `recordEditability` at `AdminOnly` means the record is permanently admin-only from the moment it is approved — deliberate for signed contracts, an outage for anything a rep still works.

## Deployable Metadata Shape

The whole process is one file in `approvalProcesses/`, suffix `.approvalProcess`. Everything it *does* lives elsewhere: actions are `WorkflowActionReference` pointers into `workflows/<Object>.workflow-meta.xml`.

| Element | Type / enum | The decision it encodes |
|---|---|---|
| `active` | boolean, **required** | Once activated you can never add, delete, or reorder steps, or change reject or skip behaviour — even after deactivating |
| `allowedSubmitters` | `ApprovalSubmitter[]`, **required** | `type` is `group` / `role` / `user` / `roleSubordinates` / `roleSubordinatesInternal` / `owner` / `creator` / `partnerUser` / `customerPortalUser` / `portalRole` / `portalRoleSubordinates` / `allInternalUsers`; `submitter` is ignored for `owner`, `creator`, `allInternalUsers` |
| `entryCriteria` | `criteriaItems` **or** `formula`, never both | Omit it entirely to let every record enter. `valueField` (field-to-field comparison) is not supported in approval filter criteria |
| `approvalStep[]` | ordered array | Document order **is** execution order. Up to 30 steps per process |
| `assignedApprover.approver.type` | `adhoc` / `user` / `userHierarchyField` / `relatedUserField` / `queue` | `name` is omitted for `adhoc` and `userHierarchyField`; it is a username for `user`, a user-lookup field name for `relatedUserField`, a queue name for `queue`. Up to 25 approvers per step |
| `whenMultipleApprovers` | `Unanimous` (default) / `FirstResponse` | With `Unanimous`, one rejection rejects the step |
| `ifCriteriaNotMet` | `ApproveRecord` / `RejectRecord` / `GotoNextStep` | `RejectRecord` is first-step only; `GotoNextStep` on step 1 rejects a record that matches no later step |
| `rejectBehavior.type` | `RejectRequest` / `BackToPrevious` | Not allowed on the first step — there, final rejection actions decide |
| `nextAutomatedApprover` | `userHierarchyField` + `useApproverFieldOfRecordOwner` | Omit it and **no** step may use `userHierarchyField`. `useApproverFieldOfRecordOwner` picks whether step 1 reads the hierarchy field on the record *owner* or on the *submitter* |
| `initialSubmissionActions` / `approvalActions` / `rejectionActions` / `finalApprovalActions` / `finalRejectionActions` / `recallActions` | `ApprovalAction` → `WorkflowActionReference[]` | `type` is `Alert`, `FieldUpdate`, `Task`, `OutboundMessage`, or `FlowAction`. `FlowAction` is the closed flow-trigger pilot — for new work use a record-triggered Flow keyed off the field update instead |
| `emailTemplate` | `Folder/Developer_Name` | A **Classic** template; the guide notes Lightning email templates are not packageable. Omit for the default template |
| `enableMobileDeviceAccess` | boolean | `true` forbids `adhoc` approvers anywhere in the process |
| `allowRecall` | boolean | `false` means only administrators can recall |
| `approvalPageFields` | `field[]` | Approvers see these on mobile too; keep it to the decision-relevant fields |

Full deployable XML, the matching workflow actions, `package.xml`, the CLI commands, and the verification SOQL are in `references/metadata-examples.md`.

## Recommended Workflow

1. **Route first.** Read `standards/decision-trees/automation-selection.md` (cheat-sheet "Approval chain"). If the answer is parallel reviewers, SLA timers, or cross-object stages, stop and hand off to `flow/orchestration-flows`; if the answer is CPQ quote approvals, hand off to `admin/cpq-approval-workflows`.
2. **Fill in `templates/approval-design-template.md`.** Every row must be answered before any XML is written — the template's Overview, Entry Criteria, Step Design, and Submission/Recall tables are the inputs to the metadata, and its Irreversible Decisions block is the one you cannot revisit after activation.
3. **Inventory the actions.** List every field update, email alert, task, and outbound message the process will reference, and confirm each exists in `workflows/<Object>.workflow-meta.xml` and each email template exists in the target org. Missing references fail the deploy, not the design review.
4. **Write the XML.** Copy the shapes in `references/metadata-examples.md` into `approvalProcesses/<Object>.<Name>.approvalProcess-meta.xml`, keeping `active` at `false` until the target org has the actions.
5. **Lint before deploy.** Run `python3 skills/admin/approval-processes/scripts/check_approval_design.py --manifest-dir force-app/main/default`, which flags an active process with no entry criteria, a step with no `assignedApprover`, a permanently-locked approved record, an `emailTemplate` reference with no matching file in the tree, and two active processes on the same object that both take every record.
6. **Deploy in order, then set process order by hand.** Workflow actions and email templates first, approval process second. The metadata does not carry the order of active processes, so re-order them in the destination org before activating.
7. **Verify with data, not with Setup.** Submit one record as a real submitter (not as System Administrator), then run the `ProcessInstance` / `ProcessInstanceWorkitem` queries in `references/metadata-examples.md` to confirm which process was entered and who holds the work item. Check `references/gotchas.md` before declaring anything fixed.

---

## Salesforce-Specific Gotchas

| Gotcha | Why it bites |
|---|---|
| Pending approval locks the record | If downstream users still need edits, you must plan for that explicitly. |
| Blank approver fields cause submission failure at runtime | Standard approval does not fix bad routing data for you. |
| Recall does not reverse every side effect | Emails, field updates, and related tasks may already exist. |
| Approval Processes age badly when org structure changes | Manager-based routing that worked last year can silently fail after reorgs. |
| Standard Approval Process is not a universal workflow engine | Once you need complex branching, timers, or cross-object state, move to Flow/custom design. |
| Activation freezes the step structure | Steps cannot be added, deleted, or reordered, and reject or skip behaviour cannot be changed, once the process has been activated — deactivating does not release it. |
| A submission enters exactly one process | Entry criteria are evaluated across every process applicable to the submitter, in the org's process order, and the first match wins; the metadata does not carry that order. |
| `userHierarchyField` approvers need `nextAutomatedApprover` | Omit that element on the process and no step is allowed to route by user hierarchy field at all. |

Each of these is worked through with what happens / when / how to avoid in `references/gotchas.md`.

## Proactive Triggers

Surface these WITHOUT being asked:

| Trigger | Action |
|---|---|
| Requirement says "approval" but only needs awareness | Suggest notification or task instead of a locked-record process. |
| Approver comes from a user lookup field with poor data hygiene | Flag as runtime risk immediately. |
| Submitter still needs to edit the record after submission | Force the record-lock conversation before design continues. |
| More than two exception paths or re-approval loops are requested | Reassess whether standard Approval Process is the wrong tool. |
| Approval step sends email without tested template ownership | Flag. Email quality and sender governance become operational issues fast. |

## Output Artifacts

| When you ask for... | You get... |
|---------------------|------------|
| Approval design | Entry criteria, approver source, step flow, and lock/recall decisions |
| Approval review | Routing risks, locking issues, maintainability concerns |
| Submission failure triage | Root-cause path for criteria, approver, lock, or automation conflicts |
| Should we use approval process? | Standard approval vs Flow/custom approval recommendation |
| Deployable metadata | `approvalProcesses/<Object>.<Name>.approvalProcess-meta.xml` plus the `workflows/<Object>.workflow-meta.xml` actions it references and a `package.xml` |
| Verification | `ProcessInstance` / `ProcessInstanceWorkitem` SOQL proving which process was entered, its status, and who holds the pending work item |

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing or reviewing `approvalProcess` XML, the workflow actions it references, `package.xml`, the retrieve/deploy commands, or the verification SOQL |
| `references/gotchas.md` | A process routes to the wrong approver, locks the wrong people out, cannot be edited after activation, or picked the wrong process after a deploy |
| `references/examples.md` | Sizing a requirement: which shapes fit standard approvals and which one is the signal to stop and use Flow |
| `references/llm-anti-patterns.md` | Reviewing AI-generated approval guidance before you act on it |
| `references/well-architected.md` | Justifying the design against the pillars, or chasing the official source behind a claim here |
| `templates/approval-design-template.md` | Capturing the decisions before any XML is written — especially the irreversible ones |
| `scripts/check_approval_design.py` | Linting `approvalProcesses/` in a DX tree before deploying |

---

## Related Skills

- **admin/approval-process-apex-patterns**: Use for `Approval.ProcessSubmitRequest`, `Approval.ProcessWorkitemRequest`, `Approval.lock` / `unlock` / `isLocked`, auto-submission from a trigger or invocable, and bulk approval code. This skill keeps only a ten-line submit snippet.
- **admin/cpq-approval-workflows**: Use for CPQ Advanced Approvals — SBAA approval rules, approval chains, and smart approvals on Quotes. NOT for the standard `ApprovalProcess` metadata type.
- **flow/orchestration-flows**: Use when the requirement is multi-stage, multi-user, cross-object review with per-stage owners; the automation-selection tree routes here once approvals stop being linear on one object.
- **flow/flow-orchestration-patterns**: Use for the stage/step decomposition patterns once orchestration is the chosen tool.
- **admin/email-templates-and-alerts**: Use when approval communications, reminders, and templates are the main design problem — including the Classic template the `emailTemplate` element must point at. NOT for step routing or record locking.
- **admin/flow-for-admins**: Use for the record-triggered Flow that auto-submits, or the post-approval Flow the decision tree pairs with an approval process. NOT for simple single-object approvals.
- **admin/change-management-and-deployment**: Use when deploying approval-process changes that affect production operations or release governance, including the manual process-order step after deploy. NOT for approval design itself.
