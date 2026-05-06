---
name: data-virtualization-patterns
description: "Choosing between virtualizing external data into Salesforce (External Objects via Salesforce Connect / OData / cross-org adapter) and replicating it (Bulk API ingest into a custom object). Covers OData 2.0 / 4.0 adapter mechanics, indirect lookup keys, the per-callout limits and the per-transaction callout cap, what External Objects cannot do (no triggers, no validation rules, no workflow / flow record-triggers, no reports beyond joined-style limits, limited search), and the Salesforce-to-Salesforce cross-org variant. NOT for plain REST callouts (see integration/named-credential-patterns), NOT for ETL / one-time data migration (see data/data-migration-strategy)."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Security
  - Reliability
triggers:
  - "salesforce connect external object odata adapter"
  - "external object trigger validation rule not supported"
  - "indirect lookup external id virtualize cross org"
  - "virtualize vs replicate data salesforce decision"
  - "data virtualization callout limit external object"
  - "salesforce-to-salesforce cross org adapter external object"
  - "high data volume don't replicate external object"
tags:
  - salesforce-connect
  - external-objects
  - odata
  - virtualization
  - cross-org
inputs:
  - "Source system (the data lives where) and protocol it speaks (OData, REST, cross-org)"
  - "Read / write requirements (read-only virtualization is much simpler)"
  - "Latency tolerance (virtualization adds round-trip latency on every page render)"
outputs:
  - "Virtualize-vs-replicate decision with cited tradeoff"
  - "External Object configuration (adapter type, indirect lookup, name field, scope)"
  - "Limit budget (callouts per transaction, page size, per-row constraints)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-05
---

# Data Virtualization Patterns

Salesforce Connect lets you expose data that lives outside Salesforce
as **External Objects** — sObject-like records that look native in
the UI, in SOQL, and in Apex, but whose rows are fetched on demand
from a remote source. The data never lands in Salesforce storage.

The promise is appealing: no ETL, no replication lag, no extra
storage cost, single source of truth. The reality has sharp edges.
External Objects are not full sObjects. Many capabilities customers
expect from a custom object — triggers, validation rules,
record-triggered flows, formula fields referencing other records,
roll-up summaries, full-text search, audit trails — are absent or
significantly restricted. Practitioners who skip the limits review
discover the gaps in production.

This skill is a decision and configuration guide. It helps you pick
**virtualize vs replicate** for a specific data set, then walks you
through the External Object configuration that avoids the most
common production problems.

## When virtualization is the right answer

Virtualization is appropriate when all of the following hold:

- The data is read-mostly from Salesforce's perspective. Writes back
  to the source are possible (OData 4.0 with writable adapter), but
  introduce more failure modes.
- The dataset is large enough that replicating it is expensive in
  storage cost or sync complexity, and the remote source is the
  authoritative system of record.
- Salesforce automation requirements are limited to display and
  cross-object reference (a Contact -> ExternalAccount lookup), not
  triggers, validation, or record-triggered flows on the external
  rows.
- The remote source can serve a request within the page-load budget
  (a few hundred milliseconds) for the typical row counts a Lightning
  page or list view will request.

When the workload is write-heavy, automation-heavy, or latency-
sensitive, replication into a regular custom object is the right
call — even with the storage and freshness tradeoffs.

## Adapter choices

Salesforce Connect ships several adapters; pick by the source's
protocol and the cross-org pattern needed.

| Adapter | Use when |
|---|---|
| OData 2.0 | Source exposes an OData 2.0 endpoint; legacy partners |
| OData 4.0 | Source exposes OData 4.0; preferred for new builds; supports writes |
| Cross-Org | Source is another Salesforce org; uses Salesforce-to-Salesforce protocol |
| Custom (Apex) | Source is REST / GraphQL / non-OData; implement `DataSource.Provider` and `DataSource.Connection` |

The Custom (Apex) adapter is the escape hatch but carries the
ownership cost of writing the connector code, handling pagination,
mapping types, and dealing with auth refresh.

## Recommended Workflow

1. **Confirm the use case is read-mostly and automation-light.** Validate that External Object's "no triggers, no record-triggered flows, no validation rules, no roll-up summary" limits do not block requirements. If they do, replicate instead.
2. **Pick the adapter.** OData 4.0 if the source can speak it; cross-org for org-to-org; custom Apex for everything else. Avoid OData 2.0 for new builds unless the legacy partner blocks an upgrade.
3. **Define indirect lookup keys.** External Objects do not have native AccountId joins; you use Indirect Lookups that join on an External Id field. Confirm the External Id is unique and indexed on the Salesforce-side parent.
4. **Size the callout budget.** Each list view, related list, or page render that touches an External Object issues a callout. The per-transaction callout cap (100 sync) and per-24-hour external-object callout caps matter at scale; do not assume the limits are unlimited.
5. **Test the negative paths.** Source down, source slow, source returns malformed data, auth token expired. The platform's behavior on each differs — slow source produces page-load timeouts, down source produces blank related lists, malformed data fails silently.
6. **Document the practitioner contract.** Make explicit in admin / dev documentation that this object cannot have triggers, validation, or record-triggered flows. Without this, the next admin will try to add one and be confused when it is not in the picker.

## What This Skill Does Not Cover

| Topic | See instead |
|---|---|
| Plain REST callouts (no External Object) | `integration/named-credential-patterns` |
| One-time ETL / data migration | `data/data-migration-strategy` |
| Big Objects (append-only, async query) | `data/big-objects-patterns` |
| Change Data Capture out of Salesforce | `integration/change-data-capture-patterns` |
