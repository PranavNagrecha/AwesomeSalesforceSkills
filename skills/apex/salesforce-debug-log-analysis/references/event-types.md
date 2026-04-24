# Complete Salesforce Debug Log Event Types

Salesforce logs every runtime event as a pipe-delimited line. The first token is always the timestamp, the second is the event type. This reference lists every major event type you will encounter, grouped by category.

## Log header

Every log starts with a header line:
```
57.0 APEX_CODE,FINEST;APEX_PROFILING,INFO;CALLOUT,INFO;DATA_ACCESS,INFO;DB,FINEST;NBA,INFO;SYSTEM,DEBUG;VALIDATION,INFO;VISUALFORCE,INFO;WAVE,INFO;WORKFLOW,FINER
```

The first number is the API version. Following it is a semicolon-delimited list of log categories with their level.

### Log levels per category

Each category has levels NONE, ERROR, WARN, INFO, DEBUG, FINE, FINER, FINEST. Higher levels = more events.

| Category | What it controls |
|---|---|
| `APEX_CODE` | Trigger/class execution events. FINEST shows every line. |
| `APEX_PROFILING` | METHOD_ENTRY/EXIT timing. |
| `CALLOUT` | HTTP callout request/response. |
| `DATA_ACCESS` | Access control evaluation (rare). |
| `DB` | SOQL, SOSL, DML events and explain plans. FINEST shows full queries. |
| `SYSTEM` | System.debug() output and system-level events. |
| `VALIDATION` | Validation rule evaluation. |
| `VISUALFORCE` | VF page rendering, controller calls. |
| `WORKFLOW` | Flows, workflow rules, process builder, approvals. FINER shows FLOW_ASSIGNMENT_DETAIL. |
| `NBA` | Next Best Action (Einstein). |
| `WAVE` | Tableau CRM. |
| `SCHEDULING` | Scheduled jobs. |

If the log is missing events you expect (e.g., no FLOW_ASSIGNMENT_DETAIL), the relevant category is not at a high enough level. Ask the user to adjust trace flags.

## Execution envelope events

| Event | Meaning |
|---|---|
| `EXECUTION_STARTED` | Transaction begins. Every log has exactly one. |
| `EXECUTION_FINISHED` | Transaction ends. |
| `CODE_UNIT_STARTED` | A named code unit is entered (trigger, class, flow, anonymous). |
| `CODE_UNIT_FINISHED` | The code unit is exited. |
| `ENTERING_MANAGED_PKG` | Execution entered managed package code. Namespace follows. |
| `SYSTEM_MODE_ENTER` | Entering `without sharing` or other elevated context. |
| `SYSTEM_MODE_EXIT` | Leaving elevated context. |

## DML events

| Event | Meaning |
|---|---|
| `DML_BEGIN` | A DML statement starts. Includes `Op` (operation), `Type` (SObject), and `Rows`. |
| `DML_END` | The DML completes. |
| `ASYNC_DML_BEGIN` | Platform-initiated async DML (e.g., formula recalculation). |
| `ASYNC_DML_END` | Async DML completes. |
| `EXCEPTION_THROWN` | Any exception (DML or otherwise). Includes stack trace. |
| `FATAL_ERROR` | Uncaught exception that kills the transaction. |

DML operations:
- `Insert`, `Update`, `Upsert`, `Delete`, `Merge`, `Undelete`
- Platform event publish: `Op:Insert|Type:My_Event__e`

## SOQL and SOSL events

| Event | Meaning |
|---|---|
| `SOQL_EXECUTE_BEGIN` | Query begins. Full SOQL follows. |
| `SOQL_EXECUTE_EXPLAIN` | Query plan. Shows selectivity, index use. |
| `SOQL_EXECUTE_END` | Query ends. Row count follows. |
| `SOSL_EXECUTE_BEGIN` | SOSL search begins. |
| `SOSL_EXECUTE_END` | SOSL search ends. |

### Reading SOQL_EXECUTE_EXPLAIN

```
15:10:19.148 (6725005489)|SOQL_EXECUTE_EXPLAIN|[12]|Index on Contact : [Email], cardinality: 2, sobjectCardinality: 1234567, relativeCost: 0.05
```

Key numbers:
- `cardinality`: number of rows matching the indexed portion.
- `sobjectCardinality`: total rows in the object.
- `relativeCost`: platform's cost estimate. Below 1.0 is good; above 1.0 suggests the optimizer chose a non-optimal plan.

If you see `TableScan` instead of `Index on ...`, the query is not using an index. Slow.

## Trigger events

| Event | Meaning |
|---|---|
| `CODE_UNIT_STARTED|[EventService.....trigger]` | Trigger firing. Context (BeforeInsert, AfterUpdate, etc.) follows. |

## Flow events

See `flows.md` for complete coverage. Core events:

| Event | Meaning |
|---|---|
| `FLOW_START_INTERVIEW_BEGIN` | Flow interview starts. |
| `FLOW_START_INTERVIEW_END` | Flow interview start completed. |
| `FLOW_CREATE_INTERVIEW_BEGIN/_END` | Interview object created. |
| `FLOW_ELEMENT_BEGIN/_END` | Flow element executes. |
| `FLOW_ELEMENT_FAULT` | Element failed. |
| `FLOW_ASSIGNMENT_DETAIL` | Variable or field assigned. |
| `FLOW_VALUE_ASSIGNMENT` | Internal record snapshot. |
| `FLOW_RULE_DETAIL` | Decision rule evaluated. |
| `FLOW_DECISION_DETAIL` | Decision outcome. |
| `FLOW_LOOP_DETAIL` | Loop iteration. |
| `FLOW_ACTIONCALL_DETAIL` | Invocable action called. |
| `FLOW_SUBFLOW_DETAIL` | Subflow invoked. |
| `FLOW_WAIT_EVENT_WAITING_DETAIL` | Pause element engaged. |
| `FLOW_WAIT_EVENT_RESUMING_DETAIL` | Pause resumed. |
| `FLOW_FIND_RECORDS_BEGIN/_END` | Get Records element. |
| `FLOW_CREATE_RECORDS_BEGIN/_END` | Create Records element. |
| `FLOW_UPDATE_RECORDS_BEGIN/_END` | Update Records element. |
| `FLOW_DELETE_RECORDS_BEGIN/_END` | Delete Records element. |
| `FLOW_BULK_ELEMENT_BEGIN/_END` | Bulk element processing. |
| `FLOW_BULK_ELEMENT_DETAIL` | Per-record bulk detail. |
| `FLOW_BULK_ELEMENT_FAULT` | Bulk element record-level fault. |
| `FLOW_INTERVIEW_FINISHED` | Interview complete. |
| `FLOW_INTERVIEW_FINISHED_LIMIT` | Interview truncated by limit. |
| `FLOW_FORMULA_DETAIL` | Formula evaluation. |

## Workflow rule events (legacy)

| Event | Meaning |
|---|---|
| `WF_RULE_EVAL_BEGIN` | Evaluating workflow rules. |
| `WF_RULE_EVAL_VALUE` | Formula value evaluated. |
| `WF_RULE_EVAL_END` | Evaluation complete. |
| `WF_CRITERIA_BEGIN` | Rule criteria evaluated. |
| `WF_CRITERIA_END` | Criteria evaluation complete. |
| `WF_RULE_ENTRY_CRITERIA` | Rule entry criteria. |
| `WF_ACTION` | Action executed (field update, task, email, outbound msg). |
| `WF_FIELD_UPDATE` | Workflow field update. |
| `WF_TASK` | Task created. |
| `WF_EMAIL_ALERT` | Email alert fired. |
| `WF_OUTBOUND_MSG` | Outbound message queued. |
| `WF_TIME_TRIGGER` | Time-based workflow action fired. |

## Approval process events

| Event | Meaning |
|---|---|
| `WF_APPROVAL` | Approval action. |
| `WF_APPROVAL_SUBMIT` | Submit for approval. |
| `WF_APPROVAL_SUBMITTER` | Submitter identified. |
| `WF_ASSIGNED_APPROVER` | Approver assigned. |
| `WF_PROCESS_NODE` | Approval process step. |

## Visualforce events

| Event | Meaning |
|---|---|
| `VF_PAGE_MESSAGE` | `<apex:pageMessage>` rendered. |
| `VF_APEX_CALL` | Controller method called (getter, setter, action). |
| `VF_EVALUATE_FORMULA_BEGIN/_END` | Formula in page evaluated. |
| `VF_SERIALIZE_VIEWSTATE_BEGIN/_END` | View state serialized. |
| `VF_DESERIALIZE_VIEWSTATE_BEGIN/_END` | View state deserialized. |

## Validation rule events

| Event | Meaning |
|---|---|
| `VALIDATION_RULE` | Validation rule evaluated. |
| `VALIDATION_FORMULA` | Formula of the rule. |
| `VALIDATION_PASS` | Passed. |
| `VALIDATION_FAIL` | Failed. |

## Callout events

| Event | Meaning |
|---|---|
| `CALLOUT_REQUEST` | HTTP request sent. |
| `CALLOUT_RESPONSE` | HTTP response received. |
| `NAMED_CREDENTIAL_REQUEST` | Named credential resolved before callout. |
| `NAMED_CREDENTIAL_RESPONSE` | Named credential response. |
| `EXTERNAL_SERVICE_REQUEST` | External Service invoked. |
| `EXTERNAL_SERVICE_RESPONSE` | Response. |

## Governor limit events

| Event | Meaning |
|---|---|
| `LIMIT_USAGE_FOR_NS` | Running total of limit usage per namespace. |
| `CUMULATIVE_LIMIT_USAGE` | Block begin for cumulative usage summary. |
| `CUMULATIVE_LIMIT_USAGE_END` | Block end. |
| `LIMIT_USAGE` | Specific limit event (SOQL, DML, heap, CPU). |
| `CUMULATIVE_PROFILING` | Profile summary. |
| `CUMULATIVE_PROFILING_BEGIN/_END` | Profile block markers. |

## Variable and memory events

| Event | Meaning |
|---|---|
| `VARIABLE_SCOPE_BEGIN` | Variable declared in a scope. |
| `VARIABLE_ASSIGNMENT` | Variable assigned a value. |
| `HEAP_ALLOCATE` | Heap allocation for an object. |
| `STATEMENT_EXECUTE` | Apex statement executed (FINEST only). |

## Method profiling events

| Event | Meaning |
|---|---|
| `METHOD_ENTRY` | Method called. |
| `METHOD_EXIT` | Method returned. |
| `CONSTRUCTOR_ENTRY` | Constructor called. |
| `CONSTRUCTOR_EXIT` | Constructor returned. |
| `SYSTEM_METHOD_ENTRY` | System method called. |
| `SYSTEM_METHOD_EXIT` | System method returned. |
| `TOTAL_EMAIL_RECIPIENTS_QUEUED` | Email recipients queued. |

## Async job events

| Event | Meaning |
|---|---|
| `BATCH_APEX_START` | Batch start() method called. |
| `BATCH_APEX_EXECUTE` | Batch execute() called for a scope. |
| `BATCH_APEX_FINISH` | Batch finish() called. |
| `ASYNC_START` | Async context entered. |
| `QUEUED_JOB` | Job queued (queueable, future, batch). |

## Event-driven events

| Event | Meaning |
|---|---|
| `EVENT_SERVICE_PUB` | Platform event published. |
| `EVENT_SERVICE_SUB` | Platform event subscribed. |
| `EVENT_SERVICE_SUB_DETAIL` | Subscription detail. |
| `PLATFORM_EVENT_PUBLISH` | Platform event publish (alternate name). |
| `CDC_EVENT` | Change Data Capture event. |

## Testing events

| Event | Meaning |
|---|---|
| `TESTING_LIMITS` | Test-specific limit tracking. |
| `STATIC_VARIABLE_LIST` | Static variables at test start. |

## Miscellaneous events

| Event | Meaning |
|---|---|
| `USER_INFO` | User context metadata (at log start). |
| `USER_DEBUG` | `System.debug()` output. |
| `PUSH_TRACE_FLAGS` | Trace flags applied. |
| `POP_TRACE_FLAGS` | Trace flags popped. |
| `IDEAS_QUERY_EXECUTE` | Ideas query (legacy). |
| `WAVE_APP_LIFECYCLE` | Tableau CRM app events. |
| `NBA_NODE_BEGIN/_END` | Next Best Action node. |
| `NBA_NODE_DETAIL` | NBA node detail. |
| `NBA_NODE_ERROR` | NBA node error. |
| `NBA_STRATEGY_BEGIN/_END` | NBA strategy. |
| `NBA_OFFER_INVALID` | NBA offer invalid. |
| `EMAIL_QUEUE` | Email queued for send. |
| `ORCHESTRATION_SEQUENCE_DETAIL` | Flow orchestrator. |
| `ORCHESTRATION_STAGE_DETAIL` | Orchestrator stage. |
| `ORCHESTRATION_STEP_DETAIL` | Orchestrator step. |

## Grep cheat sheet (quick reference)

```bash
# Entry points
grep "EXECUTION_STARTED\|CODE_UNIT_STARTED" log.log | head -10

# All triggers that fired
grep "CODE_UNIT_STARTED.*trigger" log.log

# All flows
grep "FLOW_START_INTERVIEW_BEGIN" log.log

# All DML
grep "DML_BEGIN" log.log

# All SOQL (counts if many)
grep -c "SOQL_EXECUTE_BEGIN" log.log

# All exceptions
grep -E "EXCEPTION_THROWN|FATAL_ERROR|FLOW_ELEMENT_FAULT|VALIDATION_FAIL" log.log

# Governor usage summary
grep -A 30 "CUMULATIVE_LIMIT_USAGE$" log.log

# User debug output
grep "USER_DEBUG" log.log

# Callouts
grep "CALLOUT_REQUEST\|CALLOUT_RESPONSE" log.log

# Platform events
grep "EVENT_SERVICE_PUB\|EVENT_SERVICE_SUB" log.log

# Workflow rules (legacy orgs)
grep "WF_RULE_EVAL_BEGIN\|WF_FIELD_UPDATE" log.log

# Validation rules
grep "VALIDATION_" log.log

# Method timing (look for slow methods)
grep -E "METHOD_ENTRY|METHOD_EXIT" log.log | head -40

# Managed package entries (namespaces)
grep -oE "ENTERING_MANAGED_PKG\|[A-Za-z_0-9]+" log.log | sort -u

# Flow field assignments (e.g., for specific field)
grep "FLOW_ASSIGNMENT_DETAIL" log.log | grep "My_Field__c"

# Queries matching a field
grep "SOQL_EXECUTE_BEGIN" log.log | grep "My_Field__c"

# All unique entities DML'd
grep "DML_BEGIN" log.log | grep -oE "Type:[A-Za-z_0-9]+" | sort -u
```

## Log level recommendations for specific investigations

When asking the user to re-capture a log for deeper investigation, recommend these levels:

| Investigation | APEX_CODE | APEX_PROFILING | CALLOUT | DB | SYSTEM | VALIDATION | VISUALFORCE | WORKFLOW |
|---|---|---|---|---|---|---|---|---|
| Flip-flop field | FINEST | INFO | INFO | FINEST | DEBUG | INFO | INFO | FINER |
| Performance | INFO | FINE | INFO | FINEST | DEBUG | INFO | INFO | INFO |
| Flow error | INFO | INFO | INFO | FINE | DEBUG | INFO | INFO | FINEST |
| Governor limit | FINE | FINE | INFO | FINEST | DEBUG | INFO | INFO | FINE |
| Integration (callout) | INFO | INFO | FINEST | INFO | DEBUG | INFO | INFO | INFO |
| VF page | INFO | INFO | INFO | FINE | DEBUG | INFO | FINEST | INFO |

Setting everything to FINEST makes huge logs that may hit the 5MB per-log cap or 20MB daily cap. Be surgical.
