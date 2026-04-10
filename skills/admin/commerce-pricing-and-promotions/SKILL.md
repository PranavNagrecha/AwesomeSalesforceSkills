---
name: commerce-pricing-and-promotions
description: "Use this skill when configuring pricebooks, tiered pricing, promotions, coupon codes, or cart discounts for B2B or D2C Commerce stores. Trigger keywords: WebStorePricebook, BuyerGroupPricebook, PriceAdjustmentSchedule, PromotionsCartCalculator, commerce coupon, cart-level discount, tiered price, Commerce promotion. NOT for CPQ pricing, standard Sales Cloud Opportunity pricebooks, or Quote pricing."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Scalability
triggers:
  - "pricebook is not showing up for buyers in the commerce store"
  - "commerce promotion is active but discount is not applying at checkout"
  - "how do I set up tiered pricing based on quantity in B2B Commerce"
  - "coupon code is being rejected even though it is valid in the Promotions object"
  - "buyer group pricebook assignment is not resolving the right price"
  - "how many pricebooks can a B2B store support and what happens when you exceed the limit"
tags:
  - commerce
  - pricing
  - promotions
  - pricebook
  - b2b-commerce
  - d2c-commerce
  - buyer-group
  - tiered-pricing
  - coupons
  - cart-discounts
inputs:
  - "WebStore Id and store type (B2B or D2C)"
  - "Pricebook2 records and their intended buyer audience (BuyerGroup or guest)"
  - "Promotion scope: store-wide, segment, BuyerGroup, or coupon-gated"
  - "Tiered pricing requirements: quantity breaks and adjustment amounts"
  - "Checkout flow name (to confirm PromotionsCartCalculator subflow inclusion)"
outputs:
  - "WebStorePricebook junction records wiring pricebooks to the store"
  - "BuyerGroupPricebook junction records assigning pricebooks to buyer groups"
  - "PriceAdjustmentSchedule and PriceAdjustmentTier records for tiered pricing"
  - "Promotion, PromotionSegmentSalesStore, and PromotionSegmentBuyerGroup records"
  - "Checkout flow verified to include the Promotions subflow"
  - "SOQL validation queries confirming record wiring"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Commerce Pricing and Promotions

This skill activates when a practitioner needs to configure pricebook assignment, tiered pricing, or promotions (including coupons and cart-level discounts) for a Salesforce B2B or D2C Commerce store. It covers the full pricing resolution stack — from pricebook attachment through discount application at checkout — and explains all silent-failure limits that cause real production bugs.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Store type and Id:** B2B and D2C stores share the same pricing objects but differ in guest-buyer access patterns. Retrieve the `WebStore.Id` first.
- **Pricebook resolution limit:** The price engine evaluates at most 25 pricebooks per API call. Pricebooks ranked beyond 25 are silently excluded — no error is raised. Count assigned pricebooks before adding new ones.
- **Promotions do not self-apply:** Activating a Promotion record does not automatically apply discounts at checkout. The checkout flow must include the `PromotionsCartCalculator` subflow. Confirm this before debugging "promotion not working" reports.
- **API version floor:** `PriceAdjustmentSchedule` (tiered pricing parent) requires API v60.0+. `PriceAdjustmentTier` requires API v47.0+. Verify the org's API version before deploying tiered pricing metadata.

---

## Core Concepts

### 1. Pricebook Attachment via Junction Objects

Commerce stores do not use the standard Sales Cloud `Pricebook2Id` field on Account or Opportunity. Two dedicated junction objects control pricebook visibility:

- **`WebStorePricebook`** — links a `Pricebook2` to a `WebStore`. Maximum **5 pricebooks per store**. This is the platform hard limit; the 6th record raises a validation error.
- **`BuyerGroupPricebook`** — links a `Pricebook2` to a `BuyerGroup`. Maximum **50 pricebooks per BuyerGroup** and **100 BuyerGroups per pricebook**.

During price resolution, the engine collects all pricebooks visible to the buyer (via their BuyerGroup memberships and the store's WebStorePricebook assignments), ranks them by the `Priority` field on the junction record, then evaluates at most **25 pricebooks**. Pricebooks ranked 26th or higher are silently skipped — no error, no log entry.

### 2. Tiered Pricing with PriceAdjustmentSchedule

Tiered pricing (quantity-based price breaks) uses two objects linked to a `PricebookEntry`:

- **`PriceAdjustmentSchedule`** (API v60.0+) — the parent record that defines the adjustment method (`Percent`, `Amount`, or `Price`) and the associated `PricebookEntry`.
- **`PriceAdjustmentTier`** (API v47.0+) — child records on the schedule, each defining a `LowerBound`, optional `UpperBound`, and the adjustment value.

The engine applies the matching tier at add-to-cart time. If no tier matches (e.g., quantity falls outside all defined bounds), the base `PricebookEntry.UnitPrice` is used without adjustment.

### 3. Promotions, Segments, and the Checkout Flow Requirement

A `Promotion` record activates a discount but does nothing by itself. The full promotion execution stack is:

1. **`Promotion`** — defines the discount type, priority, start/end dates, and whether it is automatic or coupon-gated.
2. **`PromotionSegmentSalesStore`** — scopes the promotion to a specific `WebStore`.
3. **`PromotionSegmentBuyerGroup`** — further scopes the promotion to a specific `BuyerGroup` (optional; omit for store-wide promotions).
4. **`PromotionCode`** — links a coupon code string to the promotion (only for coupon-gated promotions).
5. **Checkout flow with `PromotionsCartCalculator` subflow** — at checkout, the platform's evaluate API runs all applicable automatic promotions (up to 50) and all applied manual/coupon promotions (up to 50) ranked by `Priority`. Promotions beyond rank 50 in either category are silently excluded.

Hard cart limits enforced at checkout:
- Maximum **5 coupon codes per cart** — adding a 6th raises a user-visible error.
- Maximum **24 item-level adjustments** per cart.
- Maximum **6 order-level adjustments** per cart.

---

## Common Patterns

### Pattern A: Store-Wide Automatic Promotion

**When to use:** A discount applies to all buyers in the store with no coupon required — e.g., a site-wide 10% off sale.

**How it works:**
1. Create a `Promotion` record with `IsActive = true`, `Priority` set relative to other promotions, and `StartDate`/`EndDate` defined.
2. Create a `PromotionSegmentSalesStore` record linking the promotion to the target `WebStore`.
3. Leave `PromotionSegmentBuyerGroup` absent (store-wide scope).
4. Confirm the checkout flow includes the `PromotionsCartCalculator` subflow — without it, the promotion never fires.
5. Test by adding qualifying products to a cart and completing checkout.

**Why not the alternative:** Simply activating the `Promotion` record and assuming it applies is the most common production bug. The checkout flow integration is non-optional.

### Pattern B: BuyerGroup-Scoped Pricebook with Tiered Pricing

**When to use:** Different buyer tiers (e.g., Distributors vs. Retailers) need different base prices, with further quantity-based discounts layered on top.

**How it works:**
1. Create one `Pricebook2` per buyer tier with appropriate `PricebookEntry` records and `UnitPrice` values.
2. Create a `BuyerGroupPricebook` junction record for each `Pricebook2` → `BuyerGroup` pairing. Set `Priority` to control resolution order within the group (lower number = higher priority).
3. Create a `WebStorePricebook` junction record for each pricebook that should also be discoverable at the store level (keep total under 5).
4. For products with quantity breaks, create a `PriceAdjustmentSchedule` linked to the relevant `PricebookEntry`, then add `PriceAdjustmentTier` child records for each quantity band.
5. Verify tier bounds are contiguous and non-overlapping — gaps cause the base price to apply silently.

**Why not the alternative:** Using a single pricebook for all buyers and applying manual price overrides at order entry bypasses the automated resolution stack and cannot scale across thousands of products or buyer groups.

### Pattern C: Coupon-Gated Promotion

**When to use:** A discount applies only when a buyer enters a valid coupon code at checkout.

**How it works:**
1. Create a `Promotion` record with the discount definition. Set it as manual (not automatic) so it does not fire without a code.
2. Create a `PromotionSegmentSalesStore` junction to scope it to the correct store.
3. Create one or more `PromotionCode` records linked to the promotion, each with a unique `Code` string.
4. Buyers enter the code at checkout. The `PromotionsCartCalculator` subflow validates the code and applies the discount.
5. Enforce the 5-coupon-per-cart limit in UX design — surface a clear error message if a buyer attempts to add a 6th code.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| All buyers in the store get the same price | One `Pricebook2` attached via `WebStorePricebook` | Simplest resolution path; use `BuyerGroupPricebook` only when differentiation is needed |
| Different buyer groups need different prices | Separate `Pricebook2` per tier, attached via `BuyerGroupPricebook` | The resolution engine picks the highest-priority matching pricebook per buyer |
| Quantity breaks on specific products | `PriceAdjustmentSchedule` + `PriceAdjustmentTier` on `PricebookEntry` | Declarative tiered pricing; no custom Apex required |
| Automatic discount for all buyers | `Promotion` + `PromotionSegmentSalesStore`, no coupon | Simplest promotion scope; still requires the checkout flow subflow |
| Discount only for a specific buyer group | `Promotion` + `PromotionSegmentSalesStore` + `PromotionSegmentBuyerGroup` | Scoping to BuyerGroup prevents the discount from leaking to other segments |
| Discount requires a coupon code | `Promotion` (manual) + `PromotionCode` records | Manual promotions are only evaluated when a buyer supplies the code |
| Store is close to the 5-pricebook limit | Consolidate buyer tiers into fewer `Pricebook2` records | The 5-per-store limit is hard; consolidation or BuyerGroupPricebook is the only path |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Audit current pricebook assignment.** Query `WebStorePricebook` for the target `WebStore.Id` and count existing records. Confirm the count is under 5 before creating new ones. Query `BuyerGroupPricebook` for each relevant `BuyerGroup` and confirm counts are under 50.
2. **Design the buyer-tier-to-pricebook mapping.** Document which `BuyerGroup` maps to which `Pricebook2` and what `Priority` value each junction record should carry. Confirm total unique pricebooks evaluated per buyer does not exceed 25.
3. **Create or update pricebook junction records.** Insert `WebStorePricebook` records for store-level visibility and `BuyerGroupPricebook` records for segment-level assignment. Set `Priority` fields deliberately — the evaluation order determines which price wins when multiple pricebooks contain the same product.
4. **Configure tiered pricing if required.** Create `PriceAdjustmentSchedule` linked to the target `PricebookEntry`, then add `PriceAdjustmentTier` child records with contiguous quantity bounds. Verify no gaps exist between tier upper and lower bounds.
5. **Set up promotions and scope them correctly.** Create `Promotion` records, then wire `PromotionSegmentSalesStore` (required) and optionally `PromotionSegmentBuyerGroup`. For coupon-gated promotions, create `PromotionCode` records. Confirm `IsActive = true` and date ranges are correct.
6. **Verify the checkout flow includes the Promotions subflow.** Open the active checkout flow in Flow Builder and confirm the `PromotionsCartCalculator` element is present in the cart calculation sequence. Without it, no promotions fire.
7. **Run SOQL validation and end-to-end checkout test.** Execute the validation queries in the template to confirm all junction records are wired correctly. Place a test order as a buyer in the affected `BuyerGroup` and confirm prices and discounts resolve as expected.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `WebStorePricebook` count for the store is 5 or fewer
- [ ] `BuyerGroupPricebook` count per BuyerGroup is 50 or fewer; pricebook has 100 or fewer BuyerGroups
- [ ] Total pricebooks visible to any single buyer does not exceed 25
- [ ] `PriceAdjustmentTier` bounds are contiguous (no gaps, no overlaps) for every tiered product
- [ ] Each active `Promotion` has a `PromotionSegmentSalesStore` record for the correct store
- [ ] Checkout flow contains the `PromotionsCartCalculator` subflow element
- [ ] Cart-level adjustments stay within limits: 24 item-level, 6 order-level, 5 coupon codes
- [ ] Promotions ranked beyond 50 (automatic) or 50 (manual) have been removed or re-prioritized
- [ ] End-to-end checkout test performed as a buyer in each affected BuyerGroup

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Silent pricebook exclusion at rank 26+** — The price engine evaluates at most 25 pricebooks per call. If a buyer belongs to multiple BuyerGroups with many pricebook assignments and the total visible pricebooks exceeds 25, the lowest-priority ones are silently skipped. No error is logged. Buyers may see wrong prices with no obvious cause.
2. **Promotions require the checkout flow subflow** — Activating a `Promotion` record and making it active does not apply any discount. The `PromotionsCartCalculator` must be present in the active checkout flow. Removing or bypassing the flow (e.g., during testing with a custom flow) silently disables all promotions.
3. **5 coupon codes per cart is a hard limit** — Attempting to apply a 6th coupon code raises a user-visible error. Design the UX to surface a clear message before this limit is hit, not after.
4. **Silent promotion exclusion at rank 51+** — The evaluate API processes at most 50 automatic and 50 manual promotions per checkout, ranked by `Priority`. Promotions outside that window are silently ignored. Regularly audit promotion counts and retire expired records.
5. **`Pricebook2Id` on Account does not work for Commerce** — The standard Sales Cloud field `Account.Pricebook2Id` is ignored by the Commerce pricing engine. Pricebook assignment for Commerce buyers must go through `WebStorePricebook` and `BuyerGroupPricebook`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `WebStorePricebook` records | Junction records linking each `Pricebook2` to the `WebStore` with a `Priority` value |
| `BuyerGroupPricebook` records | Junction records assigning pricebooks to `BuyerGroup` records for segment-specific pricing |
| `PriceAdjustmentSchedule` records | Parent records enabling tiered pricing on a `PricebookEntry` (requires API v60.0+) |
| `PriceAdjustmentTier` records | Child records defining quantity bounds and adjustment values for tiered pricing |
| `Promotion` + segment junction records | `Promotion`, `PromotionSegmentSalesStore`, `PromotionSegmentBuyerGroup` records defining the discount and its scope |
| `PromotionCode` records | Coupon code strings linked to manual promotions |
| SOQL validation queries | Queries verifying junction record wiring before buyer testing |

---

## Related Skills

- `admin/b2b-commerce-store-setup` — covers `WebStore`, `BuyerGroup`, `EntitlementPolicy`, and catalog access wiring that must be in place before pricing configuration
