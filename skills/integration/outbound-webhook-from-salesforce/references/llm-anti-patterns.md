# LLM Anti-Patterns — Outbound Webhook From Salesforce

Mistakes AI assistants make when asked to make Salesforce POST to an external
endpoint. The recurring cause: "send an HTTP request when a record changes" is a
five-line problem in most stacks and a twelve-artifact problem on this platform,
and the extra artifacts exist for reasons that are not visible in the request.

---

## Anti-Pattern 1: The callout inside the trigger

**What the LLM generates:**

```apex
trigger OrderTrigger on Order (after update) {
    for (Order o : Trigger.new) {
        if (o.Status != Trigger.oldMap.get(o.Id).Status) {
            HttpRequest req = new HttpRequest();
            req.setEndpoint('https://partner.example.com/webhook');
            req.setMethod('POST');
            req.setBody(JSON.serialize(o));
            new Http().send(req);
        }
    }
}
```

**Why it happens:** "when the record changes, POST to the endpoint" maps directly
onto "in the after-update trigger, send an HTTP request". Every clause of the
requirement is satisfied. The platform rule that forbids it is invisible in the
code and is not derivable from general HTTP knowledge.

**Correct pattern:** the Apex Developer Guide: *"You can't make a callout when
there are pending operations in the same transaction. Things that result in
pending operations are DML statements…"* A trigger has pending DML by
construction, so the runtime throws `You have uncommitted work pending` and rolls
back the user's save. Write a delivery row (DML is legal), enqueue one Queueable
for the batch, and call out from there.

Three further defects in the same six lines, each independently fatal: the
callout is inside a loop over `Trigger.new` (100-callout limit, and unreachable
anyway inside the 120-second cumulative budget), the endpoint is a hardcoded
hostname rather than `callout:<NamedCredential>`, and `JSON.serialize(o)` ships
every loaded field on the sObject — including PII — to a third party.

**Detection hint:** `new Http().send(` or `Http.send(` anywhere in a trigger,
trigger handler, or `after` context.

---

## Anti-Pattern 2: `@future(callout=true)` as the reliability answer

**What the LLM generates:**

```apex
@future(callout=true)
public static void sendWebhook(Id orderId, String payload) {
    HttpRequest req = new HttpRequest();
    req.setEndpoint('callout:Partner/v1/events');
    req.setMethod('POST');
    req.setBody(payload);
    new Http().send(req);
}
```

**Why it happens:** it is the smallest change that makes the `uncommitted work
pending` exception go away, and `@future(callout=true)` is *named* for exactly
this. The exception disappearing feels like the problem being solved.

**Correct pattern:** `@future` moves the callout to a legal context and silently
deletes the reliability requirement. A `@future` that fails leaves no state, no
retry, and no record that the event existed — the event is simply gone, and
nobody learns about it until the partner asks. It also takes primitives only, so
the payload has to be serialized into the parameter anyway.

Use a Queueable implementing `Database.AllowsCallouts`, backed by a durable
delivery row written in the triggering transaction. If loss genuinely is
acceptable, say so explicitly in the design rather than arriving at it by
accident.

**Detection hint:** `@future(callout=true)` presented as the fix for a callout
ordering error, with no persisted delivery state anywhere in the answer.

---

## Anti-Pattern 3: Retry as a loop with a sleep

**What the LLM generates:**

```apex
for (Integer attempt = 0; attempt < 5; attempt++) {
    HttpResponse res = new Http().send(req);
    if (res.getStatusCode() < 300) { return; }
    Long until = System.currentTimeMillis() + (1000 * (Long) Math.pow(2, attempt));
    while (System.currentTimeMillis() < until) { /* wait */ }
}
```

**Why it happens:** exponential backoff in a loop is the textbook retry, and it is
correct in a language with a real `sleep` and no transaction budget.

**Correct pattern:** the busy-wait burns CPU against the 10,000 ms synchronous /
60,000 ms asynchronous limit and the callouts burn the 120-second cumulative
timeout, so the whole loop dies inside one transaction and takes the delivery with
it. Backoff has to be *scheduled*, not slept: persist `Next_Attempt_At__c`, return,
and let a scheduled sweeper pick the row up. A retry schedule measured in hours
cannot live inside a transaction measured in seconds.

**Detection hint:** any busy-wait loop, `System.currentTimeMillis()` used as a
timer, or a `for` loop containing both a callout and a backoff calculation.

---

## Anti-Pattern 4: Idempotency assumed rather than negotiated

**What the LLM generates:** a complete retry design with backoff and
dead-lettering, and a payload with no idempotency key — or one with a key that
the answer never mentions the receiver needing to honour.

**Why it happens:** retry is the part of the requirement that was stated.
Duplicate suppression on the receiver's side is somebody else's system, outside
the boundary of the code being written.

**Correct pattern:** at-least-once delivery means duplicates are certain, not
possible. A key you send that the receiver ignores is decoration. The design
step is a written confirmation of what happens when they receive the same event
twice, and it has to happen before the code, because "please deduplicate on
`X-Event-Id`" is a contract change with their release cycle attached.

On your side the key belongs on an External Id, Unique field so that duplicate
*queuing* is a database constraint rather than a race.

**Detection hint:** a retry design with no idempotency key, or a key with no
statement about receiver-side behaviour.

---

## Anti-Pattern 5: The secret in Custom Metadata

**What the LLM generates:**

```apex
String secret = Webhook_Config__mdt.getInstance('Partner').Signing_Secret__c;
Blob mac = Crypto.generateMac('hmacSHA256', Blob.valueOf(body), Blob.valueOf(secret));
```

**Why it happens:** protected Custom Metadata genuinely is the right home for
*inbound* webhook secrets, where the org must read the value to verify a
signature — and the two situations look identical from the code's side.

**Correct pattern:** for outbound, the secret belongs in a Named Credential's
**External Credential**, because that is what makes rotation a Setup change
instead of a deployment, and because Salesforce then "manages all authentication
for Apex callouts that specify a named credential as the callout endpoint so that
your code doesn't have to". Reference it with the documented merge syntax
(`{!$Credential.Password}`,
`{!$Credential.<AuthProviderName>.<ParameterName>}`) rather than reading the value
into an Apex variable, so there is no local copy to leak.

**Detection hint:** a signing secret read from `__mdt`, a Custom Setting, or a
literal, in code whose direction is outbound.

---

## Anti-Pattern 6: Serializing the payload twice

**What the LLM generates:**

```apex
Blob mac = Crypto.generateMac('hmacSHA256',
    Blob.valueOf(ts + '.' + JSON.serialize(payload)), secret);
req.setBody(JSON.serialize(payload));
```

**Why it happens:** the two lines are written for two different purposes and each
is individually correct. That the *bytes* must be identical, and that two
serializations of a `Map` may not be, is a property of HMAC rather than of the
code.

**Correct pattern:** serialize once into a `String`, sign that string, send that
string. When the payload is already persisted on an outbox row, sign and send the
stored field — the persisted value is then the single definition of what those
bytes are.

**Detection hint:** two `JSON.serialize` calls on the same object in one method,
where one feeds a signature and the other feeds the body.

---

## Anti-Pattern 7: One Queueable per record

**What the LLM generates:**

```apex
for (Order o : changedOrders) {
    System.enqueueJob(new WebhookDeliveryJob(o.Id));
}
```

**Why it happens:** one job per event is a clean mental model and reads as
correct parallelism. Bulkification is a Salesforce-specific discipline that
applies to a loop the model has no reason to see as a loop over a *governed*
resource.

**Correct pattern:** `System.enqueueJob` is capped at 50 per synchronous
transaction and 1 per asynchronous one, so a Data Loader batch of 200 fails at
the 51st call and rolls back the whole load. Enqueue one job for the batch and let
it query its own work from the outbox.

Prove it with the assertion most webhook producers do not have:

```apex
Assert.areEqual(1, Limits.getQueueableJobs(),
    'A bulk update must enqueue one delivery job, not one per record');
```

**Detection hint:** `System.enqueueJob` inside a `for` loop, or a Queueable whose
constructor takes a single record id.

---

## Anti-Pattern 8: Retrying every non-2xx

**What the LLM generates:**

```apex
if (res.getStatusCode() != 200) {
    scheduleRetry(row);
}
```

**Why it happens:** "not success, so try again" is the intuitive rule, and it is
right for the failures people picture — timeouts and outages.

**Correct pattern:** a 400 or 422 is the receiver telling you the *request* is
wrong. Retrying it will fail identically every time, consumes the retry budget
that transient failures need, and pushes a permanently broken row through a
backoff schedule for eight hours before dead-lettering it. Retry 5xx, 408, and
429; dead-letter other 4xx immediately with the response body recorded so the bug
is diagnosable.

And honour `Retry-After` where the receiver sends it — their number overrides
your schedule, and ignoring it while they are shedding load is how a client gets
blocked outright.

**Detection hint:** a retry predicate written as `statusCode != 200` or
`!isSuccess()`, with no distinction between transient and permanent.

---

## Anti-Pattern 9: Delta payloads

**What the LLM generates:**

```json
{"orderId":"801...","statusChange":{"from":"Draft","to":"Activated"}}
```

**Why it happens:** the trigger has `Trigger.old` and `Trigger.new` right there,
the requirement said "notify on change", and a from/to pair is the most faithful
description of what happened.

**Correct pattern:** every retrying design reorders — Salesforce documents the
same property of its own Outbound Messaging: "Messages are retried independent of
their order in the queue. As a result, messages can be delivered out of order." A
transition payload applied out of order corrupts the receiver's state, and applied
twice may double-count.

Send absolute state with a monotonic version instead, so the receiver can discard
anything older than what it holds:

```json
{"resource":{"id":"801...","status":"Activated","version":1723645200000}}
```

Include the prior value as *context* if the receiver wants it, but never as the
thing they apply.

**Detection hint:** `from`/`to`, `previous`, `delta`, or `change` as the
load-bearing part of an outbound payload.

---

## Anti-Pattern 10: `JSON.serialize(record)` as the payload

**What the LLM generates:**

```apex
req.setBody(JSON.serialize(order));
```

**Why it happens:** it is one line, it produces valid JSON, and the record is
exactly the thing the event is about.

**Correct pattern:** it emits every field the query happened to load, which grows
silently as other code adds fields to the shared selector, and it exports the
org's internal field API names as a public contract. The first added
`Customer_SSN__c` is exfiltrated with no code change and no review. Build an
explicit `Map<String, Object>` — the fields you chose, a `schemaVersion`, an
`occurredAt`, and a correlation id — so the payload is a decision rather than an
accident.

**Detection hint:** `JSON.serialize` applied directly to an sObject or a
`List<sObject>` in an outbound path.

---

## Anti-Pattern 11: Treating Event Relay as a webhook option

**What the LLM generates:** a comparison table listing Event Relay alongside
Apex callouts and Flow HTTP Callout as interchangeable ways to POST to an
endpoint, sometimes recommended for "scalability".

**Why it happens:** it appears in the same family of documentation, it moves
events out of Salesforce, and the name suggests a general-purpose relay.

**Correct pattern:** `EventRelayConfig` requires `destinationResourceName` — "the
developer name of the named credential, which stores the AWS account
information" — and relays platform events and change data capture events to
Amazon EventBridge. It is not a way to call a partner's HTTPS endpoint. Where the
destination genuinely is an AWS estate it is excellent and removes your whole
delivery layer; presented as a webhook mechanism it sends someone down a
multi-day path to a dead end.

**Detection hint:** Event Relay recommended for a requirement whose destination is
an HTTPS URL rather than an AWS account.

---

## Anti-Pattern 12: A happy-path test presented as coverage

**What the LLM generates:**

```apex
@IsTest
static void testWebhook() {
    Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator(200, '{"ok":true}'));
    Test.startTest();
    WebhookService.send(order);
    Test.stopTest();
    Assert.areEqual('Sent', [SELECT Status__c FROM Webhook_Delivery__c].Status__c);
}
```

**Why it happens:** it is a correct test of the stated behaviour, it passes, and
it produces coverage. The cases that matter were not in the request.

**Correct pattern:** this test passes against an implementation with no retry, no
idempotency, no transient/permanent distinction, and no bulkification — which is
to say against an implementation that will lose events in its first week. The
suite has to include: a 5xx that stays `Pending` with a future
`Next_Attempt_At__c`; a 4xx that dead-letters immediately; a duplicate event that
converges on one row via the External Id; a 429 whose `Retry-After` is honoured;
and a 200-record bulk update that enqueues exactly one job.

**Detection hint:** a webhook test suite whose assertions are all on the success
path, or one with fewer tests than the design has failure modes.
