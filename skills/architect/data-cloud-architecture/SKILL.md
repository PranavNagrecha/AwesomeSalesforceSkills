---
name: data-cloud-architecture
description: "Use when designing or evaluating a Data Cloud implementation architecture — covering data lake strategy (DSO/DLO/DMO layers), identity resolution rule design, activation target configuration, and segmentation strategy. Trigger phrases: Data Cloud architecture design, identity resolution strategy, activation target setup, data lakehouse layers, unified profile design, Data Cloud segment activation, DMO mapping strategy, golden profile design. NOT for individual data stream ingestion setup, not for Data Cloud licensing questions, not for Marketing Cloud journey builder, not for individual calculated insight formulas."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
  - Performance
triggers:
  - "design the Data Cloud architecture for our org"
  - "how should we configure identity resolution rules across multiple data sources"
  - "which activation targets do we need and how do we connect them before segment publish"
  - "how do DSO, DLO, and DMO layers work together in Data Cloud"
  - "unified profile is missing records — how do we diagnose identity resolution coverage"
  - "should we use Calculated Insights or Streaming Insights for this segment filter"
  - "our segment activations are failing — activation target connection not authenticated"
tags:
  - Data-Cloud
  - data-lake
  - identity-resolution
  - activation
  - segmentation
  - DMO
  - unified-profile
  - lakehouse
inputs:
  - List of data sources being ingested into Data Cloud (CRM, marketing, commerce, external)
  - Identity attributes available per source (email, phone, loyalty ID, SFMC contact key)
  - Activation targets required (SFTP, S3, Meta, Google, LinkedIn, Marketing Cloud, CRM)
  - Segment use cases and time-sensitivity requirements
  - Data volume and refresh frequency per source
  - Whether multi-business-unit or single-BU Data Cloud deployment
outputs:
  - Recommended DSO → DLO → DMO → Unified Individual layer design
  - Identity resolution ruleset design (match rules, reconciliation rules)
  - Activation target connection checklist before first segment publish
  - Segmentation strategy recommendation (batch vs streaming insight filters)
  - DMO mapping requirements per data source
  - Review checklist for identity resolution coverage
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

Use this skill when designing or evaluating a Data Cloud implementation architecture. Data Cloud is a real-time data platform built on a lakehouse model — it ingests raw data, cleanses it, harmonizes it to a canonical data model, and resolves identities across sources to produce a Unified Individual (golden profile). This skill covers the four-layer data flow, identity resolution design, activation target configuration, and segmentation strategy. It does not cover how to configure individual data streams or calculated insight formulas.

---

## Before Starting

Gather this context before working on a Data Cloud architecture:

- **What data sources are in scope?** The identity resolution strategy depends entirely on which identity attributes (email, phone, loyalty ID, SFMC contact key) are available in each source. Sources with no Contact Point or Party Identification DMO mappings cannot contribute to unified profiles.
- **What activation channels are required?** Each activation target — file-based (SFTP, S3, GCS), ad platform (Meta, Google, LinkedIn, Amazon, TikTok), or Salesforce platform (Marketing Cloud, Core CRM, Commerce) — requires its own authenticated connection configured before a segment can be published. Activation failures at go-live are almost always caused by missing pre-configured connections.
- **What are the time-sensitivity requirements for segment filters?** Calculated Insights run on batch schedules and introduce lag — segments that depend on them cannot reflect the very latest activity. Streaming Insights update in near real-time and are appropriate for time-sensitive use cases.

---

## Core Concepts

### 1. Data Lakehouse Layer Flow: DSO → DLO → DMO → Unified Individual

Data Cloud processes data through four sequential layers:

1. **Data Source Object (DSO):** The raw ingested data in its source schema. Data arrives here with no transformation. DSOs are created automatically when a data stream is configured. Do not use DSOs as analysis targets — they are transient landing zones, not stable analytical objects.

2. **Data Lake Object (DLO):** Cleansed and deduplicated source data. The DLO retains the source schema but removes obvious errors and applies field-level type normalization. DLOs are the right layer for source-specific analysis before harmonization.

3. **Data Model Object (DMO):** Harmonized data mapped to Salesforce's canonical Data Cloud data model (Individual, Contact Point Email, Contact Point Phone, Party Identification, Engagement, etc.). Field mappings from DLO to DMO are configured manually. The quality of DMO mapping is the single most important determinant of identity resolution coverage. Only DMOs with Contact Point or Party Identification mappings contribute to identity resolution.

4. **Unified Individual:** The golden profile produced by identity resolution. Each Unified Individual aggregates records from multiple source DMOs that have been matched to the same physical person. Reconciliation rules control which source value "wins" for each attribute on the Unified Individual.

The pipeline is irreversible at each layer — downstream quality problems almost always originate from incomplete DMO mapping, not from ingestion errors.

### 2. Identity Resolution: Match Rules and Reconciliation Rules

Identity resolution is the process by which Data Cloud determines that records from different sources represent the same individual and merges them into a Unified Individual. It operates in two phases:

**Match rules** determine when two records are the same individual. Match rule types:
- **Exact match:** Records are linked only when a field value is byte-identical (e.g., email address). High precision, low recall. Use for high-confidence identifiers.
- **Fuzzy match:** Records are linked when a field value is similar within a configurable threshold (useful for name variations). Lower precision — test with real data before enabling in production.
- **Normalized match:** Applies normalization before comparison (e.g., strips formatting from phone numbers before matching). Recommended for phone and address fields.
- **Compound match:** Requires multiple fields to match simultaneously (e.g., first name + last name + zip code). Higher precision than single-field matching; useful when no unique identifier is available.

**Transitive matching** is applied automatically: if Record A matches Record B, and Record B matches Record C, then A, B, and C are placed in the same identity cluster even if A and C share no direct match. This is the correct behavior but can cause unexpected large clusters if low-precision match rules are active.

**Reconciliation rules** determine which source value populates each attribute on the Unified Individual when multiple sources disagree:
- **Most Frequent:** The value that appears most often across matched records wins. Best for stable categorical attributes.
- **Most Recent:** The most recently updated record's value wins. Best for time-sensitive attributes (current email, current address).
- **Source Priority:** A manually configured source order determines which value wins. Use when a specific source is designated the system of record for an attribute.

### 3. Activation Targets

Activation targets are the outbound channels through which Data Cloud publishes segment membership. Three categories:

- **File-based targets:** SFTP, Amazon S3, Google Cloud Storage. Used for batch downstream systems. The segment is exported as a file on a configured schedule.
- **Ad platform targets:** Meta Ads, Google Ads, LinkedIn Ads, Amazon Ads, TikTok Ads. Audience segments are pushed directly to the ad platform's audience API.
- **Salesforce platform targets:** Marketing Cloud (contact injection into sendable data extensions), Core CRM (contact/lead updates), Commerce Cloud.

Every activation target requires its own authenticated connection — credentials or OAuth tokens configured in Data Cloud's Activation Targets setup. **A segment cannot be published to a target that has not been authenticated in advance.** This is the most common cause of first-publish failures in go-live scenarios.

### 4. Segmentation Strategy: Batch vs Streaming Insights

Segments in Data Cloud can filter on three types of attributes:

- **DMO attributes:** Directly mapped fields on Data Model Objects. Updated on the DMO's ingestion schedule.
- **Calculated Insights (CI):** Pre-computed aggregate metrics (e.g., total purchase value, engagement score). CIs run on a batch schedule — the default refresh is hourly to daily depending on configuration. Any segment that filters on a CI attribute will reflect the last batch computation, not real-time data.
- **Streaming Insights:** Near-real-time computed metrics derived from streaming data ingestion. Appropriate for time-sensitive filters (e.g., "in-session behavior in the last 15 minutes," "opened email within the last hour").

The critical architectural decision: **use Calculated Insights for historical aggregate metrics; use Streaming Insights for time-sensitive behavioral signals.** Mixing CI-based filters into a segment intended for real-time activation introduces lag that undermines the use case.

---

## Common Patterns

### Pattern 1: Multi-Source Identity Resolution with Email as Anchor

**When to use:** The org ingests data from CRM, Marketing Cloud, and an e-commerce platform. Each source uses a different unique identifier but all capture email addresses.

**How it works:**
1. Map each source's email field to `ContactPointEmail` DMO with `emailAddress` as the matching field.
2. Configure an exact match rule on `emailAddress` as the primary match rule.
3. Add a normalized match rule on phone (if available) as a secondary rule to catch records where email is missing.
4. Set reconciliation rules: Most Recent for email and phone; Source Priority (CRM wins) for name and address.
5. Run identity resolution in test mode and review cluster size distribution — clusters larger than 10 records typically indicate a low-precision match rule creating false merges.

**Why not rely on fuzzy name matching alone:** Name-only matching produces large false-positive clusters (common names), especially in consumer data. Always anchor to a unique identifier (email, phone) first.

### Pattern 2: Activation Readiness Pre-Flight

**When to use:** Preparing for the first segment publication to any activation target.

**How it works:**
1. In Data Cloud Setup, navigate to Activation Targets and verify each target has a green "Connected" status before segment scheduling.
2. For file-based targets (SFTP/S3/GCS): confirm write permissions by testing a small manual export.
3. For ad platform targets: verify the platform API token has not expired — ad platform tokens have short expiry windows (Meta: 60 days; Google: OAuth refresh tokens are long-lived but require consent re-approval if scopes change).
4. For Marketing Cloud targets: confirm the target Business Unit's API user has permission to write to the target data extension.
5. Schedule a dry-run activation with a small test segment (100 records) before activating production segments.

**Why not activate without pre-flight:** Activation failures surface only at publish time, not at segment build time. A failed activation does not retry automatically — it requires manual re-trigger after fixing the connection.

### Pattern 3: Diagnosing Low Unified Individual Coverage

**When to use:** Identity resolution has run but the Unified Individual record count is significantly lower than expected relative to source record volume.

**How it works:**
1. Check DMO mapping completeness: confirm every source DMO that should contribute to identity resolution has a mapping to either `ContactPointEmail`, `ContactPointPhone`, or `PartyIdentification`. A DMO mapped only to `Engagement` or `Product` will not contribute to identity clusters.
2. Review match rule filter conditions: match rules can have filter conditions (e.g., only match records where `emailVerified = true`). Overly restrictive filters silently exclude records.
3. Check for high null rates on match key fields: if 60% of records have a null email address, the effective match pool is 40% of the data regardless of rule configuration.
4. Inspect the identity resolution run log for error counts — field type mismatches between DMO fields and match rule configuration cause silent exclusion.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Multiple sources have email; need unified profile | Exact match on ContactPointEmail DMO as primary rule | Email is the highest-precision single identifier; exact match avoids false clusters |
| Source has no email but has loyalty ID | Map loyalty ID to PartyIdentification DMO; use exact match on partyIdentificationNumber | PartyIdentification is the canonical DMO for proprietary IDs |
| Segment filter needs to reflect last 15 minutes of activity | Use Streaming Insights, not Calculated Insights | Calculated Insights have batch lag (hourly+); Streaming Insights are near-real-time |
| Activation to Meta Ads failing at publish time | Verify Meta API token expiry and re-authenticate the Activation Target connection | Ad platform tokens expire; unauthenticated targets silently fail at publish |
| Unified Individual count far below source record count | Audit DMO mappings — ensure ContactPoint or PartyIdentification mappings exist for each source | Only DMOs with these mappings participate in identity resolution |
| Need to activate to both Marketing Cloud and CRM simultaneously | Configure two separate Activation Target connections; they can share the same segment | Each platform requires its own authenticated target — one segment can publish to multiple targets |
| Reconciliation rule for email address | Use Most Recent | Email addresses change over time; the most recently updated source is the best authority |
| Name and address reconciliation | Use Source Priority (designate CRM as system of record) | CRM typically has the most carefully maintained demographic data |

---

## Recommended Workflow

1. **Map data sources to DMO layers before any ingestion work.** For each source being onboarded, document which DMO each source field will map to, and confirm at least one ContactPointEmail, ContactPointPhone, or PartyIdentification mapping exists per source that should contribute to identity resolution. Sources without these mappings will ingest successfully but will be invisible to identity resolution — this is the most common source of unexplained coverage gaps.

2. **Design identity resolution ruleset with match rule hierarchy.** Start with the highest-precision identifier available (email > loyalty ID > phone > name+address compound). Configure exact match on that identifier first. Add secondary rules only after validating the primary rule's cluster distribution. Review transitive matching behavior — a secondary fuzzy rule on name can dramatically inflate cluster sizes if the primary rule creates many small clusters that become transitively connected.

3. **Configure all activation targets before building segments.** Navigate to Activation Targets in Data Cloud Setup and authenticate every outbound channel that will be used. Test each connection explicitly. Do not defer activation target setup to the day of go-live — authentication issues for ad platform targets often require platform-side re-authorization that takes time.

4. **Classify segment filters by time-sensitivity and choose the right insight type.** For each planned segment, review the filter attributes: if any filter requires data fresher than the Calculated Insight batch schedule, replace that filter with a Streaming Insight. Document the refresh lag for each Calculated Insight used in production segments so stakeholders understand the effective data recency.

5. **Run identity resolution in validation mode and review cluster metrics.** After configuring match rules, run identity resolution and inspect the cluster size distribution report. Clusters with more than 20 records are a signal of low-precision match rules creating false merges. A cluster merge rate (records merged / total source records) below 5% may indicate missing DMO mappings preventing resolution from running at all.

6. **Validate Unified Individual coverage against expected source record volume.** Calculate the expected coverage rate: (Unified Individuals created / total unique source records across all participating sources). If the rate is significantly lower than expected, audit DMO field mappings, check match rule filter conditions, and inspect null rates on match key fields.

7. **Document reconciliation rule decisions and test against known records.** For each attribute on the Unified Individual, record which reconciliation rule was chosen and why. Test reconciliation outcomes against a set of known test records where the correct source-of-truth value is established. Reconciliation rule choices are invisible at runtime — they can only be validated by inspecting the resulting Unified Individual values against expected outcomes.

---

## Review Checklist

Run through these before marking a Data Cloud architecture design complete:

- [ ] Every source DMO that should contribute to identity resolution has at least one ContactPointEmail, ContactPointPhone, or PartyIdentification mapping
- [ ] Match rule hierarchy is documented: primary rule (highest-precision identifier) → secondary rules in descending precision order
- [ ] Transitive matching implications reviewed for each match rule combination — no low-precision rules that could cause runaway cluster growth
- [ ] Reconciliation rule chosen and justified for each Unified Individual attribute
- [ ] All activation targets authenticated and connection-tested before segment scheduling
- [ ] Segment filters audited for time-sensitivity — Calculated Insights replaced with Streaming Insights where batch lag is unacceptable
- [ ] Identity resolution cluster distribution reviewed — no clusters > 20 records unless deliberately expected (household-level resolution)
- [ ] Unified Individual coverage rate validated against source record volume

---

## Salesforce-Specific Gotchas

1. **Identity resolution silently excludes records without ContactPoint or PartyIdentification DMO mappings.** A source DMO mapped only to Engagement or Product will ingest and appear in query results but will never contribute a record to a Unified Individual cluster. The ingestion job succeeds with no errors — the exclusion is silent. Always verify the DMO mapping type for every source intended to contribute to unified profiles.

2. **Calculated Insights introduce batch lag — time-sensitive segment filters on CI attributes will not reflect current activity.** The default CI refresh schedule is configured per insight, ranging from hourly to daily. A segment that filters "purchased in the last 2 hours" using a CI will only be as fresh as the last CI batch run, not as of the moment of segment evaluation. Use Streaming Insights for sub-hour time sensitivity.

3. **Each activation target requires a separate authenticated connection before segment publish.** Segment configuration and activation target authentication are independent steps. A segment can be fully configured, published, and scheduled against an unauthenticated target — the failure only surfaces at publish execution time. There is no warning during segment setup. Pre-flight all connections before go-live.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| DMO mapping matrix | Per-source table mapping source fields to DMO entity and field, noting identity-resolution-eligible mappings |
| Identity resolution ruleset design | Match rule hierarchy with rule type, match field, and filter conditions documented; reconciliation rule per attribute |
| Activation target pre-flight checklist | Per-target authentication status, last test date, and token expiry date |
| Segmentation strategy document | Per-segment filter classification (DMO attribute vs CI vs Streaming Insight) with refresh lag documented |

---

## Related Skills

- `data/data-cloud-data-streams` — Individual data stream configuration and DLO/DMO field mapping setup; use before this skill to onboard each source
- `architect/ai-ready-data-architecture` — Designing the underlying Salesforce data model and field design for AI and Data Cloud readiness; use before this skill when the org has multiple data sources with conflicting schemas
- `data/data-cloud-vector-search-dev` — Implementing vector search on Data Cloud data; this skill covers the architecture prerequisite (identity resolution and DMO design) that vector search depends on
