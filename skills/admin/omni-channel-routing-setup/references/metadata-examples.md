# Metadata Examples — Omni-Channel Routing

Deployable shapes for the six Omni-Channel metadata types, taken from the Metadata API Developer Guide (v62 PDF). All six are available only when Omni-Channel is enabled in the org (API 44.0+; `Skill` 28.0+), and all support the `*` wildcard except where noted.

## Where the files live and the deploy order

| Order | Type | package.xml `<name>` | File | Why this position |
|---|---|---|---|---|
| 1 | Service channel | `ServiceChannel` | `serviceChannels/Case_Channel.serviceChannel-meta.xml` | Presence statuses reference channels |
| 2 | Presence status | `ServicePresenceStatus` | `servicePresenceStatuses/Available_Cases.servicePresenceStatus-meta.xml` | Presence configurations reference statuses |
| 3 | Decline reason | `PresenceDeclineReason` | `presenceDeclineReasons/Incorrect_Queue.presenceDeclineReason-meta.xml` | Referenced by presence configurations |
| 4 | Presence configuration | `PresenceUserConfig` | `presenceUserConfigs/Tier_1_Agents.presenceUserConfig-meta.xml` | Assigns capacity and statuses to users/profiles |
| 5 | Skill (skills-based only) | `Skill` | `skills/Billing.skill-meta.xml` | Referenced by routing configurations and rules |
| 6 | Routing configuration | `QueueRoutingConfig` | `queueRoutingConfigs/Case_Routing_Least_Active.queueRoutingConfig-meta.xml` | Referenced by the queue |
| 7 | Queue | `Queue` | `queues/Tier_1_Support.queue-meta.xml` with `<queueRoutingConfig>` | Ties routing to the pool (`admin/queues-and-public-groups`) |

## 1. Service channel for Case

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ServiceChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Case Channel</label>
    <relatedEntityType>Case</relatedEntityType>
    <capacityModel>STATUS_BASED</capacityModel>
    <hasAutoAcceptEnabled>false</hasAutoAcceptEnabled>
    <doesMinimizeWidgetOnAccept>true</doesMinimizeWidgetOnAccept>
    <secondaryRoutingPriorityField>Priority</secondaryRoutingPriorityField>
</ServiceChannel>
```

- `label` and `relatedEntityType` are required. `relatedEntityType` is the object API name.
- `capacityModel` (65.0+) is `STATUS_BASED` (capacity held until the work is closed or reassigned) or `TAB_BASED` (released when the console tab closes).
- `secondaryRoutingPriorityField` (47.0+) breaks ties inside a routing priority by a field on the work item.
- The After Conversation Work fields (`hasAfterConvoWorkTimer`, `afterConvoMaxTime`, `hasAcwExtensionEnabled`, `acwExtensionDuration`, `maxExtensions`) apply only to Messaging and Voice channels.

## 2. Presence status and 3. decline reason

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ServicePresenceStatus xmlns="http://soap.sforce.com/2006/04/metadata">
    <channels>
        <channel>Case_Channel</channel>
    </channels>
    <label>Available for Cases</label>
</ServicePresenceStatus>
```

A status with no `channels` is treated as Away. `channel` is the service channel's developer name.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PresenceDeclineReason xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Incorrect queue</label>
</PresenceDeclineReason>
```

## 4. Presence configuration: capacity, decline behaviour, and who it applies to

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PresenceUserConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Tier 1 Agents</label>
    <capacity>6</capacity>
    <enableAutoAccept>false</enableAutoAccept>
    <enableDecline>true</enableDecline>
    <enableDeclineReason>true</enableDeclineReason>
    <declineReasons>Incorrect_Queue</declineReasons>
    <presenceStatusOnDecline>Busy</presenceStatusOnDecline>
    <presenceStatusOnPushTimeout>Busy</presenceStatusOnPushTimeout>
    <enableRequestSound>true</enableRequestSound>
    <enableDisconnectSound>true</enableDisconnectSound>
    <assignments>
        <profiles>
            <profile>Support_Agent</profile>
        </profiles>
        <users>
            <user>jane.doe@acme.example</user>
        </users>
    </assignments>
</PresenceUserConfig>
```

- `capacity` is required and is the agent's total work units. A Case whose routing configuration weighs 2 lets this agent hold 3 cases.
- `enableAutoAccept` and `enableDecline` are mutually exclusive; decline options only apply with `enableDecline` = `true`.
- `assignments` is how agents get into Omni-Channel at all. An agent in no presence configuration shows Available and receives nothing (SKILL.md, Presence Statuses).
- `interruptibleCapacity` (57.0+) only applies when the Interruptible Capacity feature is enabled.

## 5. Skill (skills-based routing)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Skill xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Billing</label>
    <description>Invoice, refund and payment questions</description>
    <skillType>Department</skillType>
    <assignments>
        <profiles>
            <profile>Billing_Specialist</profile>
        </profiles>
        <users>
            <user>jane.doe@acme.example</user>
        </users>
    </assignments>
</Skill>
```

Skill **levels**, Service Resources, and the skills-based routing rules that pick skills from work-item fields are records, not metadata; create them after deploy (SKILL.md, Skills-Based Routing). The `Skill` type also serves Chat and Field Service.

## 6. Routing configuration

```xml
<?xml version="1.0" encoding="UTF-8"?>
<QueueRoutingConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Case Routing Least Active</label>
    <routingModel>LEAST_ACTIVE</routingModel>
    <routingPriority>1</routingPriority>
    <capacityWeight>2.0</capacityWeight>
    <capacityType>INHERITED</capacityType>
    <pushTimeout>120</pushTimeout>
    <queueOverflowAssignee>Tier_1_Overflow</queueOverflowAssignee>
    <isAttributeBased>false</isAttributeBased>
</QueueRoutingConfig>
```

- `routingModel` is `LEAST_ACTIVE`, `MOST_AVAILABLE`, or `EXTERNAL_ROUTING`; `routingPriority` is required and lower numbers route first.
- Use `capacityWeight` **or** `capacityPercentage`, not both; Voice must consume the whole capacity.
- `pushTimeout` in seconds; `0` means push timeout is off. Pair it with `presenceStatusOnPushTimeout` on the presence configuration or the timed-out agent keeps receiving work (gotchas #5).
- `queueOverflowAssignee` / `userOverflowAssignee` receive work nobody can take.
- Skills-based: set `isAttributeBased` to `true` and list default skills under `QueueRoutingConfigSkill/skill`; `dropAdditionalSkillsTimeout` relaxes additional skills after N seconds.
- The guide's own sample also shows `pausedCapacityWeight` (64.0+, status-based capacity with Enhanced Omni-Channel only).

## package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types><members>*</members><name>ServiceChannel</name></types>
    <types><members>*</members><name>ServicePresenceStatus</name></types>
    <types><members>*</members><name>PresenceDeclineReason</name></types>
    <types><members>*</members><name>PresenceUserConfig</name></types>
    <types><members>*</members><name>Skill</name></types>
    <types><members>*</members><name>QueueRoutingConfig</name></types>
    <types><members>Tier_1_Support</members><name>Queue</name></types>
    <version>62.0</version>
</Package>
```

Verify after deploy: every case queue has a routing configuration (`SELECT DeveloperName, QueueRoutingConfigId FROM Group WHERE Type = 'Queue'`), and at least one agent in the presence configuration can select a status that includes the Case channel.
