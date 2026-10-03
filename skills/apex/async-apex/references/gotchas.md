# Gotchas: Async Apex

Non-obvious Salesforce platform behaviors that cause real production problems in this domain. Line numbers refer to the pdftotext extraction of the Apex Developer Guide PDF, release 262 (`salesforce_apex_developer_guide.pdf`).

## Gotcha 1: One child Queueable per executing Queueable, and one enqueue in any async context

**What happens:** A Queueable, Batch `execute`, or future method enqueues a second job and gets a `LimitException`.

**When it occurs:** When a worker tries to fan out from an async context.

**How to avoid:** Chain exactly one next job. Fan out from the synchronous entry point (up to 50 enqueues) or redesign with Batch, Cursors, or Platform Events.

**Source:** Apex Developer Guide (262), Per-Transaction Apex Limits, "Maximum number of Apex jobs added to the queue with System.enqueueJob": 50 synchronous, 1 asynchronous (L19573); "Queueable Apex Limits": "Only one child job can exist for each parent queueable job."

---

## Gotcha 2: A rollback discards the Queueables it enqueued

**What happens:** The trigger enqueued a sync job, the transaction later failed, and the job never ran. Nothing is logged.

**When it occurs:** When the enqueue happens before validation, a later trigger, or a DML failure rolls the transaction back.

**How to avoid:** Treat the enqueue as part of the transaction. If the job must run even when the user's save fails, publish a platform event configured to publish immediately or log the request separately.

**Source:** Apex Developer Guide (262), "Queueable Apex": "If an Apex transaction rolls back, any queueable jobs queued for execution by the transaction aren't processed." Platform Events Developer Guide (262): with the Publish Immediately behavior, "If the transaction fails and is rolled back, the event message is still published and can't be rolled back."

---

## Gotcha 3: Future methods are blocked from Batch and future contexts

**What happens:** A Batch `execute` that calls a future method fails.

**When it occurs:** When existing future-based helpers are reused from batch or future code.

**How to avoid:** From Batch, enqueue one Queueable per `execute` or make callouts directly in a batch that implements `Database.AllowsCallouts`. Future calls from a Queueable are allowed (50), though Salesforce discourages fanning out many.

**Source:** Apex Developer Guide (262), Per-Transaction Apex Limits, "Maximum number of methods with the future annotation allowed per Apex invocation": 50 synchronous; "0 in batch and future contexts; 50 in queueable context" (L19568 to L19571); "Future Method Considerations." The exact exception text is UNVERIFIED (2026-10-03).

---

## Gotcha 4: Future parameters are primitives, and order is not guaranteed

**What happens:** A future method receives a stale record, or two future calls run in the opposite order to the calls.

**When it occurs:** When sObjects are serialized into strings to get around the parameter rule, or logic depends on call order.

**How to avoid:** Pass IDs and re-query inside the method. Do not depend on execution order; use a single Queueable for ordered steps.

**Source:** Apex Developer Guide (262), "Future Annotation": parameters "must be primitive data types, arrays of primitive data types, or collections of primitive data types"; "Future Method Considerations": the method "doesn't necessarily execute in the same order that it's called in"; "Future Methods": the sObject "can change between the time that you call the method and the time that it executes."

---

## Gotcha 5: Scheduled Apex runs with synchronous limits and no synchronous callouts

**What happens:** A scheduler that processes data inline hits the 100-query or 10,000 ms CPU limit, or a callout from `execute` fails.

**When it occurs:** When the scheduler does the work instead of dispatching it.

**How to avoid:** Keep the scheduler thin: enqueue a callout-capable Queueable or start a Batch. Mark member variables `transient` if they must not persist between runs.

**Source:** Apex Developer Guide (262), Per-Transaction Apex Limits note: "Although scheduled Apex is an asynchronous feature, synchronous limits apply to scheduled Apex jobs" (L19536); "Apex Scheduler Notes and Best Practices": "Synchronous Web service callouts aren't supported from scheduled Apex" and member variables persist between runs.

---

## Gotcha 6: Batch slots and the flex queue are small

**What happens:** `Database.executeBatch` throws `LimitException`, or jobs sit in Holding for hours.

**When it occurs:** When triggers or `finish` methods start batches per event. Only 5 batch jobs are queued or active, the flex queue holds 100 more, and only one `start` method runs at a time.

**How to avoid:** Start batches from a single dispatcher, check flex-queue depth (`AsyncApexJob` with Status = 'Holding') before submitting, or use Cursors with chained Queueables.

**Source:** Apex Developer Guide (262), Salesforce Platform Apex Limits: batch jobs queued or active concurrently 5, flex queue Holding 100, start method concurrent executions 1 (L19779 to L19783); "Holding Batch Jobs in the Apex Flex Queue": "If the Apex flex queue has the maximum number of 100 jobs, Database.executeBatch throws a LimitException."

---

## Gotcha 7: Batch scope above 2,000 is silently re-chunked, and 50 million rows is a hard stop

**What happens:** A scope of 5,000 behaves like 2,000. A locator that returns more than 50 million rows fails the job immediately.

**When it occurs:** With `Database.getQueryLocator` and an oversized scope, or an unfiltered query on a huge object.

**How to avoid:** Use a scope that is a factor of 2,000 (100, 200, 400) and filter the locator query.

**Source:** Apex Developer Guide (262), "Batch Apex Governor Limits": QueryLocator scope maximum 2,000; "A maximum of 50 million records can be returned in the Database.QueryLocator object. If more than 50 million records are returned, the batch job is immediately terminated and marked as Failed."

---

## Gotcha 8: The daily async allowance is shared and checked up front

**What happens:** A large batch refuses to start with an `AsyncApexExecutions Limit exceeded` exception even though it has not run a single scope.

**When it occurs:** When Batch, Queueable, scheduled, and future executions together approach 250,000 (or 200 per license) in 24 hours.

**How to avoid:** Monitor `DailyAsyncApexExecutions` through the REST limits resource or `OrgLimits`, and reduce per-record jobs.

**Source:** Apex Developer Guide (262), Salesforce Platform Apex Limits (L19732 to L19736) and footnote 7: "Batch Apex preemptively checks the required asynchronous job capacity."

---

## Gotcha 9: Async tests only run at Test.stopTest(), and Batch runs one execute

**What happens:** Assertions made before `Test.stopTest()` fail, and a batch test with more rows than one scope does not exercise later scopes.

**When it occurs:** When tests treat async calls as immediate.

**How to avoid:** Wrap the enqueue or `executeBatch` in `Test.startTest()` and `Test.stopTest()`, assert afterwards, and size data to one scope.

**Source:** Apex Developer Guide (262), "Testing Future Methods" ("When stopTest is executed, all asynchronous processes are run synchronously") and "Testing Batch Apex" ("you can test only one execution of the execute method").

---

## Gotcha 10: Deploying a scheduled class fails while jobs are pending, and refreshes drop schedules

**What happens:** A deployment fails with "This schedulable class has jobs pending or in progress," and after a sandbox refresh the nightly job is missing.

**When it occurs:** On releases that change a scheduled class or its dependencies, and after every sandbox refresh.

**How to avoid:** Delete the scheduled job, deploy, and reschedule. Add rescheduling to the post-refresh runbook.

**Source:** Apex Developer Guide (262), "Apex Scheduler Notes and Best Practices."
