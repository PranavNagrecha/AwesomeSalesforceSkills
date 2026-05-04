# Gotchas — Automotive Cloud Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Standard Objects Hidden Until License Activates

**What happens:** Practitioners try to find `Vehicle` or `VehicleDefinition` in Object Manager and see nothing. They conclude the objects don't exist and build custom `Vehicle__c`.

**When it occurs:** Sandbox provisioned before the Automotive Cloud license was attached, or in a developer org where Automotive Cloud was never enabled.

**How to handle:** Confirm license provisioning via Setup → Company Information → Org Edition. The Automotive Cloud standard objects (`Vehicle`, `VehicleDefinition`, `Appraisal`, `WarrantyTerm`, `Driver`, `DriverQualification`, `Fleet`, `FinancialAccount`) appear in Object Manager only after the license is active. If license is active and objects are still hidden, raise a support case before building custom equivalents.

---

## Gotcha 2: `VehDefSearchableField` Is a Separate Population Step

**What happens:** Vehicle definitions load successfully but inventory search returns no results. Practitioners assume the search index is broken.

**When it occurs:** First-time inventory load that focused on `VehicleDefinition` and `Vehicle` only.

**How to handle:** For every searchable field on `VehicleDefinition` (BodyStyle, FuelType, DriveTrain, etc.), populate a corresponding `VehDefSearchableField` row pointing at the definition. The searchable-fields table is what powers the inventory UI's filter facets — without rows in this table, the search returns empty.

---

## Gotcha 3: AccountAccountRelation Effective Dates Are Enforced

**What happens:** Practitioners create an `AccountAccountRelation` without setting `EffectiveFromDate` / `EffectiveToDate`. Sharing rules and reports filter to "active relationships" by default and skip these records.

**When it occurs:** Quick-create test data, or migrations that didn't carry over relationship dates from the legacy system.

**How to handle:** Always populate `EffectiveFromDate`. Leave `EffectiveToDate` blank for currently-active relationships, or set it to a future date for fixed-term franchise agreements. Document the date convention in the migration runbook.

---

## Gotcha 4: ActionableEvent Status Cannot Be Updated Directly Via DML

**What happens:** Practitioners write Apex to set `ActionableEventOrchestration.Status` directly via `update`. The DML succeeds but downstream orchestration steps don't fire.

**When it occurs:** Custom completion-tracking automation that bypasses the ActionableEvent invocable actions.

**How to handle:** Drive orchestration state through the `ActionableEventOrchestration` invocable actions (Start, Advance, Complete) rather than direct field updates. The orchestration engine performs side-effects (event publication, Case auto-creation) in the invocable path — direct DML skips those side-effects and leaves the orchestration in an inconsistent state.

---

## Gotcha 5: FinancialAccount Sharing Inherits From Account, Not Vehicle

**What happens:** A `FinancialAccount` linked to a Vehicle is invisible to the dealer service team that owns the Vehicle. Practitioners assume the lookup grants visibility.

**When it occurs:** Retail-credit setup where dealer staff need to see the loan balance to discuss payoff with the customer.

**How to handle:** `FinancialAccount` sharing follows the customer Account (the `AccountId` field on FinancialAccount), not the linked Vehicle. To grant dealer staff visibility, share the customer Account through the `AccountAccountRelation`-driven sharing rule, or add an explicit Account team / sharing rule that grants the dealer's role visibility on the customer Account.

---

## Gotcha 6: VIN Is Not Globally Unique Across Edge Cases

**What happens:** Practitioners assume VIN is a true global natural key and use it as the only Vehicle external ID. Then a salvage-title vehicle is rebuilt with a different VIN, or a pre-1981 vehicle has a non-standard 11-character VIN, and the load fails or merges incorrectly.

**When it occurs:** Used-vehicle inventory ingestion, especially fleet auctions or salvage operations.

**How to handle:** Use VIN as the primary external ID for new-vehicle inventory, but plan for an exception path: a synthetic key (`Source_System_Id__c`) for legacy / non-standard / rebuilt-title vehicles. Document the exception path in the data-load runbook.
