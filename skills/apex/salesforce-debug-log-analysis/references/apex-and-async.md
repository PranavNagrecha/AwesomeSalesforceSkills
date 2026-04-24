# Apex and Async Patterns in Debug Logs

Apex is the programmatic layer. This reference covers every Apex construct you will see in logs: triggers, classes, batch, queueable, future, scheduled, platform events, CDC, and test execution. Each has distinct log signatures, limits, and failure modes.

## Triggers

### The trigger events

A DML fires up to 7 trigger contexts in this order:
1. `before insert`
2. `before update`
3. `before delete`
4. `after insert`
5. `after update`
6. `after delete`
7. `after undelete`

Log signature:
```
CODE_UNIT_STARTED|[EventService.....trigger]|<id>|<TriggerName> on <Object> trigger event BeforeUpdate
```

### The trigger handler pattern

Mature orgs use a single trigger per object that delegates to Apex handler classes. Common frameworks:
- fflib (FinancialForce)
- Kevin O'Hara's TriggerHandler
- Custom in-house handlers

Log signatures to identify:
```
CODE_UNIT_STARTED|[EventService.....trigger]|<id>|ContactTrigger on Contact trigger event BeforeUpdate
CODE_UNIT_STARTED|[EventService.....apex]|<class-id>|ContactTriggerHandler.onBeforeUpdate
```

The pattern: trigger fires → trigger calls handler → handler calls specific business logic classes. Each layer is a `CODE_UNIT` block, deeply nested.

### Recursion control

Triggers often recurse when they update the same object they fire on. Two patterns in use:

1. **Static boolean guard**: a static variable `TriggerHandler.isExecuting` is set to true on first entry and blocks re-entry. In the log, you see the trigger enter once and skip subsequent invocations. Look for `USER_DEBUG|...|isExecuting` or similar.
2. **Record set comparison**: handler tracks which record IDs have been processed and skips them. Log shows trigger firing but the handler doing nothing.

When recursion is the culprit, the log shows the same trigger firing 3, 4, or more times in one transaction for the same record IDs, with each firing doing some work.

### Context variables

Triggers have `Trigger.new`, `Trigger.old`, `Trigger.newMap`, `Trigger.oldMap`, `Trigger.isInsert`, etc. These do not appear in the log as explicit events but are inferrable from what the trigger does (update = has both new and old).

## Apex classes

### `with sharing`, `without sharing`, `inherited sharing`

Affects whether record-level sharing is enforced. Log signatures:
- `SYSTEM_MODE_ENTER`: entering a `without sharing` context.
- `SYSTEM_MODE_EXIT`: leaving it.

If you see `SYSTEM_MODE_ENTER` around a sensitive operation, the code is running privileged regardless of user permissions.

### `@AuraEnabled` methods

Called by LWC/Aura. Show up as `CODE_UNIT_STARTED|[EventService.....apex]|...|<Class>.<method>` at the top of the transaction.

`@AuraEnabled(cacheable=true)` methods are cached by the platform and may not appear in the log at all if the result was cached. Only cache misses hit Apex.

### `@InvocableMethod` methods

Called from flows. Log signature includes `FLOW_ACTIONCALL_DETAIL` followed by the class entry.

Gotcha: the method signature must use `List<InputWrapper>` and `List<OutputWrapper>`. The log shows the serialized input list which is often useful for debugging.

### `@RestResource` classes

Expose REST endpoints. Log starts with `EXECUTION_STARTED`, then `CODE_UNIT_STARTED|[RestHttpPost_...]` or similar.

### `@future` methods

Run async in their own transaction. Log signature:
```
CODE_UNIT_STARTED|[future]|<class>.<method>
```

Constraints:
- Static only.
- Parameters must be primitives, collections of primitives, or sObject IDs.
- Up to 50 future calls per transaction (limit).
- Cannot call another future from a future.
- `@future(callout=true)` allows callouts; without it, no callouts.

When a future is queued but not yet executed, it appears in Setup > Apex Jobs as pending. The log for the future execution is a separate log.

### Queueable Apex

More flexible than future. Implements `Queueable`. Can accept sObjects directly. Can chain.

Log signature:
```
CODE_UNIT_STARTED|[EventService.....queueable]|<class-name>
```

Constraints:
- 50 queueables per transaction (50 in sync context, 50 more in async if chained).
- 1 queueable can be enqueued per queueable execute (chain).
- Can use `Queueable, Database.AllowsCallouts` to enable callouts.

To chain: inside `execute()`, call `System.enqueueJob(new NextJob())`. The log shows this as another queueable starting in a separate transaction.

### Batch Apex

`Database.Batchable<SObject>` with start, execute, finish methods. Runs async, one batch scope at a time.

Log signatures across multiple logs:
- **Start log**: `BATCH_APEX_START` event. Contains the SOQL or iterable that will drive the batches.
- **Execute logs**: one per batch (default 200 records). Each is an independent transaction. `BATCH_ID=<id>` in the header identifies them as part of the same batch job.
- **Finish log**: `BATCH_APEX_FINISH` event. Runs after all execute batches complete.

Common batch failures:
- `FATAL_ERROR` in execute: one batch failed, others continue. Failed scope is logged.
- `Too many SOQL queries` in execute: batch execute() hit 100 SOQL. Reduce scope size.
- Stateful batches (`implements Database.Stateful`): member variables persist across executes. If they accumulate lists/maps, heap size grows across batches.

### Scheduled Apex

Implements `Schedulable`. Fires on a cron schedule.

Log signatures:
- Header includes `CRON_TRIGGER_` reference.
- `CODE_UNIT_STARTED|[EventService.....scheduled]|<class-name>`
- Running user is the user who scheduled the job (not always the sysadmin).

Constraints:
- Cannot call Database.executeBatch directly from inside a schedulable if it would exceed limits. Often scheduled Apex just enqueues a queueable or batch.
- Up to 100 scheduled jobs org-wide.

## Platform Events

Event-driven messaging. Publishers publish events, subscribers (Apex triggers, flows, processes, LWC) consume them.

### Publishing

```
EventBus.publish(new My_Event__e(...));
```

Log signature in publisher:
```
DML_BEGIN|[line]|Op:Insert|Type:My_Event__e|Rows:1
EVENT_SERVICE_PUB|My_Event__e|<ReplayId>
```

### Subscribing via Apex trigger

Triggers on `__e` objects. Fire after commit in a separate transaction.

Log signature in subscriber:
```
CODE_UNIT_STARTED|[EventService.....trigger]|<id>|MyEventTrigger on My_Event__e trigger event AfterInsert
```

Running user is the Automated Process user by default, unless the trigger is configured with a run-as user.

### Subscribing via flow

Platform event-triggered flows. Same flow mechanics, different entry point.

### High-volume platform events

Retained for 72 hours. Replay by ReplayId. If subscribers fall behind, events can be lost past the retention window.

### Common failure: circular events

Trigger on `__e` publishes another event that fires another trigger that publishes another event. No platform-level recursion guard. Check that every event publisher has an off-switch.

## Change Data Capture (CDC)

CDC emits events when records change on standard or custom objects. Subscribers can trigger on `<Object>__ChangeEvent`.

Log signature:
```
CODE_UNIT_STARTED|[EventService.....trigger]|<id>|MyCDCTrigger on Account__ChangeEvent trigger event AfterInsert
```

CDC events include:
- `ChangeType`: CREATE, UPDATE, DELETE, UNDELETE, GAP_OVERFLOW
- `ChangedFields`: list of fields that changed
- `EntityName`: the object
- `RecordIds`: IDs of records that changed

Gotcha: bulk updates produce one CDC event with many record IDs. Do not assume one event per record.

## Test execution

### @isTest annotation

Classes or methods marked `@isTest` run in test mode with a rollback after completion. Data created in a test does not persist.

Log signatures:
- `CODE_UNIT_STARTED|[EventService.....test]|<class>.<method>`
- `TESTING_LIMITS` events show limits specific to the test.
- `Test.startTest()` resets governor limits; shows up in the log as a boundary.
- `Test.stopTest()` forces async to run synchronously inside the test.

### @TestSetup

Runs once before all test methods in the class. Data persists across test methods in that class (but still rolls back after).

Log signature:
```
CODE_UNIT_STARTED|[EventService.....testSetup]|<class>.<method>
```

### Test.isRunningTest()

Allows branching behavior in tests. In logs, you see the test branch executing and the production branch skipped.

## Async DML

When Apex updates records that require async processing (for instance, setting a formula field with large dependencies), you see:
```
ASYNC_DML_BEGIN
...
ASYNC_DML_END
```

This usually means the platform itself is offloading work. Not configurable.

## Governor limits for async

Async contexts have different, usually higher, limits:

| Limit | Sync | Async (batch, queueable, future) |
|---|---|---|
| SOQL queries | 100 | 200 |
| SOQL rows | 50,000 | 50,000 |
| DML statements | 150 | 150 |
| DML rows | 10,000 | 10,000 |
| Heap size | 6 MB | 12 MB |
| CPU time | 10 sec | 60 sec |
| Callouts | 100 | 100 |

`CUMULATIVE_LIMIT_USAGE` block at the end of the log shows exactly what was used per namespace.

## Recursion control across async

Static variables reset between transactions. A static boolean in a trigger does not prevent recursion across async boundaries. If you have a queueable that updates a record that fires a trigger that enqueues another queueable, no static guard stops that.

To stop async recursion, use:
- Custom settings / custom metadata to track state.
- Platform Cache.
- A field on the record indicating "processing already done".

## Mixed DML exception

Some object pairs cannot be modified in the same synchronous transaction. The classic is User + any non-setup object.

Log signature:
```
System.MixedDMLException: DML operation on setup object is not permitted after you have updated a non-setup object (or vice versa)
```

Resolution: do one operation, then do the other in `@future` or a queueable.

## Apex-specific grep recipes

```bash
# All Apex classes that ran
grep -oE "CODE_UNIT_STARTED\|\[[^]]+\]\|[^|]+" log.log | sort -u

# All triggers that fired in order
grep "CODE_UNIT_STARTED.*trigger" log.log | awk -F'|' '{print $1, $NF}'

# All DML operations
grep "DML_BEGIN" log.log

# All exceptions
grep -E "EXCEPTION_THROWN|FATAL_ERROR" log.log

# User debug output (System.debug calls)
grep "USER_DEBUG" log.log

# All method calls (with profiling)
grep -E "METHOD_ENTRY|METHOD_EXIT" log.log | head -40

# Every class name that ran (dedupe)
grep -oE "CODE_UNIT_STARTED\|[^|]+\|[^|]+\|[A-Za-z_][A-Za-z0-9_]*" log.log | sort -u

# Governor limit usage summary
grep -A 20 "CUMULATIVE_LIMIT_USAGE$" log.log

# Async context detection
grep -E "BATCH_APEX|CRON|ASYNC|queueable|future" log.log

# Platform event publish/subscribe
grep -E "EVENT_SERVICE_(PUB|SUB)" log.log
```

## Common Apex gotchas visible in logs

1. **SOQL in a loop**: `SOQL_EXECUTE_BEGIN` inside a `for` loop (inferable from execution order). Blows the 100-SOQL limit on bulk DML.
2. **DML in a loop**: same, for `DML_BEGIN`.
3. **Recursive triggers**: same trigger name appearing multiple times for the same record IDs.
4. **Unhandled exceptions in batch**: one batch fails with `FATAL_ERROR`, but the batch job continues. Silent data loss until someone checks Apex Jobs.
5. **Static variable pollution**: values set in one test persist to another in the same class. The log shows unexpected state.
6. **Async failure with no retry**: `@future` that throws is just... gone. No automatic retry.
7. **Mixed DML**: covered above. Specific exception class.
8. **Heap overflow in batch**: stateful batches accumulating collections. Check `HEAP_ALLOCATE` growth across batches.
9. **Schedulable never runs**: orgs sometimes have thousands of queued schedulable jobs stuck. Setup > Apex Jobs shows them. Not visible in log until a job actually runs.
10. **Queueable chain break**: one queueable chains to another, but the chained one throws in constructor and never runs. Logs show the parent finishing but no child log appearing.
