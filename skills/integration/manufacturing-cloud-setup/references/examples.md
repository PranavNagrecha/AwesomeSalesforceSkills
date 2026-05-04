# Examples — Manufacturing Cloud Setup

## Example 1: First Sales Agreement Go-Live with ABF Activation

**Context:** A consumer-goods manufacturer is rolling out Manufacturing Cloud to manage 24-month supply commitments with their top 50 distributors. Each agreement covers 30–60 SKUs with monthly schedules.

**Problem:** Two weeks after go-live, account executives report the executive forecast dashboard is empty. Ops confirm Sales Agreements are activated, OrderItems are flowing, but `AccountProductForecast` records do not exist.

**Solution:** The team had not activated the Account-Based Forecasting recalc DPE definition. Steps applied:

1. Setup → Data Processing Engine → located **Account-Based Forecasting recalculation** definition.
2. Activated the definition.
3. Scheduled it to run nightly at 02:00 org time.
4. Manually ran the definition once to backfill the 8 weeks of history accumulated since go-live.
5. Verified `AccountProductForecast` populated for all 50 accounts × 30+ products × monthly periods.
6. Documented the activation step in the org runbook so it is not forgotten in the next sandbox refresh.

**Lesson:** ABF recalc is an opt-in DPE job. Add it to the go-live checklist for every Manufacturing Cloud rollout.

---

## Example 2: Actual-vs-Planned Variance Investigation

**Context:** A distributor's account team reports that the Sales Agreement says they should have purchased 50K units in Q1 but the actuals dashboard shows only 30K. The distributor swears they placed the orders.

**Problem:** Three possible failure modes:

1. ABF recalc DPE is stale.
2. `OrderItem.SalesAgreementId` is null on the relevant orders.
3. Order date falls outside the schedule period boundary.

**Solution:** Investigation steps:

1. Checked DPE job history: last successful run 3 days ago. Triggered a manual recalc. Numbers moved from 30K to 42K — partial fix.
2. Queried `OrderItem WHERE AccountId = :distributorId AND SalesAgreementId = NULL` for the period. Found 80 orphan order items (8K units) where the integration had not populated `SalesAgreementId`.
3. Backfilled `SalesAgreementId` on the orphan orders by matching account + product + date-in-schedule-period.
4. Re-ran ABF recalc. Numbers landed at 50.2K — matches the distributor's claim.
5. Patched the Order ingest Flow to enforce `SalesAgreementId` population whenever an active agreement exists for the account+product.

**Lesson:** Variance investigations should always check the three failure modes in this order: DPE staleness → SalesAgreementId population → schedule period alignment.

---

## Example 3: Volume-Tier Rebate Program

**Context:** An OEM offers a quarterly volume rebate to its top 200 distributor accounts: 0–10K units = 0%, 10K–50K units = 2%, 50K+ units = 4%. Payout is calculated quarterly.

**Problem:** Initial implementation built a custom Apex rollup that ran nightly to calculate rebates. After 6 months, the rollup had accumulated edge-case bugs (period boundary handling, product-level eligibility, retroactive corrections) and was producing payouts that did not match the finance team's spreadsheet.

**Solution:** Replaced the custom rollup with native Rebate Management:

1. Created `RebateProgram` "Distributor Volume Rebate FY26".
2. Defined three tiers with cumulative-volume thresholds (0%, 2%, 4%).
3. Enrolled 200 distributors via `RebateProgramMember`.
4. Defined `RebateProgramPayoutPeriod` for each fiscal quarter.
5. Activated the **Rebate Payout Calculation** DPE definition; scheduled to run on the 5th of each month after period close.
6. First payout cycle reconciled to within $50 of the finance spreadsheet (rounding differences only). Subsequent cycles match exactly.

**Lesson:** Custom rebate logic accumulates edge-case bugs. The native Rebate Management engine handles tier boundaries, period close, retroactive corrections, and payout traceability. Always evaluate native first.

---

## Anti-Pattern: Using Opportunity for Multi-Period Demand Commitment

A manufacturer modeled 24-month supply commitments as Opportunities with a custom `Term__c` field and 24 child Opportunity Line Items per period. After 18 months, reporting was unworkable: Opportunity Stage didn't apply, OpportunityLineItem schedules were a separate Salesforce concept that didn't align, and the finance team couldn't get a clean planned-vs-actual view.

**Why it happens:** Sales-Cloud-trained practitioners default to Opportunity for any sale-related record.

**Correct approach:** Multi-period demand commitments are exactly what `SalesAgreement` was designed for. Sales Agreement schedules, ABF integration, and OrderItem reconciliation give planned-vs-actual reporting out of the box. Migrate from Opportunity-as-Agreement to SalesAgreement at the first opportunity.
