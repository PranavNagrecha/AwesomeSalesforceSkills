# Examples — Rebate Management Setup

## Example 1: Volume-Tier Program Skeleton on the Shipped Objects

**Scenario:** A distributor volume rebate for FY26 Q1: 2% up to 1,000 units, 3% to 5,000, 5% above. Paid quarterly, accrued monthly.

**Problem:** The reflex is to build `Rebate_Program__c` with a child `Benefit__c`. Those objects do not exist and nothing shipped will read them. The model is entirely standard, and the hierarchy is Program → Rebate Type → Benefit, not Program → Benefit.

**Solution:** A composite request that lays down the program, its rebate type, and the benefit tiers in one transaction:

```json
{
  "allOrNone": true,
  "compositeRequest": [
    {
      "method": "POST",
      "url": "/services/data/v63.0/sobjects/RebateProgram",
      "referenceId": "prog",
      "body": {
        "Name": "FY26 Q1 Distributor Volume Rebate",
        "Status": "Active"
      }
    },
    {
      "method": "POST",
      "url": "/services/data/v63.0/sobjects/ProgramRebateType",
      "referenceId": "rtype",
      "body": {
        "Name": "Unit Volume",
        "RebateProgramId": "@{prog.id}"
      }
    },
    {
      "method": "POST",
      "url": "/services/data/v63.0/sobjects/ProgramRebateTypeBenefit",
      "referenceId": "tier1",
      "body": {
        "ProgramRebateTypeId": "@{rtype.id}",
        "Name": "Tier 1 - up to 1000 units"
      }
    },
    {
      "method": "POST",
      "url": "/services/data/v63.0/sobjects/ProgramRebateTypeBenefit",
      "referenceId": "tier2",
      "body": {
        "ProgramRebateTypeId": "@{rtype.id}",
        "Name": "Tier 2 - 1001 to 5000 units"
      }
    }
  ]
}
```

**Why it works:** `RebateProgram` is the container; `ProgramRebateType` is what is measured — "volume rebate, revenue rebate, or rebate on every transaction" — and `ProgramRebateTypeBenefit` "Defines the benefit matrix for the rebate type. For example, 5% or $200." Putting the tiers under the rebate type rather than the program is what lets one program carry a volume rebate and a growth rebate side by side. Confirm each object's field API names against the object reference before filling in rates and thresholds; the structural relationships above are the part that is easy to get wrong.

---

## Example 2: Ingesting Transactions as `TransactionJournal`, Not a Custom Staging Object

**Scenario:** Nightly POS extract, roughly 400,000 rows, needs to reach the rebate calculation.

**Problem:** Teams stage the feed in a custom object and then try to "sync" it across. Nothing in Rebate Management reads a custom staging object, so the sync becomes a permanent second system with its own drift.

**Solution:** Load straight into `TransactionJournal` with Bulk API 2.0, keyed on an external id so the nightly job is idempotent. The object name and the loader invocation are the load-bearing parts below; take the column set from a `describe` of `TransactionJournal` in the target org rather than from this illustration, because the member, product, and quantity lookups differ by how the programme is configured:

```csv
ExternalTransactionId__c,AccountId,ProductId,TransactionDate,Quantity,Amount,CurrencyIsoCode,UnitOfMeasure
POS-2026-03-14-000117,001XX000003DHPl,01tXX0000015vXy,2026-03-14,24,318.00,USD,Case
POS-2026-03-14-000118,001XX000003DHPl,01tXX0000015vZq,2026-03-14,6,79.50,USD,Each
POS-2026-03-14-000119,001XX000003DKqR,01tXX0000015vXy,2026-03-14,120,1590.00,USD,Case
```

```bash
sf data upsert bulk \
  --sobject TransactionJournal \
  --file pos-extract-2026-03-14.csv \
  --external-id ExternalTransactionId__c \
  --wait 30
```

**Why it works:** `TransactionJournal` is "The transactions that need to be processed for a rebate program" — the shipped calculation reads it directly, so there is nothing to sync. Upserting on an external id makes a re-run safe after a partial failure, which matters because a duplicated journal row inflates a partner's tier. Note the mixed `UnitOfMeasure` values in rows 1 and 2: without `UnitOfMeasureConversion` loaded as reference data first, those 24 cases and 6 eaches are summed as 30 of something and the tier calculation is quietly wrong. Where partners self-report, `ReceivedDocument` "Allows partners to upload .CSV document" and gives the same path a portal-facing front door.

---

## Anti-Pattern: Editing a Calculated Payout to Apply a Negotiated Adjustment

**What practitioners do:** Finance agrees a goodwill top-up. An admin opens the member's payout record and edits the amount.

**What goes wrong:** The next calculation run against that payout period recomputes the value from the journals and the edit disappears. The partner has already seen the higher number, so the correction reads as a clawback. There is no record of who applied it, no approval, and no comment — the field history, if enabled at all, shows an amount change with no reason attached.

**Correct approach:** Put discretion in the objects built for it. Manual money is a `RebatePayoutAdjustment` — "Rebate amount adjustment that needs to be given manually" — and an in-period accrual correction is a `RebatePgmMbrAcruAdjustment`, which "Stores manual adjustments made to system-calculated accrual amounts, including the adjustment value, approval status, and related comments."

```apex
// Discretionary top-up recorded alongside the calculated payout,
// never written over it.
RebatePayoutAdjustment topUp = new RebatePayoutAdjustment(
    Name         = 'FY26 Q1 goodwill - late shipment credit',
    // Confirm the exact lookup and amount field API names against the
    // Rebate Management object reference before deploying.
    Description  = 'Approved by Channel Finance, ticket CHG-4471'
);
insert topUp;
```

The calculated payout stays reproducible from the journals, the adjustment carries its own approval and comment, and the two sum to what the partner is paid. That separation is what makes the audit report — payout traced back to source transactions — actually possible.
