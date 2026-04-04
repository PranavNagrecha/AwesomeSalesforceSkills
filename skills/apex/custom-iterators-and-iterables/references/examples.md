# Examples — Custom Iterators and Iterables

## Example 1: Batch Apex Job Processing Records from a Multi-Org Aggregation

**Context:** A platform team aggregates Account IDs from three separate CSV imports stored as `ContentVersion` attachments. The IDs must be deduplicated and processed in a single Batch Apex job. There is no SOQL query that can represent all three sources.

**Problem:** Without a custom Iterable, the developer loads all IDs into a `List<Id>`, passes it to a Batch `start()` as a bound SOQL query, and the job either fails to compile cleanly or forces a SOQL OFFSET pattern that is fragile. Alternatively, they try to return `List<Account>` directly from `start()`, which is valid but materializes the entire set in heap before the first `execute()` call.

**Solution:**

```apex
// --- Iterator ---
public class AggregatedAccountIterator implements Iterator<Account> {
    private List<Account> buffer;
    private Integer idx = 0;

    public AggregatedAccountIterator(Set<Id> ids) {
        // Fetch once; acceptable because the caller controls total volume < 50k
        buffer = [SELECT Id, Name, Industry FROM Account WHERE Id IN :ids];
    }

    public Boolean hasNext() {
        return idx < buffer.size();
    }

    public Account next() {
        if (!hasNext()) {
            throw new NoSuchElementException('AggregatedAccountIterator exhausted');
        }
        return buffer[idx++];
    }
}

// --- Iterable ---
public class AggregatedAccountIterable implements Iterable<Account> {
    private final Set<Id> ids;

    public AggregatedAccountIterable(Set<Id> dedupedIds) {
        this.ids = dedupedIds;
    }

    public Iterator<Account> iterator() {
        return new AggregatedAccountIterator(ids);
    }
}

// --- Batch ---
public class AggregatedAccountBatch implements Database.Batchable<SObject> {
    private final Set<Id> ids;

    public AggregatedAccountBatch(Set<Id> ids) {
        this.ids = ids;
    }

    public Iterable<SObject> start(Database.BatchableContext bc) {
        return new AggregatedAccountIterable(ids);
    }

    public void execute(Database.BatchableContext bc, List<Account> scope) {
        // business logic here
    }

    public void finish(Database.BatchableContext bc) {}
}
```

**Why it works:** `start()` returns an `Iterable<SObject>` (the return type is the interface, not the concrete class), and the batch framework calls `iterator()` once to get the cursor. The `iterator()` factory method issues the SOQL at traversal time rather than at Batch construction time, so governor limits accumulate only during the `start()` execution context where they are expected.

---

## Example 2: Lazy Keyset-Paginated Iterator for Large External Data Set

**Context:** A nightly sync job must process up to 200,000 staging records stored in a custom object `Import_Record__c`. Using `Database.getQueryLocator()` is the right answer for pure SOQL sources, but this example demonstrates keyset pagination inside a custom iterator for cases where the data source is an external HTTP endpoint returning pages of JSON records — the sObjects are constructed in Apex from HTTP callout responses.

**Problem:** A developer tries to make all callouts inside a Batch `execute()` method, hitting the 100-callout-per-transaction limit after the first few batches. Moving callouts to `start()` runs into the same limit because `start()` is also a single transaction.

**Solution:** Use a Queueable chain for callout-heavy iteration, OR — if the data can be staged into a custom object first and then batch-processed — use a keyset iterator over the staged records:

```apex
public class KeysetStagingIterator implements Iterator<Import_Record__c> {
    private List<Import_Record__c> buffer = new List<Import_Record__c>();
    private Integer bufferIdx = 0;
    private Id lastId = null;
    private Boolean done = false;
    private static final Integer PAGE = 200;

    public Boolean hasNext() {
        if (bufferIdx < buffer.size()) {
            return true;
        }
        if (done) {
            return false;
        }
        if (lastId == null) {
            buffer = [SELECT Id, Payload__c FROM Import_Record__c
                      ORDER BY Id LIMIT :PAGE];
        } else {
            buffer = [SELECT Id, Payload__c FROM Import_Record__c
                      WHERE Id > :lastId ORDER BY Id LIMIT :PAGE];
        }
        bufferIdx = 0;
        if (buffer.isEmpty()) {
            done = true;
            return false;
        }
        lastId = buffer[buffer.size() - 1].Id;
        return true;
    }

    public Import_Record__c next() {
        if (!hasNext()) {
            throw new NoSuchElementException('KeysetStagingIterator exhausted');
        }
        return buffer[bufferIdx++];
    }
}

public class StagingIterable implements Iterable<Import_Record__c> {
    public Iterator<Import_Record__c> iterator() {
        return new KeysetStagingIterator();
    }
}
```

**Why it works:** Keyset pagination (`WHERE Id > :lastId`) avoids the performance degradation of `OFFSET`-based pagination. Each page issues one SOQL query for PAGE rows, and the iterator fetches the next page only when the current buffer is exhausted. Because `hasNext()` triggers the refill when the buffer runs out, the maximum heap in use at any moment is one page of 200 records, not the full 200,000-row set.

**Important caveat:** The cumulative rows returned across all pages still count against the 50,000-row query-rows-returned limit in the `start()` transaction. This pattern is suitable only when total rows remain under that limit. For sets exceeding 50,000, use `Database.getQueryLocator()` instead.

---

## Anti-Pattern: Returning Iterator<SObject> Directly from start()

**What practitioners do:** Implement `Iterator<SObject>` on the Batch class itself and attempt `return this` from `start()`, because the batch class has `hasNext()` and `next()` methods.

**What goes wrong:** `Database.Batchable<SObject>.start()` must return either `Database.QueryLocator` or `Iterable<SObject>`. Returning an `Iterator<SObject>` directly does not satisfy `Iterable<SObject>` — the compiler will reject it unless the class also implements `Iterable<SObject>`. Even if combined, using `return this` means `iterator()` must return a fresh cursor but `this` already has mutable state. The pattern entangles batch lifecycle and iteration cursor logic in a single class, making it fragile.

**Correct approach:** Keep the Batch class, the Iterable, and the Iterator as three separate classes. The Batch class owns the data source parameters; the Iterable is a factory; the Iterator owns the cursor state. This separation ensures `iterator()` always returns a fresh, independent cursor and the Batch class remains stateless with respect to traversal.
