# Gotchas — Change Data Capture Admin

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Data Cloud Silently Modifies the DataCloudEntities Channel

**What happens:** When a CRM Data Stream is created in Data Cloud to ingest Salesforce CRM object changes, Salesforce automatically adds a `PlatformEventChannelMember` record to the `DataCloudEntities` channel for the target entity. This modification happens without any visible trace in the Change Data Capture Setup page, and without any admin approval step. If an admin then queries `PlatformEventChannelMember` records and removes or modifies the `DataCloudEntities` channel member via Metadata API or Tooling API — for example, because it looks like an unintended duplicate of a custom channel selection — Data Cloud sync for that CRM Data Stream breaks silently. The Data Cloud pipeline stops receiving updates for that entity, and no error surfaces immediately in either Salesforce or Data Cloud.

**When it occurs:** Any org that has Data Cloud enabled with at least one active CRM Data Stream. The breakage occurs when the `DataCloudEntities` channel members are modified directly outside of Data Cloud, typically during CDC audits or cleanup activities.

**How to avoid:** Always identify which channel members belong to the `DataCloudEntities` channel before any cleanup. Use this Tooling API query first:

```soql
SELECT QualifiedApiName
FROM PlatformEventChannelMember
WHERE PlatformEventChannel.MasterLabel = 'DataCloudEntities'
```

Treat every row in this result as read-only from the admin perspective. CRM Data Stream configuration in Data Cloud is the only supported way to add or remove entities from this channel.

---

## Gotcha 2: Enrichment on Standard Per-Object Channels Is Silently Ignored

**What happens:** Practitioners who know that enrichment requires `PlatformEventChannelMember` configuration sometimes attempt to add `EnrichedField` records to the channel member for a standard per-object channel such as `/data/AccountChangeEvent`. Metadata API accepts the deployment without error. The `EnrichedField` records persist in the org and appear correctly when queried via Tooling API. However, at event delivery time, the enriched fields are not included in the event payload. The subscriber receives only the fields that were part of the originating DML change, identical to a non-enriched subscription. No error or warning is surfaced.

**When it occurs:** Whenever enrichment is configured on a `PlatformEventChannelMember` whose `EventChannel` is a standard per-object channel (those ending in `ChangeEvent`, such as `AccountChangeEvent`, `Contact__ChangeEvent`, etc.) rather than a custom channel created via `PlatformEventChannel` metadata.

**How to avoid:** Enrichment is only supported on `PlatformEventChannelMember` records in custom channels (channel API names ending in `__chn`). Before adding `EnrichedField` records, verify that the target `PlatformEventChannelMember` belongs to a custom `PlatformEventChannel` and not to a standard or default channel. If enrichment is needed on a standard object, create a dedicated custom channel for that object and configure enrichment there. Update the subscriber to connect to the custom channel path.

---

## Gotcha 3: The CDC Setup Page Shows Only the Default ChangeEvents Channel

**What happens:** The Change Data Capture Setup page at **Setup > Integrations > Change Data Capture** displays only entity selections made on the default `ChangeEvents` standard channel. Entities assigned to custom channels (via `PlatformEventChannelMember` with a custom `PlatformEventChannel`) and entities assigned to the `DataCloudEntities` channel do not appear on this page. An admin who audits CDC coverage using only the Setup UI will see an incomplete and potentially misleading picture of which objects have CDC events being generated.

**When it occurs:** Any org with custom channels or Data Cloud CRM Data Streams active. The omission is by platform design, not a bug.

**How to avoid:** Use Tooling API as the authoritative audit source for CDC entity selections:

```soql
SELECT QualifiedApiName, PlatformEventChannelId,
       PlatformEventChannel.MasterLabel, PlatformEventChannel.ChannelType
FROM PlatformEventChannelMember
ORDER BY PlatformEventChannel.MasterLabel, QualifiedApiName
```

Run this query before making any changes to entity selections, and include its output in any CDC configuration documentation. Do not rely on the Setup UI alone for compliance or troubleshooting audits.

---

## Gotcha 4: Edition-Based Delivery Limits Are Per-Subscriber and Hard

**What happens:** The daily CDC event delivery allocation (50,000 for Performance/Unlimited, 25,000 for Enterprise, 10,000 for Developer Edition) is counted per event delivery to each subscribed client, not per unique event published. If two subscribers are connected to the same channel carrying 15,000 events, 30,000 of the org's daily allocation is consumed — not 15,000. When the daily limit is hit, CDC event delivery halts silently for all subscribers. No error is raised in the subscribing application; events simply stop arriving. The limit resets at the start of the next 24-hour window.

**When it occurs:** High-frequency DML activity combined with multiple subscribers on shared channels. Commonly encountered when the same default `ChangeEvents` channel is subscribed to by both a middleware integration and a Data Cloud CRM Data Stream.

**How to avoid:** Monitor `PlatformEventUsageMetric` daily and alert at 80% of the allocation:

```soql
SELECT Name, Value, StartDate, EndDate
FROM PlatformEventUsageMetric
WHERE Name = 'CDC Event Notifications Delivered'
ORDER BY StartDate DESC
LIMIT 7
```

Reduce subscriber count by routing high-volume consumers to dedicated custom channels with entity-level filtering so each subscriber only receives events relevant to its use case. Consider the CDC add-on if the entity count or delivery volume consistently exceeds default limits.
