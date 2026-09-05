# Examples — Apex Limits Monitoring

Worked scenarios. The **deployable** versions — `LimitGuard`, `OrgLimitsPoller`,
`Limit_Snapshot__c`, `Limit_Threshold__mdt`, the test class and the manifest — are in
`references/code-examples.md`. The examples here show the reasoning that produces them and
the two artefacts that live outside the org: the CI regression baseline and the debug-log
block you read after the fact.

## Example 1: Guard Clause Pattern in a Service Layer Method

**Context:** A service class method is called from a trigger handler and queries related Account records. The trigger fires in bulk (up to 200 records), and the query inside the method runs per invocation, potentially exhausting the 100 SOQL ceiling in a synchronous context.

**Problem:** Without a guard clause, the method blindly issues a SOQL query. When consumed SOQL approaches 100, the next call throws `System.LimitException`, which is uncatchable, terminating the entire transaction and rolling back all work.

**Solution:**

```apex
public class ContactService {

    // Buffer: stop querying when fewer than 10 SOQL queries remain
    private static final Integer SOQL_SAFETY_BUFFER = 10;

    /**
     * Returns Accounts related to the given Contact IDs.
     * Guard clause prevents LimitException when called in bulk contexts.
     */
    public static Map<Id, Account> getAccountsByContactIds(Set<Id> contactIds) {
        if (contactIds == null || contactIds.isEmpty()) {
            return new Map<Id, Account>();
        }

        // Guard: check remaining SOQL headroom before issuing the query
        Integer soqlRemaining = Limits.getLimitQueries() - Limits.getQueries();
        if (soqlRemaining < SOQL_SAFETY_BUFFER) {
            System.debug(LoggingLevel.WARN,
                'ContactService.getAccountsByContactIds: insufficient SOQL headroom. '
                + 'Remaining: ' + soqlRemaining + '. Returning empty map.');
            return new Map<Id, Account>();
        }

        List<Contact> contacts = [
            SELECT AccountId FROM Contact WHERE Id IN :contactIds
        ];

        Set<Id> accountIds = new Set<Id>();
        for (Contact c : contacts) {
            if (c.AccountId != null) {
                accountIds.add(c.AccountId);
            }
        }

        if (accountIds.isEmpty()) {
            return new Map<Id, Account>();
        }

        // Second guard before the second SOQL
        soqlRemaining = Limits.getLimitQueries() - Limits.getQueries();
        if (soqlRemaining < SOQL_SAFETY_BUFFER) {
            System.debug(LoggingLevel.WARN,
                'ContactService.getAccountsByContactIds: insufficient SOQL headroom '
                + 'before Account query. Remaining: ' + soqlRemaining);
            return new Map<Id, Account>();
        }

        return new Map<Id, Account>([
            SELECT Id, Name, BillingCity FROM Account WHERE Id IN :accountIds
        ]);
    }
}
```

**Why it works:** The guard clause uses `Limits.getLimitQueries()` (not a hardcoded 100) so the check works correctly in both synchronous (100 ceiling) and asynchronous (200 ceiling) contexts. The safety buffer of 10 leaves room for cleanup DML or other queries after this method returns.

---

## Example 2: Batch Scope Sizing Based on Limit Consumption Projection

**Context:** A Batch Apex class re-calculates rollup fields on Opportunity records. Each record in `execute` requires 2 SOQL queries (one for related line items, one for a product lookup) and 1 DML statement.

**Problem:** Using the default scope of 200 with 2 SOQL per record would require 400 SOQL queries in a single `execute` call, exceeding the 200 async ceiling. The batch would fail on every chunk.

**Solution:**

```apex
/**
 * Recalculates Opportunity rollup fields.
 *
 * Scope sizing:
 *   Async SOQL ceiling: 200
 *   Per-record SOQL cost: 2 (OpportunityLineItems query + Product2 lookup)
 *   Max records from SOQL: 200 / 2 = 100
 *   Safety factor: 0.80 → scope = 80
 *
 *   Async DML ceiling: 150 statements
 *   Per-record DML cost: 1 (update Opportunity)
 *   Max records from DML: 150 × 0.80 = 120
 *
 *   Binding constraint: SOQL → scope = 80
 */
public class OpportunityRollupBatch implements Database.Batchable<SObject> {

    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator([
            SELECT Id FROM Opportunity WHERE IsClosed = false
        ]);
    }

    public void execute(Database.BatchableContext bc, List<SObject> scope) {
        List<Opportunity> opps = (List<Opportunity>) scope;
        List<Opportunity> toUpdate = new List<Opportunity>();

        for (Opportunity opp : opps) {
            // Guard inside loop — SOQL check before first per-record query
            if ((Limits.getLimitQueries() - Limits.getQueries()) < 5) {
                System.debug(LoggingLevel.ERROR,
                    'OpportunityRollupBatch.execute: approaching SOQL limit at record '
                    + opp.Id + '. Stopping early.');
                break;
            }

            List<OpportunityLineItem> lines = [
                SELECT UnitPrice, Quantity FROM OpportunityLineItem
                WHERE OpportunityId = :opp.Id
            ];

            // Second guard before product lookup
            if ((Limits.getLimitQueries() - Limits.getQueries()) < 5) {
                break;
            }

            Decimal totalRevenue = 0;
            for (OpportunityLineItem li : lines) {
                totalRevenue += li.UnitPrice * li.Quantity;
            }

            opp.Amount = totalRevenue;
            toUpdate.add(opp);
        }

        if (!toUpdate.isEmpty()) {
            // Guard before DML
            if ((Limits.getLimitDMLStatements() - Limits.getDMLStatements()) >= 1) {
                update toUpdate;
            } else {
                System.debug(LoggingLevel.ERROR,
                    'OpportunityRollupBatch.execute: DML headroom exhausted. '
                    + 'Records not updated: ' + toUpdate.size());
            }
        }
    }

    public void finish(Database.BatchableContext bc) {}
}

// Caller — invoke with calculated scope
Database.executeBatch(new OpportunityRollupBatch(), 80);
```

**Why it works:** The scope of 80 is derived from the binding constraint (SOQL cost × safety factor). The in-loop guard clause provides a second line of defense if actual per-record SOQL consumption is higher than estimated (e.g., due to a separate query added later). Both limits — SOQL and DML — are checked independently.

---

## Example 3: Limit Checkpoint Logging for Observability

**Context:** A high-volume service class processes several phases of work. Developers need to know which phase is consuming the most limit headroom to diagnose performance issues in production.

**Solution:**

```apex
public class OrderFulfillmentService {

    public static void processOrders(List<Order> orders) {
        logLimitCheckpoint('START');

        // Phase 1: validate inventory
        validateInventory(orders);
        logLimitCheckpoint('AFTER_VALIDATE_INVENTORY');

        // Phase 2: allocate stock
        allocateStock(orders);
        logLimitCheckpoint('AFTER_ALLOCATE_STOCK');

        // Phase 3: create shipments
        createShipments(orders);
        logLimitCheckpoint('AFTER_CREATE_SHIPMENTS');
    }

    private static void logLimitCheckpoint(String label) {
        Integer soqlUsed  = Limits.getQueries();
        Integer soqlLimit = Limits.getLimitQueries();
        Integer dmlUsed   = Limits.getDMLStatements();
        Integer dmlLimit  = Limits.getLimitDMLStatements();
        Integer cpuUsed   = Limits.getCpuTime();
        Integer cpuLimit  = Limits.getLimitCpuTime();
        Integer heapUsed  = Limits.getHeapSize();
        Integer heapLimit = Limits.getLimitHeapSize();

        System.debug(LoggingLevel.DEBUG, String.format(
            '[LimitCheckpoint:{0}] SOQL {1}/{2} ({3}%) | DML {4}/{5} ({6}%) | CPU {7}/{8}ms ({9}%) | Heap {10}/{11}B ({12}%)',
            new List<Object>{
                label,
                soqlUsed,  soqlLimit,  (soqlUsed  * 100 / soqlLimit),
                dmlUsed,   dmlLimit,   (dmlUsed   * 100 / dmlLimit),
                cpuUsed,   cpuLimit,   (cpuUsed   * 100 / cpuLimit),
                heapUsed,  heapLimit,  (heapUsed  * 100 / heapLimit)
            }
        ));
    }

    private static void validateInventory(List<Order> orders) { /* ... */ }
    private static void allocateStock(List<Order> orders)      { /* ... */ }
    private static void createShipments(List<Order> orders)    { /* ... */ }
}
```

**Why it works:** Checkpoint logging uses `getLimitX()` for the ceiling rather than hardcoded values, so percentages are correct in both sync and async contexts. Debug logs are written even when the transaction eventually fails, provided they are emitted before the limit breach.

---

## Anti-Pattern: Trying to Catch `System.LimitException`

**What practitioners do:**

```apex
// WRONG — this catch block will never execute on a real limit breach
try {
    List<Account> accounts = [SELECT Id FROM Account WHERE ...];
} catch (System.LimitException le) {
    System.debug('Caught limit exception: ' + le.getMessage());
}
```

**What goes wrong:** `System.LimitException` is not a catchable exception. The Apex runtime terminates the transaction before any `catch` block can run. This code compiles without error but provides zero protection.

**Correct approach:** Use a guard clause checking `Limits.getLimitQueries() - Limits.getQueries()` before the SOQL statement. Prevention, not recovery, is the correct strategy.

---

## Example 4: A CI Limit-Consumption Baseline That Fails the Build on a Regression

**Context:** a refactor adds one query inside a helper called from a trigger handler. Every test still passes — the org has 40 test records, so nothing gets near a ceiling. Six weeks later a customer with 190 records in a batch hits the SOQL wall.

**Problem:** test pass/fail says nothing about consumption. The only per-test-method consumption record the platform keeps is `ApexTestResultLimits`, and it has to be queried deliberately after an asynchronous run (Object Reference, `object_reference L32693–32700`).

**Solution:** commit a baseline of what each test method is allowed to consume, and diff every CI run against it.

`ci/limits-baseline.csv` — committed, reviewed like any other file. Tolerance is per row because a data-heavy test legitimately consumes more than a unit test:

```text
class,method,cpu_max,soql_max,query_rows_max,dml_max,dml_rows_max,tolerance_pct
OrderServiceTest,syncCreatesShipments,1800,14,900,4,220,15
OrderServiceTest,syncHandlesEmptyList,120,1,0,0,0,25
ContactServiceTest,bulkEnrichTwoHundred,4200,9,2400,3,400,10
LimitGuardTest,nearSoqlFlipsOnceTheCeilingIsApproached,900,60,60,0,0,20
```

The query that produces the current run's numbers. `ApexTestRunResultId` scopes it to one run; without that filter the object returns every historical row:

```soql
SELECT ApexTestResult.ApexClass.Name  className,
       ApexTestResult.MethodName      methodName,
       LimitContext, Cpu, Soql, QueryRows, Dml, DmlRows,
       Callouts, Sosl, Email, AsyncCalls, MobilePush, LimitExceptions
FROM   ApexTestResultLimits
WHERE  ApexTestResult.ApexTestRunResultId = '707000000000001'
ORDER  BY Cpu DESC
```

Three preconditions decide whether that query returns anything at all, and all three are easy to break silently: the measured work must sit between `Test.startTest()` and `Test.stopTest()`, the run must be asynchronous, and only the default namespace is captured. A row of zeros means the gate is broken, not that the code got faster.

**Why it works:** the baseline turns an invisible drift into a diff a reviewer reads. `LimitContext` on each row states whether that method ran under synchronous or asynchronous ceilings, so a method that silently moved contexts — a helper promoted into a Queueable, say — shows up as a context change rather than as an unexplained jump in headroom. Heap is not covered: there is no heap column on the object, so a heap regression needs an explicit `Limits.getHeapSize()` assertion inside the test.

---

## Example 5: Reading the Per-Namespace Block After the Fact

**Context:** a save on Account intermittently fails with "Too many SOQL queries: 101", but the code path issues eleven queries and the guard reports plenty of headroom.

**Problem:** `Limits.getQueries()` reports *your namespace's* consumption. A certified managed package in the same transaction has its own 100-query allocation, and the transaction also has a cumulative cross-namespace ceiling (Apex Developer Guide, `apexdev L19666–19680`). The guard is reading one column of a wider table.

**Solution:** capture a debug log at FINEST for the Apex Profiling category and read the `CUMULATIVE_LIMIT_USAGE` block, which prints one `LIMIT_USAGE_FOR_NS` section per namespace. This is the guide's own sample output (`apexdev L38274–38289`):

```text
16:06:58.49 (49590539)|CUMULATIVE_LIMIT_USAGE
16:06:58.49 (49590539)|LIMIT_USAGE_FOR_NS|(default)|
  Number of SOQL queries: 11 out of 100
  Number of query rows: 240 out of 50000
  Number of SOSL queries: 0 out of 20
  Number of DML statements: 3 out of 150
  Number of DML rows: 210 out of 10000
  Maximum CPU time: 1840 out of 10000
  Maximum heap size: 0 out of 6000000
  Number of callouts: 0 out of 100
  Number of Email Invocations: 0 out of 10
  Number of future calls: 0 out of 50
  Number of queueable jobs added to the queue: 0 out of 50
  Number of Mobile Apex push calls: 0 out of 10

16:06:58.49 (49590539)|LIMIT_USAGE_FOR_NS|vendorpkg|
  Number of SOQL queries: 97 out of 100
  Number of query rows: 41200 out of 50000
  Number of DML statements: 2 out of 150

16:06:58.49 (49590539)|CUMULATIVE_LIMIT_USAGE_END
```

Two levels matter when you set the trace flag: `CUMULATIVE_LIMIT_USAGE` is logged at INFO and above (`apexdev L38557–38558`), but `LIMIT_USAGE_FOR_NS` — the per-namespace breakdown that answers this question — needs FINEST on the Apex Profiling category (`apexdev L38930`). A log captured at INFO shows the block boundaries and nothing between them.

Correlate the log to the failing request through `ApexLog.RequestIdentifier`, whose whole purpose is this: "Use this request identifier to correlate multiple debug logs triggered by the same request" (Object Reference, `object_reference L31363–31368`):

```soql
SELECT Id, Operation, Status, DurationMilliseconds, LogLength,
       RequestIdentifier, StartTime, Location
FROM   ApexLog
WHERE  Status != 'Success'
AND    StartTime = LAST_N_HOURS:4
ORDER  BY StartTime DESC
```

`ApexLog` carries no limit columns — `DurationMilliseconds` is wall clock, not CPU — so the numbers only exist inside `LogFile`/the log body. `Location` also tells you how long the row will survive: `Monitoring` logs are "maintained for seven days or until a user deletes them", `SystemLog` logs for 24 hours (`object_reference L31306–31312`).

**Why it works:** it separates "my code is over budget" from "the transaction is over budget", which the `Limits` class alone cannot distinguish. Once the vendor namespace is identified as the consumer, the fix is a sequencing or configuration change in that package's setup, not another guard in your handler.
