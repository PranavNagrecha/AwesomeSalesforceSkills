# Metadata Examples — Change Data Capture Admin

Deployable shapes for CDC entity selection and channels. Element names, enum values, API-version floors, file suffixes, folder names, and the base skeletons come from the Metadata API Developer Guide (v62 PDF, `PlatformEventChannel` and `PlatformEventChannelMember` sections); the worked example below extends the guide's samples to a realistic two-object channel. Lint the result with:

```bash
python3 skills/admin/change-data-capture-admin/scripts/check_change_data_capture_admin.py --manifest-dir force-app/main/default
```

## Where the files live

| Type | package.xml `<name>` | File in a DX project | API | Wildcard `*`? |
|---|---|---|---|---|
| Custom channel | `PlatformEventChannel` (member = channel full name, e.g. `SalesEvents__chn`) | `platformEventChannels/SalesEvents__chn.platformEventChannel-meta.xml` | 45.0+ | Yes — "To deploy or retrieve all custom channels, specify the wildcard character" |
| Channel member (one selected entity) | `PlatformEventChannelMember` (member = `ChannelName_EventName`) | `platformEventChannelMembers/ChangeEvents_LeadChangeEvent.platformEventChannelMember-meta.xml` | 47.0+ | Yes |
| Enriched field | `enrichedFields` element inside a member — not its own type | — | 51.0+ | — |
| Filter expression | `filterExpression` element inside a member | — | 56.0+ | — |

Both types need the **Customize Application** permission to deploy and retrieve.

## Entity selection on the standard `ChangeEvents` channel

This is what the Setup page (Setup > Integrations > Change Data Capture) writes. It **is** deployable — but only the members are. The guide is explicit: "In API version 47.0 and later, you can't deploy or retrieve the `ChangeEvents` standard channel." There is no `PlatformEventChannel` file for it; you ship one member file per selected object.

`platformEventChannelMembers/ChangeEvents_LeadChangeEvent.platformEventChannelMember-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PlatformEventChannelMember xmlns="http://soap.sforce.com/2006/04/metadata">
    <eventChannel>ChangeEvents</eventChannel>
    <selectedEntity>LeadChangeEvent</selectedEntity>
</PlatformEventChannelMember>
```

`platformEventChannelMembers/ChangeEvents_ContactChangeEvent.platformEventChannelMember-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PlatformEventChannelMember xmlns="http://soap.sforce.com/2006/04/metadata">
    <eventChannel>ChangeEvents</eventChannel>
    <selectedEntity>ContactChangeEvent</selectedEntity>
</PlatformEventChannelMember>
```

One file per selected entity — "If the channel has more than one selected entity, each entity is represented separately by a `PlatformEventChannelMember` component."

## Custom data channel with two members, enrichment and a filter

`platformEventChannels/SalesEvents__chn.platformEventChannel-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PlatformEventChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <channelType>data</channelType>
    <eventType>data</eventType>
    <label>Custom Channel for Sales Events</label>
</PlatformEventChannel>
```

`platformEventChannelMembers/SalesEvents_chn_AccountChangeEvent.platformEventChannelMember-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PlatformEventChannelMember xmlns="http://soap.sforce.com/2006/04/metadata">
    <enrichedFields>
        <name>AccountNumber</name>
    </enrichedFields>
    <enrichedFields>
        <name>Phone</name>
    </enrichedFields>
    <eventChannel>SalesEvents__chn</eventChannel>
    <filterExpression><![CDATA[(BillingCountry='United States')]]></filterExpression>
    <selectedEntity>AccountChangeEvent</selectedEntity>
</PlatformEventChannelMember>
```

`platformEventChannelMembers/SalesEvents_chn_Territory_Plan_ChangeEvent.platformEventChannelMember-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PlatformEventChannelMember xmlns="http://soap.sforce.com/2006/04/metadata">
    <eventChannel>SalesEvents__chn</eventChannel>
    <selectedEntity>Territory_Plan__ChangeEvent</selectedEntity>
</PlatformEventChannelMember>
```

UNVERIFIED (2026-09-04): the Metadata API guide documents `enrichedFields` and `filterExpression` as independent fields of `PlatformEventChannelMember` and shows each in its own sample; it never shows both on one member. The combined member above is a composition of two documented fields, not a copied sample — validate it against a sandbox before relying on it.

### How to read it

- **`channelType` is the channel's kind, and only `data` carries change events.** Valid values are `data` — "Change Data Capture channel corresponding to the selected entities" — and `event`, "a channel that contains platform events." A `data` channel is where `*ChangeEvent` entities go; a custom platform event belongs on an `event` channel.
- **`eventType` is optional and narrows the channel further** (API 61.0+): `data` for change events, `custom` for custom platform events, `monitoring` for Real-Time Event Monitoring events. `data` is valid only with `channelType` = `data`, and "a channel can hold only one type of events."
- **`label` is required and is the only field you can change later.** "You can update only the `fullName` field and the `label` field of a `PlatformEventChannel` component" — `channelType` is fixed at creation, so a channel created as `event` can never be retyped to `data`.
- **`eventChannel` is a name, not a URL.** "For the standard channel, the name is `ChangeEvents`. For a custom channel, the name is in this format: `MyChannel__chn`." `/data/AccountChangeEvent` is a subscription path, never a value for this element.
- **`selectedEntity` is the change-event name, not the object name.** `AccountChangeEvent` for the Account standard object; `MyObject__ChangeEvent` for a custom object `MyObject__c`. Note the doubled underscore before `ChangeEvent` on custom objects.
- **The member's file name follows `ChannelName_EventName`, with double underscores collapsed to one.** The guide's rule: "the member name would be `SalesEvents_chn_AccountChangeEvent` and not `SalesEvents__chn_AccountChangeEvent`" — because "two consecutive underscores in full names designate either a component name suffix or a namespace prefix." Only the *file/full name* collapses; the `<eventChannel>` and `<selectedEntity>` values inside keep their real double underscores, which is why the custom-object member above is filed as `SalesEvents_chn_Territory_Plan_ChangeEvent` while its `selectedEntity` stays `Territory_Plan__ChangeEvent`.
- **Elements are written in alphabetical order** in every sample in the guide (`enrichedFields`, `eventChannel`, `filterExpression`, `selectedEntity`), which is what a `sf project retrieve` returns.
- **`filterExpression` is SOQL-shaped, not SOQL.** "The filter expression format is based on SOQL and supports a subset of SOQL operators and field types." Wrap it in `CDATA` as the guide's sample does — comparison operators would otherwise need XML escaping.
- **`enrichedFields` changes delivery, not just payload.** "A non-empty enriched field is added to an update or delete change event even when not changed" — an enriched field appears on every update event, not only when it was one of the changed fields.

## package.xml

Channel and members in one manifest, so a fresh org gets the channel before the members that reference it:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>SalesEvents__chn</members>
        <name>PlatformEventChannel</name>
    </types>
    <types>
        <members>ChangeEvents_LeadChangeEvent</members>
        <members>ChangeEvents_ContactChangeEvent</members>
        <members>SalesEvents_chn_AccountChangeEvent</members>
        <members>SalesEvents_chn_Territory_Plan_ChangeEvent</members>
        <name>PlatformEventChannelMember</name>
    </types>
    <version>62.0</version>
</Package>
```

The standard channel's members are listed under `PlatformEventChannelMember` like any other; there is no `ChangeEvents` entry under `PlatformEventChannel`. Both types accept `*`, but a wildcard on `PlatformEventChannelMember` also pulls back members that other features (packages, Data Cloud) created — see `references/gotchas.md`.

## Retrieve, deploy, delete

```bash
# Pull the org's current selection and channels into source before editing
sf project retrieve start \
  --metadata "PlatformEventChannel:SalesEvents__chn" \
             "PlatformEventChannelMember:ChangeEvents_LeadChangeEvent" \
  --target-org my-sandbox

# Everything at once (both types wildcarded) — review the diff before committing
sf project retrieve start --metadata "PlatformEventChannel" "PlatformEventChannelMember" --target-org my-sandbox

# Lint, then validate without deploying
python3 skills/admin/change-data-capture-admin/scripts/check_change_data_capture_admin.py --manifest-dir force-app/main/default
sf project deploy validate --manifest manifest/package.xml --target-org my-sandbox

sf project deploy start --manifest manifest/package.xml --target-org my-sandbox
```

Turning CDC **off** for an entity is a destructive change, not an edit: "The `createMetadata()` and `deleteMetadata()` calls aren't supported with the `PlatformEventChannelMember` metadata type. To delete a channel member from a channel, deploy `destructiveChanges.xml` for this type and specify the full name of the member."

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>ChangeEvents_LeadChangeEvent</members>
        <name>PlatformEventChannelMember</name>
    </types>
    <version>62.0</version>
</Package>
```

The standard channel itself cannot be destroyed — "You can't delete the `ChangeEvents` standard channel with `destructiveChanges.xml`, but you can delete channel members." A custom channel can be: deleting it also deletes all of its `PlatformEventChannelMember` components.

## Verification after deploy

**1. Confirm the entity is publishing and being delivered.** `PlatformEventUsageMetric` (Object Reference, API 50.0+) holds "separate usage metrics for platform events and change data capture events". `Name` is a restricted picklist — the two CDC values are `CHANGE_EVENTS_PUBLISHED` and `CHANGE_EVENTS_DELIVERED` — and `Value` is the count:

```soql
SELECT Name, StartDate, EndDate, Value
FROM PlatformEventUsageMetric
WHERE Name IN ('CHANGE_EVENTS_PUBLISHED', 'CHANGE_EVENTS_DELIVERED')
  AND StartDate >= 2026-08-05T00:00:00Z
  AND EndDate <= 2026-09-04T00:00:00Z
ORDER BY StartDate DESC
```

`StartDate` and `EndDate` are required filters, hourly-granular, in UTC. Per-entity numbers need `EventName` (`AccountChangeEvent`), which "is available only when Enhanced Usage Metrics is enabled" (API 58.0+) and requires `UsageType` in the `SELECT` or `WHERE`.

**2. Confirm in-org subscribers attached.** `EventBusSubscriber` "represents a trigger, process, or flow that's subscribed to a platform event or a change data capture event. Doesn't include CometD or Pub/Sub API subscribers." For a change event, `Topic` is the change event name:

```soql
SELECT ExternalId, Name, Type, Status, LastProcessed, LastPublished
FROM EventBusSubscriber
WHERE Topic = 'AccountChangeEvent'
```

`Status` should read `Running`. `Error` means the trigger exceeded its retries on `EventBus.RetryableException` and stopped receiving events; `Suspended` means an admin or an internal error disconnected it. `LastProcessed` and `LastPublished` replace `Position` and `Tip` as of API 66.0.

**3. Setup check.** The selected entities appear in Setup > Integrations > Change Data Capture — the guide describes the standard channel as the one that "corresponds to the entity selection in the Change Data Capture page in Setup". Custom channels do not appear on that page.

## Apex subscriber — excerpt only

A change-event trigger is the developer-side counterpart of this configuration. Ten-line excerpt, adapted from the Apex Developer Guide's `Products__ChangeEvent` sample, purely so the admin can recognise what consumes the entity selection:

```apex
// EXCERPT — see apex/change-data-capture-apex for the full pattern, retries and tests
trigger AccountChangeTrigger on AccountChangeEvent (after insert) {
    for (AccountChangeEvent evt : Trigger.new) {
        EventBus.ChangeEventHeader header = evt.ChangeEventHeader;
        if (header.getChangeType() == 'UPDATE'
                && header.getChangedFields().contains('Phone')) {
            // downstream work keyed on header.getRecordIds()
        }
    }
}
```

Two admin-relevant facts about that trigger: its batch size is **2,000**, not 200 — "The Apex trigger batch size for platform events and Change Data Capture events is 2,000" (App Limits cheat sheet, line 417) — and `changetype` can arrive as `GAP_CREATE`, `GAP_UPDATE`, `GAP_DELETE`, `GAP_UNDELETE` or `GAP_OVERFLOW` (Apex Reference Guide, `ChangeEventHeader`, lines 157299–157304).

## Allocations

The App Limits cheat sheet's "Platform Event Allocations" section (lines 1244–1252) names three allocation sets — "Platform Event Allocations", "Change Data Capture Allocations" ("the number custom channels, selected entities in a channel, and event delivery") and "Pub/Sub API and Event Allocations" — but ships them as pointers, without the numbers.

| Allocation | Value | Source |
|---|---|---|
| Apex trigger batch size for CDC events | 2,000 | App Limits cheat sheet, line 417 (grounded) |
| Event retention window in the event bus | 72 hours | Metadata API guide, `ManagedEventSubscription.defaultReplay` / `errorRecoveryReplay`, lines 86615–86629: `EARLIEST` "sends new events and any other events less than 72 hours old" (grounded) |
| Daily change events delivered, Performance / Unlimited | 50,000 | UNVERIFIED (2026-09-04): not in the App Limits cheat sheet, which links out to the CDC Allocations page instead of listing it. Confirm against the org's own CDC allocation figures before designing to it |
| Daily change events delivered, Enterprise | 25,000 | UNVERIFIED (2026-09-04): same — cheat sheet has the heading, not the number |
| Daily change events delivered, Developer | 10,000 | UNVERIFIED (2026-09-04): same |
| Maximum custom channels per org | — | UNVERIFIED (2026-09-04): the cheat sheet names this allocation ("the number custom channels") but does not print a value in the extracted text |
| Maximum selected entities per channel | — | UNVERIFIED (2026-09-04): named by the cheat sheet, value not printed |

Publish and delivery are counted separately: `PlatformEventUsageMetric.Name` carries both `CHANGE_EVENTS_PUBLISHED` and `CHANGE_EVENTS_DELIVERED`, and the delivered metric counts events "delivered to CometD and Pub/Sub API clients, empApi Lightning components, and event relays". Track both — a delivery figure that outruns the publish figure is the normal shape of a multi-subscriber channel, not a bug. UNVERIFIED (2026-09-04): the docs here do not state the arithmetic relating one publish to N subscriber deliveries; do not model headroom on an assumed multiplier without checking the org's own metrics.
