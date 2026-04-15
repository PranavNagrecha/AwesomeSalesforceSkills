---
name: data-cloud-segmentation
description: "Use this skill when creating, filtering, refreshing, or activating audience segments in Salesforce Data Cloud. Covers segment types (Standard, Real-Time, Waterfall, Dynamic, Data Kit), segment refresh schedules, activation field mapping, and audience publishing. NOT for Marketing Cloud Contact Builder segments, NPC Actionable Segmentation, or Experience Cloud audience targeting."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
  - Operational Excellence
triggers:
  - "How do I create a segment in Data Cloud and publish it to an activation target?"
  - "Why is my Data Cloud segment not refreshing as frequently as expected?"
  - "What is the difference between Rapid Publish and Standard segment refresh in Data Cloud?"
  - "Activation is missing contacts — how do I debug a Data Cloud segment that excludes too many profiles?"
  - "How do I map segment member attributes to an activation target in Data Cloud?"
  - "What are the limits on Data Cloud segments and activations per org?"
  - "I need to set up a real-time segment in Data Cloud for personalization"
tags:
  - data-cloud
  - segmentation
  - activation
  - audience-publishing
  - segment-refresh
  - real-time-segmentation
inputs:
  - "Data Cloud org with Salesforce CRM connector or ingestion sources configured"
  - "Unified Individual DMO populated via identity resolution"
  - "Named activation target (Salesforce CRM, Marketing Cloud, cloud storage, or custom)"
  - "Business audience definition: filter criteria, recency windows, contact attributes needed"
outputs:
  - "Published segment with configured refresh schedule"
  - "Activation with field mappings from segment to target"
  - "Segment filter logic validated against known hard limits"
  - "Documented refresh strategy (Standard vs. Rapid Publish vs. Incremental)"
dependencies:
  - admin/data-cloud-identity-resolution
  - admin/data-cloud-provisioning
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-15
---

# Data Cloud Segmentation

This skill activates when a practitioner needs to create, configure, publish, or troubleshoot audience segments in Salesforce Data Cloud. It covers the full segment lifecycle: building filter logic against Unified Profiles, choosing the right segment type and refresh schedule, mapping attributes to activation targets, and diagnosing why contacts are missing from downstream systems.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm Data Cloud is provisioned and at least one data stream is ingested and identity-resolved. Segments without a populated Unified Individual DMO return empty populations.
- Know the org's current Rapid Publish segment count. The hard org-wide limit is **20 Rapid Publish segments**. Exceeding it silently prevents creation of new Rapid Publish segments without surfacing an obvious error.
- Identify whether the target activation system (Salesforce CRM, Marketing Cloud Engagement, cloud storage) is already configured as an activation target in Data Cloud setup. Activation cannot proceed without a named target.
- Clarify the segment's population size expectation. Segments with populations over **10 million Unified Profiles** cannot use related attributes in activations.

---

## Core Concepts

### Segment Types

Data Cloud supports five segment types, each with different use cases and constraints:

| Type | Description | Key Constraint |
|---|---|---|
| Standard | Filter-based segment refreshed on a schedule | Default; 12–24 hour refresh cycle |
| Real-Time | Evaluated near-continuously for use in real-time personalization | Requires real-time data stream; higher processing cost |
| Waterfall | Mutually exclusive priority-ordered buckets | Contacts can appear in only one bucket |
| Dynamic | Segment membership driven by changes to a related data object | Useful for event-triggered audiences |
| Data Kit | Segments packaged and distributed via Data Kits | Cross-org distribution pattern |

The org-wide hard limit is **9,950 total segments** across all types.

### Segment Refresh Schedules

Segment refresh and activation delivery are **independently configured**. Refreshing a segment more frequently does not accelerate when activation data lands in the destination system.

Three refresh options exist:

- **Standard refresh** — runs every 12–24 hours; evaluates the full data history for the segment's date range.
- **Rapid Publish** — runs every 1–4 hours but only considers the **last 7 days of data**. Hard org limit: **20 Rapid Publish segments** total. Segments requiring history older than 7 days will silently under-count members if Rapid Publish is selected.
- **Incremental refresh** — evaluates only records that changed since the last run; reduces compute but requires a change-detection-compatible data model.

### Activation and Field Mapping

An activation connects a segment to a named activation target and specifies which attributes to publish alongside the segment membership record. Limits:

- Maximum **20 related attributes** per activation (attributes pulled from objects related to the Unified Individual, not direct profile attributes).
- Maximum **100 activations with related attributes** per org.
- Segments with **10M+ population** cannot include any related attributes; only core identity fields are supported.

Activation has its own refresh schedule that is separate from the segment refresh. A segment that refreshes every 2 hours on Rapid Publish may still deliver to a Marketing Cloud activation only once per day if the activation is configured for daily refresh.

### Null Email Addresses and Contact Completeness

Data Cloud activates segment members regardless of whether the contact has an email address unless the segment filter **explicitly excludes null email**. This is a platform default that frequently causes unexpected deliverability failures in downstream systems. Always add an explicit filter: `Email IS NOT NULL` (or the equivalent on the activation target's required identity field) when the downstream system requires a valid contact identifier.

---

## Common Patterns

### Pattern: Standard Segment with CRM Activation

**When to use:** Sending a daily audience of qualified leads or contacts from Data Cloud back to a Salesforce CRM campaign or list for Sales Cloud follow-up.

**How it works:**
1. In Data Cloud, navigate to Segments and create a new Standard segment.
2. Define filter criteria on the Unified Individual DMO (e.g., `LifetimeValue > 500`, `LastPurchaseDate within 90 days`, `Email IS NOT NULL`).
3. Set refresh schedule to Standard (every 12 hours is sufficient for CRM use cases).
4. Navigate to Activations, create a new activation pointing to the Salesforce CRM activation target.
5. Map the segment to the target CRM object (Contact or Lead), map required fields (Email, FirstName, LastName), and optionally add up to 20 related attributes.
6. Set the activation publish schedule (independent of segment refresh).
7. Publish manually to validate the first run, then confirm records appear in the CRM target list.

**Why not a simpler approach:** Reports and list views in CRM cannot pull cross-cloud data or apply Data Cloud identity resolution. Only activation delivers a refreshed, deduplicated list.

### Pattern: Rapid Publish Segment for Real-Time Personalization

**When to use:** Feeding a segment into a personalization engine (e.g., Marketing Cloud Personalization or a connected CDP activation) where audience membership needs to reflect behavior from the last few hours.

**How it works:**
1. Verify the org has fewer than 20 existing Rapid Publish segments before creating a new one.
2. Create a segment with filter criteria scoped to attributes that change within a 7-day window (e.g., `CartAbandonedDate within 2 days`, `Email IS NOT NULL`).
3. Set refresh to Rapid Publish (1–4 hour cadence).
4. Do not use Rapid Publish for segments that require historical lookback longer than 7 days — lifetime spend, multi-year engagement — because older data is excluded from the evaluation window.
5. Create the activation with a matching high-frequency publish schedule.

**Why not Standard:** Standard refresh runs every 12–24 hours; for cart abandonment or browse behavior, that lag misses the engagement window.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Daily campaign audience for CRM outreach | Standard segment + Standard activation | No need for sub-24h freshness; avoids Rapid Publish quota |
| Cart abandonment or time-sensitive behavior in last 48h | Rapid Publish segment | Refreshes every 1–4 hours; fits 7-day lookback window |
| Need 30-day or longer historical lookback | Standard segment | Rapid Publish only looks back 7 days |
| Org already has 20 Rapid Publish segments | Standard segment with shortest allowed schedule | Cannot exceed 20 Rapid Publish cap |
| Segment population > 10 million profiles | Standard segment, no related attributes on activation | Related attributes not supported above 10M |
| Mutually exclusive VIP / Standard / Lapsed tiers | Waterfall segment | Ensures each profile lands in exactly one bucket |
| Contacts missing from activation with no error | Add Email IS NOT NULL filter, check activation refresh schedule | Null emails pass through; activation has its own schedule |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm prerequisites** — Verify Data Cloud is provisioned, at least one data stream is ingested and identity-resolved, and an activation target is configured. Check the org's current Rapid Publish segment count if planning a high-frequency segment.
2. **Define segment type and filter logic** — Choose the segment type (Standard, Real-Time, Waterfall, Dynamic, Data Kit) based on the audience use case. Build filter criteria against the Unified Individual DMO. Add an explicit `Email IS NOT NULL` filter (or equivalent required identity field) unless the downstream system can handle null identifiers.
3. **Select refresh schedule** — Choose Standard (12–24h) for most use cases. Use Rapid Publish only if the use case requires sub-4-hour freshness AND the data lookback fits within 7 days AND the org has fewer than 20 existing Rapid Publish segments. Use Incremental for large data volumes where change detection is feasible.
4. **Create and configure the activation** — Navigate to Activations, select the segment and activation target, map required identity fields, and add up to 20 related attributes. Set the activation's own publish schedule independently of the segment refresh.
5. **Publish and validate** — Trigger a manual publish on the first run. Confirm member count in the segment preview matches expectations. Confirm records appear in the activation target within the expected delivery window.
6. **Monitor for limit violations** — After publishing, verify segment population count, check activation delivery logs, and confirm Rapid Publish quota is not exceeded at the org level.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Segment filter includes explicit null exclusion on required identity field (Email IS NOT NULL or equivalent)
- [ ] Segment type is appropriate for the use case (Standard for daily; Rapid Publish only for <7-day lookback and org count <20)
- [ ] Activation refresh schedule is explicitly configured and matches the delivery SLA (not assumed to inherit segment schedule)
- [ ] Related attribute count per activation does not exceed 20
- [ ] Segment population is below 10M if related attributes are mapped in the activation
- [ ] Org-wide Rapid Publish count verified before selecting Rapid Publish refresh
- [ ] Org-wide segment count checked against the 9,950 limit for large deployments

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Rapid Publish silently under-counts when data is older than 7 days** — Rapid Publish evaluates only the last 7 days of data regardless of how the segment filter is written. A filter for `LastPurchaseDate within 30 days` will appear to work but will only evaluate events from the past 7 days, silently missing contacts whose last purchase was 8–30 days ago.
2. **Segment refresh schedule and activation publish schedule are independent** — Increasing segment refresh frequency does not change how often the activation delivers data to the downstream system. Both must be configured separately. A Rapid Publish segment paired with a daily activation schedule delivers no faster than once per day.
3. **Null email addresses are activated by default** — Data Cloud includes contacts with null email in segment membership. Unless a filter explicitly excludes nulls, the activation will attempt to send contacts with no email to the downstream system, causing silent failures or malformed records in Marketing Cloud or CRM.
4. **9,950 segment limit is org-wide and hard** — There is no UI warning as the org approaches the limit. At exactly 9,950 segments, creation fails with a generic error. Large orgs with automated segment generation must track count proactively.
5. **Related attribute cap blocks activation setup for large segments** — The 20 related attribute limit per activation and 100 total activations-with-related-attributes limit per org are enforced at save time. For segments over 10M profiles, the activation form will not allow related attribute selection at all.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Published segment | A named Data Cloud segment with filter criteria, population count, and refresh schedule |
| Activation configuration | Mapping of segment to activation target with field mappings and publish schedule |
| Segment filter specification | Documented filter logic including null exclusions and date range constraints |
| Refresh strategy decision record | Rationale for Standard vs. Rapid Publish vs. Incremental choice |

---

## Related Skills

- admin/data-cloud-identity-resolution — identity resolution must be completed before segment population reflects unified profiles; run this skill first
- admin/data-cloud-provisioning — org must be provisioned with Data Cloud before segments can be created
- admin/data-cloud-calculated-insights — calculated insights can be used as filter attributes in segments; use when segment criteria require aggregated metrics
- admin/data-cloud-activation-development — for custom activation targets beyond Salesforce CRM, Marketing Cloud, and native connectors
