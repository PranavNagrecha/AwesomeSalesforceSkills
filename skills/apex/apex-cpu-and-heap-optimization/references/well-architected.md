# Well-Architected Notes — Apex CPU And Heap Optimization

## Relevant Pillars

### Performance

This skill is directly about transaction efficiency and throughput under real load.

Tag findings as Performance when:
- algorithmic cost is too high for the transaction budget
- heap pressure comes from unnecessarily retained data
- large payload handling or logging consumes disproportionate resources

### Scalability

CPU- and heap-heavy patterns often work for tiny data sets and fail at production scale.

Tag findings as Scalability when:
- performance collapses as record or payload counts rise
- the design assumes single-record or small-list behavior
- async chunking or caching should be considered

### Reliability

Limit failures cause user-visible rollbacks and brittle background processing.

Tag findings as Reliability when:
- CPU or heap exceptions are already causing transaction failures
- diagnostics are too weak to isolate hotspots
- the workload is too heavy for one transaction boundary

## Architectural Tradeoffs

- **Micro-optimization vs structural refactor:** most wins come from changing data shape, not syntax trivia.
- **Single transaction vs async decomposition:** sometimes the cheapest optimization is to split the workload.
- **Rich diagnostics vs extra overhead:** instrumentation helps until it becomes the bottleneck itself.

## Anti-Patterns

1. **Nested-loop brute force after bulkification** — database-safe but still CPU-expensive.
2. **Large payload duplication** — heap pain with little business value.
3. **Blind tuning without measurement** — changes risk without confidence.

## Trade-Off: Budget Ownership

A CPU or heap budget belongs to the **transaction**, not to a class. Certified
managed packages get their own SOQL and DML allowances but share your CPU time,
heap, and transaction execution time, so a design that is measured in isolation
can still fail once an ISV package joins the same save order. Architecturally
this means the unit of performance review is the save order for an object, not
the Apex class in the pull request.

## Official Sources Used

- **Salesforce Developer Limits and Allocations Quick Reference**, "Per-Transaction
  Apex Limits" table and footnotes 4–5 (`salesforce_app_limits_cheatsheet.txt`
  L57–L106, L161, L170–L177) — the sync/async CPU ceilings (10,000 / 60,000 ms),
  heap ceilings (6 MB / 12 MB), the 10-minute transaction execution limit, and the
  statement that DML server CPU counts while database and callout wait time does
  not. Also the note at L36–L37 that scheduled Apex runs on synchronous limits.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf
- **Salesforce Developer Limits and Allocations Quick Reference**, "Per-Transaction
  Certified Managed Package Limits" (`salesforce_app_limits_cheatsheet.txt`
  L207–L209, L241–L248) — heap, CPU, transaction execution time and unique
  namespaces are the four limits that do *not* count separately per certified
  namespace, and the cumulative cross-namespace multiplier does not apply to them.
- **Apex Developer Guide**, "SOQL For Loops" and "SOQL For Loops Versus Standard
  SOQL Queries" (`apexdev.txt` L9967–L10030, L10105–L10110, L20271–L20285) —
  chunking in batches of 200 as the documented heap remedy, the explicit CPU cost
  of that trade, and the partial-serialization behaviour of the for-loop variable.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- **Apex Developer Guide**, "Using Batch Apex" and "Batch Apex Considerations"
  (`apexdev.txt` L17519–L17524, L17701–L17743) — governor limits reset per
  `execute`, `Database.Stateful` retains instance members only, and the 2,000-record
  scope ceiling for a `QueryLocator` start method.
- **Apex Developer Guide**, "Static and Instance Methods, Variables, and
  Initialization Code" and "Exceptions that Can't be Caught" (`apexdev.txt`
  L3738–L3792, L39721–L39728) — static state persists across trigger invocations
  while limits reset, and `System.LimitException` skips `catch` and `finally`.
- **Apex Developer Guide**, "Debug Log" (`apexdev.txt` L38239–L38241,
  L38275–L38284, L38930–L38941) — `LIMIT_USAGE_FOR_NS` fields, and the rule that
  minimal heap usage is reported as `0`.
- **Apex Reference Guide**, `Limits` class and `Test` class (`apexrefguide.txt`
  L220544–L220567, L220711–L220734, L241055–L241090) — `getCpuTime` /
  `getLimitCpuTime` / `getHeapSize` (documented as *approximate*) /
  `getLimitHeapSize`, and the fact that `Test.startTest()` assigns a new set of
  governor limits while code after `Test.stopTest()` reverts to the original ones.
- **`standards/decision-trees/performance-tuning.md`** — Rule 0 (profile before
  tuning) and branches Q2/Q3/Q4, which route a CPU or heap symptom into this skill
  and route counting limits elsewhere.
- **Salesforce Well-Architected** — Performance, Scalability, and Reliability
  pillar framing used in the sections above.
