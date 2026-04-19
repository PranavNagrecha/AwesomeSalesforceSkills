# Examples — Apex Limits Monitoring

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
