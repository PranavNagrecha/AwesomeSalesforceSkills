# Examples — Change Data Capture Admin

## Example 1: Enabling CDC for a Custom Object with Enrichment on a Custom Channel

**Scenario:** A warehouse management system needs to receive Salesforce Inventory__c record changes enriched with the Warehouse_Location__c and Product_Name__c fields so it does not have to issue a follow-up REST query per event.

**Problem:** The team initially enables Inventory__c via Setup > Integrations > Change Data Capture and tries to add enriched fields through the UI. The Setup UI provides no enrichment configuration option, and attempting to add enrichment to the default `/data/Inventory__ChangeEvent` per-object channel via Metadata API silently fails — the enrichment records are created but ignored at delivery time.

**Solution:**

Create a dedicated custom channel and configure enrichment through `PlatformEventChannelMember` with `EnrichedField` children:

`PlatformEventChannel` metadata (`WMS_Sync__chn.platformEventChannel`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PlatformEventChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <channelType>data</channelType>
    <label>WMS Sync</label>
</PlatformEventChannel>
```

`PlatformEventChannelMember` metadata (`WMS_Sync__chn-Inventory__c.platformEventChannelMember`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PlatformEventChannelMember xmlns="http://soap.sforce.com/2006/04/metadata">
    <eventChannel>WMS_Sync__chn</eventChannel>
    <selectedEntity>Inventory__c</selectedEntity>
    <enrichedFields>
        <name>Warehouse_Location__c</name>
    </enrichedFields>
    <enrichedFields>
        <name>Product_Name__c</name>
    </enrichedFields>
</PlatformEventChannelMember>
```

Deploy both files:

```bash
sf project deploy start --source-dir force-app/main/default/platformEventChannels
```

Verify via Tooling API that enrichment records exist:

```soql
SELECT Id, Name, PlatformEventChannelMemberId
FROM EnrichedField
WHERE PlatformEventChannelMember.EventChannel.Name = 'WMS_Sync__chn'
```

**Why it works:** Enrichment is only supported on `PlatformEventChannelMember` records in custom multi-entity channels. The subscriber on `/data/WMS_Sync__chn` receives the full Warehouse_Location__c and Product_Name__c values in each event payload, regardless of whether those fields were part of the originating DML change.

---

## Example 2: Auditing CDC Coverage When Data Cloud Is Active

**Scenario:** An org uses both a custom ERP sync CDC channel and Data Cloud CRM Data Streams. A new team member assumes the Setup UI shows all enabled objects and misses entities that Data Cloud added to the `DataCloudEntities` channel. They then try to remove an entity from the `DataCloudEntities` channel via Metadata API to "clean up" what they believe is a duplicate, breaking Data Cloud sync.

**Problem:** The Change Data Capture Setup page only reflects the default `ChangeEvents` channel. Custom channel members and `DataCloudEntities` channel members are invisible in the UI, creating a false audit baseline.

**Solution:**

Perform a full audit using Tooling API before making any channel modifications:

```soql
SELECT QualifiedApiName, PlatformEventChannelId,
       PlatformEventChannel.MasterLabel, PlatformEventChannel.ChannelType
FROM PlatformEventChannelMember
ORDER BY PlatformEventChannel.MasterLabel, QualifiedApiName
```

To isolate Data Cloud-managed selections specifically:

```soql
SELECT QualifiedApiName
FROM PlatformEventChannelMember
WHERE PlatformEventChannel.MasterLabel = 'DataCloudEntities'
```

After running the audit, document which entities appear in each channel. Apply this rule:
- Entities in `DataCloudEntities` — do not modify; manage only through Data Cloud CRM Data Stream configuration.
- Entities in custom channels — manage via Metadata API deployment.
- Entities in the default `ChangeEvents` channel — manage via Setup UI or Metadata API.

**Why it works:** Tooling API provides a complete view across all channel types. Respecting the `DataCloudEntities` channel as Data Cloud-owned prevents silent data sync breakage that has no immediate error but surfaces as stale CRM data in Data Cloud analytics.

---

## Example 3: Monitoring Delivery Allocation Before the Daily Cap Is Reached

**Scenario:** An Enterprise Edition org (25,000 events/24h limit) is approaching its daily CDC delivery limit during peak hours. The team has no monitoring in place and discovers the cap only after subscribers stop receiving events.

**Problem:** CDC event delivery stops silently when the daily allocation is exhausted. Salesforce does not send a proactive alert unless monitoring is configured.

**Solution:**

Query `PlatformEventUsageMetric` daily to track consumption:

```soql
SELECT Name, Value, StartDate, EndDate
FROM PlatformEventUsageMetric
WHERE Name = 'CDC Event Notifications Delivered'
ORDER BY StartDate DESC
LIMIT 7
```

Set up a scheduled Flow or Apex job that runs this query daily and sends an alert when `Value` exceeds 80% of the org's edition allocation (20,000 for Enterprise Edition).

Additionally, consider reducing per-subscriber delivery volume by routing high-volume consumers to a single dedicated custom channel with server-side entity filtering instead of subscribing multiple clients to the default `ChangeEvents` channel.

**Why it works:** `PlatformEventUsageMetric` is the only supported Salesforce-native mechanism for tracking CDC delivery consumption without enabling third-party monitoring tools. Alerting at 80% provides time to investigate and reduce subscriber count or purchase the add-on before delivery halts.

---

## Anti-Pattern: Adding Enrichment to the Default Per-Object Channel

**What practitioners do:** After enabling an object in Setup, they create `EnrichedField` records on the `PlatformEventChannelMember` for `/data/AccountChangeEvent` using Metadata API or Tooling API, expecting the enriched fields to appear in the standard per-object channel's event payload.

**What goes wrong:** Enrichment is silently ignored on standard per-object channels. The metadata deployment succeeds, the `EnrichedField` records persist, but the delivered event payloads do not include the enriched field values. The subscriber receives only changed field values as with a non-enriched subscription, with no error surfaced.

**Correct approach:** Create a custom `PlatformEventChannel`, assign the target entity via `PlatformEventChannelMember`, and configure `EnrichedField` children on that channel member. Route the subscriber to the custom channel path (e.g., `/data/Account_Enriched__chn`) instead of the standard per-object channel.
