---
name: apex-limits-monitoring
description: "Use this skill when writing Apex that must check governor limits at runtime before executing expensive operations — guard clauses, early-exit patterns, Queueable re-queue on limit approach, and batch scope sizing. Trigger keywords: check governor limits before SOQL apex, defensive coding against limits apex, Limits.getDMLStatements getLimitDMLStatements, Limits class usage, guard clause governor limits, remaining SOQL queries Apex, heap size check before DML, LimitException handling. NOT for limit values themselves — see apex-cpu-and-heap-optimization. NOT for async job design choices — use the async-selection decision tree. NOT for org-level aggregate limit consumption — see architect/org-limits-monitoring."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
triggers:
  - "check governor limits before SOQL apex"
  - "defensive coding against limits apex"
  - "Limits.getDMLStatements getLimitDMLStatements guard clause"
  - "how to avoid System.LimitException in Apex"
  - "Queueable re-queue when approaching CPU limit"
  - "batch scope sizing based on limit consumption"
tags:
  - apex-limits
  - governor-limits
  - defensive-coding
  - limits-class
  - monitoring
inputs:
  - "The Apex class, trigger, or batch class under review"
  - "Expected data volume or iteration count if batch/bulk"
  - "Whether the transaction runs synchronously or asynchronously"
outputs:
  - "Guard clauses inserted before expensive operations (SOQL, DML, heap-intensive work)"
  - "Early-exit and re-queue logic for Queueable jobs nearing the CPU or SOQL ceiling"
  - "Batch scope-size recommendation derived from per-record limit projection"
  - "Observability log statements that report remaining limit headroom as a percentage"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-19
---

# Apex Limits Monitoring

Activate this skill when writing Apex that must stay within Salesforce governor limits at runtime. It covers the `Limits` class API, guard-clause patterns, early-exit and re-queue strategies, and batch scope calculation — all oriented toward defensive coding that prevents a transaction from hitting `System.LimitException`.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the code runs synchronously or asynchronously; ceilings differ (e.g., 100 vs 200 SOQL queries, 10 s vs 60 s CPU).
- Identify the highest-volume code path — that is where limit pressure accumulates, not average paths.
- `System.LimitException` is uncatchable and untestable through try/catch; the transaction terminates before any handler can run. Prevention is the only option.

---

## Core Concepts

### The `Limits` Class — `getX()` / `getLimitX()` Pairs

Every governor limit exposes two methods:

| Method | Returns |
|---|---|
| `Limits.getX()` | Consumed so far in this transaction |
| `Limits.getLimitX()` | Ceiling for this transaction context |

**Key pairs used in defensive coding:**

| Concern | Used | Ceiling |
|---|---|---|
| SOQL queries | `Limits.getQueries()` | `Limits.getLimitQueries()` |
| DML statements | `Limits.getDMLStatements()` | `Limits.getLimitDMLStatements()` |
| DML rows | `Limits.getDMLRows()` | `Limits.getLimitDMLRows()` |
| CPU time (ms) | `Limits.getCpuTime()` | `Limits.getLimitCpuTime()` |
| Heap size (bytes) | `Limits.getHeapSize()` | `Limits.getLimitHeapSize()` |
| Aggregate queries | `Limits.getAggregateQueries()` | `Limits.getLimitAggregateQueries()` |
| Callouts | `Limits.getCallouts()` | `Limits.getLimitCallouts()` |
| Future calls | `Limits.getFutureCalls()` | `Limits.getLimitFutureCalls()` |

Always call the pair: `getX()` tells you current consumption; `getLimitX()` gives the ceiling. Using only `getLimitX()` tells you nothing about current usage.

### Sync vs Async Ceilings

Limits are not the same in all contexts:

| Limit | Synchronous | Asynchronous (Batch, Queueable, Future, Scheduled) |
|---|---|---|
| SOQL queries | 100 | 200 |
| DML statements | 150 | 150 |
| CPU time | 10,000 ms | 60,000 ms |
| Heap size | 6 MB | 12 MB |

Defensive code that works in synchronous tests may not be conservative enough in synchronous production triggers if it assumes async ceilings. Guard clauses must use `Limits.getLimitX()` (which returns the correct ceiling for the current context) rather than hardcoded constants.

### CPU Time and Callouts

CPU time is measured as total Apex execution time excluding time spent waiting on:
- Callout responses (HTTP/web service wait time is not charged to the 10,000 ms CPU limit)
- Database I/O wait

This means `Limits.getCpuTime()` can read low even when wall-clock time is high. Profiling callout-heavy code should supplement `Limits.getCpuTime()` with callout count (`Limits.getCallouts()`).

### `System.LimitException` Is Uncatchable

When any governor limit is exceeded, Salesforce throws `System.LimitException`. This exception:
- Cannot be caught with `try/catch`
- Terminates the entire transaction immediately
- Cannot be logged inside the same transaction (no `catch` block runs)

The only correct strategy is prevention: check limits before the operation, not after.

---

## Common Patterns

### Guard Clause Before Expensive Operation

**When to use:** Any service-layer method that issues SOQL, DML, or heap-intensive work inside a loop or called from multiple code paths.

**How it works:** Compute `remaining = getLimitX() - getX()`. If remaining is below a safe threshold (typically 10% of the ceiling or an absolute floor), either skip the operation, log a warning, or throw an application exception.

**Why not the alternative:** Relying on a try/catch around `System.LimitException` does not work — the exception is uncatchable. A guard clause is the only safe option.

```apex
private static final Integer SOQL_SAFETY_BUFFER = 10;

public static List<Account> fetchRelatedAccounts(Set<Id> contactIds) {
    Integer remaining = Limits.getLimitQueries() - Limits.getQueries();
    if (remaining < SOQL_SAFETY_BUFFER) {
        // Log and return empty — caller must handle gracefully
        System.debug(LoggingLevel.WARN,
            'fetchRelatedAccounts: insufficient SOQL headroom. Remaining: ' + remaining);
        return new List<Account>();
    }
    return [SELECT Id, Name FROM Account WHERE Id IN (
        SELECT AccountId FROM Contact WHERE Id IN :contactIds
    )];
}
```

### Queueable Re-Queue on Limit Approach

**When to use:** Long-running Queueable jobs that process variable-size datasets where hitting the CPU or SOQL ceiling mid-execution is possible.

**How it works:** Inside the `execute` method, check remaining headroom after each batch of records. When headroom falls below a defined threshold, persist a cursor (e.g., the last processed record Id or an offset) and enqueue a new Queueable instance to continue.

```apex
public class AccountProcessorQueueable implements Queueable {
    private List<Id> remainingIds;

    public AccountProcessorQueueable(List<Id> ids) {
        this.remainingIds = ids;
    }

    public void execute(QueueableContext ctx) {
        List<Id> nextBatch = new List<Id>();
        Integer cpuSafetyThreshold = (Integer)(Limits.getLimitCpuTime() * 0.85);

        for (Integer i = 0; i < remainingIds.size(); i++) {
            if (Limits.getCpuTime() >= cpuSafetyThreshold) {
                // Slice remaining work and re-queue
                nextBatch = remainingIds.subList(i, remainingIds.size());
                break;
            }
            processRecord(remainingIds[i]);
        }

        if (!nextBatch.isEmpty() && !Test.isRunningTest()) {
            System.enqueueJob(new AccountProcessorQueueable(nextBatch));
        }
    }

    private void processRecord(Id recordId) {
        // Per-record logic
    }
}
```

### Batch Scope Size Calculation

**When to use:** Designing a new Batch Apex class where the per-record limit consumption is known or estimable.

**How it works:** Estimate the number of SOQL queries or DML operations per record in `execute`. Divide the async SOQL ceiling (200) by the per-record SOQL cost, then apply a safety factor of 0.80 to set the `scope` parameter.

**Example:** If each record costs 2 SOQL queries:
- `200 SOQL / 2 per record = 100 records max`
- Apply 0.80 safety factor: `scope = 80`

This calculation should be documented in a class-level comment and re-validated when the per-record logic changes.

### Observability: Log Remaining Headroom as a Percentage

**When to use:** High-volume service classes and batch execute methods where limit headroom should be visible in debug logs.

```apex
public static void logLimitCheckpoint(String label) {
    Integer soqlUsed = Limits.getQueries();
    Integer soqlLimit = Limits.getLimitQueries();
    Integer dmlUsed = Limits.getDMLStatements();
    Integer dmlLimit = Limits.getLimitDMLStatements();
    Integer cpuUsed = Limits.getCpuTime();
    Integer cpuLimit = Limits.getLimitCpuTime();
    Integer heapUsed = Limits.getHeapSize();
    Integer heapLimit = Limits.getLimitHeapSize();

    System.debug(LoggingLevel.DEBUG, String.format(
        '[LimitCheckpoint:{0}] SOQL {1}/{2} ({3}%) | DML {4}/{5} ({6}%) | CPU {7}/{8}ms ({9}%) | Heap {10}/{11}B ({12}%)',
        new List<Object>{
            label,
            soqlUsed, soqlLimit, (soqlUsed * 100 / soqlLimit),
            dmlUsed, dmlLimit, (dmlUsed * 100 / dmlLimit),
            cpuUsed, cpuLimit, (cpuUsed * 100 / cpuLimit),
            heapUsed, heapLimit, (heapUsed * 100 / heapLimit)
        }
    ));
}
```

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Service method called from trigger, may issue SOQL | Guard clause with `Limits.getQueries()` / `getLimitQueries()` before the query | Prevents LimitException mid-transaction; trigger context has no retry mechanism |
| Queueable job processing variable-size dataset | CPU/SOQL headroom check inside loop + re-queue with cursor | Async CPU ceiling is 60 s but not infinite; re-queue carries no platform cost if Queueable chain depth allows |
| Batch class execute — uncertain per-record SOQL cost | Estimate per-record cost, calculate scope via formula, document in class header | Scope set too high causes batch failures; too low wastes executions |
| Heap-intensive transformation (large collections) | `Limits.getHeapSize()` check before building large in-memory structures | Object graph size is non-obvious; collections of large SObjects can consume MB quickly |
| Need to observe limit consumption across environments | `logLimitCheckpoint` after each major processing phase | Debug logs are the only in-transaction observability mechanism |
| Determining whether to use sync vs async | Use async-selection decision tree in `standards/decision-trees/async-selection.md` | This skill covers defensive coding, not job-type selection |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner writing or reviewing Apex for limit safety:

1. **Identify the transaction context** — synchronous (trigger, VF controller, REST endpoint) or asynchronous (Batch, Queueable, Future, Scheduled). Look up the correct ceilings using `Limits.getLimitX()` at runtime rather than hardcoding constants.
2. **Locate high-volume code paths** — find every loop, recursive call, or fan-out method. These are where limit consumption compounds. Mark each SOQL query and DML statement inside or called from a loop.
3. **Insert guard clauses** — before each SOQL or DML inside or near a loop, add a remaining-headroom check. Use a safety buffer (10% of ceiling or an absolute floor of 10 operations) to leave room for post-loop cleanup DML.
4. **Design re-queue logic for Queueable jobs** — if the job processes a variable-length list, add a CPU/SOQL headroom check inside the iteration loop. On breach of threshold, slice the unprocessed tail and enqueue a new instance.
5. **Size Batch scope defensively** — estimate per-record SOQL and DML consumption in `execute`. Divide the async ceiling by the per-record cost and apply 0.80 safety factor. Document the formula in the class header comment.
6. **Add checkpoint logging** — insert `logLimitCheckpoint` calls after major phases in high-volume code to make limit consumption visible in debug logs.
7. **Validate with bulk test data** — run Apex tests with 200+ record datasets to exercise bulk code paths. Use `Test.startTest()` / `Test.stopTest()` to reset limit counters and isolate the unit under test.

---

## Review Checklist

- [ ] Every SOQL query inside or called from a loop has a guard clause checking `Limits.getQueries()` vs `Limits.getLimitQueries()`
- [ ] Every DML statement inside or called from a loop has a guard clause checking `Limits.getDMLStatements()` vs `Limits.getLimitDMLStatements()`
- [ ] No hardcoded limit constants — all ceilings come from `Limits.getLimitX()` at runtime
- [ ] Queueable jobs that process variable-length datasets implement re-queue logic with a CPU/SOQL threshold
- [ ] Batch `execute` scope size is documented with the per-record cost formula
- [ ] No `try/catch(System.LimitException)` blocks — they cannot catch this exception
- [ ] Checkpoint log statements are present in high-volume service methods
- [ ] Apex tests use 200+ records to exercise bulk code paths

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`System.LimitException` is uncatchable** — Unlike most exceptions, `System.LimitException` cannot be caught. The transaction terminates before any `catch` block executes. Code like `try { ... } catch (System.LimitException e) { ... }` compiles but the catch block never runs on a real limit breach.

2. **Heap check must account for object graph, not just primitives** — `Limits.getHeapSize()` measures the full object graph stored in memory, including nested SObject fields, collections, and string values. A `List<Account>` with 10,000 records and five populated text fields can easily consume several MB. Checking heap only at the top of a method understates consumption if nested objects are populated inside the loop.

3. **DML statements vs DML rows confusion** — `Limits.getDMLStatements()` counts the number of DML calls (insert, update, delete, etc.), not the number of records affected. `Limits.getDMLRows()` counts the total records across all DML calls. Bulkifying DML reduces statement count but not row count. Both limits apply independently.

4. **CPU time excludes callout wait time** — `Limits.getCpuTime()` does not include time waiting for external HTTP callout responses. Code with heavy callout I/O can have low CPU time but still be slow. However, callout count is separately limited (`Limits.getCallouts()` / `Limits.getLimitCallouts()` = 100 per transaction).

5. **Aggregate queries count against their own limit** — SOQL aggregate queries (those with `COUNT()`, `SUM()`, `GROUP BY`, etc.) count against `Limits.getAggregateQueries()` / `Limits.getLimitAggregateQueries()` (300 per transaction), which is separate from the standard SOQL query limit. Monitoring only `Limits.getQueries()` misses aggregate query consumption.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Guard-clause Apex snippet | A reusable pattern checking SOQL/DML/heap headroom before an expensive operation, ready to paste into a service class |
| Queueable re-queue pattern | A Queueable `execute` implementation with CPU/SOQL headroom check and cursor-based re-queue logic |
| Batch scope size recommendation | A numeric scope value derived from the per-record limit cost formula, documented with the calculation |
| `logLimitCheckpoint` utility method | A debug-logging method that reports all key limits as percentage consumed |

---

## Related Skills

- `apex/apex-cpu-and-heap-optimization` — covers techniques for reducing CPU and heap consumption; this skill covers monitoring and guarding against limits, not optimization
- `apex/apex-batch-chaining` — covers chaining multiple Batch Apex jobs; use alongside this skill when sizing per-batch scope
- `architect/org-limits-monitoring` — covers org-level aggregate limit visibility via `OrgLimits` class and monitoring dashboards; this skill covers per-transaction runtime defensive coding
- Decision tree: `standards/decision-trees/async-selection.md` — use before deciding which async mechanism to employ
