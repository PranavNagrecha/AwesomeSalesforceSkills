---
name: data-cloud-data-model-objects
description: "Use when designing or managing Data Model Objects (DMOs) in Salesforce Data Cloud — covers DMO schema design, subject area governance, data relationships between DMOs, XMD (extended metadata) layer management, data transforms (streaming vs. batch), and mandatory DMO requirements for identity resolution. NOT for standard Salesforce CRM object design, Data Cloud data stream configuration, or SOQL queries against Data Cloud objects."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "How do I design custom Data Model Objects in Data Cloud for my data schema?"
  - "What DMOs are required for identity resolution to work in Data Cloud?"
  - "How to update XMD field labels and formatting in Data Cloud datasets"
  - "Data Cloud DMO relationship limit — only one relationship per field pair allowed"
  - "Difference between streaming transforms and batch transforms in Data Cloud DMOs"
  - "How do I harmonize my data into the Customer 360 Data Model in Data Cloud / Data 360?"
  - "What is the harmonization (Transform and Model) stage of the Data Cloud lifecycle?"
  - "Which batch data transform node type writes the result to a DMO?"
  - "How do I build a batch data transform pipeline to populate a Data Cloud DMO?"
tags:
  - data-cloud
  - DMO
  - XMD
  - data-model
  - identity-resolution
  - data-transforms
  - harmonization
inputs:
  - "Source data schema: entities, fields, data types, and relationships"
  - "Identity resolution scope: which DMOs need to feed matching rules"
  - "Subject area taxonomy: how entities should be organized in the Customer 360 Data Model"
outputs:
  - "DMO schema design with subject area assignments and field definitions"
  - "Mandatory DMO checklist for identity resolution"
  - "Data transform type selection (streaming vs. batch) per use case"
  - "XMD update API specification for field formatting customization"
dependencies: []
version: 1.2.0
author: Pranav Nagrecha
updated: 2026-07-07
---

# Data Cloud Data Model Objects

This skill activates when a practitioner needs to design or manage Data Model Objects (DMOs) in Salesforce Data Cloud. DMOs are the semantic layer of the Customer 360 Data Model — they are logical groupings of data stored in Data Lake Objects (DLOs) and organized into subject areas. This skill covers DMO schema design, mandatory DMOs for identity resolution, the XMD (extended metadata) layer for field formatting, and the data transform types that can create or populate DMOs.

---

## Before Starting

Gather this context before working on anything in this domain:

- DMOs do NOT support SOQL. Queries against DMO data require the Data Cloud Query API (ANSI SQL), not standard Salesforce SOQL. Attempting to query a DMO via SOQL will fail.
- Five DMOs are mandatory for identity resolution: Individual, Party Identification, Contact Point Email, Contact Point Phone, and Contact Point Address. Data streams that do not map to these DMOs cannot participate in identity resolution.
- Only one data relationship is permitted per field pair between two mapped DMOs. Multiple relationships between the same two fields are not supported.
- XMD (extended metadata) has three tiers: System XMD (platform-generated, immutable), Main XMD (org-customizable via REST API), and User XMD (per-user preferences). You can only modify Main XMD, not System XMD.
- Streaming transforms are restricted to a single DLO (no cross-DLO joins); batch transforms support joins and aggregations across multiple DLOs.

---

## Core Concepts

### Where This Sits: The "Harmonize" Stage

Mapping DLO fields onto DMOs is what Salesforce officially calls **harmonization**. The Data Cloud (now branded **Data 360**) lifecycle runs: **Connect and Ingest → Transform and Model → Unify and Enhance → Analyze and Act**. Harmonization is the *Transform and Model* stage — Salesforce describes it as "harmonize data from those different sources into a standard data model—the Customer 360 Data Model." At the product level, Data 360 lets you ingest, harmonize, unify, and analyze streaming and batch data, so "harmonize your data" and "harmonization stage" are the vocabulary a practitioner will bring to exactly the DMO-mapping work this skill covers.

Operationally, harmonizing is the DLO → DMO field mapping described below: "Data mapping is the process of connecting fields in your DLOs to the standardized fields within the Customer 360 Data Model DMOs." The point of harmonizing to a shared model is downstream interoperability — "This model harmonizes disparate data sources, allowing you to draw insights and unify, segment, and activate your data." Harmonization happens *before* identity resolution: key attributes like names, IDs, email addresses, and phone numbers are mapped during harmonization precisely because they are what identity resolution later uses to link an individual's data into a unified profile (see the five mandatory DMOs below).

**Do not confuse this with the Harmonization Center.** That is a separate, similarly-named feature that lives in Marketing Cloud Intelligence (formerly Datorama), not in Data Cloud / Data 360. The Harmonization Center manages naming-convention patterns, classification rules, and harmonized dimensions for marketing analytics data — it has nothing to do with DLO-to-DMO field mapping. If a request references the "Harmonization Center," it is a different product and outside this skill's scope.

### DMO Architecture: DLO → DMO Layer

Data Cloud stores raw ingested data in Data Lake Objects (DLOs). DMOs are a semantic abstraction layer on top of DLOs:

- **DLO** — Raw storage: one DLO per data stream source. Fields are ingested as-is.
- **DMO** — Semantic model: curated schema with business-friendly names, relationships, and subject area classification. Multiple DLOs can map to a single DMO.
- **Subject Areas** — Organizational groups within the Customer 360 Data Model (e.g., Sales Order, Unified Individual, Marketing). DMOs belong to a subject area.

Field mapping from DLO to DMO is configured in the Data Stream setup. This mapping determines which DLO fields populate which DMO fields. Salesforce frames this as "DMOs are created by mapping DLOs into standardized groupings" that then "provide physical or virtual views of the underlying data." The target schema is the canonical **Customer 360 Data Model** — "the standard data model used by Data 360 to aid in data modeling and extensibility across platforms."

**Standard connectors can pre-wire the mapping.** When you ingest through a standard connector, a *data bundle* automates part of this work: "after a data stream is deployed, the data bundle automatically maps source objects from the source to a DMO in Data 360." You can then add or customize those mappings to fit the business. For source objects that have no standard DMO equivalent, you still do the mapping by hand — see Pattern 1.

When harmonizing DLO fields that carry primary or foreign keys, configure key qualifiers (fully qualified keys). Salesforce notes this lets Data 360 "accurately interpret data ingested from different sources, ensuring each record has a unique identifier and preventing misinterpretation during queries, segmentation, or calculated insights." Unqualified keys can collide across sources once harmonized into a shared DMO.

### Five Mandatory DMOs for Identity Resolution

Identity resolution in Data Cloud requires data to be mapped to specific standard DMOs:

| DMO | Purpose |
|---|---|
| `Individual` | Unified customer/person record |
| `Party Identification` | External IDs linking a person to source systems |
| `Contact Point Email` | Email addresses linked to Individual |
| `Contact Point Phone` | Phone numbers linked to Individual |
| `Contact Point Address` | Physical addresses linked to Individual |

Data streams that omit field mappings to these DMOs cannot contribute to unified identity profiles. The identity resolution ruleset operates exclusively on these five DMOs.

### XMD: Extended Metadata Layer

XMD controls how Data Cloud fields are displayed: labels, formatting, data type hints, and measure/dimension classification. It has three immutable tiers:

- **System XMD** — Automatically generated by the platform when a dataset or DMO is created. Cannot be modified.
- **Main XMD** — Org-level customization. Can be updated via `PATCH /services/data/v{version}/wave/datasets/{datasetId}/xmds/main`. This is the correct layer for adding field labels, aliases, and formatting properties.
- **User XMD** — Per-user preferences applied on top of Main XMD. Cannot be updated via API; managed by end users in the interface.

Attempting to update System XMD fields via the REST API returns an error. Identify the XMD type before attempting to modify it.

### Streaming vs. Batch Transforms

Data transforms are the "data prep and transformations" mechanism the Data 360 lifecycle uses to prepare and clean data before it is modeled and unified — the same work this skill frames as the *Transform and Model* stage. Two transform types create or populate DMO records from DLO data:

**Streaming Transforms:**
- Execute near-real-time on new DLO records as they arrive — Salesforce describes them as cleaning and enriching data "in near real-time, as it enters the system"
- Support only a single source DLO per transform (no joins)
- Cannot perform aggregations
- Use for event enrichment that does not require cross-source joins

**Batch Transforms:**
- Execute on a scheduled interval — use them "to modify select amounts of data on a scheduled time interval"
- Support joins across multiple DLOs and aggregations
- Offer more functionality than streaming transforms
- Use for analytical metrics, cross-source unified views, or enrichment requiring multiple data sources
- Can also be launched from Flow via the **Run Batch Data Transform** action, so a batch transform can be triggered as part of an orchestrated automation rather than only on its own schedule

**Batch transform node types (visual editor):** Batch transforms are built in a drag-and-drop visual editor — "you drag and drop nodes to create the data you need." The available node types are:

| Node | Purpose |
|---|---|
| `Input` | Source data — reads from a DLO **or** a DMO |
| `Output` | Writes the transformed result to a DLO **or** a DMO |
| `Aggregate` | Rolls data up to a higher granularity (sum, count, average) |
| `AI Functions` | Enriches records using predictive models |
| `Append` | Combines rows from multiple sets of data |
| `Filter` | Removes unnecessary rows from a dataset |
| `Join` | Merges two data branches on matching key fields |
| `Transform` | Calculations, string manipulation, and data formatting |
| `Update` | Replaces values when key pairs align across sources |

Because the `Output` node targets a DLO or a DMO directly, a batch transform is one of the supported paths for populating a DMO — the transformed result can land straight in the modeled layer. Streaming transforms, by contrast, cannot join or aggregate, so any DMO population requiring cross-source logic must go through a batch transform.

---

## Common Patterns

### Pattern 1: Custom DMO Schema Design

**When to use:** Onboarding a new data source that doesn't map to any existing standard DMO — e.g., a custom loyalty transaction object.

**How it works:**
1. Define the DMO name, API name, and subject area assignment
2. Identify the source DLO(s) and define field mappings (source field → DMO field)
3. Determine if the DMO needs a relationship to another DMO (e.g., linking loyalty transactions to the Individual DMO)
4. Create only one data relationship per field pair — multiple relationships between the same two DMO fields are not allowed
5. Map identity-relevant fields (email, phone, address) to the five mandatory DMOs in a separate data stream if they exist in the source

**Why not use SOQL to query the DMO:** DMOs are columnar stores, not Salesforce objects. SOQL does not work against DMO data. Use the Data Cloud Query API with ANSI SQL to query DMO records.

### Pattern 2: Main XMD Update for Field Label Customization

**When to use:** Field labels in a Data Cloud dataset or DMO need to be renamed for business-friendly display without modifying the underlying field API name.

**How it works:**
1. Retrieve the current Main XMD: `GET /services/data/v{version}/wave/datasets/{datasetId}/xmds/main`
2. Modify the `fields` array in the XMD JSON: update `label`, `alias`, or formatting properties for the target field
3. Submit the updated XMD: `PATCH /services/data/v{version}/wave/datasets/{datasetId}/xmds/main`
4. Validate the change by querying the dataset in CRM Analytics or Data Cloud interface

**Why not edit System XMD:** System XMD is platform-generated and immutable. PATCH requests targeting System XMD return a 403 error. Always work with Main XMD.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New data source, identity-relevant fields | Map to mandatory identity DMOs (Individual, Party ID, Contact Points) | Required for identity resolution participation |
| Cross-source data join for analytics | Batch Transform | Streaming transforms support only single DLO; joins require batch |
| Populate a DMO from transformed multi-source data | Batch Transform with an `Output` node targeting the DMO | `Output` writes to a DLO or DMO; batch supports the joins/aggregations streaming cannot |
| Near-real-time enrichment, single source | Streaming Transform | Faster execution; no join needed |
| Trigger a batch transform from an automation | Flow **Run Batch Data Transform** action | Runs a batch transform on demand inside an orchestration instead of only on schedule |
| Field label/format customization | PATCH Main XMD via REST API | Only Main XMD is modifiable; System XMD is immutable |
| Querying DMO data | Data Cloud Query API (ANSI SQL) | SOQL does not work against DMO objects |
| Relationship between two DMOs | One relationship per field pair maximum | Platform limit: multiple relationships on same field pair not supported |

---

## Recommended Workflow

1. **Inventory source data schema** — Document all entities, fields, data types, and relationships in the source system.
2. **Map to Customer 360 Data Model subject areas** — Identify which standard DMOs the source data fits. Create custom DMOs only for entities with no standard DMO equivalent.
3. **Design mandatory DMO mappings for identity resolution** — Confirm that identity-relevant fields (email, phone, address, external IDs) are mapped to the five mandatory DMOs.
4. **Define data relationships** — Document which DMOs need relationships. Enforce the one-relationship-per-field-pair limit during design.
5. **Select transform type** — For each DMO population path, choose streaming (single source, near-real-time) or batch (multi-source join, scheduled).
6. **Design XMD customization** — Identify which fields need label changes or formatting updates. Plan Main XMD PATCH calls for each.
7. **Validate with Data Cloud Query API** — After DMO population, run ANSI SQL queries via the Data Cloud Query API to confirm field values and relationship traversal.

---

## Review Checklist

- [ ] Five mandatory DMOs mapped for identity resolution (Individual, Party ID, Email, Phone, Address)
- [ ] Data relationships limited to one per field pair between DMO pairs
- [ ] XMD updates target Main XMD, not System XMD
- [ ] Streaming transforms restricted to single-DLO sources; joins use batch transforms
- [ ] DMO queries use Data Cloud Query API (ANSI SQL), not SOQL
- [ ] Subject area assignments documented for each custom DMO

---

## Salesforce-Specific Gotchas

1. **DMOs do not support SOQL** — DMOs are columnar stores in the Data Cloud data lake, not Salesforce objects in the CRM object model. SOQL queries against DMO API names return errors or empty results. All DMO data access requires the Data Cloud Query API with ANSI SQL syntax.
2. **System XMD is immutable — PATCH against it returns 403** — System XMD is auto-generated by the platform and cannot be modified. Main XMD is the correct target for field customization. Always retrieve the XMD type before attempting to patch it.
3. **Only one data relationship per field pair between DMOs** — You cannot create two separate data relationships between the same pair of fields on two DMOs. If a more complex mapping is needed, it must be modeled as a different field pairing or through a transform.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| DMO schema design document | Entity list with subject area, field definitions, and relationship map |
| Mandatory DMO mapping checklist | Confirmation that all five identity-resolution DMOs are mapped |
| Transform type selection | Streaming vs. batch decision for each DMO population path |
| XMD update specification | Field labels, aliases, and formatting changes as PATCH payload |

---

## Related Skills

- `data/data-cloud-data-streams` — For configuring DLO ingestion and field mapping from source to DLO
- `admin/data-cloud-identity-resolution` — For identity resolution ruleset design and matching rule configuration
- `admin/data-cloud-segmentation` — For building segments that query unified DMO profiles
- `architect/data-cloud-architecture` — For overall Data Cloud platform architecture and deployment planning
