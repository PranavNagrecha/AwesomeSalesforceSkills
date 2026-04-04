# Well-Architected Notes — Custom Iterators and Iterables

## Relevant Pillars

- **Performance** — Custom iterators exist primarily for performance. Lazy evaluation avoids materializing large collections in heap, spreading memory consumption across the batch execution timeline. The choice between eager (full List in `iterator()`) and lazy (page-at-a-time in `hasNext()`) is the central performance tradeoff for this pattern.

- **Reliability** — The 50,000-row query-rows-returned limit creates a reliability risk for custom iterables that are not sized correctly. Designs must establish a firm upper bound on total iterable records and enforce it at the data-source layer (e.g., a WHERE clause, a maximum offset guard, or a hard limit check before enqueuing the batch). Iterators that fail mid-traversal fail the entire batch job, so `hasNext()` and `next()` contract compliance is a reliability requirement.

- **Operational Excellence** — Custom iterator classes are harder to observe than `QueryLocator` jobs. Log the total records enumerated (via a counter in the Iterator and surfaced in `finish()`) to make job behavior visible. Include meaningful exception messages in `next()` so that `NoSuchElementException` failures are traceable in debug logs without re-running the job.

## Architectural Tradeoffs

**Custom Iterable vs. QueryLocator:** `Database.getQueryLocator()` is the default for SOQL-queryable sources. It uses a server-side cursor exempt from the query-rows limit and requires zero custom code. A custom `Iterable<SObject>` is warranted only when the data source cannot be represented as a single SOQL query. Choosing a custom iterable for a SOQL-queryable source adds complexity and introduces the 50,000-row limit risk for no benefit.

**Lazy vs. Eager Construction:** An eager iterator (builds the full buffer in the constructor) is simpler but equivalent in heap usage to returning a plain `List` from `start()`. Use eager construction only when the list already exists and you just need to satisfy the `Iterable` interface. Use lazy construction (buffer refilled in `hasNext()`) when reducing peak heap usage is the goal.

**Single-Class (Iterable + Iterator) vs. Two-Class Design:** Combining both interfaces in one class reduces file count but introduces shared-state bugs if `iterator()` returns `this`. Two-class separation — an immutable `Iterable` factory and a mutable `Iterator` cursor — is the safer architecture for any non-trivial data source.

## Anti-Patterns

1. **Using a custom Iterable for SOQL-queryable sources exceeding 50,000 rows** — `Database.getQueryLocator()` is exempt from the query-rows-returned limit because it uses a server-side cursor. A custom Iterable is not exempt. Returning a custom `Iterable` from `start()` for a source that could produce 100,000 SOQL rows will fail at runtime. The correct architecture is to use QueryLocator for large SOQL-queryable sources and reserve custom Iterables for non-SOQL or mixed sources under the limit.

2. **Treating the Iterator class as the unit of reuse** — Developers sometimes share an `Iterator` instance between two Batch jobs or between a Batch and a test assertion. Because `Iterator` is a stateful cursor, sharing it across contexts produces non-deterministic results. The `Iterable` factory is the reusable unit; iterators are disposable cursors and should never be stored beyond the scope of one traversal.

3. **Skipping governor-limit sizing before deployment** — Custom iterators hide their total row access inside method calls that are not visible until runtime. Not performing a pre-deployment sizing estimate (total records × rows per record across all SOQL refills) against the 50,000-row limit is an operational excellence failure that turns into a production outage on the first batch run with real data volume.

## Official Sources Used

- Apex Developer Guide: Using Custom Iterators — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_iterable.htm
- Apex Developer Guide: Batch Apex Interface — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_batch_interface.htm
- Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
