---
name: revenue-cloud-architecture
description: "Architecting on Salesforce Revenue Cloud (Revenue Lifecycle Management — RLM, the successor to CPQ-Plus + Billing). Covers the five RLM domains (Product Catalog & Pricing, Transaction Management, Contract Lifecycle Management, Order-to-Cash, Billing), the canonical data model (Product2 / PricebookEntry / Quote / Order / OrderItem / Contract / Asset / BillingSchedule / Invoice / LegalEntity), multi-entity scoping via LegalEntity, the RLM ↔ ERP integration patterns (CDC + MuleSoft preferred over point-to-point trigger callouts), and the disambiguation between native RLM and the legacy `blng__` Salesforce Billing managed package and `SBQQ__` CPQ classic. NOT for declarative CPQ classic config (see omnistudio/cpq-classic-config), NOT for Subscription Management billing patterns predating RLM (see architect/cpq-architecture-patterns)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "revenue cloud rlm revenue lifecycle management architecture"
  - "product catalog price book quote order contract asset rlm"
  - "rlm billing schedule invoice legal entity"
  - "rlm vs cpq classic vs salesforce billing managed package"
  - "rlm to erp integration cdc platform events"
  - "multi entity legal entity invoice scoping"
  - "transaction management order data model"
tags:
  - revenue-cloud
  - rlm
  - billing
  - quote-to-cash
  - legal-entity
inputs:
  - "Whether the org is on RLM, CPQ classic (`SBQQ__`), Salesforce Billing (`blng__`), or a hybrid"
  - "ERP system on the receiving end of order / invoice data and its preferred integration shape"
  - "Multi-entity scope: how many LegalEntity rows, accounting periods, tax jurisdictions"
outputs:
  - "RLM domain map with canonical objects per domain"
  - "RLM <-> ERP integration pattern (CDC, Platform Event, queueable callout)"
  - "Multi-entity setup checklist with LegalEntity scoping"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-05
---

# Revenue Cloud Architecture

"Revenue Cloud" is Salesforce's umbrella for quote-to-cash. The
modern stack is **Revenue Lifecycle Management (RLM)** — a native,
five-domain architecture that replaces the prior generation built on
the CPQ classic managed package (`SBQQ__` namespace) and the
Salesforce Billing managed package (`blng__` namespace). Many orgs
run a hybrid because RLM's adoption has been gradual.

This skill is an architecture reference. It maps the RLM domains to
their canonical objects, names the integration patterns Salesforce
Architects publishes for RLM <-> ERP, and disambiguates RLM from the
legacy products it replaces (a frequent LLM confusion).

## The five RLM domains

RLM organizes the quote-to-cash lifecycle into five composable
domains. Each owns a set of objects and a slice of behavior.

| Domain | Owns | Key Objects |
|---|---|---|
| Product Catalog & Pricing | Catalog, configurations, pricing rules | `Product2`, `Pricebook2`, `PricebookEntry`, attribute / category metadata |
| Transaction Management | Quote, configure-price-quote, order capture | `Quote`, `QuoteLineItem`, `Order`, `OrderItem` |
| Contract Lifecycle Management | Contracts, amendments, renewals | `Contract`, `ContractLineItem` |
| Order-to-Cash | Order fulfillment, asset lifecycle | `Order`, `OrderItem`, `Asset`, `AssetStatePeriod` |
| Billing | Invoicing, revenue, payments, accounting | `BillingSchedule`, `Invoice`, `InvoiceLine`, `LegalEntity`, `AccountingPeriod` |

The objects are not unique to one domain — `Order` participates in
Transaction Management (capture) and Order-to-Cash (fulfillment).
The five-domain map is conceptual. It guides which team owns what
and where to put extension logic.

## Multi-entity: the LegalEntity object

`LegalEntity` is the linchpin for multi-subsidiary setups. Invoices,
accounting periods, payment terms, and tax-treatment metadata can be
scoped per `LegalEntity`. One Salesforce org can run several legal
entities concurrently.

The risk: entity proliferation. Without governance, every regional
finance team wants a separate `LegalEntity`, and tax / accounting
configuration multiplies. Architect default: start with the smallest
`LegalEntity` count that satisfies legal / accounting separation,
expand only with finance approval.

## RLM <-> ERP integration patterns

The reference pattern published by Salesforce Architects is
event-driven, not point-to-point. The recipe:

- **Outbound from Salesforce to ERP.** Use **Change Data Capture**
  on Order / OrderItem / Invoice consumed via CometD, MuleSoft, or
  a Pub/Sub API client. Or publish a **Platform Event** from a
  trigger and have the ERP subscribe.
- **Outbound via Apex callout.** Trigger-time callouts are blocked
  (synchronous callouts from triggers aren't allowed). Use
  `@future(callout=true)` or Queueable with `Database.AllowsCallouts`
  for fire-and-forget; for transactional integration, the
  event-driven path is preferred.
- **Inbound from ERP.** REST or Bulk API loads, gated through
  `LegalEntity` scoping and validation.

The anti-pattern: writing a synchronous Apex trigger that calls the
ERP REST API on every Order insert. It cannot work synchronously
(blocked) and even when async it tightly couples Salesforce
deployments to ERP availability.

## Disambiguating RLM, CPQ classic, and Salesforce Billing

| Term | Meaning |
|---|---|
| **Revenue Cloud** | Marketing umbrella; refers to RLM in modern docs |
| **RLM** (Revenue Lifecycle Management) | Native quote-to-cash, no managed package |
| **CPQ classic** | `SBQQ__` managed package; the predecessor to RLM Transaction Management |
| **Salesforce Billing** | `blng__` managed package; the predecessor to RLM Billing |
| **Subscription Management** | Older subscription billing product, distinct from both above |

LLMs frequently conflate RLM Billing with the `blng__` package. They
are different products with different objects, different APIs, and
different upgrade paths. Confirm namespace before designing.

## Recommended Workflow

1. **Confirm which products are licensed and active.** RLM, CPQ classic, Salesforce Billing, and Subscription Management can coexist. Discover the actual managed-package state via Setup -> Installed Packages.
2. **Map the business process to the five RLM domains.** Identify which domain owns which step. This determines which objects to extend and which team is responsible.
3. **Plan multi-entity scoping early.** Decide LegalEntity count and granularity before any data model extension. Adding entities mid-flight is disruptive.
4. **Choose ERP integration shape per direction.** Outbound preferred via CDC / Platform Events. Inbound via REST / Bulk API gated through LegalEntity validation. Document the contract per direction.
5. **Avoid synchronous trigger callouts.** They are blocked by the platform; the alternative is `@future(callout=true)` or Queueable, but the architect-recommended pattern is event-driven.
6. **Stand up sandbox tests for each integration path.** Failure modes (ERP down, slow, malformed response) need explicit handling. Replay-from-CDC checkpointing is the durable pattern.
7. **Document the namespace decision.** Make explicit in the architecture record whether the integration targets native RLM objects, `SBQQ__` CPQ classic, `blng__` Salesforce Billing, or a hybrid. This prevents downstream confusion for the next team.

## What This Skill Does Not Cover

| Topic | See instead |
|---|---|
| Declarative CPQ classic configuration | `omnistudio/cpq-classic-config` |
| CPQ-classic specific quoting patterns | `architect/cpq-architecture-patterns` |
| Subscription Management (legacy) billing patterns | `architect/cpq-architecture-patterns` |
| ERP-side connector implementation | `integration/named-credential-patterns` |
