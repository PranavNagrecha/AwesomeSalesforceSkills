# Gotchas: Approval Processes

---

## Record Locking Breaks Legitimate Work

**What happens:** A submitter sends a record for approval, then another team needs to correct a field before the approver responds. The record is locked, the correction cannot be made, and business users blame Salesforce.

**When it bites you:** Revenue approvals, case escalations, and any process where business users still work the record while waiting.

**How to avoid it:** Decide up front whether the record should lock, who needs edit access while pending, and whether the approval should happen later in the lifecycle.

**Example:**
```text
Bad pattern: Submit for approval at draft stage, then expect sales ops to keep editing the record.
Better pattern: Submit only after required fields are final.
```

---

## Blank Approver Fields Fail at Runtime

**What happens:** Approval routing depends on a lookup such as `Director__c`. One record has that field blank. Submission fails even though the process design itself looks valid.

**When it bites you:** User-lookup routing, manager-based routing after org changes, and record-specific approver fields.

**How to avoid it:** Validate approver fields before submission and create a fallback owner or escalation path.

**Example:**
```text
If `Legal_Approver__c` is blank, block submission with a validation message before the user reaches the approval engine.
```

---

## Recall Does Not Undo Every Side Effect

**What happens:** A record is submitted, field updates and email alerts fire, then the submitter recalls it. The business assumes everything returned to pre-submission state. It did not.

**When it bites you:** Processes with submission actions that notify customers, create tasks, or stamp approval status fields.

**How to avoid it:** Document which actions happen on submit, approve, reject, and recall. If recall must reverse state, build that explicitly.

**Example:**
```text
Submission action: set Status = Pending Approval
Recall expectation: Status returns to Draft
Reality: only true if you build recall handling for it
```

---

## Approval Processes Hide Organizational Drift

**What happens:** A process routed cleanly when managers and directors were stable. Six months later, a reorg leaves stale manager relationships and inactive approvers, and approvals start stalling.

**When it bites you:** Manager-based approvals and orgs with frequent user moves.

**How to avoid it:** Audit approver routing after reorgs and monitor pending approvals older than the expected SLA.

**Example:**
```text
Quarterly control: report all pending approvals older than 3 business days and inspect approver assignments.
```

---

## Activation Freezes the Step Structure Permanently

**What happens:** A process is activated to test it, someone spots that step 2 should come before step 3, and the reorder button is gone. Deactivating the process does not bring it back. The Metadata API guide says it twice — once on `ApprovalProcess.active` and once on `ApprovalStep` — "After an approval process is activated, you can't add, delete, or change the order of the steps or change its reject or skip behavior, even if the process is inactive." The only route to a different step order is a new process.

**When it bites you:** The first sandbox activation, and any "let's just activate it to see" moment. Also on inherited processes where a requirement changed and the org now carries `Discount_Approval`, `Discount_Approval_v2`, and `Discount_Approval_FINAL`, all matching similar records.

**How to avoid it:** Settle step order, `rejectBehavior`, and `ifCriteriaNotMet` on paper (`templates/approval-design-template.md`) before the first activation, in any org. Deploy with `<active>false</active>` and activate once. When a change to step structure is genuinely needed, plan for a replacement process plus deactivation of the old one, and remember that pending items on the old process still have to be resolved.

**Example:**
```text
Changeable after activation: entry criteria, approvers, actions, allowRecall,
                             recordEditability, approvalPageFields
Frozen after activation:     step count, step order, rejectBehavior,
                             ifCriteriaNotMet
```

---

## A Record Enters Exactly One Process, Chosen by an Order the Metadata Does Not Carry

**What happens:** Two active approval processes exist on Opportunity. A record matches both. It enters exactly one of them — whichever comes first in the org's process order. The Apex Reference describes the evaluation for `setProcessDefinitionNameOrId(null)`: submission "evaluates entry criteria for all processes applicable to the submitter. The order of evaluation is based on the process order of the setup" and "the one that satisfies is picked and submitted." That order is not in the XML. The Metadata API guide is explicit: "The metadata doesn't include the order of active approval processes. Sometimes you have to reorder the approval processes in the destination org after deployment."

**When it bites you:** Every deploy that adds a process to an object that already has one. It looks like a successful deploy and behaves as a silent routing change in production, because a broader process that happens to sort first will swallow submissions the narrower one was written for.

**When it bites you differently:** An `allowedSubmitters` mismatch produces the same symptom with a different cause — only processes *applicable to the submitter* are evaluated, so a record can skip a process entirely because the person submitting is not in its submitter list.

**How to avoid it:** Treat process order as a deploy step, not a setting. After every deploy that adds or activates a process, open Setup → Process Automation → Approval Processes for that object and confirm the order. For auto-submission from Apex or Flow, name the process with `setProcessDefinitionNameOrId` so order cannot silently reroute you. Keep entry criteria mutually exclusive where you can, so order stops mattering.

**Example:**
```text
Order 1: Any_Opportunity_Review   entryCriteria: (none)
Order 2: Discount_Approval        entryCriteria: Discount_Percent__c > 20

A 45% discount enters Any_Opportunity_Review. Discount_Approval never runs.
The XML for both files is correct. The bug is the order.
```

---

## `userHierarchyField` Approvers Are Silently Illegal Without `nextAutomatedApprover`

**What happens:** A step is configured with approver type `userHierarchyField` to route to the manager, and the process is rejected or the step cannot be saved, because the process-level `nextAutomatedApprover` element is missing. The guide states the dependency from both ends: on the approver type, "The user hierarchy field must be defined in the `nextAutomatedApprovers` for the approval process"; on the process field, "If you exclude this field, then no approval step can use a user hierarchy field to automatically assign the approver."

**When it bites you:** Hand-written XML and LLM-generated XML, both of which tend to produce a plausible-looking `<approver><type>userHierarchyField</type></approver>` and stop there. Also when someone deletes `nextAutomatedApprover` from a process because "we're not using automated approvers", not realising every hierarchy-routed step depends on it.

**How to avoid it:** Whenever any step uses `userHierarchyField`, declare `nextAutomatedApprover` with both `userHierarchyField` and `useApproverFieldOfRecordOwner`. Decide the second one deliberately: `true` means the first executed step reads the hierarchy field on the record *owner's* user record; `false` means it reads the *submitter's*. Every later step reads the field on the previous step's approver, which is what produces a chain up the hierarchy.

**Example:**
```text
Submitted by an ops user on behalf of a rep:
  useApproverFieldOfRecordOwner = true   -> routes to the rep's manager  (intended)
  useApproverFieldOfRecordOwner = false  -> routes to the ops user's manager
```

---

## Approval Actions Are Workflow Actions, and They Live in a Different File

**What happens:** The approval process deploys as a self-contained-looking XML file and fails with an unresolved reference, or deploys and then does nothing on approval. The action elements are only `WorkflowActionReference` pointers — a `name` and a `type` from `Alert`, `FieldUpdate`, `Task`, `OutboundMessage`, `FlowAction`. The definitions live in `workflows/<Object>.workflow-meta.xml`, and the email template the `emailTemplate` element and every alert point at is a third metadata type again.

**When it bites you:** First deploy to a new org or a refreshed sandbox, where the workflow actions and Classic templates do not exist yet. Also whenever someone renames a field update: the approval file still carries the old `<name>` string, and the match is exact.

**How to avoid it:** Deploy email templates and the object's `Workflow` file before the `ApprovalProcess`, in that order, and include all three types in `package.xml` (`references/metadata-examples.md`). Note that `FlowAction` in that enum is the closed flow-trigger pilot, so the supported way to run a Flow on approval is to have the approval fire a `FieldUpdate` and put a record-triggered Flow on that field. Also note `emailTemplate` should be a Classic template — the guide records that Lightning email templates are not packageable.

**Example:**
```text
approvalProcesses/Opportunity.Discount_Approval.approvalProcess-meta.xml
  <finalApprovalActions><action>
      <name>Set_Discount_Approved_True</name>   <- just a string
      <type>FieldUpdate</type>
  </action></finalApprovalActions>

workflows/Opportunity.workflow-meta.xml
  <fieldUpdates><fullName>Set_Discount_Approved_True</fullName> ... <- the definition
```

---

## The Lock Is Not Optional, and `finalApprovalRecordLock` Can Make It Permanent

**What happens:** A team assumes the record-editability setting decides *whether* the record locks. It does not. The Object Reference says it plainly for `ProcessDefinition.LockType`: "When a record is in the approval process, it's always locked, and only an administrator can edit it. However, the currently assigned approver can also be allowed to edit the record." The setting that varies is `recordEditability` — `AdminOnly` or `AdminOrCurrentApprover` — and the approver branch additionally requires that the approver already has edit access "through user permissions and the organization-wide sharing defaults for the given object", so a read-only approver still cannot edit. Separately, `finalApprovalRecordLock` and `finalRejectionRecordLock` (both default `false`) decide whether the lock survives the outcome.

**When it bites you:** `finalApprovalRecordLock` set to `true` for auditability, then a rep needs to correct a close date on an approved deal and nobody but an admin can. Also on the approver side, where `AdminOrCurrentApprover` is chosen and the approvers still cannot edit because OWD is Private and they have no share.

**How to avoid it:** Choose `recordEditability` explicitly rather than accepting a default, and check the approver's actual record access — not just the process setting — before relying on `AdminOrCurrentApprover`. Leave both final-lock booleans `false` unless the business has asked for a permanently frozen record. Where code needs to intervene, `Approval.lock` / `unlock` / `isLocked` exist, but they use the same editability settings as the process, count as DML, are blocked before a callout, and roll back with the transaction (`admin/approval-process-apex-patterns`).

**Example:**
```text
recordEditability = AdminOrCurrentApprover, OWD Private, approver has no share
  -> approver opens the approval page, can approve, cannot fix the typo
     that is the reason they would have rejected it
```

---

## Mass Approval Request Transfers Do Not Fire Triggers

**What happens:** An admin reassigns a batch of pending approval requests to a new approver after a reorg, and every trigger, and everything downstream of those triggers, stays silent. The Apex Developer Guide lists "Mass approval request transfers" among the operations that do not invoke triggers, alongside mass campaign status changes and mass email actions.

**When it bites you:** Reorg cleanups and offboarding, exactly when an org is most likely to have automation watching approver changes to keep a shadow "Current_Approver__c" field or an audit table in sync. That field silently goes stale for the whole transferred batch.

**How to avoid it:** Do not build reporting or automation that depends on a trigger firing when approval requests are transferred. Read the live state instead: `ProcessInstanceWorkitem.ActorId` (with `OriginalActorId` for who it was first assigned to) is the source of truth, and both are polymorphic across `User` and `Group`. If a stamped field is genuinely needed, refresh it on a schedule from that query rather than from a trigger.

**Example:**
```sql
-- The reliable read after a mass transfer, in place of a trigger
SELECT Id, ActorId, OriginalActorId, ProcessInstance.TargetObjectId
FROM ProcessInstanceWorkitem
WHERE ProcessInstance.Status = 'Pending'
```

---

## Approval Does Not Re-Arm Itself When the Governed Field Changes Later

**What happens:** Approval does not re-arm itself. A field update in `finalApprovalActions` stamps a status field `Approved` once, and that value stays put. Edit the governed field afterwards (raise `Discount__c` from 25% to 40%) and the status still reads `Approved`. So a validation rule or component that trusts the status lets the second, unapproved value through. The Metadata API defines `finalApprovalActions` as the workflow actions "to execute when all required approvals have been given for a record" (api_meta 264 L25191-25192), a one-time event. `recallActions` covers only "a pending approval request" being withdrawn (L25227-25228), so recall can't reopen a finished approval. `finalApprovalRecordLock` defaults to `false` (L25194-25195), so by default the record unlocks on approval and the governed field can be edited again. UNVERIFIED (2026-10-20): the corpus lists the type's elements but never says outright that nothing re-evaluates `entryCriteria` or reverses `finalApprovalActions` after approval. The type has no element for that; the behaviour was not observed in an org.

**When it bites you:** Any gate of the form "X above a threshold needs approval" where the gate reads a stamped status, not the approved value. That covers a discount cap that blocks Closed Won until `Approval_Status__c = Approved`, and a submit button disabled while the status is `Approved`. The first edit is governed and every later edit is not.

**How to avoid it:** Reset the status, or block the change, whenever the governed field moves after approval:
- **Reset (preferred when a re-submission path must stay open):** a before-save record-triggered flow on update that clears the status, or sets it to `Pending`/blank, when the governed field changed and the prior status was `Approved`. Before-save flows run at step 3 of the save order, before custom validation rules at step 5 (apexdev 264 L15643-15645), so the threshold rule sees the cleared status in the same save. A before-save assignment needs no Update element (`flow/record-triggered-flow-patterns/references/gotchas.md`, "A Before-Save Assignment Persists With No Update Element At All"). The prior value comes from `$Record__Prior` (same file, "`$Record__Prior` Only Helps If The Logic Actually Uses It"). Condition the reset on the governed field changing. The approval's own `Approved` field update then can't trip it, because that save does not change the governed field.
- **Block:** a validation rule erroring on `ISCHANGED(Discount__c)` while `ISPICKVAL(Approval_Status__c, "Approved")` (guard `NOT(ISNEW())` as in `admin/validation-rules/references/gotchas.md`, "PRIORVALUE Does Not Work on Insert"). This holds the approved value as a ceiling, but it leaves the rep no way to re-submit if the status field is read-only to them and the submit control is disabled while `Approved`. Name who clears the status.
- **Lock:** `finalApprovalRecordLock = true` keeps the record locked after approval (L25194-25195). While a record is pending, only Modify All Data or the object's Modify All Records holders (plus, under `AdminOrCurrentApprover`, the current approver) can edit it (L25230-25247). UNVERIFIED (2026-10-20): the corpus describes `recordEditability` for records *pending* approval. It does not say the same editability applies to the post-approval lock, or that the lock alone stops the record owner from editing the governed field. Test it in a sandbox before relying on the lock instead of a reset.

**Example:**
```text
Discount__c 25% -> submitted -> Approved (field update stamps Approval_Status__c = Approved, record unlocks)
Rep edits Discount__c 25% -> 40%           Approval_Status__c still Approved
VR "Closed Won needs Approved above 20%"   passes -> 40% closes with a 25% approval
Fix: before-save flow, ISCHANGED(Discount__c) AND prior status Approved -> clear status; VR now blocks; rep re-submits
```
