# Well-Architected Notes — Change Data Capture Admin

## Relevant Pillars

- **Reliability** — Monitoring `PlatformEventUsageMetric` for daily delivery counts prevents silent event dropping when edition limits are reached. The 3-day event retention window for CDC subscribers means missed events can be replayed by reconnecting with a prior `replayId`.
- **Operational Excellence** — Documenting which objects are CDC-enabled and which channels are managed by Data Cloud prevents accidental Metadata API modifications that disrupt Data Cloud data ingestion.

## Architectural Tradeoffs

**Per-object channel vs. multi-entity channel:** Per-object channels are zero-configuration (enabled by entity selection) but require separate subscriber connections per object and do not support enrichment. Multi-entity channels require Tooling API/metadata configuration but provide a single subscriber connection for multiple objects and support enrichment. For integrations consuming events from 5+ objects, multi-entity channels reduce subscriber complexity. For 1-3 objects, per-object channels are simpler.

**CDC vs. Platform Events for change notification:** CDC captures all changes (including changes made via the Salesforce UI, API, triggers) and includes `changedFields` metadata. Platform Events require explicit publishing in Apex or Flow — they do not automatically capture UI changes unless triggered. CDC is preferable for "capture all changes" use cases. Platform Events are preferable for "publish specific business events" use cases.

## Anti-Patterns

1. **Modifying Data Cloud CDC channel members via Metadata API** — Creating, modifying, or deleting `PlatformEventChannelMember` records on the `DataCloudEntities` channel directly disrupts Data Cloud sync silently. Always manage Data Cloud CDC objects through the Data Cloud Admin UI.

2. **Attempting enrichment on per-object channels** — Adding `EnrichedField` records to per-object channels (like `AccountChangeEvent`). Enrichment is only supported on custom multi-entity channels. The configuration will either fail or silently be ignored.

3. **No monitoring of PlatformEventUsageMetric** — Enabling CDC for many high-volume objects without monitoring daily delivery counts. When the edition limit is hit, events are silently dropped — downstream integrations receive a gap in change events with no notification.

## Official Sources Used

- Change Data Capture Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_intro.htm
- PlatformEventUsageMetric — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_platformeventusagemetric.htm
- Enrich Change Events — https://help.salesforce.com/s/articleView?id=sf.cdc_enrich_events.htm&type=5
