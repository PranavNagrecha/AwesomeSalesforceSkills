# Flows in Salesforce Debug Logs

Flows are the single biggest source of complexity in modern Salesforce debug logs. They come in many types, fire in multiple phases, can be sync or async, can call each other, can call Apex, can fail partially, and can loop. This reference covers the complete surface area.

## Flow types and how they appear in logs

### Record-triggered flows

Fire on insert, update, delete, or a combination. Run either **before-save** (fast, same transaction, cannot call Apex) or **after-save** (can call Apex, subflows, other records).

Log signatures:
- `FLOW_START_INTERVIEW_BEGIN|<interview-id>|<Flow_API_Name>`
- The interview ID is unique per flow run.
- Before-save flows appear inside a `before` trigger phase of the object.
- After-save flows appear inside an `after` trigger phase.
- Multiple record-triggered flows on the same object fire in an **undefined order** unless you set the Trigger Order field (Summer '22+). Check for `Triggered_Flow_Order__c` or look at the order of interviews in the log.

### Screen flows

User-facing, run in Lightning, Experience Cloud, or embedded in LWC. Show up in the log when a screen flow calls an Apex invocable action or performs DML.

Log signatures:
- Execution context is the UI user, not an automation user.
- `FLOW_START_INTERVIEW_BEGIN` with a flow whose label ends in "Screen Flow" or is known to be UI.
- `FLOW_SCREEN_BEGIN` and `FLOW_SCREEN_END` bracket each screen the user sees.

### Scheduled flows (Schedule-Triggered Flow)

Run on a schedule defined in Setup. Similar to scheduled Apex but declarative.

Log signatures:
- `EXECUTION_STARTED` at the top with no user action preceding.
- `CODE_UNIT_STARTED|[EventService.....scheduledApex]|01p...` in some orgs, or directly `FLOW_START_INTERVIEW_BEGIN`.
- Running user is the Automated Process user (`@00D...`) or the user who scheduled the flow.

### Platform event-triggered flows

Subscribe to a platform event channel and fire when an event is published.

Log signatures:
- Trigger context on an event object (`My_Event__e`).
- `FLOW_START_INTERVIEW_BEGIN` immediately after the event fires.
- Running user is the Automated Process user by default.

### Autolaunched flows

No trigger. Called from Apex (`Flow.Interview`), Process Builder, another flow, an invocable action, or a REST API.

Log signatures:
- Appears inside a larger execution context.
- `FLOW_CREATE_INTERVIEW_BEGIN` before `FLOW_START_INTERVIEW_BEGIN` when called from Apex.

### Flow Orchestrator

Multi-step orchestrations with work items assigned to users or groups.

Log signatures:
- `FLOW_START_INTERVIEW_BEGIN` on an orchestration flow.
- `OrchestrationStage` and `OrchestrationStep` entities in DML.
- `WorkItem` records created/updated.

### Paused flows (Wait elements)

Flows with a Wait element persist their state and resume when the condition is met (time-based or event-based).

Log signatures:
- `FLOW_WAIT_EVENT_WAITING_DETAIL` when the flow is pausing.
- `FLOW_WAIT_EVENT_RESUMING_DETAIL` when it resumes (in a new transaction, new log).
- `PausedFlowInterview` record is created to persist state.

## The flow event vocabulary

In order of what you see most often to least often:

| Event | Meaning |
|---|---|
| `FLOW_START_INTERVIEWS_BEGIN` | A batch of flow interviews is about to start (bulk context). |
| `FLOW_START_INTERVIEW_BEGIN` | A single interview is starting. Includes interview ID and flow API name. |
| `FLOW_START_INTERVIEW_END` | The interview started successfully. |
| `FLOW_START_INTERVIEWS_END` | The batch finished starting. |
| `FLOW_CREATE_INTERVIEW_BEGIN/_END` | Interview object created (before START). |
| `FLOW_ELEMENT_BEGIN/_END` | A single element executing. The element type follows (Decision, Assignment, Get Records, etc.) |
| `FLOW_ELEMENT_DEFERRED` | Element marked for async execution. |
| `FLOW_ELEMENT_FAULT` | Element threw. Fault connector is taken if defined. |
| `FLOW_ASSIGNMENT_DETAIL` | A variable or record field got a value. Includes target and source. |
| `FLOW_VALUE_ASSIGNMENT` | Internal assignment, including full record snapshots. |
| `FLOW_RULE_DETAIL` | A Decision rule was evaluated. Shows which path was taken. |
| `FLOW_DECISION_DETAIL` | Decision outcome summary. |
| `FLOW_LOOP_DETAIL` | A Loop element iteration. |
| `FLOW_ACTIONCALL_DETAIL` | An invocable action was called (Apex @InvocableMethod, core action, or platform action). |
| `FLOW_SUBFLOW_DETAIL` | A subflow was invoked. |
| `FLOW_WAIT_EVENT_WAITING_DETAIL` | Pause element engaged. |
| `FLOW_WAIT_EVENT_RESUMING_DETAIL` | Pause resumed. |
| `FLOW_SCREEN_BEGIN/_END` | Screen flow screen. |
| `FLOW_CREATE_RECORDS_BEGIN/_END` | Create Records element. |
| `FLOW_UPDATE_RECORDS_BEGIN/_END` | Update Records element. |
| `FLOW_DELETE_RECORDS_BEGIN/_END` | Delete Records element. |
| `FLOW_FIND_RECORDS_BEGIN/_END` | Get Records element. |
| `FLOW_FORMULA_DETAIL` | A formula in the flow was evaluated. |
| `FLOW_INTERVIEW_FINISHED` | The whole interview is done. |
| `FLOW_INTERVIEW_FINISHED_LIMIT` | Interview hit a limit and was truncated. |
| `FLOW_BULK_ELEMENT_BEGIN/_END` | Bulk element processing multiple records at once. |
| `FLOW_BULK_ELEMENT_DETAIL` | Details per record in a bulk element. |
| `FLOW_BULK_ELEMENT_FAULT` | Bulk element failed for one or more records. |

## Reading FLOW_ASSIGNMENT_DETAIL

Format:
```
<timestamp>|FLOW_ASSIGNMENT_DETAIL|<interview-id>|<target variable>|<source value>
```

The target can be:
- A local flow variable: `FlowVar_MyThing`
- A record variable: `$Record.Field__c`
- An output variable: `OutputVar_X`

The source can be:
- A literal: `"hello"`, `true`, `42`
- A merge field: `{!$Record.Email}`
- A formula result: already evaluated
- Another variable

When diagnosing "who set this field", grep for:
```bash
grep "FLOW_ASSIGNMENT_DETAIL" log.log | grep "My_Field__c"
```

Every line that matches names both the interview ID (tells you which flow) and the value assigned.

## Reading FLOW_VALUE_ASSIGNMENT

This is the "internal" version of assignment and is where full record snapshots live. Format:
```
<timestamp>|FLOW_VALUE_ASSIGNMENT|<flow-instance-hash>|$Record|{Id=..., Field1__c=..., Field2__c=..., ...}
```

The record dump inside the curly braces is a complete snapshot of the record as the flow sees it at that moment. This is what you parse for field transitions in flip-flop diagnostics.

**Gotcha**: the record dump includes every field the flow is aware of, which is typically every field on the object (SF loads the whole record). Do not mistake appearance in this dump for "the flow wrote this field". It just means the flow knows the field exists.

## Flow fault paths

Elements can have a fault connector. When they fail, execution takes the fault path instead of throwing.

Log signature of a handled fault:
```
FLOW_ELEMENT_FAULT|<element>|<error text>
FLOW_ELEMENT_BEGIN|<fault-connector-element>|...
```

Log signature of an unhandled fault:
```
FLOW_ELEMENT_FAULT|...
FATAL_ERROR|...
```

When a record-triggered flow has no fault handler and an element fails, the whole trigger DML fails with `CANNOT_EXECUTE_FLOW_TRIGGER`.

Common faults:
- `DUPLICATES_DETECTED`: duplicate rule blocked a Create/Update.
- `FIELD_CUSTOM_VALIDATION_EXCEPTION`: a validation rule rejected.
- `INSUFFICIENT_ACCESS_OR_READONLY`: user cannot edit.
- `LIMIT_EXCEEDED`: governor limit.
- `System.NullPointerException`: the flow tried to access a null field without a null check. Very common.

## Flow bulkification

Record-triggered flows fire once per DML, but process all records in the trigger as a collection. `FLOW_BULK_ELEMENT_BEGIN` wraps the bulk processing.

**The critical point**: elements like Get Records, Create Records, Update Records, and Delete Records are **automatically bulkified** by the Flow engine. One `FLOW_UPDATE_RECORDS_BEGIN` event represents an update for all records in the trigger batch, not one per record. However, elements inside a Loop are **not** bulkified: if you have an Update inside a Loop, the flow issues one DML per iteration. This blows governor limits on bulk DML.

Grep to identify:
```bash
grep -cE "FLOW_UPDATE_RECORDS_BEGIN|FLOW_CREATE_RECORDS_BEGIN|FLOW_DELETE_RECORDS_BEGIN" log.log
```

If the count is much higher than the number of DMLs happening, you have unbulkified DML inside loops.

## Flow recursion

Flows that update the same object they are triggered on can recurse. The platform's recursion guard is limited:
- Before-save flows: cannot recurse on the same record in the same transaction. Platform blocks it.
- After-save flows: can recurse up to 5 times for the same record in the same transaction.
- If a flow updates a different record that itself triggers another flow, there is no platform recursion limit beyond general limits.

Log signature of recursion:
```
FLOW_START_INTERVIEW_BEGIN|<interview1>|My_Flow
...
FLOW_START_INTERVIEW_BEGIN|<interview2>|My_Flow   ← same flow, different interview ID
...
```

Same flow name appearing multiple times with different interview IDs in one transaction = recursion (or bulk processing multiple records, check the record IDs).

## Flow transactions

By default, each flow runs in the calling transaction. When a flow is async (triggered by an event, scheduled, or after a Pause), it runs in its own transaction.

A `FLOW_START_INTERVIEW_BEGIN` with the same interview ID appearing in different logs = same interview resumed after a Pause.

## Before-save vs after-save record-triggered flows

Before-save flows:
- Run before the record is written to the database.
- Cannot call Apex actions (invocable methods).
- Cannot perform cross-object DML.
- Cannot create/update/delete records (only modify $Record in memory).
- Fastest performance. No additional DML for same-record updates.

After-save flows:
- Run after the record is written.
- Can do everything: call Apex, cross-object DML, subflows, create/update/delete other records.
- To update the triggering record from an after-save flow, the flow issues a separate Update Records, which fires triggers again.

In the log, before-save runs inside the `before` trigger phase of the object. After-save runs inside the `after` trigger phase. If you grep triggers and flows in order, the phases are obvious.

## Flow error handling and debugging

When a flow fails and the email notification says "An Error Occurred in Flow: ...", the debug log is usually the best diagnostic. Steps:

1. Find `FLOW_ELEMENT_FAULT` in the log.
2. Read 20 lines back to understand what element threw and what inputs it had.
3. Look for the specific SObject or value that caused the issue.
4. If the fault says `NullPointerException` and references a merge field like `{!$Record.Account.Name}`, it is because the record's Account lookup was null.

**Gotcha**: cross-object merge fields in flows (like `$Record.Account.Name`) only work if the lookup is non-null AND the flow is loading related data. For before-save flows, you cannot traverse lookups; you must explicitly Get Records.

## Calling Apex from flows

Apex classes marked `@InvocableMethod` can be called as flow actions. Log signature:
```
FLOW_ACTIONCALL_DETAIL|<interview-id>|<action-label>|<action-name>|<type>|<params>
CODE_UNIT_STARTED|[EventService.....apex]|<class-name>.<method-name>
```

Everything inside the CODE_UNIT block is the Apex execution, including its own SOQL, DML, and sub-triggers.

Common @InvocableMethod use cases:
- Complex logic too gnarly for flow (regex, complex parsing, crypto).
- Callouts (flows cannot do callouts directly, must go through Apex).
- Custom validation with specific messages.
- Aggregation across many records.

## Subflows

One flow can call another. Log signature:
```
FLOW_SUBFLOW_DETAIL|<parent-interview-id>|<subflow-name>|<subflow-interview-id>
```

The subflow's events appear inline in the parent's log. Governor limits are shared across the parent and subflow.

## Multiple flows on the same object

If an object has 10 record-triggered flows, a single DML fires all 10. Unless Trigger Order is set, the order is undefined.

To see all flows that fired in a transaction:
```bash
grep "FLOW_START_INTERVIEW_BEGIN" log.log | awk -F'|' '{print $3}' | sort -u
```

To see the order:
```bash
grep "FLOW_START_INTERVIEW_BEGIN" log.log | awk -F'|' '{print $1, $3}'
```

**Gotcha with field conflicts**: if two flows both update the same field, the last one wins. The "last one" depends on order, which may not be stable across runs. This is a classic flip-flop cause: two flows alternately winning based on transaction ordering.

## Formulas inside flows

Flow formulas evaluate at the moment they are referenced. `FLOW_FORMULA_DETAIL` shows the formula expression and result.

Gotcha: formula resources referencing `$Record` in a before-save flow see the record mid-flight. If the flow modifies `$Record.Field__c` and then evaluates a formula that references `Field__c`, the formula sees the new value. This can cause confusion when the formula was designed against "the saved record".

## Get Records and SOQL

`FLOW_FIND_RECORDS_BEGIN` generates a SOQL query. The query is logged as `SOQL_EXECUTE_BEGIN` with the specific WHERE clause and fields. If you want to know exactly what fields a Get Records element pulled, look at the paired SOQL.

Gotcha: flow Get Records does not respect field-level security by default unless "Filter fields" is configured. Be careful in community/guest-user contexts.

## Async path flows

Record-triggered flows can have an "async path" that runs 0 seconds later but in its own transaction. This is new-ish (Summer '22+). 

Log signature: the main flow finishes, and then a separate log appears with the same flow name but `FLOW_START_INTERVIEW_BEGIN` in a new transaction context. The Automated Process user runs the async path.

Use case: when you want to do callouts or heavy work without blocking the user, the async path is how.

## Flow diagnostic grep recipes

```bash
# All flows that fired, in order, with timestamps
grep "FLOW_START_INTERVIEW_BEGIN" log.log | awk -F'|' '{print $1, $3}'

# Every field a specific flow assigned
grep "FLOW_ASSIGNMENT_DETAIL" log.log | grep "<interview-id>"

# Every element that faulted
grep "FLOW_ELEMENT_FAULT" log.log

# Every time the flow took a decision
grep "FLOW_RULE_DETAIL" log.log

# Every Get Records and its SOQL
paste <(grep "FLOW_FIND_RECORDS_BEGIN" log.log) <(grep -A1 "FLOW_FIND_RECORDS_BEGIN" log.log | grep "SOQL_EXECUTE_BEGIN")

# All invocable Apex actions called from flows
grep "FLOW_ACTIONCALL_DETAIL" log.log | awk -F'|' '{print $4}'

# All subflows
grep "FLOW_SUBFLOW_DETAIL" log.log

# Every interview start (unique flows)
grep "FLOW_START_INTERVIEW_BEGIN" log.log | awk -F'|' '{print $3}' | sort -u

# Recursion check: same flow starting multiple times
grep "FLOW_START_INTERVIEW_BEGIN" log.log | awk -F'|' '{print $3}' | sort | uniq -c | sort -rn
```

## Common flow gotchas that show up in logs

1. **Null pointer on merge field**: `$Record.Account.Name` where Account is null. Fault text names the expression.
2. **SOQL inside Loop**: `FLOW_FIND_RECORDS_BEGIN` appearing inside `FLOW_LOOP_DETAIL` iterations. Blows the 100-SOQL limit.
3. **Unbulkified DML**: `FLOW_UPDATE_RECORDS_BEGIN` inside a Loop. Blows the 150-DML limit.
4. **Race between two flows**: two flows writing to the same field. Values oscillate.
5. **Stale merge field**: $Record in before-save has the user's input; after another before-save flow runs, $Record has the modified value. Confusing when flows read each other's work.
6. **Forgotten fault path**: element fails, whole DML fails, user sees generic error. Add a fault path to surface the real error.
7. **Cross-object update in a before-save**: not allowed. The log shows the flow trying and failing.
8. **Calling an Apex action that does a callout from a non-async flow**: allowed only if the callout is made in a `@future(callout=true)` or queueable, not inline.
