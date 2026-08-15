# Gotchas — Outbound Webhook From Salesforce

Failure modes specific to *producing* webhooks from Salesforce. Grounded in the
Apex Developer Guide, the Apex Reference Guide, the SOAP API Developer Guide, and
the Metadata API Developer Guide (Summer '26, API 67.0).

---

## Gotcha 1: You Cannot Call Out After DML in the Same Transaction

**What happens:** `System.CalloutException: You have uncommitted work pending.
Please commit or rollback before calling out.` The user's save fails, and the
error surfaces to them as a page error on a record edit.

The Apex Developer Guide states the rule directly:

> "You can't make a callout when there are pending operations in the same
> transaction. Things that result in pending operations are DML statements,
> asynchronous Apex (such as future methods and batch Apex jobs), scheduled Apex,
> or sending email."

A record-change trigger *is* pending DML by definition, so there is no ordering
trick that makes a callout legal there.

**When it occurs:** on the first real save after a webhook is added to a trigger,
which is often in production because a single-record sandbox test with no other
automation can occasionally slip through.

**How to avoid:** persist the *intent to deliver* in the triggering transaction —
DML is legal there — and deliver from a Queueable implementing
`Database.AllowsCallouts`.

**The fix that looks right and is not:** switching to `@future(callout=true)`
makes the exception disappear. It also discards the reliability requirement — a
`@future` that fails leaves no state, no retry, and no evidence the event ever
existed. If you are going to lose events, at least lose them deliberately.

---

## Gotcha 2: The 120-Second Cumulative Budget, Not the 100-Callout Limit

**What happens:** a Queueable that delivered 30 webhooks fine yesterday starts
timing out when the partner slows down. The callout count is nowhere near 100.

Two separate ceilings apply per transaction, and the second is the one that
usually bites first:

| Limit | Value |
|---|---|
| Total callouts in a transaction | 100 |
| Maximum cumulative timeout for all callouts in a transaction | 120 seconds |
| Default timeout per callout | 10 seconds |
| Configurable timeout per callout | 1 ms – 120,000 ms |

Twelve callouts at the default 10-second timeout exhaust the 120-second budget.
The callout limit of 100 is unreachable at default timeouts.

**When it occurs:** the day the receiver degrades. Your batch size was chosen when
every response came back in 200 ms.

**How to avoid:** choose batch size and per-callout timeout *together*, and write
the arithmetic down next to both:

```apex
private static final Integer BATCH_SIZE = 10;
private static final Integer CALLOUT_MS = 8000;   // 10 × 8s = 80s < 120s
```

Never leave the timeout at the default in a batching job — the default is the
number that makes the budget unpredictable.

---

## Gotcha 3: `Database.AllowsCallouts` Is a Marker You Have to Remember

**What happens:** a `CalloutException` at runtime from a Queueable that looks
correct. There is no compile error, because the interface adds no methods.

> "Apex allows HTTP and web service callouts from queueable jobs, if they
> implement the `Database.AllowsCallouts` marker interface. In queueable jobs
> that implement this interface, callouts are also allowed in chained queueable
> jobs."

**When it occurs:** when a Queueable is refactored, split, or copied — the
interface is on the class declaration, which is exactly the line people rewrite.

**How to avoid:** `implements Queueable, Database.AllowsCallouts` as a single unit
in every job that could ever call out, and a test that actually performs a mocked
callout. A test that only asserts the job ran will not catch this.

---

## Gotcha 4: One Finalizer, Five Re-Enqueues

**What happens:** a retry design built entirely on transaction finalizers stops
retrying after five attempts and nobody can find the code that stopped it.

The Apex Developer Guide is precise on both counts:

> "Only one finalizer instance can be attached to any Queueable job."

> "A Queueable job that failed due to an unhandled exception can be successively
> re-enqueued five times by a transaction finalizer."

The second limit "applies to consecutive failures; the counter resets upon
successful completion" — so a job that intermittently succeeds never hits it, and
a genuinely broken receiver hits it in minutes.

**When it occurs:** during the first real outage, which is when the retry design
is being relied on rather than tested.

**How to avoid:** use the finalizer for what it is good at — reacting to an
*unhandled exception* that killed the job before its rows could be updated — and
put the long backoff schedule in a scheduled sweeper reading a
`Next_Attempt_At__c` field. The sweeper has no such cap and survives an org
restart, a maintenance window, and a six-hour partner outage.

Related chaining constraints worth knowing: "you can add only one job from an
executing job. Only one child job can exist for each parent queueable job", and
"For Developer Edition and Trial organizations, the maximum stack depth for
chained jobs is 5, which means that you can chain jobs four times."

---

## Gotcha 5: Serializing Twice Produces a Signature the Receiver Rejects

**What happens:** every signed request is rejected. The secret is rotated. It does
not help. Eventually the signature check gets disabled "temporarily".

```apex
// The signature covers one string; the body is a different one.
Blob mac = Crypto.generateMac('hmacSHA256',
    Blob.valueOf(ts + '.' + JSON.serialize(payloadMap)), secret);
req.setBody(JSON.serialize(payloadMap));
```

HMAC is over bytes. Two `JSON.serialize` calls on the same `Map<String, Object>`
are not contractually guaranteed to emit identical output — key ordering in a
`Map` is not part of the documented API surface — and any difference at all
produces a completely different digest.

**When it occurs:** immediately, on every request, which at least makes it
obvious that *something* is wrong. What is not obvious is that the problem is
serialization rather than the key.

**How to avoid:** serialize once into a `String`, sign that string, send that
string. Where the payload is already persisted (an outbox row), sign the stored
value and send the stored value — the persisted field is the single source of
truth for what those bytes are.

---

## Gotcha 6: Platform Event Publish Behaviour Changes Which Limit You Consume

**What happens:** a subscriber-based design starts failing with a DML limit error
in a transaction that issues almost no DML — or, in the other configuration,
succeeds under DML pressure but fails a limit nobody was watching.

The two publish behaviours consume different allocations:

- **Publish After Commit** — "Each method execution is counted as one DML
  statement against the Apex DML statement limit."
- **Publish Immediately** — "Each method execution is counted against a separate
  event publishing limit of 150 `EventBus.publish()` calls."

Use `Limits.getDMLStatements()` for the first and `Limits.getPublishImmediateDML()`
for the second.

**When it occurs:** when the publish behaviour is changed on the event definition
without anyone re-reading the code that publishes it. It is a metadata change
with a code-level consequence.

**How to avoid:** record the publish behaviour next to the publishing code, and
handle `Database.SaveResult` properly either way — "`EventBus.publish()` can
publish some passed-in events, even when other events can't be published due to
errors", so a bare `EventBus.publish(events)` with no result inspection silently
drops the ones that failed.

---

## Gotcha 7: Every Retrying Design Reorders

**What happens:** the receiver's state ends up wrong in a way that looks like data
corruption. Order 123 shows `Shipped` when it should show `Delivered`, because the
`Shipped` event failed once, retried, and landed after `Delivered`.

This is not a Salesforce quirk; it is what retry means. Salesforce's own Outbound
Messaging documents the same property: "Messages are retried independent of their
order in the queue. As a result, messages can be delivered out of order."

**When it occurs:** the first time a delivery fails and succeeds on retry — which
is to say, in the first week, on exactly the events that mattered enough to fail.

**How to avoid:** make out-of-order delivery harmless by sending absolute state
with a monotonic version, so the receiver can discard anything older than what it
already has:

```json
{"resource":{"id":"801...","status":"Shipped","version":1723645200000}}
```

A delta payload (`{"statusDelta":"+1"}`) has no defence against this at all. If
strict ordering is genuinely required, it costs a single-threaded chain with one
delivery in flight at a time, and that throughput ceiling should be agreed before
it is discovered.

---

## Gotcha 8: HTTP 200 Does Not Mean "Processed"

**What happens:** the outbox is entirely green and the partner insists they never
received a batch of events. Both are telling the truth.

A 2xx means the receiver accepted the bytes. Many receivers queue internally and
return 200 before doing anything, which is the correct design on their side — and
it means your success metric measures their *ingestion*, not their processing.

**When it occurs:** during any incident on the receiver's side of their own
queue. Your dashboard shows nothing because, from your position, nothing went
wrong.

**How to avoid:** write down what their 2xx promises, as part of the receiver
contract, before you build. Where the events matter, ask for a reconciliation
endpoint (a count or a checksum for a time window) and compare periodically. This
is unglamorous and it is the only thing that detects the failure.

---

## Gotcha 9: Outbound Messages Drop Silently at 24 Hours

**What happens:** a partner outage lasts a weekend. On Monday everything is
working and roughly a day of notifications simply do not exist anywhere.

The SOAP API Developer Guide:

> "If the endpoint is unavailable, messages stay in the queue until sent
> successfully, or until they're 24 hours old. After 24 hours, messages are
> dropped from the queue."

> "If a message can't be delivered, the interval between retries increases
> exponentially, up to a maximum of two hours between retries."

Also: "A single SOAP message can include up to 100 notifications."

**When it occurs:** during any outage longer than a day, and there is no
after-the-fact recovery — the queue is a platform-managed structure you cannot
query or replay.

**How to avoid:** for existing outbound messages, know that this is the exposure
and monitor the receiver's availability rather than the queue you cannot see. For
anything new, do not build on it: the host feature, Workflow Rules, reached end of
support on 31 December 2025. An outbox row you control has no 24-hour cliff and
can be replayed a month later.

---

## Gotcha 10: Flow HTTP Callout Has No Retry, and Adding One Means Leaving Flow

**What happens:** a low-code integration is built, works, and then silently loses
events during a partner's five-minute deploy window. There is no retry, no error
record, and no way to know which events were lost.

Flow's HTTP Callout action generates an External Service registration and an
invocable action from the API's shape, and requires an External Credential and a
Named Credential. What it does not give you is retry, backoff, dead-lettering, or
a durable record of the attempt — and none of those is expressible declaratively.

**When it occurs:** at the first receiver blip after go-live.

**How to avoid:** treat Flow HTTP Callout as correct for exactly one profile — low
volume, admin-owned, receiver tolerant of loss — and say out loud that loss is
tolerated. The moment a signature or a retry is required, the design has moved to
Apex, and pretending otherwise produces a Flow with a fault path that writes an
error record nobody sweeps.

<!-- UNVERIFIED: Salesforce Help's "Connecting to an API Without a Connector
     Using HTTP Callout" page also documents constraints on supported response
     formats and HTTP methods (JSON-only responses; method support has changed
     across releases). That page is Aura-rendered and could not be fetched, so no
     specific claim about the current method or format support is made here.
     Check it in Flow Builder against your target org before designing around a
     particular verb. -->

---

## Gotcha 11: One Queueable Per Record Does Not Survive a Mass Update

**What happens:** a data load of 10,000 rows enqueues 10,000 jobs. The org's async
queue backs up, unrelated batch jobs are delayed, and someone's nightly
integration misses its window.

The per-transaction ceiling on `System.enqueueJob` is 50 in a synchronous context
and 1 in an asynchronous one — so the naive per-record loop does not even reach
10,000; it fails at 50 and rolls back the load.

**When it occurs:** never in the sandbox, where the trigger is tested by editing
one record.

**How to avoid:** one job per *batch*, and a `Limits.getQueueableJobs()` assertion
in a bulk test:

```apex
Assert.areEqual(1, Limits.getQueueableJobs(),
    'A bulk update must enqueue one delivery job, not one per record');
```

That single assertion catches the entire class of defect, and it is the test most
webhook producers do not have.

---

## Gotcha 12: Event Relay Is Not a Webhook

**What happens:** "Event Relay" is chosen for a requirement to POST to a partner's
HTTPS endpoint, and the design has to be abandoned after the AWS account question
comes up.

`EventRelayConfig` (API 56.0 and later, suffix `.eventRelay`, directory
`eventRelays`) requires `destinationResourceName` — "the developer name of the
named credential, which stores the AWS account information" — and an
`eventChannel`. It relays platform events and change data capture events to
Amazon EventBridge.

**When it occurs:** when a mechanism table is read as a menu of interchangeable
options rather than as different shapes.

**How to avoid:** treat Event Relay as correct when the destination is an AWS
estate and wrong when it is a single HTTPS endpoint. Where it does fit, it is
genuinely excellent — it removes your entire delivery, retry, and observability
layer and replaces it with AWS's. Its `relayOption` even carries a replay
recovery mode, documented as "a JSON-encoded string that contains an option for
resuming an event relay after the system recovers from an error", with `LATEST`
(default) or `EARLIEST` resending stored events up to three days old. Its `state`
enumeration is `RUN`, `PAUSE`, `STOP`, or `DELETE`.

---

## Gotcha 13: The Outbox Is a Second Copy of Your Data

**What happens:** a compliance review discovers that a custom object contains
eighteen months of order payloads including customer names and addresses, with its
own sharing model, its own report exposure, and no retention policy.

The `Payload__c` field that makes replay trivial is also a durable copy of
whatever you send.

**When it occurs:** at the first data-protection review after go-live, or at a
subject-access request, whichever comes first.

**How to avoid:** decide this at design time rather than at review time. Restrict
the object to the integration's permission set. Set an explicit deletion policy
for `Sent` rows — a scheduled purge after N days is four lines. Where the payload
is genuinely sensitive, use notification-plus-pull instead: send an identifier and
let the receiver fetch the body over an authenticated API, so the outbox holds a
reference rather than the data.
