# LLM Anti-Patterns — Custom Iterators and Iterables

Common mistakes AI coding assistants make when generating or advising on custom Iterator and Iterable implementations in Apex.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Loading the entire dataset into a List in the Iterable constructor, defeating lazy evaluation

**What the LLM generates:**

```apex
public class MyIterable implements Iterable<SObject> {
    private List<SObject> allRecords;

    public MyIterable() {
        allRecords = [SELECT Id, Name FROM Account]; // Loads everything into heap
    }

    public Iterator<SObject> iterator() {
        return allRecords.iterator();
    }
}
```

**Why it happens:** LLMs generate the simplest implementation. But if you are using a custom Iterable instead of `Database.getQueryLocator`, the point is to NOT load everything into memory at once. Pre-loading the entire result set defeats the purpose and hits heap limits at scale.

**Correct pattern:**

```apex
public class PaginatedIterable implements Iterable<SObject> {
    public Iterator<SObject> iterator() {
        return new PaginatedIterator();
    }
}

public class PaginatedIterator implements Iterator<SObject> {
    private List<SObject> currentPage;
    private Integer pageIndex = 0;
    private Integer recordIndex = 0;
    private static final Integer PAGE_SIZE = 200;

    public PaginatedIterator() {
        loadNextPage();
    }

    private void loadNextPage() {
        Integer offset = pageIndex * PAGE_SIZE;
        currentPage = Database.query(
            'SELECT Id, Name FROM Account LIMIT ' + PAGE_SIZE + ' OFFSET ' + offset
        );
        recordIndex = 0;
        pageIndex++;
    }

    public Boolean hasNext() {
        if (recordIndex < currentPage.size()) return true;
        loadNextPage();
        return !currentPage.isEmpty();
    }

    public SObject next() {
        return currentPage[recordIndex++];
    }
}
```

**Detection hint:** Custom `Iterable` class that runs a SOQL query with no `LIMIT` in its constructor or `iterator()` method, storing results in a List field.

---

## Anti-Pattern 2: Implementing Iterator without hasNext() and next() method signatures matching the interface

**What the LLM generates:**

```apex
public class MyIterator implements Iterator<Account> {
    public Boolean hasMore() { // Wrong method name
        return index < data.size();
    }
    public Account getNext() { // Wrong method name
        return data[index++];
    }
}
```

**Why it happens:** LLMs borrow Java Iterator patterns where method names vary. Apex requires exactly `hasNext()` returning `Boolean` and `next()` returning the parameterized type. Misnaming causes a compile error: "Class must implement interface method."

**Correct pattern:**

```apex
public class MyIterator implements Iterator<Account> {
    private List<Account> data;
    private Integer index = 0;

    public MyIterator(List<Account> data) {
        this.data = data;
    }

    public Boolean hasNext() {
        return index < data.size();
    }

    public Account next() {
        if (!hasNext()) throw new NoSuchElementException('Iterator exhausted');
        return data[index++];
    }
}
```

**Detection hint:** Class implementing `Iterator<` with methods named anything other than exactly `hasNext` and `next`.

---

## Anti-Pattern 3: Returning a custom Iterable from Batch start() without understanding the 50K scope limit

**What the LLM generates:**

```apex
public class MyBatch implements Database.Batchable<SObject> {
    public Iterable<SObject> start(Database.BatchableContext bc) {
        return new MyIterable(); // Subject to 50K total record limit
    }
}
```

**Why it happens:** LLMs suggest custom Iterables for Batch `start()` without warning that when `start()` returns an `Iterable` instead of a `Database.QueryLocator`, the total record count is limited to 50,000 rows (same as standard SOQL). Only `Database.getQueryLocator` gets the 50 million row limit.

**Correct pattern:**

```apex
// If data comes from SOQL and could exceed 50K, use QueryLocator
public Database.QueryLocator start(Database.BatchableContext bc) {
    return Database.getQueryLocator('SELECT Id FROM Account');
}

// Only use custom Iterable when data comes from a non-SOQL source
// (external API, computed records) AND you know it stays under 50K
public Iterable<ExternalRecord> start(Database.BatchableContext bc) {
    return new ExternalApiIterable(); // Document: max 50K records
}
```

**Detection hint:** Batch `start()` returning `Iterable<` with a SOQL-based data source — should likely be `Database.getQueryLocator` instead.

---

## Anti-Pattern 4: Not handling the case where next() is called after the iterator is exhausted

**What the LLM generates:**

```apex
public SObject next() {
    return records[currentIndex++]; // ArrayIndexOutOfBoundsException when exhausted
}
```

**Why it happens:** LLMs generate minimal `next()` implementations that assume `hasNext()` was always called first. In practice, callers may not check, and an unguarded array access produces a confusing `ListException` instead of a clear error.

**Correct pattern:**

```apex
public SObject next() {
    if (!hasNext()) {
        throw new NoSuchElementException('No more elements in iterator');
    }
    return records[currentIndex++];
}
```

**Detection hint:** `next()` method that directly indexes into a list without a bounds check or `hasNext()` guard.

---

## Anti-Pattern 5: Making the Iterator stateful in a way that breaks Batch serialization

**What the LLM generates:**

```apex
public class MyIterator implements Iterator<SObject> {
    private Database.QueryLocator locator; // Not serializable
    private Database.QueryLocatorIterator qli;

    public MyIterator() {
        locator = Database.getQueryLocator('SELECT Id FROM Account');
        qli = locator.iterator();
    }

    public Boolean hasNext() { return qli.hasNext(); }
    public SObject next() { return qli.next(); }
}
```

**Why it happens:** LLMs try to wrap a QueryLocator in a custom Iterator. But `Database.QueryLocator` and `Database.QueryLocatorIterator` are not serializable. When used in a Batch context, the framework tries to serialize the Iterable between `start()` and `execute()`, causing a `SerializationException`.

**Correct pattern:**

```apex
// If you need a QueryLocator, return it directly from start()
public Database.QueryLocator start(Database.BatchableContext bc) {
    return Database.getQueryLocator('SELECT Id FROM Account');
}

// For custom iterators, use serializable state only
public class MyIterator implements Iterator<SObject> {
    private Integer currentOffset = 0;
    private List<SObject> currentPage;
    private static final Integer PAGE_SIZE = 200;

    public Boolean hasNext() {
        if (currentPage == null || currentPage.isEmpty()) {
            fetchPage();
        }
        return !currentPage.isEmpty();
    }
    // ...
}
```

**Detection hint:** Custom Iterator class with fields of type `Database.QueryLocator`, `Database.QueryLocatorIterator`, or other non-serializable platform types.
