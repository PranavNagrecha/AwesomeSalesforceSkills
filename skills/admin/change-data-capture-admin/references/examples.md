# Examples — Change Data Capture Admin

## Example 1: Data Cloud Silently Adding CDC Entity Selections

**Context:** A Salesforce admin enables CDC for Account, Contact, and Opportunity objects in Setup > Integrations > Change Data Capture. Three months later, the admin reviews the CDC entity selection and finds six additional objects enabled: Lead, Order, Product2, Pricebook2, and two custom objects. The admin did not configure these.

**Problem:** The org has Data Cloud active with several CRM Data Streams. When Data Cloud processes a CRM Data Stream for an object, it automatically adds that object to its internal `DataCloudEntities` channel by creating `PlatformEventChannelMember` records. These appear in the CDC setup UI but are managed by Data Cloud.

**Solution:**

1. Do NOT deselect these objects from CDC setup without checking Data Cloud first.
2. In Data Cloud Admin (Setup > Data Cloud > Data Streams), review which Salesforce objects have active CRM Data Streams.
3. The objects Data Cloud added to CDC should match the CRM Data Stream sources.
4. If a specific object's CDC is no longer needed by Data Cloud, remove the CRM Data Stream in Data Cloud Admin — this will automatically remove the CDC selection.
5. Never use Metadata API to delete `PlatformEventChannelMember` records for channels named `DataCloudEntities`.

**Why it works:** Data Cloud manages its own CDC requirements. Coordinating CDC changes through Data Cloud Admin ensures the sync pipeline is not disrupted.

---

## Example 2: Enrichment Not Working on Per-Object CDC Channel

**Context:** An integration team requests that CDC events for Account records always carry `AccountNumber`, so the subscriber can key on it without a callback. Today they subscribe to `/data/AccountChangeEvent` and `AccountNumber` only appears when it was one of the changed fields. The admin attempts to add an `EnrichedField` to the `AccountChangeEvent` channel via the Tooling API.

**Problem:** The Tooling API returns an error or the enrichment silently has no effect. Per-object channels (`/data/AccountChangeEvent`) do not support enrichment. Two facts from the Metadata API guide shape the fix: `enrichedFields` is a field of `PlatformEventChannelMember` (API 51.0+), and "a non-empty enriched field is added to an update or delete change event even when not changed" — which is exactly the behaviour the team is asking for, but only on a member of a channel you own.

**Solution:**

Create a custom channel and move the subscriber onto it:

1. Deploy a `PlatformEventChannel` with `channelType` = `data` and a `label`. Those are the only fields it takes — there is no `masterLabel`, and after creation only `fullName` and `label` can be updated.

2. Deploy a `PlatformEventChannelMember` for Account on that channel, with `AccountNumber` as an `enrichedFields` entry. The full deployable pair is in `references/metadata-examples.md`.

3. Repoint the subscriber from `/data/AccountChangeEvent` to the custom channel, and re-baseline its replay position — a new channel starts its own stream.

4. Confirm with `EventBusSubscriber` (`Topic = 'AccountChangeEvent'`, `Status = 'Running'`) that in-org triggers still attach, and with `CHANGE_EVENTS_DELIVERED` that the new channel is delivering.

**Why it works:** Enrichment is only supported on custom multi-entity `PlatformEventChannel` records. Per-object channels are read-only system channels that do not support member or enrichment configuration.

**What the team asked for that cannot be done:** the original request was for the Account *Owner's* Region — a field on User, reached through a relationship. `EnrichedField` documents one field, `name`, described as "the name of a field selected to enrich change events with"; no relationship path syntax is documented. Change events also exclude "any field whose value isn't on the record and is derived from another record or from a formula, except roll-up summary fields" (Object Reference, Change Event Fields). UNVERIFIED (2026-09-04): the guides do not state outright that a cross-object path is rejected in `enrichedFields`; they only never show one. Design for a field stored on the changed record, and have the subscriber look up related data by `recordIds`.

---

## Anti-Pattern: Not Monitoring PlatformEventUsageMetric for CDC-Heavy Orgs

**What practitioners do:** Enable CDC for 15 high-volume Salesforce objects (Opportunity, Lead, Case, Contact, Account, Task, Event, and 8 custom objects) in a production Enterprise org (25,000 event daily limit) without configuring any usage monitoring.

**What goes wrong:** During a high-volume period (month-end close), the org generates 30,000 CDC events in a single day. After the 25,000 limit is reached (around 4 PM), all subsequent CDC events are silently dropped. Downstream integrations receive no notification — they simply stop receiving updates for the remainder of the day. Business teams discover stale data the next morning.

**Correct approach:** Before enabling CDC for multiple high-volume objects, estimate daily event volume (based on historical record modification frequency) and compare against the edition limit. Set up a daily `PlatformEventUsageMetric` report or scheduled Apex job that alerts when CDC usage exceeds 70% of the daily limit. For orgs approaching the edition limit, contact Salesforce to discuss capacity upgrade or reduce the number of CDC-enabled objects to essential ones only.

**The monitoring the org should have had:** two always-available metrics, sampled daily, plotted against the org's own published allocation.

```soql
-- Daily CDC publish vs delivery for the last 30 days.
-- Name is a restricted picklist; Value is the count; StartDate/EndDate are
-- hourly-granular UTC and are how the range is scoped (60-day maximum span).
SELECT Name, StartDate, EndDate, Value
FROM PlatformEventUsageMetric
WHERE Name IN ('CHANGE_EVENTS_PUBLISHED', 'CHANGE_EVENTS_DELIVERED')
  AND StartDate >= 2026-08-05T00:00:00Z
  AND EndDate   <= 2026-09-04T00:00:00Z
ORDER BY StartDate DESC
```

Turn the two series into a standing record, reviewed at each release checkpoint:

| Sample date (UTC) | `CHANGE_EVENTS_PUBLISHED` | `CHANGE_EVENTS_DELIVERED` | Org allocation | % of allocation | Action |
|---|---|---|---|---|---|
| 2026-08-31 | 9,140 | 18,280 | (read from the org) | | baseline |
| 2026-09-01 | 22,600 | 45,200 | (read from the org) | | month-end spike — review |
| 2026-09-02 | 9,880 | 19,760 | (read from the org) | | back to baseline |

Fill the allocation column from the org's own CDC Allocations figures, not from a remembered number — the App Limits cheat sheet names the "Change Data Capture Allocations" set (lines 1244–1252) without printing its values, so any per-edition figure quoted from memory is unverified. Publish and delivery are separate metrics, and the delivery allocation is the one named after deliveries — so watch the delivered series, and treat a delivered figure well above the published figure as a sign that several subscribers are consuming the same stream rather than as a data error.

If the org has Enhanced Usage Metrics enabled (API 58.0+), the same shape narrows to one entity — and only then:

```soql
SELECT EventName, UsageType, TimeSegment, StartDate, Value
FROM PlatformEventUsageMetric
WHERE EventName = 'OpportunityChangeEvent'
  AND UsageType = 'DELIVERY'
  AND StartDate >= 2026-09-01T00:00:00Z
  AND EndDate   <= 2026-09-04T00:00:00Z
ORDER BY StartDate DESC
```

Without Enhanced Usage Metrics those fields do not exist on the object, and the query fails rather than returning zero rows — which is the honest signal that per-object CDC reporting is not available in this org yet.
