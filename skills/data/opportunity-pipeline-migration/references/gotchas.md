# Gotchas — Opportunity Pipeline Migration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: OpportunityHistory Cannot Be Inserted — This Is Not a Permissions Problem

**What happens:** The Bulk API 2.0 or SOAP API returns `INVALID_TYPE_FOR_OPERATION: entity type Opportunity History does not support create` when a migration job attempts to insert records into the OpportunityHistory object. Escalating to a System Administrator or adding the "Modify All Data" permission does not resolve the error.

**When it occurs:** Any time a migration plan treats OpportunityHistory as a writable object — typically because the migration engineer sees OpportunityHistory as a child of Opportunity in the object reference and assumes it can be loaded like other child objects (e.g., Contact under Account).

**How to avoid:** Recognize OpportunityHistory as a system-generated, read-only audit object. Historical stage data must be preserved via Task records (one Task per stage transition with `Subject = "Historical Stage: <stage>"` and `ActivityDate` = the transition date) or via sequential StageName updates on the Opportunity that cause Salesforce to auto-generate history records. Document this constraint in the migration plan before any work begins.

---

## Gotcha 2: Amount Becomes Read-Only Once OpportunityLineItems Exist

**What happens:** The Opportunity `Amount` field is editable when no line items exist. Once the first OpportunityLineItem is inserted, `Amount` becomes a system-calculated roll-up of the sum of `TotalPrice` across all line items and can no longer be set directly. An update operation targeting `Amount` on an Opportunity with line items silently ignores the value — the API does not return an error, but the Amount does not change.

**When it occurs:** When the source system's opportunity total does not precisely match the sum of line item `UnitPrice × Quantity`, or when rounding differences between systems produce a small discrepancy. The migration engineer loads Opportunities with the correct Amount, then loads line items, and discovers the Amount has changed to the calculated total.

**How to avoid:** Before loading, verify that the sum of all line item `TotalPrice` values for each opportunity matches the opportunity's expected Amount. If discrepancies exist, resolve them in the source data before the migration. Do not attempt to correct Amount after line items are loaded by issuing an update — it will not work. The only way to restore a specific Amount on an Opportunity with line items is to delete the line items, update the Amount, and re-insert the line items.

---

## Gotcha 3: Standard Price Book Entry Is Required Even When Never Used

**What happens:** Inserting a PricebookEntry for a Product2 into a custom Price Book fails with `FIELD_INTEGRITY_EXCEPTION` even though the custom Price Book exists and is active.

**When it occurs:** A Product2 record has been created but has no PricebookEntry in the Standard Price Book. Salesforce requires every product to have a Standard Price Book Entry before it can have entries in any custom Price Book. This is a data integrity constraint enforced at the API level. The error message does not clearly indicate the missing Standard PBE as the cause.

**How to avoid:** Always insert Standard Price Book Entries for every Product2 before inserting custom Price Book Entries. The Standard Price Book Entry `UnitPrice` can be $0.00 if the standard list price is not used. Query the Standard Price Book Id once: `SELECT Id FROM Pricebook2 WHERE IsStandard = true AND IsActive = true LIMIT 1`. Use this Id in all Standard PBE rows.

---

## Gotcha 4: Pricebook2Id Cannot Be Changed After Line Items Are Inserted

**What happens:** An Opportunity is loaded with an incorrect `Pricebook2Id` (e.g., the Standard Price Book instead of the intended custom Price Book), and then OpportunityLineItems are inserted referencing custom Price Book Entries. The line item insert fails with a Price Book mismatch error. Attempting to update `Pricebook2Id` on the Opportunity after line items exist fails: `FIELD_INTEGRITY_EXCEPTION: Opportunity pricebook cannot be changed when opportunity line items exist`.

**When it occurs:** When the migration CSV for Opportunities has an incorrect or missing `Pricebook2Id`, or when the Price Book is not confirmed before the line item load begins.

**How to avoid:** Validate `Pricebook2Id` on every Opportunity row before loading. After the Opportunity load, run a verification query: `SELECT Id, Pricebook2Id FROM Opportunity WHERE Legacy_Opportunity_Id__c IN (...)`. Do not proceed to load OpportunityLineItems until this verification passes.

---

## Gotcha 5: StageName Must Match the Assigned Sales Process — Not Just the Global Picklist

**What happens:** An Opportunity insert fails with `INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST: StageName` even though the stage name exists as a picklist value in the global Opportunity Stage picklist.

**When it occurs:** The Opportunity's Record Type is associated with a Sales Process that does not include all global stage values. If the source system had custom stages (e.g., "Under Legal Review") that are defined globally but not added to the Sales Process assigned to the Record Type, attempts to load records with those stage names fail.

**How to avoid:** Before the migration, query the Sales Process stages available for each Record Type: `SELECT StageName FROM OpportunityStage WHERE IsActive = true`. Cross-reference this list against all unique StageName values in the source export. For any stage not in the Sales Process, either add it to the Sales Process (requires admin action) or remap the source stage to the closest equivalent target stage before loading.

---

## Gotcha 6: OpportunitySplits Enabling Is Irreversible in Production

**What happens:** A migration plan includes loading OpportunitySplit records. The engineer enables Opportunity Splits in production Setup to allow the load. After migration, the business decides splits are not needed. Setup > Opportunity Splits no longer shows a "Disable" option — the feature cannot be turned off once enabled.

**When it occurs:** When Splits are enabled in production without first confirming the business intent and testing the configuration in a sandbox.

**How to avoid:** Enable Opportunity Splits in a sandbox first. Validate the full split load sequence (SplitType configuration → OpportunityTeamMember → OpportunitySplit) in the sandbox before enabling in production. Get explicit stakeholder sign-off before enabling in production. Document the irreversibility in the migration plan so all approvers are aware.
