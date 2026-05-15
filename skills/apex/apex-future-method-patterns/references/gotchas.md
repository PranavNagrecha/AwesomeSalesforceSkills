# Gotchas — Apex Future Method Patterns

Non-obvious Salesforce platform behaviors that bite production-grade
`@future` code. These are distinct from the `Salesforce-Specific
Gotchas` section in `SKILL.md` — each entry here surfaces a behavior
that only shows up under bulk load or specific test/timing conditions.

## Gotcha 1: `@future` calls are NOT guaranteed to run after a transaction commits

**What happens:** Most documentation says "`@future` runs after the
transaction commits." It's a useful approximation, not a guarantee.
The platform's scheduler may take seconds (typically <10) or minutes
(under load), and during high-volume releases the queue depth can
exceed an hour. There is no SLA on `@future` execution latency.

**When it occurs:** End-of-quarter heavy DML days (large data loads,
deployment refreshes), or when an org's `AsyncApexJobs` queue is
backed up by a Batch Apex job iterating millions of records. The
queue is FIFO across all async types within the same scheduler
priority, so a `@future` queued behind a multi-hour batch waits its
turn.

**How to avoid:** Never design UX that relies on `@future` work
having visibly completed. If a user-facing flow needs "post-save
confirmation" of the async result, switch to Queueable + Platform
Events (publish from `execute()`, subscribe in LWC via empApi)
so the UI gets a push notification on completion. If the operation
absolutely must run before the user sees the next page, it's not
async work — make it synchronous and accept the latency.

---

## Gotcha 2: A trigger that fires another trigger can blow the per-transaction limit silently

**What happens:** Trigger A inserts records that cause Trigger B to
fire. Both call `@future` methods. Each contributes to the same
**transaction**-level 50-future limit, but neither author of the
two triggers knows about the other. The first user to hit a bulk
update that touches both objects sees
`LimitException: Too many future calls: 51` from a stack trace that
doesn't obviously implicate either trigger.

**When it occurs:** Master-detail relationships where parent updates
cascade. Common pairing: an `Opportunity` trigger that creates
`OpportunityLineItem` rows, and the line-item trigger fires its
own `@future` for pricing. A bulk update of 50 Opportunities that
each have one line item is fine for line-item triggers alone, but
adding the Opportunity-side `@future` (which fires once per
Opportunity) puts the transaction at 50+50=100 futures.

**How to avoid:** Account for the transaction-wide limit, not just
your own trigger's contribution. Wrap `@future` calls behind a
`TriggerControl.hasRunFuture(handlerName)` static-flag check so
re-entrant fires don't double-spend. Better long-term: consolidate
the `@future` work into a single Queueable enqueued from the last
`after`-trigger handler.

---

## Gotcha 3: Mocking HTTP callouts in `@future` requires `Test.setMock` AT INVOCATION TIME, not at enqueue time

**What happens:** A test method does
`Test.setMock(HttpCalloutMock.class, new MyMock())`, then calls a
method that internally enqueues a `@future(callout=true)`, then
calls `Test.stopTest()`. The future runs but throws
`System.CalloutException: Unauthorized endpoint` — the mock never
attached. The test fails in an undebuggable way because
`Test.setMock` *appears* to have been called.

**When it occurs:** The mock is attached to the **outer** transaction
context. When `Test.stopTest()` boundaries a `@future`, the future
runs in a *new* test transaction that inherits some state but not
others. The HTTP callout mock registration is one of the bits that
does not propagate.

**How to avoid:** Call `Test.setMock(...)` inside `Test.startTest()`
*and* re-register the mock inside the future's test path if needed.
A safer pattern is to mock the *enqueue* itself: make the calling
class accept an `IFutureEnqueuer` interface, inject a no-op enqueuer
in unit tests, and write a separate integration test that exercises
the `@future` method body directly (as a static method, callable
from a test without `@future` semantics).

---

## Gotcha 4: `Test.startTest`/`Test.stopTest` doesn't reset the 50-future counter, just the limit window

**What happens:** A test does heavy setup before `Test.startTest()`
that triggers 49 `@future` calls (e.g., creating 50 records with a
trigger that enqueues one future each). Then inside the test
window, a single future call throws
`LimitException: Too many future calls: 51` even though
`Limits.getFutureCalls()` is reset by `Test.startTest()`.

**When it occurs:** When the test data setup itself fires the
production trigger code. The `@future` calls from setup count
against the same governor budget as the test's "real" calls — the
counter is reset, but the platform's scheduler-level queue
tracking is not. This is poorly documented and surfaces only at
volume.

**How to avoid:** Use `Test.startTest()` *immediately* after
inserting setup data, and use `TriggerControl.bypass(...)` (or
`System.runAs(setupUser)` with a permission-set bypass) during
setup to prevent triggers from firing futures. Validate by adding
`System.assertEquals(0, Limits.getFutureCalls(), 'no futures from setup')`
before the test's real action.

---

## Gotcha 5: An `@future` that fails 5 times is silently dropped — there is no dead-letter queue

**What happens:** A `@future(callout=true)` method calls an external
service that's been down for an hour. The first invocation fails;
the platform retries 4 more times with exponential backoff
(roughly: 1m, 5m, 15m, 30m, 60m). All 5 fail. The platform marks
the job as `Failed` in `AsyncApexJob` and *moves on*. There is no
re-queue mechanism, no automatic alert, and the data the future
was meant to push never makes it out.

**When it occurs:** Any callout against a service with low
availability. Also happens when a callout body exceeds the
6 MB request limit and Salesforce treats it as malformed — every
retry fails identically and you've burned 5 attempts on a payload
issue.

**How to avoid:** Build a fallback: log every `@future` invocation
to a custom `Async_Job_Log__c` object on enqueue, mark
`Status__c = 'Completed'` at the end of `execute()`, and run a
scheduled Batch Apex job nightly that finds rows still
`'In Progress'` after 24 hours and re-enqueues them. For
callouts specifically, prefer Platform Events (built-in retry
+ dead-letter via subscriber error handling) over `@future` when
the external service's availability is < 99%.
