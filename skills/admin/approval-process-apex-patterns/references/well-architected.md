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
6. **Bulk submission > 200 in a single call.** Governor limit;
   needs chunking.
7. **Process-instance vs workitem confusion.** Apex calls
   `setWorkitemId(processInstance.Id)` — wrong type, confusing
   error.

## Official Sources Used

- Apex Reference: Approval Class — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Approval.htm
- Apex Reference: Approval.ProcessSubmitRequest — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Approval_ProcessSubmitRequest.htm
- Apex Reference: Approval.ProcessWorkitemRequest — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Approval_ProcessWorkitemRequest.htm
- Object Reference: ProcessInstance / ProcessInstanceWorkitem — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_processinstance.htm
- Approval Process Considerations — https://help.salesforce.com/s/articleView?id=sf.approvals_considerations.htm&type=5
- Sibling skill — `skills/admin/approval-process-design/SKILL.md`
- Sibling skill — `skills/flow/flow-orchestration-patterns/SKILL.md`
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
