---
name: industries-energy-utilities-setup
description: "Operational setup guide for Salesforce Energy and Utilities Cloud: license activation, permission sets, industry-specific object configuration (ServicePoint, Meter, MeterReading, Consumption, ServiceAccount, ServiceContract, RatePlan), CIS/billing system integration, and service order management. NOT for generic admin setup, NOT for reading or querying the E&U data model schema (use architect/industries-data-model for that)."
category: admin
salesforce-version: "Spring '26+"
well-architected-pillars:
  - Reliability
  - Security
  - Operational Excellence
triggers:
  - "How do I configure service points in Energy and Utilities Cloud"
  - "setting up meter management and rate plans for utilities in Salesforce"
  - "Energy and Utilities Cloud permission sets and license activation steps"
  - "rate plan assignment not working in E&U Cloud — CIS integration incomplete"
  - "service order management setup for energy utility provider in Salesforce"
tags:
  - energy-utilities
  - industries-cloud
  - service-point
  - meter-management
  - rate-plan
  - service-order
  - cis-integration
  - admin-setup
inputs:
  - "E&U Cloud license edition provisioned in the org"
  - "External CIS or billing system details (vendor, integration type, sync frequency)"
  - "Market type: regulated utility vs competitive/deregulated market"
  - "Service types in scope (electricity, gas, water)"
  - "Meter types and usage data volume estimates"
outputs:
  - "Validated E&U Cloud setup checklist (license, permission sets, objects, integration)"
  - "ServicePoint and Meter configuration guidance"
  - "Rate plan assignment sequence and dependency map"
  - "Service order workflow configuration"
  - "CIS integration readiness assessment"
dependencies:
  - industries-data-model
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Industries Energy Utilities Setup

This skill activates when a practitioner needs to configure the operational foundation of Salesforce Energy and Utilities (E&U) Cloud: enabling the license, assigning permission sets, setting up industry-specific objects (ServicePoint, Meter, MeterReading, Consumption, ServiceAccount, ServiceContract, RatePlan), connecting the external Customer Information System (CIS) or billing platform, and configuring service order management workflows. It does not cover schema reference queries or data model architecture — use `architect/industries-data-model` for that.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm that the Energy and Utilities Cloud license is provisioned in the org — Setup > Installed Packages must show the E&U managed package. All industry-specific objects (ServicePoint, Meter, RatePlan, ServiceContract) are unavailable without this license.
- Identify the market type: regulated utility markets and competitive/deregulated markets have different service point configuration rules, rate plan assignment logic, and integration requirements. Applying regulated-market setup steps in a competitive-market org (or vice versa) produces silently incorrect billing data.
- The most common wrong assumption is that standard Salesforce admin setup patterns (user provisioning, record types, page layouts) transfer directly to E&U Cloud without modification. E&U Cloud requires specific permission sets from the managed package and industry-specific object hierarchies that do not map 1:1 to standard Account/Asset/Contract objects.

---

## Core Concepts

### Industry-Specific Object Hierarchy

Energy and Utilities Cloud adds a set of standard objects on top of core Salesforce Account and Asset objects. These objects require the E&U Cloud license and are not available in standard Salesforce editions:

- **ServicePoint** — the physical metering location where energy or utility service is delivered or measured. A ServicePoint has a geographic address, a service type (electricity, gas, water), and a market segment. It is distinct from Account (the customer) and from Asset (equipment). One Account may have multiple ServicePoints (e.g., a commercial customer with multiple meters across a campus).
- **Meter** — the physical or virtual metering device installed at a ServicePoint. A ServicePoint can have one or more Meters over its lifetime (meter replacements are modeled as new Meter records linked to the same ServicePoint).
- **MeterReading** — an individual usage reading taken from a Meter at a point in time. MeterReadings are the raw inputs used to calculate consumption.
- **Consumption** — a calculated usage record derived from one or more MeterReadings over a billing period. Consumption records are what rate plans operate against to generate charges.
- **ServiceAccount** — in E&U Cloud, this is an Account record with the Service Account record type representing a utility account associated with one or more ServicePoints. It is distinct from a commercial or residential billing account.
- **ServiceContract** — the legal agreement between the utility provider and the customer for service at one or more ServicePoints. It carries the effective dates, service type, and links to the applicable RatePlan.
- **RatePlan** — the tariff or pricing structure that determines how charges are calculated from Consumption records. RatePlan assignment is not standalone — it depends on service type, market segment (regulated or competitive), and the external CIS or billing system integration.

### License and Permission Set Activation Sequence

Setting up E&U Cloud requires completing steps in the correct order. Skipping or reordering these steps causes objects to appear missing or inaccessible:

1. Verify the E&U Cloud managed package is installed (Setup > Installed Packages).
2. Assign the Energy and Utilities Cloud permission set license to users who need access to industry objects.
3. Assign the appropriate feature permission sets from the managed package (e.g., Energy and Utilities Cloud Standard User, Energy and Utilities Cloud Admin).
4. Configure sharing settings and OWDs for industry objects — ServicePoint, ServiceContract, and RatePlan each have their own OWD that must be reviewed separately from standard object OWDs.
5. Validate that the industry objects are visible in the Object Manager before proceeding to data configuration.

### Rate Plan Assignment Dependencies

Rate plan assignment is the most failure-prone area of E&U Cloud setup. A RatePlan is not a standalone configuration — it is the intersection of:

- **Service type** (electricity, gas, water) — a RatePlan is specific to a service type and cannot be applied across service types.
- **Market segment** (residential, commercial, industrial) — regulated utility tariffs are often legally mandated by market segment; competitive market plans may have more flexibility.
- **External CIS/billing system sync** — in most E&U Cloud implementations, the external Customer Information System (CIS) or billing platform is the authoritative source for rate plan definitions. RatePlans are synchronized from the CIS into Salesforce, not created natively in Salesforce. If the CIS integration is incomplete or misconfigured, rate plan records either do not exist in Salesforce or carry stale data, which silently breaks billing cycle triggers downstream.

### Regulated vs Competitive Market Configuration

Service point configuration behaves differently depending on market type:

- **Regulated markets** — the utility is the sole provider; rate plans are set by regulatory mandate. ServicePoint market segment must match the regulated tariff class. RatePlan is typically assigned automatically based on ServicePoint attributes and cannot be customer-chosen. Switching a ServicePoint to a different rate plan requires a service order and may require regulatory approval.
- **Competitive/deregulated markets** — multiple energy retailers may serve the same physical ServicePoint. The ServicePoint carries a Distribution System Operator (DSO) identifier, a retailer identifier, and the contracted RatePlan from the chosen retailer. Rate plan switches are initiated by customer action and require a retailer change service order.

Applying regulated-market setup logic in a competitive-market org (or vice versa) produces incorrect ServicePoint record structures and rate plan assignment failures that may not surface until billing cycles run.

---

## Common Patterns

### Service Point Configuration with Meter and Rate Plan

**When to use:** Initial provisioning of a new customer service location, or migration of an existing customer from a legacy CIS into E&U Cloud.

**How it works:**

1. Create or verify the Account record for the customer (or look up the existing Account).
2. Create the ServicePoint record linked to the Account, specifying service type, market segment, and address. Ensure `MarketSegment` matches the tariff class in the CIS.
3. Create a Meter record linked to the ServicePoint. Set the meter type (AMI, AMR, analog) and status (Active).
4. Look up the applicable RatePlan record (synced from CIS) matching the ServicePoint service type and market segment. Do not create a new RatePlan record manually unless specifically required — CIS is the authoritative source.
5. Create the ServiceContract linking the Account to the ServicePoint, with the effective date and the looked-up RatePlan.
6. Validate the ServiceContract status transitions to Active.

**Why not the alternative:** Creating the ServiceContract before the ServicePoint or before the RatePlan sync is complete causes lookup failures and leaves the ServiceContract in Draft status indefinitely, with no obvious error message.

### Service Order Management for Rate Plan Changes

**When to use:** A customer requests a rate plan change, a new service connection, or a service disconnection.

**How it works:**

Service orders in E&U Cloud are managed through the Work Order or CustomerOrder object (depending on the E&U Cloud edition and OmniStudio configuration). The standard workflow is:

1. Create a service order record of the appropriate type (Connect, Disconnect, Rate Change).
2. Associate the service order with the ServicePoint and the customer's Account.
3. For a rate plan change: validate that the target RatePlan exists in Salesforce and matches the CIS-synchronized plan code. Do not proceed if the CIS record is absent.
4. Execute the service order — this triggers field service dispatch or an automated CIS API call depending on integration design.
5. After completion, update the ServiceContract with the new RatePlan effective date and verify the Consumption calculation basis resets to the new plan.

**Why not the alternative:** Updating the RatePlan directly on the ServiceContract without a service order bypasses audit trail requirements, skips the CIS synchronization step, and may violate regulatory compliance requirements in regulated market implementations.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org shows ServicePoint as unavailable | Verify E&U Cloud license and permission sets are correctly assigned | Industry objects require both a license and specific managed package permission sets |
| Rate plan assignment silently failing | Confirm CIS integration is active and RatePlan records are present in Salesforce | RatePlan is CIS-authoritative; Salesforce cannot assign plans that do not exist as synchronized records |
| Need to configure a new service location | Create ServicePoint first, then Meter, then ServiceContract with RatePlan | Object hierarchy requires ServicePoint before dependent records |
| Regulated vs competitive market setup | Confirm market type before configuring ServicePoint market segment | Market type determines whether rate plan assignment is automatic or customer-driven |
| Service order not progressing past Draft | Verify ServicePoint and RatePlan records are complete and linked | Incomplete lookups block service order status transitions |
| Implementing in a regulated-market utility | Treat RatePlan as read-only in Salesforce (CIS-owned) | Regulated tariffs are legally mandated; Salesforce should reflect, not override, CIS data |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Confirm E&U Cloud license is installed and activated — check Setup > Installed Packages for the Energy and Utilities Cloud managed package before any configuration work begins. If missing, stop and engage Salesforce licensing support.
2. Assign the E&U Cloud permission set license and the appropriate feature permission sets (Standard User, Admin) to all users who require access to industry objects — validate by checking that ServicePoint and Meter are accessible in the Object Manager.
3. Identify the market type (regulated or competitive) and configure ServicePoint object settings, market segment picklist values, and OWD sharing rules to match the market type requirements.
4. Validate that the CIS or billing system integration is functional and that RatePlan records are being synchronized correctly into Salesforce — query the RatePlan object and verify record counts match expected tariff classes from the CIS.
5. Configure ServicePoints for each service location, linking them to the correct Account, service type, and market segment — create associated Meter records for each ServicePoint.
6. Create ServiceContracts linking Accounts to ServicePoints with the applicable CIS-synchronized RatePlan — verify each ServiceContract reaches Active status before proceeding.
7. Configure and test service order workflows (connect, disconnect, rate change) against a sandbox environment before deploying to production, confirming that service orders correctly update ServiceContracts and trigger CIS synchronization.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] E&U Cloud managed package is confirmed installed in the target org
- [ ] E&U Cloud permission set license and feature permission sets are assigned to all relevant users
- [ ] Market type (regulated vs competitive) is confirmed and ServicePoint market segment values reflect that classification
- [ ] CIS/billing integration is active and RatePlan records are synchronized and present in Salesforce
- [ ] Each ServicePoint has at least one active Meter record
- [ ] Each ServiceContract references a valid, CIS-synchronized RatePlan — no manually created RatePlan records unless explicitly documented
- [ ] Service order workflows tested in sandbox for connect, disconnect, and rate change scenarios
- [ ] OWD sharing settings for ServicePoint, ServiceContract, and RatePlan reviewed and set appropriately

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Incomplete CIS integration silently breaks billing cycles** — If the RatePlan records are not synchronized from the external CIS, ServiceContracts can be created with null or stale rate plan references. No immediate error fires, but billing cycle calculations produce zero charges or incorrect charges when the Consumption records are processed. This failure surfaces days or weeks later when billing runs, not at setup time.

2. **ServicePoint is not Account, not Asset** — Practitioners familiar with standard Salesforce often map service locations to Account address fields or to Asset records. ServicePoint is a distinct object with its own location, service type, and market segment fields. Storing service location data on Account or Asset instead of ServicePoint breaks all E&U Cloud native workflows, reporting, and OmniStudio integrations that expect the ServicePoint object.

3. **Permission sets from the managed package are required, not optional** — Standard Salesforce permission sets or custom permission sets with Object CRUD permissions do NOT grant access to E&U Cloud industry objects. The managed package deploys its own permission sets. Users without these specific permission sets see object-not-found errors even after a System Administrator assigns full CRUD on the objects via a custom permission set.

4. **Regulated vs competitive market rules are not interchangeable** — Regulated-market orgs require ServicePoint MarketSegment values that match legally mandated tariff classes. Competitive-market orgs require retailer and Distribution System Operator (DSO) identifiers on the ServicePoint. Applying the wrong market type configuration does not produce an error — it produces a setup that appears complete but assigns rate plans incorrectly or fails service order workflows at runtime.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| E&U Cloud setup checklist | Validated sequence of license, permission set, object, and integration configuration steps |
| ServicePoint configuration record | Correctly structured ServicePoint with service type, market segment, and Account link |
| CIS integration readiness assessment | Verified presence and currency of CIS-synchronized RatePlan records in Salesforce |
| ServiceContract configuration | Active ServiceContract linking Account, ServicePoint, and CIS-synchronized RatePlan |
| Service order test results | Sandbox validation results for connect, disconnect, and rate change service order workflows |

---

## Related Skills

- architect/industries-data-model — schema reference for E&U Cloud objects (ServicePoint, ServiceContract) and how they relate to the broader Industries data model; use this when you need to understand object relationships rather than operational setup steps
