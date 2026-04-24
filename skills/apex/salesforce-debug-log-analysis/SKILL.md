---
name: salesforce-debug-log-analysis
description: "Use when the user has captured Salesforce debug logs and needs forensic analysis of runtime behavior — trigger cascades, flow interviews, LWC/Aura @AuraEnabled calls, batch/queueable/future/scheduled Apex, platform events, CDC, validation/workflow/approvals, callouts, DML failures, governor limit hits, managed-package traces, flip-flop fields, UNABLE_TO_LOCK_ROW, INSUFFICIENT_ACCESS, mixed DML. Triggers: '.log file', 'debug log', 'why is this field changing', 'flow cascade', 'CPU timeout', 'heap exceeded', 'UNABLE_TO_LOCK_ROW', 'INSUFFICIENT_ACCESS', 'replay debugger'. NOT for choosing log levels or designing a logging framework (use apex/debug-and-logging), and NOT for setting up trace flags or Developer Console (use apex/debug-logs-and-developer-console)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
tags:
  - debug-log-analysis
  - forensic-diagnostics
  - trigger-cascade
  - flow-interview
  - governor-limits
  - flip-flop
  - managed-packages
  - concurrency
  - sharing-errors
triggers:
  - "analyze this .log file"
  - "why does this field keep changing"
  - "flow cascade / trigger storm"
  - "UNABLE_TO_LOCK_ROW investigation"
  - "INSUFFICIENT_ACCESS or merge failure"
  - "governor limit hit in production"
  - "CPU timeout or heap exceeded"
  - "mixed DML error"
  - "my batch is stuck"
  - "platform event not firing"
  - "managed package trace (TracRTC, DLRS, CPQ, Vlocity, nCino, EDA, etc.)"
inputs:
  - "one or more captured .log files (apex-*.log, Dev Console export, CLI tail)"
  - "the user's symptom or question (field change, failure, performance, access)"
  - "record IDs, user IDs, or transaction timestamps relevant to the symptom"
outputs:
  - "root-cause headline with evidence citations from specific log events"
  - "timeline across all logs with inter-log deltas"
  - "classification of writing mechanism (Apex direct, Flow assignment, rollup, formula)"
  - "explicit statement of what the log cannot tell you plus concrete next steps"
  - "ordered recommendations from stop-the-bleeding to long-term fix"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-24
---

# Salesforce Debug Log Analysis

Salesforce debug logs look like text but behave like event traces from a distributed system. A single record update can produce tens of thousands of lines across dozens of triggers, flows, LWC controllers, rollup calculations, validation rules, workflow field updates, platform events, and managed packages. The real cause is often in a different transaction than the one the user uploaded, or inside a package whose source you cannot read. This skill captures the complete investigation pattern for every type of Salesforce runtime behavior.

## Recommended Workflow

For any Salesforce log, follow this loop in order. Do not skip steps.

1. **Triage**: classify every uploaded log by size, start time, and shape before reading content.
2. **Timeline**: build a chronological view across all logs with inter-log deltas.
3. **Classify the question**: is the user asking about a flip-flop field, a failed DML, a slow transaction, a flow error, an async job, a merge, a permission issue, or something else? Each has a different investigation recipe.
4. **Load the right reference**: the `references/` folder has dedicated guides for each major category. Load only what applies.
5. **Execute the recipe**: run the specific greps and Python extractions for that category.
6. **Report with structure**: headline, evidence, mechanism, limits, recommendations.

## Step 1: triage every log

Before reading any content, run:

```bash
cd /mnt/user-data/uploads
ls -la *.log

for f in *.log; do
  start=$(head -3 "$f" | tail -1 | awk '{print $1}')
  size=$(wc -c < "$f")
  entry=$(head -5 "$f" | grep -oE "EXECUTION_STARTED|BATCH_APEX|CRON_|CODE_UNIT_STARTED[^|]*\|[^|]*" | head -1)
  echo "$start  size=$size  $f  entry=$entry"
done | sort
```

Classify each log by shape:

| Shape | Size | Signal | Meaning |
|---|---|---|---|
| Parent synchronous | under 1MB | Opens with a top-level `CODE_UNIT_STARTED`, shallow nesting | UI action, API call, or controller entry that started something |
| Cascade (trigger/flow storm) | 2 to 10MB+ | Many `CODE_UNIT_STARTED.*trigger`, `FLOW_START_INTERVIEW_BEGIN` | Downstream firestorm caused by a DML |
| Batch execution | variable | `BATCH_APEX_START`, `BATCH_ID=` | Batch Apex execute() scope |
| Queueable | medium | `CODE_UNIT_STARTED|[EventService....queueable` | Async job |
| Future method | medium | `CODE_UNIT_STARTED|[future]` or namespace + `System.future` | @future continuation |
| Scheduled | medium | `CRON_TRIGGER_` in header | Scheduled Apex fire |
| Platform event trigger | medium | Trigger on `*__e` Object | Event subscriber firing |
| Change Data Capture | medium | Trigger on `*__ChangeEvent` | CDC subscriber firing |
| LWC/Aura controller call | small to medium | `CODE_UNIT_STARTED|[EventService.....aura` or `.apex]|*Controller.*` | @AuraEnabled method invoked |
| Visualforce | small to medium | `VF_PAGE_MESSAGE`, `VF_APEX_CALL` | VF controller lifecycle |
| REST/SOAP service | medium | `EXECUTION_STARTED` then Apex REST resource class | External API hitting custom Apex endpoint |
| Test execution | medium | `CODE_UNIT_STARTED.*test`, `TESTING_LIMITS` | @isTest run |

## Step 2: build the timeline

```python
python3 << 'EOF'
import re, os
logs = []
for f in sorted(os.listdir('.')):
    if f.endswith('.log'):
        with open(f) as fp:
            fp.readline()
            m = re.match(r'(\d{2}:\d{2}:\d{2}\.\d+)', fp.readline())
            if m: logs.append((m.group(1), f, os.path.getsize(f)))
logs.sort()
prev = None
for t, f, s in logs:
    delta = ""
    if prev:
        def sec(x):
            h,m,s = x.split(':'); return int(h)*3600+int(m)*60+float(s)
        delta = f"+{sec(t)-sec(prev):.1f}s"
    tp = "small" if s < 1_000_000 else "large"
    print(f"{t}  {tp:5s}  {s:>10}  {f}  {delta}")
    prev = t
EOF
```

Patterns in deltas:
- Fixed interval every 10 to 60 seconds: scheduled job or retry loop
- Fixed interval every few minutes: scheduled flow or cron
- Tight parent/child pairs within 1 to 5 seconds: single logical operation
- Burst then quiet: bulk load or data migration
- Steadily shrinking intervals: runaway recursion

## Step 3: classify the question

Based on what the user is asking, match to the primary investigation category below. The reference file for each category is named in the right column.

| User's symptom or question | Category | Load reference |
|---|---|---|
| "Why is this field changing?" "Flip-flop" | Field write attribution | `flows.md`, `apex-and-async.md`, `managed-packages.md`, `recipes.md` |
| "Why did my flow fail?" "Flow error" | Flow diagnostics | `flows.md`, `error-codes.md` |
| "My LWC is slow/erroring" "Aura action failed" | UI framework Apex calls | `ui-frameworks.md` |
| "My batch is stuck/failing" | Async Apex | `apex-and-async.md`, `recipes.md` |
| "Platform event not firing" "CDC trigger not running" | Event-driven Apex | `apex-and-async.md`, `integration.md` |
| "UNABLE_TO_LOCK_ROW" "Deadlock" | Concurrency | `error-codes.md`, `recipes.md` |
| "INSUFFICIENT_ACCESS" "merge won't work" "can't see record" | Sharing and FLS | `error-codes.md`, `security-sharing.md`, `recipes.md` |
| "Too many SOQL" "CPU timeout" "Heap exceeded" | Governor limits | `governor-and-performance.md`, `recipes.md` |
| "Workflow rule not firing" "Process Builder" "Approval" | Legacy automation | `legacy-automation.md` |
| "Validation rule blocking" | Validation | `error-codes.md` |
| "Callout failing" "Named credential" "External service" | Integration | `integration.md`, `recipes.md` |
| "What's this `xyz` namespace?" | Unknown managed package | `managed-packages.md` |
| "My test is failing but works in prod" | Test execution | `apex-and-async.md` |
| "VF page throwing" | Visualforce | `ui-frameworks.md` |
| "Duplicate rule blocked" "Matching rule" | Duplicate handling | `specialized-topics.md` |
| "Omni-Channel routing issue" "Skill-based routing" | Service Cloud routing | `specialized-topics.md` |
| "Einstein bot error" "NBA strategy failed" | AI features | `specialized-topics.md` |
| "Continuation timeout" "Transaction Finalizer" | Advanced async | `specialized-topics.md` |
| "Big Object query" "Custom Metadata query" | Specialized data stores | `specialized-topics.md` |
| "Lead conversion issue" "Case merge failure" | Lifecycle operations | `specialized-topics.md`, `recipes.md` |
| "Community user can't see" "Guest User" | Experience Cloud | `security-sharing.md`, `ui-frameworks.md` |
| "Encrypted field masked" "Shield" | Encryption | `security-sharing.md`, `specialized-topics.md` |
| "User needs to see X but can't" | Access model | `security-sharing.md`, `recipes.md` |
| "Slack/Quip/Heroku Connect" | External platform integration | `specialized-topics.md`, `integration.md` |

If the question touches multiple categories (common), load multiple references.

## Step 4: universal patterns worth knowing before opening any reference

### Track field value transitions (flip-flop diagnostics)

```python
import re
for f in sorted_logs:
    with open(f) as fp: content = fp.read()
    matches = re.findall(r'RECORD_ID_FRAGMENT[^}]*?FIELD_NAME[=:]"?([^,"}]+)"?', content)
    prev = None
    for i, m in enumerate(matches):
        if m != prev:
            print(f"{f} [{i:3d}] {m}")
            prev = m
```

Only print transitions. The transition index reveals how deep in the cascade the flip happens. Consistent index across logs = same automation responsible.

### Extract the full execution cascade

```bash
# Every code unit and flow interview that fired, in order
grep -E "CODE_UNIT_STARTED|FLOW_START_INTERVIEW_BEGIN|BATCH_APEX|VF_APEX_CALL" log.log | head -60
```

### Extract all DML operations

```bash
grep -E "DML_BEGIN|DML_END" log.log | head -50
```

### Extract all exceptions

```bash
grep -E "EXCEPTION_THROWN|FATAL_ERROR|FLOW_ELEMENT_FAULT|VALIDATION_FAIL" log.log
```

### Identify the running user and context

Every log has a header with the user ID, organization, and trace flag levels. Check:

```bash
head -20 log.log | grep -E "USER_INFO|EXECUTION_STARTED|APEX_CODE"
```

Also check `LastModifiedById` in any `FLOW_VALUE_ASSIGNMENT` record dumps. If it points to an integration user (`0050B...`, `005...`), you are looking at automation context. If it points to a human user (`005...`), it's a UI or API action by that person.

## Step 5: identify who wrote a field (the four mechanisms)

A field can change through exactly four mechanisms. Each has a different log signature. Before accusing any specific automation, classify which mechanism is in play:

1. **Direct Apex assignment**: `VARIABLE_ASSIGNMENT` target inside a Trigger or Apex class `CODE_UNIT_STARTED` block. Grep: `grep -B2 "FIELD_NAME =" log.log`
2. **Flow assignment**: `FLOW_ASSIGNMENT_DETAIL|<flow-id>|<variable>|<value>` or the field in `FLOW_VALUE_ASSIGNMENT` as a changed value. Grep: `grep "FLOW_ASSIGNMENT_DETAIL" log.log | grep FIELD_NAME`
3. **Rollup recalculation** (DLRS, native roll-up summary, Apex rollup): field appears in before/after record snapshots with a different value, but nothing targets it in any assignment event. Before-update triggers or master-detail rollups recalculated it.
4. **Formula or calculated field**: never actually stored. Recalculated on every read. If grep finds it in SELECT queries but never as an assignment target, it is a formula. You cannot trace who "changed" it because nothing writes to it.

Before blaming a flow or trigger, determine which mechanism applies. Check the field metadata if you can: rollups have `SummaryField__c` markers, formulas have `Formula__c` markers in record dumps.

## Step 6: report with structure

When reporting to the user, always use this structure:

1. **Headline**: one sentence naming the root cause.
2. **Evidence**: specific log events (with timestamps or line numbers) that support it.
3. **Timeline**: if multi-log, the ordered timeline with deltas.
4. **Mechanism**: how this causes the symptom, in terms of SF platform behavior.
5. **What the log cannot tell you**: explicit limits on what the log shows.
6. **Recommendations**: ordered from "stop the bleeding" to "long-term fix".

Do not dump raw log content. Summarize and quote only specific lines that matter.

## Limits: be explicit about what the log cannot tell you

The log cannot tell you:
- Which specific record is blocking a merge when the error says `not accessible: []`
- Why a user's profile/role hierarchy denies access (only that it does)
- What a formula field was "before" the transaction (formulas recalculate, they do not store)
- What happened in a different transaction that is not uploaded
- The org's OWD, sharing rules, role hierarchy, or permission set assignments
- Whether a field is a rollup, a formula, or a direct write (you must check metadata)
- Why a scheduled job fires at a particular time (check Setup > Scheduled Jobs)
- What ran inside a managed package below `ENTERING_MANAGED_PKG` (by design)
- The content of encrypted fields (shown as `****` or omitted)
- What happened on the server between a callout request and response if the remote system is third-party

When hitting one of these, state so plainly. Give the user the concrete next step outside the log: impersonate user X, query child records as admin vs integration user, open the field setup page, check Setup > Monitoring > Apex Jobs, etc.

## Reference files

The `references/` folder has dedicated guides. Load the ones relevant to the category you identified in step 3:

- `event-types.md`: complete catalog of APEX_CODE event types, header parsing, log level categories, grep cheat sheet
- `flows.md`: all flow types (record-triggered, screen, scheduled, platform event, orchestrator), flow events, fault paths, Pause, subflows, bulkification, recursion
- `apex-and-async.md`: triggers, classes, batch, queueable, future, scheduled, platform events, CDC, test execution, recursion control, mixed DML
- `ui-frameworks.md`: LWC @AuraEnabled patterns, Lightning Data Service, Aura server actions, Visualforce controllers, Experience Cloud/Communities, OmniStudio
- `managed-packages.md`: 50+ package signatures with namespace, field patterns, and known gotchas (TracRTC, DLRS, EDA, traa, CPQ, Vlocity, nCino, FinServ, Pardot, Marketo, DocuSign, and many more)
- `error-codes.md`: DML status codes, flow fault errors, limit exceptions, sharing/access errors, concurrency errors, mixed DML
- `governor-and-performance.md`: all governor limits, per-namespace tracking, CPU and heap analysis, SOQL selectivity, query plan reading, performance optimization patterns
- `legacy-automation.md`: workflow rules, process builder (now flow), approval processes, assignment rules, auto-response, escalation, entitlement, time-based actions, order of execution
- `integration.md`: callouts, named credentials, external services, platform events as integration, CDC, outbound messaging, streaming API, OAuth, Bulk API, MuleSoft/Boomi, Salesforce Connect
- `security-sharing.md`: OWD, role hierarchy, sharing rules, manual sharing, Apex managed sharing (__Share), implicit sharing, territory management, restriction rules, profile vs permission set, FLS, CRUD, with/without sharing, WITH SECURITY_ENFORCED, USER_MODE/SYSTEM_MODE, Shield Platform Encryption, Guest User, Community/Experience Cloud access
- `specialized-topics.md`: Platform Cache, Transaction Finalizers, Continuations, Big Objects, Custom Metadata, Custom Settings, Duplicate Rules, Matching Rules, Lead Conversion, Case Merge, Omni-Channel, Einstein Bots, Einstein Next Best Action, Einstein Activity Capture, Lightning Message Service, Salesforce Functions (deprecated), Heroku Connect, Data Cloud/CDP, Slack integration, Approval Processes, Account/Opportunity/Case Teams, Record Types, Person Accounts, S2S, mobile, and more
- `recipes.md`: end-to-end investigation workflows for the most common problems: flip-flop field, merge failure, governor limit, UNABLE_TO_LOCK_ROW concurrency, performance bottleneck, recursion/infinite loop, missing field update, user access issue, async job stuck, integration silently failing, bulk upload failing, emergency "stop the bleeding" checklist
- `examples.md`, `gotchas.md`, `well-architected.md`, `llm-anti-patterns.md`: repo-standard quality-gate files (worked examples, platform gotchas, pillar framing, anti-patterns to avoid).

Read these only when they apply. Do not preload all of them.

## Related skills

- `apex/debug-and-logging` — production logging strategy, structured sinks, async job monitoring (how to instrument).
- `apex/debug-logs-and-developer-console` — trace flag setup, Developer Console, anonymous Apex, Apex Replay Debugger (how to capture).
- `apex/governor-limits` and `apex/apex-limits-monitoring` — deeper governor-limit treatment once a hit is diagnosed.
- `apex/common-apex-runtime-errors` — error taxonomy reference once a specific exception is identified.

## Official Sources Used

- Apex Developer Guide — [Debug Log](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_debugging_debug_log.htm), [Debug Log Levels](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_debugging_debug_log_levels.htm), [Event Types](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_log_events_reference.htm)
- Apex Reference Guide — [System.Limits](https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_limits.htm), [AsyncApexJob](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_asyncapexjob.htm)
- Salesforce Developer Guide — [Order of Execution](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm), [Governor Limits](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm)
- Flow runtime — [Flow Fault Paths](https://help.salesforce.com/s/articleView?id=sf.flow_build_fault_connector.htm), [Debug a Flow](https://help.salesforce.com/s/articleView?id=sf.flow_distribute_debug.htm)
- Salesforce Help — [Monitor Debug Logs](https://help.salesforce.com/s/articleView?id=sf.code_add_users_debug_log.htm), [Trace Flags](https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/tooling_api_objects_traceflag.htm), [Apex Replay Debugger](https://developer.salesforce.com/tools/vscode/en/apex/replay-debugger)
- Salesforce Architects — [Well-Architected framework](https://architect.salesforce.com/well-architected/overview)
