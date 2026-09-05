# Approval Process Apex — Pre-Build Worksheet

Fill this in before writing any Apex. Workflow step 1 in `SKILL.md`.
Every row maps to a runtime failure that will otherwise be discovered
in production, one row at a time, with `allOrNone = false` quietly
absorbing it.

## Scope

| Field | Value |
|---|---|
| Skill | `approval-process-apex-patterns` |
| Object | |
| Approval process developer name | |
| Request summary | |
| Pattern (A submit / B action / C monitor / D recall) | |

## The process definition, as deployed

Run this first and paste the result:

```sql
SELECT Id, DeveloperName, Name, State, TableEnumOrId, LockType, Type
FROM ProcessDefinition
WHERE TableEnumOrId = '<Object>' AND State = 'Active'
```

| Question | Answer | Consequence if wrong |
|---|---|---|
| Is the process `State = 'Active'`? | | A named submission to an inactive process fails |
| How many active processes on this object? | | More than one, and a null `processDefinitionNameOrId` routes by org process order |
| Who is in `allowedSubmitters` (types + names)? | | `setSubmitterId` fails for any user outside the list |
| Is `allowRecall` true? | | With false, only administrators can recall — and `'Removed'` is admin-only from Apex regardless |
| `recordEditability` value | | `AdminOnly` locks the record away from the approver while pending |
| Steps, and each step's `assignedApprover` type | | `adhoc` steps need `setNextApproverIds` (exactly one Id) |
| Any step with `whenMultipleApprovers = Unanimous`? | | One rejection flips other approvers' `StepStatus` to `NoResponse` |
| Does the process have `entryCriteria`? | | Decides whether `setSkipEntryCriteria` is meaningful, and whether below-threshold rows will fail |

## Transaction budget

| Question | Answer |
|---|---|
| Rows per invocation | |
| Chunk size (convention, not a governor) | |
| `Approval.process` calls per transaction (1 per chunk) | |
| Other DML in the same transaction | |
| Total DML statements vs the 150 limit | |
| Total records processed vs the 10,000 limit | |
| Sync, Queueable, or Batch Apex | |

## Error-row policy

| Question | Answer |
|---|---|
| `allOrNone` value, and why | |
| Where failed rows go (log object / retry queue / alert) | |
| Who is paged when the failure count crosses a threshold | |
| Is a partial batch coherent for this business process? | |

## Decisions and deviations

Record anything that departs from the patterns in `SKILL.md`, and why.
Deviations that need a written reason: `setSkipEntryCriteria(true)`,
auto-approval via `setAction('Approve')`, submitting as a service user
instead of the record owner, and any recall path that assumes admin
context.

| Deviation | Reason | Reviewed by |
|---|---|---|

## Sign-off checklist

Copy the `## Review Checklist` from `SKILL.md` and tick it here, then
attach the checker output:

```bash
python3 skills/admin/approval-process-apex-patterns/scripts/check_approval_process_apex_patterns.py \
    --manifest-dir force-app/main/default
```

| Item | Status |
|---|---|
| Checker score | |
| Findings triaged | |
| Tests written for the three failure modes | |
