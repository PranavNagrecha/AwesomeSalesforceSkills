# Examples — Salesforce Functions Replacement

Worked artifacts for the replacement patterns in `SKILL.md`.

---

## Example 1: Inventory the invocation sites, not the Functions project

**Context:** A team believes it has three Functions left. The Functions project
directory has three. The org has eleven invocation sites.

**Problem:** Functions were invoked from Apex by name, so the authoritative
inventory lives in the org, not in the repo. Anything invoked from a rarely-run
path (annual close, quarterly reconciliation) has been failing silently since
the January 31, 2025 retirement without anyone raising a case.

**Solution:** Query the Tooling API for the call sites, then reconcile.

```bash
# Every Apex class or trigger that still references the Functions API.
sf data query --use-tooling-api --target-org prod \
  --query "SELECT Name, NamespacePrefix FROM ApexClass WHERE Body LIKE '%Function.get(%'"

sf data query --use-tooling-api --target-org prod \
  --query "SELECT Name FROM ApexTrigger WHERE Body LIKE '%Function.get(%'"

# Historical invocation records, if the object still resolves in this org.
# FunctionInvocationRequest was available from API 51.0 and tracks async
# invocations; treat a query failure here as one more signal, not a blocker.
sf data query --target-org prod \
  --query "SELECT Status, CreatedDate FROM FunctionInvocationRequest ORDER BY CreatedDate DESC LIMIT 50"
```

**Why it works:** `Body LIKE` against the Tooling API is the only reliable way to
find call sites in code you did not write, including managed-package-adjacent
classes and one-off utilities. The migration is complete when this query returns
zero rows — not when the Functions directory is empty.

---

## Example 2: Long-running workload — async handoff, not a synchronous callout

**Context:** A Function rendered a 40-page PDF from Opportunity data. Runtime was
45–90 seconds.

**Problem:** Ported straight onto a Heroku web dyno it hits the router's
non-configurable 30-second cap: error `H12`, the client gets an error page, and
the dyno keeps working on the dead request. Apex's own ceiling does not help —
`setTimeout` maxes at 120,000 ms, but the request is gone at 30 s regardless.

**Solution:** Accept-and-callback. Apex submits, the service returns immediately,
a worker does the work and publishes the result back.

```apex
public with sharing class DocumentRenderQueueable implements Queueable, Database.AllowsCallouts {

    private final Set<Id> opportunityIds;

    public DocumentRenderQueueable(Set<Id> opportunityIds) {
        this.opportunityIds = opportunityIds;
    }

    public void execute(QueueableContext ctx) {
        // One batched callout for the whole set — never one per record.
        HttpClient.Response res = new HttpClient()
            .namedCredential('DocumentRenderer')   // Named Credential, no raw endpoint
            .path('/v1/render-jobs')
            .method('POST')
            .header('Content-Type', 'application/json')
            .body(JSON.serialize(new Map<String, Object>{
                'opportunityIds' => new List<Id>(opportunityIds),
                'callbackTopic'  => 'Document_Render_Complete__e'
            }))
            .timeoutMs(20000)                       // submit is fast; render is not
            .retryOnTransient(true)
            .send();

        if (!res.isSuccess()) {
            throw new CalloutException(
                'Render submit failed: ' + res.statusCode + ' ' + res.status);
        }
        // res.body carries { "jobId": "..." }. The worker publishes
        // Document_Render_Complete__e when the render finishes; a trigger on
        // that Platform Event attaches the file and updates the record.
    }
}
```

```json
// The service's immediate response — work has been accepted, not completed.
HTTP/1.1 202 Accepted
{
  "jobId": "rnd_01JQ8F3K2M",
  "status": "queued",
  "estimatedSeconds": 75
}
```

**Why it works:** The Apex transaction ends in well under a second, so nothing
competes for the 120-second cumulative callout budget or the 100-callout
transaction limit. The 45–90 second render happens on a worker dyno with no
router in front of it. `HttpClient` is the repo's canonical callout wrapper
(`templates/apex/HttpClient.cls`) — it builds `callout:<NamedCredential><path>`
and exposes `.timeoutMs()`, `.retryOnTransient()` and a `Response` with
`isSuccess()`/`isTransient()`, so the retry and error-shape decisions are not
re-litigated per migration.

---

## Example 3: Short, standard-library workload — rewrite in Apex, in the right context

**Context:** A Node Function normalised addresses and computed a score. No
external libraries beyond string handling. Median runtime 900 ms.

**Problem:** This does belong in Apex, but the original invocation was from an
Account trigger. Leaving it there gives the rewrite the **synchronous** limits —
10,000 ms CPU and 6 MB heap — instead of the asynchronous 60,000 ms and 12 MB.
At 200 records per batch the CPU headroom disappears.

**Solution:** Move the entry point, not just the language.

```apex
// Trigger handler: enqueue rather than compute inline.
public with sharing class AccountTriggerHandler extends TriggerHandler {

    protected override void afterInsert() {
        System.enqueueJob(new AccountScoreQueueable(Trigger.newMap.keySet()));
    }
}
```

```apex
public with sharing class AccountScoreQueueable implements Queueable {

    private final Set<Id> accountIds;

    public AccountScoreQueueable(Set<Id> accountIds) {
        this.accountIds = accountIds;
    }

    public void execute(QueueableContext ctx) {
        List<Account> toUpdate = new List<Account>();
        for (Account a : [
                SELECT Id, BillingStreet, BillingPostalCode
                FROM   Account
                WHERE  Id IN :accountIds
                WITH USER_MODE
        ]) {
            a.Address_Score__c = AddressScorer.score(a);
            toUpdate.add(a);
        }
        update as user toUpdate;
    }
}
```

**Why it works:** The Queueable runs asynchronously, so the rewrite gets 60,000
ms CPU and 12 MB heap, and a slow scoring pass no longer lengthens the user's
save. `WITH USER_MODE` and `update as user` are the current security idiom —
`WITH SECURITY_ENFORCED` was removed in API 67.0 (Summer '26), which also made
user mode and `with sharing` the defaults for classes on that API version.
`TriggerHandler` is the repo's canonical base class (`templates/apex/TriggerHandler.cls`).

---

## Anti-Pattern: One callout per record

**What practitioners do:** Replace `Function.get('ns.enrich').invoke(record)`
with an `HttpRequest` in the same loop, one call per record, because that is what
the Function signature looked like.

**What goes wrong:** Functions ran outside the Apex transaction and did not
consume its budget. A callout does. At 101 records the transaction dies on the
**100 callouts per transaction** limit; before that it dies on the 120-second
cumulative callout timeout, since even ten calls at a 15-second timeout exceed
it. The unit test with one record passes, and the first real bulk load fails.

**Correct approach:** Batch the payload. One callout carrying `N` records, with
the service returning `N` results keyed by Id — or, for genuinely large volumes,
invert the direction entirely: publish a Platform Event and let the external
service pull from the Bulk API on its own schedule. The migration's job is to put
the work back *outside* the transaction, which is where Functions had it.
