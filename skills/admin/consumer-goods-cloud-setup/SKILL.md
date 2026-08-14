---
name: consumer-goods-cloud-setup
description: "Consumer Goods Cloud setup: visit execution, retail execution, route planning, in-store task management, compliance checks, off-shelf detection, image recognition. NOT for territory planning and route optimization for sales reps - use integration/salesforce-maps-setup. NOT for B2B Commerce storefronts - use admin/b2b-commerce-store-setup."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Scalability
tags:
  - consumer-goods
  - retail-execution
  - visit-execution
  - route-planning
  - compliance
  - industries
  - cg-cloud
triggers:
  - "how do i set up consumer goods cloud in salesforce"
  - "retail execution visit planning route configuration"
  - "field rep store visit task compliance checks"
  - "cg cloud perfect store and in store task configuration"
  - "image recognition off shelf detection setup"
  - "visit execution survey and order capture"
inputs:
  - CG Cloud edition and license assignment
  - Retail segmentation (store types, banners, territories)
  - Visit cadence and task list mix (merchandising, compliance, sales order)
  - Mobile offline and image-recognition requirements
outputs:
  - CG Cloud feature activation checklist
  - Visit templates with task mix configured
  - Route plan + territory assignment rules
  - Mobile offline and image-recognition setup notes
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
status: stub
---

# Consumer Goods Cloud Setup

Activate when configuring Salesforce Consumer Goods (CG) Cloud for a consumer-packaged-goods company: retail execution, visit planning, in-store task capture, order-taking on the field, promotion compliance, and image-recognition-driven off-shelf detection. CG Cloud is distinct from Field Service — it is merchandising-first, not dispatch-first.

## Before Starting

- **Confirm the CG Cloud license and mobile offline package.** The CG mobile app is its own download; reps cannot use the standard Salesforce mobile app for visit execution.
- **Map the retail hierarchy.** Retailer → Banner → Store → Shelf is the typical hierarchy. Modeling this as Account hierarchies drives visit targeting, route planning, and reporting.
- **Know the visit cadence.** Weekly, biweekly, monthly, or exception-triggered visits each imply a different Route Plan and Visit auto-generation strategy.

## Core Concepts

### Retail Store + Visit + Task model

`RetailStore` is its own **standard** object — "Create records for physical retail stores associated to business accounts" — not an Account record type. `Visit` (API 47.0 and later) tracks "information related to a field rep's visit to a retail store where they perform retail activities." The work inside a visit is `AssessmentTask`: "Perform activities such as planogram check, inventory check, promotion check, in-store survey, or custom task in stores." `Visitor` represents "the sales reps performing visits" and `VisitedParty` "the contact person at the account that's being visited."

### Two models in one product

CG Cloud is half standard objects and half a `cgcloud__` managed package, and the split is not intuitive. Retail Execution ships standard: `RetailStore`, `Visit`, `AssessmentTask`, `RetailStoreKpi`, `RetailVisitKpi`, `InStoreLocation`, `Assortment`, `Promotion`, `RetailLocationGroup`. Route planning, order taking, and inventory are managed-package custom objects — `cgcloud__Trip_List__c` ("Use Trip List to plan visits based on a predefined sequence of customers"), `cgcloud__Visit_Template__c` ("Template that describes the basic call behavior"), `cgcloud__Order__c`, `cgcloud__Inventory__c`, `cgcloud__POS__c`, `cgcloud__Org_Unit__c`. There is no object named `RoutePlan`.

### Visit templates and KPI targets

`cgcloud__Visit_Template__c` is the "Template that describes the basic call behavior" — the task list a rep executes. Targets and results are separate standard objects: `AssessmentIndicatorDefinition` "Define parameters that act as markers of compliance for retail tasks to compare target and actual values," `RetailStoreKpi` maps "store groups to assessment indicator definition, products, and in-store location categories and define targets," and `RetailVisitKpi` captures "the actual information during a visit against the defined assessment indicator definition and target values." Store segmentation for targeting comes from `RetailLocationGroup` plus `RetailStoreGroupAssignment`.

### Image Recognition / Computer Vision

CG Cloud integrates with Salesforce Image Recognition for on-shelf photo analysis. It scores SKU facing counts, out-of-stock flags, and planogram compliance. Requires IR license and the shipped ML models.

## Common Patterns

### Pattern: Weekly route with in-store survey

A `cgcloud__Trip_List__c` sequences a Tier-1 territory weekly; each `Visit` carries `AssessmentTask` records from a `cgcloud__Visit_Template__c` — a merchandising check, an `AssessmentTaskOrder` step ("Define an order activity that the sales rep can perform during a visit to stores"), and a compliance photo step. `RetailVisitKpi` records the captured values against the store's `RetailStoreKpi` targets.

### Pattern: Off-shelf alert routing

Image Recognition flags a SKU out-of-stock against the `InStoreLocation` ("locations within a retail store's layout such as aisles, shelves, or backrooms") and the expected `StoreProduct`. A `Case` routes to the retailer's category manager, with resolution SLA tracked via Entitlement.

### Pattern: Promotion compliance audit

A `Promotion` runs Aug 1–14, scoped by `PromotionChannel` ("Associate a promotion with a store, store group, or an account") and `PromotionProduct`. The visit template for that window includes a compliance `AssessmentTask`: "Is the endcap display up?" Photos attach through `AssessmentTaskContentDocument`; IR scores planogram match; `RetailVisitKpi` rows aggregate to a promotion compliance dashboard.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Scheduled weekly rep visits | `cgcloud__Trip_List__c` + `cgcloud__Visit_Template__c` | Shipped flow; offline-capable |
| Exception-driven visit | Event-triggered `Visit` via Flow | No trip-list disruption |
| Planogram compliance | Image Recognition + IR models | Deterministic, auditable scoring |
| Field order capture | `AssessmentTaskOrder` / `cgcloud__Order__c` | Native to CG Cloud |
| Dispatch-based field work | Use Field Service, not CG | Different shipped features |

## Recommended Workflow

1. Confirm CG Cloud license, IR license (if using), and mobile offline package are provisioned.
2. Enable CG Cloud features in Setup and create the RetailStore account record type.
3. Import the retail hierarchy (Account → `RetailStore` → `InStoreLocation`) and `RetailLocationGroup` segmentation before any visit or trip-list data.
4. Define `cgcloud__Visit_Template__c` records per store tier; attach `AssessmentTask` definitions and `RetailStoreKpi` targets.
5. Build `cgcloud__Trip_List__c` sequences per territory; assign `Visitor` records; smoke-test `Visit` generation.
6. Configure Image Recognition models (shipped or custom-trained) and attach to photo task steps.
7. Run a full round-trip in a sandbox: sync offline → execute a Visit → upload → verify KPIs populate.

## Review Checklist

- [ ] CG mobile offline app installed on a rep test device
- [ ] `RetailStore` and `RetailLocationGroup` loaded before any `Visit` or trip-list records
- [ ] Visit Templates assigned to every active store segment
- [ ] Trip-list visit generation validated for next week's window
- [ ] IR models trained / validated on agency SKU set
- [ ] Offline conflict resolution policy documented
- [ ] KPI dashboards render expected rollups per rep/territory

## Salesforce-Specific Gotchas

1. **CG Cloud uses shipped platform events for visit sync.** Disabling the events breaks offline reconciliation silently; always check the Platform Events usage monitor after enabling.
2. **Image Recognition requires pre-trained models per product line.** Out-of-the-box models do not know your SKUs; budget model-training time before go-live.
3. **Trip-list regeneration is expensive.** Rebuilding sequences on large territories can take hours — schedule off-hours.

## Output Artifacts

| Artifact | Description |
|---|---|
| CG activation runbook | License checks, feature toggles, data load order |
| Visit template catalog | Templates by store tier and program |
| Trip-list matrix | Territory × rep × cadence view |
| IR model inventory | Models in use, accuracy metrics, retrain cadence |

## Related Skills

- `architect/sales-cloud-architecture` — account and data-model foundation
- `integration/platform-events-integration` — CG visit-sync backbone
