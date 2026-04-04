# Custom Iterators and Iterables — Work Template

Use this template when designing or reviewing Apex code that implements `Iterator<T>` or `Iterable<T>`, or when deciding whether a Batch Apex `start()` method should return a `QueryLocator` or a custom `Iterable`.

## Scope

**Skill:** `custom-iterators-and-iterables`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

Answer these before writing any code:

| Question | Answer |
|---|---|
| What is the data source? (SOQL query, external API, computed list, cross-object aggregation) | |
| Can the source be expressed as a single SOQL query? | Yes / No |
| Estimated maximum record count across all pages | |
| Will total SOQL rows stay under 50,000? | Yes / No / Unknown |
| Is this for Batch Apex start(), a for-each loop, or standalone traversal? | |
| What is the expected heap impact per record? (approximate bytes) | |
| Is the iterator stateless (re-runnable) or stateful (position tracked)? | |

---

## Decision: QueryLocator vs. Custom Iterable

| Condition | Decision |
|---|---|
| Source is a single SOQL query AND total rows may exceed 50,000 | Use `Database.getQueryLocator()` |
| Source is a single SOQL query AND total rows are always < 50,000 | Either; QueryLocator preferred for simplicity |
| Source cannot be a single SOQL query | Use custom `Iterable<SObject>` |
| Source mixes SOQL + computation | Custom `Iterable<SObject>` |

**Selected approach:** (fill in)

**Reason:** (fill in)

---

## Iterator Design

### Data source

Describe where records come from and how the iterator will fetch them:

```
(e.g., "keyset SOQL on Account, ORDER BY Id, page size 200")
```

### Page / buffer strategy

| Parameter | Value |
|---|---|
| Buffer / page size | |
| Pagination key or mechanism | (keyset Id / OFFSET / external cursor) |
| Estimated total pages | |
| Total estimated SOQL rows | |

### Class structure

```apex
// Iterator class — owns cursor state
public class MyIterator implements Iterator<SObject> {
    // Internal state:
    //   - buffer: List<SObject>
    //   - bufferIdx: Integer
    //   - pagination key (lastId or offset)
    //   - done: Boolean

    public Boolean hasNext() {
        // Refill buffer when exhausted
        // Return false when done
    }

    public SObject next() {
        if (!hasNext()) {
            throw new NoSuchElementException('MyIterator exhausted');
        }
        // return buffer[bufferIdx++];
    }
}

// Iterable class — stateless factory
public class MyIterable implements Iterable<SObject> {
    // Constructor parameters (data source config)

    public Iterator<SObject> iterator() {
        return new MyIterator(/* pass config */);
    }
}

// Batch class — uses Iterable
public class MyBatch implements Database.Batchable<SObject> {
    public Iterable<SObject> start(Database.BatchableContext bc) {
        return new MyIterable(/* params */);
    }

    public void execute(Database.BatchableContext bc, List<SObject> scope) {
        // business logic
    }

    public void finish(Database.BatchableContext bc) {
        // post-processing
    }
}
```

---

## Review Checklist

- [ ] `hasNext()` returns `false` when exhausted — never throws
- [ ] `next()` throws `NoSuchElementException` (not returns null) when called past end
- [ ] `iterator()` returns a **new** cursor instance — not `this`
- [ ] Total SOQL rows across all pages confirmed < 50,000 (if using custom Iterable in Batch start())
- [ ] Keyset pagination used (not OFFSET) if record count > 2,000
- [ ] Buffer / page size fits within async heap limit (12 MB) at peak usage
- [ ] Batch class implements `Database.Batchable<SObject>` and `start()` return type is `Iterable<SObject>`
- [ ] `Database.Stateful` declared on Batch class only if inter-batch state accumulation is needed
- [ ] Test coverage includes: empty source, single record, multi-page, and exactly-one-page-boundary cases

---

## Notes

Record any deviations from the standard pattern and why:

```
(e.g., "Using eager buffer in iterator() because source is a pre-computed List with guaranteed < 10k records")
```
