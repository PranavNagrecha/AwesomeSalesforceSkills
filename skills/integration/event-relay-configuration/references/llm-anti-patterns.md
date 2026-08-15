# LLM Anti-Patterns — Event Relay Configuration

Mistakes AI assistants reliably make when asked to "stream Salesforce events to
AWS."

## Anti-Pattern 1: Deploying a Relay in the `RUN` State

**What the LLM generates:**

```xml
<EventRelayConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <destinationResourceName>callout:AWS_Account</destinationResourceName>
    <eventChannel>Order_Events__chn</eventChannel>
    <label>Order Events Relay</label>
    <state>RUN</state>
</EventRelayConfig>
```

**Why it happens:** The user asked for a working relay, and every other metadata
type deploys in its final state. Nothing about the field name suggests a
create-time restriction.

**Correct pattern:**

```
On CREATE, the only valid state is STOP:

  "The event relay is created with a default state of STOP if you don't specify
   this field. If you specify this field when creating an event relay, the only
   valid value you can set is STOP."

Activation is a separate step AFTER the AWS side associates an event bus with
the pending partner event source. state is one of the two updatable fields
(state and relayOption), so the second deploy - or Setup, or Tooling API - can
set RUN.

Always present this as a two-phase change with an AWS-side step in the middle.
```

**Detection hint:** `<state>RUN</state>` in a file being created rather than
updated, or a single-deploy plan with no AWS-side step.

---

## Anti-Pattern 2: Omitting the `callout:` Prefix

**What the LLM generates:**

```xml
<destinationResourceName>AWS_Account</destinationResourceName>
```

**Why it happens:** Every other metadata reference to a named credential in the
platform is a bare developer name. `callout:` is a runtime URL scheme used in
Apex endpoints, so putting it in a metadata field looks wrong.

**Correct pattern:**

```
The field description is explicit:

  "The developer name of the named credential, which stores the AWS account
   information. The destinationResourceName value contains the callout: prefix.
   For example: callout:MyRelayNamedCredential"

  <destinationResourceName>callout:AWS_Account</destinationResourceName>

And it cannot be corrected in place afterwards: "You can update only the state
and relayOption fields and not eventChannel or destinationResourceName."
A wrong value means delete and recreate - which produces a NEW partner event
source that the AWS side must associate again.
```

**Detection hint:** a `destinationResourceName` value with no `callout:` prefix.

---

## Anti-Pattern 3: One Channel for Everything

**What the LLM generates:** a single `Integration__chn` with
`PlatformEventChannelMember` entries for `Order_Shipped__e` and
`AccountChangeEvent`, feeding one relay.

**Why it happens:** "Channel" reads as a transport. Consolidating is good design
advice almost everywhere else.

**Correct pattern:**

```
A channel is a TYPED stream:

  "The type of events that the channel can hold. A channel can hold only one
   type of events."

Valid channelType / eventType pairs:
  event + custom      custom platform events (__e)
  data  + data        change data capture events
  event + monitoring  Real-Time Event Monitoring events
  (standard is "Reserved for internal use")

So: one channel and one relay PER EVENT TYPE. Multiple events of the SAME type
on one channel is the intended pattern - add one PlatformEventChannelMember per
event.
```

**Detection hint:** a channel with members whose suffixes are not all `__e`, or
not all `ChangeEvent`; or a `channelType` / `eventType` pair outside the table.

---

## Anti-Pattern 4: Describing `EARLIEST` as "Replays What You Missed"

**What the LLM generates:** "Set `{"ReplayRecovery":"EARLIEST"}` so no events are
lost during an outage."

**Why it happens:** The enum name implies "from the earliest missed event," and
"don't lose events" is the safe-sounding recommendation.

**Correct pattern:**

```
Two corrections, both from the docs:

1. relayOption is a FALLBACK, not the normal recovery path:
     "The event relay attempts to resume sending events from the event bus from
      where it left off. In rare occasions, if it can't resume after the last
      relayed event, it uses the error recovery option in the relayOption
      field..."
   In the common case neither option applies.

2. EARLIEST is not scoped to the outage:
     "Resend all events stored in the event bus and relay new events thereafter.
      The event bus stores events for up to three days."
   A relay down for ten minutes that falls back to EARLIEST can replay three
   days of traffic.

Choose against the DOWNSTREAM CONSUMER's idempotency:
  idempotent target      -> EARLIEST is safe, merely noisy
  non-idempotent target  -> LATEST, plus a reconciliation job that compares
                            state rather than replaying events
```

**Detection hint:** any recommendation of `EARLIEST` that does not first establish
whether the EventBridge target is idempotent.

---

## Anti-Pattern 5: Telling the Responder to Stop the Relay

**What the LLM generates:** "If the relay is erroring, stop it, investigate, then
restart."

**Why it happens:** Stop/start is the universal incident reflex, and `STOP` is the
default state so it reads as benign.

**Correct pattern:**

```
STOP is destructive to your diagnostics and to your position:

  "STOPPED - ... Some state information stored in EventRelayFeedback fields is
   deleted, such as LastRelayedEventTime and error fields. When the event relay
   is resumed, only new events are relayed."

PAUSE is not:

  "PAUSED - ... When an administrator resumes the event relay, events are
   relayed from the last position in the event bus, as long as they're within
   the retention window."

Incident guidance is therefore: PAUSE, never STOP. Stopping discards the error
fields you were about to read AND silently drops everything published while
stopped.
```

**Detection hint:** the words "stop the relay" in any troubleshooting or incident
guidance.

---

## Anti-Pattern 6: Monitoring Only `Status`

**What the LLM generates:**

```sql
SELECT Id, Status FROM EventRelayFeedback WHERE Status != 'RUNNING'
```

**Why it happens:** There is a status field with a healthy value. Alerting on
"not healthy" is the obvious construction.

**Correct pattern:**

```
Status is a poor health signal for two documented reasons:

  - ERROR is self-clearing: "The system attempts periodically to recover from
    the error. If it succeeds, the Status field value changes to RUNNING."
    A poll that samples between failures never sees ERROR.
  - A wedged subscription can report RUNNING while delivering nothing.

Alarm on staleness as well as status:

  SELECT EventRelayNumber, Status, LastRelayedEventTime,
         ErrorCode, ErrorMessage, ErrorTime, ErrorIdentifier,
         RemoteResource, EventRelayConfig.DeveloperName
  FROM EventRelayFeedback

  alert if Status == 'ERROR'
  alert if Status == 'RUNNING' and LastRelayedEventTime < now - expected_cadence
  alert if Status in ('STOPPED', 'PAUSED')

Querying this requires View Setup and Configuration.
```

**Detection hint:** a monitoring query that selects `Status` and not
`LastRelayedEventTime`.

---

## Anti-Pattern 7: Presenting the Relay as Free

**What the LLM generates:** "Event Relay requires no code and no middleware, so it
is a zero-cost way to get events into AWS."

**Why it happens:** The comparison being made is against running a Pub/Sub API
consumer, where the cost is compute and operations. The platform-side cost is
invisible in that framing.

**Correct pattern:**

```
A relay is a subscribed client and consumes the org's daily event delivery
allocation like any other:

  "The event delivery allocation is how many event messages can be delivered in
   a 24-hour period to Pub/Sub API and CometD subscribers, empApi Lightning
   components, and event relays."

  "The number of delivered events to clients is counted for each subscribed
   client, including event relays."

So adding a relay to a stream that already has two subscribers adds a third
consumer's worth of deliveries - it does not share the existing budget. The
allocation is also "shared between high-volume platform events and Change Data
Capture events."

Baseline with PlatformEventUsageMetric (API 50.0+; Enhanced Usage Metrics in
API 58.0+ for granular time segments) BEFORE switching the relay to RUN, and
retire any CometD subscriber the relay replaces in the same change.
```

**Detection hint:** an answer recommending a relay with no mention of the event
delivery allocation or of `PlatformEventUsageMetric`.

---

## Anti-Pattern 8: Skipping the AWS Handshake Entirely

**What the LLM generates:** a complete, correct set of Salesforce metadata and the
instruction "deploy this and events will flow to EventBridge."

**Why it happens:** The prompt is a Salesforce prompt. Everything the model can
produce lives on the Salesforce side, so the answer feels complete.

**Correct pattern:**

```
Creating the relay only registers a PENDING partner event source in the AWS
account. Until an AWS admin associates an event bus with it, nothing can be
delivered - and Salesforce reports no error, because from its side nothing is
wrong.

Always hand back a two-party runbook:

  Salesforce  deploy metadata (relay lands in STOP)
  Salesforce  read the source name from EventRelayFeedback.RemoteResource,
              format: aws.partner/salesforce.com/orgID/channelID
  AWS         EventBridge -> Integration -> Partner event sources
              find the pending source, associate an event bus
  AWS         create a rule on that bus with a target
  Salesforce  set state to RUN

Also flag the two-sided region requirement: ExternalCredential's AwsRegion
AuthParameter and the NamedCredential's DefaultEndpoint URL must name the same
region, or SigV4 signing scope will not match the endpoint.
```

**Detection hint:** an Event Relay answer with no AWS-side step, or one that never
mentions the partner event source.
