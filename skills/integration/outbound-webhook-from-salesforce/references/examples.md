# Examples — Outbound Webhook From Salesforce

A complete outbox-based webhook producer, built up in the order you would build
it. Every platform construct is from the Apex Developer Guide, the Apex Reference
Guide, or the Metadata API Developer Guide (Summer '26, API 67.0). The HTTP layer
delegates to [`templates/apex/HttpClient.cls`](../../../../templates/apex/HttpClient.cls)
rather than re-implementing retry, timeout, and Named Credential enforcement.

---

## Example 1: The outbox object

**Context:** an Order status change must reach a fulfilment partner's HTTPS
endpoint, at least once, in roughly real time.

**Problem:** the callout cannot happen in the transaction that changes the
Order — *"You can't make a callout when there are pending operations in the same
transaction. Things that result in pending operations are DML statements…"* — and
a retry that lives inside a transaction cannot outlive that transaction's
governor limits. Both problems are solved by persisting the *intent to deliver*
and treating the actual delivery as a separate, resumable job.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/objects/Webhook_Delivery__c/Webhook_Delivery__c.object-meta.xml -->
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Webhook Delivery</label>
    <pluralLabel>Webhook Deliveries</pluralLabel>
    <nameField>
        <label>Delivery Number</label>
        <type>AutoNumber</type>
        <displayFormat>WD-{00000000}</displayFormat>
    </nameField>
    <deploymentStatus>Deployed</deploymentStatus>
    <sharingModel>Private</sharingModel>
</CustomObject>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- .../fields/Idempotency_Key__c.field-meta.xml
     The single most important field in the design. External Id + Unique makes
     "have we already queued this event?" a database constraint rather than a
     race condition, and it is the value the receiver deduplicates on. -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Idempotency_Key__c</fullName>
    <label>Idempotency Key</label>
    <type>Text</type>
    <length>128</length>
    <externalId>true</externalId>
    <unique>true</unique>
    <caseSensitive>true</caseSensitive>
</CustomField>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- .../fields/Next_Attempt_At__c.field-meta.xml
     The sweeper's query predicate. Everything overdue is everything with
     Status__c = 'Pending' AND Next_Attempt_At__c <= NOW(). -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Next_Attempt_At__c</fullName>
    <label>Next Attempt At</label>
    <type>DateTime</type>
</CustomField>
```

The remaining fields, abbreviated: `Status__c` (Picklist —
`Pending` / `Sent` / `Failed` / `Dead`), `Attempt_Count__c` (Number),
`Payload__c` (Long Text Area), `Last_Status_Code__c` (Number),
`Last_Error__c` (Long Text Area), `Endpoint_Name__c` (Text — the Named
Credential developer name), and `Correlation_Id__c` (Text).

**Why it works:** the row is written by the same DML transaction that changed the
Order, so the change and the intent to deliver commit or roll back together.
There is no window in which the Order is updated and the webhook was never
queued.

**Retention is a design decision, not an afterthought.** `Payload__c` holds
whatever you send, which for most integrations is customer data. Set a deletion
policy for `Sent` rows and restrict the object to the integration's permission
set, or accept that you have built a second, less governed copy of your order
data.

---

## Example 2: Enqueue in the transaction, deliver outside it

### The trigger side — DML only, no callout

```apex
public with sharing class OrderWebhookProducer {

    private static final String ENDPOINT = 'Fulfilment_Partner';

    /**
     * Called from the after-update handler. Writes one delivery row per changed
     * order and enqueues a single job for the whole batch.
     *
     * Deliberately does NOT call out. The transaction has pending DML, so a
     * callout here throws CalloutException("You have uncommitted work pending")
     * and rolls back the user's save.
     */
    public static void queueStatusChanges(
            List<Order> newOrders, Map<Id, Order> oldMap) {

        List<Webhook_Delivery__c> rows = new List<Webhook_Delivery__c>();

        for (Order o : newOrders) {
            Order prior = oldMap.get(o.Id);
            if (prior != null && prior.Status == o.Status) {
                continue;
            }

            // The idempotency key must be stable for this logical event and
            // different for every other one. Record id + the field that
            // changed + the value it changed to is stable across retries and
            // across a re-run of the same trigger.
            String key = o.Id + ':status:' + o.Status;

            rows.add(new Webhook_Delivery__c(
                Idempotency_Key__c = key,
                Endpoint_Name__c   = ENDPOINT,
                Status__c          = 'Pending',
                Attempt_Count__c   = 0,
                Next_Attempt_At__c = DateTime.now(),
                Correlation_Id__c  = String.valueOf(Request.getCurrent().getRequestId()),
                Payload__c         = buildPayload(o)
            ));
        }

        if (rows.isEmpty()) {
            return;
        }

        // Upsert on the External Id rather than insert. A retried save, a
        // recursive trigger, or a mass update that touches the same record twice
        // then converges on one row instead of throwing DUPLICATE_VALUE.
        Database.upsert(rows, Webhook_Delivery__c.Idempotency_Key__c, false);

        // ONE job for the batch, not one per record. A 10,000-row data load
        // enqueuing one Queueable per record exhausts the async allocation and
        // takes the org's other async work down with it.
        System.enqueueJob(new WebhookDeliveryJob());
    }

    /**
     * Absolute state plus a version — never a delta. Every retrying design
     * reorders deliveries, and an absolute payload is safe to apply twice and
     * out of order. A delta is not.
     */
    private static String buildPayload(Order o) {
        return JSON.serialize(new Map<String, Object>{
            'schemaVersion' => 'v1',
            'eventType'     => 'order.status_changed',
            'occurredAt'    => DateTime.now().formatGmt("yyyy-MM-dd'T'HH:mm:ss'Z'"),
            'resource'      => new Map<String, Object>{
                'type'    => 'Order',
                'id'      => o.Id,
                'number'  => o.OrderNumber,
                'status'  => o.Status,
                'version' => o.SystemModstamp.getTime()
            }
        });
    }
}
```

### The delivery side — a bounded batch

```apex
/**
 * Delivers overdue webhook rows.
 *
 * Database.AllowsCallouts is a marker interface: "Apex allows HTTP and web
 * service callouts from queueable jobs, if they implement the
 * Database.AllowsCallouts marker interface. In queueable jobs that implement
 * this interface, callouts are also allowed in chained queueable jobs."
 * Omitting it produces a runtime CalloutException, not a compile error.
 */
public with sharing class WebhookDeliveryJob
        implements Queueable, Database.AllowsCallouts {

    /**
     * Sized against the transaction budget, not against convenience.
     * The cumulative callout timeout for one transaction is 120 seconds. At the
     * 8-second per-callout timeout set below, 10 deliveries consume at most 80
     * seconds, leaving headroom for a slow tail. Raising this without lowering
     * the timeout is how a job starts dying at the 120-second ceiling.
     */
    private static final Integer BATCH_SIZE     = 10;
    private static final Integer CALLOUT_MS     = 8000;
    private static final Integer MAX_ATTEMPTS   = 8;

    public void execute(QueueableContext ctx) {

        // A finalizer runs whether or not this job throws, and is the only
        // reliable place to react to an unhandled exception in a Queueable.
        // "Only one finalizer instance can be attached to any Queueable job."
        System.attachFinalizer(new WebhookDeliveryFinalizer());

        List<Webhook_Delivery__c> due = [
            SELECT Id, Idempotency_Key__c, Endpoint_Name__c, Payload__c,
                   Attempt_Count__c, Correlation_Id__c
            FROM Webhook_Delivery__c
            WHERE Status__c = 'Pending'
              AND Next_Attempt_At__c <= :DateTime.now()
            ORDER BY Next_Attempt_At__c ASC
            LIMIT :BATCH_SIZE
            FOR UPDATE
        ];

        if (due.isEmpty()) {
            return;
        }

        List<Webhook_Delivery__c> updates = new List<Webhook_Delivery__c>();
        for (Webhook_Delivery__c row : due) {
            updates.add(deliver(row));
        }

        // One DML for the whole batch, after all callouts. Doing DML between
        // callouts is legal but wasteful, and the ordering rule means a rollback
        // would leave rows describing deliveries that already happened.
        update updates;
    }

    private Webhook_Delivery__c deliver(Webhook_Delivery__c row) {

        Integer attempt = Integer.valueOf(row.Attempt_Count__c) + 1;
        row.Attempt_Count__c = attempt;

        try {
            String body      = row.Payload__c;
            String timestamp = String.valueOf(DateTime.now().getTime() / 1000);

            HttpClient.Response res = new HttpClient()
                .namedCredential(row.Endpoint_Name__c)
                .path('/v1/events')
                .method('POST')
                .header('Content-Type',    'application/json')
                .header('X-Event-Id',      row.Idempotency_Key__c)
                .header('X-Correlation-Id', row.Correlation_Id__c)
                .header('X-Timestamp',     timestamp)
                .header('X-Signature',     WebhookSigner.sign(timestamp, body))
                // Explicit, because the platform default is 10 seconds and the
                // batch arithmetic above depends on this number.
                .timeoutMs(CALLOUT_MS)
                // HttpClient's own retry is OFF here: retry belongs to the
                // outbox, which survives the transaction. An in-transaction
                // retry loop just burns the 120-second cumulative budget.
                .retryOnTransient(false)
                .body(body)
                .send();

            row.Last_Status_Code__c = res.statusCode;

            if (res.isSuccess()) {
                row.Status__c = 'Sent';
                row.Last_Error__c = null;
                return row;
            }

            // Transient (5xx / 408 / 429) retries; anything else is the
            // receiver telling you the request is wrong, and retrying a
            // rejection consumes the budget the transient failures need.
            if (res.isTransient() && attempt < MAX_ATTEMPTS) {
                row.Status__c          = 'Pending';
                row.Next_Attempt_At__c = nextAttempt(attempt, res);
                row.Last_Error__c      = clip(res.body, 2000);
            } else {
                row.Status__c     = res.isTransient() ? 'Dead' : 'Failed';
                row.Last_Error__c = clip(res.body, 2000);
                ApplicationLogger.error(
                    'WebhookDeliveryJob',
                    'Giving up on ' + row.Idempotency_Key__c +
                    ' after ' + attempt + ' attempts, last status ' + res.statusCode
                );
            }
            return row;

        } catch (CalloutException e) {
            // Timeouts and connection failures land here and are transient.
            row.Last_Error__c = clip(e.getMessage(), 2000);
            if (attempt < MAX_ATTEMPTS) {
                row.Status__c          = 'Pending';
                row.Next_Attempt_At__c = backoff(attempt);
            } else {
                row.Status__c = 'Dead';
            }
            return row;
        }
    }

    /**
     * Honour Retry-After when the receiver sends it. Their number is
     * authoritative: ignoring it while they are shedding load is how a client
     * gets blocked outright.
     */
    private DateTime nextAttempt(Integer attempt, HttpClient.Response res) {
        String retryAfter = res.headers.get('Retry-After');
        if (String.isNotBlank(retryAfter) && retryAfter.isNumeric()) {
            return DateTime.now().addSeconds(Integer.valueOf(retryAfter));
        }
        return backoff(attempt);
    }

    /** 30s, 2m, 8m, 32m, 2h, 8h, capped — with jitter so retries don't align. */
    private DateTime backoff(Integer attempt) {
        Integer capped  = Math.min(attempt, 6);
        Integer seconds = (Integer) (30 * Math.pow(4, capped - 1));
        Integer jitter  = Math.mod(Math.abs(Crypto.getRandomInteger()), Math.max(seconds / 4, 1));
        return DateTime.now().addSeconds(Math.min(seconds + jitter, 28800));
    }

    private static String clip(String s, Integer max) {
        return s != null && s.length() > max ? s.substring(0, max) : s;
    }
}
```

**Why it works:**

- No callout runs while DML is pending, so the platform rule is respected by
  construction rather than by care.
- The batch size and the per-callout timeout are chosen together against the
  120-second cumulative budget, and the relationship is written down where the
  next person will change one of them.
- Retry state is a row, so a failure at attempt 3 resumes at attempt 4 tomorrow
  rather than restarting or being lost.
- `FOR UPDATE` stops the scheduled sweeper and an event-driven enqueue from
  delivering the same row twice concurrently.

**What it deliberately does not do:** it does not guarantee ordering. Deliveries
retry independently, so a row that fails once arrives after rows created later.
That is why `buildPayload` emits absolute state with a version — the receiver can
apply it out of order safely. A design that genuinely needs ordering needs a
single-threaded chain and has to accept the throughput ceiling that comes with
one in-flight delivery at a time.

---

## Example 3: The finalizer and the sweeper

### The finalizer — for the failures that escape

```apex
/**
 * Runs after WebhookDeliveryJob whether it succeeded or threw.
 *
 * FinalizerContext.getResult() returns System.ParentJobResult: SUCCESS or
 * UNHANDLED_EXCEPTION. getException() returns the exception in the second case.
 *
 * Platform ceiling: "A Queueable job that failed due to an unhandled exception
 * can be successively re-enqueued five times by a transaction finalizer."
 * The counter resets on success — which is why the long backoff schedule lives
 * in the scheduled sweeper and not here.
 */
public class WebhookDeliveryFinalizer implements Finalizer {

    public void execute(FinalizerContext ctx) {

        if (ctx.getResult() == ParentJobResult.SUCCESS) {
            return;
        }

        // The batch died before its rows could be updated, so they are still
        // Pending with their old Next_Attempt_At__c and will be picked up by the
        // sweeper. Record why, with the async job id, so the failure is
        // attributable rather than mysterious.
        ApplicationLogger.error(
            'WebhookDeliveryFinalizer',
            'Delivery job ' + ctx.getAsyncApexJobId() +
            ' failed: ' + ctx.getException()?.getMessage()
        );

        // One re-enqueue. Anything beyond that is the sweeper's job — the
        // platform allows five successive finalizer re-enqueues, and burning
        // them in a tight loop just fails five times faster.
        System.enqueueJob(new WebhookDeliveryJob(), 5);   // 5-minute delay
    }
}
```

`System.enqueueJob(queueable, delay)` accepts a delay of 0–10 minutes. For finer
control, the `AsyncOptions` overload carries `MaximumQueueableStackDepth`, and
`System.AsyncInfo` exposes `getCurrentQueueableStackDepth()` and
`getMaximumQueueableStackDepth()` at runtime. Note the chaining constraint:
"you can add only one job from an executing job. Only one child job can exist for
each parent queueable job", and Developer Edition and Trial orgs cap the chained
stack depth at 5.

### The sweeper — the thing that makes it eventually consistent

```apex
/**
 * Schedule hourly. Everything overdue gets another attempt; nothing is lost
 * because a Queueable died, an org went into maintenance, or a partner had a
 * six-hour outage.
 */
public with sharing class WebhookSweeper implements Schedulable {

    public void execute(SchedulableContext ctx) {
        Integer overdue = [
            SELECT COUNT()
            FROM Webhook_Delivery__c
            WHERE Status__c = 'Pending'
              AND Next_Attempt_At__c <= :DateTime.now()
        ];

        if (overdue == 0) {
            return;
        }

        // Alert on DEPTH, not on individual failures. A single 503 is noise;
        // 500 overdue rows is a partner outage and somebody should know.
        if (overdue > 500) {
            ApplicationLogger.fatal(
                'WebhookSweeper',
                overdue + ' webhook deliveries overdue — check the receiver'
            );
        }

        System.enqueueJob(new WebhookDeliveryJob());
    }
}
```

**The alert that matters more than DLQ depth:** oldest-pending age. A backlog of
500 rows that is draining is fine; a backlog of 3 rows where the oldest is nine
hours old means something is stuck in a way the depth metric will never show you.

```apex
Webhook_Delivery__c oldest = [
    SELECT CreatedDate
    FROM Webhook_Delivery__c
    WHERE Status__c = 'Pending'
    ORDER BY CreatedDate ASC
    LIMIT 1
];
```

---

## Example 4: Signing — and the mistake that breaks it

**Wrong.** Serialize twice:

```apex
// The signature is computed over one string and the body sends another.
Blob mac = Crypto.generateMac(
    'hmacSHA256',
    Blob.valueOf(timestamp + '.' + JSON.serialize(payloadMap)),   // serialization #1
    secret);

req.setBody(JSON.serialize(payloadMap));                          // serialization #2
```

Two `JSON.serialize` calls on the same `Map<String, Object>` are not contractually
guaranteed to produce byte-identical output — key order in a `Map` is not part of
the API surface — and the receiver rejects everything with a signature mismatch
that looks exactly like a wrong secret. Teams then rotate the secret, which does
not help, and eventually disable the check.

**Right.** Serialize once, sign that string, send that string:

```apex
public with sharing class WebhookSigner {

    /**
     * HMAC-SHA256 over "{timestamp}.{body}" — the shape every mainstream
     * receiver library already implements. The timestamp is what lets the
     * receiver bound replay; without it, a captured request is valid forever.
     *
     * The secret lives in an External Credential, so rotation is a Setup change
     * rather than a deployment. Salesforce "manages all authentication for Apex
     * callouts that specify a named credential as the callout endpoint so that
     * your code doesn't have to" — and for a signing secret specifically, the
     * documented merge syntax lets the credential be referenced from the
     * request rather than read into Apex at all. Where the signature must be
     * computed in Apex, read it through a single accessor so there is exactly
     * one place it can leak from.
     */
    public static String sign(String timestamp, String body) {
        Blob mac = Crypto.generateMac(
            'hmacSHA256',
            Blob.valueOf(timestamp + '.' + body),
            Blob.valueOf(secret())
        );
        return 'sha256=' + EncodingUtil.convertToHex(mac);
    }

    private static String secret() {
        /* Resolved from the External Credential's named principal.
           Never a literal, never a Custom Setting, never logged. */
        return WebhookCredentials.signingSecret();
    }
}
```

Then, in the caller, the *same* `String` instance is both signed and sent:

```apex
String body = row.Payload__c;                       // serialized exactly once
String sig  = WebhookSigner.sign(timestamp, body);  // over those bytes
… .header('X-Signature', sig).body(body).send();    // and those bytes go out
```

**Note on `Crypto.generateMac` vs `verifyHMac`:** `generateMac` is correct here
because you are *producing* a signature. `verifyHMac` is the constant-time
comparison for *checking* one, and belongs on the receiving side — see
`integration/webhook-signature-verification`.

**Never log `body`, `sig`, or the secret.** The signature is not itself a secret,
but a captured body plus its signature is a replayable request, and your log
store is a much softer target than your org.

---

## Example 5: Testing the paths that actually fail

```apex
@IsTest
private class WebhookDeliveryJobTest {

    private static Webhook_Delivery__c pending(String key) {
        return new Webhook_Delivery__c(
            Idempotency_Key__c = key,
            Endpoint_Name__c   = 'Fulfilment_Partner',
            Status__c          = 'Pending',
            Attempt_Count__c   = 0,
            Next_Attempt_At__c = DateTime.now().addMinutes(-1),
            Payload__c         = '{"schemaVersion":"v1"}'
        );
    }

    @IsTest
    static void successMarksSent() {
        insert pending('evt-1');

        Test.setMock(HttpCalloutMock.class,
            new MockHttpResponseGenerator().withResponse(200, '{"ok":true}'));

        Test.startTest();
        System.enqueueJob(new WebhookDeliveryJob());
        Test.stopTest();

        Webhook_Delivery__c row = [
            SELECT Status__c, Attempt_Count__c, Last_Status_Code__c
            FROM Webhook_Delivery__c WHERE Idempotency_Key__c = 'evt-1'];

        Assert.areEqual('Sent', row.Status__c);
        Assert.areEqual(1, row.Attempt_Count__c);
        Assert.areEqual(200, row.Last_Status_Code__c);
    }

    @IsTest
    static void transientFailureSchedulesRetryAndDoesNotLoseTheEvent() {
        insert pending('evt-2');

        Test.setMock(HttpCalloutMock.class,
            new MockHttpResponseGenerator().withResponse(503, 'upstream down'));

        Test.startTest();
        System.enqueueJob(new WebhookDeliveryJob());
        Test.stopTest();

        Webhook_Delivery__c row = [
            SELECT Status__c, Attempt_Count__c, Next_Attempt_At__c
            FROM Webhook_Delivery__c WHERE Idempotency_Key__c = 'evt-2'];

        Assert.areEqual('Pending', row.Status__c,
            'A 5xx must stay retryable, not be marked Failed');
        Assert.areEqual(1, row.Attempt_Count__c);
        Assert.isTrue(row.Next_Attempt_At__c > DateTime.now(),
            'Backoff must push the next attempt into the future');
    }

    @IsTest
    static void permanentFailureDoesNotRetryForever() {
        insert pending('evt-3');

        // 422 is the receiver saying the payload is wrong. Retrying it burns
        // the budget the transient failures need and never succeeds.
        Test.setMock(HttpCalloutMock.class,
            new MockHttpResponseGenerator().withResponse(422, '{"error":"bad schema"}'));

        Test.startTest();
        System.enqueueJob(new WebhookDeliveryJob());
        Test.stopTest();

        Assert.areEqual('Failed', [
            SELECT Status__c FROM Webhook_Delivery__c
            WHERE Idempotency_Key__c = 'evt-3'].Status__c);
    }

    @IsTest
    static void duplicateEventConvergesOnOneRow() {
        // The same logical event queued twice — a recursive trigger, a retried
        // save, a mass update touching the record twice.
        Database.upsert(new List<Webhook_Delivery__c>{
            pending('evt-4'), pending('evt-4')
        }, Webhook_Delivery__c.Idempotency_Key__c, false);

        Assert.areEqual(1, [
            SELECT COUNT() FROM Webhook_Delivery__c
            WHERE Idempotency_Key__c = 'evt-4'],
            'External Id + Unique must collapse duplicates at the database');
    }

    @IsTest
    static void bulkChangeEnqueuesOneJobNotTwoHundred() {
        List<Order> orders = TestDataFactory.orders(200);
        insert orders;

        Test.setMock(HttpCalloutMock.class,
            new MockHttpResponseGenerator().withResponse(200, '{}'));

        Test.startTest();
        for (Order o : orders) { o.Status = 'Activated'; }
        update orders;
        // One job for 200 records. Assert it, because "one Queueable per record"
        // passes every single-record test and dies on the first data load.
        Assert.areEqual(1, Limits.getQueueableJobs(),
            'A bulk update must enqueue one delivery job, not one per record');
        Test.stopTest();
    }
}
```

**Why these five:** they are the cases a naive implementation gets wrong. A
happy-path test passes against code with no retry, no idempotency, no
transient/permanent distinction, and no bulkification — which is to say, against
code that will lose events in its first week.

Mock helper: [`templates/apex/tests/MockHttpResponseGenerator.cls`](../../../../templates/apex/tests/MockHttpResponseGenerator.cls),
which also supports `pushSequence(...)` for modelling a 503-then-200 recovery
across two job runs.

---

## Anti-Pattern: the callout in the trigger

**What gets written, roughly weekly, in every org:**

```apex
trigger OrderTrigger on Order (after update) {
    for (Order o : Trigger.new) {
        if (o.Status != Trigger.oldMap.get(o.Id).Status) {
            HttpRequest req = new HttpRequest();
            req.setEndpoint('callout:Fulfilment_Partner/v1/events');
            req.setMethod('POST');
            req.setBody(JSON.serialize(o));
            new Http().send(req);          // throws, every time
        }
    }
}
```

**What goes wrong, in order:**

1. `System.CalloutException: You have uncommitted work pending. Please commit or
   rollback before calling out` — the trigger's own DML is pending. The user's
   save fails.
2. Even without that, the callout is inside a `for` loop over `Trigger.new`, so a
   201-row update would exceed the 100-callouts-per-transaction limit.
3. Even bulkified, 201 callouts at the 10-second default cannot fit in the
   120-second cumulative budget.
4. `JSON.serialize(o)` ships the entire sObject — every field the query happened
   to load, including any PII on the Order — to a third party.

**The usual "fix" makes it worse:** moving the callout to `@future(callout=true)`
clears the exception and quietly discards the reliability requirement. A `@future`
method that fails leaves no state, no retry, and no record that the event ever
existed. The event is simply gone, and nobody finds out until the partner asks
why an order never arrived.

**Correct approach:** write a `Webhook_Delivery__c` row in the trigger — DML is
legal there — and enqueue one Queueable for the batch. The event is durable
before it is delivered, which is the entire point.

**Detection hint:** `new Http().send(` or `Http.send(` anywhere in a trigger,
a trigger handler, or an `after` context; `@future(callout=true)` used as a
delivery mechanism rather than as a genuine fire-and-forget; and
`JSON.serialize(someSObject)` as an outbound payload.
