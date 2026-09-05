# Examples — Apex Collections Patterns

## Example 1: Bulkified After-Insert Trigger Using Map<Id, List<SObject>>

**Context:** An after-insert trigger on `OrderItem__c` must stamp a count of line items onto the parent `Order__c`. The Order can receive up to 200 new OrderItems in a single transaction from a CSV import or API bulk load.

**Problem:** Without a collection pattern, the trigger queries the parent inside the for loop, burning one SOQL per record and hitting the 100-query governor limit at 101 records.

**Solution:**

```apex
// In OrderItemTriggerHandler.afterInsert() — see templates/apex/TriggerHandler.cls for handler scaffold

public override void afterInsert() {
    // 1. Collect parent Ids — Set de-duplicates automatically
    Set<Id> orderIds = new Set<Id>();
    for (OrderItem__c item : (List<OrderItem__c>) Trigger.new) {
        if (item.Order__c != null) {
            orderIds.add(item.Order__c);
        }
    }

    if (orderIds.isEmpty()) { return; }

    // 2. Single SOQL — all related items for every parent at once
    Map<Id, List<OrderItem__c>> itemsByOrder = new Map<Id, List<OrderItem__c>>();
    for (OrderItem__c item : [
        SELECT Id, Order__c
        FROM OrderItem__c
        WHERE Order__c IN :orderIds
    ]) {
        if (!itemsByOrder.containsKey(item.Order__c)) {
            // Initialize the inner List only when the key is absent
            itemsByOrder.put(item.Order__c, new List<OrderItem__c>());
        }
        itemsByOrder.get(item.Order__c).add(item);
    }

    // 3. Build update list — no additional SOQL in the loop
    List<Order__c> ordersToUpdate = new List<Order__c>();
    for (Id orderId : orderIds) {
        List<OrderItem__c> items = itemsByOrder.get(orderId);
        Integer count = (items != null) ? items.size() : 0;  // null-safe get
        ordersToUpdate.add(new Order__c(
            Id = orderId,
            Item_Count__c = count
        ));
    }

    // 4. Single bulk DML outside all loops
    update ordersToUpdate;
}
```

**Why it works:** The SOQL and DML each execute exactly once regardless of how many OrderItems are in `Trigger.new`, staying inside the 100 synchronous SOQL queries a transaction is allowed (`apexdev` L19544). The `containsKey` guard prevents overwriting an initialized List, and the `items != null` check at retrieval handles keys that may not be in the result map (e.g., orders with zero existing items after deletion).

---

## Example 2: Safe Set Intersection to Filter Out Excluded Records

**Context:** A service class processes a batch of Account Ids passed in from an integration. Some accounts are on a "do not process" exclusion list stored in a Custom Metadata type. The service must skip excluded accounts without iterating every Id.

**Problem:** An LLM typically generates a nested loop: for each incoming Id, iterate the exclusion list to check membership — O(n×m) time, and allocates no useful collection structure.

**Solution:**

```apex
public static List<Id> filterExcluded(List<Id> incomingIds, Set<Id> excludedIds) {
    // Work on a copy so the caller's Set is not mutated
    Set<Id> workingSet = new Set<Id>(incomingIds);  // de-duplicate at the same time

    // Remove excluded Ids in a single platform operation — O(n) not O(n*m)
    workingSet.removeAll(excludedIds);

    return new List<Id>(workingSet);
}

// ---- Caller ----
Set<Id> excluded = new Set<Id>();
for (Do_Not_Process__mdt rule : [
    SELECT Account_Id__c FROM Do_Not_Process__mdt WHERE Is_Active__c = true
]) {
    excluded.add((Id) rule.Account_Id__c);
}

List<Id> safeIds = filterExcluded(new List<Id>(Trigger.newMap.keySet()), excluded);
// safeIds contains only Ids not in the exclusion list
```

**Why it works:** `Set.removeAll()` is a single platform call implemented in native code. The method receives a copy of the incoming Ids, so the trigger's `Trigger.newMap.keySet()` is never mutated. The Custom Metadata query runs once before the loop, not inside it.

---

## Anti-Pattern: Unbounded Map Accumulation in Database.Stateful Batch

**What practitioners do:** Declare a `Map<Id, List<SObject>>` as an instance field in a `Database.Stateful` batch class and append records to it during every `execute()` chunk, intending to process them all at once in `finish()`.

**What goes wrong:** The map grows with each of the (up to) 500 `execute()` chunks. For a 200-scope batch over 100,000 records, the map accumulates all 100,000 records before `finish()` runs. Batch Apex runs against the asynchronous ceiling of 12 MB total heap (`apexdev` L19577), and the per-transaction counters that reset for each `execute` (`apexdev` L19530–L19531) do not shrink the retained map. Breaching the ceiling raises `System.LimitException` — the exception "the runtime throws if a governor limit such as heap" is exceeded (`apexdev` L39724) — and it is uncatchable (`apexdev` L17856), so the whole job fails with no partial recovery.

**Correct approach:** Flush accumulated data to Salesforce records or Platform Events at the end of each `execute()` chunk. Reserve `Database.Stateful` instance fields for lightweight counters (integers, small Sets of failure Ids) rather than growing collections.

```apex
// WRONG — accumulates all records before finish()
public class SummaryBatch implements Database.Batchable<SObject>, Database.Stateful {
    public Map<Id, List<Case>> casesByAccount = new Map<Id, List<Case>>();  // grows unboundedly

    public void execute(Database.BatchableContext bc, List<Account> scope) {
        for (Account a : scope) {
            casesByAccount.put(a.Id, new List<Case>());  // not flushed per chunk
        }
    }
}

// CORRECT — write results per chunk; keep only a counter in instance state
public class SummaryBatch implements Database.Batchable<SObject>, Database.Stateful {
    public Integer processedCount = 0;  // lightweight — safe in Stateful

    public void execute(Database.BatchableContext bc, List<Account> scope) {
        List<Account_Summary__c> summaries = new List<Account_Summary__c>();
        for (Account a : scope) {
            summaries.add(new Account_Summary__c(Account__c = a.Id, /* ... */));
        }
        insert summaries;        // flush per chunk
        processedCount += scope.size();
    }
}
```

---

## Example 3: Pruning a Map While Iterating It

**Context:** A service loads `Map<Id, Case> openCases` and must drop every entry whose `Owner` is now inactive, then act on what remains. The obvious loop edits the map from inside the loop that is walking it.

**Problem:** `keySet()` is not a snapshot — "the returned keySet is backed by the map and reflects any changes made to the map, and vice versa" (`apexrefguide` L222249–L222250). Removing from the map while iterating that keySet is the documented "Modifying a collection's elements while iterating through that collection is not supported and causes an error" case (`apexdev` L3182–L3183). The guide's own remedy is to "keep the keys you wish to remove in a temporary list, then remove them after you finish iterating the collection" (`apexdev` L3202–L3203).

**Solution:**

```apex
// WRONG — the loop is walking the map it is editing
for (Id caseId : openCases.keySet()) {
    if (!activeOwnerIds.contains(openCases.get(caseId).OwnerId)) {
        openCases.remove(caseId);
    }
}

// CORRECT — collect first, mutate afterwards
List<Id> orphaned = new List<Id>();
for (Id caseId : openCases.keySet()) {
    if (!activeOwnerIds.contains(openCases.get(caseId).OwnerId)) {
        orphaned.add(caseId);
    }
}
for (Id caseId : orphaned) {
    openCases.remove(caseId);
}

// ALSO CORRECT — never hand a live keySet across a method boundary
Set<Id> caseIdsForCallout = new Set<Id>(openCases.keySet());  // detached copy
enqueueSync(caseIdsForCallout);
openCases.clear();               // does not empty caseIdsForCallout
```

**Why it works:** The first loop only reads; every write happens after the iteration finishes. The third block is the same rule applied across a method boundary — a bare `openCases.keySet()` passed to `enqueueSync` would shrink to nothing the moment the caller cleared the map, and the callout would silently process zero records. `CollectionUtils.snapshotKeys()` in `code-examples.md` §1 is this one-liner with a null guard.

**Where this bites hardest:** the second block is safe but not free. "The List.remove method performs linearly. Using it to remove elements has time and resource implications" (`apexdev` L3200) — that note is about `List.remove`, and building a filtered copy is usually cheaper than repeated removal when more than a handful of entries go.
