# Examples — Event Relay Configuration

Event Relay is a Salesforce-managed subscriber that forwards platform events and
change data capture events to Amazon EventBridge with no code and no middleware.
Every field, enum value, and XML shape below is from the Metadata API Developer
Guide and Object Reference for the Salesforce Platform (Summer '26, API 67.0).

Four metadata components have to exist, in this order:

```text
1. The event            MyEvent__e            (or a *__ChangeEvent)
2. A channel            MyChannel__chn        PlatformEventChannel
3. Channel membership   PlatformEventChannelMember   (one per event on the channel)
4. Credentials          ExternalCredential (AwsSv4) + NamedCredential
5. The relay            EventRelayConfig      references (2) and (4)
```

Deploying (5) before (2) or (4) fails. Deploying (3) before (2) fails.

---

## Example 1: Relay a custom platform event to EventBridge

**Context:** An org publishes `Order_Shipped__e` and a downstream AWS Step Function
must react within seconds. The team currently polls the REST API every five
minutes.

**Problem:** Polling is a five-minute latency floor plus a permanent API-call cost.
A CometD or Pub/Sub API subscriber would work but means owning a long-lived
process, its checkpointing, and its failure modes.

**Solution — the four metadata files.**

`force-app/main/default/platformEventChannels/Order_Events__chn.platformEventChannel-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PlatformEventChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <channelType>event</channelType>
    <eventType>custom</eventType>
    <label>Order Events</label>
</PlatformEventChannel>
```

`channelType` and `eventType` must agree. The valid pairs from the Metadata API
guide are:

| `channelType` | `eventType` | Carries |
|---|---|---|
| `event` | `custom` | Custom platform events (`__e`) |
| `data` | `data` | Change data capture events |
| `event` | `monitoring` | Real-Time Event Monitoring events |
| — | `standard` | Reserved for internal use |

A channel holds exactly one type: "A channel can hold only one type of events."
You cannot mix `Order_Shipped__e` and `AccountChangeEvent` on one channel, which
means you cannot relay both through one relay either.

`force-app/main/default/platformEventChannelMembers/Order_Shipped_Member.platformEventChannelMember-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PlatformEventChannelMember xmlns="http://soap.sforce.com/2006/04/metadata">
    <eventChannel>Order_Events__chn</eventChannel>
    <selectedEntity>Order_Shipped__e</selectedEntity>
</PlatformEventChannelMember>
```

Two naming rules on channel members that cost an afternoon each. First, the
`package.xml` member name is `ChannelName_EventName`, and double underscores must
be collapsed to one:

> "If your channel member name contains a custom channel name to make it unique,
> ensure to replace the double underscores in the name with one underscore. For
> example, the member name would be `SalesEvents_chn_AccountChangeEvent` and not
> `SalesEvents__chn_AccountChangeEvent`."
> — Metadata API Developer Guide, `PlatformEventChannelMember`

Second, you can filter at the channel member rather than relaying everything and
discarding it downstream. `filterExpression` is "based on SOQL and supports a
subset of SOQL operators and field types" (API 56.0 and later), and belongs in a
`CDATA` block:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PlatformEventChannelMember xmlns="http://soap.sforce.com/2006/04/metadata">
    <eventChannel>Order_Events__chn</eventChannel>
    <filterExpression><![CDATA[(Region__c='AMER')]]></filterExpression>
    <selectedEntity>Order_Shipped__e</selectedEntity>
</PlatformEventChannelMember>
```

Filtering here is not cosmetic — a filtered event is never delivered, so it never
counts against the org's daily event delivery allocation. Filtering in an
EventBridge rule costs you the delivery first.

`force-app/main/default/externalCredentials/AWS_EventBridge.externalCredential-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExternalCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>AWS EventBridge</label>
    <authenticationProtocol>AwsSv4</authenticationProtocol>
    <externalCredentialParameters>
        <parameterName>Principal</parameterName>
        <parameterType>NamedPrincipal</parameterType>
        <sequenceNumber>1</sequenceNumber>
    </externalCredentialParameters>
    <externalCredentialParameters>
        <parameterName>AwsService</parameterName>
        <parameterValue>events</parameterValue>
        <parameterType>AuthParameter</parameterType>
    </externalCredentialParameters>
    <externalCredentialParameters>
        <parameterName>AwsRegion</parameterName>
        <parameterValue>us-east-1</parameterValue>
        <parameterType>AuthParameter</parameterType>
    </externalCredentialParameters>
</ExternalCredential>
```

`AwsSv4` is the documented value: "For connections to Amazon Web Services using
Signature Version 4, use `AwsSv4`." `AwsRegion` and `AwsService` are supplied as
`AuthParameter` entries — the guide gives `AwsRegion` as the worked example of an
`AuthParameter` (`"For example, AwsRegion sets the AWS Region parameter to apply
for an AWS Signature V4 authentication protocol"`).

The access key and secret are **not** in this file. They are entered as the
principal's credentials in Setup after deployment — which is the point of
separating `ExternalCredential` from its principal.

`force-app/main/default/namedCredentials/AWS_Account.namedCredential-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<NamedCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>AWS Account</label>
    <namedCredentialType>SecuredEndpoint</namedCredentialType>
    <namedCredentialParameters>
        <description>EventBridge endpoint</description>
        <parameterName>DefaultEndpoint</parameterName>
        <parameterType>Url</parameterType>
        <parameterValue>https://events.us-east-1.amazonaws.com</parameterValue>
    </namedCredentialParameters>
    <namedCredentialParameters>
        <description>AWS SigV4 auth</description>
        <parameterName>DefaultAuth</parameterName>
        <parameterType>Authentication</parameterType>
        <externalCredential>AWS_EventBridge</externalCredential>
    </namedCredentialParameters>
</NamedCredential>
```

`force-app/main/default/eventRelays/Order_Events_Relay.eventRelay-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<EventRelayConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <destinationResourceName>callout:AWS_Account</destinationResourceName>
    <eventChannel>Order_Events__chn</eventChannel>
    <label>Order Events Relay</label>
    <relayOption>{"ReplayRecovery":"LATEST"}</relayOption>
    <state>STOP</state>
</EventRelayConfig>
```

Three things about this file that the Metadata API guide states explicitly:

- `destinationResourceName` is **required** and "contains the `callout:` prefix.
  For example: `callout:MyRelayNamedCredential`". A bare credential name is
  rejected.
- `state` on creation may only be `STOP`: "The event relay is created with a
  default state of `STOP` if you don't specify this field. If you specify this
  field when creating an event relay, the only valid value you can set is `STOP`."
  You cannot deploy a running relay.
- Only `state` and `relayOption` are updatable afterwards: "You can update only
  the `state` and `relayOption` fields and not `eventChannel` or
  `destinationResourceName`." Changing the channel or the credential means
  destroying and recreating the relay.

`package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types><members>Order_Events__chn</members><name>PlatformEventChannel</name></types>
    <types><members>Order_Shipped_Member</members><name>PlatformEventChannelMember</name></types>
    <types><members>AWS_EventBridge</members><name>ExternalCredential</name></types>
    <types><members>AWS_Account</members><name>NamedCredential</name></types>
    <types><members>Order_Events_Relay</members><name>EventRelayConfig</name></types>
    <version>67.0</version>
</Package>
```

Deploying this type requires **Customize Application**: "You must have the
Customize Application permission to deploy and retrieve this type" (both
`EventRelayConfig` and `PlatformEventChannel`).

**Why it works:** the relay is a platform-managed subscriber. Salesforce owns the
connection, the replay position, and the retries. There is no process to host, no
checkpoint file, and no consumer to page someone about at 3 a.m.

---

## Example 2: Activating the partner event source on the AWS side

**Context:** The metadata deployed cleanly. Nothing arrives in EventBridge.

**Problem:** Creating the relay only creates a *pending* partner event source in
the AWS account. Until an AWS administrator associates an event bus with it, the
source cannot accept events, and the relay cannot be started.

**Solution:**

```text
Salesforce side
  1. Deploy the metadata above. Relay state is STOP.
  2. Setup → Quick Find: "Event Relays" → Event Relays.
     The relay row shows its status and the partner event source name.

AWS side (an AWS admin, in the account named by the named credential)
  3. Amazon EventBridge console → Integration → Partner event sources.
     The source appears with status "Pending".
     Its name has the form:
       aws.partner/salesforce.com/<orgId>/<channelId>
     e.g. aws.partner/salesforce.com/00DRM000000Fxts2AC/0YLRM0000004Dfg4AE
  4. Associate it with an event bus. The source moves to "Active".
  5. Create an EventBridge rule on that bus, with a target
     (Lambda, Step Functions, SQS, ...).

Salesforce side
  6. Setup → Event Relays → [relay] → change state to Run.
     Or via Tooling API / Metadata API by updating <state> to RUN.
```

The partner event source name format is documented on the
`EventRelayFeedback.RemoteResource` field: "The name of the partner event source
associated with the event relay. It is in the format
`aws.partner/salesforce.com/orgID/channelID`."

**Why it works:** the two-sided handshake means Salesforce never has to hold
long-lived write access to an arbitrary AWS bus. The AWS account owner explicitly
opts in by associating a bus.

**Why nothing arrived before step 6:** the relay was in `STOP`. From the metadata
guide: "`STOP`—(Default) The event relay is stopped and no events are relayed to
Amazon EventBridge. All current state information is deleted."

---

## Example 3: Choosing the replay recovery option, and what it costs you

**Context:** The relay entered an error state overnight (an expired AWS credential)
and recovered at 06:00. 4,000 events were published while it was down.

**Problem:** Whether those 4,000 events are delivered depends entirely on a value
set at deploy time, and the two options have opposite failure modes.

**The contract**, from the `relayOption` field description:

```json
{"ReplayRecovery":"LATEST"}
```
> "(Default) Start relaying events from new events received in the event bus. Use
> this option if you aren't interested in missed events while the relay was down."

```json
{"ReplayRecovery":"EARLIEST"}
```
> "Resend all events stored in the event bus and relay new events thereafter. The
> event bus stores events for up to three days. Use this option if you want to
> reprocess all stored events and catch up on missed events."

Two facts make this a real decision rather than a preference:

1. `relayOption` is only consulted as a *fallback*. The `EventRelayFeedback.Status`
   documentation is precise: on recovery from `ERROR`, "The event relay attempts to
   resume sending events from the event bus from where it left off. In rare
   occasions, if it can't resume after the last relayed event, it uses the error
   recovery option in the `relayOption` field of `EventRelayConfig` to determine
   where to resume from." So in the common case, neither option applies — the relay
   resumes exactly where it stopped.

2. `EARLIEST` means *all* events still in the bus, up to the three-day retention —
   not "the ones you missed." A relay that has been down for ten minutes and falls
   back to `EARLIEST` replays up to three days of traffic into EventBridge.

**Solution — pick against the consumer, not against the relay:**

| Consumer property | Choose | Because |
|---|---|---|
| Idempotent (upsert on an event key) | `EARLIEST` | Redelivery is free; missing an event is not |
| Non-idempotent (appends, sends email, charges a card) | `LATEST` | A three-day replay would be an incident |
| Financial or audit-critical, non-idempotent | `LATEST` **plus** a reconciliation job | Neither option is safe; close the gap with a query, not with replay |

Changing it later is one of the two fields you can update:

```xml
<EventRelayConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <destinationResourceName>callout:AWS_Account</destinationResourceName>
    <eventChannel>Order_Events__chn</eventChannel>
    <label>Order Events Relay</label>
    <relayOption>{"ReplayRecovery":"EARLIEST"}</relayOption>
    <state>RUN</state>
</EventRelayConfig>
```

**Why it works:** the decision is made once, at design time, by someone who knows
whether the downstream consumer can tolerate duplicates — rather than at 06:00 by
whoever is on call.

---

## Example 4: Monitoring the relay from Salesforce

**Context:** The relay is live. You need to know when it breaks, from inside
Salesforce, without watching the EventBridge console.

**Solution:** `EventRelayFeedback` is a queryable standard object carrying the
relay's runtime state.

```sql
SELECT EventRelayNumber,
       Status,
       LastRelayedEventTime,
       ErrorCode,
       ErrorMessage,
       ErrorTime,
       ErrorIdentifier,
       RemoteResource,
       EventRelayConfig.DeveloperName
FROM EventRelayFeedback
ORDER BY ErrorTime DESC
```

`Status` is a restricted picklist with five documented values:

| Value | Meaning (from the Object Reference) |
|---|---|
| `RUNNING` | "actively relaying events from Salesforce to Amazon EventBridge" |
| `PAUSED` | Admin paused it. On resume, "events are relayed from the last position in the event bus, as long as they're within the retention window" |
| `STOPPED` | Default. "Some state information stored in `EventRelayFeedback` fields is deleted, such as `LastRelayedEventTime` and error fields. When the event relay is resumed, only new events are relayed" |
| `ERROR` | "no events are relayed... The system attempts periodically to recover from the error" |
| `DELETED` | "Reserved for future use" |

Note the asymmetry between `PAUSED` and `STOPPED`. Pausing preserves position;
stopping discards it *and* wipes the error fields you would use to diagnose why it
stopped. During an incident, pause — do not stop.

**A staleness alarm.** Because `Status` returns to `RUNNING` after a transient
error, status alone is not a health signal. `LastRelayedEventTime` is:

```apex
public class EventRelayMonitor implements Schedulable {

    private static final Integer STALE_MINUTES = 15;

    public void execute(SchedulableContext ctx) {
        List<EventRelayFeedback> feedback = [
            SELECT EventRelayNumber, Status, LastRelayedEventTime,
                   ErrorCode, ErrorMessage, EventRelayConfig.DeveloperName
            FROM EventRelayFeedback
        ];

        DateTime staleBefore = DateTime.now().addMinutes(-STALE_MINUTES);

        for (EventRelayFeedback f : feedback) {
            if (f.Status == 'ERROR') {
                alert(f, 'Relay in ERROR: ' + f.ErrorCode + ' — ' + f.ErrorMessage);
            } else if (f.Status == 'RUNNING'
                       && f.LastRelayedEventTime != null
                       && f.LastRelayedEventTime < staleBefore) {
                // RUNNING but silent. Either genuinely no traffic, or the
                // subscription is wedged. Only you know the expected cadence.
                alert(f, 'Relay RUNNING but last event was ' + f.LastRelayedEventTime);
            } else if (f.Status == 'STOPPED' || f.Status == 'PAUSED') {
                alert(f, 'Relay not running: ' + f.Status);
            }
        }
    }

    private void alert(EventRelayFeedback f, String message) {
        ApplicationLogger.error('EventRelayMonitor',
            f.EventRelayConfig.DeveloperName + ': ' + message);
    }
}
```

Querying `EventRelayConfig` itself requires **View Setup and Configuration**, and
the object is read-only: "To configure an event relay, use `EventRelayConfig` in
Tooling API or `EventRelayConfig` in Metadata API."

**Why it works:** it turns a silent, platform-managed subscriber into something
with an alarm on it. The `LastRelayedEventTime` check is the part that catches the
failure mode nobody expects — a relay that reports `RUNNING` and delivers nothing.

---

## Anti-Pattern: Treating the relay as an ordering or delivery guarantee

**What practitioners do:** design the AWS consumer to assume events arrive exactly
once, in publish order, and build state machines that depend on it.

**What goes wrong:** platform events are delivered at-least-once and are not
ordered across publishes; the relay inherits both properties and adds its own
recovery semantics on top. Worse, a relay that hits `ERROR` and cannot resume from
its last position falls back to `relayOption` — which, if set to `EARLIEST`,
replays up to three days of the event bus into a consumer that was designed for
exactly-once.

**Correct approach:** make the EventBridge target idempotent on a natural key
carried in the event payload (an order id, a record id plus a version). Publish
that key deliberately as a field on the platform event rather than relying on the
replay id, which is a transport concern and is not stable across a recovery. If the
downstream process genuinely cannot be made idempotent, set
`{"ReplayRecovery":"LATEST"}` and add a reconciliation query that closes the gap by
comparing state, not by replaying events.
