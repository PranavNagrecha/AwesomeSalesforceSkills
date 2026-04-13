---
name: change-data-capture-admin
description: "Use this skill when configuring Change Data Capture in Salesforce Setup: selecting entities, creating or auditing channels, monitoring PlatformEventUsageMetric, managing enrichment on custom channels, and staying within edition delivery limits. NOT for CDC Apex triggers or external subscriber patterns — use integration/change-data-capture-integration for subscriber-side setup."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
triggers:
  - "how do I enable Change Data Capture for an object in Salesforce Setup"
  - "CDC daily delivery limit exceeded or approaching the allocation cap"
  - "configure event enrichment on a custom Change Data Capture channel"
  - "Data Cloud CRM Data Stream is interfering with my CDC channel configuration"
  - "how to monitor Change Data Capture event usage with PlatformEventUsageMetric"
  - "custom PlatformEventChannel not showing selected entities in Setup UI"
tags:
  - change-data-capture
  - cdc
  - entity-selection
  - enrichment
  - platform-events
inputs:
  - List of objects (standard and/or custom) that need CDC enabled
  - Salesforce org Edition (determines daily delivery allocation)
  - Whether the CDC add-on is licensed (removes the 5-entity cap)
  - Whether Data Cloud CRM Data Streams are active in the org
  - Whether enrichment is needed and on which channel type (custom only)
outputs:
  - Entity selection configuration (Setup UI or Metadata API)
  - PlatformEventChannel and PlatformEventChannelMember deployment guidance
  - Enrichment field configuration for multi-entity custom channels
  - PlatformEventUsageMetric query and monitoring plan
  - Edition-specific delivery limit reference and alerting guidance
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Change Data Capture Admin

Use this skill when an admin or architect needs to configure, audit, or monitor the Salesforce-side CDC setup: which entities are tracked, which channels carry those events, how enrichment is configured, and whether delivery allocation is being consumed within edition limits. For subscriber-side concerns (CometD, Pub/Sub API, replay IDs, Apex triggers, gap event handling), use `integration/change-data-capture-integration` instead.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Which edition is the org on?** Daily event delivery allocations are hard limits: 50,000 events/24h (Performance and Unlimited), 25,000 events/24h (Enterprise), 10,000 events/24h (Developer Edition). The CDC add-on shifts billing to a monthly 3M/month model.
- **Is the CDC add-on licensed?** Without the add-on, entity selection is capped at 5 objects (standard + custom combined) across all channels.
- **Is Data Cloud active with CRM Data Streams?** Data Cloud silently adds entity selections to the `DataCloudEntities` channel when a CRM Data Stream is created. Modifying those selections directly via Metadata API or Tooling API can break Data Cloud sync.
- **What channel type is in use?** Setup UI manages only the default `ChangeEvents` channel. Custom `PlatformEventChannel` entities are invisible in Setup — you must query Tooling API to audit them.
- **Is enrichment needed?** Enrichment is only supported on custom multi-entity channels (`PlatformEventChannelMember` records in a custom channel). It is not supported on standard per-object channels such as `/data/AccountChangeEvent`.

---

## Core Concepts

### Entity Selection and the 5-Entity Default Limit

CDC is enabled per object. Without the add-on, a maximum of 5 objects (standard + custom combined, counted across all channels) may be selected. Selecting the same entity on multiple channels counts as one entity toward the limit.

The Setup UI at **Setup > Integrations > Change Data Capture** controls entity selections on the default `ChangeEvents` standard channel only. Custom channel selections made via `PlatformEventChannelMember` are not reflected in the Setup UI. To get a complete picture of all selected entities, query Tooling API:

```soql
SELECT QualifiedApiName, PlatformEventChannelId
FROM PlatformEventChannelMember
```

Standard per-object channels (e.g., `/data/AccountChangeEvent`) are pre-built and do not need channel metadata — enabling the object in Setup is sufficient for subscribers on those channels.

### Channel Types and Their Administrative Scope

Three channel types exist, each with different admin responsibilities:

| Channel Type | Example Path | Admin Configuration | Setup UI? |
|---|---|---|---|
| Default multi-entity | `/data/ChangeEvents` | Enable entities in Setup UI | Yes |
| Standard per-object | `/data/AccountChangeEvent` | Enable entity in Setup UI | Yes |
| Custom channel | `/data/ERP_Sync__chn` | Deploy `PlatformEventChannel` + `PlatformEventChannelMember` via Metadata API | No |

Custom channels require Metadata API or Tooling API to create and manage. Up to 100 custom channels are supported per org. Each subscriber on a custom channel only receives events for entities assigned to that specific channel.

### Event Enrichment

Enrichment allows additional record fields to be included in the CDC event payload beyond those that changed in the triggering DML operation. This lets subscribers avoid follow-up REST API queries to retrieve context fields.

**Critical constraint:** Enrichment is supported only on `PlatformEventChannelMember` records in custom multi-entity channels. It is **not** supported on:
- Standard per-object channels (`/data/AccountChangeEvent`, etc.)
- The default `ChangeEvents` channel

**Formula fields are not supported as enriched fields.** Only stored field values can be included.

Enrichment is configured by adding `EnrichedField` child records to `PlatformEventChannelMember` via Metadata API. There is no Setup UI for enrichment configuration.

### Data Cloud and the DataCloudEntities Channel

When a CRM Data Stream is created in Data Cloud, Salesforce automatically adds the target entity's CDC selection to the `DataCloudEntities` channel. This selection does not appear in the standard CDC Setup page and is not visible through the regular Channel Member query without filtering for the `DataCloudEntities` channel ID.

**Do not modify `DataCloudEntities` channel members directly** via Metadata API or Tooling API. Removing or altering these selections can silently break Data Cloud sync for that CRM Data Stream. CRM Data Stream configuration in Data Cloud is the only supported management path for these selections.

### PlatformEventUsageMetric Monitoring

Salesforce exposes daily CDC delivery consumption through the `PlatformEventUsageMetric` standard object. Query it via SOQL to track actual usage against the edition allocation:

```soql
SELECT Name, Value, StartDate, EndDate
FROM PlatformEventUsageMetric
WHERE Name = 'CDC Event Notifications Delivered'
ORDER BY StartDate DESC
LIMIT 7
```

Delivery allocation is consumed per individual event delivery to each subscribed client. Two subscribers to the same channel each consume the full event count. Monitoring should alert when daily usage reaches 80% of the allocation to allow time for manual intervention before the hard cap is hit.

---

## Common Patterns

### Pattern 1: Standard Entity Selection for a Small Object Set

**When to use:** Fewer than 5 entities need CDC and all consumers use the default or per-object channels.

**How it works:**
1. Go to **Setup > Integrations > Change Data Capture**.
2. Move each target object from the Available list to the Selected Entities list.
3. Save. CDC events start publishing to both `/data/ChangeEvents` and the per-object channel (e.g., `/data/OpportunityChangeEvent`) immediately — no deployment required.
4. Confirm using Tooling API that the `PlatformEventChannelMember` records exist for the default channel.

**Why not Metadata API here:** For the default channel, the Setup UI is faster and requires no deployment. Metadata API is needed only for custom channels or environments where all changes must be version-controlled.

### Pattern 2: Custom Channel with Enrichment

**When to use:** A downstream system needs CDC events enriched with fields that weren't part of the change (e.g., Account Name on Opportunity change events) to avoid follow-up REST queries.

**How it works:**
1. Create a `PlatformEventChannel` metadata record:
   ```xml
   <PlatformEventChannel>
       <channelType>data</channelType>
       <label>ERP Sync</label>
   </PlatformEventChannel>
   ```
2. Create a `PlatformEventChannelMember` for each entity on the channel, including `EnrichedField` children:
   ```xml
   <PlatformEventChannelMember>
       <eventChannel>ERP_Sync__chn</eventChannel>
       <selectedEntity>Opportunity</selectedEntity>
       <enrichedFields>
           <name>AccountId</name>
       </enrichedFields>
       <enrichedFields>
           <name>StageName</name>
       </enrichedFields>
   </PlatformEventChannelMember>
   ```
3. Deploy via `sf project deploy start` or Metadata API.
4. Verify with Tooling API that `EnrichedField` child records exist on the channel member.

**Why not the standard per-object channel:** Standard channels do not support enrichment. Enrichment is only available on custom `PlatformEventChannelMember` records.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Enabling CDC for 1–5 objects, single consumer | Setup UI, default channel | No deployment required; fastest path |
| Enabling CDC for 6+ objects | Purchase CDC add-on first | Without add-on, entity selection fails silently at limit |
| Multiple consumers needing different entity subsets | Custom channels via Metadata API | Server-side isolation; prevents cross-consumer event bleed |
| Subscriber needs context fields not in the change | Custom channel with enrichment | Only supported on custom channel members |
| Entity missing from Setup UI but events are being delivered | Query Tooling API for `PlatformEventChannelMember` | Custom channels and `DataCloudEntities` are invisible in Setup |
| Data Cloud CRM Data Stream is active | Do not touch `DataCloudEntities` channel | Direct modification breaks Data Cloud sync |
| Approaching daily delivery allocation | Monitor `PlatformEventUsageMetric`, consider custom channels with filtering | Custom channels reduce per-subscriber delivery count |

---

## Recommended Workflow

1. **Confirm org edition, add-on status, and Data Cloud activity** — Identify the daily delivery limit (50K/25K/10K). Check whether the CDC add-on is licensed. Determine whether Data Cloud CRM Data Streams are active, as this constrains which channel members can be safely modified.
2. **Inventory current entity selections** — Query Tooling API for all `PlatformEventChannelMember` records to see what is already enabled, including custom channels and `DataCloudEntities`. Do not rely solely on the Setup UI.
3. **Plan channel topology** — Decide whether the default channel is sufficient or whether custom channels are needed (multiple consumers, isolation requirements, or enrichment). Document channel names, entities per channel, and any enriched fields.
4. **Configure entities and channels** — For the default channel: use Setup UI. For custom channels: create `PlatformEventChannel` and `PlatformEventChannelMember` metadata records, add `EnrichedField` children where needed, and deploy via Metadata API.
5. **Validate enrichment constraints** — Confirm that enrichment is only configured on custom multi-entity channels. Confirm no formula fields are listed as enriched fields. Verify via Tooling API that `EnrichedField` records exist on each relevant channel member.
6. **Set up delivery allocation monitoring** — Create a `PlatformEventUsageMetric` query or dashboard to track daily CDC event delivery against the org's limit. Configure alerts at 80% of the daily allocation.
7. **Document configuration in version control** — Commit all `PlatformEventChannel` and `PlatformEventChannelMember` metadata to the project's source control. Note the entities enabled via Setup UI (which are not tracked in metadata by default) in a separate audit document.

---

## Review Checklist

- [ ] Org Edition and daily delivery allocation limit are confirmed
- [ ] CDC add-on licensing status is verified against the entity count
- [ ] All `PlatformEventChannelMember` records (including custom channels) are audited via Tooling API
- [ ] `DataCloudEntities` channel is not manually modified
- [ ] Enrichment is configured only on custom multi-entity channel members (not per-object channels)
- [ ] No formula fields are listed as enriched fields
- [ ] `PlatformEventUsageMetric` monitoring is in place with an alert threshold
- [ ] Custom channel metadata is committed to version control

---

## Salesforce-Specific Gotchas

1. **Data Cloud silently modifies the `DataCloudEntities` channel** — Creating a CRM Data Stream in Data Cloud automatically adds the target entity's CDC selection to the `DataCloudEntities` channel without any visible trace in Setup. Modifying that channel selection directly via Metadata API or Tooling API breaks Data Cloud sync for that stream.

2. **Enrichment is unsupported on standard per-object channels** — Practitioners frequently try to configure enrichment on `/data/AccountChangeEvent` or similar per-object channels. This configuration is not supported; enrichment only works on `PlatformEventChannelMember` records in custom multi-entity channels. The API does not always return a clear error — the enrichment configuration is silently ignored.

3. **Custom channel selections are invisible in Setup UI** — The Change Data Capture Setup page at **Setup > Integrations > Change Data Capture** only reflects the default `ChangeEvents` channel. Entities enabled in custom channels or the `DataCloudEntities` channel do not appear. Auditing coverage using the UI alone will produce an undercount.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Entity selection list | Objects enabled for CDC per channel, including default and custom channels |
| PlatformEventChannel metadata | XML metadata for each custom channel to deploy via Metadata API |
| PlatformEventChannelMember metadata | XML metadata for entity assignments and enriched fields per channel |
| PlatformEventUsageMetric query | SOQL query and monitoring setup for daily delivery allocation tracking |
| Channel audit | Tooling API query output showing all active channel members including Data Cloud |

---

## Related Skills

- `integration/change-data-capture-integration` — Use when configuring the subscriber side: Pub/Sub API, CometD, replay ID management, gap event handling, and external system integration patterns
- `admin/outbound-message-setup` — Use when evaluating CDC vs outbound messaging for near-real-time notifications
- `admin/remote-site-settings` — Required if outbound integrations depend on external endpoint allowlisting alongside CDC consumers
