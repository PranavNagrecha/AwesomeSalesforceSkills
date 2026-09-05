# Gotchas — Apex Limits Monitoring

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.
Line citations are into the Summer '26 guide text: `apexdev` = Apex Developer Guide,
`apexrefguide` = Apex Reference Guide, `object_reference` = Object Reference,
`api_rest` = REST API Developer Guide.

## Gotcha 1: A Limit Breach Skips `finally` As Well As `catch`

**What happens:** `System.LimitException` cannot be caught — but the part that destroys a logging strategy is the second half of the same sentence: "When exceptions are uncatchable, catch blocks, **as well as `finally` blocks if any**, aren't executed" (`apexdev L39727–39728`). Code that buffers log records and flushes them in a `finally` block loses the entire buffer at the exact moment it mattered, and the transaction leaves no trace of which meter it blew.

**When it occurs:** any breach of a governor ceiling — 100 SOQL statements synchronously, 150 DML statements, 10,000 ms CPU, 6 MB heap. The runtime throws "if a governor limit such as heap size or CPU time has been exceeded, when the maximum number of SOQL queries issued has been exceeded, an attempt is made to retrieve more than the maximum number of records, and so on" (`apexdev L39723–39726`).

**How to avoid:** write the log line from inside the guard, *before* the expensive operation, not from a `finally`. For post-mortem, use a surface outside the transaction: `BatchApexErrorEvent` (`apexdev L17852–17858`), a Queueable Finalizer (`apexdev L16290–16303`), or the `ApexUnexpectedException` event log whose `EXCEPTION_CATEGORY` names the meter (`object_reference L114265–114285`).

---

## Gotcha 2: `getAggregateQueries()` Counts Relationship Subqueries, Not `COUNT()` or `GROUP BY`

**What happens:** the name suggests it tracks aggregate-function queries. It does not. The Per-Transaction Apex Limits footnote says: "In a SOQL query with parent-child relationship subqueries, each parent-child relationship counts as an extra query. These types of queries have a limit of three times the number for top-level queries. The limit for subqueries corresponds to the value that `Limits.getLimitAggregateQueries()` returns" (`apexdev L19612–19616`). A `SELECT AccountId, COUNT(Id) … GROUP BY AccountId` consumes an ordinary slot on `getQueries()`; a `SELECT Id, (SELECT Id FROM Contacts) FROM Account` consumes one on each meter.

**When it occurs:** code that guards `getQueries()` and issues nested `SELECT (SELECT …)` shapes in a loop, or code that guards `getAggregateQueries()` before a `COUNT()` and concludes it is protected.

**How to avoid:** guard `getAggregateQueries()` in code that issues relationship subqueries, and note the ceiling is derived (3× the SOQL ceiling: 300 sync, 600 async), not a printed constant. Aggregate-function queries need the ordinary `getQueries()` guard. Custom metadata types are exempt from the SOQL ceiling entirely — "In a single Apex transaction, custom metadata records can have unlimited SOQL queries" (`apexdev L19617–19618`).

---

## Gotcha 3: Scheduled Apex Is Asynchronous But Runs Under Synchronous Limits

**What happens:** the note above the Per-Transaction Apex Limits table reads: "Although scheduled Apex is an asynchronous feature, synchronous limits apply to scheduled Apex jobs" (`apexdev L19536`). A `Schedulable` sized against 200 SOQL, 12 MB heap and 60,000 ms CPU actually has 100, 6 MB and 10,000 ms. The job passes in a sandbox with ten records and fails nightly in production.

**When it occurs:** most often in a limits *monitor* — the scheduled poller that reads `OrgLimits.getAll()` and inserts a row per limit is itself the class most likely to hit a synchronous ceiling nobody budgeted for.

**How to avoid:** never assume the column; call `Limits.getLimitX()` and let the runtime answer. Keep the `Schedulable` thin and push the work into a Queueable or Batch when it needs async headroom — "we recommend that all processing take place in a separate class" (`apexdev L16621–16623`). A Finalizer has the mirror-image trap: synchronous limits apply except for total heap size, `System.enqueueJob` count, and `@future` methods per invocation (`apexdev L16297–16303`).

---

## Gotcha 4: `ApexTestResultLimits` Silently Returns Nothing Under Three Conditions

**What happens:** the object records what each test method consumed, and a CI gate built on it looks like coverage. Its Usage section imposes three conditions in three consecutive sentences (`object_reference L32693–32702`): it "captures the limits used between the `Test.startTest()` and `Test.stopTest()` methods. If `startTest()` and `stopTest()` aren't called, limits usage isn't captured"; "the associated test method must be run asynchronously"; and "limits for asynchronous Apex operations (batch, scheduled, future, and queueable) that are called within test methods aren't captured" and "limits are captured only for the default namespace." Break any one and the gate reads zero consumption, which passes.

**When it occurs:** a synchronous `sf apex run test` invocation, or a test suite where the assertions sit outside the `startTest`/`stopTest` block, or a baseline built over Batch classes whose real work happens in `execute`.

**How to avoid:** shape the tests so the measured work sits inside the block, run the suite asynchronously, and treat a row of zeros as a broken gate rather than a clean result. Note also there is no `Heap` column and no `PublishImmediateDml` column — the complete field set is `ApexTestResultId`, `AsyncCalls`, `Callouts`, `Cpu`, `Dml`, `DmlRows`, `Email`, `LimitContext`, `LimitExceptions`, `MobilePush`, `QueryRows`, `Soql`, `Sosl` (`object_reference L32570–32690`). Heap regressions need an in-test assertion. From API 49.0 the querying user needs View Setup and Configuration (`object_reference L32567–32568`).

---

## Gotcha 5: Certified Managed Packages Get Their Own Limit Allocations, So Your Reading Is Per-Namespace

**What happens:** `Limits.getQueries()` reports your namespace's consumption, not the transaction's. "If you install a certified managed package, all the Apex code in that package gets its own 150 DML statements. These DML statements are in addition to the 150 DML statements your org's native code can execute… Similarly, the certified managed package gets its own 100-SOQL-query limit for synchronous Apex" (`apexdev L19666–19671`). There is also a cumulative cross-namespace ceiling of 11× the per-namespace limit — 1,100 SOQL queries (`apexdev L19675–19680`). A monitor charting one namespace's numbers can show 40% headroom while the transaction is at the cumulative wall.

**When it occurs:** orgs running ISV packages that fire on the same objects as your triggers, especially where package code and native code both run in one save.

**How to avoid:** read the debug log's per-namespace block rather than a single number. `LIMIT_USAGE_FOR_NS` logs "Namespace and these limits" (`apexdev L38930–38944`) and the `CUMULATIVE_LIMIT_USAGE` block prints one such section per namespace (`apexdev L38274–38289`). Note the two lists differ: the emitted block includes maximum CPU time, while the documented `LIMIT_USAGE_FOR_NS` field list names "number of code statements" and several describe-call counters instead. Non-certified packages get no separate allocation — "the resources that they use continue to count against the same governor limits used by the org's custom code" (`apexdev L19684–19686`).

---

## Gotcha 6: `Test.startTest()` Adds a Limit Context, It Does Not Reset One

**What happens:** the guide is explicit that this is not a reset: "The `startTest` method does not refresh the context of the test: it adds a context to your test. For example, if your class makes 98 SOQL queries before it calls `startTest`, and the first significant statement after `startTest` is a DML statement, the program can now make an additional 100 queries. Once `stopTest` is called, however, the program goes back into the original context, and can only make 2 additional SOQL queries before reaching the limit of 100" (`apexdev L41442–41452`). A test that sets up 90 queries' worth of data, calls `startTest`, exercises a guard, then asserts *after* `stopTest` is running in a nearly exhausted context and can fail for reasons unrelated to the code under test.

**When it occurs:** exactly the tests this skill produces — a guard-threshold test has to consume real budget, so it is unusually close to the boundary on both sides of the block.

**How to avoid:** put every assertion that reads a `Limits` value inside the `startTest`/`stopTest` block, and keep bulk data setup in `@TestSetup` or before `startTest` so it does not eat the inner context. Each test method may call `startTest` and `stopTest` only once (`apexdev L41448`, `L41453`).

---

## Gotcha 7: `getHeapSize()` Is Documented As Approximate; `getCpuTime()` Is Not

**What happens:** `getHeapSize()` "returns the **approximate** amount of memory (in bytes) that has been used for the heap" (`apexrefguide L220711–220712`). `getCpuTime()` carries no qualifier: it "returns the CPU time (in milliseconds) that has been used in the current transaction" (`apexrefguide L220544–220545`). Teams routinely invert this — they treat a heap reading as exact and set a 95% trip point on it, then hit the ceiling at a reported 92%, and they hedge the CPU number they could have trusted.

**When it occurs:** heap guards with tight margins in code that builds large collections, where the gap between the reported figure and the enforced one is widest.

**How to avoid:** leave a wider margin on heap than on the other meters, and do not describe a heap number as exact in a log line or a dashboard. Email services are a separate case entirely: their heap is 50 MB, neither the 6 MB nor the 12 MB column (`apexdev L19650`).

---

## Gotcha 8: CPU Time Excludes Database Time and Callout Waits — But Not the App-Server Cost of DML

**What happens:** the footnote defining CPU time draws the line in a place people get half-right: "CPU time is calculated for the executing Apex code, and for any processes that are called from this code, such as package code and workflows… **Application server CPU time spent in DML operations is counted towards the Apex CPU limit.** Operations that don't consume application server CPU time aren't counted toward CPU time. For example, the portion of execution time spent in the database for DML, SOQL, and SOSL isn't counted, nor is waiting time for Apex callouts" (`apexdev L19645–19652`). So DML is not free on the CPU meter — only its database portion is excluded — and package code and workflow execution are charged to your budget.

**When it occurs:** callout-heavy integrations where `getCpuTime()` reads low against a long wall clock, and DML-heavy trigger cascades where the CPU reading is higher than the Apex line count suggests.

**How to avoid:** monitor `Limits.getCallouts()` alongside CPU for integration code — the ceiling is 100 per transaction with a 120-second cumulative timeout (`apexdev L19559–19562`). Bulk API and Bulk API 2.0 have their own CPU ceiling of 60,000 ms (`apexdev L19652–19653`). Separately, callouts are not allowed after DML in the same transaction: "By default, callouts aren't allowed after DML operations in the same transaction because DML operations result in pending uncommitted work" (`apexdev L35136–35137`) — a sequencing rule, not a limit, but it constrains the same code.

---

## Gotcha 9: `OrgLimits` Reports Consumed, REST `/limits` Reports Remaining, and Both Lag

**What happens:** `OrgLimit.getValue()` "returns the limit usage value" and `getLimit()` "returns the maximum allowed limit value" (`apexrefguide L226111`, `L226159`); its `toString()` prints `OrgLimit[DailyBulkApiBatches: consumed 25 of 15000]` (`apexrefguide L226190`). The REST resource returns the opposite pair: "Max is the limit for the org. Remaining is the number of calls or events left for the org" (`api_rest L2000–2002`). A poller that treats the two as interchangeable inverts every percentage, and the inversion is invisible at low consumption because 5% used and 5% remaining both look like small numbers on a fresh org.

**When it occurs:** any monitor that starts on the Apex class and later adds an external check, or vice versa.

**How to avoid:** name the field for what it holds (`Consumed__c`, not `Usage__c`) and assert the direction in a test. Neither surface is real-time: "Limit values are updated asynchronously, in near-real-time" (`apexrefguide L226081`, `L226215`), and "tabulated limits returned by the API are accurate within five minutes of resource consumption. For consistent values from this resource, avoid concurrent or rapid requests" (`api_rest L7792–7793`). These readings are a trend line, never a gate on a live transaction. `OrgLimits` also does not overlap the `Limits` class: "For comparison, the Limits Class returns Apex governor limits and not Salesforce API limits" (`apexrefguide L226213`).

---

## Gotcha 10: `getAsyncCalls()` and Three Other Meters Are Placeholders or Aliases

**What happens:** `getAsyncCalls()` and `getLimitAsyncCalls()` are documented, in full, as "Reserved for future use" (`apexrefguide L220473–220490`). A monitor that charts them charts a placeholder. Three more pairs are deprecated aliases that return another meter's value: `getRunAs()` and `getSavepoints()` and `getSavepointRollbacks()` all "return the same value as `getDMLStatements`" (`apexrefguide L220295–220305`), and `getFindSimilarCalls()` "returns the same value as `getSoslQueries`" (`apexrefguide L220246–220249`).

**When it occurs:** dashboards built by enumerating the `Limits` class method list rather than choosing meters deliberately — four of the lines are the DML line redrawn, and one is empty.

**How to avoid:** pick meters explicitly. The `ApexTestResultLimits` object does expose an `AsyncCalls` column (`object_reference L32590–32596`), which is a different thing from `Limits.getAsyncCalls()` — do not reason from one to the other.

---

## Gotcha 11: `OrgLimits` Cannot Be Mocked, and Neither Can Any Other System Type

**What happens:** a test for a limits poller naturally reaches for `Test.createStub()`. It does not apply here twice over. The Apex Stub API limitations list says "You can't mock the following Apex elements: Static methods (including future methods)… **System types**…" (`apexdev L42205–42211`), and `OrgLimits.getAll()` is a static method on a System type. There is also a namespace constraint: "The object being mocked must be in the same namespace as the call to the `Test.createStub()` method" (`apexdev L42201–42202`).

**When it occurs:** writing the first test for any class that reads `OrgLimits`, `Limits`, `UserInfo`, or `System.Request`. The test either asserts against whatever the running org happens to be consuming — which makes it non-deterministic across sandboxes — or it asserts nothing.

**How to avoid:** put a `@TestVisible` injection seam between the System call and the logic, with a plain DTO the test can construct. Assert the classification and row shape against injected readings; assert separately, and loosely, that the real read path returns something. Batchable classes cannot be stubbed either (`apexdev L42212`), so the same seam pattern applies to a Batch-based poller.

---

## Gotcha 12: DML Statements and DML Rows Are Two Independent Meters, and Bulkifying Only Moves One

**What happens:** Salesforce enforces "Total number of DML statements issued: 150" and, separately, "Total number of records processed as a result of DML statements, `Approval.process`, or `database.emptyRecycleBin`: 10,000" — the same in both the synchronous and asynchronous columns (`apexdev L19551–19554`). Replacing `update rec` inside a loop with one `update recList` collapses 200 statements into 1 and moves the row count not at all. Code that passed a bulkification review can still terminate on rows.

**When it occurs:** ETL-style Batch `execute` bodies, trigger handlers that cascade updates to children, and any migration path that touches tens of thousands of records across several bulk calls in one transaction.

**How to avoid:** guard both meters before a bulk DML, and size the second guard against the list you are about to commit rather than against current consumption. `getDMLStatements()` counts more than the DML keywords — `Approval.process`, `Database.convertLead`, `Database.emptyRecycleBin`, `Database.rollback`, `Database.setSavePoint`, `EventBus.publish` for events configured to publish after commit, and `System.runAs` all count against it (`apexdev L19623–19636`). When rows are the binding constraint, the fix is more Batch executions, not a bigger list: governor limits reset for each execution of `execute` (`apexdev L17712–17713`).

---

## Gotcha 13: A Heap Guard at Method Entry Measures Nothing the Method Will Do

**What happens:** heap consumption accumulates as the method allocates, so a single `getHeapSize()` check before the work reports the state of the caller, not of the collection about to be built. The synchronous ceiling is 6 MB and the asynchronous one 12 MB (`apexdev L19577`), and the reading itself is documented as approximate (`apexrefguide L220711`), so the margin between "looks fine at entry" and "terminated at 91%" is both wide and unsigned.

**When it occurs:** service methods that query large SObject lists and then build intermediate maps inside a loop, and Batch `execute` bodies whose scope was sized for SOQL rather than for the object graph the query returns.

**How to avoid:** check heap periodically inside the allocating loop rather than once at entry, and select only the fields the logic uses so each retrieved row costs less. UNVERIFIED (2026-09-05): the guides state the limit and that the reading is approximate, but do not document how per-field or per-record heap cost is computed, nor whether dereferencing a collection makes its memory reclaimable within the same transaction — treat "null out the list to free heap" as folklore and measure it in the target org before relying on it.
