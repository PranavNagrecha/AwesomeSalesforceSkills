# Well-Architected Mapping: Approval Processes

## Pillars Addressed

### Reliability

Approval design controls whether business-critical decisions route consistently.

- Tight entry criteria prevent accidental submissions.
- Explicit approver sourcing reduces runtime routing failures.

### User Experience

Submitters and approvers need a process that is understandable and predictable.

- Locking rules shape whether pending records feel safe or unusable.
- Clear email and status changes reduce approval confusion and support noise.

### Operational Excellence

Approval sprawl becomes an admin burden quickly.

- Reviewable step design and routing ownership keep approval logic maintainable.
- Standard-vs-custom decision discipline prevents fragile workflow bloat.

## Pillars Not Addressed

- **Security** - approval is about decision routing, not record access architecture.
- **Performance** - approval volume is usually an operational concern, not a compute-bound pattern.

## Pillar Evidence

| Claim in this skill | Pillar | Grounded in |
|---|---|---|
| Step order and reject behaviour must be settled before the first activation | Reliability | Metadata API guide, `ApprovalProcess.active` and the `ApprovalStep` note: no adding, deleting, or reordering of steps and no change to reject or skip behaviour after activation, even if the process is inactive |
| Process order is a deploy step, not a setting | Operational Excellence | Metadata API guide, `ApprovalProcess` note: the metadata does not include the order of active approval processes, and reordering in the destination org is sometimes required |
| A submission enters exactly one process | Reliability | Apex Reference, `ProcessSubmitRequest.setProcessDefinitionNameOrId` — with a null value, entry criteria for all processes applicable to the submitter are evaluated in setup process order and the first that satisfies is submitted |
| Locking is a platform behaviour, not a toggle | User Experience | Object Reference, `ProcessDefinition.LockType` — a record in an approval process is always locked and only an administrator can edit it, though the assigned approver can also be allowed to |
| `AdminOrCurrentApprover` still depends on the sharing model | User Experience | Metadata API guide, `recordEditability` — the assigned approver must have edit access through user permissions and org-wide sharing defaults |
| Approval actions are workflow actions in a separate file | Operational Excellence | Metadata API guide, `ApprovalAction` → `WorkflowActionReference` (`Alert`, `FieldUpdate`, `Task`, `OutboundMessage`, `FlowAction`) and the `Workflow` file-suffix section |
| Approver-source failure is a runtime failure, not a design-time one | Reliability | Metadata API guide, `NextAutomatedApprover` and `Approver.type` — the dependency between `userHierarchyField` steps and the process-level `nextAutomatedApprover` |

## Official Sources Used

- Metadata API Developer Guide (v62 PDF), `ApprovalProcess` section — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (every element, enum, and limit in `SKILL.md` § Deployable Metadata Shape and in `references/metadata-examples.md`: `recordEditability`, `ifCriteriaNotMet`, `rejectBehavior`, `whenMultipleApprovers`, `Approver.type`, `ProcessSubmitterType`, the 30-step and 25-approver ceilings, the activation freeze, the process-order deploy caveat, and the wildcard restriction)
- Metadata API Developer Guide (v62 PDF), `Workflow` section — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (`WorkflowActionReference` types, `WorkflowAlert` and `WorkflowFieldUpdate` required fields, `senderType`, `reevaluateOnChange`, the closed `FlowAction` pilot — the workflow file in `references/metadata-examples.md` and the "actions live in a different file" gotcha)
- Object Reference (v62 PDF), `ProcessDefinition` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (`LockType`, `State`, `TableEnumOrId`, `Type` — the "the lock is not optional" gotcha and the verification SOQL)
- Object Reference (v62 PDF), `ProcessInstance`, `ProcessInstanceWorkitem`, and `ProcessInstanceHistory` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (the `Status` picklist values, `ElapsedTimeInDays`, the `Steps` and `Workitems` child relationships, and the polymorphic `ActorId` / `OriginalActorId` — all of the verification queries in `references/metadata-examples.md`)
- Apex Reference Guide (v62), `Approval` class and `ProcessSubmitRequest` — the `setProcessDefinitionNameOrId` / `setSkipEntryCriteria` evaluation rules behind the "one process per submission" gotcha, and the statement that record locks and unlocks are DML, blocked before a callout, and rolled back with the transaction
- Apex Developer Guide (v62 PDF), "Triggers and Order of Execution" → *Operations That Don't Invoke Triggers* — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf (mass approval request transfers do not fire triggers — the last gotcha)
- Apex Developer Guide (v62 PDF), "Approval Processing" — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf (the submit snippet's shape, and the note that `Approval.process` counts against DML limits)
- `standards/decision-trees/automation-selection.md`, cheat-sheet row "Approval chain" — the routing between an Approval Process, a Flow with branching, and Flow Orchestration
- Salesforce Well-Architected Overview — governance and reliability framing for approval design
- Salesforce Winter '26 Release Notes, Salesforce Flow → Flow Approval Processes — the Approval Designer permission pair and the Submit for Activation review flow (`references/llm-anti-patterns.md` § 7)
