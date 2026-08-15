# Well-Architected Notes — Outbound Webhook From Salesforce

## Relevant Pillars

- **Reliability** — Primary pillar. The platform gives you a callout and nothing
  else: no delivery queue you can inspect, no retry you did not write, no record
  that an attempt happened. Every reliability property in this design is one you
  built. The load-bearing decision is that the *intent to deliver* is persisted
  in the same transaction as the record change — so the change and the obligation
  commit or roll back together — while the delivery itself is asynchronous and
  resumable. Once that row exists, retry, backoff, dead-lettering, replay, and
  observability are all queries against it. Without it, they have nowhere to live.

- **Security** — Two surfaces, and only one of them is obvious. The outbound
  surface is the endpoint and the credential: `callout:<NamedCredential>` rather
  than a hostname, the signing secret in an External Credential so rotation is a
  Setup change, and nothing logged. The less obvious surface is the payload
  itself — `JSON.serialize(record)` exports every field the query happened to
  load, and the next `Customer_SSN__c` someone adds to a shared selector leaves
  the org with no code change and no review. An explicit field list is an access
  control, not a style preference. Third: the outbox is a durable second copy of
  whatever you sent, with its own sharing model and its own retention obligation.

- **Operational Excellence** — The question "is the integration working?" must be
  answerable without reading a log. A dashboard of outbox `Status__c` by hour
  answers it; a debug log does not. Two alerts do most of the work and they are
  not the same alert: **DLQ depth** catches a receiver that is rejecting, and
  **oldest-pending age** catches a queue that has stopped draining — a backlog of
  three rows where the oldest is nine hours old is a worse signal than five
  hundred rows that are moving, and depth alone never shows it. Replay must be a
  documented procedure, not an improvisation performed during an incident.

- **Performance** — Bounded by two per-transaction ceilings that have to be
  designed against together: 100 callouts and, more restrictively, 120 seconds of
  cumulative callout timeout. At the 10-second default, twelve callouts exhaust
  the budget, so batch size and per-callout timeout are a single decision. The
  burst case matters more than the average: a mass update that produces 50,000
  events in ninety seconds is the load the design has to survive, and a per-record
  Queueable does not survive it at all.

## Architectural Trade-offs

**Outbox plus Queueable vs a direct async callout.** The outbox costs an object,
a retention policy, a sweeper, and a second place to look during an incident. It
buys durability across org restarts and maintenance windows, resumable retry
across hours rather than seconds, replay of a specific delivery, and an
observability surface that is a SOQL query. A `@future(callout=true)` costs
nothing and offers none of it — a failure there leaves no state and no evidence.
The outbox is the right default for anything with a consequence; the direct
callout is defensible only where event loss is explicitly acceptable and someone
has said so in writing.

**Finalizer retry vs scheduled sweeper.** A `Finalizer` reacts to the failure
immediately and is the only reliable hook for an unhandled exception that killed
the job before it could update its own rows. It is capped: "A Queueable job that
failed due to an unhandled exception can be successively re-enqueued five times by
a transaction finalizer", and only one finalizer may be attached per job. A
scheduled sweeper reading `Next_Attempt_At__c` has no cap, survives anything, and
supports a schedule measured in hours — at the cost of latency equal to its
schedule interval. Use both: the finalizer for the immediate retry, the sweeper
for the long tail. Building the whole schedule on finalizers hits the ceiling
during the first real outage.

**Apex vs Flow HTTP Callout.** Flow puts the integration in the hands of the
people who own the process, needs no deployment to change, and generates its
External Service registration from the API's own shape. It has no retry, no
backoff, no dead-lettering, and no practical way to sign a payload — and none of
those is expressible declaratively, so adding any one of them means leaving Flow
entirely. The honest boundary: Flow when volume is low, the receiver is tolerant,
and event loss is acceptable *and stated*; Apex the moment a signature or a retry
is required.

**Platform Event fan-out vs a direct producer.** Publishing an event decouples the
producer from every consumer and makes adding a second receiver a subscriber
change rather than a producer change. It costs an extra hop, a second failure
domain, and attention to which publish behaviour you chose — Publish After Commit
counts against the DML statement limit, Publish Immediately against a separate
allocation of 150 `EventBus.publish()` calls. For exactly one receiver it is
overhead; for the third receiver it is what you wish you had built first.

**Event Relay vs building the delivery layer.** Where the destination is an AWS
estate, `EventRelayConfig` removes your delivery, retry, and observability code
entirely and replaces it with EventBridge's — including a replay recovery option
that can resend stored events up to three days old. It is not a general webhook
mechanism: it requires a Named Credential holding AWS account information and
relays platform events and change data capture events to Amazon EventBridge. The
trade is a large reduction in owned code for a hard coupling to one cloud.

**Absolute state vs delta payloads.** A delta is a faithful description of what
happened and is unsafe under any retrying design, because retry reorders —
Salesforce documents this of its own Outbound Messaging: "Messages are retried
independent of their order in the queue. As a result, messages can be delivered
out of order." Absolute state with a monotonic version is idempotent and
order-insensitive at the receiver, at the cost of a larger payload and of the
receiver losing the ability to see transitions unless you include the prior value
as context. Absolute state wins on every axis that matters in production.

**Payload retention vs replay capability.** Storing the payload on the outbox row
makes replay after a bug trivial and often turns an incident into a re-run. It
also means customer data now lives in a Salesforce object with its own sharing
model, its own report exposure, and its own retention obligation. If you retain,
restrict the object and set an explicit deletion policy for `Sent` rows. If you
do not, accept that a processing bug is unrecoverable without regenerating the
events from source.

## Anti-Patterns

1. **A callout in the transaction that caused the change.** The platform forbids
   it — "You can't make a callout when there are pending operations in the same
   transaction" — and the workaround people reach for (`@future(callout=true)`)
   removes the exception and the reliability requirement together.

2. **Retry as a loop with a busy-wait.** Burns the CPU limit and the 120-second
   cumulative callout budget, and dies inside the transaction it was meant to
   outlive. Backoff must be scheduled, not slept.

3. **Assuming idempotency instead of negotiating it.** At-least-once means
   duplicates are certain. A key the receiver ignores is decoration, and finding
   that out after go-live is a contract change with their release cycle attached.

4. **Retrying every non-2xx.** A 422 will fail identically forever while
   consuming the budget the transient failures need. Retry 5xx, 408, and 429;
   dead-letter the rest immediately, with the response body recorded.

5. **The signing secret anywhere but an External Credential.** Custom Metadata is
   right for *inbound* verification and wrong here: it makes rotation a
   deployment and puts a copy of the secret in Apex memory.

6. **Serializing the payload twice.** Two `JSON.serialize` calls on the same map
   are not guaranteed to be byte-identical, and any difference makes every
   request fail signature verification in a way that looks like a wrong key.

7. **`JSON.serialize(record)` as the payload.** It exports every loaded field,
   grows silently as other code touches the selector, and publishes internal API
   names as a contract.

8. **One Queueable per record.** `System.enqueueJob` is capped at 50 per
   synchronous transaction; a Data Loader batch of 200 fails at the 51st call and
   rolls back the load.

9. **Delta payloads under a retrying design.** Retry reorders; a delta applied
   out of order corrupts the receiver and applied twice double-counts.

10. **Treating a 2xx as "processed".** Many receivers queue internally and return
    200 before doing anything. Without an agreed reconciliation, your dashboard
    stays green through their incident.

11. **Building new work on Outbound Messages.** Their host reached end of support
    on 31 December 2025, and the platform queue drops undelivered messages at 24
    hours with no way to query or replay them.

12. **Alerting only on DLQ depth.** A small backlog that has stopped draining is
    the earlier and more serious signal, and depth never shows it.

## Official Sources Used

- Apex Developer Guide — Callout Limits and Limitations ("A single Apex transaction can make a maximum of 100 callouts to an HTTP request or an API call"; "The maximum cumulative timeout for callouts by a single Apex transaction is 120 seconds"; "The default timeout is 10 seconds. A custom timeout can be defined for each callout. The minimum is 1 millisecond and the maximum is 120,000 milliseconds"; "You can't make a callout when there are pending operations in the same transaction. Things that result in pending operations are DML statements, asynchronous Apex (such as future methods and batch Apex jobs), scheduled Apex, or sending email"; the 20 concurrent-callout restriction in Developer Edition orgs) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_timeouts.htm
- Apex Developer Guide — Execution Governors and Limits (100 callouts, 120 s cumulative callout timeout, `System.enqueueJob` capped at 50 synchronous / 1 asynchronous, 10,000 ms sync and 60,000 ms async CPU, 6 MB / 12 MB heap, 150 DML statements, 100 / 200 SOQL queries) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Apex Developer Guide — Queueable Apex ("Apex allows HTTP and web service callouts from queueable jobs, if they implement the `Database.AllowsCallouts` marker interface. In queueable jobs that implement this interface, callouts are also allowed in chained queueable jobs"; "When chaining jobs with `System.enqueueJob`, you can add only one job from an executing job. Only one child job can exist for each parent queueable job"; "For Developer Edition and Trial organizations, the maximum stack depth for chained jobs is 5, which means that you can chain jobs four times"; the `System.enqueueJob(queueable, delay)` 0–10 minute overload and the `AsyncOptions` overload with `MaximumQueueableStackDepth`; `System.AsyncInfo` accessors) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_queueing_jobs.htm
- Apex Developer Guide — Transaction Finalizers ("Only one finalizer instance can be attached to any Queueable job"; "A Queueable job that failed due to an unhandled exception can be successively re-enqueued five times by a transaction finalizer"; `System.attachFinalizer`, `FinalizerContext.getAsyncApexJobId()` / `getRequestId()` / `getResult()` / `getException()`, and the `System.ParentJobResult` values `SUCCESS` and `UNHANDLED_EXCEPTION`) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_transaction_finalizers.htm
- Apex Developer Guide — Named Credentials as Callout Endpoints (`callout:My_Named_Credential/some_path`; the `{!$Credential.Password}` and `{!$Credential.<AuthProviderName>.<ParameterName>}` merge syntax; "Salesforce manages all authentication for Apex callouts that specify a named credential as the callout endpoint so that your code doesn't have to") — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_named_credentials.htm
- Apex Reference Guide — Crypto Class (`generateMac(algorithmName, input, privateKey)` for producing an HMAC; `verifyHMac` for checking one) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_restful_crypto.htm
- Platform Events Developer Guide — Publishing Platform Event Messages Using Apex (`EventBus.publish`, `Database.SaveResult` handling, "`EventBus.publish()` can publish some passed-in events, even when other events can't be published due to errors", Publish After Commit counting "as one DML statement against the Apex DML statement limit" vs Publish Immediately counting "against a separate event publishing limit of 150 `EventBus.publish()` calls", and `Limits.getPublishImmediateDML()`) — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_publish_apex.htm
- SOAP API Developer Guide — Understanding Notifications ("A single SOAP message can include up to 100 notifications"; "If a message can't be delivered, the interval between retries increases exponentially, up to a maximum of two hours between retries"; "If the endpoint is unavailable, messages stay in the queue until sent successfully, or until they're 24 hours old. After 24 hours, messages are dropped from the queue"; "Messages are retried independent of their order in the queue. As a result, messages can be delivered out of order") — https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_om_outboundmessaging_notifications.htm
- Metadata API Developer Guide — `EventRelayConfig` (API 56.0+, suffix `.eventRelay`, directory `eventRelays`; `destinationResourceName` — "Required. The developer name of the named credential, which stores the AWS account information"; `eventChannel`; `relayOption` — "A JSON-encoded string that contains an option for resuming an event relay after the system recovers from an error", with `LATEST` default and `EARLIEST` resending stored events up to three days old; `state` values `RUN` / `PAUSE` / `STOP` / `DELETE`) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_eventrelayconfig.htm
- Salesforce Help — Connecting to an API Without a Connector Using HTTP Callout (Flow Builder generates an external service registration and an invocable action; an external credential and a named credential are required) — https://help.salesforce.com/s/articleView?id=platform.flow_http_callout.htm&type=5
- Salesforce Well-Architected — Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

### Claims deliberately not made

The Salesforce Help page for Flow HTTP Callout also documents constraints on
supported response formats and HTTP methods, and those have changed across
releases. The page is Aura-rendered and could not be fetched, so this skill makes
no claim about which verbs or content types are currently supported — see the
inline marker in [`gotchas.md`](gotchas.md), Gotcha 10. Check it in Flow Builder
against the target org before designing around a particular verb.

Event Relay throughput limits and its supported event-type list are not quoted
here. The `EventRelayConfig` metadata reference confirms the destination (Amazon
EventBridge) and the general categories (platform events and change data capture
events) but does not enumerate limits, and the Event Relay considerations page
could not be fetched.
