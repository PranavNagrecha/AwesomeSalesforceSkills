# LLM Anti-Patterns — OmniStudio Asynchronous Data Operations

Scope: making an Integration Procedure that is too slow to run synchronously behave
correctly. Scale and volume design belongs to `architect/omnistudio-scalability-patterns`;
mapper-level tuning belongs to `omnistudio/dataraptor-transform-optimization`. This file is
about what changes for the caller when a step stops being synchronous.

## Anti-Pattern 1: Quoting OmniStudio timeout numbers that are actually Apex callout limits

The most-repeated numbers in this domain — "120 seconds", "10 seconds per callout" — are
**Apex callout limits**, and they matter here because an Integration Procedure's HTTP action
runs inside an Apex transaction. Presenting them as OmniStudio-specific settings sends people
looking for an OmniStudio configuration screen that will not explain them, and leaves the
governing constraint uncited.

The documented Apex figures are: a default callout timeout of **10 seconds**; a per-callout
timeout configurable between 1 millisecond and **120,000 milliseconds**; a **cumulative
120-second** limit across all callouts in a single transaction; and a maximum of **100**
callouts per transaction.

❌ "Integration Procedures time out at 120 seconds" asserted as a product limit with no
source.
✅ Name the layer the limit belongs to. The cumulative 120 seconds is what binds a chain of
HTTP actions in one transaction — three slow endpoints at 45 seconds each do not fit, no
matter how the procedure is arranged. Cite the Apex limit, because that is where the number
is documented and where it will be updated.

Source: Callout Limits and Limitations — default 10-second timeout, per-callout maximum of 120,000 ms, cumulative 120-second transaction limit, 100 callouts per transaction — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_timeouts.htm

## Anti-Pattern 2: Making a step asynchronous without changing the response contract

The defect that makes an async migration worse than the latency it fixed. When a step stops
running inline, the caller no longer receives that step's output — it receives an
acknowledgement. Generated code moves the work and leaves the OmniScript reading the same
response nodes, which are now absent, so the script renders empty values and reports success.

❌ Chain the step asynchronously and leave the consuming script mapping the same output path.
✅ Change the contract deliberately and make the two shapes distinguishable:

```json
{
  "synchronousResponse": {
    "status": "Accepted",
    "requestId": "a0X5g000000XyZaEAK",
    "pollAfterSeconds": 3
  },
  "note": "The order total is NOT in this response. It does not exist yet."
}
```

The consuming script needs an explicit in-progress state. "The value is not here yet" and
"the value is empty" have to be different states in the UI, or every slow request looks like
a data problem.

## Anti-Pattern 3: Treating a chained procedure's failure as something the caller will notice

Once a step runs outside the caller's transaction, its failure is outside the caller's error
path. The caller already returned successfully. Nothing propagates, so the failure is
invisible to the user, invisible to the OmniScript's error branch, and often invisible to
support until someone asks where their order went.

❌ Rely on the OmniScript's error handling to cover a chained step.
✅ Give the asynchronous work its own durable failure record and its own alert, and make the
polling path able to report failure as well as completion:

```apex
// The status record is the only thing that survives the caller's transaction.
public with sharing class AsyncRequestStatus {
    @AuraEnabled(cacheable=false)
    public static Map<String, Object> check(Id requestId) {
        Async_Request__c r = [
            SELECT Status__c, Failure_Reason__c, Result_Json__c
            FROM Async_Request__c
            WHERE Id = :requestId WITH USER_MODE LIMIT 1
        ];
        return new Map<String, Object>{
            'status'  => r.Status__c,               // Pending | Complete | Failed
            'error'   => r.Failure_Reason__c,       // populated only when Failed
            'payload' => r.Result_Json__c
        };
    }
}
```

A poll that can only return "not yet" turns a failure into an infinite spinner, which is the
worst of the available outcomes because it produces no support ticket with anything actionable
in it.

## Anti-Pattern 4: Reaching for asynchrony before removing the reason for the latency

Generated advice treats "it is slow" as a routing problem. Often it is not: the procedure
makes a call per record in a list, or repeats a lookup that could be fetched once, or
transforms in a place that costs more than it needs to. Making that asynchronous keeps every
one of those costs and adds a status object, a poll and a new failure mode.

❌ Chain first, measure later.
✅ Measure first. Where the time is one genuinely slow external system, asynchrony is the
right answer. Where it is N calls that could be one, or a repeated lookup, or a transform in
the wrong layer, fix that — the fastest asynchronous procedure is still slower than the
synchronous one you no longer need. Caching is documented for exactly the repeated-lookup
case, and applying it is a smaller change than restructuring the flow.

## Anti-Pattern 5: Enabling response caching without deciding what invalidates it

Caching is the cheapest latency fix available and the easiest to get wrong. A cached response
outlives the data it described, so a user who has just changed something sees the old value —
and because the write succeeded, they conclude the write failed and do it again.

❌ Turn caching on for the slow procedures and move on.
✅ Cache only what is genuinely slow-changing, and write down what makes each cached response
wrong. Anything that a user can change in the same session is a poor candidate regardless of
how expensive it is to fetch, because the confusing outcome — a stale read immediately after
a write — is worse than the latency. Where the value is both expensive and volatile, the
answer is usually to narrow what is cached rather than to shorten its lifetime.

Source: Cache for Omnistudio Data Mappers and Integration Procedures — https://help.salesforce.com/s/articleView?id=sf.os_cache_for_dataraptors_and_integration_procedures_48057.htm&type=5

## Anti-Pattern 6: Assuming steps run in parallel because they do not depend on each other

Wall-clock time is the reason to consider parallelism, and it is routinely asserted rather
than configured. Independent actions do not become concurrent by being independent — the
procedure runs its actions in the order it holds them unless configured otherwise, so a
claimed reduction from "6 seconds sequential to 3.5 parallel" is a prediction until the
configuration says so and a measurement confirms it.

❌ Describe two calls as parallel because neither uses the other's output.
✅ Confirm what the procedure is actually configured to do, and measure the result. Keep in
mind that parallelism does not help against the cumulative 120-second transaction limit in the
way it helps wall-clock time — that limit is additive across callouts, so running them
concurrently does not create room that was not there.

## Anti-Pattern 7: No record of what ran

The failure that turns a five-minute diagnosis into a day. Once work is split across
transactions, "did step 3 run" is not answerable from the caller's session, and OmniStudio's
own execution history is not a substitute for a correlation id you control.

❌ Debug an async chain from the user's description of what they saw.
✅ Generate a correlation id in the synchronous entry point, carry it into every chained step
and into the status record, and log against it. It costs one field and one parameter, and it
is the difference between reconstructing a failure and guessing at it — particularly when the
user's session ended long before the work did.
