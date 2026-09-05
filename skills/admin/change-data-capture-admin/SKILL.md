---
name: change-data-capture-admin
description: "Use when enabling, configuring, or monitoring Change Data Capture (CDC) entity selection, channel enrichment, and delivery usage limits from an admin perspective. Covers the PlatformEventChannel and PlatformEventChannelMember metadata, the standard ChangeEvents channel, custom __chn data channels, enrichedFields, filterExpression, destructive deselection, and PlatformEventUsageMetric / EventBusSubscriber monitoring. Trigger keywords: change data capture, CDC, entity selection, change event, platform event channel, channel member, enrichment, event delivery allocation. NOT for writing an Apex change-event trigger — use apex/change-data-capture-apex. NOT for subscribing an external system over Pub/Sub or CometD — use integration/change-data-capture-integration."
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
  - "deploy change data capture entity selection from sandbox to production"
  - "PlatformEventChannelMember deploy failed with an invalid channel name"
  - "turn off change data capture for an object without breaking the subscriber"
  - "add a filter expression to a change data capture channel"
  - "query PlatformEventUsageMetric for change event delivery usage"
  - "find out which Apex triggers are subscribed to a change event"
  - "subscriber stopped receiving change events and no error was raised"
tags:
  - change-data-capture
  - cdc
  - change-data-capture-admin
  - entity-selection
  - channel-enrichment
  - platform-events
  - platform-event-channel
  - metadata-api
  - event-monitoring
inputs:
  - "Salesforce edition (Performance, Unlimited, Enterprise, Developer)"
  - "Objects to enable for CDC (standard and custom)"
  - "Whether Data Cloud CRM data streams are active in the org"
  - "Whether multi-entity channel enrichment is needed"
outputs:
  - "CDC entity selection configuration via Setup > Integrations > Change Data Capture"
  - "Deployable PlatformEventChannel and PlatformEventChannelMember metadata, plus the destructiveChanges manifest that turns an entity off"
  - "PlatformEventUsageMetric monitoring query for daily delivery limits"
  - "EventBusSubscriber inventory of in-org trigger and Flow subscribers"
  - "Channel enrichment configuration guidance (multi-entity channels only)"
  - "Data Cloud CDC interaction guidance"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Change Data Capture Admin

This skill activates when an admin needs to configure Change Data Capture (CDC) entity selection, manage custom CDC channels, monitor daily delivery usage against edition limits, and understand the interaction between CDC and Data Cloud CRM data streams. It covers admin-facing CDC setup only — for Apex trigger subscriber implementation, see change-data-capture-integration.

---

## Before Starting

Gather this context before working on anything in this domain:

- **CDC is an admin-configuration feature**: Enabling CDC for an object is done in Setup > Integrations > Change Data Capture by selecting entities. No code is required to enable CDC — the events are published automatically by the platform once enabled.
- **Most critical gotcha**: If the org has Data Cloud active and has created CRM Data Streams, Data Cloud silently adds CDC entity selections to the `DataCloudEntities` channel without admin intervention. Modifying these selections via the Metadata API or Tooling API can cause unintended Data Cloud sync side effects. Always check for Data Cloud CRM data streams before modifying CDC entity selections.
- **Daily delivery limits differ by edition**: Performance and Unlimited editions receive 50,000 CDC events per 24 hours; Enterprise receives 25,000; Developer edition receives 10,000 — UNVERIFIED (2026-09-04): these three figures are not printed in the App Limits cheat sheet, which names a "Change Data Capture Allocations" set and links out instead; read the org's own allocation before designing to a number. The metering itself is real and is monitored via `PlatformEventUsageMetric`.

## Questions to Ask Before Configuring

Ask these before selecting a single entity. Each one maps to a gotcha in `references/gotchas.md`; skipping them produces a selection that deploys cleanly and still leaves a subscriber blind.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which subscriber consumes this, and is it an in-org Apex trigger or Flow, or an external Pub/Sub / CometD client?" | `EventBusSubscriber` sees only the in-org half, so an external consumer is invisible to every inventory query you will run afterwards | The subscriber list, split into what the org can see and what only the integration owners can confirm |
| "Do we need one object or a stream across several?" | One object on the standard `ChangeEvents` channel needs no channel file at all; several with enrichment or filtering needs a custom `__chn` channel | The channel decision, and therefore whether `PlatformEventChannel` is in the package |
| "Which fields must be on every event even when unchanged, and are they stored on the changed record?" | `enrichedFields` adds a field to update and delete events even when it did not change — but change events exclude formula and other derived values | The enriched field list, or the decision that the subscriber looks data up by `recordIds` |
| "Does the subscriber need only a slice of the stream — one region, one record type?" | `filterExpression` (API 56.0+) filters at the channel, so unwanted events never spend delivery allocation | A filter expression, or an explicit decision to filter downstream and pay for the volume |
| "What is this org's actual CDC delivery allocation, read from the org rather than remembered?" | Delivery stops silently at the ceiling and no subscriber is told | A real number to monitor against, and a monitoring owner |
| "What must happen when a `GAP_` event or a >72-hour outage arrives?" | `GAP_CREATE` / `GAP_UPDATE` / `GAP_DELETE` / `GAP_UNDELETE` / `GAP_OVERFLOW` are change types a subscriber must branch on, and the replay window is 72 hours; past that, recovery is reconciliation, not replay | An agreed subscriber behaviour and a reconciliation path |
| "Who turns CDC off for an object, and do they know it is a destructive deploy?" | Removing the member file from source does nothing; the entity keeps publishing and spending allocation | A `destructiveChanges.xml` step in the runbook instead of a git deletion |

What a proper configuration adds over just ticking the boxes in Setup: the selection is deployable source rather than per-sandbox clicking, the channel choice is driven by what the subscriber actually needs, delivery usage is measured against a number read from the org, and turning an entity off is a reviewed destructive deploy instead of a file that quietly disappeared from a branch.

---

## Core Concepts

### Entity Selection

CDC is enabled per object (entity) in Setup > Integrations > Change Data Capture. When an object is selected, Salesforce begins publishing change events to the `/data/<ObjectName>ChangeEvent` channel for every create, update, delete, and undelete operation on that object.

- Standard objects: Select from the "Standard Objects" list.
- Custom objects: Select from the "Custom Objects" list (both standard and custom CDC channels exist).
- The `ChangeEventHeader` included with every event captures: `changeType` (CREATE, UPDATE, DELETE, UNDELETE, plus the `GAP_` variants and `GAP_OVERFLOW`), `changedFields` (array of changed field API names for UPDATE events, including `LastModifiedDate`), `commitTimestamp`, `recordIds`, `entityName`, `transactionKey` (groups every change made in one transaction), `sequenceNumber` (position within that transaction, starting at 1), and `commitUser`.
- Change events do not carry every field: `IsDeleted` and `SystemModStamp` are excluded, as is "any field whose value isn't on the record and is derived from another record or from a formula, except roll-up summary fields, which are included" (Object Reference, Change Event Fields).

### Channel Types

Two channel types exist for CDC:

1. **Per-Object Channels** (e.g., `/data/AccountChangeEvent`): Automatically created when an object is enabled for CDC. Subscribe to receive all change events for that object only.
2. **Custom/Multi-Entity Channels**: Manually created channels (`<Name>__chn`, `channelType` = `data`) that aggregate events from multiple objects into a single subscriber channel. Support enrichment and `filterExpression`. Enrichment is ONLY available on multi-entity channels — not on per-object channels.

### Enrichment (Multi-Entity Channels Only)

Enrichment adds fields to CDC events that would otherwise appear only when they changed: "a non-empty enriched field is added to an update or delete change event even when not changed" (Metadata API guide, `EnrichedField`). For example, carrying `AccountNumber` on every AccountChangeEvent so the subscriber can key on it without a callback.

UNVERIFIED (2026-09-04): enriching with a field on a *related* record (the Owner's Region, say) is not documented — `EnrichedField` has one field, `name`, "the name of a field selected to enrich change events with", with no relationship-path syntax shown, and change events exclude values "derived from another record or from a formula". Design enrichment around fields stored on the changed record.

Enrichment configuration:
- Only supported on `PlatformEventChannel` records with `PlatformEventChannelMember` entries linking objects.
- Enriched fields are defined in `EnrichedField` records on the `PlatformEventChannelMember`.
- Formula fields cannot be enriched — only persistent field values.
- Single-entity per-object channels (e.g., `/data/AccountChangeEvent`) do NOT support enrichment.

### Deployable Shapes

Entity selection is metadata, not a click-only setting — but the two types split the work in a way that surprises people:

| What you want | Component | File |
|---|---|---|
| Turn CDC on for Lead on the standard channel | `PlatformEventChannelMember` only | `platformEventChannelMembers/ChangeEvents_LeadChangeEvent.platformEventChannelMember-meta.xml` |
| A custom stream across several objects | `PlatformEventChannel` (`channelType` = `data`) + one member each | `platformEventChannels/SalesEvents__chn.platformEventChannel-meta.xml` |
| Add a field to every update/delete event | `enrichedFields` inside the member (API 51.0+) | — |
| Deliver only matching events | `filterExpression` inside the member (API 56.0+) | — |
| Turn CDC off for an entity | `destructiveChanges.xml` naming the member | — |

The standard `ChangeEvents` channel has no channel file: "In API version 47.0 and later, you can't deploy or retrieve the `ChangeEvents` standard channel" — only its members. Full deployable XML, package.xml, the `sf` commands, and the full-name underscore rule are in `references/metadata-examples.md`.

### Daily Delivery Limits by Edition

| Edition | Daily CDC Events (per 24h rolling window) |
|---|---|
| Performance + Unlimited | 50,000 |
| Enterprise | 25,000 |
| Developer | 10,000 |

UNVERIFIED (2026-09-04): these three figures are not printed in the App Limits cheat sheet — its "Platform Event Allocations" section names a "Change Data Capture Allocations" set covering "the number custom channels, selected entities in a channel, and event delivery" and links out rather than listing values. Read the org's own allocation before designing to a number. What *is* grounded is the mechanism: delivery is metered, and `PlatformEventUsageMetric` is where you watch it.

Monitor with the fields that exist on `PlatformEventUsageMetric` (API 50.0+). `Name` is a restricted picklist, `Value` is the count, and `StartDate` / `EndDate` are hourly-granular UTC datetimes that scope the query (60-day maximum span):

```soql
SELECT Name, StartDate, EndDate, Value
FROM PlatformEventUsageMetric
WHERE Name IN ('CHANGE_EVENTS_PUBLISHED', 'CHANGE_EVENTS_DELIVERED')
  AND StartDate >= 2026-08-05T00:00:00Z
  AND EndDate <= 2026-09-04T00:00:00Z
ORDER BY StartDate DESC
```

Per-object numbers need `EventName`, which "is available only when Enhanced Usage Metrics is enabled" (API 58.0+) and requires `UsageType` in the `SELECT` or `WHERE`. Without that feature the answer is org-wide totals and nothing finer.

### In-Org Subscriber Inventory

`EventBusSubscriber` "represents a trigger, process, or flow that's subscribed to a platform event or a change data capture event. Doesn't include CometD or Pub/Sub API subscribers." For a change event, `Topic` is the change event name:

```soql
SELECT ExternalId, Name, Type, Status, LastProcessed, LastPublished
FROM EventBusSubscriber
WHERE Topic = 'AccountChangeEvent'
```

`Status` is the operational field — `Running`, `Error` (retries exhausted on `EventBus.RetryableException`), `Suspended`, `Repartitioning`. Do not compute lag from `LastPublished` minus `LastProcessed`: for change events that value is always `-1`.

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
1. Create a `PlatformEventChannel` with `channelType` = `data` (via Tooling API or metadata). `label` is required; `channelType` cannot be changed afterwards:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<PlatformEventChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <channelType>data</channelType>
    <label>Multi Object Integration Channel</label>
</PlatformEventChannel>
```
2. Add one `PlatformEventChannelMember` per object, each with `<eventChannel>MyChannel__chn</eventChannel>` and `<selectedEntity>AccountChangeEvent</selectedEntity>`. The file name collapses double underscores: `MyChannel_chn_AccountChangeEvent`.
3. Add `enrichedFields` entries inside the member for fields to include in enrichment, and `filterExpression` if the subscriber wants only a slice of the stream.
4. The subscriber connects to the custom channel URL to receive aggregated multi-object events, starting a fresh replay position.

Worked, deployable versions of all four steps — including package.xml and the `sf project deploy` commands — are in `references/metadata-examples.md`.

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

1. **Answer the questions above and pick the channel** — one object, no enrichment, no filter means the standard `ChangeEvents` channel and member files only; several objects, enrichment or filtering means a custom `__chn` channel. Record which subscribers are in-org (visible to `EventBusSubscriber`) and which are external (not).
2. **Check for feature-managed selections before touching anything** — retrieve `PlatformEventChannelMember` with a wildcard and identify members no admin created (Data Cloud's `DataCloudEntities` channel is the usual source). Leave those out of your package; `references/gotchas.md` Gotcha 1 explains what deploying over them breaks.
3. **Author the metadata** — copy the shapes from `references/metadata-examples.md`: channel file for custom channels only, one member file per entity, full names with double underscores collapsed, `enrichedFields` and `filterExpression` inside the member.
4. **Lint before you deploy** — `python3 skills/admin/change-data-capture-admin/scripts/check_change_data_capture_admin.py --manifest-dir force-app/main/default`. It errors on a non-`ChangeEvent` entity on a `data` channel and on duplicated enriched fields, warns on a member whose channel is missing from the tree, and flags `filterExpression` below API 56.0.
5. **Validate, then deploy** — `sf project deploy validate --manifest manifest/package.xml`, then deploy. Deploy channel and members in the same package so members never reference a channel that does not exist yet.
6. **Verify with the two queries** — `PlatformEventUsageMetric` for `CHANGE_EVENTS_PUBLISHED` / `CHANGE_EVENTS_DELIVERED`, `EventBusSubscriber` filtered by `Topic` with `Status = 'Running'`. Then have the subscriber team confirm receipt of a test change, including its behaviour on a `GAP_` change type.
7. **Hand over the off switch** — write the `destructiveChanges.xml` for each enabled entity into the runbook now, while the full names are in front of you, and name the owner who watches delivery usage against the org's own allocation.

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
- [ ] Channel and member files deploy together; member full names have double underscores collapsed
- [ ] `scripts/check_change_data_capture_admin.py` run against the source directory with no ERROR or WARN
- [ ] `destructiveChanges.xml` written for every enabled entity and stored with the runbook
- [ ] Subscriber behaviour on `GAP_` change types agreed in writing
- [ ] Delivery allocation read from the org, not quoted from memory, and an owner named for it

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Data Cloud silently manages CDC entity selections** — When a CRM Data Stream is created in Data Cloud, Data Cloud automatically adds the relevant Salesforce objects to the `DataCloudEntities` CDC channel without notifying the Salesforce admin. These selections appear in the CDC setup UI but are managed by Data Cloud. Modifying or deleting these `PlatformEventChannelMember` records via Metadata API or Tooling API disrupts Data Cloud's CRM data ingestion without any error message at configuration time — the disruption surfaces later as stale or missing data in Data Cloud.
2. **Enrichment is only supported on multi-entity channels** — Admins frequently attempt to add enrichment to per-object channels (e.g., add Account's Owner.Region field to `/data/AccountChangeEvent`). This is not supported. Enrichment requires a custom `PlatformEventChannel` with `PlatformEventChannelMember` records. Formula fields also cannot be used as enriched fields — only persistent stored fields.
3. **Daily delivery limits are edition-specific and non-negotiable** — If an org's CDC usage exceeds the edition daily limit, events are dropped for the remainder of the 24-hour window with no error surfaced to the admin. Downstream subscribers receive no notification of the gap. Monitor `PlatformEventUsageMetric` proactively to detect trends before hitting the limit.
4. **The standard channel is deployable only through its members** — there is no `ChangeEvents.platformEventChannel-meta.xml` to retrieve; ship one `PlatformEventChannelMember` per selected entity instead.
5. **Removing a member file from git does not disable CDC** — deselection is a `destructiveChanges.xml` deploy, because `deleteMetadata()` is unsupported for this type.
6. **A member's full name is not channel + entity** — every doubled underscore collapses to one, so `SalesEvents__chn` + `AccountChangeEvent` files as `SalesEvents_chn_AccountChangeEvent`.
7. **The subscriber inventory is half an inventory** — `EventBusSubscriber` lists triggers and Flows only, and its backlog column reads `-1` for change events.

Deeper treatment, with sources, in `references/gotchas.md`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| CDC entity selection | List of objects enabled for CDC in Setup > Integrations |
| Multi-entity channel configuration | PlatformEventChannel and PlatformEventChannelMember metadata |
| PlatformEventUsageMetric query | SOQL to monitor daily CDC event delivery against edition limits |
| Data Cloud interaction guidance | Steps to check for Data Cloud CDC management before modifying entity selections |
| `platformEventChannelMembers/*.platformEventChannelMember-meta.xml` | One deployable file per selected entity, standard or custom channel |
| `platformEventChannels/<Name>__chn.platformEventChannel-meta.xml` | Custom `data` channel definition (custom channels only) |
| `destructiveChanges.xml` | The off switch for each enabled entity, written at enablement time |
| EventBusSubscriber inventory | In-org trigger and Flow subscribers per change event, with `Status` |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You are writing or reviewing the actual XML: channel, members, enrichment, filter, package.xml, retrieve/deploy/destroy commands, and the verification queries |
| `references/gotchas.md` | A deploy failed, an entity will not turn off, a monitoring query will not compile, or a subscriber went quiet with no error |
| `references/examples.md` | You want the worked scenarios end to end — the Data Cloud surprise, the enrichment request that cannot be met as asked, and the unmonitored high-volume org |
| `references/llm-anti-patterns.md` | You are reviewing AI-generated CDC advice, or writing guidance an assistant will read |
| `references/well-architected.md` | You are justifying the channel choice, the CDC-vs-Platform-Events decision, or need the source list behind a claim |
| `templates/change-data-capture-admin-template.md` | You are running the configuration or audit as a piece of work and want the fill-in worksheet |
| `scripts/check_change_data_capture_admin.py` | Before every deploy — run it with `--manifest-dir` over the source directory |

---

## Related Skills

- integration/change-data-capture-integration — the consumer side: Pub/Sub and CometD subscribers, replay IDs, recovery after a gap
- apex/change-data-capture-apex — the in-org subscriber: change event triggers, `EventBus.RetryableException`, tests
- integration/platform-events-integration — custom platform events, which share the event bus and the delivery allocation with CDC
- integration/platform-event-schema-evolution — what happens to subscribers when the underlying object's fields change
- admin/integration-admin-connected-apps — Configure connected apps for the subscriber's CometD authentication
