---
name: data-cloud-data-streams
description: "Step-by-step guidance for configuring Data Cloud data streams: connecting source connectors, mapping Data Lake Objects (DLOs) to Data Model Objects (DMOs), enabling identity resolution rulesets, defining Calculated Insights, and activating unified profiles. Trigger keywords: data stream setup, DLO to DMO mapping, identity resolution ruleset, ingestion API, Calculated Insights SQL. NOT for CRM Analytics datasets, Tableau CRM dataflows, or general Salesforce reporting."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Scalability
triggers:
  - "How do I set up a data stream in Data Cloud to ingest customer records?"
  - "My identity resolution ruleset is greyed out or cannot be created after mapping fields"
  - "What DMOs do I need to map to before I can run identity resolution in Data Cloud?"
  - "How do I create a Calculated Insight to aggregate purchase history for segmentation?"
  - "Data Cloud ingestion API upsert vs append — which do I use and what are the limits?"
  - "How do I activate a unified profile segment to a Marketing Cloud activation target?"
tags:
  - data-cloud
  - data-streams
  - dlo-dmo-mapping
  - identity-resolution
  - calculated-insights
  - ingestion-api
  - activation
inputs:
  - Source system type (Salesforce CRM connector, Ingestion API, MuleSoft, S3, Marketing Cloud, etc.)
  - Fields available in the source that represent individual identity (email, phone, loyalty ID, CRM contact ID)
  - Whether real-time or batch ingestion is required
  - Target activation channel (Marketing Cloud, advertising audience, webhook, etc.)
outputs:
  - Configured data stream with DLO-to-DMO field mappings
  - Identity resolution ruleset referencing Individual and Contact Point DMOs
  - Calculated Insight SQL definition for segmentation metrics
  - Activation target and segment activation configuration
  - Review checklist confirming all required DMO mappings are in place
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# Data Cloud Data Streams

This skill activates when a practitioner needs to ingest external or CRM data into Data Cloud, map that data to the harmonized Data Model Objects required for identity resolution, define Calculated Insights for segmentation, and push unified profiles to activation targets. It covers the full operational pipeline from raw ingestion through unified profile activation.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm which Data Cloud connector type will be used: native Salesforce CRM connector, Ingestion API (REST), MuleSoft Salesforce Connector, cloud storage (S3/GCS), or a partner connector. Each has different field-mapping entry points.
- Identify which source fields represent individual identity: primary email, mobile phone, loyalty program ID, CRM Contact ID. These are the only fields that can anchor identity resolution rulesets.
- Confirm whether deletions are required. The Ingestion API supports only `append` and `upsert` operations. Deletions must be routed through the standard pipeline (not the Ingestion API).
- Check the org-level limit: a maximum of 2 identity resolution rulesets are supported per org. Plan ruleset usage across all data streams before committing to a design.

---

## Core Concepts

### Data Lake Objects (DLOs) and the Ingestion Layer

When a data stream is created, Data Cloud stores incoming records in a Data Lake Object (DLO). The DLO is a raw representation of the source data with no harmonization. Each data stream maps to exactly one DLO, and the DLO schema is inferred from the first batch of records or from an explicit schema upload. DLOs are not queryable for segmentation — they must be mapped to DMOs before any identity or analytics work can occur.

### Data Model Objects (DMOs) and Mandatory Mapping Requirements

Data Cloud's harmonized data model organizes data into semantic object types called Data Model Objects. Two DMO types are mandatory for every customer data stream that should participate in identity resolution:

1. **Individual DMO** — represents a real-world person. The `Individual ID` field is the primary key. At minimum, `First Name` and `Last Name` must be mapped alongside `Individual ID`.
2. **Contact Point DMO** — represents a channel-specific contact address for an individual. The four Contact Point DMO subtypes are: Email, Phone, Address, and App. At least one Contact Point DMO mapping is required. Alternatively, a **Party Identification DMO** mapping (for external IDs like loyalty numbers) can satisfy this requirement.

If a data stream maps only to the Individual DMO but not to any Contact Point or Party Identification DMO, the identity resolution ruleset creation UI will be blocked. This is the single most common configuration error.

### Identity Resolution Rulesets

An identity resolution ruleset defines the matching rules Data Cloud uses to determine that records from different data streams represent the same real-world individual. Rulesets reference the Individual DMO and Contact Point DMO fields. Data Cloud merges matching records into a Unified Individual profile. The org-level limit is **2 rulesets per org** — this is a hard platform limit, not a default. Plan carefully if multiple business units share a single Data Cloud org.

### Calculated Insights vs. Streaming Insights

**Calculated Insights** are SQL-defined batch metrics attached to DMOs. They run on a defined schedule and produce aggregated values (e.g., `total_purchases_last_90_days`, `average_order_value`) that enrich unified profiles for segmentation. Calculated Insights are authored in the Data Cloud UI using a SQL editor and can reference multiple DMOs.

**Streaming Insights** are distinct. They process Web SDK and Mobile SDK event streams in near-real-time and produce point-in-time behavioral signals. Do not conflate the two: Streaming Insights cannot be created from batch DLO data, and Calculated Insights do not run in real time.

---

## Common Patterns

### Pattern 1: CRM-Sourced Customer Profile with Identity Resolution

**When to use:** You have a Salesforce CRM org with Contact records and want to unify them with an external commerce or loyalty system in Data Cloud.

**How it works:**
1. Connect the Salesforce CRM data stream. The CRM connector auto-creates DLOs for Contact, Lead, and Account.
2. In the data stream mapping UI, map Contact fields to the Individual DMO: `ContactId` → `Individual ID`, `FirstName` → `First Name`, `LastName` → `Last Name`.
3. Map `Contact.Email` to the Contact Point Email DMO: `Email` → `Email Address`, `ContactId` → `Individual ID` (the foreign key linking back to Individual).
4. For the external commerce stream (via Ingestion API or S3 connector), map the same fields: `customer_id` → `Individual ID`, `email` → Contact Point Email `Email Address`.
5. Create an identity resolution ruleset using the Contact Point Email DMO as the match key. Data Cloud will merge CRM contacts and commerce customers who share the same email into a single Unified Individual.

**Why not the alternative:** Skipping the Contact Point Email mapping and relying on name matching alone produces far more false-positive merges and cannot create a valid ruleset.

### Pattern 2: Real-Time Behavioral Event Ingestion via Ingestion API

**When to use:** An external system (loyalty app, web backend) needs to push transactional events to Data Cloud in near-real-time for use in segmentation.

**How it works:**
1. Obtain a connected app OAuth token with the `cdp_ingest_api` scope.
2. POST batches of records (up to 200 KB per request) to the Ingestion API endpoint: `POST /api/v1/ingest/sources/{sourceApiName}/{objectName}`.
3. Use `upsert` mode when the source has a stable primary key (e.g., transaction ID). Use `append` for immutable event logs.
4. Map the ingested DLO to the appropriate DMO (e.g., a custom `PurchaseEvent` DMO or the standard `Sales Order` DMO).
5. Note: if records need to be deleted from Data Cloud, the Ingestion API cannot delete them. Deletions must be submitted through the standard pipeline using the Data Cloud bulk delete facility.

**Why not the alternative:** Trying to use the Ingestion API with a delete payload will fail silently or return an error. Teams that build delete logic into their Ingestion API integration waste significant debugging time before discovering this platform constraint.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Source is Salesforce CRM (Contacts, Accounts, Leads) | Native Salesforce CRM Connector | Auto-discovers objects; no schema upload required |
| Source is a custom backend with a REST API | Ingestion API with upsert mode | Lowest latency; supports up to 200 KB per request batch |
| Source is a nightly file export from an ERP | S3 or SFTP connector with scheduled refresh | File-based connectors handle large batch volumes well |
| Need to merge customer records across sources | Identity resolution ruleset on Contact Point Email or Phone | Most reliable match signal; required DMO mappings enforced |
| Need aggregate metrics for segmentation (e.g., total spend) | Calculated Insight with batch SQL | Runs on schedule; enriches Unified Individual for use in segment filters |
| Need real-time behavioral events (web/mobile clicks) | Streaming Insights (Web/Mobile SDK) | Near-real-time; incompatible with batch DLO data |
| Need to delete records from Data Cloud | Standard pipeline bulk delete | Ingestion API does not support delete operations |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Inventory source fields and identity attributes.** Before creating any connector, list all fields in the source system that represent individual identity (email, phone, external loyalty ID). Confirm whether the source has a stable unique key per person that can serve as `Individual ID`. Without this mapping plan, DMO configuration will require rework.

2. **Create the data stream and configure the connector.** In Data Cloud Setup, navigate to Data Streams and click New. Select the connector type. For the Ingestion API, create a connected app first and note the `sourceApiName`. For CRM connectors, authorize the source org. After the connector is established, the DLO is created automatically.

3. **Map the DLO to the Individual DMO.** In the data stream mapping UI, open the Individual object mapping. Map the source primary key field to `Individual ID`. Map first and last name fields. Save. This mapping is required — without it the data contributes nothing to unified profiles.

4. **Map the DLO to at least one Contact Point or Party Identification DMO.** Open the Contact Point Email, Phone, Address, or App mapping (or Party Identification mapping for external IDs). Map the appropriate contact field and the `Individual ID` foreign key. Save. This step is what unlocks identity resolution ruleset creation.

5. **Verify the identity resolution ruleset can be created.** Navigate to Identity Resolution in Data Cloud. If the ruleset creation button is active and both Individual and Contact Point mappings appear in the match rule picklist, the DMO configuration is correct. Create the ruleset using the most reliable identity attribute (email is preferred over phone due to formatting consistency).

6. **Define Calculated Insights for segmentation metrics (if required).** Navigate to Calculated Insights and author SQL selecting from the mapped DMOs. Reference the `Unified Individual` object as the base to ensure insights are tied to merged profiles, not raw source records.

7. **Configure activation.** Create an activation target (Marketing Cloud, advertising audience, or webhook). Build a segment using the Unified Individual DMO and any Calculated Insight fields. Publish the activation. Confirm the segment population count is non-zero before handing off.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every data stream has DLO mapped to the Individual DMO with `Individual ID`, `First Name`, and `Last Name`
- [ ] Every customer data stream also maps to at least one Contact Point DMO or Party Identification DMO
- [ ] Identity resolution ruleset has been created and run at least once; Unified Individual count is non-zero
- [ ] If Calculated Insights are defined, they reference `Unified Individual` (not raw DLO objects) as the base
- [ ] Activation target is configured and segment population count has been confirmed
- [ ] Ingestion API delete requirements reviewed — any delete flows use the standard pipeline, not the Ingestion API
- [ ] Org-level identity resolution ruleset count checked — must remain at or below 2 rulesets total

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Mapping only to Individual DMO blocks ruleset creation** — A data stream that maps its DLO to the Individual DMO but does not also map to a Contact Point or Party Identification DMO will appear fully configured but will prevent identity resolution ruleset creation. The ruleset creation UI gives no helpful error message pointing to this missing mapping.

2. **Ingestion API deletions silently fail** — The Ingestion API accepts only `append` and `upsert` operations. Sending a delete payload returns an error (or in some configurations a silent failure). Teams that build delete pipelines into their Ingestion API integration discover this only after records accumulate incorrectly in Data Cloud.

3. **Two-ruleset org limit is absolute** — The maximum of 2 identity resolution rulesets per org is a hard platform limit, not a configuration default. Multi-BU orgs that each want their own ruleset will hit this limit quickly. Plan ruleset scope to cover all required data streams before committing to a design.

4. **DLO primary key must not be mapped to Party Identification ID** — The `Party Identification ID` field on the Party Identification DMO is an internal Data Cloud system key. Mapping the source record's primary key directly to this field corrupts the DMO and produces incorrect identity resolution results. Instead, use a custom Party Identification `Identification Number` field for the external ID value.

5. **Calculated Insights run in batch, not real-time** — Calculated Insights are not updated incrementally as records flow in. They run on a scheduled cadence. Segments that depend on Calculated Insight values will reflect the state as of the last completed run, not the current ingest state. Use Streaming Insights (Web/Mobile SDK) if near-real-time behavioral signals are required.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Data stream configuration | Connector type, source object, DLO name, refresh schedule |
| DLO-to-DMO field mapping table | Maps each source field to its target DMO and field name |
| Identity resolution ruleset definition | Match rules, identity attributes used, expected Unified Individual count |
| Calculated Insight SQL | SQL definition, referenced DMOs, schedule cadence |
| Activation target configuration | Activation type, segment name, channel-specific field mappings |

---

## Related Skills

- `architect/ai-ready-data-architecture` — Covers identity resolution strategy and cross-source identity attribute planning; use before this skill when the org has multiple data sources with conflicting identity fields
- `data/analytics-dataset-management` — Covers CRM Analytics dataset creation and dataflow management; use instead of this skill when the target is Tableau CRM/CRM Analytics, not Data Cloud
