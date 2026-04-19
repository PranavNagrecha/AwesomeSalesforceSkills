# Probe: automation-graph-for-sobject

## Purpose

Enumerate **every active piece of automation** on a given SObject so a builder agent can answer "what already fires on this object?" **before** designing new automation. This is the antidote to the most common real-life failure mode: adding a third overlapping record-triggered flow to an object that already has two plus a trigger plus a process builder.

Consumed by `flow-builder` (Step 0 — preflight), `apex-builder` (recursion-risk check), `automation-migration-router` (source discovery).

---

## Arguments

| Arg | Type | Required | Notes |
|---|---|---|---|
| `object` | string | yes | sObject API name, e.g. `Account` |
| `include_inactive` | boolean | no (default `false`) | Also return inactive flows / workflow rules (useful for `/refactor-apex` audit, not for `/build-flow`) |
| `include_managed` | boolean | no (default `false`) | Include managed-package automations (usually read-only; adding a flow doesn't collide, but execution order still matters) |

---

## Queries

Run each query in order. All are Tooling API. For `Flow` and `FlowDefinitionView`, prefer `FlowDefinitionView` — it captures the latest active version without per-flow Metadata retrieval, which is lighter.

### 1. Active Flows and Process Builders on the object

```sql
SELECT DurableId, ApiName, Label, ProcessType, TriggerType, TriggerObjectOrEventLabel,
       IsActive, IsOutOfDate, ActiveVersionId, LatestVersionId, VersionNumber
FROM FlowDefinitionView
WHERE TriggerObjectOrEventLabel = :object
  AND IsActive = true
  AND (include_managed=true OR NamespacePrefix = null)
ORDER BY ProcessType, ApiName
LIMIT 200
```

Classify each row:
- `ProcessType = 'Workflow'` → **Process Builder** (legacy, should be migrated).
- `ProcessType = 'AutoLaunchedFlow'` + `TriggerType IN ('RecordAfterSave','RecordBeforeSave','RecordBeforeDelete')` → **Record-Triggered Flow**.
- `ProcessType = 'Flow'` → Screen Flow (not object-scoped automation unless launched from an action on this object — flag as ambiguous).
- `ProcessType = 'AutoLaunchedFlow'` + no trigger type → **Auto-launched subflow** (fires when invoked).
- `ProcessType = 'Orchestrator'` → **Orchestration Flow**.

### 2. Apex triggers on the object

```sql
SELECT Id, Name, TableEnumOrId, Status, UsageBeforeInsert, UsageBeforeUpdate,
       UsageBeforeDelete, UsageAfterInsert, UsageAfterUpdate, UsageAfterDelete,
       UsageAfterUndelete, NamespacePrefix, ApiVersion
FROM ApexTrigger
WHERE TableEnumOrId = :object
  AND Status = 'Active'
  AND (include_managed=true OR NamespacePrefix = null)
```

The `UsageBefore*` / `UsageAfter*` flags tell you which events the trigger handles — critical for order-of-execution reasoning.

### 3. Validation rules

```sql
SELECT Id, ValidationName, Active
FROM ValidationRule
WHERE EntityDefinition.QualifiedApiName = :object
  AND Active = true
```

### 4. Workflow rules (still supported, deprecated)

```sql
SELECT Id, Name, TableEnumOrId, Active
FROM WorkflowRule
WHERE TableEnumOrId = :object
  AND Active = true
```

### 5. Approval processes (if record-triggered logic may collide with approvals)

```sql
SELECT Id, DeveloperName, ObjectType, Active
FROM ProcessDefinition
WHERE ObjectType = :object
  AND Active = true
```

### 6. Invocable actions defined in Apex (methods callable from Flow)

```sql
SELECT Id, Name
FROM ApexClass
WHERE Body LIKE '%@InvocableMethod%'
  AND NamespacePrefix = null
LIMIT 200
```

(Body filtering is expensive; only run this when `flow-builder` is about to add an action call and needs to check for an existing invocable instead of re-implementing.)

---

## Output Shape

Return one structured block the caller can drop into a report:

```yaml
automation_graph:
  object: Account
  collected_at: 2026-04-19T14:00:00Z
  active:
    record_triggered_flows:
      - api_name: Account_Stamp_Description_Before_Save
        label: Stamp Description Before Save
        trigger_type: RecordBeforeSave
        version: 3
    process_builders:
      - api_name: Account_PB_v1
        label: Account Lifecycle PB
    triggers:
      - name: AccountTrigger
        events: [BeforeUpdate, AfterUpdate]
        api_version: "60.0"
    validation_rules:
      - name: Account_Billing_Required
    workflow_rules: []
    approval_processes: []
  flags:
    - code: MULTIPLE_RECORD_TRIGGERED_FLOWS
      severity: P1
      count: 3
      message: "Account has 3 active record-triggered flows. Consolidate before adding a 4th."
    - code: PROCESS_BUILDER_PRESENT
      severity: P1
      message: "Process Builder is deprecated; migrate via /migrate-workflow-pb before adding new Flow automation."
```

## Flags the probe should raise

| Code | Severity | Trigger |
|---|---|---|
| `MULTIPLE_RECORD_TRIGGERED_FLOWS` | P1 | ≥3 active record-triggered flows on the same trigger context (e.g. 3 BeforeSave) |
| `PROCESS_BUILDER_PRESENT` | P1 | any active Process Builder on the object |
| `WORKFLOW_RULE_PRESENT` | P2 | any active Workflow Rule on the object |
| `TRIGGER_AND_FLOW_COEXIST` | P2 | both active Apex trigger(s) AND active record-triggered flows on the same context — order of execution concern |
| `APPROVAL_PROCESS_ACTIVE` | P2 | Approval process active — be careful with before-save writes that might conflict |

## Consuming the probe

**`flow-builder` Step 0:**
- Run this probe at the start of the Plan, before the decision tree.
- If `MULTIPLE_RECORD_TRIGGERED_FLOWS` fires, the agent **does not automatically refuse** — but the Process Observations MUST document the existing flows and the design MUST declare an explicit merge/extend/new justification. A soft nudge, not a hard gate (pending real-user data).
- If `PROCESS_BUILDER_PRESENT`, recommend `/migrate-workflow-pb` as a follow-up agent.

**`apex-builder`:**
- Run this probe when the Apex under design includes a trigger or an `@InvocableMethod` that `flow-builder` might later consume. Surfaces recursion risk.

**`automation-migration-router`:**
- Use the probe to discover sources; the router already has its own dispatch, but this probe gives the caller a single view of what needs migrating.

---

## Non-goals

- This probe does **not** score risk — it enumerates and flags. Risk scoring is the consuming agent's job.
- This probe does **not** suggest consolidation. That is a human-plus-flow-builder decision in Step 1.
- This probe does **not** fetch the full Flow XML. If the consuming agent needs the XML to compare, it issues a separate `tooling_query` per flow.

---

## Related skills

- `flow/record-triggered-flow-patterns`
- `apex/trigger-and-flow-coexistence`
- `standards/decision-trees/automation-selection.md`

## Provenance

Introduced by feedback entry `feedback/FEEDBACK_LOG.md#2026-04-19` (Cursor review of flow-builder, item P1). Lightweight landing intentionally — no hard-gate refusal until we have real-user signal on overlap thresholds.
