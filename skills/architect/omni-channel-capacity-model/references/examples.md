# Examples — Omni-Channel Capacity Model

## Example 1: Multi-Channel Contact Center with Weighted Capacity

**Context:** A financial services company runs a contact center with 50 agents handling cases (email), live chat, and inbound phone calls through Omni-Channel. Agents currently use tab-based capacity (1 unit per item) and complain about being assigned a phone call while already on two chats.

**Problem:** Every routing configuration charges a weight of 1, so all work items cost the same. An agent with 3 items (2 chats + 1 phone call) appears to have the same load as an agent with 3 open cases, even though a phone call demands full attention. (Corrected framing: tab-based versus status-based capacity decides when capacity is released, not how much an item costs; the cost is the routing configuration's weight.)

**Solution:**

```text
Presence Configuration: "Standard Agent"
  Total Capacity: 10

Routing Configuration Weights (QueueRoutingConfig.capacityWeight):
  Voice:     10 units  (fully occupies agent)
  Case:       5 units  (moderate effort, async)
  Chat:       3 units  (real-time, concurrent OK)
  Messaging:  3 units  (real-time, concurrent OK)

Interruptible Channels (ServiceChannel.isInterruptible = true): Case, Messaging
Non-Interruptible Channels: Voice, Chat

Result scenarios for an agent with capacity 10:
  - 1 Voice call = 10/10 (full, no more work routed)
  - 2 Chats = 6/10 (room for 1 more chat but not a case)
  - 1 Case + 1 Chat = 8/10 (room for nothing at weight 3+)
  - 2 Cases = 10/10 (full)
```

**Why it works:** Weighted capacity prevents the platform from stacking a phone call on top of active chats. The agent's capacity is consumed proportionally to real effort, and voice calls fill the entire budget so no concurrent work is assigned.

---

## Example 2: Skills Matrix with Overflow for Insurance Claims

**Context:** An insurance company has three specialized queues: Auto Claims, Home Claims, and General Inquiries. Each queue has 10 dedicated agents. During storm season, Home Claims volume triples and the dedicated team cannot keep up.

**Problem:** Without overflow, Home Claims queue wait times spike to 30+ minutes while Auto Claims agents sit at 40% utilization.

**Solution:**

```text
Skills Setup:
  Skill: "Auto Claims"    -> assigned to 10 Auto agents + 5 cross-trained General agents
  Skill: "Home Claims"    -> assigned to 10 Home agents + 5 cross-trained General agents
  Skill: "General Support" -> assigned to all 30 agents

Routing Configuration (Primary):
  Queue: Home Claims Queue
  Routing Model: Most Available
  Required Skill: "Home Claims"
  Priority: 1

Routing Configuration (Secondary / Overflow):
  Queue: Home Claims Overflow Queue
  Routing Model: Most Available
  Required Skill: "General Support"
  Priority: 2
  Activation: After 90-second timeout on primary queue
  (UNVERIFIED (2026-10-03): the routing configuration exposes queueOverflowAssignee
   and userOverflowAssignee, but the trigger conditions for overflow are in
   Salesforce Help only; confirm the timeout mechanism before committing to it.
   For skills, dropAdditionalSkillsTimeout is the documented fallback.)

Monitoring:
  - Weekly overflow rate report
  - Alert if overflow exceeds 20% of total Home Claims volume
  - Cross-training plan triggered when overflow exceeds 15% for 2 consecutive weeks
```

**Why it works:** Primary routing tries the specialist pool first. If no Home Claims agent has capacity within 90 seconds, the item overflows to the General Support pool. Cross-trained agents handle the overflow while specialists focus on the highest-complexity items.

---

## Anti-Pattern: Flat Capacity Across All Channels

**What practitioners do:** Set all Service Channel weights to 1 and give agents a capacity of 5, thinking "5 concurrent items is reasonable."

**What goes wrong:** An agent ends up with 1 phone call + 2 chats + 2 cases simultaneously. The phone call demands full attention, so chats go unanswered and customer satisfaction drops. Meanwhile, the system sees the agent at 5/5 capacity and routes the next phone call to a different agent who may also be juggling multiple items.

**Correct approach:** Use differentiated weights that reflect actual agent effort. A phone call should consume all or nearly all capacity. Chats should consume moderate capacity. Cases should consume a middle range since they require focus but are not real-time. Start with Voice=10, Case=5, Chat=3 and adjust from measured handle times.

---

## Example 3: Deployable Capacity Metadata For Blended Voice, Messaging, And Case Agents

**Context:** 80 blended agents take phone calls, web messaging, and cases. Measured handle times: voice 420 s, messaging 600 s across about three concurrent sessions, cases 1,500 s and often reopened. Agents should hold up to three messaging sessions, take a call when they hold no case, and keep cases on their capacity until closed. Interruptible Capacity and status-based capacity are enabled (API 65.0 or later).

**The capacity design:**

| Setting | Metadata | Value | Why |
|---|---|---|---|
| Agent primary capacity | `PresenceUserConfig.capacity` | 10 | Budget for primary work |
| Agent interruptible capacity | `PresenceUserConfig.interruptibleCapacity` | 6 | Three messaging sessions at 2 |
| Voice cost | `QueueRoutingConfig.capacityWeight` (Voice_Routing) | 10 | Voice must use the entire capacity weight |
| Case cost | `QueueRoutingConfig.capacityWeight` (Case_Routing) | 5 | Two cases fill primary capacity |
| Messaging cost | `QueueRoutingConfig.capacityWeight` (Messaging_Routing) | 2 | Draws on the interruptible pool |
| Case release rule | `ServiceChannel.capacityModel` (Case_Work) | `STATUS_BASED` | Held until Closed, paused while Waiting on Customer |
| Messaging pool | `ServiceChannel.isInterruptible` (Web_Messaging) | `true` | Consumes interruptible capacity |

UNVERIFIED (2026-10-03): that an agent holding only interruptible messaging work can still be pushed a voice call, and that weights on interruptible work are counted against `interruptibleCapacity` rather than `capacity`, follow from the field descriptions ("consumes interruptible or primary capacity") but the routing behaviour is documented in Salesforce Help only. Pilot with 5 to 10 agents before rollout.

`force-app/main/default/presenceUserConfigs/Blended_Agents.presenceUserConfig-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PresenceUserConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <assignments>
        <profiles>
            <profile>Service Agent</profile>
        </profiles>
    </assignments>
    <capacity>10</capacity>
    <enableAutoAccept>false</enableAutoAccept>
    <enableDecline>true</enableDecline>
    <enableDeclineReason>false</enableDeclineReason>
    <enableDisconnectSound>true</enableDisconnectSound>
    <enableRequestSound>true</enableRequestSound>
    <interruptibleCapacity>6</interruptibleCapacity>
    <label>Blended Agents</label>
    <presenceStatusOnDecline>Away</presenceStatusOnDecline>
    <presenceStatusOnPushTimeout>Away</presenceStatusOnPushTimeout>
</PresenceUserConfig>
```

`force-app/main/default/queueRoutingConfigs/Voice_Routing.queueRoutingConfig-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<QueueRoutingConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <capacityType>NOT INTERRUPTIBLE</capacityType>
    <capacityWeight>10.0</capacityWeight>
    <label>Voice Routing</label>
    <pushTimeout>20</pushTimeout>
    <routingModel>MOST_AVAILABLE</routingModel>
    <routingPriority>0</routingPriority>
</QueueRoutingConfig>
```

`force-app/main/default/queueRoutingConfigs/Messaging_Routing.queueRoutingConfig-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<QueueRoutingConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <capacityType>INHERITED</capacityType>
    <capacityWeight>2.0</capacityWeight>
    <label>Messaging Routing</label>
    <pushTimeout>30</pushTimeout>
    <routingModel>MOST_AVAILABLE</routingModel>
    <routingPriority>1</routingPriority>
</QueueRoutingConfig>
```

`force-app/main/default/serviceChannels/Case_Work.serviceChannel-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ServiceChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <capacityModel>STATUS_BASED</capacityModel>
    <isInterruptible>false</isInterruptible>
    <label>Case Work</label>
    <relatedEntityType>Case</relatedEntityType>
    <secondaryRoutingPriorityField>Priority</secondaryRoutingPriorityField>
    <serviceChannelFieldPriorities>
        <priority>1</priority>
        <value>High</value>
    </serviceChannelFieldPriorities>
    <serviceChannelStatusFieldMappings>
        <type>IN_PROGRESS</type>
        <value>Working</value>
    </serviceChannelStatusFieldMappings>
    <serviceChannelStatusFieldMappings>
        <type>PAUSED</type>
        <value>Waiting on Customer</value>
    </serviceChannelStatusFieldMappings>
    <serviceChannelStatusFieldMappings>
        <type>COMPLETED</type>
        <value>Closed</value>
    </serviceChannelStatusFieldMappings>
    <statusField>Status</statusField>
</ServiceChannel>
```

Element names come from the Metadata API reference for each type; `Case_Routing` and `Web_Messaging` follow the same patterns. UNVERIFIED (2026-10-03): the exact child structure of `serviceChannelStatusFieldMappings` (the reference documents it with the `ServiceChannelFieldPriority` type, whose `priority` is marked required for secondary-priority mappings) and the literal `NOT INTERRUPTIBLE` value with a space as written in the reference. Retrieve one channel and one routing configuration from a sandbox configured in Setup and match their XML before deploying.

**Release manifest** (`manifest/package.xml`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Blended_Agents</members>
        <name>PresenceUserConfig</name>
    </types>
    <types>
        <members>Case_Routing</members>
        <members>Messaging_Routing</members>
        <members>Voice_Routing</members>
        <name>QueueRoutingConfig</name>
    </types>
    <types>
        <members>Case_Work</members>
        <members>Web_Messaging</members>
        <name>ServiceChannel</name>
    </types>
    <version>67.0</version>
</Package>
```

**Verify after deployment.** Confirm live sessions carry the new capacities:

```soql
SELECT UserId, ServicePresenceStatusId, ConfiguredCapacity, ConfiguredInterruptCapacity, StatusStartDate
FROM UserServicePresence
WHERE IsCurrentState = true
```

Then measure two weeks of load per agent:

```soql
SELECT UserId, AVG(AverageCapacity) avgCapacity, SUM(AtCapacityDuration) secondsAtCapacity, SUM(IdleDuration) secondsIdle
FROM UserServicePresence
WHERE StatusStartDate = LAST_N_DAYS:14
GROUP BY UserId
```

Agents with high `AtCapacityDuration` and long queue waits mean capacity is too low or weights too high; high `IdleDuration` with queue waits points at skills or presence statuses, not capacity.

**Why it works:** every number in the design maps to one documented field on one metadata type, the voice weight equals the agent's total as the platform requires, case capacity is held until the status says Closed, and the verification queries read the values the platform actually applied.

