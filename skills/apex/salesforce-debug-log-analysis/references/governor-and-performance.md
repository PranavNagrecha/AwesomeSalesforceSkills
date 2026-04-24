# Governor Limits and Performance Analysis

Salesforce enforces governor limits to prevent any single transaction from monopolizing shared resources. Every transaction has a budget per limit type. When the budget is exceeded, the transaction throws a LimitException and rolls back.

This reference covers every governor limit, how to read limit usage in logs, and how to diagnose performance problems.

## The complete governor limit table

Limits differ between synchronous and asynchronous contexts.

| Limit | Synchronous | Async (batch, future, queueable) |
|---|---|---|
| SOQL queries | 100 | 200 |
| SOQL query row limit | 50,000 | 50,000 |
| SOSL queries | 20 | 20 |
| SOSL query row limit | 2,000 | 2,000 |
| DML statements | 150 | 150 |
| DML row limit | 10,000 | 10,000 |
| Total heap size | 6 MB | 12 MB |
| Max CPU time (ms) | 10,000 | 60,000 |
| Max execution time (ms) | 10 min wall | 10 min wall |
| Max callouts per transaction | 100 | 100 |
| Max callout cumulative time (ms) | 120,000 | 120,000 |
| Max @future calls per transaction | 50 | 50 |
| Max email invocations per transaction | 10 | 10 |
| Max stack depth | 1,000 frames | 1,000 frames |
| Max records for @InvocableMethod | 2,000 | 2,000 |
| Max PushTopic queries | 100 | 100 |
| Max records returned by Database.Cursor fetch | 2,000 | 2,000 |

### Per-transaction vs per-license

Most limits are per-transaction. A few are org-wide:
- Org-wide daily API call limit (based on licenses)
- Platform event publishing limits (hourly)
- Scheduled jobs: 100 org-wide
- Async Apex executions per 24 hours: 250,000 or 200 × license count, whichever is higher

## Reading limit usage in logs

### CUMULATIVE_LIMIT_USAGE block

The standard dump appears at the end of each transaction (or before a LimitException) and shows namespace-by-namespace usage.

Format:
```
CUMULATIVE_LIMIT_USAGE
LIMIT_USAGE_FOR_NS|(default)|
  Number of SOQL queries: 34 out of 100
  Number of query rows: 1234 out of 50000
  Number of SOSL queries: 0 out of 20
  Number of DML statements: 12 out of 150
  Number of DML rows: 89 out of 10000
  Maximum CPU time: 3478 out of 10000
  Maximum heap size: 2193423 out of 6000000
  Number of callouts: 0 out of 100
  Number of Email Invocations: 0 out of 10
  Number of future calls: 0 out of 50
  Number of queueable jobs added to the queue: 0 out of 50
  Number of Mobile Apex push calls: 0 out of 10
LIMIT_USAGE_FOR_NS|TracRTC|
  Number of SOQL queries: 12 out of 100
  ...
LIMIT_USAGE_FOR_NS|dlrs|
  Number of SOQL queries: 8 out of 100
  ...
CUMULATIVE_LIMIT_USAGE_END
```

Each managed package gets its own namespace budget. The `(default)` namespace is your code.

### Reading the block

Quick grep:
```bash
grep -A 30 "CUMULATIVE_LIMIT_USAGE$" log.log
```

Or more structured:
```bash
awk '/CUMULATIVE_LIMIT_USAGE$/,/CUMULATIVE_LIMIT_USAGE_END/' log.log
```

Watch for namespaces with high SOQL or DML counts. That is often the culprit.

### LIMIT_USAGE events (granular)

With the right trace flag level, you can see each individual limit use:
```
LIMIT_USAGE|SOQL_QUERIES|1|0|100
LIMIT_USAGE|DML_STATEMENTS|1|0|150
```

Format: `LIMIT_USAGE|<type>|<current-for-ns>|<current-for-default>|<limit>`

## Diagnosing "Too many SOQL queries"

Symptoms: `System.LimitException: Too many SOQL queries: 101` or similar.

Steps:
1. Count SOQL in the log:
   ```bash
   grep -c "SOQL_EXECUTE_BEGIN" log.log
   ```
2. Group queries by source:
   ```bash
   grep -B 2 "SOQL_EXECUTE_BEGIN" log.log | grep "CODE_UNIT_STARTED\|FLOW_FIND_RECORDS_BEGIN" | sort | uniq -c | sort -rn
   ```
3. Look for queries inside loops: if the same query text appears dozens of times in one transaction, it is in a loop.

Common causes:
- SOQL in Apex `for` loop: classic bug.
- Flow Get Records inside a Loop element: same bug in declarative form.
- Recursive triggers firing queries each time.
- Rollup packages (DLRS) querying many children.
- Validation rules that trigger SOQL-heavy formulas.
- Formula fields that reference related records (formulas can force SOQL in triggers).

### Fix patterns

Apex:
```apex
// Bad
for (Contact c : contacts) {
  Account a = [SELECT Name FROM Account WHERE Id = :c.AccountId];
}

// Good (bulkified)
Set<Id> accountIds = new Set<Id>();
for (Contact c : contacts) accountIds.add(c.AccountId);
Map<Id, Account> accountMap = new Map<Id, Account>([SELECT Name FROM Account WHERE Id IN :accountIds]);
for (Contact c : contacts) {
  Account a = accountMap.get(c.AccountId);
}
```

Flow:
- Move Get Records OUT of Loop elements.
- Use Collection Filter instead of Get inside a Loop.

## Diagnosing "Apex CPU time limit exceeded"

Symptoms: `System.LimitException: Apex CPU time limit exceeded`.

The CPU limit counts Apex execution time only, not time waiting for queries, callouts, or DML.

Steps:
1. Enable `APEX_PROFILING,FINE`.
2. Grep `METHOD_ENTRY` and `METHOD_EXIT`:
   ```bash
   grep -E "METHOD_ENTRY|METHOD_EXIT" log.log
   ```
3. Compute method durations from timestamp deltas. The methods with the largest deltas are the CPU hogs.

Common CPU hogs:
- Large loops with complex branching.
- Deeply recursive code.
- Heavy string manipulation, regex, or JSON parsing.
- Serialization/deserialization of large lists.
- Calling many `@future` or queueable jobs (the enqueuing overhead adds up).

### Fix patterns

- Cache values outside loops.
- Short-circuit expensive checks.
- Use `Database.query` with specific fields instead of `SELECT *`.
- Move heavy work to async (future, queueable, batch) where the limit is 60s.

## Diagnosing "Apex heap size too large"

Symptoms: `System.LimitException: Apex heap size too large: <n>`.

Heap counts the memory held by live Apex variables. 6MB sync, 12MB async.

Common heap hogs:
- Large SObject lists held in memory.
- Stateful batch classes accumulating lists across batches.
- Caching entire SOQL results.
- String concatenation in loops (each append creates a new string).

Steps:
1. Grep `HEAP_ALLOCATE`:
   ```bash
   grep "HEAP_ALLOCATE" log.log | wc -l
   ```
   Not hugely useful for diagnosis but confirms heap pressure.
2. Identify large collections:
   ```bash
   grep "VARIABLE_ASSIGNMENT" log.log | grep -oE "^[^|]+\|[^|]+\|[^|]+\|[^|]+\|.*" | sort | head
   ```
3. For stateful batches, check if instance variables accumulate across `execute()` invocations.

### Fix patterns

- Use `Database.QueryLocator` in batch to stream records instead of loading all at once.
- Avoid storing more than needed in stateful batch variables.
- Use `System.Limits.getHeapSize()` to check heap mid-execution.
- Clear variables when done: `bigList = null;`.

## Diagnosing SOQL selectivity issues

### SOQL_EXECUTE_EXPLAIN events

Every query gets an explain plan:
```
SOQL_EXECUTE_EXPLAIN|[line]|Index on Contact : [Email], cardinality: 2, sobjectCardinality: 1234567, relativeCost: 0.05
```

Key numbers:
- `relativeCost` below 1.0: query is using the index efficiently.
- `relativeCost` above 1.0: the optimizer chose a non-optimal plan.
- `TableScan` in the plan: no index was used. Slow.

### Selectivity thresholds

Standard indexes consider a query selective if it matches:
- Less than 30% of the total rows, AND
- Fewer than 1,000,000 rows (absolute)

Custom indexes have tighter thresholds (10% / 333,333 rows).

For highly selective queries, ensure:
- The WHERE clause filters on indexed fields.
- The filter values exist (NULL often does not use indexes).
- No leading wildcards in LIKE.
- Boolean filters on low-cardinality data (IsDeleted, IsClosed) often do not use indexes.

### SKEW_DETECTED

Data skew: too many child records under a single parent (>10,000 children per parent). Causes lock contention and performance issues.

```
SKEW_DETECTED|<parent-field>|<parent-id>
```

Fix: spread children across parents (e.g., multiple default accounts instead of one "Miscellaneous" account).

## Diagnosing callout performance

### CALLOUT_REQUEST / CALLOUT_RESPONSE

Timestamp delta between REQUEST and RESPONSE is the callout duration.

```
CALLOUT_REQUEST|[line]|url:https://api.example.com/...
CALLOUT_RESPONSE|[line]|status:200
```

Cumulative callout time across all callouts in a transaction: 120 seconds limit.

If a callout takes >10 seconds, consider async:
- `@future(callout=true)`
- `Queueable with Database.AllowsCallouts`
- Continuation (for VF with long callouts)

## Identifying the worst offender

Summary workflow:
```bash
# 1. Get counts
echo "SOQL: $(grep -c SOQL_EXECUTE_BEGIN log.log)"
echo "DML: $(grep -c DML_BEGIN log.log)"
echo "Callouts: $(grep -c CALLOUT_REQUEST log.log)"
echo "Flows: $(grep -c FLOW_START_INTERVIEW_BEGIN log.log)"
echo "Triggers: $(grep -c 'CODE_UNIT_STARTED.*trigger' log.log)"

# 2. Per-namespace usage
awk '/CUMULATIVE_LIMIT_USAGE$/,/CUMULATIVE_LIMIT_USAGE_END/' log.log

# 3. Per-namespace SOQL count
grep -B 10 "SOQL_EXECUTE_BEGIN" log.log | grep "ENTERING_MANAGED_PKG" | sort | uniq -c | sort -rn
```

## Performance optimization patterns

1. **Bulkify**: one query/DML for a batch, not one per record.
2. **Selective queries**: filter on indexed fields.
3. **Cache**: use `Map<Id, SObject>` to avoid re-querying.
4. **Async offload**: move heavy work to batch/queueable/future.
5. **Skip unchanged records**: in triggers, compare new vs old to avoid unnecessary work.
6. **Use `WITH SECURITY_ENFORCED` sparingly**: it adds overhead to every query. Profile first.
7. **Flatten rollups**: if DLRS is killing performance, consider scheduled recalculation instead of realtime.
8. **Use platform events for decoupling**: instead of directly calling dependent logic, publish an event.
9. **Use Change Data Capture for integration**: lets external systems subscribe to changes instead of polling.

## Performance anti-patterns

1. **Queries in loops**: covered above.
2. **Using formula fields heavily in triggers**: formulas evaluate on query, contributing to heap.
3. **Over-indexed objects**: too many custom indexes slow DML.
4. **Unbounded SOQL**: `SELECT Id FROM Contact` without WHERE.
5. **Large static variables**: they persist for the transaction, consuming heap.
6. **Recursive triggers**: covered in apex-and-async.md.
7. **Chatty integrations**: one callout per record instead of bulk API.
8. **Overly broad Duplicate Rules**: evaluate on every DML, expensive.
9. **Too many validation rules with SOQL formulas**: cross-object references in validation formulas can force SOQL.

## Test class governor limits

Tests start with fresh limits. `Test.startTest()` resets limits so you can assert a specific operation does not exceed them. `Test.stopTest()` forces async to execute synchronously.

In tests, use:
```apex
Test.startTest();
// Code under test
System.assertEquals(1, Limits.getQueries(), 'Expected 1 SOQL');
Test.stopTest();
```

Profile via the log to find hotspots before failing in production.

## Monitoring in Setup

Even without logs:
- Setup > Monitoring > Debug Logs: live log stream.
- Setup > Monitoring > Apex Jobs: batch/queueable/future/scheduled history.
- Setup > Monitoring > Scheduled Jobs: upcoming scheduled jobs.
- Setup > Monitoring > Apex Flex Queue: queued batches.
- Setup > Monitoring > Time-Based Workflow: pending time-triggered workflow/flow actions.
- Setup > Monitoring > Scheduled Flows: list of scheduled flows.
- Setup > Event Manager: platform event / CDC configuration and metrics.
