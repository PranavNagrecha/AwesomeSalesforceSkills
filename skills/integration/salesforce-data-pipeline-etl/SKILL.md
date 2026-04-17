---
name: salesforce-data-pipeline-etl
description: "Export large Salesforce datasets to a lakehouse via Bulk API 2.0, CDC streams, or Salesforce Data Pipelines. NOT for ad-hoc exports."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Reliability
triggers:
  - "salesforce to snowflake"
  - "etl from salesforce"
  - "bulk api 2 export"
  - "change data capture to lake"
tags:
  - etl
  - bulk-api
  - cdc
  - snowflake
inputs:
  - "source objects + volume"
  - "sink (Snowflake, BigQuery, Databricks)"
outputs:
  - "ETL architecture: initial load + incremental CDC pattern"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Salesforce Data Pipeline / ETL

Production Salesforce → lake pipelines combine a one-time Bulk API 2.0 snapshot with an ongoing CDC or Platform Event stream. Naive incremental loads on LastModifiedDate lose updates during the query window; CDC guarantees ordered delta capture.

## When to Use

Analytics workloads that need <1h freshness on Salesforce data in a warehouse.

Typical trigger phrases that should route to this skill: `salesforce to snowflake`, `etl from salesforce`, `bulk api 2 export`, `change data capture to lake`.

## Recommended Workflow

1. Initial snapshot: Bulk API 2.0 query job per object; store in staging.
2. Subscribe to CDC for each object via Pub/Sub API (or Change Data Capture Stream).
3. Apply deltas onto snapshot using event ChangeEventHeader.commitTimestamp + changeType (CREATE/UPDATE/DELETE/GAP_FILL).
4. Handle GAP_FILL events with a re-query of affected Ids (CDC may gap on heavy load).
5. Monitor replay lag; auto-refresh from Bulk snapshot if lag > threshold.

## Key Considerations

- CDC event retention is 3 days — downtime >3 days requires full re-snapshot.
- Field-level deletions of custom fields trigger schema migrations downstream.
- Big Object data cannot be streamed via CDC.
- Avoid SOQL polling at scale — you hit API limits.

## Worked Examples (see `references/examples.md`)

- *Snowflake mirror* — Finance analytics
- *Gap-fill handler* — CDC gap after outage

## Common Gotchas (see `references/gotchas.md`)

- **CDC retention exceeded** — Consumer offline >3 days; events lost.
- **Missing GAP_FILL** — Silently lose records.
- **SOQL polling fallback** — Eats API allocation.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- LastModifiedDate polling as primary path
- Ignoring GAP_FILL events
- No replay-id checkpointing

## Official Sources Used

- Apex REST & Callouts — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts.htm
- Named Credentials — https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm
- Connect REST API — https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/
- Private Connect — https://help.salesforce.com/s/articleView?id=sf.private_connect_overview.htm
- Bulk API 2.0 — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/
- Pub/Sub API — https://developer.salesforce.com/docs/platform/pub-sub-api/guide/intro.html
