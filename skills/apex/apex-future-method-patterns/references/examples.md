# Examples — Apex Future Method Patterns

Two worked scenarios and one anti-pattern. Each example assumes
`async-selection.md` has been consulted and `@future` is the right
mechanism (callout from trigger, fire-and-forget, no chaining
requirement).

---

## Example 1: HTTP callout from a record-triggered context

**Context:** When a Case transitions to `Status = 'Escalated'`, an
external incident-management system (PagerDuty / Opsgenie) needs to
be notified via HTTP POST. The trigger handler must not block the
user's save, and the external system's 5-second response time would
exceed Salesforce's synchronous-callout limit if 200 cases were
escalated in a single bulk update.

**Problem:** Practitioners try to call `Http.send()` directly from the
trigger handler. The first call works; the second fails with
`System.CalloutException: You have uncommitted work pending`, because
the trigger has already issued a DML and Salesforce won't release the
HTTP socket until the transaction commits. Wrapping in `@future`
without `callout=true` produces a clearer error:
`Callout from scheduled Apex or trigger cannot be performed`.

**Solution:**

```apex
public with sharing class CaseEscalationNotifier {
    public static void notifyForEscalations(
        List<Case> newCases,
        Map<Id, Case> oldMap
    ) {
        Set<Id> escalatedIds = new Set<Id>();
        for (Case c : newCases) {
            Case prior = oldMap?.get(c.Id);
            if (c.Status == 'Escalated'
                && (prior == null || prior.Status != 'Escalated')) {
                escalatedIds.add(c.Id);
            }
        }
        if (!escalatedIds.isEmpty()) {
            notifyPagerDuty(escalatedIds);
        }
    }

    @future(callout=true)
    public static void notifyPagerDuty(Set<Id> caseIds) {
        List<Case> cases = [
            SELECT Id, CaseNumber, Subject, Priority, OwnerId
              FROM Case
             WHERE Id IN :caseIds
        ];
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:PagerDuty/v2/enqueue');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setBody(JSON.serialize(new Map<String, Object>{
            'routing_key' => '${!$Credential.PagerDuty.RoutingKey}',
            'event_action' => 'trigger',
            'payload' => buildPayload(cases)
        }));
        HttpResponse res = new Http().send(req);
        if (res.getStatusCode() >= 400) {
            ApplicationLogger.error(
                'CaseEscalationNotifier',
                'PagerDuty returned ' + res.getStatusCode(),
                res.getBody()
            );
        }
    }
}
```

**Why it works:** The trigger handler does no callout itself — it
just collects `Id`s and enqueues one `@future` call. `callout=true`
licenses the method to issue HTTP requests *after* the trigger's
DML commits. The re-query inside the future is required: `@future`
can't accept `List<Case>`, so we round-trip through `Set<Id>` and
fetch fresh values, which has the bonus of seeing any post-trigger
field updates (e.g., a flow that runs after the trigger has set
`Owner.Email`).

---

## Example 2: Bulk-safe future invocation when caller may exceed 50/transaction

**Context:** A nightly batch job processes 10,000 ContentVersion
records and needs to push thumbnails to a CDN for each one. The
desired pattern is one `@future` per ContentVersion to maximize
parallelism, but the per-transaction limit is 50 future calls.

**Problem:** The naïve loop
`for (ContentVersion cv : versions) { uploadThumbnail(cv.Id); }`
fails with `LimitException: Too many future calls: 51` on the 51st
record. The fix is to chunk the work, but the chunking must produce
groups large enough that each future call has meaningful payload but
small enough to fit inside the future's 60s CPU budget.

**Solution:**

```apex
public class ThumbnailUploader {
    private static final Integer FUTURES_PER_TXN = 45;
    private static final Integer IDS_PER_FUTURE  = 250;

    public static void enqueueAll(List<Id> versionIds) {
        if (versionIds.size() > FUTURES_PER_TXN * IDS_PER_FUTURE) {
            throw new IllegalArgumentException(
                'Use Batch Apex for >' + (FUTURES_PER_TXN * IDS_PER_FUTURE) +
                ' versions; this caller exceeds the @future ceiling.'
            );
        }
        Set<Id> chunk = new Set<Id>();
        for (Id vid : versionIds) {
            chunk.add(vid);
            if (chunk.size() >= IDS_PER_FUTURE) {
                uploadChunk(chunk);
                chunk = new Set<Id>();
            }
        }
        if (!chunk.isEmpty()) {
            uploadChunk(chunk);
        }
    }

    @future(callout=true)
    public static void uploadChunk(Set<Id> versionIds) {
        try {
            for (ContentVersion cv : [
                SELECT Id, VersionData, FileType
                  FROM ContentVersion
                 WHERE Id IN :versionIds
            ]) {
                uploadToCdn(cv);
            }
        } catch (Exception e) {
            ApplicationLogger.error('ThumbnailUploader', e);
        }
    }
}
```

**Why it works:** 45 × 250 = 11,250 records per transaction, with a
5-call safety margin against the 50-future limit. The
`IllegalArgumentException` guards the calling code from silently
exceeding capacity — better to fail fast than to lose 49 records.
The `try/catch` inside the future is essential: an uncaught exception
in `@future` consumes one of the 5 platform-managed retries, then
disappears unless you've wired up an Apex Job error monitor.

---

## Anti-Pattern: Calling `@future` from another `@future`

**What practitioners do:** A future method calls a helper marked
`@future` to "fan out" work:

```apex
@future(callout=true)
public static void parentFuture(Set<Id> ids) {
    for (Id i : ids) {
        childFuture(new Set<Id>{i});  // boom
    }
}

@future
public static void childFuture(Set<Id> ids) { ... }
```

**What goes wrong:** Throws
`AsyncException: Future method cannot be called from a future or batch method.`
The platform refuses to nest async contexts of this type. Practitioners
hit this when modernizing an old "fan-out" Apex utility, or when an
LWC quick-action handler is itself wrapped in `@future` and tries to
delegate to existing infrastructure.

**Correct approach:** Switch the *outer* method to `Queueable`.
Queueable supports chaining (`System.enqueueJob(new ChildQueueable(...))`
from inside `execute()`), up to a depth of 5 in production and 1 in
test context. If the work doesn't need callouts and doesn't need
to chain, just collapse the two futures into one with the
combined `Set<Id>`. The decision matrix in
`standards/decision-trees/async-selection.md` will route you correctly:
any "I need to chain" requirement disqualifies `@future` entirely.
