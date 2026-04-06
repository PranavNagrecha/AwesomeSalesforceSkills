# LLM Anti-Patterns — Streaming API and PushTopic

Common mistakes AI coding assistants make when generating or advising on Salesforce Streaming API and PushTopic configuration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending PushTopic for New Implementations

**What the LLM generates:** "Create a PushTopic to stream Account changes to your external system" without noting that PushTopic and the Streaming API are legacy features. Platform Events, Change Data Capture, and Pub/Sub API are the modern alternatives.

**Why it happens:** PushTopic has extensive training data from years of Salesforce integration documentation. LLMs default to it without recognizing the Salesforce evolution toward event-driven architectures.

**Correct pattern:**

```text
Streaming technology evolution in Salesforce:

LEGACY (still functional but not recommended for new development):
- PushTopic: SOQL-based record change streaming
- Generic Streaming Events: custom payload channels

CURRENT (recommended for new development):
- Change Data Capture (CDC): replaces PushTopic for record change streaming
  - Automatic events, richer payload, supports delete/undelete
- Platform Events: replaces Generic Streaming for custom business events
  - Declarative schema, Apex/Flow/API publishing
- Pub/Sub API (gRPC): replaces CometD for external subscription
  - Better performance, bidirectional, managed replay

Migrate existing PushTopics to CDC where possible.
```

**Detection hint:** Flag new integration designs that use PushTopic instead of CDC or Platform Events. Look for `PushTopic` object creation in Apex or setup instructions.

---

## Anti-Pattern 2: Not Handling CometD Reconnection and Replay

**What the LLM generates:** CometD client code that connects once and subscribes without implementing reconnection logic or replay ID management for recovering missed events after a network interruption.

**Why it happens:** Basic CometD examples show the happy path: connect, subscribe, receive. The reconnection with replay (critical for production reliability) adds significant complexity that tutorials often omit.

**Correct pattern:**

```text
CometD client reliability requirements:

1. Connection management:
   - Implement automatic reconnection on disconnect
   - Use exponential backoff for reconnection attempts
   - Handle: DISCONNECTED, NETWORK_ERROR, HANDSHAKE_FAILURE

2. Replay ID management:
   - Store the last received ReplayId persistently (database, file)
   - On reconnect, subscribe with the stored ReplayId
   - If ReplayId has expired (>24 hours for PushTopic):
     fall back to -1 (all retained) or -2 (new only)

3. CometD replay extension:
   Map<String, Long> replayMap = new HashMap<>();
   replayMap.put("/topic/MyPushTopic", lastStoredReplayId);
   client.addExtension(new CometDReplayExtension(replayMap));

4. Error handling:
   - Handle advisory messages on /meta/handshake, /meta/connect
   - Log and alert on repeated connection failures
```

**Detection hint:** Flag CometD implementations without reconnection logic or ReplayId persistence. Look for subscribe calls without replay extension configuration.

---

## Anti-Pattern 3: Creating PushTopics with Non-Selective SOQL Queries

**What the LLM generates:** `PushTopic pt = new PushTopic(); pt.Query = 'SELECT Id, Name, Description FROM Account';` with an unfiltered query that evaluates every Account record on every change, causing performance degradation.

**Why it happens:** LLMs generate the simplest query that returns the desired fields. The performance implications of PushTopic query evaluation (which runs on every DML event matching the sObject) are not commonly discussed.

**Correct pattern:**

```text
PushTopic query best practices:

- Query is evaluated on every create/update/delete/undelete of the sObject
- Broad queries impact org performance

Optimize:
1. SELECT only the fields you need in the notification payload
   BAD:  SELECT Id, Name, Description, BillingAddress, ... (20 fields)
   GOOD: SELECT Id, Name, Status__c (only fields the consumer needs)

2. Use WHERE clause to filter the scope:
   pt.Query = 'SELECT Id, Name FROM Account WHERE Type = \'Customer\'';
   (only notifies when Customer accounts change)

3. Set NotifyForOperationCreate, NotifyForOperationUpdate, etc.
   to limit which DML operations trigger notifications

4. Set NotifyForFields to 'Referenced' (notify only when selected
   fields change) or 'Where' (notify when WHERE fields change)
```

**Detection hint:** Flag PushTopic definitions with SELECT * or many fields, or without a WHERE clause. Check `NotifyForFields` setting — default 'Referenced' is usually correct but should be intentional.

---

## Anti-Pattern 4: Exceeding the PushTopic and Streaming Channel Limits

**What the LLM generates:** "Create a PushTopic for each object you want to monitor" without noting the org-wide limits on PushTopics and streaming channels.

**Why it happens:** Limits on streaming channels are less documented than governor limits. LLMs create PushTopics freely without checking allocation.

**Correct pattern:**

```text
Streaming API limits:

PushTopics:
- Maximum 100 PushTopics per org (across all sObjects)
- Maximum 2,000 concurrent CometD clients per org
- Event delivery retention: 24 hours (for replay)

Generic Streaming Events:
- Maximum 100 streaming channels per org
- Separate from PushTopic count

CometD client limits:
- Maximum connections per user: varies (typically 25)
- Long-poll timeout: 120 seconds (reconnect required)

If approaching limits:
- Consolidate PushTopics (use broader queries with client-side filtering)
- Migrate to CDC (no PushTopic count limit — enable per object)
- Use Pub/Sub API (better connection management, fewer client connections)
```

**Detection hint:** Flag designs that propose more than 20 PushTopics without checking the 100-per-org limit. Check for missing client connection limit considerations.

---

## Anti-Pattern 5: Not Using the Correct Channel Path Format

**What the LLM generates:** Subscribing to `/PushTopic/MyTopic` or `/events/MyTopic` instead of the correct channel path format for each streaming type.

**Why it happens:** Different streaming mechanisms use different channel path prefixes. LLMs mix them up because the patterns are similar but not identical.

**Correct pattern:**

```text
Correct channel path formats:

PushTopic:
  /topic/{PushTopicName}
  Example: /topic/AccountChanges

Generic Streaming Event:
  /u/{StreamingChannelName}
  Example: /u/MyCustomChannel

Platform Event:
  /event/{EventApiName}
  Example: /event/Order_Update__e

Change Data Capture (specific object):
  /data/{ObjectChangeEventName}
  Example: /data/AccountChangeEvent

Change Data Capture (all changes):
  /data/ChangeEvents

Do NOT use:
  /PushTopic/ (wrong prefix)
  /events/ (wrong prefix)
  /topic/Order_Update__e (wrong — Platform Events use /event/)
```

**Detection hint:** Flag CometD subscriptions with incorrect channel prefixes. Check for `/PushTopic/` instead of `/topic/`, or `/events/` instead of `/event/`.
