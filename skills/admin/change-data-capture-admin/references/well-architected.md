# Well-Architected Notes — Change Data Capture Admin

## Relevant Pillars

- **Reliability** — Monitoring `PlatformEventUsageMetric` for daily delivery counts prevents silent event dropping when edition limits are reached. The event retention window is 72 hours — a subscription set to `EARLIEST` "sends new events and any other events less than 72 hours old" (Metadata API guide, `ManagedEventSubscription`) — so missed events can be replayed by reconnecting with a prior `replayId` inside that window and not after it. The same passage warns that replaying `EARLIEST` over a large backlog "can slow performance and exhaust the event delivery allocation", which makes replay an incident action with an owner rather than a default reconnect setting.
- **Operational Excellence** — Documenting which objects are CDC-enabled and which channels are managed by Data Cloud prevents accidental Metadata API modifications that disrupt Data Cloud data ingestion.

## Architectural Tradeoffs

**Per-object channel vs. multi-entity channel:** Per-object channels are zero-configuration (enabled by entity selection) but require separate subscriber connections per object and do not support enrichment. Multi-entity channels require Tooling API/metadata configuration but provide a single subscriber connection for multiple objects and support enrichment. For integrations consuming events from 5+ objects, multi-entity channels reduce subscriber complexity. For 1-3 objects, per-object channels are simpler.

**CDC vs. Platform Events for change notification:** CDC captures all changes (including changes made via the Salesforce UI, API, triggers) and includes `changedFields` metadata. Platform Events require explicit publishing in Apex or Flow — they do not automatically capture UI changes unless triggered. CDC is preferable for "capture all changes" use cases. Platform Events are preferable for "publish specific business events" use cases.

## Anti-Patterns

1. **Modifying Data Cloud CDC channel members via Metadata API** — Creating, modifying, or deleting `PlatformEventChannelMember` records on the `DataCloudEntities` channel directly disrupts Data Cloud sync silently. Always manage Data Cloud CDC objects through the Data Cloud Admin UI.

2. **Attempting enrichment on per-object channels** — Adding `EnrichedField` records to per-object channels (like `AccountChangeEvent`). Enrichment is only supported on custom multi-entity channels. The configuration will either fail or silently be ignored.

3. **No monitoring of PlatformEventUsageMetric** — Enabling CDC for many high-volume objects without monitoring daily delivery counts. When the edition limit is hit, events are silently dropped — downstream integrations receive a gap in change events with no notification.

## Official Sources Used

- Metadata API Developer Guide, `PlatformEventChannel` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (channelType `data`/`event` and eventType enums; "you can update only the fullName field and the label field"; "In API version 47.0 and later, you can't deploy or retrieve the ChangeEvents standard channel"; the `channelMembers` removal at 47.0 — Gotchas 4 and 6, and the channel shapes in `references/metadata-examples.md`)
- Metadata API Developer Guide, `PlatformEventChannelMember` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (required `eventChannel` and `selectedEntity`; `enrichedFields` at API 51.0 and `filterExpression` at API 56.0; the `ChannelName_EventName` full-name rule with collapsed double underscores; destructiveChanges as the only deletion path — Gotchas 5 and 7, and the checker's severity rules)
- Metadata API Developer Guide, `ManagedEventSubscription` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf ("events less than 72 hours old" and the warning that subscribing with `EARLIEST` "can slow performance and exhaust the event delivery allocation" — the retention and replay half of Gotcha 10, and the Reliability pillar note)
- Object Reference, `PlatformEventUsageMetric` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (the `Name` restricted picklist values `CHANGE_EVENTS_PUBLISHED` / `CHANGE_EVENTS_DELIVERED`, the `Value` count, hourly UTC `StartDate`/`EndDate`, and the Enhanced Usage Metrics gate on `EventName`/`EventType`/`UsageType` — Gotcha 8 and every monitoring query in this package)
- Object Reference, `EventBusSubscriber` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf ("Doesn't include CometD or Pub/Sub API subscribers"; `Status` values; "for high-volume platform events and change events, the value for Tip isn't available and is always -1" — Gotcha 9 and the subscriber inventory query)
- Object Reference, `StandardObjectNameChangeEvent` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (the change event naming rules, the `ChangeEventHeader` payload example, the list of objects that have associated ChangeEvent objects, and the exclusion of `IsDeleted`, `SystemModStamp` and formula-derived fields from change events — the enrichment grounding in Gotcha 2)
- Apex Reference Guide, `ChangeEventHeader` class — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/apexrefguide.pdf (`changetype` values including the `GAP_` prefix and `GAP_OVERFLOW`; `changedfields`, `recordids`, `transactionkey`, `sequencenumber` — the gap-event half of Gotcha 10)
- Salesforce Developer Limits and Allocations Quick Reference — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf (the CDC Apex trigger batch size of 2,000; and the "Platform Event Allocations" section, which names a "Change Data Capture Allocations" set without printing its values — the basis for every UNVERIFIED marker on a per-edition delivery number in this package)
- Change Data Capture Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_intro.htm
- PlatformEventUsageMetric — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_platformeventusagemetric.htm
- Enrich Change Events — https://help.salesforce.com/s/articleView?id=sf.cdc_enrich_events.htm&type=5
