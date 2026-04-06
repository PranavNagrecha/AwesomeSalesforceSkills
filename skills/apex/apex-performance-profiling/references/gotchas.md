# Gotchas -- Apex Performance Profiling

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Log Truncation Silently Hides The Most Expensive Code

**What happens:** Debug logs are capped at 20 MB. In complex transactions with FINEST logging, the log often truncates before the most expensive operations are recorded. The Apex Log Analyzer flame graph appears complete but is actually missing the tail of the transaction, which may contain the real hotspot.

**When it occurs:** Transactions with many trigger invocations, flow executions, or large record sets at FINEST log level. Batch jobs with complex execute methods are especially prone.

**How to avoid:** Set only Apex Code and Database to FINEST; set all other categories (Workflow, Validation, System, Visualforce, Callout) to ERROR or NONE. Check the final line of the log for `*** Skipped N bytes of detailed log` which indicates truncation. If truncation persists, use Limits checkpoint instrumentation instead.

---

## Gotcha 2: FINEST Logging Overhead Causes Tests To Fail That Pass In Production

**What happens:** Capturing a debug log at FINEST level adds 10-30% CPU overhead because the platform serializes every method entry, exit, variable assignment, and limit checkpoint into the log buffer. A transaction that uses 8,500 ms of CPU time in production may consume 10,500 ms when profiled, causing a `System.LimitException` that does not occur in normal operation.

**When it occurs:** Any transaction that is already within 20-30% of the CPU limit. The profiling itself pushes it over the edge, creating a Heisenbug that only appears during observation.

**How to avoid:** Use Limits checkpoint instrumentation (which adds negligible overhead) as the primary profiling tool for transactions near the CPU limit. Use FINEST logging only for transactions that have significant headroom. If you must profile a near-limit transaction, reduce the batch size or input data to create breathing room.

---

## Gotcha 3: Query Plan Results Differ Between Sandbox And Production

**What happens:** The SOQL Query Plan tool bases its cost estimates on actual data distribution and table cardinality. A query that shows a low-cost index scan in sandbox (1,000 records) may show a high-cost table scan in production (500,000 records) because custom indexes may not exist in sandbox, or data selectivity ratios differ.

**When it occurs:** When developers rely on sandbox Query Plan results to validate production SOQL performance. Also after sandbox refresh, if custom indexes were not re-provisioned.

**How to avoid:** Always run Query Plan analysis against production or a full-copy sandbox that mirrors production data volume. Remember that custom indexes must be explicitly requested from Salesforce Support for each org and are not transferred during sandbox refresh.

---

## Gotcha 4: Managed Package Code Appears As A Black Box In Flame Graphs

**What happens:** Methods inside installed managed packages show as a single collapsed entry in the debug log and flame graph. The log shows the namespace-prefixed method call and its total duration, but no internal breakdown. If a managed package method is the bottleneck, the flame graph correctly attributes time to it but cannot reveal which internal logic is slow.

**When it occurs:** Any org with installed AppExchange packages or ISV integrations that participate in triggers, flows, or invocable actions.

**How to avoid:** If a managed package method consumes significant time, reduce how often it is called (e.g., bulkify the input, filter records before calling, or move the invocation to async). Contact the ISV with your profiling data showing the time attribution. There is no way to profile inside managed package code from outside the namespace.

---

## Gotcha 5: Limits.getCpuTime Does Not Include Database Time

**What happens:** `Limits.getCpuTime()` measures only Apex execution time. It does not include time spent executing SOQL queries, DML operations, or waiting for callout responses. A transaction that takes 15 seconds wall-clock but only 2,000 ms of CPU time has a database or callout bottleneck, not an Apex compute bottleneck.

**When it occurs:** When developers use only `Limits.getCpuTime()` checkpoints and conclude there is no performance problem because CPU time is low, while the user experiences multi-second page loads due to slow queries or lock contention.

**How to avoid:** Profile database cost separately using `Limits.getQueries()`, `Limits.getQueryRows()`, and `Limits.getDMLStatements()`. Use the Apex Log Analyzer flame graph which visually separates Apex method time from SOQL/DML time. For callout bottlenecks, check `Limits.getCallouts()` and the callout response time shown in the debug log.
