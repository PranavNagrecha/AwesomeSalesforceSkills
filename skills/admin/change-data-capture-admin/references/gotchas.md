# Gotchas — Change Data Capture Admin

## Gotcha 1: Data Cloud Silently Manages CDC Entity Selections

**What happens:** An admin reviewing CDC entity selection finds objects they did not configure. Alternatively, an admin removes objects from CDC selection and finds that Data Cloud data ingestion for those objects breaks silently — data in Data Cloud becomes stale without any error in Salesforce setup or logs.

**When it occurs:** Any org with active Data Cloud and CRM Data Streams. Data Cloud creates `PlatformEventChannelMember` records for its internal `DataCloudEntities` channel when CRM Data Streams are configured. These appear in the standard CDC Setup UI alongside admin-configured entities.

**How to avoid:** Before modifying any CDC entity selections in an org with Data Cloud active, review which objects have active CRM Data Streams in Data Cloud Admin. Do not remove or modify any `PlatformEventChannelMember` records on the `DataCloudEntities` channel via Metadata API or Tooling API. Manage Data Cloud CDC requirements through the Data Cloud Admin interface. Document which objects are Data Cloud-managed vs. admin-managed.

---

## Gotcha 2: Enrichment Cannot Be Added to Single-Entity Per-Object Channels

**What happens:** An admin or developer attempts to enrich per-object CDC events (e.g., add `Account.Owner.Region` to `/data/AccountChangeEvent` events). The Tooling API returns an error, or the configuration appears to save but enriched fields never appear in the event payload.

**When it occurs:** Any attempt to add `EnrichedField` records to `PlatformEventChannelMember` records on system-generated per-object channels. Per-object channels are managed by the platform and do not support enrichment configuration.

**How to avoid:** For enrichment, create a custom `PlatformEventChannel` (multi-entity channel) via Tooling API or metadata. Add the target objects as `PlatformEventChannelMember` records on this custom channel. Add `EnrichedField` records on the channel member. Subscribe the integration to the custom channel URL. The subscriber will now receive enriched events. Formula fields cannot be enriched fields — only stored persistent fields.

---

## Gotcha 3: CDC Daily Event Limits Are Silently Enforced Without Admin Notification

**What happens:** CDC event delivery silently stops for the remainder of the day once the edition's daily limit is reached. Downstream subscribers continue to be connected but receive no new events. No email, setup alert, or API error notifies the admin that events are being dropped. The gap in change events is discovered later when downstream data is found to be stale.

**When it occurs:** High-volume orgs that enable CDC for many objects or that experience unexpected high-volume periods (month-end, marketing campaigns, large data imports). Enterprise orgs are most at risk with the 25,000 event daily limit.

**How to avoid:** Monitor `PlatformEventUsageMetric` regularly. Create a scheduled Apex job or Salesforce Flow that queries daily CDC usage and sends an alert email when usage exceeds 70% of the edition limit. For high-volume orgs, estimate CDC event volume before enabling objects for CDC (multiply average daily record modifications by the number of enabled objects). If usage consistently approaches the limit, reduce the number of CDC-enabled objects or upgrade to Performance/Unlimited edition for the higher 50,000 event limit.
