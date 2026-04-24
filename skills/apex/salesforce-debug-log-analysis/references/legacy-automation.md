# Legacy Automation: Workflow Rules, Process Builder, Approval Processes, Assignment Rules

Salesforce has deprecated or frozen most of these but they still run in many orgs. This reference covers how each appears in the log and what it means.

## Workflow Rules (frozen)

Deprecated in late 2022 (existing rules keep working, no new ones can be created). Still prevalent in legacy orgs.

### Event sequence

Workflow rules fire after triggers in the standard order of execution:
1. System validation rules
2. Before-save triggers
3. Custom validation rules
4. Save (but not committed)
5. **After-save triggers**
6. Assignment rules
7. Auto-response rules
8. **Workflow rules**
9. Escalation rules (Cases only)
10. Entitlement rules (Cases only)
11. Roll-up summary fields
12. Parent record recalculation
13. Sharing rule evaluation
14. Commit

If a workflow rule has a field update, the record is **saved again** and triggers fire a second time (with `Trigger.isExecuting` set and `isRecursive` rules in play).

### Log signatures

| Event | Meaning |
|---|---|
| `WF_RULE_EVAL_BEGIN` | Workflow rule evaluation begins |
| `WF_RULE_EVAL_VALUE` | Formula evaluation intermediate |
| `WF_CRITERIA_BEGIN` | Rule criteria evaluation begins |
| `WF_CRITERIA_END` | Criteria end |
| `WF_RULE_ENTRY_CRITERIA` | Entry criteria formula |
| `WF_RULE_EVAL_END` | Evaluation complete |
| `WF_ACTION` | Action executed (field update, task, email, outbound msg) |
| `WF_FIELD_UPDATE` | Field update action |
| `WF_TASK` | Task created |
| `WF_EMAIL_ALERT` | Email alert fired |
| `WF_OUTBOUND_MSG` | Outbound message queued |
| `WF_TIME_TRIGGER` | Time-based action fired |
| `WF_NEXT_APPROVER` | Approval process next approver |
| `WF_ESCALATION_RULE` | Case escalation rule fired |
| `WF_SOFT_REJECT` | Approval soft reject |

### Diagnostic approach

```bash
# All workflow rules that fired
grep "WF_RULE_EVAL_BEGIN\|WF_CRITERIA_BEGIN" log.log

# All workflow field updates
grep "WF_FIELD_UPDATE" log.log | awk -F'|' '{print $3, $4}'

# Time-based workflow (useful for debugging delayed actions)
grep "WF_TIME_TRIGGER" log.log
```

Workflow field updates that update the same record fire triggers again. Watch for cascade effects.

## Process Builder (frozen)

Deprecated in late 2022. Still runs in orgs with legacy processes.

Under the hood, Process Builder compiles to Flow. In newer logs, processes appear as flow interviews with "PB_" or similar prefix. In older logs, they have their own events.

### Log signatures

Process Builder appears as a flow with naming convention `<Object>_PB_*` or a label starting with "PB" or containing "Process".

```bash
grep "FLOW_START_INTERVIEW_BEGIN" log.log | grep -iE "pb|process"
```

### Gotchas

- Process Builder evaluates all criteria in order. If you have 10 criteria blocks, all 10 evaluate (even if earlier ones match).
- Immediate actions fire in the Process Builder transaction. Scheduled actions fire in a separate transaction, at the scheduled time.
- Multiple processes on the same object fire in an unspecified order.
- Common performance pitfall: a Process Builder that does SOQL or DML for each record in a bulk DML. Not auto-bulkified as well as Flow.

## Approval Processes

### Event sequence

1. User clicks Submit for Approval.
2. Entry criteria evaluated.
3. Initial submission actions fire (field updates, tasks, emails).
4. First approval step evaluates its criteria.
5. Approver assigned.
6. Record locked (`Approval.isLocked`).
7. On approval: next step or final approval actions.
8. On rejection: rejection actions.
9. On recall: recall actions.

### Log signatures

| Event | Meaning |
|---|---|
| `WF_APPROVAL` | Approval action |
| `WF_APPROVAL_SUBMIT` | Submit for approval |
| `WF_APPROVAL_SUBMITTER` | Submitter identified |
| `WF_ASSIGNED_APPROVER` | Approver assigned |
| `WF_PROCESS_NODE` | Approval process step |

### Common issues

- Records with approval in progress cannot be edited except by specific approvers (`ENTITY_IS_LOCKED`).
- Parallel approvals: multiple approvers must all approve. Log shows each approver.
- Auto-approval / auto-rejection based on formula.
- Delegated approver: the log shows both delegated and original approver.

## Assignment Rules

Lead and Case assignment rules fire on create (or configured to fire on update).

### Log signatures

```
CODE_UNIT_STARTED|[AssignmentRule]|<rule-name>
```

### Gotchas

- Assignment Rules fire after triggers but before workflow rules.
- Active assignment rule can differ by user. Each user's profile or permission set determines the rule.
- Setting `AssignmentRuleHeader.useDefaultRule = true` in Apex invokes the default rule during DML.
- Assignment Rules respect queue-based assignment, including round-robin and skill-based (Omni-Channel).

## Auto-Response Rules

Fire on Case and Lead create when "Assign using active auto-response rule" is checked.

### Log signatures

```
CODE_UNIT_STARTED|[AutoResponseRule]|<rule-name>
WF_EMAIL_ALERT|...
```

## Escalation Rules (Cases only)

Time-based rules for escalating Cases.

### Log signatures

```
WF_ESCALATION_RULE
```

Shows in the log only when the rule fires, which may be hours after the Case was created (time-based).

## Entitlement Rules (Cases only)

SLA tracking for support.

### Log signatures

```
ENTITLEMENT_*
MILESTONE_*
```

Milestones can fire triggers on `Case_Milestone` when completed or violated.

## Time-based actions (general)

Both workflow rules and Process Builder can have time-based actions. These sit in a queue (Setup > Monitoring > Time-Based Workflow) until their trigger time.

### Log signatures

When a time-based action fires, it appears in a separate transaction/log:
- Running user: the user who first created the record (for workflows) or the user at time of evaluation (for PB).
- `WF_TIME_TRIGGER` event.

### Gotchas

- Time-based actions evaluate entry criteria when they fire. If the record no longer meets criteria, the action is canceled (and logged).
- Records with pending time-based actions cannot be undeleted cleanly; the queue may have stale entries.
- Reschedule: changing the field that drives the time calculation reschedules the action.

## Multi-automation order conflicts

When a single DML triggers:
1. Triggers (before, after)
2. Validation Rules
3. Duplicate Rules
4. Before-save flows
5. After-save flows
6. Process Builder (compiled to flow)
7. Workflow Rules
8. Workflow field updates (may re-trigger #1)
9. Escalation Rules
10. Entitlement Rules
11. Assignment Rules

...the record can be modified many times before the final commit. Each modification can cascade.

Common flip-flop pattern:
- After-save flow sets Field__c = "A"
- Workflow field update sets Field__c = "B"
- This re-runs the trigger, which runs the after-save flow again
- Flow sets Field__c = "A" again
- Workflow field update has already fired once per save, so it does not fire again
- Result: Field__c = "A" at commit, but intermediate states show the flip-flop

Diagnostic: grep `DML_BEGIN` with `Op:Update` and the same record ID. Each occurrence is a save.

## Migration context

Salesforce is migrating everything to Flow:
- Workflow Rules → Record-Triggered Flow
- Process Builder → Record-Triggered Flow
- Approval Processes → Orchestrator (still in progress)

In debugging modern orgs, you typically find a mix:
- Legacy WF rules still firing for old logic.
- Legacy PB processes partially migrated to flow.
- New automations in Record-Triggered Flow.

This mix is the biggest source of confusion in mature orgs. Same object might have 3 WF rules, 2 PB processes, 5 flows, and 2 trigger handlers, all touching the same fields.

## Migration diagnostic

Count automations per object:
```bash
# Workflow rules
grep "WF_RULE_EVAL_BEGIN" log.log | awk -F'|' '{print $3}' | sort -u

# Process Builder (via flow)
grep "FLOW_START_INTERVIEW_BEGIN" log.log | awk -F'|' '{print $3}' | grep -iE "pb|process" | sort -u

# Flows
grep "FLOW_START_INTERVIEW_BEGIN" log.log | awk -F'|' '{print $3}' | sort -u

# Triggers
grep "CODE_UNIT_STARTED.*trigger" log.log | awk -F'|' '{print $3}' | sort -u
```

If an object has 5+ automations, it is a strong candidate for consolidation. Each adds risk and debugging complexity.

## Recommendations for legacy automation cleanup

1. Inventory: find every WF rule and PB process per object.
2. Identify what they do (field updates, tasks, emails).
3. Decide: migrate to Flow or deprecate.
4. Test in sandbox thoroughly; order of execution matters.
5. Flag any rule that does a field update; that is the highest-risk migration.
6. For recursion-sensitive code, ensure Flow-based replacements respect the same recursion guards.
7. Update documentation; legacy automation is often undocumented.
