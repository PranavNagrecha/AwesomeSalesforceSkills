# Examples — OmniStudio Asynchronous Data Operations

## Example 1: A checkout that could not fit inside one transaction

**Context:** An OmniScript checkout calling three external systems — pricing, credit and
fulfilment — through HTTP actions in a single Integration Procedure.

**Problem:** Two of the three endpoints were slow. Because the actions ran in one Apex
transaction, their timeouts were additive: the cumulative callout allowance for a transaction
is 120 seconds, and three endpoints given generous individual timeouts do not fit inside it
regardless of how the procedure is arranged. The first fix raised each callout's timeout,
which made the failure arrive later rather than not at all.

**Solution:** Split at the transaction boundary. A synchronous entry point records the
request and returns immediately; the slow work runs afterwards against that record; the UI
polls.

```apex
// Synchronous entry point: writes the request, returns an acknowledgement, ends fast.
public with sharing class CheckoutRequestService {

    @AuraEnabled
    public static Map<String, Object> submit(String cartJson) {
        Async_Request__c req = new Async_Request__c(
            Status__c         = 'Pending',
            Correlation_Id__c = generateCorrelationId(),   // carried into every later step
            Payload_Json__c   = cartJson
        );
        insert req;

        // Hand off. Nothing slow happens inside this transaction.
        System.enqueueJob(new CheckoutWorker(req.Id));

        return new Map<String, Object>{
            'status'           => 'Accepted',
            'requestId'        => req.Id,
            'correlationId'    => req.Correlation_Id__c,
            'pollAfterSeconds' => 3
            // NOTE: the order total is deliberately absent. It does not exist yet.
        };
    }

    private static String generateCorrelationId() {
        return EncodingUtil.convertToHex(Crypto.generateAesKey(128)).substring(0, 16);
    }
}
```

```apex
// Status endpoint: must be able to report FAILURE, not only "not yet".
public with sharing class CheckoutStatusService {

    @AuraEnabled(cacheable=false)
    public static Map<String, Object> check(Id requestId) {
        Async_Request__c r = [
            SELECT Status__c, Failure_Reason__c, Result_Json__c, Correlation_Id__c
            FROM Async_Request__c
            WHERE Id = :requestId WITH USER_MODE
            LIMIT 1
        ];
        return new Map<String, Object>{
            'status'        => r.Status__c,           // Pending | Complete | Failed
            'error'         => r.Failure_Reason__c,   // populated only when Failed
            'payload'       => r.Result_Json__c,
            'correlationId' => r.Correlation_Id__c    // quote this in a support ticket
        };
    }
}
```

**Why it works:** the constraint being respected is a transaction boundary, not a
configuration setting. Once the slow calls are outside the user's transaction, the cumulative
callout allowance applies to a much smaller unit of work and the individual timeouts can stay
sensible.

**The contract change that has to happen with it:** the synchronous response no longer
contains the order total, so any consumer still reading that node now reads nothing. "Not
computed yet" and "empty" must be different states in the UI, or every slow request presents
as a data defect. This is the step most async migrations skip, and it is the one that makes
them look like a regression.

**Why the status endpoint reports failure explicitly:** the caller's transaction has already
returned successfully, so a later failure propagates nowhere — not to the user, not to the
OmniScript's error branch. A poll that can only answer "not yet" converts a failure into an
infinite spinner, and an infinite spinner produces a support ticket with nothing actionable
in it.

**The correlation id is not decoration.** Once work spans transactions, "did the credit step
run" is unanswerable from the user's session. One field and one parameter is the difference
between reconstructing the failure and guessing.

---

## Example 2: Removing the latency instead of moving it

**Context:** A procedure that enriched a list of records, taking around six seconds, which
the team planned to make asynchronous.

**Problem:** The six seconds were not one slow system. The procedure made one external call
per record in the list and re-fetched the same reference data on each iteration. Making that
asynchronous would have kept every one of those costs and added a status record, a polling
loop and a new class of invisible failure — for a request that could simply be made fast.

**Solution:** Measure first, then fix what the measurement points at. Asynchrony stayed on
the shelf.

```apex
// Before restructuring anything, find out where the time and the callouts actually go.
public class ProcedureProfiler {
    public static void report(String label) {
        System.debug(LoggingLevel.INFO, String.format(
            '{0} | callouts {1}/{2} | cpu {3}/{4} ms | queries {5}/{6}',
            new List<Object>{
                label,
                Limits.getCallouts(),   Limits.getLimitCallouts(),      // 100 per transaction
                Limits.getCpuTime(),    Limits.getLimitCpuTime(),
                Limits.getQueries(),    Limits.getLimitQueries()
            }));
    }
}
```

```json
// The finding, and the two changes that followed from it.
{
  "measured": {
    "externalCallouts": 40,
    "note": "one per record — the endpoint accepts a batch, so this was 40 calls doing the work of 1"
  },
  "changes": [
    {
      "change": "batch the enrichment call",
      "why": "the cumulative 120-second callout allowance is additive across calls, so 40 calls consume it 40 times over even when each is fast"
    },
    {
      "change": "cache the reference lookup",
      "why": "the same slow-changing data was fetched once per record; it changes daily, and no user can change it mid-session, which is what makes it a safe thing to cache"
    }
  ],
  "result": "well inside the synchronous budget — no status record, no poll, no new failure mode"
}
```

**Why it works:** the six seconds were a call-per-record problem wearing the costume of a
latency problem. Asynchrony is the right answer when the time is one genuinely slow external
system; it is the wrong answer when the time is N calls that could be one, because the
fastest asynchronous procedure is still slower than the synchronous one you no longer need.

**The rule applied to the caching decision:** the reference data was cached because a user
cannot change it during their session. Anything a user *can* change in-session is a poor
cache candidate no matter how expensive it is to fetch — a stale read immediately after a
successful write reads as "my change did not save", and the user does it again. Decide what
makes each cached response wrong before enabling it, not afterwards.

**On parallelism, if it comes up next:** independent actions do not become concurrent by
being independent, so any "6 seconds sequential becomes 3.5 parallel" claim is a prediction
until the configuration says so and a measurement confirms it. And it would not have helped
the real problem here: the cumulative callout limit is additive across a transaction, so
running calls concurrently does not create allowance that was not there.
