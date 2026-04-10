# Examples — Commerce Pricing and Promotions

## Example 1: Tiered Pricing for a B2B Distributor Pricebook

**Context:** A B2B Commerce org sells industrial parts. Distributor buyers get a volume discount: standard price for 1–9 units, 10% off for 10–49 units, 18% off for 50+ units. The `PricebookEntry` for SKU-1001 already exists in the Distributor `Pricebook2`.

**Problem:** Without `PriceAdjustmentSchedule` and `PriceAdjustmentTier` records, every quantity resolves to the flat `UnitPrice`. Manual per-order overrides are not scalable across 5,000 SKUs.

**Solution:**

```soql
-- Step 1: Find the PricebookEntry for SKU-1001 in the Distributor pricebook
SELECT Id, Pricebook2Id, Product2Id, UnitPrice
FROM PricebookEntry
WHERE Pricebook2.Name = 'Distributor Pricebook'
  AND Product2.ProductCode = 'SKU-1001'
```

Then create records via the API or Data Loader:

```json
// PriceAdjustmentSchedule (parent — requires API v60.0+)
{
  "Name": "SKU-1001 Distributor Tier Schedule",
  "AdjustmentType": "PercentageDiscount",
  "PricebookEntryId": "<PricebookEntry.Id from above>"
}

// PriceAdjustmentTier — Tier 1: 1–9 units (no discount)
{
  "PriceAdjustmentScheduleId": "<schedule Id>",
  "LowerBound": 1,
  "UpperBound": 9,
  "AdjustmentValue": 0
}

// PriceAdjustmentTier — Tier 2: 10–49 units (10% off)
{
  "PriceAdjustmentScheduleId": "<schedule Id>",
  "LowerBound": 10,
  "UpperBound": 49,
  "AdjustmentValue": 10
}

// PriceAdjustmentTier — Tier 3: 50+ units (18% off)
{
  "PriceAdjustmentScheduleId": "<schedule Id>",
  "LowerBound": 50,
  "UpperBound": null,
  "AdjustmentValue": 18
}
```

**Why it works:** The Commerce price engine reads the `PriceAdjustmentSchedule` linked to the `PricebookEntry` and applies the matching tier at add-to-cart time. Tier bounds must be contiguous — a gap between `UpperBound` of one tier and `LowerBound` of the next causes the engine to fall back to the base `UnitPrice` for quantities in the gap. Setting `UpperBound = null` on the last tier means it applies to all quantities above the lower bound.

---

## Example 2: BuyerGroup-Scoped Promotion with Checkout Flow Verification

**Context:** A D2C Commerce org wants to give VIP buyers a 15% discount on their next order. The discount should only apply to buyers in the "VIP Buyers" BuyerGroup and should not appear on the storefront as a publicly visible promotion — so it is automatic (no coupon required) but scoped to the BuyerGroup segment.

**Problem:** An admin creates the `Promotion` record, sets it to active, and links it to the store via `PromotionSegmentSalesStore`. QA reports the discount never appears at checkout. The root cause: the org's checkout flow was cloned from a template before the `PromotionsCartCalculator` element was added, so promotions are never evaluated.

**Solution:**

```soql
-- Step 1: Confirm the Promotion is active and in-window
SELECT Id, Name, IsActive, StartDate, EndDate, Priority
FROM Promotion
WHERE Name = 'VIP 15% Off'

-- Step 2: Confirm PromotionSegmentSalesStore is wired to the correct store
SELECT Id, PromotionId, SalesStoreId
FROM PromotionSegmentSalesStore
WHERE PromotionId = '<Promotion.Id>'
  AND SalesStore.Name = 'VIP D2C Store'

-- Step 3: Confirm BuyerGroup scoping
SELECT Id, PromotionId, BuyerGroupId, BuyerGroup.Name
FROM PromotionSegmentBuyerGroup
WHERE PromotionId = '<Promotion.Id>'
```

Then open Flow Builder and locate the active checkout flow. Search for the element `PromotionsCartCalculator`. If it is absent, add it to the cart calculation sequence — it must run before the cart totals are finalized.

**Why it works:** The `PromotionsCartCalculator` is the execution bridge between the `Promotion` data model and the live cart. Without it in the flow, the platform never calls the evaluate API that reads promotion records and applies discounts. Adding the element and reactivating the flow is the only fix — no amount of data changes to the Promotion records will matter without it.

---

## Anti-Pattern: Using Account.Pricebook2Id for Commerce Buyers

**What practitioners do:** An admin familiar with Sales Cloud assigns a pricebook to a buyer account by setting `Account.Pricebook2Id` to the desired `Pricebook2.Id`, then expects Commerce store buyers in that account to see those prices.

**What goes wrong:** The Commerce pricing engine does not read `Account.Pricebook2Id`. Pricebook resolution in Commerce is driven exclusively by `WebStorePricebook` and `BuyerGroupPricebook` junction records. Buyers see either the standard pricebook or no price, depending on what is wired via junction records. No error is raised — the field is simply ignored by the Commerce engine.

**Correct approach:** Assign the `Pricebook2` to the buyer's `BuyerGroup` via a `BuyerGroupPricebook` record. Set the `Priority` field on the junction to control resolution order. Optionally also attach the pricebook to the store via `WebStorePricebook` if it should be visible at the store level.

```soql
-- Verify correct wiring (not Account.Pricebook2Id)
SELECT Id, BuyerGroupId, Pricebook2Id, Priority
FROM BuyerGroupPricebook
WHERE BuyerGroup.Name = 'Distributor Buyers'
ORDER BY Priority ASC
```
