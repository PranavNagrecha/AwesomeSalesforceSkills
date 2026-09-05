# Well-Architected Notes — Approval Process Apex Patterns

## Relevant Pillars

- **Reliability** — Bulk submission patterns with `allOrNone =
  false` and per-row error logging are the highest-leverage
  reliability investment. Default true rolls back the whole batch
  on first failure; one bad row blocks everything.
- **Security** — Auto-approval (programmatic `'Approve'` action)
  is a security-sensitive primitive. The audit-trail "approved by"
  reflects the Apex running user, not the configured approver.
  Document explicitly when policy is enforced upstream of the
  platform's approver-assignment.
- **Operational Excellence** — Stuck-approval monitoring (Pattern C)
  surfaces approvals waiting on inactive users / aged > SLA. Without
  it, stuck approvals accumulate invisibly until someone notices the
  process didn't complete.

## Architectural Tradeoffs

- **Apex-driven approval vs Flow Orchestration vs Standard Approval
  Process buttons.** Standard buttons for human-only single-decision
  flows. Flow Orchestration for multi-stage / multi-human / new
  designs. Apex for bulk system-initiated, custom UI, or signals
  from external systems.
- **`allOrNone = true` vs `false`.** True = strict batch
  semantics; useful when partial submission is incoherent (e.g.
  "submit all linked records or none"). False = best-effort with
  per-row reporting; default for bulk system batches.
- **Recall-from-trigger vs admin-action recall.** Trigger-driven
  recall is automatic but requires the editing user to have recall
  permission. Admin-action recall (queue + admin processes) is more
  controlled but slower. Pick by trust model.
- **Auto-approval audit-trail mismatch vs context-switch
  impersonation.** Accepting "approved by Automated Process" with
  documented policy upstream is simpler. Impersonating the
  configured approver is more secure-feeling but requires Modify
  All Data and careful context handling.

## Anti-Patterns

1. **Hardcoded process-definition record IDs.** Brittle across orgs;
   use API names.
2. **Bulk submission with default `allOrNone = true`.** First
   failure rolls back successful submissions.
3. **Default running-user as submitter** in batch contexts.
   Approvals appear submitted by the batch service account, not
   the actual owner.
4. **Recall called from trigger without permission handling.**
   Permission errors fail silently or surface confusingly.
5. **Auto-approval without explicit policy-vs-platform-action
   documentation.** Audit trail and policy diverge silently.
6. **Budgeting bulk submission by chunk size instead of by DML.**
   The binding limits are 150 DML statements and 10,000 records
   processed per transaction; `Approval.process` consumes both. A
   chunk size of 200 is a convention, not a documented governor.
7. **Process-instance vs workitem confusion.** Apex calls
   `setWorkitemId(processInstance.Id)` — wrong type, confusing
   error.
8. **Setting `submitterId` to a record owner without checking
   `allowedSubmitters`.** The Apex Reference requires the submitter
   to be an allowed submitter; owners outside that list fail per row.
9. **Selecting `Actor.IsActive` on `ProcessInstanceWorkitem`.**
   `ActorId` is polymorphic over Group and User; the query needs
   `TYPEOF`, and queue-assigned requests have no user at all.
10. **Leaving `processDefinitionNameOrId` null to "let the platform
    decide".** Routing then depends on org process order, which no
    deployment carries.
11. **Mixing `Approval.lock` / `unlock` with callouts in one
    method.** Both are DML and are blocked before a callout.

## Official Sources Used

- **Apex Reference Guide** (v62 PDF, https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/apex_reference_guide.pdf), *Approval Class* — "Record locks and unlocks are treated as DML. They're blocked before a callout, they count toward your DML limits" (gotcha 12; the locking subsection of SKILL.md § Core Concepts) and the four `process()` overloads with their `allOrNone` semantics (SKILL.md § Bulk submission).
- **Apex Reference Guide**, *ProcessSubmitRequest Class* — "The user must be one of the allowed submitters in the process definition setup" (gotcha 11); "If the process definition name or ID is not specified, this parameter is ignored" for `setSkipEntryCriteria` (gotcha 15); "the order of evaluation is based on the process order of the setup" for a null process name (gotcha 14).
- **Apex Reference Guide**, *ProcessWorkitemRequest Class* and *ProcessRequest Class* — "Valid values are: Approve, Reject, or Removed. Only system administrators can specify Removed" (gotcha 5, the Security pillar note above); `setNextApproverIds` "must be a single-entry list" (gotcha 8).
- **Apex Reference Guide**, *ProcessResult Class* — `getInstanceStatus()` values Approved / Rejected / Removed / Pending and `getNewWorkitemIds()` (examples.md Example 1; the submit-then-approve path in metadata-examples.md).
- **Apex Developer Guide** (v62 PDF, https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf), *Execution Governors and Limits* footnote 2 and *Approval Processing* — `Approval.process` counts against the 150 DML statements and 10,000 records-processed limits (gotcha 7, the Reliability pillar note above); the worked submit-then-approve sample (metadata-examples.md § The Apex service class).
- **Object Reference** (v62 PDF, https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf), *ProcessInstanceWorkitem* / *ProcessInstanceStep* — `ActorId` "Refers To: Group, User" and is Updateable, `ElapsedTimeInDays` is Filter/Sort, and `StepStatus` flips to `NoResponse` for other approvers on a unanimous step (gotchas 13 and 16; the reassign-instead-of-recall option).
- **Object Reference**, *ProcessInstance* and *ProcessDefinition* — the nine-value `Status` picklist, non-nillable `TargetObjectId`, and the `DeveloperName` / `State` / `TableEnumOrId` preflight query (SKILL.md § Before Starting; metadata-examples.md § Verification).
- **Metadata API Developer Guide** (v62 PDF, https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf), *ApprovalProcess* — `allowRecall`, `allowedSubmitters`, `recordEditability`, the 30-step and 25-approver caps, the activation freeze, the entry-criteria overwrite behaviour, and the sample definition the test fixture is shaped from (gotchas 5, 8, 11, 17; metadata-examples.md § The test-fixture approval process).
- **Salesforce App Limits Cheat Sheet** (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf) — the per-transaction DML statement and records-processed rows naming `Approval.process` explicitly (gotcha 7's limits table).
- Approval Process Considerations — https://help.salesforce.com/s/articleView?id=sf.approvals_considerations.htm&type=5 (carried forward from v1.0.0; help.salesforce.com cannot be fetched from this environment, so claims resting on it alone are not re-verified here).
- Remove Pending Approval Requests / Mass Transfer Approval Requests — https://help.salesforce.com/s/articleView?id=sf.data_approval_requests_remove.htm&type=5 (the declarative bulk-cleanup row in SKILL.md § Decision Guidance; same fetch caveat).
- Sibling skill — `skills/admin/approval-processes/SKILL.md` (declarative process design, which this skill deliberately does not duplicate).
- Sibling skill — `skills/flow/flow-orchestration-patterns/SKILL.md` (the Flow-native alternative in the tradeoff above).
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (pillar framing).
