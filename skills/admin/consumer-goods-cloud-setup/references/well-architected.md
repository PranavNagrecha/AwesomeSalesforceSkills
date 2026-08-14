# Well-Architected Notes — Consumer Goods Cloud Setup

## Relevant Pillars

### Reliability

Retail execution is a chain of reference data with hard ordering dependencies, and the failure mode at every link is silence rather than an error. A `RetailLocationGroup` created after the KPI load has no `RetailStoreKpi` targets, so visits against it record actuals with nothing to score. A `StoreProduct` without an `InStoreLocation` gives image recognition no expected placement. None of these raise anything; they produce a compliance dashboard that is confidently wrong. Reliability here is a load order plus a set of completeness checks that run before go-live and after every reference-data change.

### Operational Excellence

CG Cloud is two object models under one product name — standard Retail Execution objects (`RetailStore`, `Visit`, `AssessmentTask`, `RetailStoreKpi`, `RetailVisitKpi`, `InStoreLocation`, `Assortment`, `Promotion`) and roughly 150 `cgcloud__` managed-package objects covering route planning, ordering, and inventory. Knowing which layer a given capability lives in is the difference between configuring what shipped and rebuilding it. Managed-package objects also carry upgrade semantics the standard ones do not, so customisations against them need their own review at each package version.

### Scalability

A visit is not one record. A weekly cadence across a few thousand stores generates visits, assessment tasks, KPI actuals, content documents, order activities, and signature records — a multiplier of roughly one order of magnitude per visit. Photo attachments dominate storage. Scaling means deciding retention per object rather than for the org: KPI actuals are the analytical asset and should be kept, while the photographs that produced a passing planogram score usually need not be retained past the promotion period.

## Architectural Tradeoffs

**Store groups vs. per-store targets.** `RetailStoreKpi` attaches targets to store groups, which keeps a few thousand stores maintainable and forces every store into a segment. Per-store precision requires narrower groups, and the group count is the maintenance cost. Segment by what actually differentiates the target — format and volume band — not by geography, which reps and territories already handle.

**Assortment breadth vs. visit length.** A wide assortment gives richer compliance data and a longer visit. Reps have a fixed number of minutes per store, and a task list that cannot be finished is abandoned rather than shortened. Scope the assortment to what the visit's time budget supports, and let promotion-period templates add depth temporarily.

**Photo evidence vs. storage.** Image capture is what makes planogram compliance defensible with the retailer and is the largest storage line in the deployment. Retaining photos for disputed or failing checks and discarding those attached to passing ones keeps the evidence that gets used and drops the bulk that does not.

## Anti-Patterns

1. **Modelling stores as an Account record type.** `RetailStore` is a standard object and every retail-execution object relates to it. Typed Accounts have nothing to attach visits, KPIs, store products, or in-store locations to, and by the time this surfaces the Accounts are entangled with contacts and opportunities.

2. **Inferring object names from feature names.** There is no `RoutePlan`; route planning is `cgcloud__Trip_List__c`. Any name written from the capability's conversational label rather than from the developer guide has roughly even odds of being wrong, because the product mixes standard and namespaced objects with no visible rule.

3. **Reporting on `RetailVisitKpi` alone.** Actuals without their `RetailStoreKpi` targets and shared `AssessmentIndicatorDefinition` produce compliance numbers that are either uniformly perfect or uniformly zero. Compliance is the join, and a dashboard that reads one side is not measuring anything.

## Official Sources Used

- Consumer Goods Cloud Developer Guide — Standard Objects for Retail Execution — verbatim descriptions for `RetailStore`, `Visit` (API 47.0+), `Visitor`, `VisitedParty`, `AssessmentTask`, `AssessmentTaskOrder`, `AssessmentTaskContentDocument`, `AssessmentIndicatorDefinition`, `RetailStoreKpi`, `RetailVisitKpi`, `InStoreLocation`, `RetailLocationGroup`, `RetailStoreGroupAssignment`, `Assortment`, `AssortmentProduct`, `StoreAssortment`, `StoreProduct`, `Promotion`, `PromotionChannel`, `PromotionProduct`, `DeliveryTask`, `SignatureTask`, `SignatureTaskLineItem`, `OtherComponentTask`, `VehicleUserAssignment` (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.retail_api.meta/retail_api/sforce_api_objects_retail_overview.htm
- Consumer Goods Cloud Developer Guide — Custom Objects for Retail Execution — the `cgcloud__` namespace, `cgcloud__Trip_List__c`, `cgcloud__Visit_Template__c`, `cgcloud__Order__c`, `cgcloud__Inventory__c`, `cgcloud__POS__c`, `cgcloud__Org_Unit__c`, and the absence of any `RoutePlan` object (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.retail_api.meta/retail_api/sforce_api_objects_236_custom_objects.htm
- Consumer Goods Cloud Developer Guide — `Visit` (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.retail_api.meta/retail_api/sforce_api_objects_visits.htm
- Consumer Goods Cloud Developer Guide — `RetailStoreKpi` (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.retail_api.meta/retail_api/sforce_api_objects_retailstorekpi.htm
- Object Reference for the Salesforce Platform — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
