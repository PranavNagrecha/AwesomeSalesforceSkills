# Gotchas — Commerce Pricing and Promotions

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Pricebooks Beyond Rank 25 Are Silently Excluded at Resolution Time

**What happens:** The Commerce pricing engine evaluates at most 25 pricebooks per API call. If the total number of pricebooks visible to a buyer — across all their `BuyerGroup` memberships and the store's `WebStorePricebook` records — exceeds 25, the engine silently skips the lowest-priority ones. No error is logged, no exception is thrown, and the buyer sees a price from a pricebook that should have been overridden.

**When it occurs:** Most commonly in multi-tenant B2B orgs where many `BuyerGroup` records exist, each with its own pricebook assignments. A buyer belonging to multiple BuyerGroups can easily accumulate 30+ visible pricebooks. Also occurs when development pricebooks are left active and attached to BuyerGroups after testing.

**How to avoid:** Audit the pricebook count per buyer segment before adding new pricebook assignments. Query the union of `WebStorePricebook` and `BuyerGroupPricebook` for each BuyerGroup a buyer belongs to, count unique `Pricebook2Id` values, and confirm the total is 25 or fewer. Remove or deactivate pricebook assignments for retired development pricebooks.

---

## Gotcha 2: Promotions Never Fire Without the PromotionsCartCalculator Subflow

**What happens:** A `Promotion` record is created, set to `IsActive = true`, scoped to the correct store via `PromotionSegmentSalesStore`, and has a valid date range — but no discount ever appears at checkout. The cause is that the active checkout flow does not include the `PromotionsCartCalculator` element.

**When it occurs:** Consistently when a checkout flow was cloned from an older template before the Promotions subflow element was available, or when a custom checkout flow was built from scratch without referencing the standard template. Also occurs when an org upgrades Commerce and the flow is not updated to include the new element.

**How to avoid:** Before debugging any promotion, open Flow Builder and confirm the `PromotionsCartCalculator` element is present in the active checkout flow's cart calculation sequence. This check should be the first step in any "promotion not working" investigation. The element must execute before cart totals are finalized.

---

## Gotcha 3: The 5-Coupon-Per-Cart Limit Raises a User-Visible Error with No Graceful Fallback

**What happens:** When a buyer attempts to apply a 6th coupon code to their cart, the platform raises an error. The error surfaces in the storefront UI, but the default error message is generic and does not clearly communicate the limit to the buyer.

**When it occurs:** Any cart where 5 `PromotionCode` records have already been applied. More common in orgs with aggressive promotional strategies that stack multiple coupon codes.

**How to avoid:** Add frontend validation in the store to count applied coupon codes before allowing the buyer to submit a new one. Surface a human-readable message ("Maximum of 5 promo codes per order") before the platform error fires. Also review the promotional strategy — if buyers routinely need more than 5 codes, consider consolidating promotions into fewer, more comprehensive records.

---

## Gotcha 4: PriceAdjustmentTier Gaps Cause Silent Fallback to Base UnitPrice

**What happens:** If a gap exists between the `UpperBound` of one `PriceAdjustmentTier` and the `LowerBound` of the next tier, quantities that fall in the gap receive the base `PricebookEntry.UnitPrice` with no adjustment applied. No warning is raised — the system silently falls back to the base price.

**When it occurs:** During initial tier configuration when tier bounds are set independently rather than as a contiguous sequence. For example, Tier 1 ends at `UpperBound = 9` and Tier 2 starts at `LowerBound = 11` — quantities of exactly 10 receive the base price.

**How to avoid:** Verify that `LowerBound` of each subsequent tier equals `UpperBound + 1` of the previous tier. Set `UpperBound = null` on the final tier to cover all quantities above the lower bound without an upper cap. Use a SOQL query to extract all tiers for a schedule ordered by `LowerBound` and visually inspect for gaps before deploying.

---

## Gotcha 5: Promotions Beyond Rank 50 Are Silently Excluded at Checkout

**What happens:** The Commerce promotions evaluate API processes at most 50 automatic promotions and 50 manual/coupon promotions per checkout call, ranked by the `Priority` field on the `Promotion` record. Promotions ranked 51st or lower in either category are silently excluded. A promotion with a lower priority number than expected can be displaced if many higher-priority promotions are active simultaneously.

**When it occurs:** Orgs that accumulate promotions over time without retiring expired ones. A seasonal promotion from a previous year still set to `IsActive = true` occupies a priority slot at checkout. Over several promotional cycles, the active promotion count can exceed 50 without anyone noticing.

**How to avoid:** Implement a hygiene process to set `IsActive = false` on promotions past their `EndDate`. Run a regular SOQL audit of active promotions ordered by `Priority` to ensure the most important ones fall within the top 50. Consider using `EndDate` instead of manual deactivation as the primary gate for promotion expiry.

---

## Gotcha 6: WebStorePricebook Hard Limit of 5 Is Per Store, Not Per Org

**What happens:** Each `WebStore` record can have at most 5 `WebStorePricebook` junction records. Attempting to create a 6th raises a platform validation error. This limit is per store — an org with two stores can have up to 5 pricebooks per store (10 total `WebStorePricebook` records across the org).

**When it occurs:** When an org grows beyond a simple pricing model and attempts to attach more than 5 pricebooks directly to a store for broad visibility. Often encountered when teams add development or seasonal pricebooks without removing old ones.

**How to avoid:** For additional pricing differentiation beyond 5, use `BuyerGroupPricebook` instead of `WebStorePricebook`. `BuyerGroupPricebook` allows up to 50 pricebooks per BuyerGroup and is the recommended path for segment-specific pricing. Reserve `WebStorePricebook` slots for pricebooks that need store-wide (guest or default) visibility.
