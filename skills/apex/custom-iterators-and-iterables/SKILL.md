---
name: custom-iterators-and-iterables
description: "Use this skill when implementing the Iterable<T> or Iterator<T> interfaces in Apex to create custom traversal logic, build lazy-evaluation data sources for Batch Apex, or stream large result sets without materializing an entire List. Trigger keywords: custom iterator, Iterable interface, Iterator interface, batch start iterable, lazy evaluation apex, streaming apex query, paginated batch. NOT for standard list iteration (use for-each on List directly), NOT for Batch Apex fundamentals (use batch-apex-patterns), NOT for Apex triggers or synchronous bulk patterns."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
  - Operational Excellence
triggers:
  - "I need to feed a Batch Apex job records that don't come from a SOQL query locator"
  - "My Batch Apex start method needs to return a custom Iterable instead of a QueryLocator"
  - "I want to paginate through a large data set lazily without loading all records into a List at once"
  - "How do I implement the Iterator interface in Apex to walk through a custom collection?"
  - "Batch job is hitting heap limits because start() builds a massive List before processing"
tags:
  - apex
  - batch-apex
  - iterator
  - iterable
  - lazy-evaluation
  - memory-optimization
inputs:
  - "The data source the job must traverse (SOQL result, external API response, aggregated object, or computed collection)"
  - "Expected record volume and whether it exceeds safe in-memory List thresholds"
  - "Whether the iterator needs to be stateful (track position) or stateless (re-queryable)"
  - "Batch scope size and governor limit budget (heap, CPU, SOQL)"
outputs:
  - "Apex class implementing Iterator<SObject> with hasNext() and next() methods"
  - "Apex class implementing Iterable<SObject> with iterator() factory method"
  - "Batch Apex class whose start() method returns the custom Iterable"
  - "Decision guidance on when to use custom Iterable vs. Database.getQueryLocator()"
dependencies:
  - batch-apex-patterns
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Custom Iterators and Iterables

Use this skill when a Batch Apex job needs a non-SOQL data source for its `start()` method, or when you want to traverse records lazily without materializing a full `List<SObject>` in heap. It covers the `Iterator<T>` and `Iterable<T>` interfaces, their contracts, patterns for lazy evaluation, and the constraints that apply when using them inside Batch Apex.

---

## Before Starting

- Confirm whether the data source can be expressed as a single SOQL query. If it can, `Database.getQueryLocator()` is almost always the right choice because it streams results transparently and is exempt from the 50,000-row SOQL query limit. Only reach for a custom Iterable when the data source cannot be a single SOQL query.
- Understand that when `start()` returns an `Iterable`, the total records the platform can handle across all batches is bounded by the 50,000-row query-rows-returned governor limit, not the separate query locator cursor limit. This is a critical difference.
- Custom Iterators cannot be used directly in Apex for-each loops unless they are wrapped inside a class that also implements `Iterable<T>`. An `Iterator<T>` alone is not iterable by the for-each construct — the for-each loop requires `Iterable<T>`.
- Heap usage is your primary risk: if `iterator()` pre-materializes the entire collection at construction time, you have not gained anything over a plain `List`. Genuine lazy evaluation means `next()` fetches or computes one element (or a small page) at a time.

---

## Core Concepts

### The Iterator<T> Interface

`Iterator<T>` has exactly two methods: `Boolean hasNext()` and `T next()`. Both must be declared `global` or `public`. The platform calls `hasNext()` before calling `next()`; the contract is that `next()` must not be called when `hasNext()` returns `false`. Violating this contract throws a `NoSuchElementException` at runtime. The type parameter `T` is most commonly `SObject` or a concrete sObject type when used with Batch Apex, but can be any Apex type.

### The Iterable<T> Interface

`Iterable<T>` has a single method: `Iterator<T> iterator()`. When a class implements `Iterable<T>`, it can appear in an Apex for-each loop and can be returned from `Database.Batchable<T>.start()`. The `iterator()` method is called once per loop or once by the batch executor to obtain the iterator cursor. It should create and return a fresh `Iterator<T>` each time so the collection can be traversed multiple times independently.

### Batch Apex start() with Iterable

When `start(Database.BatchableContext bc)` returns `Iterable<SObject>` instead of `Database.QueryLocator`, the batch framework calls `iterator()` on the return value to enumerate all records, then chunks them into execute() batches of the configured scope size. The key behavioral difference from `QueryLocator` is that the full enumeration is subject to standard Apex governor limits, including the 50,000-row query-rows-returned cap per transaction in the `start()` execution context. The batch framework does not bypass this limit for custom iterables the way it bypasses it for `QueryLocator`.

### Lazy Evaluation Pattern

A lazy iterator defers fetching or computing the next element until `next()` is called. A common pattern is a SOQL-offset paginator: the iterator holds a current offset and page buffer. When the buffer is exhausted, `next()` triggers the next SOQL query to refill the buffer. This spreads heap usage over time but introduces additional SOQL queries. Because `start()` runs in a single transaction with its own governor limit context, the total number of rows returned across all paginated queries still accumulates against the 50,000-row query-rows-returned limit.

---

## Common Patterns

### Pattern 1 — Custom Iterable Wrapping a Pre-Computed List

**When to use:** The records to process are produced by Apex logic (e.g., aggregated results, cross-object computations, external API responses) that cannot be expressed as a SOQL query locator, but the total record count is known to stay well within the 50,000-row query-rows-returned limit.

**How it works:** Produce the `List<SObject>` in the `iterator()` method (not at construction time) and return a list-backed iterator that walks the list with an integer index.

```apex
public class ComputedAccountIterable implements Iterable<Account> {
    private final List<Id> accountIds;

    public ComputedAccountIterable(List<Id> ids) {
        this.accountIds = ids;
    }

    public Iterator<Account> iterator() {
        // Fetch at iteration time, not at construction time
        return [SELECT Id, Name FROM Account WHERE Id IN :accountIds].iterator();
    }
}
```

Note: `List<T>.iterator()` returns a built-in `Iterator<T>`, so wrapping a built-in list is zero boilerplate.

**Why not the alternative:** Passing `accountIds` as a bind variable to `Database.getQueryLocator()` is actually simpler when the IDs come from a prior Apex step. Use the custom Iterable pattern only when the data source is not a query at all — for example, records synthesized from a REST callout or an aggregation.

### Pattern 2 — Stateful Custom Iterator with Internal Cursor

**When to use:** The data source is externally paginated (e.g., records fetched from an external API), or when you need per-element transformation logic before the batch framework sees each record.

**How it works:** Implement `Iterator<SObject>` directly with an internal page buffer and a done flag.

```apex
public class PagedExternalIterator implements Iterator<Account> {
    private List<Account> buffer = new List<Account>();
    private Integer bufferIndex = 0;
    private Integer offset = 0;
    private static final Integer PAGE_SIZE = 200;
    private Boolean exhausted = false;

    public Boolean hasNext() {
        if (bufferIndex < buffer.size()) {
            return true;
        }
        if (exhausted) {
            return false;
        }
        // Refill buffer
        buffer = [SELECT Id, Name FROM Account ORDER BY CreatedDate LIMIT :PAGE_SIZE OFFSET :offset];
        bufferIndex = 0;
        offset += buffer.size();
        if (buffer.isEmpty()) {
            exhausted = true;
            return false;
        }
        return true;
    }

    public Account next() {
        if (!hasNext()) {
            throw new NoSuchElementException('No more elements');
        }
        return buffer[bufferIndex++];
    }
}

public class PagedExternalIterable implements Iterable<Account> {
    public Iterator<Account> iterator() {
        return new PagedExternalIterator();
    }
}
```

**Why not the alternative:** A single SOQL query with an OFFSET clause becomes inefficient past roughly 2,000 rows because the database must skip scanned rows. For very large sets, prefer `QueryLocator`. For moderate sets where a single SOQL query is architecturally impossible, pagination inside a custom iterator spreads the work.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Data comes from a single SOQL query on sObjects | `Database.getQueryLocator()` | Exempted from the 50 k query-rows limit; cursor managed by platform |
| Records produced by Apex logic or external callout | Custom `Iterable<SObject>` in `start()` | Only option when a SOQL query locator cannot represent the source |
| Need for-each loop over custom Apex objects | Implement `Iterable<T>` on the class | For-each requires `Iterable<T>`, not `Iterator<T>` alone |
| Total record count < 50,000 and source is pre-computed | `List<SObject>.iterator()` wrapped in an `Iterable` | Simplest path; built-in list iterator handles cursor |
| Large paginated external source where count is unknown | Stateful custom `Iterator` with lazy SOQL pagination | Avoids materializing full set; fetches per page on demand |
| Multi-object or aggregated source requiring joins | Custom `Iterator` that merges multiple lists | QueryLocator only supports single-query sources |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

- [ ] `hasNext()` never throws; it returns `false` when exhausted
- [ ] `next()` throws `NoSuchElementException` (not returns `null`) when called past end
- [ ] `iterator()` on the `Iterable` creates a fresh cursor each call — no shared mutable state between calls
- [ ] Total rows returned through the iterator in the `start()` context stay within the 50,000-row query-rows-returned governor limit
- [ ] Heap usage has been estimated: the buffer size and object size stay within the 12 MB async heap limit
- [ ] The Batch class implements `Database.Batchable<SObject>` and `start()` return type matches the iterator element type
- [ ] If `Database.Stateful` is needed for accumulating results, it is declared on the Batch class, not the Iterator class

---

## Salesforce-Specific Gotchas

1. **Custom Iterators are subject to the 50,000-row query limit in start()** — Unlike `Database.getQueryLocator()`, which runs in a separate cursor context exempt from the query-rows-returned limit, a custom `Iterable` returned from `start()` runs inside the batch's `start()` transaction. Every SOQL row that `next()` fetches counts against the 50,000-row-per-transaction limit in that context. If your iterable pages through 60,000 records via SOQL, the job fails with `System.LimitException: Too many query rows: 50001`.

2. **Iterator<T> alone cannot be used in a for-each loop** — Apex for-each requires the target to implement `Iterable<T>`. An `Iterator<T>` by itself is not iterable. A common mistake is implementing only `Iterator<T>` and then using `for (SObject o : myIterator)`, which produces a compile error. Always pair `Iterator<T>` with a wrapping `Iterable<T>` when for-each syntax is required.

3. **Mutable state in iterator() causes ghost-replay bugs** — If the `Iterable` class stores the iterator's position as an instance variable and `iterator()` returns `this` rather than a new cursor, the second caller (or the second batch job enqueue) resumes from where the first left off instead of starting from the beginning. Always return `new MyIterator(...)` from `iterator()` rather than re-using a stored cursor.

4. **OFFSET-based pagination degrades at scale** — SOQL `OFFSET` scans and discards leading rows on every query, making it progressively slower and more CPU-intensive as the offset grows. Beyond roughly 2,000 records, use keyset pagination (`WHERE Id > :lastId ORDER BY Id`) instead of `OFFSET` inside a custom iterator.

5. **Scope size still applies; hasNext() may be called more times than expected** — The batch framework calls `hasNext()` and `next()` to fill each batch scope slice. With a scope of 200, `next()` is called 200 times before `execute()` runs. If `hasNext()` triggers a SOQL refill on every call (instead of buffering), you will exhaust SOQL-per-transaction limits quickly. Always buffer a full page before returning `true` from `hasNext()`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Iterator<SObject> implementation | Apex class with `hasNext()` and `next()` carrying a lazy page buffer |
| Iterable<SObject> wrapper | Apex class returning a fresh cursor from `iterator()` for use in Batch start() or for-each loops |
| Batch Apex class using custom Iterable | Batch class whose `start()` returns the custom Iterable with correct type parameter |
| Decision table | Guidance on QueryLocator vs. custom Iterable vs. pre-computed List for a given scenario |

---

## Related Skills

- `batch-apex-patterns` — Covers Batch Apex structure, scope tuning, `Database.Stateful`, and `QueryLocator` patterns; use alongside this skill when designing the full batch job
- `apex-queueable-patterns` — When record volume or complexity is moderate, Queueable chaining may avoid the need for Batch + Iterable altogether
