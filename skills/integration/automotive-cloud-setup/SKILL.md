---
name: automotive-cloud-setup
description: "Use this skill when setting up or extending Salesforce Automotive Cloud — including the Vehicle / VehicleDefinition data model, dealer-OEM relationship modeling via AccountAccountRelation, ActionableEvent orchestration for service campaigns and recalls, FinancialAccount lifecycle for retail-credit deals, and DriverQualification / WarrantyTerm extensions. Triggers on: Automotive Cloud setup, Salesforce Automotive Cloud data model, Vehicle vs VehicleDefinition, dealer hierarchy AccountAccountRelation, Automotive Cloud actionable events, recall campaign Salesforce. NOT for general Sales Cloud opportunity work on a vehicle product (use standard Opportunity), NOT for Manufacturing Cloud sales agreements (use manufacturing-cloud-setup), NOT for Field Service vehicle inventory (use FSL skills)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
tags:
  - automotive-cloud
  - vehicle
  - vehicle-definition
  - dealer-management
  - actionable-events
  - financial-account
  - recall-campaign
  - driver-qualification
  - warranty
  - industry-cloud
inputs:
  - "Automotive Cloud license enabled on the org"
  - "Dealer / OEM organizational structure (single tenant vs multi-dealer hierarchy)"
  - "Source system providing VIN-keyed vehicle data (DMS, telematics, OEM inventory feed)"
  - "Lifecycle events tracked in scope: sales, service, recall, warranty, financial"
outputs:
  - "Vehicle and VehicleDefinition data model populated with required relationships"
  - "Dealer-OEM hierarchy modeled with AccountAccountRelation and partner roles"
  - "ActionableEvent / ActionableEventType configuration for recall and service campaigns"
  - "FinancialAccount lifecycle wired to Opportunity / Order for retail credit deals"
triggers:
  - "configuring Salesforce Automotive Cloud objects from scratch"
  - "modeling dealer-to-OEM hierarchy in Automotive Cloud"
  - "setting up recall or service campaign orchestration with ActionableEvent"
  - "Vehicle vs VehicleDefinition: which to use when"
  - "Automotive Cloud FinancialAccount setup for retail credit deals"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-03
---

# Automotive Cloud Setup

This skill activates when a practitioner is setting up Salesforce Automotive Cloud — the industry cloud that adds a VIN-centric data model, dealer hierarchy patterns, lifecycle event orchestration, and retail-credit financial objects on top of Sales / Service Cloud. It covers the Vehicle vs VehicleDefinition split, dealer-OEM relationship modeling, ActionableEvent orchestration, and FinancialAccount lifecycle. It does NOT cover Field Service mobile inventory, Manufacturing Cloud forecasting, or generic Sales Cloud opportunity flows that happen to reference a vehicle.

---

## Before Starting

Gather this context before working in this domain:

- Confirm the org has the Automotive Cloud license — the skill's standard objects (`Vehicle`, `VehicleDefinition`, `DriverQualification`, `WarrantyTerm`, the `Scope3CrbnFtprnt` family, etc.) are gated behind that license and will not appear in Object Manager otherwise.
- Identify the source-of-truth for VIN data. In most installations the OEM inventory feed or a Dealer Management System (DMS) is upstream — Automotive Cloud is rarely the system of record for vehicle build data.
- Map the dealer org structure on paper before configuring `AccountAccountRelation`. Multi-tenant OEM-dealer-customer hierarchies are difficult to refactor once relationship records exist.
- Identify which lifecycle events ActionableEvent will orchestrate (recalls, service campaigns, warranty notifications). The `ActionableEventType` design happens up-front, not iteratively.

---

## Core Concepts

### Vehicle vs VehicleDefinition

This is the foundational data-model split practitioners get wrong on day one:

**`VehicleDefinition`** — the model/trim/year template ("2026 Ford F-150 Lariat 4x4"). One record per build configuration, shared across many physical vehicles. Owns specifications, MSRP, available options, and `VehDefSearchableField` records used by inventory search.

**`Vehicle`** — the physical, VIN-identified asset. One record per VIN. Points to its `VehicleDefinition` via `VehicleDefinitionId`. Owns the per-instance state: current owner, current dealer, mileage, registration, warranty start date.

Mixing these — for example, putting MSRP on `Vehicle` instead of `VehicleDefinition` — duplicates pricing data across every VIN and breaks model-level reporting. Putting VIN on `VehicleDefinition` collapses the model into a single instance and breaks inventory search.

### Dealer-OEM Hierarchy via AccountAccountRelation

Automotive Cloud uses Account for dealers, OEMs, and customers, but the dealer ↔ OEM relationship is modeled through **`AccountAccountRelation`** rather than the classic `ParentId` field. This is deliberate: a dealer can sell vehicles from multiple OEMs (multi-franchise dealerships are the norm), and a parent account hierarchy is single-valued.

Each `AccountAccountRelation` carries a relationship role (e.g., `Franchisee`, `Distributor`, `Service Partner`) and effective dates. Sharing rules and visibility decisions should reference these relations rather than `ParentId`.

### ActionableEvent for Lifecycle Orchestration

Automotive Cloud ships an event-driven orchestration model for recalls, service campaigns, and other multi-step lifecycle actions:

- **`ActionableEventType`** — the template ("FY26 Q2 Brake Recall"). Defines the orchestration recipe.
- **`ActionableEventTypeDef`** — versioned definition rows attached to the type. Lets the recipe change over time without losing history.
- **`ActionableEventOrchestration`** — the runtime instance attached to a specific Vehicle / Account. Tracks state across the orchestration steps.
- **`ActionableEventSubtype`** — sub-categories within a type, used to fan out the recipe.

This is how a recall campaign reaches every affected VIN, opens a Case at the responsible dealer, and tracks remedy completion — without bespoke automation.

### FinancialAccount for Retail Credit

`FinancialAccount`, `FinancialAccountAddress`, `FinancialAccountBalance`, `FinancialAccountFee` — these objects model the loan / lease / financing tied to a vehicle sale. They are the same objects used by Financial Services Cloud, sharing the data model across the Industries platform. Connect them to the Vehicle (via a junction or custom lookup), to the customer Account, and to the Opportunity that closed the deal.

### DriverQualification and Fleet

`DriverQualification` tracks license, endorsement, and medical-certificate state for fleet drivers. It is paired with `Driver`, `DrivingLicense`, and `Fleet` for commercial/fleet operations. Unused for retail consumer scenarios — only enable when the org actually has fleet customers.

---

## Common Patterns

### Pattern 1: VIN Ingestion from OEM / DMS Feed

**When to use:** Standing up a new dealer org or migrating from a legacy DMS.

**How it works:**

1. Bulk-load `VehicleDefinition` records first — one per model/trim/year, deduplicated on the natural key (Make + Model + ModelYear + Trim).
2. Bulk-load `Vehicle` records, lookup-resolving `VehicleDefinitionId` from the staged definitions. Use external IDs on both objects to make the load idempotent.
3. Populate `VehDefSearchableField` rows for every searchable spec attribute on the definition (this drives inventory UX search).
4. Wire a delta feed (Platform Event or Bulk API 2.0) for ongoing inventory sync — full reload on every run is wasteful at fleet scale.

**Why deduplicate definitions first:** Without a clean definitions table, VIN ingestion produces a definition explosion (one definition per VIN), breaking model-level reporting and inflating storage.

### Pattern 2: Dealer Hierarchy with Multi-Franchise Support

**When to use:** Any org modeling dealers that sell more than one OEM brand.

**How it works:**

1. Create the OEM as an `Account` of record type `OEM` (or equivalent custom record type).
2. Create each Dealer as an `Account` of record type `Dealer`.
3. For each OEM-Dealer pairing, create an `AccountAccountRelation` with role `Franchisee` and effective dates.
4. Build sharing rules and report filters off `AccountAccountRelation`, not `ParentId`.
5. Customer Accounts link to the selling Dealer via a custom lookup, never via `ParentId` (which would break OEM-Dealer hierarchy).

### Pattern 3: Recall Campaign Orchestration

**When to use:** OEM issues a recall affecting a defined VIN range.

**How it works:**

1. Define an `ActionableEventType` for the recall family (e.g., "Brake Component Recall").
2. Create an `ActionableEventTypeDef` for this specific recall instance — the version of the recipe that applies right now.
3. For each affected VIN, generate an `ActionableEventOrchestration` referencing the Vehicle and the type.
4. The orchestration steps notify the customer, open a Case at the assigned dealer, and track remedy completion through the orchestration state.
5. Report on completion rate by querying orchestration state per type.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Multi-franchise dealer (sells multiple OEM brands) | `AccountAccountRelation` per OEM-Dealer pair | `ParentId` is single-valued; can't model multi-franchise |
| Pricing / MSRP / build specs | Fields on `VehicleDefinition` | Belongs to the model template, not the VIN |
| Per-VIN state (mileage, owner, registration) | Fields on `Vehicle` | Belongs to the physical asset |
| Recall affecting a VIN range | `ActionableEventType` + per-VIN `ActionableEventOrchestration` | Built-in orchestration; avoids bespoke trigger code |
| Retail loan / lease tied to a vehicle sale | `FinancialAccount` + `FinancialAccountBalance` + lookup to Vehicle | Industries-shared data model; reuse rather than custom Account hierarchy |
| Fleet / commercial driver tracking | `Driver` + `DriverQualification` + `Fleet` | Standard fleet objects; do not invent custom Driver |
| Used-car appraisal workflow | `Appraisal` standard object | Ships with Automotive Cloud — do not build custom |

---

## Recommended Workflow

1. Confirm Automotive Cloud license is provisioned and standard objects appear in Object Manager.
2. Map the dealer/OEM/customer org structure on paper. Decide whether `AccountAccountRelation` is needed (any multi-franchise scenario → yes).
3. Build the `VehicleDefinition` master from the OEM build catalog, with external IDs for idempotent reload.
4. Implement `Vehicle` ingestion using the definition lookup, with a delta-feed pattern (Platform Event or Bulk API 2.0).
5. Configure `AccountAccountRelation` records and rebuild sharing rules to reference them.
6. For each lifecycle program (recall, service campaign, warranty notification), define `ActionableEventType` and `ActionableEventTypeDef` versions before generating orchestrations.
7. If retail financing is in scope, configure `FinancialAccount` lifecycle and link to Vehicle + Opportunity.
8. Test the end-to-end flow with a representative VIN: dealer assignment, recall orchestration, financial account creation.

---

## Review Checklist

- [ ] `VehicleDefinition` and `Vehicle` correctly separated — pricing / specs not duplicated per VIN
- [ ] External IDs on both Vehicle and VehicleDefinition for idempotent reload
- [ ] `AccountAccountRelation` used for OEM-Dealer relationships (not `ParentId`)
- [ ] Sharing rules reference `AccountAccountRelation`, not `ParentId`
- [ ] `ActionableEventType` + `ActionableEventTypeDef` defined before generating orchestrations
- [ ] FinancialAccount records linked to both Vehicle and Opportunity (no orphan financials)
- [ ] DriverQualification only populated for fleet-customer scenarios (not retail)
- [ ] `Appraisal` standard object used rather than a custom `Appraisal__c`

---

## Salesforce-Specific Gotchas

1. **Vehicle vs VehicleDefinition Confusion** — Putting MSRP, options, or build specs on `Vehicle` instead of `VehicleDefinition` duplicates data per VIN and breaks model-level reporting. Always keep the model template separate from the per-VIN instance.

2. **`ParentId` Hierarchy Cannot Model Multi-Franchise Dealers** — A dealer that sells Ford and Toyota has two OEM relationships. `ParentId` is single-valued and breaks at the second OEM. Use `AccountAccountRelation` from day one.

3. **ActionableEvent Without TypeDef Versioning** — Skipping `ActionableEventTypeDef` and pointing orchestrations directly at `ActionableEventType` works initially, but the moment the recipe changes (recall remedy steps update), historical orchestrations get rewritten retroactively. Always create a TypeDef per version.

4. **VIN as External ID on the Wrong Object** — Marking VIN as the external ID on `VehicleDefinition` collapses the entire model into one record. VIN is a per-instance attribute and belongs as the external ID on `Vehicle` only.

5. **DriverQualification for Retail Customers** — Populating `DriverQualification` on consumer Accounts pulls in fleet-management compliance UX (license expiry alerts, medical-cert tracking) that retail orgs do not need. Only enable for fleet customers.

6. **Skipping `VehDefSearchableField` Population** — Without these rows, the inventory search UI returns no results even when `VehicleDefinition` records exist. The searchable fields table is a separate population step.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Data model design document | VehicleDefinition vs Vehicle field placement, external ID strategy |
| Dealer hierarchy map | OEM/Dealer/Customer Accounts with AccountAccountRelation roles |
| ActionableEvent type catalog | Type + TypeDef versions for each lifecycle program (recall, service, warranty) |
| FinancialAccount integration plan | Loan/lease lifecycle linking Vehicle, Opportunity, Account |
| Inventory ingestion runbook | OEM/DMS → VehicleDefinition → Vehicle load sequence with delta-feed pattern |

---

## Related Skills

- manufacturing-cloud-setup — for OEM-side production planning and account-based forecasting that feeds the dealer inventory
- industries-cloud-selection — for the architect-level decision of whether Automotive Cloud is the right vertical fit
- ha-dr-architecture — for backup strategy across the high-volume Vehicle / FinancialAccount data model
