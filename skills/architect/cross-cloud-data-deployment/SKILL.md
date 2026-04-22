---
name: cross-cloud-data-deployment
description: "Cross-cloud data deployment: designing the data handoff when an implementation spans Sales Cloud, Service Cloud, Marketing Cloud, Data Cloud, Commerce Cloud. Shared keys, identity resolution, sync vs event, CDC, Data Cloud as hub. NOT for single-cloud data model design (use sales-cloud-core-setup or service-cloud-core-setup). NOT for integration pattern selection (use integration-pattern-selection decision tree)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Reliability
  - Security
tags:
  - cross-cloud
  - data-cloud
  - identity-resolution
  - cdc
  - marketing-cloud
  - data-model
  - deployment
triggers:
  - "how do we share customer data between sales cloud and marketing cloud"
  - "data cloud as hub for cross-cloud customer identity"
  - "identity resolution across salesforce clouds"
  - "cdc change data capture for cross cloud sync"
  - "sales service commerce cloud data handoff architecture"
  - "how to deploy shared objects across multiple salesforce clouds"
inputs:
  - Clouds in scope (Sales, Service, Marketing, Commerce, Data Cloud, Industries)
  - Shared entities (Customer, Account, Product, Order, Case)
  - Data flow direction (one-way, two-way, hub-and-spoke)
  - SLA and consistency requirements per flow
outputs:
  - Cross-cloud data topology diagram
  - Shared-key and identity-resolution strategy
  - Sync vs event decision per entity
  - Deployment ordering for shared metadata
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Cross-Cloud Data Deployment

Activate when an implementation spans multiple Salesforce clouds (Sales, Service, Marketing, Commerce, Data Cloud, Industries) and data must be consistent across them. Cross-cloud is less about "how do we integrate?" and more about "who owns which field, and how does the truth propagate?"

## Before Starting

- **Identify the system of record per entity.** Customer in Sales Cloud or Data Cloud? Product in Commerce or PIM? Case in Service or Industries? Write it down. Ambiguity here breaks everything downstream.
- **Draw the flows BEFORE picking tech.** A whiteboard diagram of data flowing between clouds is the artifact that drives integration selection, not the other way around.
- **Establish the shared key strategy early.** External IDs, Person IDs, Account IDs — whichever key ties clouds together must be chosen before data model finalization.

## Core Concepts

### Data Cloud as the hub

Data Cloud ingests from Sales / Service / Commerce / Marketing, performs identity resolution, builds a unified profile, and exposes back via Calculated Insights, Activations, and Zero Copy. It becomes the cross-cloud customer brain.

### Identity resolution

Matching rules (deterministic or probabilistic) collapse multiple Contact / Lead / Customer records across clouds into a Unified Individual. The rule set is per-org and evolves.

### Change Data Capture (CDC) vs Platform Events

CDC emits record-level field changes automatically; Platform Events are bespoke business events. For cross-cloud sync of CRUD, prefer CDC; for domain events (Order Shipped, Case Escalated), prefer Platform Events.

### Shared keys

External ID fields on each cloud point to a common reference. Pattern: every record carries the same `Global_Customer_Id__c` with External ID + Unique. Upserts become trivially safe.

## Common Patterns

### Pattern: Sales + Service co-resident; Marketing via Data Cloud

Sales and Service share one org (one Account, Contact). Data Cloud ingests from the org and from Marketing Cloud; Marketing activates segments back. Clean.

### Pattern: Sales + Commerce with Order propagation

Commerce creates Orders; OMS / Sales Cloud handles service. Use Platform Events for "Order Placed" rather than REST sync — decouples cadence.

### Pattern: Data Cloud Zero Copy for analytics, not operational

Zero Copy (Snowflake, BigQuery, Databricks) for analytics without duplication. NOT for operational sync — latency and semantics differ.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Shared customer identity across 3+ clouds | Data Cloud as hub | Native identity resolution |
| Sales ↔ Service single-org | Native relationships, no integration | Same org |
| Marketing engagement → Sales | Marketing Cloud Connect or Data Cloud Activation | Supported paths |
| Commerce order → Service case | Platform Events | Decoupled cadence |
| Analytics across clouds | Data Cloud + Zero Copy | No duplication |

## Recommended Workflow

1. Inventory the clouds in scope and the shared entities each owns.
2. Assign system-of-record per entity; document ownership explicitly.
3. Select shared keys; add External ID + Unique fields on each cloud.
4. Decide sync vs event per flow; pick CDC, Platform Events, Marketing Cloud Connect, or Data Cloud.
5. Design identity resolution rules in Data Cloud; validate with a two-cloud sample.
6. Plan the deployment order: data model first (shared keys), then integration, then activation.
7. Build an end-to-end smoke test from creation in cloud-A to arrival in cloud-B.

## Review Checklist

- [ ] System-of-record documented for every shared entity
- [ ] External ID + Unique present on every cross-cloud object
- [ ] Sync vs event decision made per flow
- [ ] Data Cloud identity resolution rules tested
- [ ] Deployment ordering respects key dependencies
- [ ] Error handling and replay designed for every flow
- [ ] Cross-cloud reporting strategy addressed

## Salesforce-Specific Gotchas

1. **Marketing Cloud Connect has its own identity model (Subscriber Key).** Mapping Subscriber Key to Data Cloud Unified Individual requires explicit rules.
2. **Data Cloud is not real-time for all flows.** Streaming ingestion + CI refresh can mean minutes of lag; do not architect operational flows around Data Cloud latency.
3. **CDC has order guarantees per record but not across records.** Cross-object consistency must come from a different mechanism.

## Output Artifacts

| Artifact | Description |
|---|---|
| Cross-cloud topology diagram | Clouds, flows, shared keys |
| System-of-record matrix | Entity × cloud with SoR marked |
| Shared key inventory | External IDs across clouds |
| Deployment ordering plan | Data model → integration → activation |

## Related Skills

- `architect/multi-cloud-architecture` — multi-cloud org strategy
- `integration/integration-pattern-selection` — mechanism choice
- `data/data-cloud-foundation` — Data Cloud specifics
