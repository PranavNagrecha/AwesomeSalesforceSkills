---
name: apex-performance-profiling
description: "Use when diagnosing where Apex transactions spend CPU, heap, SOQL, or DML time using the Salesforce diagnostic toolchain: Apex Log Analyzer flame graphs in VS Code, Developer Console execution timeline, SOQL Query Plan tool, and Limits-class checkpoint instrumentation. Triggers: 'why is my Apex slow', 'flame graph Apex', 'profile Apex transaction', 'Query Plan tool', 'Apex Log Analyzer'. NOT for fixing specific CPU or heap patterns after the hotspot is found (use apex-cpu-and-heap-optimization), NOT for debug log setup or trace flag mechanics (use debug-logs-and-developer-console), and NOT for SOQL query rewriting (use soql-query-optimization)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Operational Excellence
tags:
  - apex-performance-profiling
  - flame-graph
  - query-plan
  - apex-log-analyzer
  - execution-timeline
  - profiling
triggers:
  - "why is my Apex transaction slow and how do I find the bottleneck"
  - "how to use the Apex Log Analyzer flame graph in VS Code"
  - "how to read the Developer Console execution timeline for performance"
  - "SOQL Query Plan tool shows TableScan — what does that mean"
  - "how to instrument Apex code with Limits checkpoints for profiling"
inputs:
  - "debug log from the slow transaction (FINEST Apex level preferred)"
  - "whether the slowness is user-facing (sync) or background (async/batch)"
  - "approximate data volume and object graph complexity"
outputs:
  - "identified hotspot location with method, line, and time attribution"
  - "SOQL Query Plan analysis with index recommendations"
  - "profiling instrumentation code for ongoing measurement"
  - "prioritized list of optimization targets ranked by time or resource cost"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Apex Performance Profiling

Use this skill when an Apex transaction is slow or approaching governor limits and the developer needs to identify where time and resources are being consumed before attempting fixes. This skill covers the diagnostic toolchain and profiling methodology — finding the hotspot — not the optimization patterns applied after the hotspot is found.

---

## Before Starting

Gather this context before working on anything in this domain:

- Do you have a debug log captured at FINEST Apex log level for the slow transaction? If not, capture one first (see debug-logs-and-developer-console).
- Is the slowness in a synchronous user transaction (10,000 ms CPU limit) or an async context like batch/queueable (60,000 ms CPU limit)?
- Is the problem CPU time, SOQL query count/rows, DML operations, or wall-clock time from callouts? The profiling approach differs for each.

---

## Core Concepts

### Debug Logs Are The Raw Profiling Data

Every Apex profiling workflow starts with a debug log. The log contains timestamped entries for every method entry/exit, SOQL execution, DML operation, and governor limit consumption. The log must be captured at FINEST level for Apex Code and Database categories to get method-level timing. Logs truncate at 20 MB; if a log is truncated, reduce other log categories (Workflow, Validation, System) to NONE or ERROR to preserve Apex and Database detail.

### Apex Log Analyzer Renders Flame Graphs From Debug Logs

The Apex Log Analyzer extension for VS Code parses debug logs and renders interactive flame graphs showing the call tree with time attribution down to 0.001 ms precision. Each bar in the flame graph represents a method invocation; width encodes duration. SOQL and DML operations appear as distinct colored nodes in the call tree, making it immediately visible whether time is spent in Apex computation or database operations. This is the single most effective tool for identifying Apex performance bottlenecks.

### The Developer Console Execution Overview Shows Timeline

The Developer Console's Execution Overview tab provides a timeline view showing Apex execution, database operations, and workflow processing as horizontal bars on a time axis. While less precise than the Apex Log Analyzer flame graph, it is available without installing any extension and can quickly reveal whether a transaction is dominated by Apex processing, SOQL, DML, or workflow/flow execution. The Timeline tab shows cumulative governor limit consumption over the transaction.

### SOQL Query Plan Reveals Index Usage

The Query Plan tool in the Developer Console (or via the REST API at `/services/data/vXX.0/query?explain=<soql>`) returns the execution plan for a SOQL query. It shows the leading operation type (TableScan, IndexScan, or SharingIndex), the estimated cost (where cost below 1.0 generally indicates an indexed path), and which fields could be indexed to improve the plan. A TableScan on a table with more than 100,000 records is almost always a performance problem.

---

## Common Patterns

### Pattern 1: Flame Graph Analysis With Apex Log Analyzer

**When to use:** A transaction is slow and you need to find exactly which method or operation consumes the most time.

**How it works:**

1. Capture a debug log at FINEST Apex Code level for the transaction.
2. Open the log in VS Code with the Apex Log Analyzer extension installed.
3. Switch to the flame graph view. The widest bars at the bottom of the graph represent the most time-consuming methods.
4. Click a bar to see its exact duration, SOQL count, and DML count.
5. Look for repeated narrow bars that sum to significant time — these indicate a method called many times inside a loop.
6. Identify whether the hotspot is Apex computation (method body time) or database (SOQL/DML child nodes).

**Why not the alternative:** Reading raw debug log text is error-prone for complex transactions because method entry/exit pairs can span thousands of lines. The flame graph collapses this into a visual hierarchy where the biggest cost is immediately visible.

### Pattern 2: Limits Checkpoint Instrumentation

**When to use:** You need to measure performance in production-like conditions without the overhead of FINEST logging, or you want to add permanent instrumentation to track regression.

**How it works:**

```apex
public class OrderProcessor {
    public static void processOrders(List<Order> orders) {
        Long cpuStart = Limits.getCpuTime();
        Integer queriesBefore = Limits.getQueries();

        // --- Phase 1: Validation ---
        validateOrders(orders);
        System.debug(LoggingLevel.WARN,
            'PROFILING Phase1-Validate: CPU=' +
            (Limits.getCpuTime() - cpuStart) + 'ms, ' +
            'SOQL=' + (Limits.getQueries() - queriesBefore));

        // --- Phase 2: Enrichment ---
        Long phase2Start = Limits.getCpuTime();
        Integer phase2Queries = Limits.getQueries();
        enrichOrders(orders);
        System.debug(LoggingLevel.WARN,
            'PROFILING Phase2-Enrich: CPU=' +
            (Limits.getCpuTime() - phase2Start) + 'ms, ' +
            'SOQL=' + (Limits.getQueries() - phase2Queries));

        // --- Phase 3: Commit ---
        Long phase3Start = Limits.getCpuTime();
        Integer phase3DML = Limits.getDMLStatements();
        commitOrders(orders);
        System.debug(LoggingLevel.WARN,
            'PROFILING Phase3-Commit: CPU=' +
            (Limits.getCpuTime() - phase3Start) + 'ms, ' +
            'DML=' + (Limits.getDMLStatements() - phase3DML));
    }
}
```

**Why not the alternative:** Flame graphs require FINEST-level logging which adds overhead and may truncate in complex transactions. Limits checkpoints work at any log level and can stay in code as lightweight permanent instrumentation.

### Pattern 3: SOQL Query Plan Analysis

**When to use:** A SOQL query is returning correct results but is slow, especially on objects with more than 100,000 records.

**How it works:**

1. Open the Developer Console and enable the Query Plan tool (Help > Preferences > Enable Query Plan).
2. Paste the SOQL query into the Query Editor and click Query Plan (not Execute).
3. Review the plan output:
   - **Leading Operation Type:** TableScan means no index is used; Index means a custom or standard index is being used.
   - **Cost:** Values below 1.0 generally indicate acceptable plans. Values above 1.0 indicate the optimizer chose a table scan.
   - **Cardinality:** The estimated number of rows the operation will process.
   - **sObjectCardinality:** The total number of records in the table.
4. If the plan shows TableScan with high cost, check whether a custom index on the WHERE clause fields would help. Request custom indexes from Salesforce Support for production orgs.

**Why not the alternative:** Running EXPLAIN via the REST API (`/services/data/vXX.0/query?explain=`) returns the same data programmatically and can be automated, but the Developer Console approach is faster for ad-hoc investigation.

---

## Decision Guidance

| Situation | Recommended Tool | Reason |
|---|---|---|
| Transaction is slow; unknown cause | Apex Log Analyzer flame graph | Visual call tree makes the biggest cost immediately obvious |
| Need to compare performance before/after a code change | Limits checkpoint instrumentation | Produces repeatable numeric measurements at any log level |
| SOQL query is suspected bottleneck on large table | Query Plan tool | Shows whether indexes are used and estimates scan cost |
| Transaction involves triggers on multiple objects | Developer Console Timeline | Shows Apex vs. workflow vs. flow time on a single axis |
| Production performance regression | Limits checkpoints + Event Monitoring | FINEST logging in production is too risky; lightweight instrumentation plus Event Monitoring is safer |
| Complex async chain (queueable chaining or batch) | Apex Log Analyzer on each job's log | Each async execution gets its own log and its own governor context |

---

## Recommended Workflow

Step-by-step instructions for profiling an Apex performance problem:

1. **Reproduce and capture** -- Set trace flags at FINEST for Apex Code and Database, reduce other categories to ERROR, then trigger the slow transaction. Download the debug log.
2. **Visualize the call tree** -- Open the log in Apex Log Analyzer (VS Code) or the Developer Console Timeline. Identify the top 1-3 methods or operations consuming the most time.
3. **Classify the hotspot** -- Determine whether the bottleneck is Apex CPU (method body time), SOQL (query execution time or query count), DML (row count or lock contention), or callout (HTTP wait time).
4. **Analyze query plans for SOQL hotspots** -- If SOQL is the bottleneck, run the Query Plan tool on each expensive query. Check for TableScan on large objects and missing indexes.
5. **Instrument with Limits checkpoints** -- Add `Limits.getCpuTime()` and `Limits.getQueries()` checkpoints around the hotspot to establish a numeric baseline before optimizing.
6. **Optimize and re-measure** -- Apply the appropriate fix (see apex-cpu-and-heap-optimization or soql-query-optimization) and re-run the instrumented transaction. Compare checkpoint values to confirm improvement.
7. **Decide on permanent instrumentation** -- For business-critical transactions, leave lightweight `Limits` checkpoints in place with `LoggingLevel.WARN` so future regressions are detectable without FINEST logging.

---

## Review Checklist

Run through these before marking profiling work complete:

- [ ] Debug log was captured at FINEST Apex Code level and is not truncated
- [ ] Flame graph or timeline was reviewed; top hotspot is identified with specific method and line
- [ ] SOQL Query Plan was checked for any query on an object with more than 10,000 records
- [ ] Limits checkpoint instrumentation is in place around the hotspot with before/after measurements
- [ ] Optimization was verified by comparing checkpoint values before and after the fix
- [ ] Permanent instrumentation decision was made: keep lightweight checkpoints or remove profiling code

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Debug log truncation hides the bottleneck** -- Logs truncate at 20 MB. A FINEST-level log for a complex transaction often exceeds this limit. When the log is truncated, the flame graph is incomplete and may not show the actual hotspot. Reduce non-essential log categories to ERROR and keep only Apex Code and Database at FINEST.
2. **FINEST logging itself adds CPU overhead** -- Capturing a debug log at FINEST level adds measurable CPU time to the transaction (sometimes 10-30% overhead). A transaction that passes in production may fail the CPU limit when profiled. Use Limits checkpoints as a complementary approach that adds negligible overhead.
3. **Query Plan cost thresholds differ from optimizer behavior** -- The Query Plan tool shows estimated cost, but the actual optimizer threshold for using a custom index varies. A cost of 0.9 does not guarantee an index scan in production; Salesforce may still choose a table scan based on data distribution and selectivity. Custom indexes require a support case and are not self-service.
4. **Async contexts reset governor limits but not Limits class behavior** -- Each async execution (batch execute, queueable run) gets fresh governor limits. Profiling a batch job means analyzing each `execute()` invocation's log separately. The overall batch elapsed time is not visible in any single debug log.
5. **Managed package code is hidden in logs** -- Methods inside managed packages appear as namespace-prefixed entries in the debug log but their internal implementation is not expanded. The flame graph shows time attributed to the managed package call but cannot drill into it. If a managed package method is the hotspot, the only option is to reduce call frequency or contact the ISV.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Profiling report | Summary of hotspots found, with method names, line numbers, time attribution, and SOQL/DML counts |
| Query Plan analysis | For each expensive SOQL query: leading operation type, cost, cardinality, and index recommendation |
| Instrumented code | Apex class with Limits checkpoint instrumentation around performance-critical sections |
| Before/after comparison | Numeric comparison of CPU time, SOQL count, and DML count before and after optimization |

---

## Related Skills

- apex-cpu-and-heap-optimization -- Use after profiling to apply specific CPU and heap fix patterns to identified hotspots
- debug-logs-and-developer-console -- Use for debug log setup, trace flag configuration, and Apex Replay Debugger mechanics
- soql-query-optimization -- Use when the profiling bottleneck is a specific SOQL query that needs rewriting or indexing
- governor-limits -- Use for understanding the full set of governor limits and general limit avoidance strategy

---

## Official Sources Used

- Apex Developer Guide -- Execution Governors and Limits: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Apex Developer Guide -- Apex Debugging: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_debugging.htm
- Apex Reference Guide -- Limits Class: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_limits.htm
- Salesforce Well-Architected -- Performance: https://architect.salesforce.com/well-architected/performant
- SOQL and SOSL Reference -- Query Plan Tool: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_query_plan.htm
