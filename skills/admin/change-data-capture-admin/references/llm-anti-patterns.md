# LLM Anti-Patterns — Change Data Capture Admin

Common mistakes AI coding assistants make when advising on CDC admin configuration.

## Anti-Pattern 1: Recommending Enrichment on Per-Object CDC Channels

**What the LLM generates:** "To add the Account Owner's Region to your AccountChangeEvent payload, add an EnrichedField to the AccountChangeEvent PlatformEventChannelMember."

**Why it happens:** The enrichment API (PlatformEventChannelMember + EnrichedField) is documented in the context of CDC. LLMs may not know that it only applies to custom multi-entity channels.

**Correct pattern:**

```
Enrichment is ONLY supported on custom multi-entity PlatformEventChannel records.

Per-object channels (/data/AccountChangeEvent) are system-managed and 
do NOT support enrichment configuration.

For enrichment:
1. Create a custom PlatformEventChannel (channelType=data)
2. Add PlatformEventChannelMember for each object (including Account)
3. Add EnrichedField records on the PlatformEventChannelMember
4. Subscribe to the custom channel URL (not the per-object URL)

Also: Formula fields cannot be enriched fields — only persistent stored fields.
```

**Detection hint:** Any instruction to add enrichment directly to `/data/AccountChangeEvent` or any per-object CDC channel.

---

## Anti-Pattern 2: Modifying Data Cloud CDC Channel Members via Metadata API

**What the LLM generates:** "To change the CDC entity selection, use the Metadata API to modify PlatformEventChannelMember records on the DataCloudEntities channel."

**Why it happens:** Metadata API is the standard way to manage Salesforce configuration. LLMs apply it broadly without knowing the Data Cloud interaction.

**Correct pattern:**

```
NEVER modify PlatformEventChannelMember records on the DataCloudEntities 
channel via Metadata API or Tooling API.

If the org has Data Cloud with CRM Data Streams:
- Data Cloud manages its own CDC entity selections in DataCloudEntities channel
- Modifying these records via API disrupts Data Cloud CRM sync silently
- There is NO error at modification time — the disruption surfaces as stale 
  or missing data in Data Cloud later

Correct approach:
- Manage Data Cloud CDC objects through Data Cloud Admin UI
- Only modify non-DataCloud CDC entity selections via admin Setup UI or Metadata API
```

**Detection hint:** Any recommendation to use Metadata API or Tooling API to modify the `DataCloudEntities` channel members.

---

## Anti-Pattern 3: Not Distinguishing CDC Admin from CDC Apex Subscriber Implementation

**What the LLM generates:** "To use Change Data Capture, enable it in Setup and then write an Apex trigger to process the change events: `trigger AccountChangeEventTrigger on AccountChangeEvent (after insert) {...}`"

**Why it happens:** CDC admin setup and CDC Apex subscriber implementation are often discussed together. LLMs may conflate the two in a single response.

**Correct pattern:**

```
CDC admin configuration (this skill):
- Enable objects in Setup > Integrations > Change Data Capture
- Configure channels and enrichment
- Monitor PlatformEventUsageMetric

CDC subscriber implementation (see change-data-capture-integration skill):
- Apex trigger on *ChangeEvent objects
- CometD subscriber for external systems
- ReplayId management for replay

These are separate concerns. Admins can enable CDC without any Apex code.
External systems subscribe via CometD without Apex triggers.
```

**Detection hint:** Any CDC response that mixes Setup entity selection with Apex trigger code without clearly separating admin vs. developer concerns.

---

## Anti-Pattern 4: Claiming CDC Has Real-Time Unlimited Event Delivery

**What the LLM generates:** "Change Data Capture delivers all record changes to subscribers in real-time with no limits."

**Why it happens:** CDC is marketed as a real-time change notification mechanism. Edition-specific daily delivery limits are a constraint not always highlighted in feature descriptions.

**Correct pattern:**

```
CDC delivery limits by edition (per 24-hour rolling window):
- Performance + Unlimited: 50,000 events
- Enterprise: 25,000 events  
- Developer: 10,000 events

When the limit is reached: events are SILENTLY DROPPED for the remainder 
of the day. No alert, no error, no notification to subscribers.

Monitor: PlatformEventUsageMetric SOQL object
Alert threshold: 70% of edition limit
```

**Detection hint:** Any claim that CDC has no limits or delivers unlimited events.

---

## Anti-Pattern 5: Recommending Formula Fields for CDC Enrichment

**What the LLM generates:** "Enrich your AccountChangeEvent with the Account's Tier__c formula field to include the calculated tier in every change event."

**Why it happens:** Formula fields are commonly used for derived values in Salesforce. LLMs may not know the enrichment field limitation.

**Correct pattern:**

```
Formula fields CANNOT be used as enriched fields in CDC channels.
Only persistent stored field values can be enriched.

If a formula-computed value needs to be in the CDC payload:
Option A: Create a persistent custom field (populated via a trigger or flow)
          and enrich with that field instead of the formula.
Option B: Have the subscriber look up the formula value via a Salesforce API
          callback using the record ID from the change event.
Option C: Re-evaluate whether enrichment is needed or if the subscriber 
          can compute the value locally.
```

**Detection hint:** Any enrichment configuration that specifies a formula field as the enriched field.
