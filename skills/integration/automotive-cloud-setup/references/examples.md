# Examples — Automotive Cloud Setup

## Example 1: VIN Ingestion with Definition Deduplication

**Context:** A regional dealer group is migrating from a 15-year-old DMS into Salesforce Automotive Cloud. The legacy export contains 84,000 vehicle rows but only 2,300 distinct model/trim/year combinations.

**Problem:** A first-pass load created one `VehicleDefinition` per row, producing 84,000 definition records. Inventory search became unusable (every model appeared 30+ times in the type-ahead) and per-model reports broke.

**Solution:** Re-staged the load:

1. Built a deduplication pass keyed on `(Make, Model, ModelYear, Trim, BodyStyle)`. Loaded those 2,300 rows into `VehicleDefinition` first with an external ID `Build_Key__c`.
2. Loaded `Vehicle` records using `VehicleDefinitionId` resolved by upsert against `Build_Key__c`. External ID on `Vehicle` is the VIN itself.
3. Populated `VehDefSearchableField` rows for `BodyStyle`, `FuelType`, `DriveTrain`, `TrimLevel` — the four facets the dealer-portal UX filters on.
4. Wired ongoing inventory delta as a Bulk API 2.0 ingest job triggered by the OEM's nightly feed.

After the rebuild, `VehicleDefinition` count stabilized at ~2,400 (slight growth as new model years arrived) and inventory search returned correct, deduplicated results.

---

## Example 2: Multi-Franchise Dealer Hierarchy

**Context:** A dealer holding company owns 12 rooftops. Three rooftops sell Ford only, four sell Toyota only, and five are dual-franchise (Ford + Honda or Toyota + Subaru). The original implementation used `ParentId` to point each Dealer Account at its primary OEM.

**Problem:** The dual-franchise dealers could only point at one OEM through `ParentId`. Recall campaigns from the secondary OEM never reached those dealers because the sharing rule was keyed on `ParentId`. Customers buying a Honda from a Ford-primary dealer also disappeared from Honda's customer reports.

**Solution:** Replaced `ParentId` with `AccountAccountRelation`:

1. Created Account records for each OEM (Ford, Toyota, Honda, Subaru) with record type `OEM`.
2. For every OEM-Dealer pair, created an `AccountAccountRelation` with role `Franchisee` and the franchise effective date.
3. Rewrote the recall-routing sharing rule to traverse `AccountAccountRelation` rather than `ParentId`.
4. Cleared `ParentId` on Dealer Accounts (left blank — the Dealer Account is its own apex).

Result: dual-franchise rooftops now receive recall campaigns from both OEMs, and customer assignment correctly flows to whichever OEM relationship covers the sold vehicle.

---

## Example 3: Recall Orchestration with TypeDef Versioning

**Context:** An OEM issues a brake-component recall in Q1, then a remedy update in Q2 (the original remedy did not fully address the issue, so additional repair steps were added).

**Problem:** The original implementation pointed `ActionableEventOrchestration` records directly at `ActionableEventType`. When the Q2 remedy update was applied to the type, every Q1 orchestration retroactively showed the Q2 steps in its history, breaking audit trails.

**Solution:** Added an explicit TypeDef per version:

1. `ActionableEventTypeDef` v1 (Q1 remedy) — three steps: notify owner, open Case, complete repair.
2. `ActionableEventTypeDef` v2 (Q2 remedy) — five steps: notify owner, open Case, complete repair, install supplemental kit, verify with road test.
3. Q1 orchestrations remained pointed at v1; new Q2 orchestrations point at v2.
4. Reporting query joins on TypeDef version, so completion-rate reports separate the two waves correctly.

---

## Anti-Pattern: Custom `Vehicle__c` When Standard `Vehicle` Exists

A dealer org built a custom `Vehicle__c` object before discovering that Automotive Cloud ships a standard `Vehicle` object. The custom object captured VIN, mileage, owner — duplicating standard functionality. Migration cost: 4 weeks of data backfill, broken integrations, and refactored sharing rules.

**Why it happens:** The Automotive Cloud license was provisioned mid-project; the team had already built `Vehicle__c` against vanilla Sales Cloud and never re-evaluated.

**Correct approach:** When Automotive Cloud is provisioned, audit Object Manager for the standard objects (`Vehicle`, `VehicleDefinition`, `Appraisal`, `WarrantyTerm`, `FinancialAccount`) before building any custom equivalents. The standard objects ship with prebuilt page layouts, list views, and ActionableEvent integration that custom objects do not get.
