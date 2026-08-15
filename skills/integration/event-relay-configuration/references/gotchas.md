# Gotchas — Event Relay Configuration

Non-obvious behaviours of Salesforce Event Relay. Grounded in the Metadata API
Developer Guide (`EventRelayConfig`, `PlatformEventChannel`, `ExternalCredential`)
and the Object Reference (`EventRelayConfig`, `EventRelayFeedback`), Summer '26 /
API 67.0.

## Gotcha 1: A Newly Deployed Relay Cannot Be Started by the Deployment

**What happens:** The team deploys `<state>RUN</state>` so the relay comes up live.
The deploy either fails or silently lands in `STOP`, and the on-call engineer spends
the change window looking for a permissions problem.

> "The event relay is created with a default state of `STOP` if you don't specify
> this field. If you specify this field when creating an event relay, the only
> valid value you can set is `STOP`."
> — Metadata API Developer Guide, `EventRelayConfig.state`

**When it occurs:** On every first deployment of a relay, in every environment.

**How to avoid:** Treat activation as a separate, post-deploy step, and put it in
the runbook rather than the pipeline. It is not a defect — the two-sided AWS
handshake (Gotcha 2) means the relay *cannot* usefully run at deploy time anyway.
The second deployment, which updates `state` to `RUN`, is valid because `state` is
one of the two updatable fields.

---

## Gotcha 2: Creating the Relay Only Creates a *Pending* Partner Event Source

**What happens:** All the metadata deploys, the relay is set to `RUN`, and no event
ever reaches EventBridge. There is no error in Salesforce, because from
Salesforce's point of view nothing is wrong.

Creating an event relay registers a partner event source in the AWS account in
**pending** status. Until an AWS administrator associates an event bus with it,
the source cannot receive anything.

**When it occurs:** Whenever the Salesforce team and the AWS team are different
teams — which is the normal case, and precisely why this stalls.

**How to avoid:** Plan the handshake as a two-party change with a named owner on
each side:

```text
Salesforce  deploy metadata; relay in STOP
AWS         EventBridge → Integration → Partner event sources
            find aws.partner/salesforce.com/<orgId>/<channelId>  (status Pending)
            associate an event bus  → status Active
AWS         create a rule on that bus with a target
Salesforce  Setup → Event Relays → set state to Run
```

The exact source name is readable from Salesforce without asking AWS — it is the
`RemoteResource` field on `EventRelayFeedback`, documented as
`aws.partner/salesforce.com/orgID/channelID`. Send that string to the AWS admin
rather than a screenshot.

---

## Gotcha 3: `destinationResourceName` Must Carry the `callout:` Prefix

**What happens:** The deploy fails with an invalid-field error, or the relay is
created and immediately errors. The named credential exists and is named exactly
what the file says.

> "Required. The developer name of the named credential, which stores the AWS
> account information. The `destinationResourceName` value contains the
> `callout:` prefix. For example: `callout:MyRelayNamedCredential`"
> — Metadata API Developer Guide

**When it occurs:** Whenever the value is hand-written rather than copied from the
documented sample, because every other metadata reference to a named credential in
the platform is a bare name.

**How to avoid:** Copy the sample shape:

```xml
<destinationResourceName>callout:AWS_Account</destinationResourceName>
```

Note also that this is one of the two fields you **cannot** update: "You can update
only the `state` and `relayOption` fields and not `eventChannel` or
`destinationResourceName`." Pointing a relay at a different AWS account means
deleting and recreating it — and recreating it produces a *new* partner event
source that the AWS side must associate again.

---

## Gotcha 4: One Channel Holds One Event Type, So One Relay Carries One Type

**What happens:** A team builds a single "integration channel" intended to carry
custom platform events *and* change data capture events, so one relay serves the
whole integration. The channel will not deploy, or the second
`PlatformEventChannelMember` is rejected.

> "The type of events that the channel can hold. A channel can hold only one type
> of events."
> — Metadata API Developer Guide, `PlatformEventChannel.eventType`

The valid `channelType` / `eventType` pairs are `event`+`custom`, `data`+`data`,
and `event`+`monitoring` (`standard` is "Reserved for internal use").

**When it occurs:** During design, when someone reasonably assumes a channel is a
transport rather than a typed stream.

**How to avoid:** Plan one channel and one relay per event type from the start:

```text
Order_Events__chn    channelType=event  eventType=custom      Order_Shipped__e, Order_Cancelled__e
Account_CDC__chn     channelType=data   eventType=data        AccountChangeEvent
Security_Mon__chn    channelType=event  eventType=monitoring  LoginEventStream
```

Multiple *events of the same type* on one channel is fine and is the intended
pattern — add one `PlatformEventChannelMember` per event. The constraint is on
mixing types.

---

## Gotcha 5: `relayOption` Is a Fallback, Not the Normal Recovery Path

**What happens:** A team sets `{"ReplayRecovery":"EARLIEST"}` believing it means
"catch up on anything missed." The relay recovers from a ten-minute outage and
replays three days of events into a downstream consumer.

Two separate facts collide here. First, on recovery the relay normally does *not*
consult `relayOption` at all:

> "The event relay attempts to resume sending events from the event bus from where
> it left off. **In rare occasions**, if it can't resume after the last relayed
> event, it uses the error recovery option in the `relayOption` field of
> `EventRelayConfig` to determine where to resume from."
> — Object Reference, `EventRelayFeedback.Status`

Second, `EARLIEST` is not scoped to the outage:

> "Resend all events stored in the event bus and relay new events thereafter. The
> event bus stores events for up to three days."

**When it occurs:** Rarely — which is the problem. The behaviour is exercised for
the first time during a real incident, in production, at the worst moment.

**How to avoid:** Choose against the downstream consumer's idempotency, not
against a preference for completeness. If the EventBridge target is idempotent on
a business key, `EARLIEST` is safe and a three-day replay is merely noisy. If it is
not — if it appends rows, sends email, or moves money — use `LATEST` and close the
gap with a reconciliation query that compares *state*, never by replaying events.

---

## Gotcha 6: `STOPPED` Destroys Your Diagnostics; `PAUSED` Does Not

**What happens:** A relay errors. The responder stops it "to make it stop
retrying," intending to investigate. The error fields are now empty and the last
relayed timestamp is gone.

> "`STOPPED`—The event relay is stopped and no events are relayed to Amazon
> EventBridge. **Some state information stored in `EventRelayFeedback` fields is
> deleted, such as `LastRelayedEventTime` and error fields.** When the event relay
> is resumed, only new events are relayed."

Compare:

> "`PAUSED`— An administrator paused the event relay. No events are relayed to
> Amazon EventBridge during this status. When an administrator resumes the event
> relay, events are relayed from the last position in the event bus, as long as
> they're within the retention window."

**When it occurs:** During the first production incident, because "stop" is the
word people reach for.

**How to avoid:** Put it in the runbook in exactly these words: **during an
incident, pause — never stop.** Pausing halts delivery, preserves the replay
position, and preserves the error fields you need to diagnose. Stopping discards
both, and on resume you silently lose every event published while it was stopped.

---

## Gotcha 7: `RUNNING` Is Not a Health Signal

**What happens:** A monitor alerts on `Status != 'RUNNING'`. The relay's
subscription wedges, `Status` stays `RUNNING`, no events flow, and nothing alerts.
The gap is discovered downstream, days later.

`ERROR` is also self-clearing — "The system attempts periodically to recover from
the error. If it succeeds, the `Status` field value changes to `RUNNING`" — so a
poll that samples between failures never sees `ERROR` at all.

**When it occurs:** With any status-only monitor, and with any monitor whose poll
interval is longer than the platform's recovery interval.

**How to avoid:** Alarm on `LastRelayedEventTime` staleness relative to the
integration's known cadence, in addition to `Status`. A relay reporting `RUNNING`
whose last delivery was 40 minutes ago on a stream that publishes every minute is
broken, regardless of what the picklist says. Capture `ErrorCode`, `ErrorMessage`,
`ErrorTime`, and `ErrorIdentifier` on every poll — they describe only the *last*
error and are wiped by a stop.

---

## Gotcha 8: Every Relayed Event Consumes Your Event Delivery Allocation

**What happens:** A team adds a relay alongside existing CometD and Pub/Sub API
subscribers, and the org starts hitting its daily event delivery limit. The relay
looks free because it costs no compute.

The Platform Events Developer Guide counts event relays as a delivery client
throughout its allocation discussion — the daily delivered-event allocation applies
to "Pub/Sub API clients, CometD clients, `empApi` Lightning components, and event
relays," and "The number of delivered events to clients is counted for each
subscribed client, including event relays."

That last clause is the expensive one: adding a relay to a stream that already has
two subscribers does not split the existing budget, it adds a third consumer's
worth of deliveries. The guide's own worked example:

> "For example, you have an Unlimited Edition org with a default allocation of
> 50,000 events in a 24-hour period. Within a few hours, 20,000 event messages are
> delivered to two subscribed clients. So you consumed 40,000 events and are still
> entitled to 10,000 events within the 24-hour period."

Note also that "The event delivery allocation is shared between high-volume
platform events and Change Data Capture events," so a CDC relay competes with your
custom-event traffic for the same daily budget.

**When it occurs:** In orgs that already stream events, at the point the relay is
switched from `STOP` to `RUN` — often weeks after the deployment that created it,
so the cause is not obvious.

**How to avoid:** Baseline usage before enabling. Query `PlatformEventUsageMetric`
(or enable Enhanced Usage Metrics, available in API 58.0 and later, for a per-client
breakdown) and project the relay's contribution from the stream's publish rate.
Where a relay is replacing a CometD subscriber, retire the subscriber in the same
change rather than running both "for a while."

---

## Gotcha 9: Deploying and Retrieving Requires Customize Application

**What happens:** A CI service user with a carefully minimised permission set fails
to deploy the relay, or retrieves a package silently missing it.

> "You must have the Customize Application permission to deploy and retrieve this
> type."
> — Metadata API Developer Guide, `EventRelayConfig` (the same rule is stated for
> `PlatformEventChannel`)

And on the read side, from the Object Reference: "To retrieve or query this object,
you must have the View Setup and Configuration permission."

**When it occurs:** In pipelines that use a least-privilege deployment user, and in
monitoring code that queries `EventRelayConfig` as an integration user.

**How to avoid:** Grant Customize Application to the deployment identity and View
Setup and Configuration to the monitoring identity, and record why in the permission
set description — a future least-privilege review will otherwise strip them.

---

## Gotcha 10: The AWS Credential Is Not in the Metadata, and Its Expiry Is Invisible

**What happens:** The relay runs for months and then enters `ERROR` overnight. The
metadata is unchanged and source control shows nothing.

`ExternalCredential` metadata carries the authentication *protocol* (`AwsSv4`) and
its parameters (`AwsRegion`, `AwsService`), but the principal's actual key material
is entered in Setup and is deliberately not in the deployable artifact. Nothing in
the repository changes when it rotates or expires, and nothing in Salesforce warns
before it does.

**When it occurs:** At AWS key rotation, at IAM policy changes, and when a
temporary STS-based principal reaches the end of its duration.

**How to avoid:** Treat the credential as an operational asset with its own expiry
date, recorded outside the repo. Prefer the STS variant (`AuthProtocolVariant`
`AwsSv4_STS` with an `AwsStsPrincipal`) so the long-lived secret lives in AWS IAM
rather than in Salesforce, and so revocation is an AWS-side action. Either way, the
detection path is the `EventRelayFeedback` monitor from Gotcha 7 — the credential
itself gives you no signal.

---

## Gotcha 11: Region Is Configured in Two Places and Must Agree

**What happens:** The relay authenticates but events never appear on the bus, or
signature validation fails intermittently.

The AWS region appears twice in the configuration:

- `ExternalCredential` → `AwsRegion` as an `AuthParameter` — used to compute the
  Signature Version 4 signing scope.
- `NamedCredential` → `DefaultEndpoint` URL — for example
  `https://events.us-east-1.amazonaws.com`.

A SigV4 signature scoped to one region presented to another region's endpoint is
not valid.

**When it occurs:** After a copy-paste from another integration, or when an
environment is stood up in a second region and only one of the two values is
updated.

**How to avoid:** Derive both from a single value in whatever templates your
pipeline uses, and add the pair to the deployment review checklist. When a relay
authenticates but delivers nothing, compare these two strings before anything else.
