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

**Context:** An integration team requests that CDC events for Account records include the Account Owner's Region field (a field on the User object). The admin attempts to add an `EnrichedField` to the `AccountChangeEvent` channel via the Tooling API.

**Problem:** The Tooling API returns an error or the enrichment silently has no effect. Per-object channels (`/data/AccountChangeEvent`) do not support enrichment.

**Solution:**

Create a multi-entity custom channel:

1. Via Tooling API or metadata, create a `PlatformEventChannel`:
```xml
<PlatformEventChannel>
    <channelType>data</channelType>
    <label>Account Enriched Channel</label>
    <masterLabel>Account_Enriched_Channel</masterLabel>
</PlatformEventChannel>
```

2. Create a `PlatformEventChannelMember` linking Account to the custom channel.

3. Create an `EnrichedField` record on the member for `Owner.Region` (the field path through the relationship).

4. Subscribe the integration to the custom channel URL instead of `/data/AccountChangeEvent`.

**Why it works:** Enrichment is only supported on custom multi-entity `PlatformEventChannel` records. Per-object channels are read-only system channels that do not support member or enrichment configuration.

---

## Anti-Pattern: Not Monitoring PlatformEventUsageMetric for CDC-Heavy Orgs

**What practitioners do:** Enable CDC for 15 high-volume Salesforce objects (Opportunity, Lead, Case, Contact, Account, Task, Event, and 8 custom objects) in a production Enterprise org (25,000 event daily limit) without configuring any usage monitoring.

**What goes wrong:** During a high-volume period (month-end close), the org generates 30,000 CDC events in a single day. After the 25,000 limit is reached (around 4 PM), all subsequent CDC events are silently dropped. Downstream integrations receive no notification — they simply stop receiving updates for the remainder of the day. Business teams discover stale data the next morning.

**Correct approach:** Before enabling CDC for multiple high-volume objects, estimate daily event volume (based on historical record modification frequency) and compare against the edition limit. Set up a daily `PlatformEventUsageMetric` report or scheduled Apex job that alerts when CDC usage exceeds 70% of the daily limit. For orgs approaching the edition limit, contact Salesforce to discuss capacity upgrade or reduce the number of CDC-enabled objects to essential ones only.
