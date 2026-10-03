---
name: etl-vs-api-data-patterns
description: "Use this skill when selecting between ETL/ELT tools and API-based integration for ongoing data pipelines between Salesforce and external systems: Informatica Cloud, MuleSoft Batch, Jitterbit, and direct Bulk API patterns. Trigger keywords: ETL vs API integration choice, Informatica vs MuleSoft data pipeline, should I use ETL or API for Salesforce, bulk data pipeline architecture, ongoing data sync tool selection, choose between Bulk API and REST for a nightly sync, design an ETL load into Salesforce. NOT for one-time migration — use data/data-migration-planning. NOT for Platform Events, CDC or Pub/Sub vs Bulk API timing — use integration/real-time-vs-batch-integration."
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
  - "choose between Bulk API 2.0 and the REST API for a nightly sync from our ERP"
  - "design a recurring upsert from a data warehouse into Salesforce"
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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# ETL vs API Data Patterns

Use this skill when deciding between ETL/ELT-based integration and API-based integration for ongoing data pipelines touching Salesforce. The scope is persistent integration pipelines, not one-time migrations. The primary question: should this pipeline move data in scheduled bulk batches through an ETL tool, or record by record through APIs as events happen?

---

## Before Starting

Gather this context before working on anything in this domain:

- Is this a **one-time migration** or an **ongoing recurring pipeline**? One-time migrations go to `data/data-migration-planning`.
- What is the latency requirement? Seconds (real-time), minutes (near-real-time), or hours/daily (batch)?
- How many records change per run, and per day? The 2,000-record line in the Bulk API 2.0 guide is the first fork.
- Which system is the data master for each object? The Batch Data Synchronization pattern rates solutions differently by master.
- Is data quality profiling, lineage governance, or master data management (MDM) required?
- What licenses are available: MuleSoft Anypoint, Informatica, another ETL tool, or only native Salesforce APIs?

---

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "How many records change per run, and how many per day across all jobs?" | The Bulk API 2.0 guide calls more than 2,000 records a good candidate for Bulk API 2.0, and caps ingest at 150,000,000 records per rolling 24 hours | The interface per job: Composite or sObject Collections under 2,000, Bulk API 2.0 above | A job that fits the daily record and batch allocations instead of failing mid-run |
| "How soon after a change must the other system see it?" | Integration Patterns says timeliness "isn't of significant importance" in Batch Data Synchronization | A latency target that picks batch, Change Data Capture, or Remote Call-In | No five-minute ETL schedule sold as real-time |
| "Which system is the master for this object?" | The Batch Data Synchronization table rates Change Data Capture best when Salesforce is master and third-party ETL best when the remote system is master | One direction of truth per object and a matching key strategy | Fewer conflicting updates and a clear owner for corrections |
| "Which external ID will match records on both sides?" | Integration Patterns tells ETL jobs to use primary keys from both systems; a Bulk API 2.0 upsert needs `externalIdFieldName` | An External ID field on each target object | Idempotent reruns instead of duplicates after a restart |
| "Do child records arrive grouped by parent?" | Bulk API 2.0 runs batches in parallel only, and Integration Patterns warns that ungrouped child loads fail on parent locks | A sort order by parent key in the extract | Fewer lock failures and fewer retry loops |
| "Does the business need data quality, lineage, or MDM?" | The Salesforce Architects "Better Together" page assigns those to Informatica and real-time API mediation to MuleSoft | A platform choice tied to requirements, not to whichever license exists | A tool that already does what the compliance team will ask for |

What a proper configuration adds over just wiring a connector: the pipeline uses the right Salesforce interface for its volume, reruns safely by external ID, stays inside the daily allocations, and keeps a control table that tells you where to restart.

---

## Core Concepts

### Application integration vs data integration

The Salesforce Architects page "Leveraging MuleSoft and Informatica: Better Together" treats the two as complementary. MuleSoft leads on application connectivity: real-time API mediation, event handling and orchestration, and short-lived transactional reliability. Informatica leads on data management: large-scale ETL/ELT, data quality, lineage, governance, and MDM. Its platform-selection rule: interactive processes composed from independent services require MuleSoft; bulk data movement, transformation, and management require Informatica; complex architectures may require both.

The Data Integration decision guide adds a landscape rule: use MuleSoft or another ESB or ETL solution if it is already part of your landscape.

### The Salesforce-side interface

| Volume per operation | Interface | Grounding |
|---|---|---|
| Fewer than 2,000 records | REST Composite or sObject Collections (up to 200 records per call), or SOAP | Bulk API 2.0 guide introduction; REST API guide, sObject Collections |
| More than 2,000 records | Bulk API 2.0 ingest or query job | Bulk API 2.0 guide introduction |
| One record per event, seconds of latency | REST or SOAP Remote Call-In, or Platform Events | Integration Patterns, Remote Call-In |

Bulk API 2.0 facts that shape an ETL design:

- Ingest and query jobs use CSV only. The `contentType` property accepts only `CSV` for both.
- You do not create batches. Salesforce creates a batch for every 10,000 records, up to 150,000,000 records per day. If the limit is exceeded mid-job, the remaining data is not processed and the job fails.
- A job upload can be up to 150 MB after base64 encoding; the cheat sheet advises uploading no more than 100 MB.
- A batch that cannot finish in 5 minutes is retried, up to 20 times, then the whole job fails.
- `concurrencyMode` is parallel only.
- Batches are shared with Bulk API (1.0): 15,000 per rolling 24 hours. Only ingest jobs consume batches.
- Bulk API and Bulk API 2.0 calls count toward the org's daily API request allocation. The 150,000,000-record ceiling is a separate limit, not a separate call budget.
- Results stay retrievable for 7 days after the job completes.

### MuleSoft batch processing

MuleSoft is not only a real-time tool. Mule batch processing uses a Batch Job, one or more Batch Steps, and an optional Batch Aggregator, with persistent queues so a job can resume after a crash or redeploy, and an On Complete phase that reports which records succeeded and failed (MuleSoft docs, "Batch Processing"). If MuleSoft is already the platform, a Mule batch job writing through the Salesforce connector to Bulk API 2.0 is a valid ETL path. UNVERIFIED (2026-10-03): which Salesforce connector operations use Bulk API 2.0 by default; confirm in the connector version you run.

---

## Common Patterns

### Pattern: Scheduled ETL into Salesforce with a control table

**When to use:** A warehouse or ERP is the master and a nightly or weekly window is acceptable.

**How it works (Integration Patterns, Batch Data Synchronization):**
1. Read a control table for the last run time and other control values.
2. Query the source for rows changed since then.
3. Apply validation and enrichment rules.
4. Sort child rows by parent key, then write with a Bulk API 2.0 upsert on an External ID.
5. Read `failedResults` and `unprocessedrecords` for the job.
6. On success, advance the control values; on failure, record restart values and exit.

The guide recommends keeping control tables where the ETL tool can reach them even when Salesforce is unavailable: Salesforce is a spoke, the ETL infrastructure is the hub.

### Pattern: Salesforce as master, replicated outward

Change Data Capture is rated "Best" when Salesforce is the master. It publishes create, update, delete, and undelete events that an integration app consumes. Third-party ETL querying Salesforce on timestamps is rated "Good." See `integration/change-data-capture-integration`.

### Pattern: Event-driven record sync into Salesforce

**When to use:** A source system change must appear in Salesforce within seconds.

**How it works:** The source publishes an event. Middleware transforms it and calls the REST API (one record, or sObject Collections for small groups) or publishes a platform event. Remote Call-In is synchronous request-reply. Integration Patterns rates Remote Call-In "Suboptimal" for bulk synchronization because of continuous traffic and locking.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Record-level change visible in seconds | API-led (MuleSoft or custom) with REST or Platform Events | Batch timeliness is not the design goal of Batch Data Synchronization |
| Nightly delta of hundreds of thousands of rows | ETL tool with Bulk API 2.0 upsert | More than 2,000 records per operation |
| Data quality, lineage, or MDM required | Informatica | Assigned to Informatica by the Architects "Better Together" page |
| MuleSoft licensed, bulk load needed, no governance requirement | Mule batch job plus Bulk API 2.0 | Avoids a second platform |
| Salesforce is master, external store needs deltas | Change Data Capture | Rated Best in Batch Data Synchronization |
| One-time migration | `data/data-migration-planning` | Not an ongoing pipeline |
| Jitterbit or another iPaaS under evaluation | Vendor documentation plus this decision table | UNVERIFIED (2026-10-03): whether any architect.salesforce.com page gives Jitterbit selection criteria; the Data Integration decision guide does not name it |

---

## Recommended Workflow

1. **Classify the scenario.** Ongoing pipeline or one-time migration. Route migrations to `data/data-migration-planning`.
2. **Fix latency and master per object.** Record seconds, minutes, or a nightly window, and which system owns each object.
3. **Size each job.** Records per run and per day; pick Composite or sObject Collections under 2,000 records and Bulk API 2.0 above; check the day against 150,000,000 records and 15,000 batches.
4. **Choose the platform.** Governance, quality, MDM: Informatica. Interactive, event-driven processes: MuleSoft. Both if the architecture needs both.
5. **Build the Salesforce side.** External ID fields (`references/metadata-examples.md`), an API-only integration user, and the Bulk API 2.0 upsert sequence (`references/examples.md`).
6. **Lint the job specs.** Run `python3 scripts/check_etl_vs_api_data_patterns.py --manifest-dir <folder>` over the job JSON and CSV files.
7. **Record the decision.** Use `templates/etl-vs-api-data-patterns-template.md`.

---

## Review Checklist

- [ ] Confirmed this is an ongoing pipeline, not a one-time migration
- [ ] Latency and data master recorded per object
- [ ] Jobs above 2,000 records use Bulk API 2.0; smaller ones use Composite or sObject Collections
- [ ] Daily volume checked against 150,000,000 ingest records and 15,000 batches
- [ ] Every upsert names an External ID that exists on the target object
- [ ] Child rows sorted by parent key
- [ ] Failed and unprocessed results read within 7 days and fed to a retry path
- [ ] Platform choice traced to latency, volume, and governance needs

---

## Salesforce-Specific Gotchas

See `references/gotchas.md`. The two that cause the most production incidents: Bulk API 2.0 calls still count toward the daily API allocation, and an ingest job that crosses the daily record limit stops and leaves the rest unprocessed.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| ETL vs API decision record | Rationale based on latency, volume, master, and governance |
| Interface map | Per job: Composite, sObject Collections, Bulk API 2.0, or Platform Events |
| External ID and job specs | CustomField metadata and Bulk API 2.0 job JSON |
| Integration architecture diagram | Source, ETL/API layer, control table, and Salesforce endpoint |

---

## Related Skills

- `data/data-migration-planning`: one-time data migration tool selection (not ongoing ETL)
- `integration/middleware-integration-patterns`: iPaaS vendor comparison and general middleware selection
- `integration/real-time-vs-batch-integration`: Platform Events, CDC, and Pub/Sub timing choices
- `integration/change-data-capture-integration`: CDC-based incremental replication patterns
