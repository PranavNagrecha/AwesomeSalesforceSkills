# LLM Anti-Patterns -- Apex Performance Profiling

Common mistakes AI coding assistants make when generating or advising on Apex performance profiling.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using System.currentTimeMillis Instead Of Limits.getCpuTime

**What the LLM generates:** Instrumentation code using `System.currentTimeMillis()` or `Datetime.now().getTime()` to measure method duration and calculate elapsed time by subtracting timestamps.

**Why it happens:** Java and other languages use wall-clock timestamps for profiling. LLMs default to this familiar pattern. Salesforce Apex has a dedicated `Limits.getCpuTime()` method that measures only Apex CPU consumption, excluding SOQL, DML, and callout wait time.

**Correct pattern:**

```apex
Long cpuBefore = Limits.getCpuTime();
// ... code to profile ...
Long cpuAfter = Limits.getCpuTime();
System.debug(LoggingLevel.WARN, 'CPU cost: ' + (cpuAfter - cpuBefore) + 'ms');
```

**Detection hint:** `currentTimeMillis|Datetime\.now\(\)\.getTime\(\)` in profiling context

---

## Anti-Pattern 2: Recommending JVM Profilers Or APM Tools That Do Not Work On Salesforce

**What the LLM generates:** Suggestions to use JProfiler, VisualVM, New Relic APM agents, or Java Flight Recorder to profile Apex code. Sometimes suggests attaching a debugger or using thread dumps.

**Why it happens:** LLMs trained on general Java performance content suggest JVM-level tools. Salesforce Apex runs on a multi-tenant platform where customers have no access to the JVM, cannot install agents, and cannot attach debuggers.

**Correct pattern:**

```
Use Salesforce-native tools only:
- Apex Log Analyzer (VS Code extension) for flame graphs
- Developer Console Execution Overview for timeline
- Query Plan tool for SOQL analysis
- Limits class methods for checkpoint instrumentation
- Event Monitoring (Shield) for production analytics
```

**Detection hint:** `JProfiler|VisualVM|Flight Recorder|New Relic agent|thread dump|jstack|attach debugger`

---

## Anti-Pattern 3: Suggesting FINEST Logging In Production Without Warning About Overhead

**What the LLM generates:** Instructions to set trace flags at FINEST level for all categories in production to diagnose a performance issue, without mentioning the CPU overhead this adds or the 20 MB log truncation risk.

**Why it happens:** FINEST is the correct level for maximum diagnostic detail. LLMs recommend it without understanding that the observation itself changes the result (Heisenbug) and that production trace flags expire and have overhead implications.

**Correct pattern:**

```
For production profiling:
1. Use Limits checkpoint instrumentation (near-zero overhead)
2. If FINEST is required, set ONLY Apex Code and Database to FINEST
3. Set all other categories to ERROR or NONE
4. Warn that FINEST adds 10-30% CPU overhead
5. Check log for truncation indicator: "*** Skipped N bytes"
6. Consider Event Monitoring as a zero-overhead alternative for aggregate analysis
```

**Detection hint:** `FINEST` recommended without mentioning overhead, truncation, or production risk

---

## Anti-Pattern 4: Claiming Custom Indexes Can Be Created Via Setup UI Or Metadata API

**What the LLM generates:** Instructions to create a custom index on a field through Setup, or by deploying index metadata via Metadata API or SFDX. Sometimes generates fictional `CustomIndex` metadata types.

**Why it happens:** LLMs generalize from standard database concepts where CREATE INDEX is a DBA operation. In Salesforce, custom indexes on standard and custom fields (beyond the automatic ones on Id, Name, RecordTypeId, etc.) must be requested through a Salesforce Support case and are provisioned by Salesforce internally.

**Correct pattern:**

```
Custom index provisioning:
1. Identify the field(s) needing an index via Query Plan analysis
2. Open a case with Salesforce Support requesting a custom index
3. Provide the Query Plan output showing TableScan and high cost
4. Support provisions the index on the production org
5. Custom indexes are NOT transferred during sandbox refresh
6. Re-request indexes for sandbox if needed for testing
```

**Detection hint:** `CREATE INDEX|CustomIndex|deploy.*index|Setup.*index.*field`

---

## Anti-Pattern 5: Ignoring That Limits.getCpuTime Excludes Database And Callout Time

**What the LLM generates:** Profiling code that uses only `Limits.getCpuTime()` and concludes "the transaction uses X ms, which is within the 10,000 ms limit, so there is no performance problem" -- even when the user reports multi-second response times.

**Why it happens:** The LLM correctly identifies `Limits.getCpuTime()` as the Apex profiling method but does not understand that it excludes SOQL execution time, DML commit time, and HTTP callout wait time. A transaction can have 500 ms CPU but 8 seconds of wall-clock time due to slow queries or callouts.

**Correct pattern:**

```apex
// Profile ALL resource dimensions, not just CPU
System.debug(LoggingLevel.WARN, 'PROFILE: ' +
    'CPU=' + Limits.getCpuTime() + '/' + Limits.getLimitCpuTime() + 'ms, ' +
    'SOQL=' + Limits.getQueries() + '/' + Limits.getLimitQueries() + ', ' +
    'SOQLRows=' + Limits.getQueryRows() + '/' + Limits.getLimitQueryRows() + ', ' +
    'DML=' + Limits.getDMLStatements() + '/' + Limits.getLimitDMLStatements() + ', ' +
    'DMLRows=' + Limits.getDMLRows() + '/' + Limits.getLimitDMLRows() + ', ' +
    'Callouts=' + Limits.getCallouts() + '/' + Limits.getLimitCallouts()
);
```

**Detection hint:** Profiling recommendation mentioning only `getCpuTime` without `getQueries` or `getDMLStatements`

---

## Anti-Pattern 6: Hallucinating An Apex Profiler API Or Built-In Profiling Framework

**What the LLM generates:** References to `System.startProfiling()`, `Profiler.trace()`, `@Profile` annotation, `ApexProfiler` class, or similar non-existent APIs. Sometimes invents a `System.getMethodTime()` or `Limits.getMethodCpuTime(String methodName)` method.

**Why it happens:** LLMs generate plausible-sounding API names based on patterns from other languages (Python's cProfile, Java's JFR annotations). No such built-in profiling framework exists in Apex.

**Correct pattern:**

```
Apex has no built-in profiling framework. Available profiling tools:
- Limits.getCpuTime() and other Limits methods (manual checkpoints)
- Debug logs with Apex Log Analyzer (external visualization)
- Developer Console Timeline (built-in but limited)
- Query Plan tool (SOQL-specific)
```

**Detection hint:** `System\.startProfil|Profiler\.|@Profile|ApexProfiler|getMethodTime|getMethodCpu`
