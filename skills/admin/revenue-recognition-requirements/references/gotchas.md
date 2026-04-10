# Gotchas — Revenue Recognition Requirements

Non-obvious Salesforce Billing platform behaviors that cause real production problems in this domain.

## Gotcha 1: Finance Periods Must Exist Before Revenue Schedules Can Generate

**What happens:** When an Order is activated and `blng__RevenueRecognitionRule__c` is set on Product2, the Billing engine attempts to create a `blng__RevenueSchedule__c` record and distribute revenue across Finance Periods. If no Finance Periods exist that overlap the Order's service date range, the engine silently skips schedule creation. No error record is created, no warning is surfaced in the UI, and no platform notification fires. The OrderProduct appears to have activated normally.

**When it occurs:** Any Order activation where Finance Periods for the relevant service dates have not yet been created. This commonly occurs at the start of a new fiscal year (when the new year's Finance Periods have not been created yet), for multi-year subscriptions where only the first year's periods exist, or in sandbox environments that were refreshed without Finance Period data.

**How to avoid:** Before activating any Order in a revenue-recognition-enabled Salesforce Billing org, query `blng__FinancePeriod__c` records and confirm at least one Active Finance Period exists for every calendar month in the Order's service date range. Create missing Finance Periods via Salesforce Billing setup or via data import (usually an admin task done at fiscal year start). Run the check as the first step in the pre-activation workflow.

---

## Gotcha 2: Revenue Schedules Do Not Auto-Update on Contract Amendment

**What happens:** When a CPQ amendment order is activated (for an upgrade, downgrade, or co-term), the Billing engine creates a new `blng__RevenueSchedule__c` for the amendment OrderProduct (the delta). The original `blng__RevenueSchedule__c` is left unchanged — it continues spreading the original contract value across its original Finance Period range. There is no automatic consolidation, no update to the original schedule's total amount, and no signal that the two schedules need to be reconciled.

**When it occurs:** Every contract amendment in a Salesforce Billing org where the product uses revenue recognition rules. This includes seat-count upgrades, plan changes, co-terms, and early renewals.

**How to avoid:** Document the amendment reconciliation process explicitly:
1. After amendment order activation, query both the original and amendment `blng__RevenueSchedule__c` records.
2. Determine whether GL reporting sums both schedules (correct for delta-based ERP integrations) or expects a single consolidated schedule (requires manual Finance team reconciliation).
3. Never edit `blng__RevenueSchedule__c.blng__TotalAmount__c` directly — close the original and create a fresh net-new schedule if consolidation is required.

---

## Gotcha 3: blng__RevenueSchedule__c and OpportunityLineItem Revenue Schedules Are Completely Different Objects

**What happens:** Standard Salesforce has a feature called "Revenue Schedules" that can be enabled in Setup > Products > Schedule Settings. When enabled, OpportunityLineItems gain a Revenue Schedule related list that allows splitting revenue across periods for forecasting purposes. Practitioners unfamiliar with Salesforce Billing often confuse this feature with `blng__RevenueSchedule__c`. Enabling the standard feature, populating OpportunityLineItem revenue splits, or querying the standard `OpportunityLineItemSchedule` object has zero effect on Salesforce Billing revenue recognition behavior.

**When it occurs:** When a Salesforce admin or developer is asked to "set up revenue recognition" in a Billing org and reaches for the standard Salesforce setup path instead of the Billing-specific configuration path. This is especially common when the practitioner has prior Salesforce experience without Salesforce Billing experience.

**How to avoid:** Establish a clear naming convention in project documentation: always qualify "revenue schedule" with either "Billing revenue schedule (blng__RevenueSchedule__c)" or "standard OpportunityLineItem revenue schedule" to avoid ambiguity. When reviewing configuration, check for `blng__RevenueRecognitionRule__c` on Product2 (correct for Billing) rather than "Schedule Settings" in Setup (not relevant to Billing).

---

## Gotcha 4: SSP Defaults to List Price Ratio if Standalone Selling Price Is Not Set

**What happens:** For bundle products sold with multiple distinct performance obligations under ASC 606, the Billing engine must allocate the total transaction price to each component. If `blng__StandaloneSellingPrice__c` is not populated on the bundle component Product2 records, the engine falls back to using list price ratios for allocation. List price ratios often differ from the Standalone Selling Price ratios required by ASC 606, creating revenue allocations that fail audit review. The platform does not warn that SSP is missing — it silently applies the fallback.

**When it occurs:** Any bundled product sale where components have distinct performance obligations but `blng__StandaloneSellingPrice__c` was never populated. Common in orgs that migrated from a pre-ASC 606 configuration or that added new bundle components without updating the SSP field.

**How to avoid:** After setting up any bundle product in Salesforce Billing, verify that `blng__StandaloneSellingPrice__c` is populated on each component Product2. Work with Finance to confirm the SSP values are documented and approved. Include an SSP verification step in the product launch checklist.

---

## Gotcha 5: blng__RevenueTransaction__c Records Are System-Managed — Direct Edits Corrupt GL Integrity

**What happens:** Revenue Transaction records (`blng__RevenueTransaction__c`) are created and maintained by the Billing engine as Finance Periods close or revenue events trigger recognition. If a practitioner modifies these records directly (via Data Loader, Apex, or the UI) to correct a GL amount or reclassify a transaction, the engine's internal consistency checks are bypassed. The revenue schedule's tracked recognized-to-date amount diverges from the sum of its child transaction records, producing GL imbalances that are difficult to trace and reconcile.

**When it occurs:** When Finance discovers a recognition error (wrong GL account, wrong period, wrong amount) and attempts to fix it by editing the transaction record directly rather than correcting the underlying configuration and re-triggering schedule generation.

**How to avoid:** Treat `blng__RevenueTransaction__c` records as append-only, system-managed records. To correct a recognition error, the correct approach is to:
1. Identify the root cause (wrong rule, wrong Finance Period, wrong SSP).
2. Close the affected `blng__RevenueSchedule__c`.
3. Correct the configuration on the Product2 or the Revenue Recognition Rule.
4. Generate a corrected schedule via the appropriate Salesforce Billing process.
5. Record the correction as a manual journal entry in the ERP for the periods already closed.
