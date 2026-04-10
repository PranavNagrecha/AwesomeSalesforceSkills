# Commerce Pricing and Promotions — Work Template

Use this template when configuring pricebooks, tiered pricing, promotions, or coupons for a Salesforce B2B or D2C Commerce store.

## Scope

**Skill:** `commerce-pricing-and-promotions`

**Request summary:** (fill in what the user asked for)

**Store type:** [ ] B2B  [ ] D2C

**WebStore Id:** _______________

---

## Pre-Work Audit

Complete these queries before making any changes.

### Current WebStorePricebook Count

```soql
SELECT COUNT()
FROM WebStorePricebook
WHERE WebStoreId = '<WebStore.Id>'
-- Must be 4 or fewer before adding another pricebook (limit: 5 per store)
```

Result: _______ / 5 used

### BuyerGroupPricebook Count per BuyerGroup

```soql
SELECT BuyerGroupId, BuyerGroup.Name, COUNT(Id) pricebookCount
FROM BuyerGroupPricebook
WHERE BuyerGroupId IN (SELECT Id FROM BuyerGroup WHERE WebStoreId = '<WebStore.Id>')
GROUP BY BuyerGroupId, BuyerGroup.Name
-- Each BuyerGroup: must be under 50; warn if approaching 25 (evaluation limit)
```

### Active Promotion Count

```soql
SELECT COUNT()
FROM Promotion
WHERE IsActive = true
  AND (EndDate = null OR EndDate >= TODAY)
-- Must be under 50 automatic + 50 manual to avoid silent exclusion
```

Active automatic promotions: _______ / 50
Active manual/coupon promotions: _______ / 50

---

## Context Gathered

- **Store type:** B2B / D2C
- **Affected BuyerGroups:** (list names)
- **Pricebooks involved:** (list Pricebook2 names)
- **Checkout flow name:** _______________
- **PromotionsCartCalculator confirmed in flow:** [ ] Yes  [ ] No  [ ] Not applicable
- **Known constraints:** (note any limits already near capacity)

---

## Pricebook Assignment Plan

Document the intended pricebook-to-buyer-group mapping before creating records.

| Pricebook2 Name | Assigned via | BuyerGroup Name | Priority | Notes |
|---|---|---|---|---|
| (e.g., Distributor Pricebook) | BuyerGroupPricebook | Distributor Buyers | 10 | — |
| (e.g., Standard Pricebook) | WebStorePricebook | All store visitors | 20 | Guest-visible |

Total unique pricebooks per buyer (calculate): _______ / 25 max

---

## Tiered Pricing Configuration

Complete only if tiered pricing is required.

**Product / PricebookEntry:** _______________

**PriceAdjustmentSchedule:**
- AdjustmentType: [ ] PercentageDiscount  [ ] FixedAmount  [ ] Price

**Tier Bounds (verify contiguous — no gaps):**

| Tier | LowerBound | UpperBound | AdjustmentValue | Notes |
|---|---|---|---|---|
| 1 | 1 | ___ | ___ | |
| 2 | ___ | ___ | ___ | LowerBound must = previous UpperBound + 1 |
| 3 | ___ | null | ___ | Set last UpperBound to null for open-ended |

Gap check: LowerBound[n+1] = UpperBound[n] + 1 for all tiers? [ ] Yes  [ ] No (fix before deploying)

---

## Promotion Configuration

Complete only if promotions are being added or modified.

| Field | Value |
|---|---|
| Promotion Name | |
| IsActive | true / false |
| StartDate | |
| EndDate | |
| Priority | |
| Type | Automatic / Manual (coupon-gated) |
| Discount Type | |
| Discount Value | |

**Segment Junction Records Required:**

- [ ] `PromotionSegmentSalesStore` — WebStore.Id: _______________
- [ ] `PromotionSegmentBuyerGroup` (optional) — BuyerGroup.Id: _______________

**Coupon Codes (if manual promotion):**

| Code | MaxUsageCount | ExpirationDate |
|---|---|---|
| | | |
| | | |

---

## SOQL Validation Queries

Run these after making changes to confirm correct wiring.

```soql
-- 1. Confirm WebStorePricebook wiring
SELECT Id, WebStoreId, Pricebook2Id, Pricebook2.Name, IsActive, Priority
FROM WebStorePricebook
WHERE WebStoreId = '<WebStore.Id>'
ORDER BY Priority ASC

-- 2. Confirm BuyerGroupPricebook wiring
SELECT Id, BuyerGroupId, BuyerGroup.Name, Pricebook2Id, Pricebook2.Name, Priority
FROM BuyerGroupPricebook
WHERE BuyerGroup.Name IN ('<BuyerGroup name>', '<another BuyerGroup>')
ORDER BY BuyerGroupId, Priority ASC

-- 3. Confirm PriceAdjustmentSchedule and tiers
SELECT Id, Name, AdjustmentType, PricebookEntryId,
       (SELECT Id, LowerBound, UpperBound, AdjustmentValue
        FROM PriceAdjustmentTiers
        ORDER BY LowerBound ASC)
FROM PriceAdjustmentSchedule
WHERE PricebookEntryId = '<PricebookEntry.Id>'

-- 4. Confirm Promotion segment wiring
SELECT Id, Name, IsActive, Priority, StartDate, EndDate,
       (SELECT Id, SalesStoreId FROM PromotionSegmentSalesStores),
       (SELECT Id, BuyerGroupId FROM PromotionSegmentBuyerGroups)
FROM Promotion
WHERE Name = '<Promotion name>'

-- 5. Confirm coupon codes (if applicable)
SELECT Id, Code, MaxUsageCount, CurrentUsageCount, ExpirationDate
FROM PromotionCode
WHERE PromotionId = '<Promotion.Id>'
```

---

## Review Checklist

- [ ] `WebStorePricebook` count for the store is 5 or fewer
- [ ] `BuyerGroupPricebook` count per BuyerGroup is 50 or fewer
- [ ] Total pricebooks visible to any buyer does not exceed 25
- [ ] `PriceAdjustmentTier` bounds are contiguous (no gaps, no overlaps)
- [ ] Each active `Promotion` has a `PromotionSegmentSalesStore` record for this store
- [ ] Checkout flow contains the `PromotionsCartCalculator` subflow element
- [ ] Cart adjustment limits verified: 24 item-level, 6 order-level, 5 coupon codes
- [ ] Active promotion count is within 50 automatic / 50 manual limits
- [ ] End-to-end checkout test performed as a buyer in each affected BuyerGroup

---

## Notes

(Record any deviations from the standard pattern, decisions made, and why.)
