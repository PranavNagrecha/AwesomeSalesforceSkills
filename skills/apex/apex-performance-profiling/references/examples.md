# Examples -- Apex Performance Profiling

## Example 1: Flame Graph Reveals Trigger Handler As Bottleneck

**Context:** A custom Account trigger fires on bulk updates from a data loader. Users report that loads of 200 records take over 30 seconds and occasionally hit the CPU time limit.

**Problem:** Without profiling, the developer guesses that SOQL queries are the bottleneck and spends time optimizing queries that turn out to be fast. The actual bottleneck is a utility method called inside a nested loop in the trigger handler.

**Solution:**

1. Set a trace flag on the running user at FINEST for Apex Code and Database, ERROR for everything else.
2. Run a data loader update of 200 Account records.
3. Download the debug log from Setup > Debug Logs.
4. Open the log in VS Code with Apex Log Analyzer. The flame graph shows:
   - `AccountTriggerHandler.handleAfterUpdate` -- 8,200 ms total
   - `AccountTriggerHandler.enrichAccounts` -- 7,900 ms (nested call)
   - `FieldMappingUtil.resolveMapping` -- called 40,000 times (200 records x 200 field mappings), 7,500 ms total

**Why it works:** The flame graph immediately shows that `resolveMapping` is called 40,000 times. Each call is only 0.19 ms, so it would not stand out in a raw log scan. But the aggregate 7,500 ms dominates the transaction. The fix is to refactor `resolveMapping` to accept a batch of records instead of being called per-field-per-record.

---

## Example 2: SOQL Query Plan Identifies Missing Custom Index

**Context:** A Visualforce page loads Opportunity records filtered by a custom field `Region__c` with a WHERE clause. The page is fast in sandbox (5,000 Opportunities) but takes 8 seconds in production (800,000 Opportunities).

**Problem:** The SOQL query returns only 50 rows but scans 800,000 records because `Region__c` is not indexed.

**Solution:**

1. Open the Developer Console in production (or a full sandbox).
2. Enable Query Plan (Help > Preferences > Enable Query Plan).
3. Enter the query:
```sql
SELECT Id, Name, Amount, CloseDate FROM Opportunity WHERE Region__c = 'EMEA' AND StageName = 'Closed Won' LIMIT 50
```
4. Click "Query Plan". The result shows:
   - Leading Operation: TableScan
   - Cost: 4.2
   - Cardinality: 800,000
   - Notes: "No applicable index found for Region__c"
5. Open a Salesforce Support case requesting a custom index on `Opportunity.Region__c`.
6. After the index is provisioned, re-run the Query Plan:
   - Leading Operation: Index
   - Cost: 0.003
   - Cardinality: 1,200

**Why it works:** The Query Plan tool reveals that the optimizer is forced into a table scan. Without it, the developer might assume the query itself is the problem and try rewriting SOQL that is already correct. The real fix is an index, not a query change.

---

## Example 3: Limits Checkpoints Isolate Phase-Level Cost In A Complex Transaction

**Context:** An Order processing class runs through validation, enrichment, pricing, and commit phases. The transaction occasionally fails with "Apex CPU time limit exceeded" but the developer does not know which phase is expensive.

**Problem:** Capturing a FINEST debug log adds enough overhead that the transaction always fails when profiled. The developer needs a lightweight alternative.

**Solution:**

```apex
public class OrderProcessor {
    public static void process(List<Order> orders) {
        Map<String, Long> cpuProfile = new Map<String, Long>();
        Map<String, Integer> soqlProfile = new Map<String, Integer>();

        Long cpuMark = Limits.getCpuTime();
        Integer soqlMark = Limits.getQueries();

        validateOrders(orders);
        cpuProfile.put('1-Validate', Limits.getCpuTime() - cpuMark);
        soqlProfile.put('1-Validate', Limits.getQueries() - soqlMark);

        cpuMark = Limits.getCpuTime();
        soqlMark = Limits.getQueries();
        enrichOrders(orders);
        cpuProfile.put('2-Enrich', Limits.getCpuTime() - cpuMark);
        soqlProfile.put('2-Enrich', Limits.getQueries() - soqlMark);

        cpuMark = Limits.getCpuTime();
        soqlMark = Limits.getQueries();
        calculatePricing(orders);
        cpuProfile.put('3-Price', Limits.getCpuTime() - cpuMark);
        soqlProfile.put('3-Price', Limits.getQueries() - soqlMark);

        cpuMark = Limits.getCpuTime();
        Integer dmlMark = Limits.getDMLStatements();
        commitOrders(orders);
        cpuProfile.put('4-Commit', Limits.getCpuTime() - cpuMark);

        System.debug(LoggingLevel.WARN,
            'PROFILING OrderProcessor CPU=' + cpuProfile +
            ' SOQL=' + soqlProfile +
            ' TotalCPU=' + Limits.getCpuTime() + '/' + Limits.getLimitCpuTime());
    }
}
```

Output in log at WARN level:
```
PROFILING OrderProcessor CPU={1-Validate=120, 2-Enrich=6800, 3-Price=2100, 4-Commit=340} SOQL={1-Validate=2, 2-Enrich=15, 3-Price=8} TotalCPU=9360/10000
```

**Why it works:** The profiling output immediately shows that phase 2 (Enrich) consumes 6,800 ms of 10,000 ms available. The developer now knows exactly where to focus optimization effort, and this instrumentation adds less than 1 ms of overhead compared to the 10-30% overhead of FINEST logging.

---

## Anti-Pattern: Profiling By Adding System.debug Everywhere

**What practitioners do:** When a transaction is slow, the developer adds `System.debug('TIMING: ' + System.currentTimeMillis())` statements throughout the code and tries to calculate durations by subtracting timestamps from the raw log.

**What goes wrong:** `System.currentTimeMillis()` measures wall-clock time, not CPU time. It includes time waiting for SOQL, DML, and callouts, making it impossible to distinguish Apex compute cost from database cost. Additionally, excessive `System.debug` calls themselves consume CPU time and heap, distorting the measurement.

**Correct approach:** Use `Limits.getCpuTime()` for CPU-specific measurement and `Limits.getQueries()` / `Limits.getDMLStatements()` for database operations. Use the Apex Log Analyzer flame graph for visual call-tree analysis rather than manually parsing log timestamps.
