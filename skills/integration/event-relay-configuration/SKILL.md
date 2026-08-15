---
name: event-relay-configuration
description: "Use when forwarding Salesforce Platform Events or Change Data Capture to AWS EventBridge via Event Relay. Covers Named Credential + Connection setup, channel selection, event filter design, replay handling. NOT for consuming external events in Salesforce (see pub-sub-api or salesforce-connect) — use integration/aws-salesforce-patterns."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "event relay aws eventbridge"
  - "forward platform events to aws"
  - "salesforce to eventbridge cdc"
  - "event relay setup"
  - "event relay retry"
tags:
  - integration
  - event-relay
  - pub-sub
  - aws
  - eventbridge
inputs:
  - Platform Events or CDC channel to forward
  - AWS account + region for EventBridge
  - Throughput and retry requirements
outputs:
  - Event Relay configuration (Named Credential, Connection, Relay Config)
  - IAM / permission design
  - Filter strategy
  - Monitoring and replay runbook
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Event Relay Configuration (Salesforce → AWS EventBridge)

Event Relay is a Salesforce-managed subscriber that forwards platform events and
change data capture events to Amazon EventBridge with no code and no middleware.
It replaces the DIY pattern of an Apex callout from a platform event trigger, and
it replaces a self-hosted Pub/Sub API consumer, by moving the subscription, the
replay position, and the retry behaviour into the platform.

What it removes is operational: a process to host, a checkpoint to persist, a
consumer to page someone about. What it does **not** remove is at-least-once
delivery, unordered events, and a recovery fallback that can replay up to three
days of the event bus. That work moves to the AWS side, where it belongs.

---

## Before Starting

1. **Confirm the destination is Amazon EventBridge.** Event Relay relays "platform
   events and change data capture events from Salesforce to Amazon EventBridge."
   For any other target, this is the wrong tool — use Pub/Sub API with your own
   consumer, or a Named Credential callout from Apex.

2. **Establish who owns the AWS account.** Creating a relay registers a *pending*
   partner event source in AWS. Until an AWS administrator associates an event bus
   with it, nothing is delivered and Salesforce reports no error. If you cannot
   name that person, the integration cannot be completed.

3. **Determine whether the downstream target is idempotent.** This single fact
   decides the `relayOption` value, and it is far cheaper to establish now than at
   06:00 during a recovery.

4. **Baseline the event delivery allocation.** A relay is a subscribed client and
   consumes the org's daily delivery allocation per client. Query
   `PlatformEventUsageMetric` before switching it on.

---

## Core Concepts

### Five components, in dependency order

```text
1. The event           MyEvent__e  /  MyObject__ChangeEvent
2. Channel             MyChannel__chn                PlatformEventChannel
3. Channel member(s)   one per event, optional filter PlatformEventChannelMember
4. Credentials         ExternalCredential (AwsSv4) + NamedCredential
5. Relay               EventRelayConfig -> references (2) and (4)
```

### A channel is a typed stream

"A channel can hold only one type of events." The valid pairs:

| `channelType` | `eventType` | Carries |
|---|---|---|
| `event` | `custom` | Custom platform events (`__e`) |
| `data` | `data` | Change data capture events |
| `event` | `monitoring` | Real-Time Event Monitoring events |

Consequence: one relay per event *type*. An integration spanning custom events and
CDC is two channels, two relays, and two partner event sources.

### Filter at the channel member, not downstream

`PlatformEventChannelMember.filterExpression` (API 56.0 and later) is "based on
SOQL and supports a subset of SOQL operators and field types" — for example
`City__c = 'San Francisco'`. A filtered event is never delivered, so it never
consumes delivery allocation. Filtering in an EventBridge rule costs you the
delivery first.

### The relay config is mostly immutable

```xml
<EventRelayConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <destinationResourceName>callout:AWS_Account</destinationResourceName>
    <eventChannel>Order_Events__chn</eventChannel>
    <label>Order Events Relay</label>
    <relayOption>{"ReplayRecovery":"LATEST"}</relayOption>
    <state>STOP</state>
</EventRelayConfig>
```

- `destinationResourceName` **requires** the `callout:` prefix.
- On create, `state` may only be `STOP`.
- "You can update only the `state` and `relayOption` fields and not `eventChannel`
  or `destinationResourceName`." Repointing the relay means delete and recreate —
  and a new partner event source the AWS side must associate again.

### Replay recovery is a fallback, not the normal path

`relayOption` accepts exactly two values, `{"ReplayRecovery":"LATEST"}` (default)
and `{"ReplayRecovery":"EARLIEST"}`. There is **no specific-replay-id option** —
that is a Pub/Sub API capability, not an Event Relay one.

And it usually does not apply. On recovery the relay "attempts to resume sending
events from the event bus from where it left off. In rare occasions, if it can't
resume after the last relayed event, it uses the error recovery option." When it
does apply, `EARLIEST` means *everything still in the bus*, up to the three-day
retention — not "what you missed."

### Retention

High-volume platform event messages are stored for 72 hours (3 days); legacy
standard-volume messages for 24 hours. A relay paused longer than the retention
window loses whatever aged out, regardless of `relayOption`.

### State semantics

| State | Delivery | Position | Diagnostics |
|---|---|---|---|
| `RUNNING` | Yes | — | — |
| `PAUSED` | No | **Preserved** (within retention) | Preserved |
| `STOPPED` | No | Discarded — only new events on resume | **`LastRelayedEventTime` and error fields deleted** |
| `ERROR` | No | Retried; self-clears to `RUNNING` on success | Populated |

During an incident, **pause — never stop**.

---

## Common Patterns

### Pattern A — custom platform event to EventBridge

Channel (`event`/`custom`) → member per event → `AwsSv4` credential pair → relay.
Full metadata in [`references/examples.md`](references/examples.md), Example 1.

### Pattern B — CDC to EventBridge with a filter

Channel (`data`/`data`) → one member per `*ChangeEvent` with a `filterExpression`
that drops the regions or record types the AWS side does not care about. This is
where the allocation savings are: CDC on a busy object is the highest-volume stream
most orgs have.

### Pattern C — activation as a two-party runbook

Deploy in `STOP`, read the partner event source name from
`EventRelayFeedback.RemoteResource`
(`aws.partner/salesforce.com/orgID/channelID`), hand it to the AWS admin, wait for
the bus association, then set `RUN`.

### Pattern D — staleness monitoring

Poll `EventRelayFeedback` on a schedule and alarm on `Status == 'ERROR'`,
`Status in ('STOPPED','PAUSED')`, **and** `Status == 'RUNNING'` with a
`LastRelayedEventTime` older than the stream's known cadence. Status alone misses
both the self-clearing error and the wedged-but-running case. Implementation in
[`references/examples.md`](references/examples.md), Example 4.

---

## Decision Guidance

| Situation | Approach |
|---|---|
| Target is EventBridge, transformation belongs on the AWS side | Event Relay |
| Target is not AWS | Pub/Sub API consumer, or Named Credential callout from Apex |
| Need in-flight enrichment, batching, or an explicit replay id | Pub/Sub API consumer |
| Low volume, high value, delivery allocation is tight | Apex trigger subscriber — non-API subscribers don't count against the delivery allocation |
| Downstream target is idempotent | `{"ReplayRecovery":"EARLIEST"}` |
| Downstream target appends, notifies, or moves money | `{"ReplayRecovery":"LATEST"}` plus a reconciliation job |
| Only a subset of events matter to AWS | `filterExpression` on the channel member |
| Custom events *and* CDC both needed | Two channels, two relays — the platform forbids mixing |

---

## Recommended Workflow

1. **Confirm Event Relay fits**: destination is Amazon EventBridge, no in-flight
   transformation is required, and an AWS account owner is identified and
   available for the handshake.
2. **Design the channel per event type**, with one `PlatformEventChannelMember`
   per event and a `filterExpression` wherever the AWS side needs a subset.
   Remember the member full-name rule: `ChannelName_EventName` with double
   underscores collapsed to one.
3. **Create the `ExternalCredential` (`AwsSv4`) and `NamedCredential`**, making
   sure the credential's `AwsRegion` parameter and the named credential's
   `DefaultEndpoint` host name the same AWS region.
4. **Deploy the `EventRelayConfig` in `STOP`**, with the `callout:` prefix on
   `destinationResourceName` and the `relayOption` chosen against the downstream
   target's idempotency.
5. **Complete the AWS handshake**: send the `RemoteResource` partner event source
   name to the AWS admin, who associates an event bus and creates a rule with a
   target.
6. **Set the relay to `RUN`** and confirm delivery on both sides —
   `EventRelayFeedback.LastRelayedEventTime` in Salesforce, and the rule's
   invocation metrics in EventBridge.
7. **Wire monitoring and write the incident runbook**, including the staleness
   alarm and the "pause, never stop" rule.

---

## Review Checklist

- [ ] `destinationResourceName` carries the `callout:` prefix
- [ ] `state` is `STOP` in the creating deployment
- [ ] `channelType` / `eventType` pair is valid and matches the events on it
- [ ] One relay per event type; no attempt to mix custom events and CDC
- [ ] Channel member full names collapse double underscores (`SalesEvents_chn_...`)
- [ ] `filterExpression` applied wherever AWS needs a subset
- [ ] `AwsRegion` parameter and `DefaultEndpoint` host name the same region
- [ ] `relayOption` justified against downstream idempotency, in writing
- [ ] Deployment identity has Customize Application; monitoring identity has View
      Setup and Configuration
- [ ] AWS-side owner named; partner event source association is a tracked step
- [ ] Monitoring alarms on `LastRelayedEventTime` staleness, not only `Status`
- [ ] Runbook says pause, never stop
- [ ] Event delivery allocation baselined; any subscriber the relay replaces is
      retired in the same change

---

## Salesforce-Specific Gotchas

Full detail with quotes in [`references/gotchas.md`](references/gotchas.md).

1. **A relay cannot be created in `RUN`** — only `STOP`.
2. **Creating the relay only creates a *pending* partner event source**; without
   the AWS-side bus association, nothing flows and nothing errors.
3. **`destinationResourceName` needs the `callout:` prefix**, and cannot be
   updated afterwards.
4. **One channel holds one event type**, so one relay carries one type.
5. **`relayOption` is a rare fallback**, and `EARLIEST` replays the whole bus.
6. **`STOPPED` deletes your diagnostics**; `PAUSED` does not.
7. **`RUNNING` is not a health signal** — `ERROR` self-clears and a wedged relay
   still reports `RUNNING`.
8. **Every relayed event consumes the daily delivery allocation**, per client, and
   that allocation is shared with CDC.
9. **Deploy needs Customize Application**; query needs View Setup and Configuration.
10. **The AWS credential is not in the metadata** and its expiry is invisible from
    Salesforce.
11. **Region is configured twice** and must agree.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Relay metadata bundle | Channel, member(s) with filters, `ExternalCredential`, `NamedCredential`, `EventRelayConfig` in `STOP`, plus the `package.xml` |
| Two-party activation runbook | Salesforce steps, the partner event source name to hand over, AWS steps, and the final `RUN` transition, each with a named owner |
| Replay decision record | Which `relayOption` was chosen, the downstream idempotency evidence that justified it, and the reconciliation job if `LATEST` |
| Monitoring job | Scheduled `EventRelayFeedback` poll alarming on status **and** `LastRelayedEventTime` staleness |
| Allocation projection | Baseline `PlatformEventUsageMetric` reading and the projected delta from the new relay |

---

## Related Skills

- `integration/platform-events-integration` — designing the event payload itself,
  which becomes the public contract with every EventBridge consumer
- `integration/change-data-capture-integration` — CDC channel and entity selection,
  the highest-volume stream most orgs relay
- `integration/named-credentials-setup` — the `ExternalCredential` /
  `NamedCredential` pair and AWS Signature V4 configuration
