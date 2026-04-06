# Examples — Record Locking and Contention

## Example 1: Sort-Before-DML in Batch Apex

**Context:** A batch job updates Contacts across many Accounts. When running with a scope of 200, some batches contain Contacts from the same Account that another batch is also processing. The job intermittently fails with UNABLE_TO_LOCK_ROW.

**Problem:** Without sorting, two concurrent batch scopes may lock the same Account rows in different orders, causing deadlocks.

**Solution:**

```apex
public class ContactEnrichmentBatch implements Database.Batchable<SObject> {
    public Database.QueryLocator start(Database.BatchableContext bc) {
        // ORDER BY AccountId ensures each scope groups children by parent
        return Database.getQueryLocator(
            'SELECT Id, AccountId, MailingCity FROM Contact WHERE NeedsEnrichment__c = true ORDER BY AccountId'
        );
    }

    public void execute(Database.BatchableContext bc, List<Contact> scope) {
        // Scope already arrives sorted by AccountId due to ORDER BY in start()
        for (Contact c : scope) {
            c.MailingCity = enrichCity(c);
        }
        update scope;
    }

    public void finish(Database.BatchableContext bc) { }

    private String enrichCity(Contact c) {
        // enrichment logic
        return c.MailingCity;
    }
}
```

**Why it works:** ORDER BY in the start query ensures each scope contains Contacts grouped by Account. Because all concurrent scopes process Accounts in ascending ID order, they never deadlock. Additionally, the grouping reduces the number of distinct parent locks per scope.

---

## Example 2: FOR UPDATE with Minimal Lock Window

**Context:** A service class reads an Inventory__c record, checks available quantity, and decrements it. Two users clicking "Reserve" simultaneously could both read the same quantity and double-decrement.

**Problem:** Without FOR UPDATE, there is a race condition between read and write.

**Solution:**

```apex
public class InventoryService {
    public static void reserveStock(Id inventoryId, Decimal quantity) {
        // Lock the row immediately — other transactions wait here
        Inventory__c inv = [
            SELECT Id, Available_Quantity__c
            FROM Inventory__c
            WHERE Id = :inventoryId
            FOR UPDATE
        ];

        if (inv.Available_Quantity__c < quantity) {
            throw new InsufficientStockException('Only ' + inv.Available_Quantity__c + ' available');
        }

        // Minimal logic between lock acquisition and DML
        inv.Available_Quantity__c -= quantity;
        update inv;
    }
}
```

**Why it works:** FOR UPDATE serializes concurrent access. The key practice is keeping the logic between the FOR UPDATE query and the update DML as short as possible to minimize the lock-hold window.

---

## Example 3: Queueable Retry for Transient Lock Failures

**Context:** A platform-event subscriber processes Order__c records. During peak hours, multiple event batches occasionally contend on the same parent Account records.

**Problem:** The contention is transient and resolves within seconds, but the subscriber fails the entire batch.

**Solution:**

```apex
public class OrderEventHandler implements Queueable {
    private List<Order__c> orders;
    private Integer attempt;
    private static final Integer MAX_RETRIES = 3;

    public OrderEventHandler(List<Order__c> orders, Integer attempt) {
        this.orders = orders;
        this.attempt = attempt;
    }

    public void execute(QueueableContext ctx) {
        try {
            update orders;
        } catch (DmlException e) {
            if (isLockError(e) && attempt < MAX_RETRIES) {
                System.enqueueJob(new OrderEventHandler(orders, attempt + 1));
            } else {
                // Log to custom object for ops review
                insert new Integration_Error__c(
                    Message__c = e.getMessage(),
                    Context__c = 'OrderEventHandler attempt ' + attempt
                );
            }
        }
    }

    private Boolean isLockError(DmlException e) {
        for (Integer i = 0; i < e.getNumDml(); i++) {
            if (e.getDmlType(i) == StatusCode.UNABLE_TO_LOCK_ROW) {
                return true;
            }
        }
        return false;
    }
}
```

**Why it works:** Each Queueable execution runs in a separate transaction with a natural delay, giving the contending transaction time to release its locks. Capping retries prevents infinite chaining.

---

## Anti-Pattern: Wrapping Every DML in FOR UPDATE "Just in Case"

**What practitioners do:** Add FOR UPDATE to every SOQL query to "prevent lock errors," believing it provides safety.

**What goes wrong:** FOR UPDATE acquires locks earlier and holds them longer than necessary. It actually increases contention by widening the lock window. It also fails in Batch Apex (FOR UPDATE is not allowed in batch start queries) and cannot be used with aggregate queries.

**Correct approach:** Use FOR UPDATE only for read-modify-write patterns where two transactions could race on the same row. For most DML, the implicit lock acquired at DML time is sufficient and has the smallest possible window.
