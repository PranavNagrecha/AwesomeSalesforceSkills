---
name: change-data-capture-admin
description: "Use when enabling, configuring, or monitoring Change Data Capture (CDC) entity selection, channel enrichment, and delivery usage limits from an admin perspective. NOT for CDC Apex trigger implementation (use change-data-capture-integration)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "How do I enable Change Data Capture for an object in Salesforce?"
  - "CDC entity selection is showing objects I did not configure — why?"
  - "How do I add enrichment to a Change Data Capture channel?"
  - "What is the daily CDC event delivery limit for my Salesforce edition?"
  - "Data Cloud added objects to CDC without my approval — how do I fix this?"
tags:
  - change-data-capture
  - cdc
  - change-data-capture-admin
  - entity-selection
  - channel-enrichment
  - platform-events
inputs:
  - "Salesforce edition (Performance, Unlimited, Enterprise, Developer)"
  - "Objects to enable for CDC (standard and custom)"
  - "Whether Data Cloud CRM data streams are active in the org"
  - "Whether multi-entity channel enrichment is needed"
outputs:
  - "CDC entity selection configuration via Setup > Integrations > Change Data Capture"
  - "PlatformEventUsageMetric monitoring query for daily delivery limits"
  - "Channel enrichment configuration guidance (multi-entity channels only)"
  - "Data Cloud CDC interaction guidance"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# Change Data Capture Admin

This skill activates when an admin needs to configure Change Data Capture (CDC) entity selection, manage custom CDC channels, monitor daily delivery usage against edition limits, and understand the interaction between CDC and Data Cloud CRM data streams. It covers admin-facing CDC setup only — for Apex trigger subscriber implementation, see change-data-capture-integration.

---

## Before Starting

Gather this context before working on anything in this domain:

- **CDC is an admin-configuration feature**: Enabling CDC for an object is done in Setup > Integrations > Change Data Capture by selecting entities. No code is required to enable CDC — the events are published automatically by the platform once enabled.
- **Most critical gotcha**: If the org has Data Cloud active and has created CRM Data Streams, Data Cloud silently adds CDC entity selections to the `DataCloudEntities` channel without admin intervention. Modifying these selections via the Metadata API or Tooling API can cause unintended Data Cloud sync side effects. Always check for Data Cloud CRM data streams before modifying CDC entity selections.
- **Daily delivery limits differ by edition**: Performance and Unlimited editions receive 50,000 CDC events per 24 hours; Enterprise receives 25,000; Developer edition receives 10,000. These limits are monitored via `PlatformEventUsageMetric`.

---

## Core Concepts

### Entity Selection

CDC is enabled per object (entity) in Setup > Integrations > Change Data Capture. When an object is selected, Salesforce begins publishing change events to the `/data/<ObjectName>ChangeEvent` channel for every create, update, delete, and undelete operation on that object.

- Standard objects: Select from the "Standard Objects" list.
- Custom objects: Select from the "Custom Objects" list (both standard and custom CDC channels exist).
- The `ChangeEventHeader` included with every event captures: `changeType` (CREATE, UPDATE, DELETE, UNDELETE), `changedFields` (array of changed field API names for UPDATE events), `commitTimestamp`, `recordIds`, and `commitUser` (the user who made the change).

### Channel Types

Two channel types exist for CDC:

1. **Per-Object Channels** (e.g., `/data/AccountChangeEvent`): Automatically created when an object is enabled for CDC. Subscribe to receive all change events for that object only.
2. **Custom/Multi-Entity Channels**: Manually created channels that aggregate events from multiple objects into a single subscriber channel. Support enrichment (adding fields from related objects to the event payload). Enrichment is ONLY available on multi-entity channels — not on per-object channels.

### Enrichment (Multi-Entity Channels Only)

Enrichment adds additional fields to CDC events beyond what the changed record itself contains. For example, enriching AccountChangeEvent with the related Owner's Region field.

Enrichment configuration:
- Only supported on `PlatformEventChannel` records with `PlatformEventChannelMember` entries linking objects.
- Enriched fields are defined in `EnrichedField` records on the `PlatformEventChannelMember`.
- Formula fields cannot be enriched — only persistent field values.
- Single-entity per-object channels (e.g., `/data/AccountChangeEvent`) do NOT support enrichment.

### Daily Delivery Limits by Edition

| Edition | Daily CDC Events (per 24h rolling window) |
|---|---|
| Performance + Unlimited | 50,000 |
| Enterprise | 25,000 |
| Developer | 10,000 |

Monitor via SOQL:
```soql
SELECT StartDate, EndDate, Value, Name 
FROM PlatformEventUsageMetric 
WHERE Name = 'MonthlyPlatformEvents' 
ORDER BY StartDate DESC 
LIMIT 1
```

Or for CDC-specific usage:
```soql
SELECT EventType, UsageDate, UsageCount 
FROM PlatformEventUsageMetric 
WHERE EventType = 'ChangeDataCapture'
ORDER BY UsageDate DESC 
LIMIT 30
```

### Data Cloud Interaction

If Data Cloud is active in the org and CRM Data Streams have been created, Data Cloud silently adds CDC entity selections to the `DataCloudEntities` internal CDC channel. This channel appears in the entity selection UI as "managed by Data Cloud." Modifying these selections via the Metadata API or Tooling API (e.g., deleting or changing a `PlatformEventChannelMember` record for the `DataCloudEntities` channel) can disrupt Data Cloud's CRM data sync without any warning.

If you need to adjust CDC for objects also used by Data Cloud, manage the entity selection through the Data Cloud Admin UI rather than the standard CDC setup or metadata deployment.

---

## Common Patterns

### Enabling CDC for Standard and Custom Objects

**When to use:** A new integration needs to subscribe to Salesforce object change events for real-time data sync.

**How it works:**
1. Navigate to Setup > Integrations > Change Data Capture.
2. Select standard objects (e.g., Account, Opportunity, Contact) by moving them to the "Selected Entities" list.
3. Select custom objects the same way.
4. Save. CDC is now enabled — events are published immediately for new changes.
5. The integration subscribes to `/data/AccountChangeEvent` (and similar channels) via CometD or Apex triggers.

### Setting Up a Multi-Entity Channel with Enrichment

**When to use:** A single subscriber needs change events from multiple objects in one channel, with additional context fields enriched into the payload.

**How it works:**
1. Create a `PlatformEventChannel` record with ChannelType = `data` (via Tooling API or metadata):
```xml
<PlatformEventChannel>
    <channelType>data</channelType>
    <label>Multi Object Integration Channel</label>
</PlatformEventChannel>
```
2. Add `PlatformEventChannelMember` records linking each object to the channel.
3. Add `EnrichedField` records to the `PlatformEventChannelMember` for fields to include in enrichment.
4. The subscriber connects to the custom channel URL to receive aggregated multi-object events.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Subscribe to changes on a single object | Per-object channel (/data/AccountChangeEvent) | Built-in, no configuration beyond entity selection |
| Subscribe to changes across multiple objects | Multi-entity custom channel | Single connection for multiple objects |
| Need additional context fields in event payload | Multi-entity channel with enrichment | Enrichment only on multi-entity channels |
| Monitor CDC delivery usage | PlatformEventUsageMetric SOQL query | Tracks events against edition limits |
| Data Cloud has CDC selections I did not configure | Check Data Cloud CRM Data Streams — do not modify via Metadata API | Data Cloud manages its own CDC channel |
| Need enrichment on a single-object per-object channel | Not supported — migrate to multi-entity channel | Enrichment cannot be added to per-object channels |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Check for Data Cloud CDC interactions** — Before modifying any CDC entity selections, query the org for active Data Cloud CRM Data Streams. If Data Cloud is active, do not modify the `DataCloudEntities` channel member records directly via Metadata API.
2. **Select entities for CDC** — Navigate to Setup > Integrations > Change Data Capture. Move required objects (standard and custom) to the Selected Entities list. Save.
3. **Confirm entity selection** — Verify the selected objects appear in the Selected Entities list. For each selected object, confirm the per-object channel exists: `/data/<ObjectName>ChangeEvent`.
4. **Configure multi-entity channel (if needed)** — If a single subscriber needs multiple objects or enrichment, create a `PlatformEventChannel` and link objects via `PlatformEventChannelMember` records. Add `EnrichedField` records for any enriched fields.
5. **Monitor daily delivery usage** — Query `PlatformEventUsageMetric` for CDC event counts. Establish a baseline and alert if usage approaches the edition limit.
6. **Test subscriber connectivity** — After enabling CDC, have the integration team confirm the subscriber can connect to the channel and receives test events generated by updating records in the org.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Data Cloud CRM Data Streams checked before modifying CDC entity selections
- [ ] Required objects selected in Setup > Integrations > Change Data Capture
- [ ] Per-object channel confirmed for each enabled object
- [ ] Multi-entity channel and enrichment configured (if required)
- [ ] Enriched fields are persistent (not formula fields)
- [ ] PlatformEventUsageMetric monitoring scheduled
- [ ] Subscriber team confirmed connectivity and event receipt

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Data Cloud silently manages CDC entity selections** — When a CRM Data Stream is created in Data Cloud, Data Cloud automatically adds the relevant Salesforce objects to the `DataCloudEntities` CDC channel without notifying the Salesforce admin. These selections appear in the CDC setup UI but are managed by Data Cloud. Modifying or deleting these `PlatformEventChannelMember` records via Metadata API or Tooling API disrupts Data Cloud's CRM data ingestion without any error message at configuration time — the disruption surfaces later as stale or missing data in Data Cloud.
2. **Enrichment is only supported on multi-entity channels** — Admins frequently attempt to add enrichment to per-object channels (e.g., add Account's Owner.Region field to `/data/AccountChangeEvent`). This is not supported. Enrichment requires a custom `PlatformEventChannel` with `PlatformEventChannelMember` records. Formula fields also cannot be used as enriched fields — only persistent stored fields.
3. **Daily delivery limits are edition-specific and non-negotiable** — If an org's CDC usage exceeds the edition daily limit, events are dropped for the remainder of the 24-hour window with no error surfaced to the admin. Downstream subscribers receive no notification of the gap. Monitor `PlatformEventUsageMetric` proactively to detect trends before hitting the limit.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| CDC entity selection | List of objects enabled for CDC in Setup > Integrations |
| Multi-entity channel configuration | PlatformEventChannel and PlatformEventChannelMember metadata |
| PlatformEventUsageMetric query | SOQL to monitor daily CDC event delivery against edition limits |
| Data Cloud interaction guidance | Steps to check for Data Cloud CDC management before modifying entity selections |

---

## Related Skills

- change-data-capture-integration — Apex trigger and subscriber implementation for CDC events
- integration-admin-connected-apps — Configure connected apps for the subscriber's CometD authentication
