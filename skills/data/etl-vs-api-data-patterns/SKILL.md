---
name: etl-vs-api-data-patterns
description: "Use this skill when selecting between ETL/ELT tools and API-based integration for ongoing data pipelines between Salesforce and external systems: Informatica Cloud, MuleSoft Batch, Jitterbit, and direct Bulk API patterns. Trigger keywords: ETL vs API integration choice, Informatica vs MuleSoft data pipeline, should I use ETL or API for Salesforce, bulk data pipeline architecture, ongoing data sync tool selection. NOT for one-time data migration tool selection (use data-migration-planning), Data Loader usage, or real-time event-driven integration (use event-driven-architecture-patterns)."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
triggers:
  - "should I use ETL or API-based integration for my Salesforce data pipeline"
  - "when should I use Informatica versus MuleSoft for Salesforce data integration"
  - "my ETL job is using the Salesforce REST API for bulk inserts and hitting API limits"
  - "how do I choose between MuleSoft Batch and Informatica for ongoing data sync"
  - "what is the difference between ETL and real-time API integration for Salesforce"
  - "we need near-real-time sync but our ETL tool runs every 5 minutes — is that sufficient"
tags:
  - etl
  - data-integration
  - informatica
  - mulesoft
  - bulk-api
  - integration-architecture
inputs:
  - "Data volume: row count and frequency of change"
  - "Latency requirement: real-time, near-real-time, or batch"
  - "Source system type: Salesforce as source, target, or both"
  - "Available tools: MuleSoft license, Informatica license, or custom"
  - "Data quality and lineage governance requirements"
outputs:
  - "ETL vs API integration decision with rationale"
  - "Tool selection recommendation (Informatica, MuleSoft, Bulk API)"
  - "Architecture pattern for the selected approach"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# ETL vs API Data Patterns

Use this skill when deciding between ETL/ELT-based integration and API-based integration for ongoing data pipelines touching Salesforce. The scope is persistent integration pipelines (not one-time migrations) and the primary question is: should this integration use bulk batch processing via an ETL tool or event-driven API-based integration?

---

## Before Starting

Gather this context before working on anything in this domain:

- Is this a **one-time migration** or an **ongoing recurring pipeline**? One-time migrations go to `data-migration-planning`.
- What is the latency requirement? Seconds (real-time), minutes (near-real-time), or hours/daily (batch)?
- What is the data volume? Millions of rows per run or thousands?
- Is data quality profiling, lineage governance, or master data management (MDM) required?
- What licenses are available: MuleSoft Anypoint, Informatica Cloud Services, or native Salesforce Bulk API?

---

## Core Concepts

### The Official Salesforce Architects Framing: Complementary, Not Competing

The Salesforce Architects official guidance treats MuleSoft and Informatica as **complementary tools** on a selection axis, not competitors:

- **MuleSoft** owns: real-time API connectivity, event-driven orchestration, latency-sensitive application integration, API management, and experience/process/system API layer design.
- **Informatica** owns: ETL/ELT for massive datasets, data quality and profiling, lineage governance, master data management (MDM), and data warehouse/lake pipelines.

The selection axis is **"application integration" vs "data integration"**:
- Application integration = API-first, event-driven, latency-sensitive → MuleSoft
- Data integration = bulk volume, transformation pipelines, governance requirements → Informatica or ETL tools

Salesforce Bulk API 2.0 is the standard Salesforce-side interface that all ETL tools must use for bulk operations. ETL tools that call the REST API for bulk loads (using standard CRUD REST calls) will exhaust REST API limits and underperform.

### MuleSoft Batch Scope for Bulk Operations

MuleSoft is not exclusively a real-time tool. MuleSoft's **Batch scope** provides structured bulk processing within MuleSoft flows with commit size, threading, and on-complete error handling. For scenarios where MuleSoft is already the integration platform and a bulk Salesforce load is needed, MuleSoft Batch + Salesforce Connector using Bulk API 2.0 is a valid pattern — without requiring a separate ETL tool.

However, MuleSoft Batch scope does not provide:
- Native data quality profiling (no data-health reports)
- Lineage governance (no native lineage graph)
- Source-to-target mapping documentation for compliance purposes

For those capabilities, Informatica (or a comparable ETL platform with lineage) is required.

### Bulk API 2.0 Limits

Salesforce Bulk API 2.0 limits at Spring '25:
- Maximum 150 million rows per 24-hour window across all jobs
- Individual job batch limit: up to 10,000 records per batch
- Ingest jobs: CSV only
- Query jobs: support CSV and JSON results

ETL tools using Salesforce connectors should use Bulk API 2.0, not the REST API sObjects endpoint, for volume above 200 records per operation.

---

## Common Patterns

### Pattern: Informatica Cloud for Large-Volume ETL with Governance

**When to use:** Daily or weekly sync of millions of records between a data warehouse (Snowflake, Redshift) and Salesforce with data quality profiling and lineage requirements.

**How it works:**
1. Configure Informatica Cloud Services connector to Salesforce (uses Bulk API 2.0 under the hood).
2. Design a mapping in Informatica that includes data quality transformations (standardize, validate, deduplicate).
3. Schedule as a taskflow with dependency sequencing (data quality check → load).
4. Use Informatica's lineage catalog to document source-to-target field mapping for compliance.

**Why not MuleSoft:** MuleSoft does not provide native data quality profiling or lineage documentation. For compliance-driven data governance, Informatica is the appropriate tool.

### Pattern: MuleSoft API-Led for Real-Time or Near-Real-Time Sync

**When to use:** Customer record updates in an external CRM must reflect in Salesforce within seconds or minutes. Event-driven trigger on source system change.

**How it works:**
1. Source system publishes a change event (webhook, message queue, or Kafka topic).
2. MuleSoft experience or process API receives the event and transforms it.
3. MuleSoft Salesforce Connector calls the REST API (CRUD) or Platform Events to write to Salesforce.
4. Latency is typically < 5 seconds end-to-end.

**Why not ETL:** ETL tools process in scheduled batches. They cannot respond to individual record change events in real time. Batch ETL has inherent latency of the batch interval (minutes to hours).

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Real-time event-driven sync | MuleSoft API | ETL cannot respond sub-minute; API is required |
| Daily full extract of millions of rows | Informatica Cloud or ETL tool | ETL tools optimize for bulk throughput via Bulk API 2.0 |
| Data quality profiling and lineage required | Informatica | Native DQ and lineage capabilities |
| MuleSoft already licensed, bulk load needed | MuleSoft Batch + Bulk API 2.0 connector | Avoid adding another tool when MuleSoft can handle batch |
| One-time migration | Use data-migration-planning skill | Not an ongoing pipeline scenario |
| Jitterbit selection criteria needed | Use official Salesforce integration docs as baseline | Jitterbit lacks formal Salesforce Architects documentation |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Classify the integration scenario** — Is this ongoing sync (ETL/API decision) or one-time migration? Route one-time migrations to `data-migration-planning`.
2. **Determine latency requirement** — Sub-minute: API-led. Hourly or daily batch: ETL or MuleSoft Batch.
3. **Assess data volume** — Above ~200 records per operation: require Bulk API 2.0 support in any tool selected.
4. **Evaluate governance requirements** — Data quality profiling and lineage needed? Informatica is the primary option with formal Salesforce Architects endorsement.
5. **Check tool availability** — MuleSoft license available? MuleSoft Batch can handle bulk loads without a separate ETL tool for non-governance scenarios.
6. **Document the decision** — Record the selected approach, rationale, expected data volume, refresh frequency, and Bulk API 2.0 usage confirmation.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Confirmed this is an ongoing pipeline (not one-time migration)
- [ ] Latency requirement classified (real-time / near-real-time / batch)
- [ ] Data volume assessed and Bulk API 2.0 confirmed for high-volume loads
- [ ] Governance requirements assessed (data quality profiling, lineage)
- [ ] Tool selection documented with rationale
- [ ] No REST API sObjects endpoint used for bulk loads (must use Bulk API 2.0)

---

## Salesforce-Specific Gotchas

1. **Conflating one-time migration with ongoing ETL pipeline** — One-time migrations have completely different tool selection criteria (SFDMU, Dataloader, Data Import Wizard). Ongoing ETL pipelines require different architecture. Do not apply migration tool guidance to ETL pipeline design.

2. **Using REST API sObjects for bulk ETL** — ETL tools that call the standard REST API CRUD endpoints for bulk loads exhaust the daily REST API limit rapidly. Bulk operations must use Bulk API 2.0. Any tool that does not support Bulk API 2.0 is inappropriate for high-volume ongoing ETL.

3. **Recommending ETL for real-time scenarios** — ETL batch processing has inherent latency. If a use case requires record-level sync within seconds, an ETL tool (even with short batch intervals) is architecturally inappropriate. Event-driven API integration is required.

4. **Jitterbit selection criteria not in official Salesforce Architects documentation** — Only Informatica and MuleSoft have formal treatment in architect.salesforce.com guidance. Jitterbit selection criteria require vendor documentation rather than official Salesforce source grounding.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| ETL vs API decision record | Documented rationale for tool selection based on latency, volume, and governance needs |
| Tool comparison matrix | Side-by-side of Informatica, MuleSoft, and direct Bulk API on key criteria |
| Integration architecture diagram | Data flow showing source, ETL/API layer, and Salesforce endpoint |

---

## Related Skills

- `data/data-migration-planning` — Use for one-time data migration tool selection (not ongoing ETL)
- `integration/middleware-integration-patterns` — Use for iPaaS vendor comparison and general middleware selection
- `architect/etl-vs-api-data-patterns` — Use for architect-level data integration decision framework
- `integration/change-data-capture-integration` — Use for CDC-based incremental replication patterns
