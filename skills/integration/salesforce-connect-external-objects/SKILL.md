---
name: salesforce-connect-external-objects
description: "Use when deciding whether Salesforce Connect and External Objects are the right fit for external data access, or when reviewing OData, cross-org, and custom adapter patterns, query limitations, and latency tradeoffs. Triggers: 'Salesforce Connect', 'External Objects', '__x', 'OData adapter', 'custom adapter'. NOT for the External Object configuration walkthrough and the full inventory of what they cannot do — triggers, validation rules, record-triggered flows, roll-ups, indirect lookup keys — use data/data-virtualization-patterns. NOT for keeping high-volume history inside Salesforce instead — use data/external-data-and-big-objects."
category: integration
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Scalability
  - Reliability
tags:
  - salesforce-connect
  - external-objects
  - odata
  - custom-adapter
  - virtual-data
triggers:
  - "should I use Salesforce Connect or copy the data"
  - "external object query limitations in Salesforce"
  - "OData versus custom adapter for Salesforce Connect"
  - "cross org external object design"
  - "external objects performance and reporting limits"
  - "set up an OData 4.0 external data source for Salesforce Connect"
  - "write Apex that queries or inserts external object records"
inputs:
  - "source system type and whether the data must remain outside Salesforce"
  - "latency, availability, and write requirements"
  - "query shape, reporting needs, and relationship model"
outputs:
  - "virtual versus replicated data recommendation"
  - "review findings for adapter choice and platform-fit risks"
  - "Salesforce Connect pattern with operational guardrails"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Salesforce Connect External Objects

Use this skill when the architecture question is whether Salesforce should virtualize external data instead of copying it. Salesforce Connect is best when the source system stays authoritative and users need near-real-time access without a full replication pipeline. It is a poor fit when teams secretly need native Salesforce behavior on that data but do not want to admit they really need replication.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the source of truth staying outside Salesforce, and is that requirement real?
- Do users need read-only lookup-style access, or are they expecting reporting, automation, and low-latency interaction like a native object?
- Is the adapter choice OData, cross-org, or custom Apex because of source-system constraints?

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Must the data stay in the source system, and what latency and uptime does that system offer?" | Every external object query is a round trip; each join adds another | A latency budget and an availability owner | Pages that degrade predictably when the source is slow, instead of surprising users |
| "Which queries will users and code run: filters, sorts, counts, joins, text search?" | External objects reject aggregates other than `COUNT()`, `LIKE`, `INCLUDES`, `TYPEOF`, `WITH`, and more; subqueries return at most 1,000 rows | A query inventory checked against the SOQL limits table | No late rewrite when a report or LWC uses an unsupported clause |
| "Read-only, or must users create and update records in the source?" | External objects are read-only unless the data source is writable; Apex writes use `insertAsync`, `updateAsync`, or the `Immediate` variants | The writable flag and the write path per caller | Writes that reach the source and can be monitored through `BackgroundOperation` |
| "Does the source support OData 2.0 or 4.0, or is it another Salesforce org?" | Adapter choice (`OData`, `OData4`, `SfdcOrg`, custom Apex) sets the feature set and the build cost | The adapter and the protocol settings (row counts, server-driven paging, high data volume) | The least-code adapter that meets the query inventory |
| "How do related Salesforce records link to the external rows?" | Indirect lookups need a parent field that is both External ID and unique; external lookups key on the external object's External ID | The relationship type per link and the matching key | Related lists that resolve instead of showing empty |
| "Will batch jobs or automation process these records?" | Triggers are not supported on external objects (except change event triggers for OData 4.0); batch Apex with a query locator needs row counts and paging configured | The automation path or an explicit "no automation" decision | No design that depends on a trigger that can never fire |

What a proper configuration adds over "just creating the external object": queries are proven against the documented limits, writes go through the asynchronous path with monitoring, relationships use the right key, and nobody expects triggers or full reporting on data that never lands in Salesforce.

---

## Core Concepts

### External Objects Are Virtual Data Surfaces

External Objects expose data that is stored outside Salesforce. That keeps storage and synchronization problems smaller, but it means performance and availability depend on the external system as well as on Salesforce.

### Adapter Choice Changes The Operating Model

OData adapters are the clean default when the source supports them. Cross-org patterns fit Salesforce-to-Salesforce virtualization. Custom adapters exist for sources that cannot expose a supported standard shape, but they increase implementation and support cost.

### Platform Feature Coverage Is Not The Same As Native Data

External Objects can participate in useful UI and query patterns, but they do not behave exactly like standard or custom objects in every part of the platform. If the use case needs native automation, reporting depth, or consistently low latency, replication may be the better answer.

### Query Shape And User Expectations Matter

Virtualized data is fine for lookup and reference views. It becomes painful when pages, related lists, or repeated queries assume local-database speed.

| SOQL feature on `__x` | Behavior (SOQL and SOSL Reference v67.0) |
|---|---|
| Subquery or filter on a parent external object | Up to 1,000 rows |
| Joins | Up to 4 per query across external and other objects; each join is a separate round trip |
| `AVG`, `SUM`, `MIN`, `MAX`, `COUNT(field)`, `GROUP BY`, `HAVING` | Not supported |
| `COUNT()` | Supported; for OData adapters only when Request Row Counts is enabled and the source returns a total |
| `LIKE`, `INCLUDES`, `EXCLUDES`, `toLabel()`, `TYPEOF`, `FOR VIEW`, `FOR REFERENCE`, `WITH` | Not supported |
| `ORDER BY` in relationship queries (OData) | Not supported; `NULLS FIRST` / `NULLS LAST` ignored |
| `queryMore()` when the external object drives the query | Only the primary object; no subqueries |
| Static SOQL in Apex tests | Fails for custom adapters; use dynamic SOQL or a SOQL stub |

### Adapters and Writes

| Adapter (`ExternalDataSource.type`) | Fits | Notes |
|---|---|---|
| `OData4` / `OData` | A source that exposes OData | Request Row Counts, Server Driven Pagination, and High Data Volume live in `customConfiguration` |
| `SfdcOrg` | Another Salesforce org | Writable only from API 39.0 |
| Apex class (custom adapter) | A source with no standard protocol | DML is not allowed inside the adapter; all Apex limits apply |
| `AmazonDynamoDB`, `AmazonAthena` | Those AWS stores | Schema descriptors in `externalDataSrcDescriptors` |

External objects are read-only by default; `isWritable` on the data source enables create, update, and delete. Apex "can't execute standard insert(), update(), or create() operations on external objects"; it uses `Database.insertAsync()` and related methods (or `insertImmediate()` for portal users), and `BackgroundOperation` records show job status. Writes from the UI and API are synchronous.

---

## Common Patterns

### Reference Data Lookup Pattern

**When to use:** Users need current ERP or legacy-system facts inside Salesforce without nightly copy jobs.

**How it works:** Expose the external entity as an External Object, keep queries narrow, and present the data where it supports decisions rather than where it drives heavy automation.

**Why not the alternative:** Full replication adds ETL cost and data-drift problems when users mainly need read access.

### Hybrid Pattern

**When to use:** Most data can stay external, but a hot subset or summary must behave like native Salesforce data.

**How it works:** Use Salesforce Connect for the broad virtual surface and replicate only the narrow subset that needs native workflows or reporting.

### Custom Adapter Escape Hatch

**When to use:** The source system cannot expose the right standard protocol but virtualization is still justified.

**How it works:** Build an adapter only after proving the source-of-truth and operational benefits outweigh the added complexity.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need current external data with minimal replication | Salesforce Connect | Virtual access fits the requirement |
| Need native automation, heavy reporting, and low-latency record behavior | Replicate into Salesforce | Users are really asking for local data behavior |
| Source exposes OData cleanly | OData adapter | Lowest-friction standard option |
| Source cannot expose a supported standard but virtualization is still justified | Custom adapter | Use only when the value outweighs added build and support cost |

---


## Recommended Workflow

1. Confirm the source of truth stays external and record the latency and availability budget; if users really need native automation or deep reporting, recommend replication instead.
2. Inventory every query the pages, reports, and code will run, and check each one against the SOQL limits table above.
3. Pick the adapter and set the data source options: Request Row Counts if anything uses `COUNT()` or batch Apex, Server Driven Pagination for large result sets, `isWritable` only when writes are required.
4. Model relationships: indirect lookups on a parent field that is External ID and unique, external lookups on the external object's External ID.
5. Build Apex against the asynchronous write methods, mock queries with `Test.createSoqlStub`, and use dynamic SOQL in custom adapter tests. Deployable files are in [`references/metadata-examples.md`](references/metadata-examples.md).
6. Run `python3 skills/integration/salesforce-connect-external-objects/scripts/check_salesforce_connect_external_objects.py --manifest-dir force-app/main/default` and fix every ERROR.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Source-of-truth ownership is explicit and still belongs outside Salesforce.
- [ ] Adapter choice is justified by protocol and operational reality.
- [ ] Page and query design respect latency and external availability.
- [ ] Use cases that need native automation or deep reporting are challenged.
- [ ] Relationships and query limits are tested with realistic volumes.
- [ ] Reporting expectations are validated before the project promises native parity.

---

## Salesforce-Specific Gotchas

One-line summaries; the full entries are in [`references/gotchas.md`](references/gotchas.md).

| Gotcha | Short form |
|---|---|
| Triggers and Apex managed sharing | Not available on external objects; only change event triggers for OData 4.0 |
| Apex DML | Use `insertAsync` / `updateAsync` / `deleteAsync` or the `Immediate` variants, not plain DML |
| Unsupported SOQL | Aggregates other than `COUNT()`, `LIKE`, `WITH`, and others fail |
| Batch Apex | Query locator needs Request Row Counts; iterable batches store external rows in Salesforce while running |
| External ID values | Salesforce may store them; never use sensitive data |
| Custom adapter edits | Resave the Provider class after changing the Connection class |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Virtual-data decision | Recommendation for Salesforce Connect versus replication |
| External object review | Findings on adapter fit, performance expectations, and platform limitations |
| Hybrid architecture pattern | Guidance for when only a subset should be replicated |

---

## Related Skills

- `integration/graphql-api-patterns` - use when the real question is client-side query shaping rather than external-data virtualization.
- `data/roll-up-summary-alternatives` - use when the main gap is summary behavior over related data, not where that data is sourced.
- `integration/oauth-flows-and-connected-apps` - use when authentication to the external platform is the main blocker.
